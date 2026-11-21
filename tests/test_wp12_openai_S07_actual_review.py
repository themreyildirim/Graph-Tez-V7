"""Gerçek S07 dosyalarını değiştirmeyen testler; yeni API/optimizer yok."""
from pathlib import Path
from decimal import Decimal
import socket
import sys
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S07_actual_review as r


class RealReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK')):
            cls.data=r.inspect();cls.rows,cls.span=r.agent_annotations(cls.data)

    def test_01_hashes_inventory_and_prior_sources(self):
        for k in ['raw_run_hashes_match','run_inventory_matches_manifest','raw_response_hash_matches_record','all_prior_public_records_and_inputs_unchanged']:
            self.assertTrue(self.data['checks'][k])

    def test_02_request_prompt_scope_frozen(self):
        self.assertTrue(self.data['checks']['request_and_source_equal_frozen_S07'])
        self.assertTrue(self.data['checks']['prompt_components_and_execution_scope_hash_match'])

    def test_03_raw_to_schema_and_application(self):
        self.assertTrue(self.data['checks']['raw_JSON_matches_validated_and_independent_assessment'])
        self.assertEqual(self.data['schema_status'],'PASS');self.assertEqual(self.data['application_status'],'PASS')

    def test_04_real_PDF_full_pages_and_quote_slices(self):
        for k in ['raw_PDF_identity_and_page_count','PDF_full_pages_ranges_and_hashes','same_original_extractor']:
            self.assertTrue(self.data['checks'][k])
        self.assertEqual([p['physical_page'] for p in self.data['page_checks']],[4,7])

    def test_05_real_HTTP_completion_and_single_request(self):
        self.assertTrue(self.data['checks']['expected_completed_model'])
        self.assertTrue(self.data['checks']['three_HTTP_200_single_inference'])

    def test_06_exact_preflight_usage_and_caps(self):
        self.assertTrue(self.data['checks']['token_usage_matches_preflight_and_caps'])
        u=self.data['usage'];self.assertEqual((u['input_tokens'],u['output_tokens'],u['total_tokens']),(1962,504,2466))

    def test_07_independent_cost_cache_reasoning(self):
        self.assertTrue(self.data['checks']['independent_usage_cost_matches'])
        self.assertTrue(self.data['checks']['preflight_estimate_matches_frozen_policy'])
        self.assertEqual(Decimal(self.data['usage_token_cost_USD']),Decimal('.0037395'))
        self.assertEqual(self.data['usage']['input_tokens_details']['cached_tokens'],0)
        self.assertEqual(self.data['usage']['output_tokens_details']['reasoning_tokens'],0)

    def test_08_budget9_3_and_old_stop_retained(self):
        self.assertTrue(self.data['checks']['budget_9_HTTP_3_reservations_retained'])
        self.assertTrue(self.data['checks']['previous_stop_and_current_single_attempt_retained'])
        self.assertEqual(Decimal(self.data['aggregate_budget']['reserved_USD']),Decimal('.069'))

    def test_09_actual_English_phrase_is_not_rewritten(self):
        t=self.rows[2]['model_explanation_exact']
        self.assertEqual(t[self.span['char_start']:self.span['char_end']],'impaired renal function')
        self.assertEqual(self.data['Turkish_quality_agent'],'NOT_FULL_PASS_UNTRANSLATED_CRITICAL_CONDITION')
        self.assertTrue(self.span['gloss_is_not_modified_LLM_output'])

    def test_10_citation_note_does_not_retroactively_fail_schema(self):
        self.assertEqual(self.rows[1]['agent_source_status'],'CORE_CLASS_INTRO_SUPPORTED_CITATION_CONTEXT_NOTE')
        self.assertEqual(self.data['application_status'],'PASS')
        self.assertFalse(self.data['method_or_frozen_criteria_changed_after_result'])

    def test_11_semantic_language_and_human_are_separate(self):
        self.assertFalse(self.data['S01_fixed_sentence_validator_used'])
        self.assertTrue(all(x['human_decision']=='PENDING' for x in self.rows))
        self.assertTrue(self.data['checks']['human_and_no_release_gate_preserved'])
        self.assertEqual(self.data['human_review'],'PENDING')

    def test_12_no_GNN_predictions_and_S04_locked(self):
        self.assertTrue(self.data['checks']['no_GNN_or_tool_outputs'])
        self.assertTrue(self.data['checks']['S04_stays_execution_locked'])

    def test_13_exact_three_item_sources_preserved(self):
        self.assertEqual(len(self.rows),3)
        self.assertEqual(sum(len(x['primary_quote_exact']) for x in self.rows),380)
        self.assertEqual([len(x['all_cited_ids']) for x in self.rows],[3,1,1])

    def test_14_missing_telemetry_and_old_unknown_not_zero(self):
        self.assertEqual(self.data['RAM_VRAM_telemetry'],'NOT_COLLECTED')
        self.assertEqual(self.data['repeat_stability'],'NOT_EVALUABLE_SINGLE_S07_RESPONSE')
        self.assertEqual(self.data['pilot_total_invoice_cost'],'UNKNOWN_PRIOR_429_USAGE_AND_INVOICE_NOT_QUERIED')
        self.assertEqual(Decimal(self.data['known_completed_S01_plus_S07_token_cost_USD']),Decimal('.0056430'))


if __name__=='__main__':unittest.main(verbosity=2)
