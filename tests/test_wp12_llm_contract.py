"""Gerçek 44 alıntıyla teknik sözleşme testleri; hiçbir aday LLM çıktısı değildir."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import wp12_llm_contract as c


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle, cls.annotations = c.load_sources()
        cls.by_key = {a['key']: a for a in cls.annotations}

    def fixture(self, key='E_identity'):
        a = self.by_key[key]
        ids = [a['quote_id']] + sorted(c.dependencies(self.annotations)[a['quote_id']])
        candidate = {'schema_version': c.VERSION, 'status': 'candidate', 'refusal_code': None,
                     'items': [{'explanation_tr': 'TEKNİK TEST ADAYI; gerçek açıklama değildir.',
                                'source_scope': a['attribution_scope'], 'statement_kind': a['purpose'],
                                'evidence_ids': ids}]}
        return candidate, ids

    def validate(self, value, ids, **kw):
        return c.validate_candidate(value, allowed_ids=ids, bundle=self.bundle,
                                    annotations=self.annotations, **kw)

    def test_01_all44_exact_spans(self):
        q, p, a = c.source_index(self.bundle, self.annotations)
        self.assertEqual((len(q), len(p), len(a)), (44, 17, 44))

    def test_02_pending_not_semantic_pass(self):
        x, ids = self.fixture()
        self.assertIn('PENDING_HUMAN', self.validate(x, ids))

    def test_03_missing_evidence(self):
        x, ids = self.fixture(); x['items'][0]['evidence_ids'] = []
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_04_unknown_evidence(self):
        x, ids = self.fixture(); x['items'][0]['evidence_ids'] = ['invented']
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_05_unselected_real_evidence(self):
        x, ids = self.fixture()
        with self.assertRaises(ValueError): self.validate(x, [self.by_key['D_identity']['quote_id']])

    def test_06_no_model_branch(self):
        x, ids = self.fixture(); x['predicted_by_GNN'] = {'score': .9}
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_07_no_model_or_label_fields(self):
        for field in ['model_score', 'SHAP', 'delta_z', 'new_side_effect', 'MedDRA_label']:
            with self.subTest(field=field):
                x, ids = self.fixture(); x['items'][0][field] = 'forbidden'
                with self.assertRaises(ValueError): self.validate(x, ids)

    def test_08_class_scope_not_direct(self):
        x, ids = self.fixture('D_class_GI'); x['items'][0]['source_scope'] = 'drug_direct'
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_09_class_context_required(self):
        x, ids = self.fixture('D_class_GI'); x['items'][0]['evidence_ids'] = ids[:1]
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_10_renal_exception_required(self):
        x, ids = self.fixture('D_class_renal')
        self.assertIn(self.by_key['D_BUN_exception']['quote_id'], ids)
        x['items'][0]['evidence_ids'].remove(self.by_key['D_BUN_exception']['quote_id'])
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_11_warning_not_adverse_event(self):
        x, ids = self.fixture('D_teeth'); x['items'][0]['statement_kind'] = 'invented_adverse_event'
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_12_exact_wrapper_citations(self):
        x, ids = self.fixture('D_class_renal')
        y = c.build_review_envelope(x, allowed_ids=ids, bundle=self.bundle, annotations=self.annotations)
        q = {q['quote_id']: q for q in self.bundle['quotes']}
        for cite in y['reported_in_PDF'][0]['citations']:
            self.assertEqual(cite['source_sentence'], q[cite['quote_id']]['quote'])
            self.assertEqual(cite['page_number'], q[cite['quote_id']]['page_number'])
        self.assertIsNone(y['predicted_by_GNN']['artifact_ref'])
        self.assertFalse(y['semantic_review']['auto_release'])

    def test_13_no_evidence_no_summary(self):
        x, _ = self.fixture()
        with self.assertRaises(ValueError): self.validate(x, [])

    def test_14_forbidden_tasks(self):
        for task in ['prediction', 'shap', 'delta_z', 'meddra_label', 'clinical_risk']:
            x, ids = self.fixture()
            with self.subTest(task=task), self.assertRaises(ValueError): self.validate(x, ids, task=task)

    def test_15_refusal_contains_no_claim(self):
        x = {'schema_version': c.VERSION, 'status': 'refused', 'refusal_code': 'NO_SOURCE', 'items': []}
        self.assertEqual(self.validate(x, []), 'REFUSED_NO_EXPLANATION')

    def test_16_forged_refusal_rejected(self):
        x, ids = self.fixture(); x['status'] = 'refused'; x['refusal_code'] = 'NO_SOURCE'
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_17_source_tampering_rejected(self):
        b = copy.deepcopy(self.bundle); b['quotes'][0]['page_number'] += 1
        with self.assertRaises(AssertionError): c.source_index(b, self.annotations)
        b = copy.deepcopy(self.bundle); b['quotes'][0]['quote'] += 'changed'
        with self.assertRaises(AssertionError): c.source_index(b, self.annotations)

    def test_18_reproducibility_and_no_mutation(self):
        x, ids = self.fixture(); before = json.dumps(self.bundle, sort_keys=True)
        a = c.build_review_envelope(x, allowed_ids=ids, bundle=self.bundle, annotations=self.annotations)
        b = c.build_review_envelope(x, allowed_ids=ids, bundle=self.bundle, annotations=self.annotations)
        self.assertEqual(a, b); self.assertEqual(before, json.dumps(self.bundle, sort_keys=True))

    def test_19_hallucination_not_automatically_released(self):
        x, ids = self.fixture(); x['items'][0]['explanation_tr'] = 'Kaynakta bulunmayan bir ifade.'
        # Yapısal geçişin semantik doğruluk OLMADIĞINI açıkça sınar.
        self.assertIn('PENDING_HUMAN', self.validate(x, ids))

    def test_20_inference_disabled(self):
        with self.assertRaises(RuntimeError): c.infer()

    def test_21_no_network_or_process(self):
        with patch('socket.socket', side_effect=AssertionError('network forbidden')), \
             patch('subprocess.Popen', side_effect=AssertionError('process forbidden')):
            x, ids = self.fixture(); self.validate(x, ids)

    def test_22_duplicates_rejected(self):
        x, ids = self.fixture(); x['items'][0]['evidence_ids'] *= 2
        with self.assertRaises(ValueError): self.validate(x, ids)

    def test_23_schema_alignment(self):
        stored = json.loads((ROOT/'docs/schemas/WP12_local_llm_candidate_v1.schema.json').read_text(encoding='utf-8'))
        self.assertEqual(stored, c.schema(self.annotations))

    def test_24_quotes_not_modified_by_dependencies(self):
        before = copy.deepcopy(self.annotations); c.dependencies(self.annotations)
        self.assertEqual(before, self.annotations)


if __name__ == '__main__':
    unittest.main(verbosity=2)
