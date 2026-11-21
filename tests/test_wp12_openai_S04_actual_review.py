"""Gerçek S04 teknik tutarlılığı; anlamsal başarı testi veya yeni API değildir."""
from pathlib import Path
from decimal import Decimal
from copy import deepcopy
import json
import socket
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S04_actual_review as r


class S04Actual(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(socket, 'socket', side_effect=AssertionError('NO_NETWORK')):
            cls.data = r.inspect(); cls.rows = r.agent_annotations(cls.data)

    def test_01_run_hashes_inventory(self):
        self.assertTrue(self.data['checks']['run_hashes_and_inventory'])
        self.assertTrue(self.data['checks']['raw_hash_matches_run_record'])

    def test_02_frozen_prompt_sources_and_scope(self):
        self.assertTrue(self.data['checks']['frozen_request_source_and_prompt'])
        self.assertTrue(self.data['checks']['prompt_hash_and_scope'])

    def test_03_raw_JSON_schema_application_recomputed(self):
        self.assertTrue(self.data['checks']['raw_JSON_assessment_and_saved_JSON'])
        self.assertTrue(self.data['checks']['schema_and_application'])

    def test_04_complete_expected_model_and_response_ID(self):
        self.assertTrue(self.data['checks']['completed_expected_model_no_error'])

    def test_05_single_inference_three_HTTP_and_request_ID(self):
        self.assertTrue(self.data['checks']['three_HTTP200_single_inference'])

    def test_06_PDF_identity_and_physical_pages(self):
        self.assertTrue(self.data['checks']['PDF_identity_and_page_count'])
        self.assertEqual([x['physical_page'] for x in self.data['page_checks']],[4,5])

    def test_07_full_pages_slices_and_original_extractor(self):
        self.assertTrue(self.data['checks']['PDF_full_pages_and_ranges'])
        self.assertTrue(self.data['checks']['original_extractor_version'])

    def test_08_exact_precount_usage_limits(self):
        self.assertTrue(self.data['checks']['token_count_usage_and_limits'])
        u=self.data['usage']
        self.assertEqual((u['input_tokens'],u['output_tokens'],u['total_tokens']),(2828,776,3604))

    def test_09_independent_cost_no_reasoning_double_count(self):
        self.assertTrue(self.data['checks']['independent_cost_and_preflight'])
        self.assertEqual(Decimal(self.data['usage_token_cost_USD']),Decimal('.005613'))
        self.assertEqual(self.data['usage']['input_tokens_details']['cached_tokens'],0)
        self.assertEqual(self.data['usage']['output_tokens_details']['reasoning_tokens'],0)

    def test_10_prior_245_files_and_12_4_ledger(self):
        self.assertTrue(self.data['checks']['prior_245_sources_unchanged'])
        self.assertTrue(self.data['checks']['budget12_HTTP4_inference_092'])
        self.assertTrue(self.data['checks']['single_S04_scope_and_prior_stop_retained'])

    def test_11_human_and_GNN_separation(self):
        self.assertTrue(self.data['checks']['human_pending_and_no_release'])
        self.assertTrue(self.data['checks']['no_GNN_or_tools'])
        self.assertTrue(all(x['human_decision']=='PENDING' for x in self.rows))

    def test_12_citation_order_primary_scope_kind(self):
        sources={x['quote_id']:x for x in r.scenario.context('S04')[1]['sources']}
        self.assertEqual([len(x['all_cited_ids']) for x in self.rows],[1,2,3])
        for row in self.rows:
            src=sources[row['all_cited_ids'][0]]
            self.assertEqual((row['scope'],row['kind']),(src['scope'],src['kind']))
            self.assertTrue(set(src['required_context_quote_ids']).issubset(row['all_cited_ids']))

    def test_13_exact_source_and_output_not_rewritten(self):
        self.assertEqual(sum(len(x['primary_quote_exact']) for x in self.rows),3803)
        items=self.data['parsed_json']['result']['items']
        self.assertEqual([x['model_explanation_exact'] for x in self.rows],[x['explanation_tr'] for x in items])
        self.assertEqual(r.public_sha(r.RUN/'inference_response_raw.json'),r.RAW_HASH)

    def test_14_manual_quality_notes_bound_to_observed_spans(self):
        self.assertIn('erken belirtiler',self.rows[0]['model_explanation_exact'])
        self.assertNotIn('early',self.rows[0]['primary_quote_exact'])
        self.assertIn('usually associated',self.rows[1]['primary_quote_exact'])
        self.assertIn('özellikle',self.rows[1]['model_explanation_exact'])
        self.assertIn('belirli bir oranlara',self.rows[2]['model_explanation_exact'])
        self.assertFalse(self.data['general_semantic_classifier'])

    def test_15_overlap_is_not_independent_evidence(self):
        p=r.scenario.context('S04')[1]['sources']
        self.assertEqual(len({x['document_id'] for x in p}),1)
        self.assertEqual(len({x['physical_page'] for x in p}),2)
        self.assertEqual(p[1]['quote'][p[2]['char_start']:p[2]['char_end']],p[2]['quote'])

    def test_16_unknown_billing_telemetry_and_stability_not_zero(self):
        self.assertEqual(self.data['RAM_VRAM_telemetry'],'NOT_COLLECTED')
        self.assertEqual(self.data['repeat_stability'],'NOT_EVALUABLE_SINGLE_S04_RESPONSE')
        self.assertEqual(self.data['pilot_total_invoice_cost'],'UNKNOWN_PRIOR_429_USAGE_AND_INVOICE_NOT_QUERIED')
        self.assertEqual(Decimal(self.data['known_completed_S01_S07_S04_token_cost_USD']),Decimal('.0112560'))

    def test_17_original_human_criteria_not_tuned(self):
        plan=r.read(r.budget.QA/'human_review_plan_S04.json')
        self.assertEqual(plan['frozen_plan'],r.scenario.semantic_plan('S04'))
        self.assertFalse(self.data['S01_fixed_sentence_validator_used'])
        self.assertFalse(self.data['method_or_criteria_changed_after_result'])

    def test_18_wrong_meaning_correct_ID_cannot_be_semantic_PASS(self):
        # TEST_ONLY mutation in memory: no model response or source file is changed.
        raw=deepcopy(r.read(r.RUN/'inference_response_raw.json'))
        val=deepcopy(self.data['parsed_json'])
        val['result']['items'][2]['explanation_tr']='TEST_ONLY: Bu yan etkiler kesin olarak yaygındır.'
        for m in raw['output']:
            for c in m.get('content',[]):
                if c.get('type')=='output_text':c['text']=json.dumps(val,ensure_ascii=False)
        result=r.scenario.assess(raw,'S04')
        self.assertEqual(result['schema_status'],'PASS')
        self.assertEqual(result['application_status'],'PASS')
        self.assertIsNone(result['semantic_success'])
        self.assertEqual(result['human_review'],'PENDING')
        self.assertFalse(result['automatic_release'])


if __name__=='__main__':unittest.main(verbosity=2)
