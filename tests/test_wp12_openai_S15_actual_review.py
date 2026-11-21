import sys,socket,unittest,json
from pathlib import Path
from copy import deepcopy
from decimal import Decimal
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_openai_S15_actual_review as r
class Actual(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  with patch.object(socket,'socket',side_effect=AssertionError('NO_NETWORK')):cls.v=r.inspect()
 def test_01_all_independent_checks(self):self.assertTrue(all(self.v['checks'].values()))
 def test_02_expected_refusal_not_candidate(self):
  x=self.v['parsed_json']['result'];self.assertEqual((x['status'],x['refusal_code'],x['items']),('refused','IMAGE_TEXT_UNAVAILABLE',[]))
 def test_03_frozen_empty_source_not_missing_measurement(self):
  self.assertEqual(r.a.context('S15')[1]['sources'],[]);self.assertEqual(self.v['source_quote_count'],0)
 def test_04_language_not_inferred_from_tr(self):self.assertEqual(self.v['actual_Turkish_explanation_quality'],'NOT_EVALUABLE_NO_EXPLANATION_TEXT')
 def test_05_usage_exact(self):
  u=self.v['usage'];self.assertEqual((u['input_tokens'],u['output_tokens'],u['total_tokens']),(766,52,818))
 def test_06_cost_exact(self):
  self.assertEqual(Decimal(self.v['usage_token_cost_USD']),Decimal('.0008085'));self.assertEqual(Decimal(self.v['known_completed_five_case_token_cost_USD']),Decimal('.01273125'))
 def test_07_human_pending_not_agent_approval(self):
  self.assertEqual(self.v['formal_human_review'],'PENDING');self.assertFalse(self.v['automatic_release'])
 def test_08_wrong_ret_code_still_schema_pass_not_application(self):
  raw=deepcopy(r.read(r.RUN/'inference_response_raw.json'));v=deepcopy(self.v['parsed_json']);v['result']['refusal_code']='NO_SOURCE'
  raw['output'][0]['content'][0]['text']=json.dumps(v)
  a=r.a.assess(raw,'S15');self.assertEqual(a['schema_status'],'PASS');self.assertEqual(a['application_status'],'FAIL_IMAGE_TEXT_UNAVAILABLE_POLICY');self.assertIsNone(a['semantic_success'])
 def test_09_budget_and_single_attempt(self):
  self.assertEqual(self.v['aggregate_budget']['reserved_USD'],'0.138');self.assertTrue(self.v['checks']['single_scope_locks_and_old_stop'])
 def test_10_missing_telemetry_and_invoice_not_zero(self):
  self.assertEqual(self.v['RAM_VRAM'],'NOT_COLLECTED');self.assertTrue(self.v['invoice_total'].startswith('UNKNOWN'));self.assertEqual(self.v['new_API_requests'],0)
if __name__=='__main__':unittest.main(verbosity=2)
