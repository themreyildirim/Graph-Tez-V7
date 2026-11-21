"""Gerçek V2 yanıtı, kayıtlı şablon farkı, Qwen bellek kapıları. Ağ/inference yok."""
from pathlib import Path
import sys
import copy
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp12_source_case as c
import wp12_method_v2 as v
import wp12_gemma_v2_real_review as a
import wp12_registered_templates as go


class RealV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r=c.read(a.QA/'Gemma_V2_independent_review.json')
        cls.response=c.read(a.RUN/'source_response_raw.json')
        cls.req=c.read(a.RUN/'source_request.json')
    def test_01_real_raw_hashes_21_files(self):
        h=c.read(a.RUN/'file_hashes.json');self.assertEqual(len(h)+1,21)
        self.assertTrue(all(c.sha(a.RUN/p)==x for p,x in h.items()))
    def test_02_approved_request_unchanged(self):self.assertEqual(self.req,v.request_for_S01())
    def test_03_real_generation_completed(self):
        self.assertEqual((self.response['done'],self.response['done_reason']),(True,'stop'))
        self.assertEqual(self.r['transport_generation']['HTTP'],200)
    def test_04_server729_vs_offline724_preserved(self):
        self.assertEqual((self.r['transport_generation']['server_prompt_tokens'],self.r['transport_generation']['offline_planned_tokens']),(729,724))
        self.assertEqual(self.r['original_pipeline_status_preserved']['status'],'TOKEN_COUNT_ALIGNMENT_FAILED')
    def test_05_actual312_output_tokens_within_budget(self):self.assertEqual(self.response['eval_count'],312)
    def test_06_independent_schema_source_check_not_override(self):
        x=self.r['independent_posthoc_content_check'];self.assertTrue(x['schema_valid']);self.assertTrue(x['source_contract_valid'])
        self.assertIsNone(x['semantic_success'])
    def test_07_language_false_declaration(self):
        self.assertEqual(self.r['semantic_agent_review']['language'],'FAIL')
        self.assertTrue(self.r['semantic_agent_review']['language_declaration_tr_is_false_for_actual_sentence_language'])
    def test_08_heuristic_limit_visible(self):
        self.assertTrue(all(x['status']=='PENDING_HUMAN_LANGUAGE_REVIEW' for x in self.r['independent_posthoc_content_check']['language_checks']))
    def test_09_primary_quotes_and_purposes_correct(self):
        self.assertEqual(self.r['semantic_agent_review']['primary_quote_kind_alignment'],'PASS')
        self.assertEqual(self.r['independent_posthoc_content_check']['task_coverage'],'BOTH_SOURCE_PURPOSES_PRESENT')
    def test_10_B_reason_language_not_token_count(self):
        self.assertTrue(self.r['branch_B']['authorized']);self.assertIn('NOT because of token mismatch',self.r['branch_B']['reason'])
    def test_11_human_pending_no_automatic_release(self):
        self.assertEqual(self.r['semantic_agent_review']['human_review'],'PENDING');self.assertFalse(self.r['semantic_agent_review']['automatic_release'])
    def test_12_A_global_claim_preserved_and_no_retry(self):
        p=ROOT/'reports/qa/WP12/conditional_local_llm_v1/control/stage_A_generation_claim.json'
        self.assertEqual(c.sha(p),c.sha(a.RUN/'generation_claim_copy.json'))
    def test_13_actual_memory34_samples(self):
        m=self.r['memory'];self.assertEqual(m['samples'],34);self.assertGreaterEqual(m['sampled_min_RAM_GiB'],.75)
        self.assertEqual(m['OS_pressure_samples_true'],0)
    def test_14_Go_template_lex_trim(self):
        self.assertEqual(go.execute(' a \n{{- if .System }}X{{end -}} \n b',[]),' ab')
    def test_15_unknown_template_expressions_rejected(self):
        with self.assertRaises(ValueError):go.execute('{{ execute_unknown }}',[])
    def test_16_input_is_data_not_template_code(self):
        self.assertEqual(go.execute('{{range .Messages}}{{.Content}}{{end}}',[{'role':'user','content':'{{ unknown }}'}]),'{{ unknown }}')
    def test_17_range_variables_and_nested_conditions(self):
        t='{{range $i, $m := .Messages}}{{if eq $m.Role "user"}}{{$i}}:{{$m.Content}}{{end}}{{end}}'
        self.assertEqual(go.execute(t,[{'role':'system','content':'s'},{'role':'user','content':'u'}]),'1:u')
    def test_18_collate_and_system_separate(self):
        out=go.execute('{{.System}}|{{range .Messages}}{{.Role}}:{{.Content}};{{end}}',[{'role':'system','content':'s'},{'role':'user','content':'a'},{'role':'user','content':'b'}])
        self.assertEqual(out,'s|system:s;user:a\n\nb;')
    def test_19_Gemma_registered_template_two_user_turns(self):
        x=c.read(a.QA/'pure_template_reconstruction.json')
        self.assertEqual((x['Gemma_Go_user_turns'],x['Gemma_GGUF_user_turns']),(2,1))
    def test_20_Gemma_registered_render_manual_equivalence(self):
        actual=go.execute(a.registered_template(a.GEMMA_TEMPLATE),self.req['messages'])
        expected=''.join('<start_of_turn>user\n'+m['content']+'<end_of_turn>\n' for m in self.req['messages'])+'<start_of_turn>model\n'
        self.assertEqual(actual,expected)
    def test_21_Qwen_system_and_user_one_each(self):
        x=c.read(a.QA/'pure_template_reconstruction.json');self.assertEqual((x['Qwen_system_turns'],x['Qwen_user_turns']),(1,1))
    def test_22_template_native_count_unknown_not_invented(self):
        x=c.read(a.QA/'registered_template_token_diagnostics.json')
        self.assertEqual(x['status'],'BLOCKED_VOCAB_ONLY_RAM_GUARD');self.assertEqual(x['counts'],'UNKNOWN')
    def test_23_Qwen_local_digest_matches_historical(self):
        x=c.read(a.QA/'Qwen_cache_and_resource_assessment.json')
        self.assertEqual(x['local_registered_digest'],'sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0')
        self.assertTrue(x['historic_frozen_digest_matches'])
    def test_24_Qwen_hashes_and_dimensions_present(self):
        x=c.read(a.QA/'Qwen_cache_and_resource_assessment.json')
        self.assertEqual(x['model_bytes'],2497280480);self.assertEqual(x['architecture']['qwen3.block_count'],36)
        self.assertTrue(all(y['SHA_verified'] for y in x['layer_hashes']))
    def test_25_Qwen_full_FP16_KV_288MiB(self):
        x=c.read(a.QA/'Qwen_cache_and_resource_assessment.json');self.assertEqual(x['full_FP16_KV_bytes_at_2048'],288*2**20)
    def test_26_Qwen_separate_policy_not_Gemma_threshold_copy(self):
        x=c.read(ROOT/'configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json')
        self.assertEqual((x['RAM_floor_bytes'],x['GPU_floor_MiB'],x['commit_floor_bytes']),(3*2**30,3584,4*2**30))
        self.assertFalse(x['automatic_threshold_lowering']);self.assertFalse(x['execution_enabled'])
    def test_27_Qwen_host_ram_block_is_real(self):
        p=c.read(ROOT/'configs/WP12_QWEN4B_CONDITIONAL_MEMORY_v1.json')
        self.assertLess(p['current_RAM_bytes'],p['RAM_floor_bytes'])
    def test_28_Qwen_request_diff_only_model(self):
        q=c.read(a.QA/'Qwen_S01_v2_request_NOT_SENT.json');q['model']=self.req['model'];self.assertEqual(q,self.req)
    def test_29_old_V1_still_failed(self):
        import wp12_low_memory_run_review as old
        self.assertTrue(old.source_checks()['all_raw_hashes_valid'])
        s,_=old.structural_checks();self.assertFalse(s['application_contract_valid'])
    def test_30_no_network_in_diagnostic_content_check(self):
        with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
            self.assertTrue(v.inspect_candidate(__import__('json').loads(self.response['message']['content']))['schema_valid'])
    def test_31_original_pipeline_review_not_changed(self):
        original=c.read(a.RUN/'structural_review.json');self.assertEqual(original,self.r['original_pipeline_status_preserved'])
    def test_32_Qwen_state_NOT_RUN_and_19x3_closed(self):
        s=c.read(a.QA/'conditional_state_after_GemmaV2.json');self.assertEqual(s['B_actual_inference'],'NOT_RUN')
        self.assertEqual(s['Qwen_requests'],0);self.assertFalse(s['automatic_publication']);self.assertFalse(s['WP13'])


if __name__=='__main__':unittest.main(verbosity=2)
