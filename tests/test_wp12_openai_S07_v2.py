"""V2 teknik testleri; tüm model yanıtları TEST_ONLY fixture, ağ kapalı."""
import contextlib
import copy
import io
import json
from decimal import Decimal
from pathlib import Path
import socket
import sys
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_scenarios_v2 as s
import wp12_openai_pilot_budget_v2 as b
import wp12_openai_S07_v2_client as client
import wp12_human_review_control_v1 as human
from wp12_api_security import public_sha

DUMMY='TEST_ONLY_FAKE_KEY_NOT_PROVIDER_CREDENTIAL'


def fixture_candidate(case):
    ctx,payload,_,_=s.context(case)
    return {'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'candidate','refusal_code':None,'language':'tr',
        'items':[{'explanation_tr':'TECHNICAL_FIXTURE_NOT_MODEL_OUTPUT','source_scope':x['scope'],'statement_kind':x['kind'],
            'evidence_ids':[x['quote_id'],*x['required_context_quote_ids']]} for x in payload['sources']]}}


def response(case='S07',value=None):
    return {'id':'resp_TEST_ONLY','model':'gpt-5.4-mini-2026-03-17','status':'completed',
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(fixture_candidate(case) if value is None else value)}]}],
        'usage':{'input_tokens':2000,'input_tokens_details':{'cached_tokens':0},'output_tokens':350,'output_tokens_details':{'reasoning_tokens':0}}}


class Scenarios(unittest.TestCase):
    def test_01_frozen_three_quotes_and_characters(self):
        for case,chars in [('S07',380),('S04',3803)]:
            ctx,payload,_,_=s.context(case)
            self.assertEqual(sum(len(x['quote']) for x in payload['sources']),chars)
            self.assertEqual([x['quote_id'] for x in payload['sources']],ctx['scenario']['evidence_ids'])
            self.assertEqual(payload['acceptance_criteria_tr'],ctx['scenario']['acceptance_criteria_tr'])

    def test_02_BUN_two_sentences_and_class_dependency(self):
        _,payload,_,_=s.context('S07')
        renal,intro,exception=payload['sources']
        self.assertEqual(set(renal['required_context_quote_ids']),{intro['quote_id'],exception['quote_id']})
        self.assertIn('Studies to date indicate',exception['quote'])
        self.assertIn('patients with impaired renal function',exception['quote'])
        self.assertEqual(renal['scope'],'class_level')

    def test_03_S04_transitive_page4_dependency(self):
        _,p,_,_=s.context('S04');p4,p5,unknown=p['sources']
        self.assertEqual(set(unknown['required_context_quote_ids']),{p4['quote_id'],p5['quote_id']})
        self.assertIn('Not known (frequency cannot be estimated',unknown['quote'])

    def test_04_schema_supported_subset_required_closed(self):
        def visit(node):
            if isinstance(node,list):
                for x in node:visit(x)
            elif isinstance(node,dict):
                self.assertFalse(set(node)&{'oneOf','if','then','else','not','allOf','uniqueItems','prefixItems'})
                if node.get('type')=='object':
                    self.assertFalse(node['additionalProperties']);self.assertEqual(set(node['properties']),set(node['required']))
                for x in node.values():visit(x)
        for case in ['S07','S04']:
            schema=s.schema(case);Draft202012Validator.check_schema(schema);self.assertNotIn('anyOf',schema);visit(schema)

    def test_05_valid_technical_fixture_never_semantic_success(self):
        for case in ['S07','S04']:
            result=s.assess(response(case),case)
            self.assertEqual(result['application_status'],'PASS')
            self.assertIsNone(result['semantic_success']);self.assertEqual(result['human_review'],'PENDING')
            self.assertFalse(result['automatic_release'])

    def test_06_missing_context_rejected(self):
        for case in ['S07','S04']:
            value=fixture_candidate(case)
            chosen=next(x for x in value['result']['items'] if len(x['evidence_ids'])==3)
            chosen['evidence_ids'].pop()
            result=s.assess(response(case,value),case)
            self.assertNotEqual(result['application_status'],'PASS')

    def test_07_unknown_quote_or_scope_rejected(self):
        for mutation in ['quote','scope']:
            v=fixture_candidate('S07')
            if mutation=='quote':v['result']['items'][0]['evidence_ids'][0]='quote:UNKNOWN_TEST_ONLY'
            else:v['result']['items'][0]['source_scope']='direct_doxycycline'
            self.assertNotEqual(s.assess(response(value=v),'S07')['schema_status'],'PASS')

    def test_08_duplicate_primary_and_swapped_first_context_rejected(self):
        v=fixture_candidate('S07');v['result']['items'][1]=copy.deepcopy(v['result']['items'][0])
        self.assertEqual(s.assess(response(value=v),'S07')['application_status'],'FAIL')
        v=fixture_candidate('S07');x=v['result']['items'][0]['evidence_ids'];x[0],x[1]=x[1],x[0]
        self.assertNotEqual(s.assess(response(value=v),'S07')['application_status'],'PASS')

    def test_09_correct_ID_does_not_detect_wrong_meaning(self):
        # Bilerek yanlış anlam: teknik kapının semantik classifier olmadığını gösterir.
        for case,wrong in [('S07','TEST_ONLY: Doxycycline her hastada kesin BUN artışı yapar.'),
                           ('S04','TEST_ONLY: Bilinmeyen sıklık yüzde 99 demektir.')]:
            v=fixture_candidate(case);v['result']['items'][0]['explanation_tr']=wrong
            result=s.assess(response(case,v),case)
            self.assertEqual(result['application_status'],'PASS');self.assertIsNone(result['semantic_success'])
            self.assertEqual(result['agent_source_review'],'PENDING')

    def test_10_refusal_empty_items_and_appropriateness_separate(self):
        v={'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'refused','refusal_code':'IMAGE_TEXT_UNAVAILABLE','language':'tr','items':[]}}
        result=s.assess(response(value=v),'S07')
        self.assertEqual(result['schema_status'],'PASS');self.assertNotEqual(result['application_status'],'PASS')
        v['result']['items']=fixture_candidate('S07')['result']['items']
        self.assertEqual(s.assess(response(value=v),'S07')['schema_status'],'FAIL')
        v=fixture_candidate('S07');v['result']['items']=[]
        self.assertEqual(s.assess(response(value=v),'S07')['schema_status'],'FAIL')

    def test_11_native_refusal_incomplete_or_wrong_model(self):
        x=response();x['output'][0]['content']=[{'type':'refusal','refusal':'TEST_ONLY'}]
        self.assertEqual(s.assess(x,'S07')['schema_status'],'NOT_EVALUABLE')
        x=response();x['status']='incomplete';self.assertEqual(s.assess(x,'S07')['status'],'INCOMPLETE_OR_FAILED_NO_RETRY')
        x=response();x['model']='OTHER_MODEL';self.assertEqual(s.assess(x,'S07')['status'],'UNEXPECTED_MODEL_STOP')

    def test_12_no_S01_fixed_sentences_or_cross_case_source_transfer(self):
        self.assertFalse(s.semantic_plan('S07')['S01_fixed_sentence_tests_used'])
        self.assertIn('iki',s.semantic_plan('S07')['frozen_acceptance_criteria_tr'])
        p=s.request('S07');self.assertNotIn('Erythromycin',p['input'][0]['content'][0]['text'])
        self.assertEqual(p['max_output_tokens'],1200);self.assertEqual(p['tools'],[])


class BudgetAndRunner(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.policy=s.old.c.read(b.POLICY)

    def setUp(self):
        self.network=patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK'));self.network.start()
        self.temp=tempfile.TemporaryDirectory(prefix='S07_v2_test_',dir=s.QA)
        self.tmp=Path(self.temp.name).resolve();self.assertTrue(self.tmp.is_relative_to(s.QA.resolve()))
        self.prior=self.tmp/'prior';self.prior.mkdir();self.scope=self.tmp/'scope'
        for i in range(1,7):self.write(self.prior/f'http_{i:02d}.json',{'extra_budget_guard_USD':'0.001'})
        for i in range(1,3):self.write(self.prior/f'inference_reservation_{i:02d}.json',{'reserved_USD':'0.02'})
        self.write(self.prior/'BILLING_OR_LIMIT_STOP.json',{'status':'OLD_STOP_TEST_ONLY'})
        self.hashes={p.name:public_sha(p) for p in self.prior.iterdir()}
        self.patches=[patch.object(b,'PRIOR_ROOTS',[self.prior]),patch.object(b,'CONTROL',self.scope),
            patch.object(b,'verify',return_value=self.policy)]
        for p in self.patches:p.start()

    def tearDown(self):
        self.assertEqual({p.name:public_sha(p) for p in self.prior.iterdir()},self.hashes)
        for p in reversed(self.patches):p.stop()
        assert self.tmp.is_relative_to(s.QA.resolve()) and self.tmp.name.startswith('S07_v2_test_')
        self.temp.cleanup();self.network.stop()

    def write(self,path,value):path.write_text(json.dumps(value),encoding='utf-8')

    def run_fake(self,chain=None):
        folder=self.tmp/('run'+str(len(list(self.tmp.glob('run*')))));folder.mkdir()
        chain=[{'id':'gpt-5.4-mini'},{'input_tokens':2000},response()] if chain is None else chain
        calls=[]
        def send(method,path,data,key):
            calls.append((method,path));item=chain[len(calls)-1]
            if isinstance(item,BaseException):raise item
            code=item.pop('_HTTP',200)
            return {'HTTP_status':code,'body':json.dumps(item),'request_id':'req_TEST_ONLY','elapsed_seconds':.01}
        return client.perform(folder,DUMMY,self.policy,send),calls,folder

    def test_13_old6_and2_reservations_retained(self):
        state=b.aggregate(self.policy)
        self.assertEqual((state['HTTP_reservations_total'],state['inference_reservations_total']),(6,2))
        self.assertEqual(Decimal(state['reserved_USD']),Decimal('.046'))

    def test_14_ten_total_not_ten_new_and_max_reservation(self):
        projected=b.projected(self.policy,HTTP=24,inference=8)
        self.assertTrue(projected['within_limits']);self.assertEqual(Decimal(projected['reserved_USD']),Decimal('.230'))
        self.assertFalse(b.projected(self.policy,HTTP=25,inference=8)['within_limits'])
        self.assertFalse(b.projected(self.policy,HTTP=24,inference=9)['within_limits'])

    def test_15_success_single_request_pending_after9_HTTP(self):
        result,calls,folder=self.run_fake()
        self.assertEqual([x[1] for x in calls],['/models/gpt-5.4-mini','/responses/input_tokens','/responses'])
        self.assertEqual(result['status'],'STRUCTURE_VALID_PENDING_AGENT_AND_HUMAN_REVIEW')
        state=b.aggregate(self.policy);self.assertEqual(state['HTTP_reservations_total'],9)
        self.assertEqual(state['inference_reservations_total'],3);self.assertEqual(Decimal(state['reserved_USD']),Decimal('.069'))

    def test_16_same_S07_cannot_repeat(self):
        self.run_fake();result,calls,_=self.run_fake()
        self.assertEqual(calls,[]);self.assertEqual(result['inference_attempts'],0)

    def test_17_context_budget_no_truncation_no_inference(self):
        result,calls,folder=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':6001}])
        self.assertEqual(len(calls),2);self.assertEqual(result['failure_reason'],'CONTEXT_BUDGET')
        self.assertEqual(s.old.c.read(folder/'source_request.json'),s.request('S07'))

    def test_18_HTTP_error_no_retry_and_redacts_message(self):
        chain=[{'id':'gpt-5.4-mini'},{'input_tokens':2000},{'_HTTP':429,'error':{'code':'credit_balance_exhausted','message':DUMMY}}]
        result,calls,folder=self.run_fake(chain)
        self.assertEqual(len(calls),3);self.assertEqual(result['HTTP_status'],429)
        self.assertTrue((folder/'inference_error_redacted.json').exists());self.assertFalse((folder/'inference_response_raw.json').exists())
        self.assertNotIn(DUMMY,(folder/'inference_error_redacted.json').read_text(encoding='utf-8'))

    def test_19_timeout_and_unknown_usage_stop(self):
        result,calls,_=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':2000},TimeoutError(DUMMY)])
        self.assertEqual(len(calls),3);self.assertEqual(result['status'],'FAILED_STOP_NO_RETRY')
        self.assertTrue((self.scope/'BILLING_OR_LIMIT_STOP.json').exists())

    def test_20_no_budget_room_no_first_HTTP(self):
        for i in range(7,29):self.write(self.prior/f'http_{i:02d}.json',{'extra_budget_guard_USD':'0.001'})
        self.hashes={p.name:public_sha(p) for p in self.prior.iterdir()}
        _,calls,_=self.run_fake();self.assertEqual(calls,[])

    def test_21_explicit_budget_acceptance_before_key(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['S07','--run-s07']),patch.object(client,'project_key',side_effect=AssertionError('NO_KEY')),contextlib.redirect_stdout(out):
            code=client.main()
        self.assertNotEqual(code,0);self.assertIn('BUDGET_V2_EXPLICIT_ACCEPTANCE_REQUIRED',out.getvalue())

    def test_22_S04_execution_flag_rejected(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['S07','--run-s04']),contextlib.redirect_stdout(out):
            with self.assertRaises(SystemExit):client.main()
        self.assertIn('INVALID_ARGUMENTS',out.getvalue())

    def test_23_AppContainer_no_key_or_API(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['S07','--run-s07','--accept-budget-v2']),patch.object(client.old,'is_appcontainer',return_value=True),patch.object(client,'project_key',side_effect=AssertionError('NO_KEY')),contextlib.redirect_stdout(out):
            code=client.main()
        self.assertNotEqual(code,0);self.assertIn('APPCONTAINER_STOP_NO_API',out.getvalue())

    def test_24_credential_dotenv_only_and_no_secret_response(self):
        with patch.object(client,'load_key',return_value=None) as load:
            self.assertIsNone(client.project_key());load.assert_called_once_with(s.ROOT,environ={})
        x=response();x['unexpected_echo']=DUMMY
        _,_,folder=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':2000},x])
        self.assertFalse((folder/'inference_response_raw.json').exists())


class HumanControl(unittest.TestCase):
    def event(self):
        items=s.old.c.read(human.RUN/'validated_JSON.json')['result']['items']
        return {'version':'WP12-human-decision-event-v1','case_id':'S01','run_id':human.RUN.name,
            'raw_response_sha256':public_sha(human.RUN/'inference_response_raw.json'),'reviewed_item_indices':[1,2],
            'quote_ids':[x['evidence_ids'][0] for x in items],'decision':'APPROVED','reviewer_id':'TEST_ONLY_REVIEWER',
            'reviewer_role':'TEST_ONLY_ROLE','reviewed_at':'2026-11-08T17:00:00+03:00','user_confirmation_reference':'TEST_ONLY_NOT_SUBMITTED'}

    def test_25_anonymous_statement_cannot_be_formal_event(self):
        x=self.event();x['reviewer_id']=None
        with self.assertRaises(ValueError):human.validate_event(x,[])

    def test_26_scope_hash_identity_and_timezone_required(self):
        for key,value in [('raw_response_sha256','BAD_TEST_ONLY'),('reviewed_item_indices',[1]),('reviewer_id','UNREGISTERED'),('reviewed_at','2026-11-08T17:00:00')]:
            x=self.event();x[key]=value
            with self.assertRaises(ValueError):human.validate_event(x,['TEST_ONLY_REVIEWER'])

    def test_27_registered_fixture_validates_without_writing(self):
        before=public_sha(human.RUN/'run_record.json')
        result=human.validate_event(self.event(),['TEST_ONLY_REVIEWER'])
        self.assertTrue(result['decision_not_written_by_validator']);self.assertFalse(result['automatic_publication'])
        self.assertEqual(public_sha(human.RUN/'run_record.json'),before)

    def test_28_formal_S01_QA_stays_pending(self):
        self.assertEqual(s.old.c.read(human.RUN/'run_record.json')['human_review'],'PENDING')
        qa=s.ROOT/'reports/qa/WP12/openai_S01_success_review_v1/human_review_pending.json'
        self.assertEqual(s.old.c.read(qa)['status'],'PENDING')


if __name__=='__main__':unittest.main(verbosity=2)
