"""Gerçek inference yapmadan deneysel bellek sınırları ve izolasyon testleri."""
from pathlib import Path
import copy
import sys
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import wp12_source_low_memory as low
import wp12_source_case as c


class LowMemoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p=c.read(low.POLICY)
        cls.runner=(ROOT/cls.p['runner']).read_text(encoding='utf-8')

    def sample(self):return {'available_bytes':1610612736,'commit_available_bytes':3221225472,'low_memory_notification':False}
    def gpu(self):return {'free_MiB':1024}

    def test_01_exact_entry_boundaries_pass(self):self.assertTrue(low.entry_gate(self.sample(),self.gpu(),self.p))
    def test_02_RAM_below_stops(self):
        x=self.sample();x['available_bytes']-=1;self.assertFalse(low.entry_gate(x,self.gpu(),self.p))
    def test_03_GPU_below_stops(self):self.assertFalse(low.entry_gate(self.sample(),{'free_MiB':1023},self.p))
    def test_04_commit_below_stops(self):
        x=self.sample();x['commit_available_bytes']-=1;self.assertFalse(low.entry_gate(x,self.gpu(),self.p))
    def test_05_OS_pressure_at_entry_stops(self):
        x=self.sample();x['low_memory_notification']=True;self.assertFalse(low.entry_gate(x,self.gpu(),self.p))
    def test_06_missing_each_measurement_stops(self):
        for key in self.sample():
            x=self.sample();del x[key]
            with self.subTest(key=key),self.assertRaises(ValueError):low.entry_gate(x,self.gpu(),self.p)
        with self.assertRaises(ValueError):low.entry_gate(self.sample(),{},self.p)
    def test_07_unknown_pressure_stops(self):
        x=self.sample();x['low_memory_notification']=None
        with self.assertRaises(ValueError):low.entry_gate(x,self.gpu(),self.p)
    def test_08_runtime_RAM_warning(self):
        x=self.sample();x['available_bytes']=805306367;self.assertTrue(low.runtime_warning(x,self.p))
    def test_09_runtime_commit_warning(self):
        x=self.sample();x['commit_available_bytes']=1073741823;self.assertTrue(low.runtime_warning(x,self.p))
    def test_10_runtime_OS_pressure_warning(self):
        x=self.sample();x['low_memory_notification']=True;self.assertTrue(low.runtime_warning(x,self.p))
    def test_11_runtime_missing_stops(self):
        with self.assertRaises(ValueError):low.runtime_warning({},self.p)
    def test_12_runtime_exact_boundary_no_warning(self):
        x=self.sample();x.update(available_bytes=805306368,commit_available_bytes=1073741824)
        self.assertFalse(low.runtime_warning(x,self.p))
    def test_13_original_v2_entry_unchanged(self):
        p=c.read(c.CONFIG);self.assertEqual((p['RAM_floor_bytes'],p['GPU_floor_MiB']),(2684354560,2048))
        self.assertIn('<2684354560',(ROOT/'scripts/wp12_source_case.py').read_text(encoding='utf-8'))
    def test_14_original_prompt_and_schema_unchanged(self):
        self.assertEqual(c.request_for(c.context()),c.read(c.QA/'package/request.json'))
        self.assertEqual(c.read(c.QA/'package/offline_token_proof.json')['input_token_count'],919)
    def test_15_dependency_and_runner_hashes(self):
        for p,h in self.p['immutable_inputs_sha256'].items():self.assertEqual(c.sha(ROOT/p),h,p)
        self.assertEqual(c.sha(ROOT/self.p['runner']),self.p['runner_sha256'])
    def test_16_exactly_one_generation_call(self):
        self.assertEqual(self.runner.count('.PostAsync('),1)
        self.assertIn('param([switch]$RunFirstCase)',self.runner)
    def test_17_AppContainer_before_API(self):
        self.assertLess(self.runner.index('STOP_APPContainer_NO_API_ATTEMPT'),self.runner.index("Read-LocalMetadata 'version'"))
    def test_18_pressure_and_commit_in_runtime(self):
        self.assertIn('if ($sample.available_bytes -lt 805306368 -or $sample.commit_available_bytes -lt 1073741824 -or $sample.low_memory_notification)',self.runner)
    def test_19_no_guarantee_no_continuation(self):
        self.assertFalse(self.p['safety_guarantee']);self.assertFalse(self.p['automatic_retry'])
        self.assertFalse(self.p['stage2_enabled']);self.assertFalse(self.p['automatic_publication'])
        self.assertIn('server completion is unknown',self.runner)
    def test_20_no_kill_download_or_settings_commands(self):
        for forbidden in ['Stop-Process','Set-ExecutionPolicy','Start-Service','/api/pull','ollama pull','-Verb RunAs']:
            self.assertNotIn(forbidden,self.runner)
    def test_21_actual_measurements_complete_and_classified(self):
        m=c.read(low.QA/'current_measurements.json');self.assertEqual(m['measurement_status'],'COMPLETE')
        self.assertTrue(low.entry_gate(m['memory'],m['GPU'],self.p))
        self.assertEqual((m['API_attempts'],m['inference_attempts']),(0,0))
    def test_22_invalid_runtime_measurement_rejected(self):
        x=self.sample();x['available_bytes']=float('nan')
        with self.assertRaises(ValueError):low.runtime_warning(x,self.p)
    def test_23_BUN_dependencies_unchanged(self):
        ctx=c.context('S07');ann={a['key']:a for a in ctx['annotations']}
        self.assertIn(ann['D_BUN_exception']['quote_id'],ctx['scenario']['evidence_ids'])
    def test_24_structural_valid_is_never_semantic_success(self):
        candidate={'schema_version':'WP12-local-llm-candidate-v1','status':'refused','refusal_code':'UNCERTAIN_EVIDENCE','items':[]}
        r=c.validate_response({'model':self.p['model'],'done':True,'done_reason':'stop','prompt_eval_count':919,
            'eval_count':20,'message':{'content':c.dump(candidate)}},c.context(),{'input_token_count':919})
        self.assertIsNone(r['semantic_success']);self.assertFalse(r['automatic_release'])
    def test_25_source_case_immutable_in_experimental_policy(self):
        self.assertEqual(self.p['scenario_id'],'S01');self.assertEqual(self.p['repeat'],1)
        self.assertEqual(self.p['max_generation_requests'],1)
        self.assertIn('configs/WP12_SOURCE_SINGLE_CASE_v1.json',self.p['immutable_inputs_sha256'])


if __name__=='__main__':unittest.main(verbosity=2)
