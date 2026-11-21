"""Frozen S04 tek-istek yürütümü; TEST_ONLY transport, ağ ve gerçek key yok."""
from pathlib import Path
import contextlib
import io
import json
import socket
import sys
import tempfile
import unittest
from decimal import Decimal
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S04_v1_client as client
import wp12_openai_S04_execution_v1 as b
from wp12_api_security import public_sha

DUMMY='TEST_ONLY_NOT_PROVIDER_CREDENTIAL_012345'


def response():
    _,payload,_,_=client.s.context('S04')
    value={'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'candidate','refusal_code':None,'language':'tr',
        'items':[{'explanation_tr':'TECHNICAL_FIXTURE_NOT_MODEL_OUTPUT','source_scope':s['scope'],'statement_kind':s['kind'],
            'evidence_ids':[s['quote_id'],*s['required_context_quote_ids']]} for s in payload['sources']]}}
    return {'id':'resp_TEST_ONLY','model':'gpt-5.4-mini-2026-03-17','status':'completed',
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(value)}]}],
        'usage':{'input_tokens':3500,'input_tokens_details':{'cached_tokens':0},'output_tokens':400,'output_tokens_details':{'reasoning_tokens':0}}}


class S04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.policy={**client.s.old.c.read(b.base.POLICY),'execution_scope_version':'WP12-S04-single-execution-v1'}

    def setUp(self):
        self.net=patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK'));self.net.start()
        self.temp=tempfile.TemporaryDirectory(prefix='S04_test_',dir=b.QA);self.tmp=Path(self.temp.name).resolve()
        self.assertTrue(self.tmp.is_relative_to(b.QA.resolve()));self.prior=self.tmp/'prior';self.prior.mkdir();self.scope=self.tmp/'scope'
        for i in range(1,10):self.write(self.prior/f'http_{i:02d}.json',{'extra_budget_guard_USD':'0.001'})
        for i in range(1,4):self.write(self.prior/f'inference_reservation_{i:02d}.json',{'reserved_USD':'0.02'})
        self.write(self.prior/'S07_attempt_01.json',{'status':'COMPLETED_TEST_ONLY'})
        self.before={p.name:public_sha(p) for p in self.prior.iterdir()}
        self.patches=[patch.object(b.base,'PRIOR_ROOTS',[self.prior]),patch.object(b.base,'CONTROL',self.tmp/'prior_S07_empty'),
            patch.object(b,'CONTROL',self.scope),patch.object(b,'verify',return_value=self.policy)]
        for p in self.patches:p.start()

    def tearDown(self):
        self.assertEqual({p.name:public_sha(p) for p in self.prior.iterdir()},self.before)
        for p in reversed(self.patches):p.stop()
        assert self.tmp.is_relative_to(b.QA.resolve()) and self.tmp.name.startswith('S04_test_')
        self.temp.cleanup();self.net.stop()

    def write(self,path,data):path.write_text(json.dumps(data),encoding='utf-8')

    def run_fake(self,chain=None):
        folder=self.tmp/('run'+str(len(list(self.tmp.glob('run*')))));folder.mkdir()
        chain=[{'id':'gpt-5.4-mini'},{'input_tokens':3500},response()] if chain is None else chain
        calls=[]
        def send(method,path,payload,key):
            calls.append((method,path,payload));value=chain[len(calls)-1]
            if isinstance(value,BaseException):raise value
            code=value.pop('_HTTP',200)
            return {'HTTP_status':code,'body':json.dumps(value),'request_id':'req_TEST_ONLY','elapsed_seconds':.01}
        return client.perform(folder,DUMMY,self.policy,send),calls,folder

    def test_01_frozen_request_bytes_prompt_schema_source(self):
        _,calls,folder=self.run_fake()
        frozen=client.s.QA/'S04_request_NOT_SENT.json'
        self.assertEqual((folder/'source_request.json').read_text(encoding='utf-8'),
            json.dumps(client.s.old.c.read(frozen),ensure_ascii=False,indent=2,allow_nan=False))
        self.assertEqual(calls[-1][2],client.s.old.c.read(frozen))
        self.assertEqual(calls[-1][2]['instructions'],client.s.request('S04')['instructions'])

    def test_02_three_sources_and_page4_transitive_closure(self):
        _,p,_,_=client.s.context('S04');p4,p5,unknown=p['sources']
        self.assertEqual(sum(len(x['quote']) for x in p['sources']),3803)
        self.assertEqual(set(unknown['required_context_quote_ids']),{p4['quote_id'],p5['quote_id']})
        self.assertIn('Not known (frequency cannot be estimated',unknown['quote'])

    def test_03_prior_9_HTTP_3_inference_and_069_reserve(self):
        state=b.aggregate(self.policy)
        self.assertEqual((state['HTTP_reservations_total'],state['inference_reservations_total']),(9,3))
        self.assertEqual(Decimal(state['reserved_USD']),Decimal('.069'))

    def test_04_one_S04_and_global12_4_092(self):
        result,calls,folder=self.run_fake()
        self.assertEqual(result['scenario_id'],'S04');self.assertEqual(result['inference_attempts'],1)
        self.assertEqual([x[1] for x in calls],['/models/gpt-5.4-mini','/responses/input_tokens','/responses'])
        state=b.aggregate(self.policy)
        self.assertEqual((state['HTTP_reservations_total'],state['inference_reservations_total']),(12,4))
        self.assertEqual(Decimal(state['reserved_USD']),Decimal('.092'))
        self.assertTrue(client.s.old.c.read(folder/'execution_scope.json')['existing_budget_v2_limits_preserved'])

    def test_05_same_scope_cannot_repeat(self):
        self.run_fake();result,calls,_=self.run_fake()
        self.assertEqual(calls,[]);self.assertEqual(result['inference_attempts'],0)

    def test_06_context_cap_no_truncation_or_inference(self):
        result,calls,folder=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':6001}])
        self.assertEqual(len(calls),2);self.assertEqual(result['failure_reason'],'CONTEXT_BUDGET')
        self.assertEqual(client.s.old.c.read(folder/'source_request.json'),client.s.request('S04'))

    def test_07_30_HTTP_and_10_total_inference_limits(self):
        self.assertTrue(b.projected(self.policy,HTTP=21,inference=7)['within_limits'])
        self.assertFalse(b.projected(self.policy,HTTP=22,inference=7)['within_limits'])
        self.assertFalse(b.projected(self.policy,HTTP=21,inference=8)['within_limits'])
        self.assertEqual(Decimal(b.projected(self.policy,HTTP=21,inference=7)['reserved_USD']),Decimal('.230'))

    def test_08_no_remaining_room_no_first_HTTP(self):
        for i in range(10,29):self.write(self.prior/f'http_{i:02d}.json',{'extra_budget_guard_USD':'0.001'})
        self.before={p.name:public_sha(p) for p in self.prior.iterdir()}
        _,calls,_=self.run_fake();self.assertEqual(calls,[])

    def test_09_timeout_no_retry(self):
        result,calls,_=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':3500},TimeoutError(DUMMY)])
        self.assertEqual(len(calls),3);self.assertEqual(result['status'],'FAILED_STOP_NO_RETRY')
        self.assertTrue((self.scope/'BILLING_OR_LIMIT_STOP.json').exists())

    def test_10_HTTP_error_redaction_no_retry(self):
        result,calls,folder=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':3500},
            {'_HTTP':429,'error':{'code':'credit_balance_exhausted','message':DUMMY}}])
        self.assertEqual(result['HTTP_status'],429);self.assertEqual(len(calls),3)
        self.assertNotIn(DUMMY,(folder/'inference_error_redacted.json').read_text(encoding='utf-8'))

    def test_11_AppContainer_before_key_or_API(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['S04','--run-s04']),patch.object(client.old,'is_appcontainer',return_value=True),patch.object(client,'project_key',side_effect=AssertionError('NO_KEY')),contextlib.redirect_stdout(out):
            result=client.main()
        self.assertNotEqual(result,0);self.assertIn('APPCONTAINER_STOP_NO_API',out.getvalue())

    def test_12_only_S04_CLI(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['S04','--run-s07']),contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):client.main()
        self.assertIn('INVALID_ARGUMENTS',out.getvalue())

    def test_13_key_dotenv_only_secret_echo_not_saved(self):
        with patch.object(client,'load_key',return_value=None) as load:
            self.assertIsNone(client.project_key());load.assert_called_once_with(client.s.ROOT,environ={})
        x=response();x['key_echo']=DUMMY
        _,_,folder=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':3500},x])
        self.assertFalse((folder/'inference_response_raw.json').exists())

    def test_14_correct_ID_wrong_frequency_never_semantic_success(self):
        x=response();data=json.loads(x['output'][0]['content'][0]['text'])
        data['result']['items'][2]['explanation_tr']='TEST_ONLY: Bilinmeyen sıklık kesin olarak yüzde 90 yaygınlıktır.'
        x['output'][0]['content'][0]['text']=json.dumps(data)
        review=client.s.assess(x,'S04')
        self.assertEqual(review['application_status'],'PASS');self.assertIsNone(review['semantic_success'])
        self.assertEqual(review['human_review'],'PENDING');self.assertFalse(review['automatic_release'])

    def test_15_existing_semantic_review_plan_unchanged(self):
        frozen=client.s.old.c.read(client.s.QA/'S04_semantic_review_plan.json')
        self.assertEqual(frozen,client.s.semantic_plan('S04'))
        self.assertFalse(frozen['S01_fixed_sentence_tests_used']);self.assertFalse(frozen['source_ID_is_semantic_success'])

    def test_16_S01_S07_formal_QA_not_changed(self):
        for relative in ['reports/qa/WP12/openai_S01_success_review_v1/human_review_pending.json',
                         'reports/qa/WP12/openai_S07_actual_review_v1/human_review_pending.json']:
            self.assertEqual(client.s.old.c.read(client.s.ROOT/relative)['status'],'PENDING')


if __name__=='__main__':unittest.main(verbosity=2)
