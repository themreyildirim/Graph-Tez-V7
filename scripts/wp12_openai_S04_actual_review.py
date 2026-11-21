"""S04 gerçek kayıt denetimi: yalnız dosya okur, key/API/optimizer kullanmaz."""
from pathlib import Path
from decimal import Decimal
import hashlib
from jsonschema import Draft202012Validator
import wp12_openai_scenarios_v2 as scenario
import wp12_openai_S04_execution_v1 as budget
from wp12_api_security import public_sha, is_private_path
from wp12_pilot import get_engine
from wp12_openai_client import parse_json

ROOT = scenario.ROOT
RUN = ROOT/'reports/qa/WP12/openai_S04_user_runs_v1/20261108_182154_7cd004b827cf4fb98d004be0a3390177'
QA = ROOT/'reports/qa/WP12/openai_S04_actual_review_v1'
FIG = ROOT/'reports/figures/WP12/openai_S04_actual_review_v1'
PDF = ROOT/'data/user_pdfs/pil.502.pdf'
RAW_HASH = 'acbafb53ffb8c937d5d1589a979d165b35ae654f94263b424653443b9edc6138'


def read(path):
    return scenario.old.c.read(path)


def model_message(raw):
    parts = [c['text'] for m in raw['output'] if m.get('type') == 'message'
             for c in m.get('content', []) if c.get('type') == 'output_text']
    if len(parts) != 1:
        raise ValueError('ONE_OUTPUT_TEXT_REQUIRED')
    return parts[0]


def inspect():
    manifest = read(RUN/'file_hashes.json')
    assert all(Path(n).name == n and not is_private_path(n) for n in manifest)
    hashes = {n: public_sha(RUN/n) == h for n, h in manifest.items()}
    raw = read(RUN/'inference_response_raw.json'); rec = read(RUN/'run_record.json')
    value = read(RUN/'validated_JSON.json'); req = read(RUN/'source_request.json')
    provenance = read(RUN/'source_provenance.json')
    Draft202012Validator(req['text']['format']['schema']).validate(value)
    assessed = scenario.assess(raw, 'S04'); saved = read(RUN/'technical_and_review_gates.json')
    ctx, payload, _, _ = scenario.context('S04'); bundle = ctx['bundle']
    docid = provenance['sources'][0]['document_id']
    document = next(x for x in bundle['documents'] if x['document_id'] == docid)
    extraction = next(x for x in bundle['extraction_runs'] if x['document_id'] == docid)
    engine = get_engine(); pages = []; quotes = []
    with engine.open(str(PDF)) as pdf:
        count = len(pdf); texts = {}
        for n in sorted({s['physical_page'] for s in payload['sources']}):
            text = pdf[n-1].get_text('text', sort=False, flags=extraction['extractor_options']['flags'])
            texts[n] = text
            frozen = next(p for p in bundle['pages'] if p['document_id'] == docid and p['page_number'] == n)
            pages.append({'physical_page': n, 'full_text_matches_frozen': text == frozen['text'],
                          'text_sha256': hashlib.sha256(text.encode()).hexdigest(), 'codepoints': len(text)})
        for s in payload['sources']:
            quotes.append({'quote_id': s['quote_id'], 'physical_page': s['physical_page'],
                'char_start': s['char_start'], 'char_end': s['char_end'],
                'exact_slice_matches': texts[s['physical_page']][s['char_start']:s['char_end']] == s['quote'],
                'quote_hash_matches': hashlib.sha256(s['quote'].encode()).hexdigest() == s['quote_sha256']})
    policy = read(budget.base.POLICY); config = read(budget.POLICY)
    use = raw['usage']; inp = use['input_tokens']; cached = use['input_tokens_details']['cached_tokens']
    out = use['output_tokens']; reasoning = use['output_tokens_details']['reasoning_tokens']
    prices = policy['prices_per_million_USD']
    ci = Decimal(inp-cached)*Decimal(prices['input'])/1000000
    cc = Decimal(cached)*Decimal(prices['cached_input'])/1000000
    co = Decimal(out)*Decimal(prices['output'])/1000000
    cost = ci+cc+co
    components = {'instructions_sha256': hashlib.sha256(req['instructions'].encode()).hexdigest(),
        'input_text_sha256': hashlib.sha256(req['input'][0]['content'][0]['text'].encode()).hexdigest(),
        'schema_sha256': hashlib.sha256(scenario.old.c.dump(req['text']['format']['schema']).encode()).hexdigest(),
        'quote_sha256': [x['quote_sha256'] for x in payload['sources']]}
    stages = [{'stage': n, **read(RUN/(n+'_HTTP_metadata.json'))}
              for n in ['model_access', 'input_token_count', 'inference']]
    ledger = budget.aggregate(policy); scope = read(RUN/'execution_scope.json')
    protected = config['protected_prior_public_files_sha256']
    controls = [read(p) for p in budget.CONTROL.glob('*.json')]
    count_raw = read(RUN/'input_token_count_response_raw.json')
    checks = {
        'run_hashes_and_inventory': all(hashes.values()) and
            {p.name for p in RUN.iterdir() if p.is_file()} == set(manifest)|{'file_hashes.json'},
        'raw_hash_matches_run_record': public_sha(RUN/'inference_response_raw.json') == rec['raw_response_sha256'] == RAW_HASH,
        'frozen_request_source_and_prompt': req == scenario.request('S04') and provenance == payload
            and req == read(scenario.QA/'S04_request_NOT_SENT.json'),
        'prompt_hash_and_scope': components == read(RUN/'prompt_components_sha256.json') and
            scope['source_request_sha256'] == public_sha(RUN/'source_request.json'),
        'raw_JSON_assessment_and_saved_JSON': parse_json(model_message(raw)) == value and assessed == saved,
        'schema_and_application': assessed['schema_status'] == 'PASS' and assessed['application_status'] == 'PASS',
        'completed_expected_model_no_error': raw['model'] == rec['model_returned'] == 'gpt-5.4-mini-2026-03-17'
            and raw['id'] == rec['response_id'] and raw['status'] == 'completed'
            and raw.get('error') is None and raw.get('incomplete_details') is None,
        'three_HTTP200_single_inference': [x['HTTP_status'] for x in stages] == [200,200,200]
            and rec['http_attempts'] == 3 and rec['inference_attempts'] == 1 and rec['automatic_retry'] is False
            and rec['API_request_id'] == stages[-1]['request_id'],
        'PDF_identity_and_page_count': public_sha(PDF) == document['raw_sha256'] and count == document['page_count'],
        'PDF_full_pages_and_ranges': all(x['full_text_matches_frozen'] for x in pages)
            and all(x['exact_slice_matches'] and x['quote_hash_matches'] for x in quotes),
        'original_extractor_version': engine.VersionBind == extraction['extractor_version'],
        'token_count_usage_and_limits': count_raw['input_tokens'] == inp and inp <= policy['input_token_cap']
            and out <= policy['max_output_tokens'] and 0 <= cached <= inp and 0 <= reasoning <= out
            and use['total_tokens'] == inp+out,
        'independent_cost_and_preflight': cost == Decimal(rec['usage_token_cost_USD']) and
            scenario.old.usage_cost(use, policy) == read(RUN/'usage_and_token_cost.json') and
            scenario.old.estimate_upper(count_raw['input_tokens'],policy) == read(RUN/'cost_preflight.json'),
        'prior_245_sources_unchanged': all(public_sha(ROOT/n) == h for n,h in protected.items()),
        'budget12_HTTP4_inference_092': ledger['HTTP_reservations_total'] == 12
            and ledger['inference_reservations_total'] == 4 and Decimal(ledger['reserved_USD']) == Decimal('.092')
            and ledger == read(RUN/'aggregate_budget_after_run.json') and ledger['within_limits'],
        'single_S04_scope_and_prior_stop_retained': len(list(budget.CONTROL.glob('S04_attempt*.json'))) == 1
            and len(list(budget.CONTROL.glob('inference_reservation*.json'))) == 1
            and len(list(budget.CONTROL.glob('http_*.json'))) == 3
            and all(x.get('run_directory') == str(RUN) for x in controls)
            and (budget.base.PRIOR_ROOTS[0]/'BILLING_OR_LIMIT_STOP.json').exists(),
        'human_pending_and_no_release': rec['human_review'] == assessed['human_review'] == 'PENDING'
            and rec['automatic_release'] is False and assessed['semantic_success'] is None,
        'no_GNN_or_tools': assessed['trusted_envelope']['predicted_by_GNN'] ==
            {'status':'NOT_REQUESTED_IN_WP12','artifact_ref':None} and raw['tools'] == [] and raw['service_tier'] == 'default',
    }
    prior = read(ROOT/'reports/qa/WP12/openai_S07_actual_review_v1/independent_review.json')
    return {'status': 'TECHNICAL_PASS_SOURCE_AND_LANGUAGE_NOTES_PENDING_HUMAN', 'checks': checks,
        'model': raw['model'], 'API_request_id': rec['API_request_id'], 'response_id': raw['id'],
        'HTTP_status': rec['HTTP_status'], 'completion_status': raw['status'],
        'latency_seconds': rec['latency_seconds'], 'usage': use, 'prices_per_million_USD': prices,
        'input_cost_USD': str(ci), 'cached_cost_USD': str(cc), 'output_cost_USD': str(co),
        'usage_token_cost_USD': str(cost),
        'known_completed_S01_S07_S04_token_cost_USD': str(Decimal(prior['known_completed_S01_plus_S07_token_cost_USD'])+cost),
        'pilot_total_invoice_cost': 'UNKNOWN_PRIOR_429_USAGE_AND_INVOICE_NOT_QUERIED',
        'schema_status': assessed['schema_status'], 'application_status': assessed['application_status'],
        'source_core_agent': 'UNKNOWN_FREQUENCY_AND_PAGE4_CONTEXT_RETAINED_WITH_QUALIFIER_NOTES',
        'Turkish_quality_agent': 'TURKISH_EXPLANATION_WITH_QUOTED_ENGLISH_MEDICAL_TERMS_AND_STYLE_NOTES',
        'human_review': 'PENDING', 'automatic_release': False, 'false_refusal_observed': False,
        'general_semantic_classifier': False, 'S01_fixed_sentence_validator_used': False,
        'method_or_criteria_changed_after_result': False,
        'RAM_VRAM_telemetry': 'NOT_COLLECTED', 'repeat_stability': 'NOT_EVALUABLE_SINGLE_S04_RESPONSE',
        'raw_files_verified': len(manifest), 'source_PDF_sha256': document['raw_sha256'], 'source_PDF_pages': count,
        'page_checks': pages, 'quote_checks': quotes, 'aggregate_budget': ledger, 'stages': stages,
        'exact_model_message': model_message(raw), 'parsed_json': value, 'new_API_requests_during_review': 0}


def agent_annotations(review):
    """Yalnız RAW_HASH ile sabitlenmiş gerçek cevaba ait insan olmayan ajan notları."""
    if public_sha(RUN/'inference_response_raw.json') != RAW_HASH:
        raise ValueError('ANNOTATION_BOUND_TO_ONE_RECORDED_RESPONSE')
    sources = {s['quote_id']: s for s in scenario.context('S04')[1]['sources']}
    notes = [
        ('SOURCE_CORE_SUPPORTED_WITH_UNSUPPORTED_TEMPORAL_WORD',
         'Yan etki olasılığı, herkesin yaşamayabileceği ve acil doktor iletişimi bağlamı korunuyor. Ancak “erken belirtiler” kaynakta yok: zamanlamaya ilişkin ek niteleme. Bu gözlem yeni yan etki saptaması değildir; kaynak sadakati notudur.'),
        ('SOURCE_SUPPORTED_WITH_QUALIFIER_AND_SUMMARY_OMISSION_NOTES',
         'Yan etki örnekleri ve bilinmeyen sıklık aynı p5 kaynağında. İşitme kaybı geri dönüşlü; yüksek doz/böbrek koşulu ve olabilirlik mevcut. “usually associated” → “özellikle ... görülebildiği” birebir değil: usually/genellikle açık aktarılmamış. İshalin şiddet/uzama/kan-mukus nitelemeleri, ayrı püstüloz uyarısı, çocuklar ve raporlama özette yok; bunlar kapsam eksiklikleridir. “daha ağır” karşılaştırmasının referansı kaynakta açık değil. Tinnitus/vertigo gibi terimler hasta dili bakımından ayrıca değerlendirilmeli.'),
        ('UNKNOWN_FREQUENCY_MEANING_SUPPORTED_WITH_STYLE_AND_OVERLAP_NOTES',
         'Mevcut verilerden sıklığın hesaplanamaması Türkçe açıklanmış; nadir/yaygın/yüzde veya kesin yokluk yapılmamış. İngilizce başlık/niteleme birebir alıntı olarak verilmiş, anlamı Türkçe açıklanıyor. “belirli bir oranlara” dilbilgisi sorunu. “tekrar” sözcüğü, aynı p5 metninin örtüşen alıntılarda bulunması nedeniyle bağımsız ikinci kanıt gibi okunmamalı.')]
    rows = []
    for i, (item, (status, note)) in enumerate(zip(review['parsed_json']['result']['items'],notes),1):
        source = sources[item['evidence_ids'][0]]
        rows.append({'item':i, 'primary_quote_id':source['quote_id'], 'physical_page':source['physical_page'],
            'scope':item['source_scope'], 'kind':item['statement_kind'], 'primary_quote_exact':source['quote'],
            'model_explanation_exact':item['explanation_tr'], 'all_cited_ids':item['evidence_ids'],
            'all_cited_quotes_exact':[sources[q]['quote'] for q in item['evidence_ids']],
            'source_qualifier_exact':source['qualifier'], 'agent_source_status':status, 'agent_note_tr':note,
            'raw_response_sha256':RAW_HASH, 'human_decision':'PENDING', 'reviewer_id':None, 'automatic_release':False})
    return rows
