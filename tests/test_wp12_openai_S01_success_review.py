"""Kaydedilmiş gerçek S01 üzerinde salt okunur kontroller; yeni inference yok."""
import sys
import socket
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S01_success_review as r


class SuccessReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK')):cls.result=r.inspect()

    def test_01_real_manifest_and_inventory(self):
        for k in ['run_hashes_all_match','run_inventory_matches_manifest','record_raw_and_prompt_hashes_match']:
            self.assertTrue(self.result['checks'][k])
        self.assertEqual(self.result['raw_files_verified'],20)

    def test_02_identical_request_across_accounts(self):
        self.assertTrue(self.result['checks']['same_source_request_as_first_failed_account_byte_for_byte'])
        self.assertTrue(self.result['checks']['frozen_request_and_source_unchanged'])

    def test_03_HTTP_completion_and_model(self):
        self.assertTrue(self.result['checks']['all_HTTP_200'])
        self.assertTrue(self.result['checks']['completed_expected_model'])

    def test_04_JSON_and_independent_schema_review(self):
        self.assertTrue(self.result['checks']['strict_parsed_raw_matches_saved_JSON'])
        self.assertTrue(self.result['checks']['independent_validator_matches_saved_review'])

    def test_05_PDF_hash_page_ranges_actual_source(self):
        for k in ['raw_PDF_identity_and_page_count','fresh_PDF_page_range_and_quote_hashes','extractor_version_matches_original']:
            self.assertTrue(self.result['checks'][k])
        self.assertEqual([x['physical_page'] for x in self.result['source_page_checks']],[1,6])

    def test_06_exact_token_usage_and_preflight(self):
        self.assertTrue(self.result['checks']['actual_usage_matches_server_preflight'])
        self.assertTrue(self.result['checks']['usage_within_input_output_caps'])
        u=self.result['usage'];self.assertEqual((u['input_tokens'],u['output_tokens'],u['total_tokens']),(1236,217,1453))

    def test_07_independent_cost_reasoning_cache(self):
        self.assertTrue(self.result['checks']['independent_Decimal_cost_matches_saved'])
        self.assertEqual(Decimal(self.result['usage_token_cost_USD']),Decimal('0.0019035'))
        self.assertEqual(self.result['usage']['input_tokens_details']['cached_tokens'],0)
        self.assertEqual(self.result['usage']['output_tokens_details']['reasoning_tokens'],0)

    def test_08_single_request_controls_and_budget(self):
        for k in ['one_inference_three_HTTP_no_retry','both_accounts_budget_retained','prior_billing_stop_and_new_single_attempt_lock_retained']:
            self.assertTrue(self.result['checks'][k])

    def test_09_no_tools_or_GNN_scores(self):self.assertTrue(self.result['checks']['no_tools_or_GNN_prediction'])

    def test_10_pending_human_is_not_auto_approval(self):
        self.assertTrue(self.result['checks']['human_and_release_gate_preserved'])
        self.assertEqual(self.result['human_review'],'PENDING');self.assertFalse(self.result['automatic_release'])

    def test_11_agent_annotations_cite_exact_items_only(self):
        rows=r.item_reviews(self.result)
        self.assertEqual(len(rows),2)
        self.assertEqual(sum(len(x['source_quote_exact']) for x in rows),537)
        self.assertTrue(all(x['human_decision']=='PENDING' and x['auto_release'] is False for x in rows))
        self.assertEqual([x['model_explanation_exact'] for x in rows],[x['explanation_tr'] for x in self.result['parsed_json']['result']['items']])

    def test_12_limits_single_case_and_missing_telemetry(self):
        self.assertEqual(self.result['repeat_stability'],'NOT_EVALUABLE_SINGLE_COMPLETED_RESPONSE')
        self.assertEqual(self.result['RAM_VRAM_telemetry'],'NOT_COLLECTED_FOR_API_RUN')
        self.assertEqual(len(self.result['source_omissions']),2)
        self.assertEqual(self.result['earlier_failed_request_actual_cost'],'UNKNOWN_NO_USAGE')


if __name__=='__main__':unittest.main(verbosity=2)
