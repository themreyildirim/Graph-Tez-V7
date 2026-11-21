"""Koşullu plan + gerçek yürütücü saf kontrolleri. Hiçbir inference yapılmaz."""
from pathlib import Path
import copy
import sys
import unittest
from unittest.mock import patch
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp12_source_case as c
import wp12_method_v2 as v
import wp12_gemma_v2_user_run as r


class ConditionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg=c.read(r.CONFIG);cls.ps=(ROOT/cls.cfg['runner']).read_text(encoding='utf-8')
        cls.proof=c.read(v.QA/'v2_actual_token_proof.json')
    def fixture(self):
        return {'schema_version':v.VERSION,'language':'tr','status':'candidate','refusal_code':None,
            'items':[{'explanation_tr':'Bu yalnız bir teknik test cümlesidir; model yanıtı değildir.',
                'source_scope':s['scope'],'statement_kind':s['kind'],'evidence_ids':[s['quote_id']]}
                for s in v.verified_S01_context()['sources']]}
    def response(self,x=None):
        return {'model':'gemma3:1b-it-q4_K_M','done':True,'done_reason':'stop','prompt_eval_count':724,
            'eval_count':100,'message':{'content':c.dump(self.fixture() if x is None else x)}}
    def test_01_frozen_method_inputs_hash(self):
        for p,h in self.cfg['immutable_inputs_sha256'].items():self.assertEqual(c.sha(ROOT/p),h,p)
        self.assertEqual(c.sha(ROOT/self.cfg['runner']),self.cfg['runner_sha256'])
    def test_02_exact_accepted_request_and_schema(self):
        self.assertEqual(v.request_for_S01(),c.read(v.QA/'S01_request_v2_PROPOSED_NOT_SENT.json'))
        self.assertEqual(v.case_schema(),c.read(v.QA/'S01_case_schema_v2_PROPOSED.json'))
    def test_03_one_HTTP_generation_site(self):self.assertEqual(self.ps.count('.PostAsync('),1)
    def test_04_atomic_project_wide_slot(self):
        self.assertIn('[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None',self.ps)
        self.assertIn('stage_A_generation_claim.json',self.ps)
        self.assertLess(self.ps.index('$claimFile ='),self.ps.index('.PostAsync('))
    def test_05_second_invocation_gate_before_API(self):
        self.assertLess(self.ps.index('STOP_STAGE_A_SINGLE_ATTEMPT_ALREADY_CLAIMED_NO_API'),self.ps.index("Read-LocalMetadata 'version'"))
    def test_06_AppContainer_before_API(self):
        self.assertLess(self.ps.index('STOP_APPContainer_NO_API_ATTEMPT'),self.ps.index("Read-LocalMetadata 'version'"))
    def test_07_no_force_reset_download_or_privilege(self):
        for key in ['Stop-Process','Set-ExecutionPolicy','Start-Service','/api/pull','ollama pull','-Verb RunAs','[switch]$Force','Remove-Item']:
            self.assertNotIn(key,self.ps)
    def test_08_memory_policy_unchanged(self):
        policy=c.read(ROOT/self.cfg['hardware_policy_reference'])
        for key in ['RAM_floor_bytes','GPU_floor_MiB','commit_floor_bytes','runtime_RAM_floor_bytes','runtime_commit_floor_bytes','HTTP_timeout_seconds']:
            self.assertEqual(self.cfg[key],policy[key])
    def test_09_runtime_all_three_warning_conditions(self):
        self.assertIn('if ($sample.available_bytes -lt 805306368 -or $sample.commit_available_bytes -lt 1073741824 -or $sample.low_memory_notification)',self.ps)
    def test_10_technical_valid_fixture_still_human_pending(self):
        x=r.assess_response(self.response(),self.proof)
        self.assertEqual((x['technical_status'],x['schema_status'],x['application_status']),('PASS','PASS','PASS'))
        self.assertEqual(x['language_quality'],'PENDING');self.assertEqual(x['source_faithfulness'],'PENDING_AGENT_AND_HUMAN_REVIEW')
        self.assertIsNone(x['semantic_success']);self.assertFalse(x['automatic_release'])
    def test_11_refused_nonempty_fails(self):
        x=self.fixture();x.update(status='refused',refusal_code='IMAGE_TEXT_UNAVAILABLE')
        result=r.assess_response(self.response(x),self.proof)
        self.assertEqual(result['schema_status'],'FAIL');self.assertEqual(result['application_status'],'FAIL')
    def test_12_wrong_kind_fails(self):
        x=self.fixture();x['items'][0]['statement_kind']='formulation'
        self.assertEqual(r.assess_response(self.response(x),self.proof)['schema_status'],'FAIL')
    def test_13_English_quality_failure_separate(self):
        x=self.fixture();x['items'][0]['explanation_tr']='The provided text does not contain information about this product.'
        result=r.assess_response(self.response(x),self.proof)
        self.assertEqual(result['technical_status'],'PASS');self.assertEqual(result['language_quality'],'FAIL')
    def test_14_missing_task_purpose_failure(self):
        x=self.fixture();x['items']=x['items'][:1]
        result=r.assess_response(self.response(x),self.proof)
        self.assertEqual(result['application_status'],'FAIL');self.assertEqual(result['task_coverage'],'TASK_COVERAGE_INCOMPLETE')
    def test_15_token_mismatch_is_technical_not_semantic(self):
        x=self.response();x['prompt_eval_count']=723;result=r.assess_response(x,self.proof)
        self.assertEqual(result['technical_status'],'FAIL');self.assertEqual(result['application_status'],'NOT_EVALUABLE')
    def test_16_wrong_model_or_incomplete(self):
        for k,value in [('model','other'),('done_reason','length'),('done',False),('eval_count',385)]:
            x=self.response();x[k]=value;self.assertEqual(r.assess_response(x,self.proof)['technical_status'],'FAIL')
    def test_17_duplicate_key_or_NaN_fail_JSON(self):
        for text in ['{"status":"candidate","status":"refused"}','{"x":NaN}']:
            x=self.response();x['message']['content']=text
            self.assertEqual(r.assess_response(x,self.proof)['status'],'V2_JSON_SYNTAX_FAIL')
    def test_18_no_network_in_assessment(self):
        with patch('socket.socket',side_effect=AssertionError('NO_NETWORK')):
            self.assertEqual(r.assess_response(self.response(),self.proof)['technical_status'],'PASS')
    def test_19_wait_A_when_not_run(self):self.assertEqual(r.next_action(),'WAIT_USER_STAGE_A_RUN')
    def test_20_technical_no_response_does_not_trigger_quality_fallback(self):
        self.assertEqual(r.next_action(technical='FAIL'),'REPORT_TECHNICAL_BLOCK_QUALITY_NOT_EVALUABLE')
        self.assertEqual(r.next_action(True,'FAIL',schema='FAIL'),'REPORT_TECHNICAL_BLOCK_QUALITY_NOT_EVALUABLE')
    def test_21_any_completed_quality_failure_authorizes_B_prep(self):
        for key in ['schema','application','language','source','task']:
            self.assertEqual(r.next_action(True,'PASS',**{key:'FAIL'}),'PREPARE_QWEN_WITH_SEPARATE_MEMORY_AND_IDENTITY_AUDIT')
    def test_22_no_automatic_human_acceptance(self):
        self.assertEqual(r.next_action(True,'PASS','PASS','PASS'),'REVIEW_ACTUAL_RESPONSE_AND_WAIT_HUMAN_SEMANTIC_DECISION')
    def test_23_even_human_pass_stops_before_19x3(self):
        self.assertEqual(r.next_action(True,'PASS','PASS','PASS','PASS','PASS','PASS','PASS'),'PRESENT_SINGLE_CASE_RESULTS_STOP_BEFORE_19X3')
    def test_24_conditional_plan_no_download_no_threshold_copy(self):
        p=c.read(ROOT/'configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json')
        self.assertFalse(p['stage_B']['copy_Gemma_low_memory_thresholds']);self.assertFalse(p['stage_B']['download'])
        self.assertFalse(p['stage_B']['automatic_threshold_reduction']);self.assertFalse(p['WP13'])
    def test_25_claim_not_consumed_by_preparation(self):self.assertFalse((ROOT/self.cfg['generation_slot']).exists())
    def test_26_old_actual_run_remains_failed(self):
        import wp12_low_memory_run_review as a
        self.assertTrue(a.source_checks()['all_raw_hashes_valid'])
        x,_=a.structural_checks();self.assertFalse(x['application_contract_valid'])
    def test_27_request_before_single_slot(self):
        self.assertLess(self.ps.index('SOURCE_REQUEST_HASH_MISMATCH'),self.ps.index('$claimFile ='))
        self.assertLess(self.ps.index('STOP_MEMORY_GATE_RECHECK'),self.ps.index('$claimFile ='))
    def test_28_failed_HTTP_raw_retained_before_review(self):
        self.assertLess(self.ps.index("Save-Text 'source_response_raw.json' $body"),self.ps.index("throw 'SOURCE_HTTP_ERROR"))
    def test_29_generation_budget_unchanged(self):
        self.assertEqual(v.request_for_S01()['options'],{'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108,'num_batch':32})
        self.assertEqual(self.proof['input_token_count'],724)
    def test_30_no_active_B_runner_or_batch_switch(self):
        self.assertIn('param([switch]$RunFirstCase)',self.ps)
        self.assertNotIn('qwen3:',self.ps);self.assertFalse(self.cfg['automatic_retry'])


if __name__=='__main__':unittest.main(verbosity=2)
