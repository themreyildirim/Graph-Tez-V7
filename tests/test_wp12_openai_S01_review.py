"""Gerçek kullanıcı kaydında ağsız, değiştirmeyen inceleme testleri."""
import sys
import socket
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S01_review as r


class Review(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK')):
            cls.data=r.inspect()

    def test_run_and_manifest_integrity(self):
        self.assertTrue(self.data['checks']['run_file_hashes_all_match'])
        self.assertTrue(self.data['checks']['run_manifest_matches_file_inventory'])
        self.assertEqual(self.data['raw_run_files_verified'],11)

    def test_original_sources_and_prompt(self):
        for k in ['run_request_hash_matches_record','prompt_component_hashes_match','frozen_source_and_request_equal']:
            self.assertTrue(self.data['checks'][k])

    def test_preparation_and_dependencies_preserved(self):
        self.assertTrue(self.data['checks']['prepared_public_artifacts_unchanged'])
        self.assertTrue(self.data['checks']['policy_public_dependencies_unchanged'])

    def test_exact_HTTP_stages(self):self.assertEqual([x['HTTP_status'] for x in self.data['stages']],[200,200,429])

    def test_specific_credit_error_not_rate_or_model_quality(self):
        self.assertEqual(self.data['provider_error']['code'],'credit_balance_exhausted')
        self.assertEqual(self.data['provider_error']['type'],'insufficient_quota')
        self.assertEqual(self.data['classification'],'API_BILLING_BLOCKED_NO_MODEL_OUTPUT')

    def test_single_attempt_no_generated_output(self):
        self.assertEqual(self.data['inference_attempts'],1)
        self.assertEqual(self.data['completed_generations'],0)
        self.assertTrue(self.data['checks']['no_generated_explanation_or_usage'])

    def test_count_is_preflight_not_billed_usage(self):
        self.assertEqual(self.data['input_token_preflight_count'],1236)
        self.assertIsNone(self.data['actual_billed_input_tokens'])
        self.assertIsNone(self.data['actual_usage_token_cost_USD'])
        self.assertTrue(self.data['checks']['preflight_count_and_cost_match'])

    def test_semantic_review_not_imputed(self):
        for k in ['schema_status','Turkish_quality','source_faithfulness']:
            self.assertEqual(self.data[k],'NOT_EVALUABLE_NO_OUTPUT')
        self.assertEqual(self.data['generated_model_snapshot'],'UNKNOWN_NO_GENERATED_RESPONSE')

    def test_slots_and_guard_not_reset(self):
        for k in ['one_recorded_inference_attempt','three_HTTP_attempts','billing_guard_retained','automatic_retry_off','no_automatic_release']:
            self.assertTrue(self.data['checks'][k])
        self.assertFalse(self.data['retry_or_guard_reset'])


if __name__=='__main__':unittest.main(verbosity=2)
