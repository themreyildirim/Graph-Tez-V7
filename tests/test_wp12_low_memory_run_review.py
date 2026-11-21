"""Gerçek S01-R1 kaydının ağsız bağımsız inceleme testleri; inference yok."""
from pathlib import Path
import copy
import json
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp12_low_memory_run_review as a
import wp12_source_case as c


class ActualRunReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.audit=a.audit();cls.res=c.read(a.RUN/'source_response_raw.json')
        cls.candidate=json.loads(cls.res['message']['content'])

    def test_01_all17_raw_files_and16_manifest_entries(self):
        self.assertEqual((self.audit['source']['raw_files'],self.audit['source']['manifest_entries']),(17,16))
        self.assertTrue(self.audit['source']['all_raw_hashes_valid'])
    def test_02_exact_model_digest(self):
        self.assertEqual(self.audit['source']['API_digest'],'sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c')
    def test_03_wrapper_and_source_are_separate_objects(self):
        r=c.read(a.RUN/'run_record.json')['identity_validation']
        self.assertNotEqual(r['local_wrapper_manifest_file_sha256'],r['source_manifest_file_sha256'])
        self.assertTrue(self.audit['source']['wrapper_and_source_manifest_independently_valid'])
    def test_04_real_generation_completed(self):
        t=self.audit['technical'];self.assertTrue(t['model_produced_nonempty_response'])
        self.assertEqual((t['HTTP_status'],t['done'],t['done_reason']),(200,True,'stop'))
    def test_05_exact_tokens_and_no_length_stop(self):
        t=self.audit['technical'];self.assertEqual((t['prompt_tokens'],t['output_tokens'],t['prompt_cached_tokens']),(919,188,0))
        self.assertFalse(t['token_truncation_evidence'])
    def test_06_JSON_schema_pass_does_not_imply_contract_pass(self):
        s=self.audit['structural'];self.assertTrue(s['case_JSON_Schema_valid']);self.assertTrue(s['v1_JSON_Schema_valid'])
        self.assertFalse(s['application_contract_valid']);self.assertEqual(s['application_error'],'invalid refusal')
    def test_07_refusal_contains_claim(self):
        self.assertTrue(self.audit['structural']['refused_with_nonempty_items'])
    def test_08_kind_does_not_match_cited_quote(self):
        x=self.audit['structural']['item_checks'][0]
        self.assertTrue(x['selected_real_quote']);self.assertTrue(x['source_scope_matches_primary'])
        self.assertFalse(x['statement_kind_matches_primary'])
        self.assertEqual((x['output_kind'],x['cited_quote_kind']),('formulation','identity'))
    def test_09_message_is_exact_original(self):
        self.assertEqual((a.QA/'model_message_content_exact.txt').read_text(encoding='utf-8'),self.res['message']['content'])
    def test_10_no_model_Turkish_explanation(self):
        s=self.audit['semantic'];self.assertIsNone(s['actual_Turkish_model_explanation'])
        self.assertTrue(s['exact_explanation_field'].startswith('The provided text'))
    def test_11_translation_is_separately_labeled(self):
        self.assertIn('reviewer_Turkish_translation_NOT_MODEL_OUTPUT',self.audit['semantic'])
    def test_12_formulation_absence_claim_is_contradicted(self):
        row=next(x for x in self.audit['semantic']['findings'] if x['topic']=='formülasyon')
        self.assertEqual(row['status'],'CONTRADICTED')
    def test_13_identity_and_active_ingredient_omitted(self):
        for topic in ['ürün','etkin_madde']:
            row=next(x for x in self.audit['semantic']['findings'] if x['topic']==topic)
            self.assertEqual(row['status'],'OMITTED')
    def test_14_original_PDF_pages_spans_and_hash(self):
        rows=a.verify_pdf_pages();self.assertEqual([x['page'] for x in rows],[1,6])
        self.assertTrue(all(x['source_span_matches_original_PDF'] for x in rows))
        self.assertIn('enteric-coated',rows[1]['quote'])
    def test_15_entry_gate_and_stability(self):
        m=self.audit['memory'];self.assertTrue(m['entry_gates_passed'])
        self.assertEqual(m['stable_sample_count'],5);self.assertGreaterEqual(m['stable_span_seconds'],4)
    def test_16_runtime_samples_do_not_violate_experimental_policy(self):
        m=self.audit['memory'];self.assertEqual(m['runtime_sample_count'],37)
        self.assertGreaterEqual(m['sampled_RAM_min_GiB'],.75)
        self.assertGreaterEqual(m['sampled_commit_min_GiB'],1)
        self.assertEqual(m['OS_low_memory_signal_true_count'],0)
    def test_17_GPU_peak_and_unsampled_memory_remain_UNKNOWN(self):
        m=self.audit['memory'];self.assertIn('UNKNOWN',m['runtime_GPU_peak'])
        self.assertEqual(m['system_unsampled_RAM_min'],'UNKNOWN');self.assertFalse(m['safety_guarantee'])
    def test_18_saved_validation_reproduced_without_writing_run(self):
        before={p.name:c.sha(p) for p in a.RUN.iterdir() if p.is_file()}
        a.structural_checks()
        self.assertEqual(before,{p.name:c.sha(p) for p in a.RUN.iterdir() if p.is_file()})
    def test_19_no_network_for_audit(self):
        with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
            self.assertEqual(a.audit(),self.audit)
    def test_20_human_approval_pending_and_no_publication(self):
        self.assertEqual(self.audit['semantic']['human_semantic_review'],'PENDING')
        self.assertFalse(self.audit['semantic']['approved_or_publishable'])
        self.assertIsNone(self.audit['structural']['original_semantic_success'])
    def test_21_single_attempt_and_no_download_record(self):
        self.assertEqual((self.audit['source']['recorded_attempts'],self.audit['source']['new_downloads_recorded']),(1,0))
    def test_22_model_failure_cause_not_guessed(self):
        self.assertIn('UNKNOWN',self.audit['technical']['root_cause_of_model_content_error'])
    def test_23_only_recommendation_no_57_calls(self):
        self.assertIn('DO_NOT_START_19x3',self.audit['semantic']['next_stage_recommendation'])
    def test_24_frozen_dependencies_and_prompt_unchanged(self):
        self.assertTrue(self.audit['source']['request_and_frozen_context_equal'])
        self.assertEqual(c.context('S01')['scenario']['source_characters'],537)
    def test_25_mutated_label_not_reclassified_as_success(self):
        # Yalnız RAM içi test; gerçek yanıtı/yöntemi düzeltmez.
        x=copy.deepcopy(self.candidate);x['status']='candidate';x['refusal_code']=None
        res=copy.deepcopy(self.res);res['message']['content']=c.dump(x)
        result=c.validate_response(res,c.context(),c.read(a.RUN/'token_budget.json'))
        self.assertFalse(result['structural_valid']) # kind/id uyuşmazlığı da yakalanır.


if __name__=='__main__':unittest.main(verbosity=2)
