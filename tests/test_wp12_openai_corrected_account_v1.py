"""Yeni hesap scope'u: yalnız ağsız test fixture'ları; gerçek key hiçbir testte yok."""
from pathlib import Path
from unittest.mock import patch
import contextlib
import io
import json
import socket
import sys
import tempfile
import unittest
from decimal import Decimal
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import wp12_openai_corrected_account_v1 as new
from wp12_api_security import public_sha

DUMMY='TEST_ONLY_NOT_A_REAL_CREDENTIAL_123456'


def fake_response():
    src=new.adapter.source_payload()['sources']
    value={'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'candidate','refusal_code':None,'language':'tr',
        'items':[{'explanation_tr':'Kaynak bu ürünü eritromisin tablet olarak tanımlar.','source_scope':'product_identity',
                  'statement_kind':s['kind'],'evidence_ids':[s['quote_id']]} for s in src]}}
    return {'id':'resp_TEST_ONLY','model':'gpt-5.4-mini-2026-03-17','status':'completed',
        'output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(value)}]}],
        'usage':{'input_tokens':1236,'input_tokens_details':{'cached_tokens':0},
                 'output_tokens':200,'output_tokens_details':{'reasoning_tokens':0}}}


class Corrected(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.base=new.original.c.read(new.adapter.POLICY)

    def setUp(self):
        self.network=patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK_IN_OFFLINE_TEST'))
        self.network.start()
        self.temp=tempfile.TemporaryDirectory(prefix='corrected_account_test_',dir=new.QA)
        self.tmp=Path(self.temp.name).resolve();self.assertTrue(self.tmp.is_relative_to(new.QA.resolve()))
        self.old=self.tmp/'old';self.old.mkdir();self.scope=self.tmp/'new'
        for n in range(1,4):self.put(self.old/f'http_{n:02d}.json',{'extra_budget_guard_USD':'0.001'})
        self.put(self.old/'inference_reservation_01.json',{'reserved_USD':'0.02'})
        self.put(self.old/'BILLING_OR_LIMIT_STOP.json',{'status':'OLD_UNKNOWN_COST_RETAINED_TEST_ONLY'})
        self.old_hashes={p.name:public_sha(p) for p in self.old.iterdir()}
        self.patches=[patch.object(new,'PRIOR_CONTROL',self.old),patch.object(new,'CONTROL',self.scope)]
        for p in self.patches:p.start()
        self.config={'protected_prior_public_files_sha256':{},'new_executor_public_files_sha256':{}}

    def tearDown(self):
        self.assertEqual({p.name:public_sha(p) for p in self.old.iterdir()},self.old_hashes)
        for p in reversed(self.patches):p.stop()
        assert self.tmp.is_relative_to(new.QA.resolve()) and self.tmp.name.startswith('corrected_account_test_')
        self.temp.cleanup();self.network.stop()

    def put(self,path,data):path.write_text(json.dumps(data),encoding='utf-8')

    def chain(self):return [{'id':'gpt-5.4-mini'},{'input_tokens':1236},fake_response()]

    def run_fake(self,chain=None):
        chain=self.chain() if chain is None else chain
        folder=self.tmp/('run'+str(len(list(self.tmp.glob('run*')))));folder.mkdir()
        calls=[]
        def send(method,path,payload,key):
            calls.append((method,path,payload))
            item=chain[len(calls)-1]
            if isinstance(item,BaseException):raise item
            status=item.pop('_HTTP_status',200)
            return {'HTTP_status':status,'body':json.dumps(item),'request_id':'req_TEST_ONLY','elapsed_seconds':.01}
        record=new.perform(folder,DUMMY,self.base,self.config,send=send)
        return record,calls,folder

    def test_01_prior_reservations_included(self):
        x=new.aggregate_budget(self.base)
        self.assertEqual(x['HTTP_attempt_reservations_all_accounts'],3)
        self.assertEqual(x['inference_reservations_all_accounts'],1)
        self.assertEqual(Decimal(x['reserved_USD_all_accounts']),Decimal('.023'))

    def test_02_one_new_inference_and_all_account_totals(self):
        record,calls,folder=self.run_fake()
        self.assertEqual([x[1] for x in calls],['/models/gpt-5.4-mini','/responses/input_tokens','/responses'])
        self.assertEqual(record['inference_attempts'],1)
        totals=new.aggregate_budget(self.base)
        self.assertEqual(totals['HTTP_attempt_reservations_all_accounts'],6)
        self.assertEqual(totals['inference_reservations_all_accounts'],2)
        self.assertEqual(Decimal(totals['reserved_USD_all_accounts']),Decimal('.046'))
        self.assertTrue((folder/'inference_response_raw.json').exists())

    def test_03_old_billing_stop_is_unchanged(self):
        self.run_fake()
        self.assertEqual(new.original.c.read(self.old/'BILLING_OR_LIMIT_STOP.json')['status'],'OLD_UNKNOWN_COST_RETAINED_TEST_ONLY')

    def test_04_new_scope_cannot_repeat(self):
        self.run_fake();record,calls,_=self.run_fake()
        self.assertEqual(calls,[]);self.assertEqual(record['inference_attempts'],0)

    def test_05_single_scope_restores_original_module_control(self):
        original=new.original.CONTROL
        self.run_fake();self.assertEqual(new.original.CONTROL,original)
        with self.assertRaises(RuntimeError):
            with new.isolated_control():raise RuntimeError('TEST_ONLY')
        self.assertEqual(new.original.CONTROL,original)

    def test_06_token_over_cap_never_infers(self):
        chain=self.chain();chain[1]['input_tokens']=6001
        record,calls,_=self.run_fake(chain)
        self.assertEqual(len(calls),2);self.assertEqual(record['inference_attempts'],0)

    def test_07_transport_timeout_no_retry(self):
        chain=self.chain();chain[2]=TimeoutError(DUMMY)
        record,calls,folder=self.run_fake(chain)
        self.assertEqual(len(calls),3);self.assertEqual(record['status'],'FAILED_STOP_NO_RETRY')
        self.assertTrue((self.scope/'BILLING_OR_LIMIT_STOP.json').exists())
        self.assertNotIn(DUMMY,(folder/'run_record.json').read_text(encoding='utf-8'))

    def test_08_429_failure_is_retained(self):
        chain=self.chain();chain[2]={'_HTTP_status':429,'error':{'type':'insufficient_quota','code':'credit_balance_exhausted','message':DUMMY}}
        record,calls,folder=self.run_fake(chain)
        self.assertEqual(record['status'],'FAILED_STOP_NO_RETRY');self.assertEqual(len(calls),3)
        self.assertTrue((folder/'inference_error_redacted.json').exists())
        self.assertFalse((folder/'inference_response_raw.json').exists())

    def test_09_aggregate_HTTP_limit_stops_transport(self):
        for n in range(4,11):self.put(self.old/f'http_{n:02d}.json',{'extra_budget_guard_USD':'0.001'})
        self.old_hashes={p.name:public_sha(p) for p in self.old.iterdir()}
        _,calls,folder=self.run_fake()
        self.assertEqual(calls,[])
        audit=new.original.c.read(folder/'actual_transport_attempts.json')
        self.assertEqual(audit['inference_transport_attempts'],0)

    def test_10_all_account_inference_limit(self):
        for n in range(2,12):self.put(self.old/f'inference_reservation_{n:02d}.json',{'reserved_USD':'0.02'})
        self.old_hashes={p.name:public_sha(p) for p in self.old.iterdir()}
        self.assertFalse(new.aggregate_budget(self.base)['within_original_pilot_caps'])

    def test_11_bad_ledger_amount_not_ignored(self):
        self.put(self.old/'http_04.json',{'extra_budget_guard_USD':'0'})
        self.old_hashes={p.name:public_sha(p) for p in self.old.iterdir()}
        with self.assertRaises(ValueError):new.aggregate_budget(self.base)

    def test_12_project_dotenv_only_not_inherited_key(self):
        with patch.object(new,'load_key',return_value=DUMMY) as loader:
            self.assertEqual(new.project_key(),DUMMY)
            loader.assert_called_once_with(new.ROOT,environ={})

    def test_13_absent_key_remains_absent(self):
        with patch.object(new,'load_key',return_value=None):self.assertIsNone(new.project_key())

    def test_14_AppContainer_never_loads_key_or_sends(self):
        out=io.StringIO()
        with patch.object(sys,'argv',['corrected','--run-single-s01']),patch.object(new.original,'is_appcontainer',return_value=True),patch.object(new,'project_key',side_effect=AssertionError('NO_KEY')),contextlib.redirect_stdout(out):
            status=new.main()
        self.assertNotEqual(status,0);self.assertIn('APPCONTAINER_STOP_NO_API',out.getvalue())

    def test_15_identical_prompt_model_schema_sources(self):
        _,calls,_=self.run_fake()
        actual=calls[-1][2]
        self.assertEqual(actual,new.original.c.read(new.adapter.QA/'S01_Responses_request_NOT_SENT.json'))
        self.assertEqual(actual['model'],'gpt-5.4-mini');self.assertEqual(actual['max_output_tokens'],1200)

    def test_16_structural_pass_requires_human_review(self):
        record,_,folder=self.run_fake()
        self.assertEqual(record['status'],'PENDING_SOURCE_AND_HUMAN_REVIEW')
        assessed=new.original.c.read(folder/'structural_and_language_review.json')
        self.assertIsNone(assessed['semantic_success']);self.assertEqual(assessed['human_review'],'PENDING')

    def test_17_secret_echo_not_persisted(self):
        chain=self.chain();chain[2]['echo']=DUMMY
        _,_,folder=self.run_fake(chain)
        self.assertFalse((folder/'inference_response_raw.json').exists())
        for p in folder.iterdir():self.assertNotIn(DUMMY,p.read_text(encoding='utf-8'))

    def test_18_prior_real_failed_records_unchanged(self):
        data=new.original.c.read(new.POLICY)
        new.verify_public_inputs(data)
        self.assertTrue(data['one_additional_S01_attempt_authorized'])
        self.assertTrue(data['prior_failure_cause_user_reported_not_independent_account_verification'])


if __name__=='__main__':unittest.main(verbosity=2)
