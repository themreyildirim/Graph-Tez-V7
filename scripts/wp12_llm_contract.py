"""WP12 tasarım v1: ağ/LLM istemcisi içermeyen, salt veri doğrulayıcı.

Bir adayın geçmesi anlam doğruluğu değildir: bütün adaylar insan incelemesinde
bekler. Kaynaklar kabul edilmiş pilot paketinden okunur; değiştirilmez.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PILOT = ROOT / 'reports/qa/WP12/pilot_v1'
VERSION = 'WP12-local-llm-candidate-v1'
REFUSALS = ('NO_SOURCE', 'FORBIDDEN_TASK', 'MISSING_CONTEXT',
            'IMAGE_TEXT_UNAVAILABLE', 'CONTEXT_BUDGET', 'UNCERTAIN_EVIDENCE')


def load_sources():
    bundle = json.loads((PILOT / 'source_evidence_bundle.json').read_text(encoding='utf-8'))
    annotations = json.loads((PILOT / 'source_context_annotations.json').read_text(encoding='utf-8'))
    return bundle, annotations


def source_index(bundle, annotations):
    quotes = {q['quote_id']: q for q in bundle['quotes']}
    pages = {p['page_id']: p for p in bundle['pages']}
    assert len(quotes) == len(bundle['quotes'])
    assert len(pages) == len(bundle['pages'])
    ann = {a['quote_id']: a for a in annotations}
    assert set(ann) == set(quotes)
    for q in quotes.values():
        p = pages[q['page_id']]
        assert p['document_id'] == q['document_id']
        assert p['extraction_run_id'] == q['extraction_run_id']
        assert p['page_number'] == q['page_number'] == p['page_index'] + 1
        assert 0 <= q['char_start'] < q['char_end'] <= len(p['text'])
        assert p['text'][q['char_start']:q['char_end']] == q['quote']
        assert sha256(q['quote'].encode()).hexdigest() == q['quote_sha256']
        assert sha256(p['text'].encode()).hexdigest() == p['text_sha256']
    return quotes, pages, ann


def dependencies(annotations):
    """Ek tasarım kuralı eski anotasyonları değiştirmez: renal ifadeye istisna ekle."""
    by_key = {a['key']: a for a in annotations}
    out = {a['quote_id']: set(a['context_quote_ids']) for a in annotations}
    out[by_key['D_class_renal']['quote_id']].add(by_key['D_BUN_exception']['quote_id'])
    return out


def schema(annotations):
    scopes = sorted({a['attribution_scope'] for a in annotations})
    purposes = sorted({a['purpose'] for a in annotations})
    def obj(properties):
        return {'type': 'object', 'additionalProperties': False,
                'required': list(properties), 'properties': properties}
    s = obj({'schema_version': {'const': VERSION},
             'status': {'enum': ['candidate', 'refused']},
             'refusal_code': {'type': ['string', 'null'], 'enum': [None, *REFUSALS]},
             'items': {'type': 'array', 'maxItems': 4, 'items': obj({
                 'explanation_tr': {'type': 'string', 'minLength': 1, 'maxLength': 1200},
                 'source_scope': {'enum': scopes}, 'statement_kind': {'enum': purposes},
                 'evidence_ids': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                                  'items': {'type': 'string'}}})}})
    s['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    return s


def validate_candidate(candidate, *, allowed_ids, bundle, annotations, task='source_summary'):
    """Yalnız yapısal/provenans kapısı; semantik otomatik kabul YOK."""
    quotes, _, ann = source_index(bundle, annotations)
    if not isinstance(candidate, dict) or set(candidate) != {
            'schema_version', 'status', 'refusal_code', 'items'}:
        raise ValueError('strict top-level keys')
    if candidate['schema_version'] != VERSION:
        raise ValueError('version')
    if not isinstance(candidate['items'], list):
        raise ValueError('items list')
    if candidate['status'] == 'refused':
        if candidate['items'] or candidate['refusal_code'] not in REFUSALS:
            raise ValueError('invalid refusal')
        return 'REFUSED_NO_EXPLANATION'
    if task != 'source_summary':
        raise ValueError('forbidden task: no prediction, attribution or label generation')
    if candidate['status'] != 'candidate' or candidate['refusal_code'] is not None:
        raise ValueError('candidate status')
    allowed = set(allowed_ids)
    if not allowed or not allowed <= set(quotes):
        raise ValueError('no trusted source')
    if not 1 <= len(candidate['items']) <= 4:
        raise ValueError('candidate item count')
    deps = dependencies(annotations)
    for item in candidate['items']:
        if not isinstance(item, dict) or set(item) != {
                'explanation_tr', 'source_scope', 'statement_kind', 'evidence_ids'}:
            raise ValueError('strict item keys')
        text = item['explanation_tr']
        if not isinstance(text, str) or not text.strip() or len(text) > 1200:
            raise ValueError('explanation text')
        # Ek savunma: tam semantik doğrulayıcı olarak sunulmaz.
        if any(t in text.casefold() for t in ('shap', 'meddra', 'δz', 'delta_z', 'gnn', 'model skoru')):
            raise ValueError('forbidden generated output')
        ids = item['evidence_ids']
        if not isinstance(ids, list) or not all(isinstance(x, str) for x in ids):
            raise ValueError('evidence list')
        if not ids or len(set(ids)) != len(ids) or not set(ids) <= allowed:
            raise ValueError('unknown, missing, duplicate or unselected evidence')
        for qid in ids:
            if not deps[qid] <= set(ids):
                raise ValueError('missing contextual source')
        # Birincil alıntının kapsamı/amacı birebir; bağlam alıntıları ayrı işlev görür.
        primary = ann[ids[0]]
        if item['source_scope'] != primary['attribution_scope']:
            raise ValueError('scope promotion or mismatch')
        if item['statement_kind'] != primary['purpose']:
            raise ValueError('statement kind mismatch')
    return 'STRUCTURE_VALID_PENDING_HUMAN_SEMANTIC_REVIEW'


def build_review_envelope(candidate, *, allowed_ids, bundle, annotations, task='source_summary'):
    status = validate_candidate(candidate, allowed_ids=allowed_ids, bundle=bundle,
                                annotations=annotations, task=task)
    quotes, pages, ann = source_index(bundle, annotations)
    result = {'schema_version': 'WP12-source-explanation-envelope-v1',
              'status': status, 'reported_in_PDF': [],
              'predicted_by_GNN': {'status': 'NOT_REQUESTED_IN_WP12', 'artifact_ref': None},
              'semantic_review': {'status': 'NOT_PERFORMED', 'auto_release': False}}
    for item in candidate['items']:
        citations = []
        for qid in item['evidence_ids']:
            q = quotes[qid]; p = pages[q['page_id']]
            citations.append({**deepcopy(q), 'source_sentence': q['quote'],
                              'printed_page_label': p['printed_page_label'],
                              'attribution_scope': ann[qid]['attribution_scope'],
                              'statement_kind': ann[qid]['purpose'],
                              'source_qualifier': ann[qid]['qualifier']})
        result['reported_in_PDF'].append({**deepcopy(item), 'citations': citations})
    return result


def infer(*args, **kwargs):
    raise RuntimeError('DESIGN_ONLY: LLM execution is not authorized in this stage')
