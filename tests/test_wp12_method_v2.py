"""V2 öneri testleri; fixture'lar teknik testtir, gerçek model açıklaması değildir."""
from pathlib import Path
import copy
import hashlib
import json
import sys
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp12_method_v2 as v
import wp12_source_case as old
from wp12_vocab_counter import template_from_gguf
from jsonschema import Draft202012Validator


class MethodV2Tests(unittest.TestCase):
    def candidate(self):
        return {'schema_version':v.VERSION,'language':'tr','status':'candidate','refusal_code':None,
            'items':[{'explanation_tr':'Bu yalnız bir teknik test cümlesidir; model çıktısı değildir.',
                'source_scope':s['scope'],'statement_kind':s['kind'],'evidence_ids':[s['quote_id']]}
                for s in v.verified_S01_context()['sources']]}
    def valid_generic(self,value):return Draft202012Validator(v.generic_schema()).is_valid(value)
    def test_01_proposed_schema_metaschema(self):
        Draft202012Validator.check_schema(v.generic_schema());Draft202012Validator.check_schema(v.case_schema())
        self.assertEqual(v.generic_schema(),old.read(v.SCHEMA))
        self.assertEqual(v.case_schema(),old.read(v.QA/'S01_case_schema_v2_PROPOSED.json'))
        self.assertEqual(v.request_for_S01(),old.read(v.QA/'S01_request_v2_PROPOSED_NOT_SENT.json'))
    def test_02_candidate_nonempty_valid(self):self.assertTrue(self.valid_generic(self.candidate()))
    def test_03_candidate_empty_invalid(self):
        x=self.candidate();x['items']=[];self.assertFalse(self.valid_generic(x))
    def test_04_candidate_nonnull_refusal_invalid(self):
        x=self.candidate();x['refusal_code']='NO_SOURCE';self.assertFalse(self.valid_generic(x))
    def test_05_refused_empty_valid_generic(self):
        x=self.candidate();x.update(status='refused',refusal_code='NO_SOURCE',items=[])
        self.assertTrue(self.valid_generic(x))
    def test_06_refused_nonempty_invalid_generic(self):
        x=self.candidate();x.update(status='refused',refusal_code='NO_SOURCE')
        self.assertFalse(self.valid_generic(x))
    def test_07_refused_null_invalid_generic(self):
        x=self.candidate();x.update(status='refused',items=[]);self.assertFalse(self.valid_generic(x))
    def test_08_wrong_language_declaration_invalid(self):
        x=self.candidate();x['language']='en';self.assertFalse(self.valid_generic(x))
    def test_09_extra_prediction_field_invalid(self):
        x=self.candidate();x['predicted_by_GNN']={'score':.8};self.assertFalse(self.valid_generic(x))
    def test_10_S01_image_refusal_not_eligible(self):
        x=self.candidate();x.update(status='refused',refusal_code='IMAGE_TEXT_UNAVAILABLE',items=[])
        self.assertFalse(Draft202012Validator(v.case_schema()).is_valid(x))
        self.assertEqual(v.S01_refusal_policy()['model_allowed_refusal_codes'],[])
    def test_11_source_kind_ID_coupling(self):
        x=self.candidate();x['items'][0]['statement_kind']='formulation'
        self.assertFalse(v.inspect_candidate(x)['schema_valid'])
    def test_12_scope_promotion_rejected(self):
        x=self.candidate();x['items'][0]['source_scope']='drug_direct'
        self.assertFalse(v.inspect_candidate(x)['schema_valid'])
    def test_13_unselected_ID_rejected(self):
        x=self.candidate();x['items'][0]['evidence_ids']=['invented'];self.assertFalse(v.inspect_candidate(x)['schema_valid'])
    def test_14_language_observed_English_flag(self):
        text="The provided text does not contain any information about the product's form or formulation."
        self.assertEqual(v.language_screen(text)['status'],'OBVIOUS_NON_TURKISH')
    def test_15_ASCII_Turkish_not_required_to_have_accents(self):
        r=v.language_screen('Bu ilac tablet olarak sunulur.');self.assertEqual(r['status'],'PENDING_HUMAN_LANGUAGE_REVIEW')
        self.assertFalse(r['automatic_success'])
    def test_16_limited_screen_false_negative_still_not_success(self):
        r=v.language_screen('Pink capsules exist.')
        self.assertEqual(r['status'],'PENDING_HUMAN_LANGUAGE_REVIEW');self.assertTrue(r['human_required'])
    def test_17_valid_fixture_never_auto_semantic_pass(self):
        x=v.inspect_candidate(self.candidate());self.assertTrue(x['schema_valid']);self.assertTrue(x['source_contract_valid'])
        self.assertIsNone(x['semantic_success']);self.assertFalse(x['automatic_release'])
    def test_18_obvious_English_with_correct_schema_rejected(self):
        x=self.candidate();x['items'][0]['explanation_tr']='The provided text does not contain information about this product.'
        r=v.inspect_candidate(x);self.assertTrue(r['schema_valid']);self.assertIn('OBVIOUS_NON_TURKISH',r['errors'])
    def test_19_one_item_incomplete_task_flag(self):
        x=self.candidate();x['items']=x['items'][:1]
        r=v.inspect_candidate(x);self.assertTrue(r['schema_valid']);self.assertEqual(r['task_coverage'],'TASK_COVERAGE_INCOMPLETE')
    def test_20_new_fact_with_valid_ID_not_misrepresented_as_proven(self):
        x=self.candidate();x['items'][0]['explanation_tr']='Bu kaynakta olmayan bir iddiadır.'
        r=v.inspect_candidate(x);self.assertIsNone(r['semantic_success']);self.assertEqual(r['human_review'],'PENDING')
    def test_21_original_19_scenarios_frozen(self):
        p=ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'
        self.assertEqual(old.sha(p),'6b17f8c306c5c39c70e5a160ab001bdb2ceff2b5b5fbbab7bda2d762cf22e73b')
        self.assertEqual(len(old.read(p)),19)
    def test_22_full_source_context_in_user_message(self):
        req=v.request_for_S01();data=json.loads(req['messages'][1]['content']);ctx=v.verified_S01_context()
        self.assertEqual(data['sources'],ctx['sources']);self.assertEqual(sum(len(x['quote']) for x in data['sources']),537)
        self.assertEqual(data['question_tr'],ctx['scenario']['question_tr'])
        self.assertEqual(data['acceptance_criteria_tr'],ctx['scenario']['acceptance_criteria_tr'])
    def test_23_source_mutation_rejected(self):
        ctx=v.verified_S01_context();ctx=copy.deepcopy(ctx);ctx['sources'][0]['quote']+='changed'
        with self.assertRaises(ValueError):v.S01_refusal_policy(ctx)
    def test_24_BUN_and_class_dependencies_untouched(self):
        ctx=old.context('S07');ann={a['key']:a for a in ctx['annotations']}
        self.assertIn(ann['D_BUN_exception']['quote_id'],ctx['scenario']['evidence_ids'])
    def test_25_system_role_and_instruction_explicit(self):
        req=v.request_for_S01();self.assertEqual([x['role'] for x in req['messages']],['system','user'])
        self.assertIn('Her explanation_tr cümlesi Türkçe olmalı',req['messages'][0]['content'])
        self.assertIn('IMAGE_TEXT_UNAVAILABLE kullanma',req['messages'][0]['content'])
    def test_26_model_and_generation_settings_preserved(self):
        new=v.request_for_S01();prior=old.read(old.QA/'package/request.json')
        for key in ['model','options','stream','think','keep_alive','truncate','shift']:self.assertEqual(new[key],prior[key])
    def test_27_memory_policy_unchanged(self):
        plan=old.read(ROOT/'configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json')
        p=old.read(ROOT/plan['hardware_policy_reference'])
        self.assertEqual(old.sha(ROOT/plan['hardware_policy_reference']),plan['hardware_policy_sha256'])
        for key in ['RAM_floor_bytes','GPU_floor_MiB','commit_floor_bytes','runtime_RAM_floor_bytes','runtime_commit_floor_bytes','HTTP_timeout_seconds']:
            self.assertEqual(plan[key],p[key])
    def test_28_future_max_one_not_started(self):
        p=old.read(ROOT/'configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json')
        self.assertEqual((p['max_future_generation_attempts'],p['actual_new_generation_attempts']),(1,0))
        self.assertTrue(p['user_approval_required_before_execution']);self.assertFalse(p['all19x3_enabled'])
    def test_29_no_network_in_pure_validator(self):
        with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
            self.assertTrue(v.inspect_candidate(self.candidate())['source_contract_valid'])
    def test_30_exact_token_proof_and_repeatability(self):
        x=old.read(v.QA/'v2_actual_token_proof.json');tests=old.read(v.QA/'tokenizer_tests.json')
        self.assertEqual(x['input_token_count'],724);self.assertTrue(x['admitted'])
        self.assertTrue(tests['repeat_identical']);self.assertEqual((tests['old_real_smoke_count'],tests['old_S01_count']),(41,919))
    def test_31_oversized_prompt_not_cut(self):
        x=old.read(v.QA/'tokenizer_tests.json')
        self.assertEqual(x['oversized_status'],'CONTEXT_BUDGET');self.assertTrue(x['test_suffix_intact'])
    def test_32_system_template_hash_bound_to_prompt(self):
        p=old.read(v.QA/'v2_actual_token_proof.json')
        rendered=v.render_request(v.request_for_S01(),template_from_gguf()['tokenizer.chat_template'])
        self.assertEqual(hashlib.sha256(rendered.encode()).hexdigest(),p['rendered_prompt_sha256'])
    def test_33_historical_failed_run_preserved_and_still_failed(self):
        import wp12_low_memory_run_review as a
        self.assertTrue(a.source_checks()['all_raw_hashes_valid'])
        s,_=a.structural_checks();self.assertFalse(s['application_contract_valid'])
        self.assertEqual(s['application_error'],'invalid refusal')
    def test_34_original_actual_reply_cannot_pass_v2(self):
        import wp12_low_memory_run_review as a
        response=old.read(a.RUN/'source_response_raw.json');candidate=json.loads(response['message']['content'])
        self.assertFalse(self.valid_generic(candidate)) # Asıl veri değiştirilmez; v1 başarılı ilan edilmez.
        adapted=copy.deepcopy(candidate);adapted['schema_version']=v.VERSION;adapted['language']='tr'
        self.assertFalse(self.valid_generic(adapted)) # Sürüm uyarlansa da refused+items artık geçmez.
    def test_35_trusted_envelope_not_prediction(self):
        r=v.inspect_candidate(self.candidate());e=r['trusted_envelope']
        self.assertEqual(e['predicted_by_GNN']['status'],'NOT_REQUESTED_IN_WP12');self.assertIsNone(e['predicted_by_GNN']['artifact_ref'])
        self.assertFalse(e['semantic_review']['auto_release'])
    def test_36_no_fake_example_answer_in_prompt(self):
        req=v.request_for_S01();self.assertNotIn('TEKNİK TEST',req['messages'][0]['content'])
        self.assertNotIn('explanation_tr',json.loads(req['messages'][1]['content']))


if __name__=='__main__':unittest.main(verbosity=2)
