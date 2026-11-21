"""Tamamen offline: sentetik transport yanıtları gerçek API sonucu değildir."""
import copy
import io
import json
import re
import socket
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import wp12_openai_adapter as a
import wp12_openai_client as client
import wp12_api_security as security
from jsonschema import Draft202012Validator

DUMMY='TEST_ONLY_NOT_A_REAL_API_KEY_0123456789'


def candidate():
    sources=a.source_payload()['sources']
    return {'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'candidate',
        'refusal_code':None,'language':'tr','items':[
            {'explanation_tr':'Prospektüs bu ürünü eritromisin tablet olarak tanımlar.',
             'source_scope':'product_identity','statement_kind':'identity','evidence_ids':[sources[0]['quote_id']]},
            {'explanation_tr':'Kaynakta etkin madde ve tablet formülasyonu belirtilmektedir.',
             'source_scope':'product_identity','statement_kind':'formulation','evidence_ids':[sources[1]['quote_id']]}]}}


def response():
    return {'id':'resp_TEST_ONLY','model':'gpt-5.4-mini-2026-03-17','status':'completed',
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(candidate(),ensure_ascii=False)}]}],
        'usage':{'input_tokens':1000,'input_tokens_details':{'cached_tokens':200},
                 'output_tokens':400,'output_tokens_details':{'reasoning_tokens':100}}}


class Offline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.policy=json.loads(a.POLICY.read_text(encoding='utf-8'))

    def setUp(self):
        # Hiçbir test ağ açamaz; perform() için send açıkça enjekte edilir.
        self.no_network=patch.object(socket,'socket',side_effect=AssertionError('NETWORK_FORBIDDEN_IN_OFFLINE_TEST'))
        self.no_network.start()
        self.temp=tempfile.TemporaryDirectory(prefix='wp12_api_test_',dir=a.QA)
        self.tmp=Path(self.temp.name).resolve()
        self.assertTrue(self.tmp.is_relative_to(a.QA.resolve()))

    def tearDown(self):
        # Windows recursive cleanup yalnız doğrulanmış test klasöründe.
        assert self.tmp.is_relative_to(a.QA.resolve()) and self.tmp.name.startswith('wp12_api_test_')
        self.temp.cleanup();self.no_network.stop()

    def run_fake(self,responses):
        folder=self.tmp/'run';folder.mkdir()
        calls=[]
        def fake(method,path,payload,key):
            calls.append((method,path))
            value=responses[len(calls)-1]
            if isinstance(value,BaseException):raise value
            return {'HTTP_status':value.get('HTTP_status',200),'body':json.dumps(value.get('body',{})),
                    'request_id':'req_TEST_ONLY','elapsed_seconds':0.01}
        with patch.object(client,'CONTROL',self.tmp/'control'):
            record=client.perform(folder,DUMMY,self.policy,send=fake)
        return record,calls,folder

    def success_chain(self):
        return [{'body':{'id':a.MODEL}},{'body':{'input_tokens':1000}},{'body':response()}]

    def test_01_sources_real_two_pages_and_hashes(self):
        p=a.source_payload();self.assertEqual(p['DrugBank_parent_id'],'DB00199')
        self.assertEqual([x['physical_page'] for x in p['sources']],[1,6])
        import hashlib
        texts=[]
        for source in p['sources']:
            text=source['quote'];texts.append(text)
            self.assertEqual(len(text),source['char_end']-source['char_start'])
            self.assertEqual(hashlib.sha256(text.encode()).hexdigest(),source['quote_sha256'])
        self.assertEqual(sum(map(len,texts)),537)

    def test_02_frozen_sources_and_scenarios_hashes(self):
        for path,digest in self.policy['immutable_public_inputs_sha256'].items():
            self.assertEqual(security.public_sha(ROOT/path),digest,path)
        self.assertEqual(len(json.loads((ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json').read_text(encoding='utf-8'))),19)

    def test_03_schema_subset_closed_required_objects(self):
        schema=a.api_schema();Draft202012Validator.check_schema(schema)
        self.assertEqual(schema['type'],'object');self.assertNotIn('anyOf',schema)
        def visit(node):
            if isinstance(node,list):
                for x in node:visit(x)
            elif isinstance(node,dict):
                self.assertFalse(set(node)&{'oneOf','allOf','not','if','then','else','const','uniqueItems'})
                if node.get('type')=='object':
                    self.assertIs(node['additionalProperties'],False)
                    self.assertEqual(set(node['properties']),set(node['required']))
                for x in node.values():visit(x)
        visit(schema)

    def test_04_adapter_preserves_v2_candidate_semantics(self):
        good=candidate();Draft202012Validator(a.api_schema()).validate(good)
        Draft202012Validator(a.v.case_schema()).validate(good['result'])
        for change in ['empty','wrong_id','wrong_kind','extra','false_refusal']:
            bad=copy.deepcopy(good)
            if change=='empty':bad['result']['items']=[]
            if change=='wrong_id':bad['result']['items'][0]['evidence_ids']=['quote:UNKNOWN_TEST_ONLY']
            if change=='wrong_kind':bad['result']['items'][0]['statement_kind']='warning'
            if change=='extra':bad['result']['invented_score']=1
            if change=='false_refusal':bad['result']['status']='refused'
            self.assertFalse(Draft202012Validator(a.api_schema()).is_valid(bad),change)

    def test_05_request_no_tools_no_truncation_no_storage(self):
        r=a.build_request()
        self.assertEqual(r['tools'],[]);self.assertEqual(r['tool_choice'],'none')
        self.assertEqual(r['reasoning'],{'effort':'none'})
        self.assertEqual(r['max_output_tokens'],1200);self.assertEqual(r['truncation'],'disabled')
        self.assertFalse(r['store']);self.assertFalse(r['background']);self.assertFalse(r['stream'])
        self.assertNotIn('Authorization',json.dumps(r))
        payload=json.loads(r['input'][0]['content'][0]['text'])
        self.assertEqual(payload,a.source_payload());self.assertNotIn('C:\\',json.dumps(payload))

    def test_06_exact_count_payload_contains_same_sources_schema(self):
        r=a.build_request();count=a.token_count_payload(r)
        self.assertEqual(count['input'],r['input']);self.assertEqual(count['text'],r['text'])
        self.assertNotIn('max_output_tokens',count)

    def test_07_cost_upper_at_input_cap(self):
        bound=a.estimate_upper(6000,self.policy)
        self.assertEqual(Decimal(bound['worst_case_no_cache_USD']),Decimal('.0099'))
        self.assertEqual(Decimal(bound['margin_upper_USD']),Decimal('.01188'))
        self.assertFalse(bound['cached_discount_assumed'])
        for n in [6001,None,-1,0,True]:
            with self.assertRaises(ValueError):a.estimate_upper(n,self.policy)

    def test_08_actual_cache_cost_reasoning_not_double_counted(self):
        cost=a.usage_cost(response()['usage'],self.policy)
        self.assertEqual(Decimal(cost['actual_token_cost_USD']),Decimal('.002415'))
        self.assertTrue(cost['reasoning_not_double_counted'])

    def test_09_missing_and_invalid_billing_stops(self):
        for usage in [None,{}, {'input_tokens':1,'output_tokens':1},
                      {'input_tokens':1,'output_tokens':1,'input_tokens_details':{'cached_tokens':2}}]:
            self.assertIsNone(a.usage_cost(usage,self.policy)['actual_token_cost_USD'])
        usage=response()['usage'];usage['input_tokens_details']['cache_write_tokens']=10
        self.assertEqual(a.usage_cost(usage,self.policy)['status'],'UNPRICED_CACHE_WRITE_STOP')

    def test_10_total_reserved_budget_below_quarter_dollar(self):
        reserve=Decimal(self.policy['reservation_per_inference_USD'])*10+Decimal(self.policy['reservation_per_HTTP_USD'])*10
        self.assertEqual(reserve,Decimal('.21'));self.assertLess(reserve,Decimal('.25'))

    def test_11_success_fake_chain_one_inference_not_semantic_approval(self):
        record,calls,folder=self.run_fake(self.success_chain())
        self.assertEqual(calls,[('GET','/models/gpt-5.4-mini'),('POST','/responses/input_tokens'),('POST','/responses')])
        self.assertEqual(record['inference_attempts'],1)
        self.assertEqual(record['status'],'PENDING_SOURCE_AND_HUMAN_REVIEW')
        review=json.loads((folder/'structural_and_language_review.json').read_text(encoding='utf-8'))
        self.assertIsNone(review['semantic_success']);self.assertFalse(review['automatic_release'])
        self.assertEqual(review['human_review'],'PENDING')

    def test_12_count_over_cap_never_infers(self):
        chain=self.success_chain();chain[1]['body']['input_tokens']=6001
        record,calls,_=self.run_fake(chain)
        self.assertEqual(len(calls),2);self.assertEqual(record['inference_attempts'],0)

    def test_13_timeout_does_not_retry_or_echo_exception(self):
        chain=self.success_chain();chain[2]=TimeoutError(DUMMY)
        record,calls,folder=self.run_fake(chain)
        self.assertEqual(len(calls),3);self.assertEqual(record['status'],'FAILED_STOP_NO_RETRY')
        self.assertTrue((self.tmp/'control/BILLING_OR_LIMIT_STOP.json').exists())
        self.assertNotIn(DUMMY,(folder/'run_record.json').read_text(encoding='utf-8'))

    def test_14_HTTP_error_redacts_secret_message(self):
        record,calls,folder=self.run_fake([{'HTTP_status':401,'body':{'error':{'message':DUMMY,'code':'invalid_api_key'}}}])
        self.assertEqual(len(calls),1);self.assertEqual(record['inference_attempts'],0)
        self.assertFalse((folder/'model_access_response_raw.json').exists())
        safe=(folder/'model_access_error_redacted.json').read_text(encoding='utf-8')
        self.assertNotIn(DUMMY,safe);self.assertIn('invalid_api_key',safe)

    def test_15_secret_tainted_success_body_never_saved(self):
        chain=self.success_chain();chain[2]['body']['unexpected_echo']=DUMMY
        _,_,folder=self.run_fake(chain)
        self.assertFalse((folder/'inference_response_raw.json').exists())

    def test_16_S01_global_attempt_cannot_repeat(self):
        _,_,_=self.run_fake(self.success_chain())
        folder=self.tmp/'run2';folder.mkdir()
        with patch.object(client,'CONTROL',self.tmp/'control'):
            record=client.perform(folder,DUMMY,self.policy,send=lambda *args:self.fail('NO_SECOND_API'))
        self.assertEqual(record['http_attempts'],0)

    def test_17_atomic_HTTP_and_inference_slot_limits(self):
        for stem in ['http','inference_reservation']:
            for n in range(1,11):self.assertEqual(client.claim_slot(self.tmp,stem,10,{'TEST_ONLY':True}),n)
            with self.assertRaises(ValueError):client.claim_slot(self.tmp,stem,10,{})

    def test_18_incomplete_or_native_refusal_kept_separate(self):
        r=response();r['status']='incomplete'
        self.assertEqual(a.assess_response(r)['status'],'INCOMPLETE_OR_FAILED_NO_RETRY')
        r=response();r['output'][0]['content']=[{'type':'refusal','refusal':'TEST_ONLY'}]
        self.assertEqual(a.assess_response(r)['status'],'API_NATIVE_REFUSAL_RECORDED_NO_RETRY')

    def test_19_wrong_model_and_duplicate_JSON_rejected(self):
        r=response();r['model']='UNAPPROVED_TEST_ONLY'
        self.assertEqual(a.assess_response(r)['status'],'UNEXPECTED_MODEL_VERSION_STOP')
        r=response();r['output'][0]['content'][0]['text']='{"result":{},"result":{}}'
        self.assertEqual(a.assess_response(r)['schema_status'],'FAIL')
        for value in ['{"x":1,"x":2}','{"x":NaN}']:
            with self.assertRaises(ValueError):client.parse_json(value)

    def test_20_schema_pass_not_language_or_faithfulness_pass(self):
        r=response();data=candidate();data['result']['items'][0]['explanation_tr']='The product contains erythromycin tablets.'
        r['output'][0]['content'][0]['text']=json.dumps(data)
        check=a.assess_response(r)
        self.assertEqual(check['schema_status'],'PASS');self.assertEqual(check['Turkish_quality'],'FAIL')
        self.assertEqual(check['source_faithfulness'],'PENDING_AGENT_AND_HUMAN_REVIEW')

    def test_21_environment_precedence_dotenv_no_interpolation(self):
        (self.tmp/'.env').write_text('OPENAI_API_KEY='+DUMMY+'\nOTHER_SECRET=NEVER_LOAD\n',encoding='utf-8')
        env={'OPENAI_API_KEY':'TEST_ONLY_ENV_KEY_abcdefghijkl'}
        self.assertEqual(security.load_key(self.tmp,env),env['OPENAI_API_KEY'])
        self.assertEqual(security.load_key(self.tmp,{}),DUMMY)
        self.assertNotIn('OTHER_SECRET',env)
        (self.tmp/'.env').write_text('OPENAI_API_KEY=TEST_ONLY_${SHOULD_NOT_EXPAND}\n',encoding='utf-8')
        self.assertIn('${SHOULD_NOT_EXPAND}',security.load_key(self.tmp,{}))

    def test_22_missing_or_header_injection_key_no_value_output(self):
        self.assertIsNone(security.load_key(self.tmp,{}))
        self.assertIsNone(security.load_key(self.tmp,{'OPENAI_API_KEY':DUMMY+'\nInjected: invalid'}))
        with patch('dotenv.dotenv_values',side_effect=ValueError(DUMMY)):
            stream=io.StringIO()
            with redirect_stdout(stream):self.assertIsNone(security.load_key(self.tmp,{}))
            self.assertEqual(stream.getvalue(),'')

    def test_23_private_file_rejected_before_open_or_hash(self):
        for name in ['.env','.env.dev','.env.local','.env_backup','credentials.json','secrets.json','x.pem','.aws/file']:
            self.assertTrue(security.is_private_path(self.tmp/name))
            with patch.object(Path,'open',side_effect=AssertionError('MUST_NOT_READ')):
                with self.assertRaises(ValueError):security.public_sha(self.tmp/name)

    def test_24_secret_and_headers_not_written_to_evidence(self):
        e=security.Evidence(self.tmp,DUMMY)
        for text in [DUMMY,'{"Authorization":"not_a_real_header"}','Bearer TEST_ONLY']:
            with self.assertRaises(security.SecretBlocked):e.text('blocked.json',text)
            self.assertFalse((self.tmp/'blocked.json').exists())
        self.assertIsNone(security.safe_request_id(DUMMY,DUMMY))
        self.assertIsNone(security.safe_request_id('bad\nheader',DUMMY))

    def test_25_gitignore_rules_and_tracked_secret_detection_synthetic(self):
        (self.tmp/'.gitignore').write_bytes((ROOT/'.gitignore').read_bytes())
        subprocess.run(['git','init','--quiet',str(self.tmp)],check=True,capture_output=True)
        for name in ['.env','.env.dev','.env.local','nested/.env.local','credentials-test.json','test.pem']:
            result=subprocess.run(['git','-C',str(self.tmp),'check-ignore',name],capture_output=True)
            self.assertEqual(result.returncode,0,name)
        (self.tmp/'.env').write_text('TEST_ONLY_NO_REAL_KEY',encoding='utf-8')
        subprocess.run(['git','-C',str(self.tmp),'add','-f','.env'],check=True,capture_output=True)
        self.assertTrue(security.git_privacy_state(self.tmp)['tracked_private_files_detected'])

    def test_26_invalid_cli_argument_never_echoed(self):
        p=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/wp12_openai_client.py'),'--'+DUMMY],capture_output=True,text=True)
        self.assertNotEqual(p.returncode,0);self.assertNotIn(DUMMY,p.stdout+p.stderr)

    def test_27_no_real_API_ledger_slots(self):
        self.assertFalse(list(client.CONTROL.glob('http_*.json')))
        self.assertFalse(list(client.CONTROL.glob('inference_reservation_*.json')))
        self.assertFalse(list(client.CONTROL.glob('S01_attempt_*.json')))

    def test_28_plan_is_frozen_four_cases_no_implicit_execution(self):
        plan=json.loads((a.QA/'small_evaluation_plan_NOT_AUTHORIZED.json').read_text(encoding='utf-8'))
        self.assertEqual([x['scenario_id'] for x in plan['frozen_scenarios_unchanged']],['S01','S04','S07','S17'])
        self.assertEqual(plan['HTTP_plan_if_all_preflights_pass']['total'],9)
        self.assertTrue(self.policy['further_scenarios_require_user_review_of_first_result'])

    def test_29_expired_prices_stop_before_network(self):
        p=copy.deepcopy(self.policy);p['pricing_valid_until_UTC']='2000-01-01T00:00:00+00:00'
        with patch.object(client.c,'read',return_value=p),patch.object(client,'git_privacy_state',return_value={'tracked_private_files_detected':False}):
            with self.assertRaisesRegex(ValueError,'PRICE_SNAPSHOT_EXPIRED'):client.verify_policy()

    def test_30_safe_error_reason_never_echoes_unknown_secret(self):
        self.assertEqual(client.safe_reason(ValueError(DUMMY)),'UNCLASSIFIED_EXCEPTION_NO_DETAILS_LOGGED')
        self.assertEqual(client.safe_reason(ValueError('INPUT_TOKEN_CAP_STOP_NO_INFERENCE')),'INPUT_TOKEN_CAP_STOP_NO_INFERENCE')

    def test_31_budget_configuration_tamper_stops(self):
        p=copy.deepcopy(self.policy);p['max_inference_requests']=11
        with patch.object(client.c,'read',return_value=p):
            with self.assertRaisesRegex(ValueError,'HARD_BUDGET'):client.verify_policy()

    def test_32_model_access_failure_never_infers(self):
        record,calls,_=self.run_fake([{'body':{'id':'OTHER_TEST_ONLY'}}])
        self.assertEqual(len(calls),1);self.assertEqual(record['inference_attempts'],0)
        self.assertEqual(record['failure_reason'],'MODEL_ACCESS_NOT_CONFIRMED')

    def test_33_predicted_GNN_field_never_generated(self):
        check=a.assess_response(response())['validation']['trusted_envelope']
        self.assertIn('reported_in_PDF',check);self.assertIn('predicted_by_GNN',check)
        self.assertNotIn('score',json.dumps(candidate()))

    def test_34_HTTP_quota_exhaustion_does_not_claim_inference_sent(self):
        control=self.tmp/'control'
        for n in range(8):client.claim_slot(control,'http',10,{'TEST_ONLY':True})
        record,calls,_=self.run_fake(self.success_chain())
        self.assertEqual(len(calls),2);self.assertEqual(record['inference_attempts'],0)
        self.assertEqual(record['failure_reason'],'REQUEST_OR_BUDGET_SLOT_LIMIT_STOP')
        self.assertFalse((control/'BILLING_OR_LIMIT_STOP.json').exists())

    def test_35_AppContainer_stops_before_key_load_and_network(self):
        stream=io.StringIO()
        with patch.object(sys,'argv',['wp12_openai_client','--run-first-case']),patch.object(client,'is_appcontainer',return_value=True),patch.object(client,'load_key',side_effect=AssertionError('NO_KEY_LOAD')),redirect_stdout(stream):
            code=client.main()
        self.assertNotEqual(code,0);self.assertIn('APPCONTAINER_STOP_NO_API',stream.getvalue())


if __name__=='__main__':unittest.main(verbosity=2)
