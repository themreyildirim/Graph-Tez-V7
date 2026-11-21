import sys,json,socket,tempfile,unittest
from pathlib import Path
from copy import deepcopy
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S16_v1_client as c
b=c.b
class S16(unittest.TestCase):
 def setUp(self):
  self.net=patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK'));self.net.start()
  self.temp=tempfile.TemporaryDirectory(dir=b.QA,prefix='TEST_ONLY_');self.path=Path(self.temp.name)
  self.ctrl=patch.object(b,'CONTROL',self.path/'control');self.ctrl.start()
  self.policy={**b.prior.base.old.c.read(b.prior.base.POLICY),'execution_scope_version':'S16-test'}
  self.verify=patch.object(b,'verify',return_value=self.policy);self.verify.start()
 def tearDown(self):
  self.verify.stop();self.ctrl.stop();self.temp.cleanup();self.net.stop()
 def response(self,code='NO_SOURCE'):
  return {'model':'gpt-5.4-mini-2026-03-17','id':'resp_TEST_ONLY','status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps({'result':{'schema_version':'WP12-local-llm-candidate-v2','status':'refused','refusal_code':code,'language':'tr','items':[]}})}]}],'usage':{'input_tokens':800,'input_tokens_details':{'cached_tokens':0},'output_tokens':60,'output_tokens_details':{'reasoning_tokens':0}}}
 def run_fake(self,values=None):
  folder=self.path/('run'+str(len(list(self.path.glob('run*')))));folder.mkdir()
  values=values or [{'id':'gpt-5.4-mini'},{'input_tokens':800},self.response()];calls=[]
  def send(method,path,data,key):
   calls.append(path);v=values[len(calls)-1]
   if isinstance(v,BaseException):raise v
   return {'HTTP_status':200,'elapsed_seconds':.01,'request_id':'req_TEST_ONLY','body':json.dumps(v)}
  return c.perform(folder,'TEST_ONLY_NOT_A_PROVIDER_KEY',self.policy,send),calls
 def test_01_frozen_empty_sources(self):
  x,p,_,_=c.s.context('S16');self.assertEqual(p['sources'],[]);self.assertEqual(x['scenario']['evidence_ids'],[]);self.assertIn('REFUSE: NO_SOURCE',p['acceptance_criteria_tr'])
 def test_02_S15_not_authorized(self):
  with self.assertRaises(ValueError):c.s.request('S15')
 def test_03_expected_refusal_application(self):
  v=c.s.assess(self.response(),'S16');self.assertEqual(v['application_status'],'PASS');self.assertIsNone(v['semantic_success']);self.assertEqual(v['human_review'],'PENDING')
 def test_04_wrong_refusal_not_success(self):self.assertEqual(c.s.assess(self.response('IMAGE_TEXT_UNAVAILABLE'),'S16')['application_status'],'FAIL_NO_SOURCE_POLICY')
 def test_05_refused_nonempty_items_schema_fail(self):
  raw=self.response();v=json.loads(raw['output'][0]['content'][0]['text']);v['result']['items']=[{}];raw['output'][0]['content'][0]['text']=json.dumps(v);self.assertEqual(c.s.assess(raw,'S16')['schema_status'],'FAIL')
 def test_06_unknown_not_negative(self):self.assertEqual(c.s.assess(self.response(),'S16')['trusted_envelope']['predicted_by_GNN']['status'],'NOT_REQUESTED_IN_WP12')
 def test_07_current_budget12_4(self):
  v=b.aggregate(self.policy);self.assertEqual((v['HTTP_reservations_total'],v['inference_reservations_total'],v['reserved_USD']),(12,4,'0.092'))
 def test_08_one_request_and15_5_budget(self):
  v,calls=self.run_fake();self.assertEqual(len(calls),3);self.assertEqual(v['inference_attempts'],1);self.assertEqual(b.aggregate(self.policy)['reserved_USD'],'0.115')
 def test_09_no_retry(self):
  self.run_fake();v,calls=self.run_fake();self.assertEqual(calls,[])
 def test_10_timeout_no_retry(self):
  v,calls=self.run_fake([TimeoutError()]);self.assertEqual(len(calls),1);self.assertEqual(v['status'],'FAILED_STOP_NO_RETRY')
 def test_11_context_limit_no_inference(self):
  v,calls=self.run_fake([{'id':'gpt-5.4-mini'},{'input_tokens':6001}]);self.assertEqual(len(calls),2);self.assertEqual(v['failure_reason'],'CONTEXT_BUDGET')
 def test_12_global_limits(self):
  self.assertFalse(b.projected(self.policy,HTTP=19)['within_limits']);self.assertFalse(b.projected(self.policy,inference=7)['within_limits']);self.assertEqual(self.policy['operational_reservation_ceiling_USD'],'0.25')
if __name__=='__main__':unittest.main(verbosity=2)
