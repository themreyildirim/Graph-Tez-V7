"""Gerçek iki kayıt üstünde offline teşhis testleri; çıktı veya kaynak değiştirilmez."""
from pathlib import Path
import copy
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp12_user_smoke_review import read,sha,verify_file_manifest
from wp12_gemma_failure_diagnosis import ROOT,diagnose


class DiagnosisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runs=sorted((ROOT/'reports/qa/WP12/gemma1b_v2_user_smoke_runs').glob('*/run_record.json'))
        cls.hash=sha(ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2.ps1')

    def inspect(self,p,record=None):
        return diagnose(read(p) if record is None else record,read(p.parent/'metadata_1_version.json'),
            read(p.parent/'metadata_2_tags.json'),script_hash=self.hash,
            filenames={x.name for x in p.parent.iterdir()})

    def test_two_original_manifests(self):
        self.assertEqual(len(self.runs),2)
        for p in self.runs:self.assertEqual(len(verify_file_manifest(p.parent)),3)

    def test_exact_failure_not_timeout(self):
        for p in self.runs:
            d=self.inspect(p);self.assertEqual(d['confirmed_failure'],'MODEL_DIGEST_MISMATCH')
            self.assertFalse(d['timeout_detected'])

    def test_no_inference_or_load_claim(self):
        for p in self.runs:
            d=self.inspect(p);self.assertFalse(d['inference_request_sent'])
            self.assertEqual(d['server_model_residency'],'UNKNOWN_NO_API_PS_RESPONSE_OR_SERVER_LOAD_LOG')

    def test_memory_recomputed_not_executed(self):
        for p in self.runs:
            d=self.inspect(p);self.assertFalse(d['memory_gate_executed'])
            self.assertFalse(d['initial_RAM_recomputed_pass'])
            self.assertTrue(d['initial_GPU_recomputed_pass']);self.assertTrue(d['initial_commit_recomputed_pass'])

    def test_exact_HTTP_status_not_fabricated(self):
        for p in self.runs:self.assertEqual(self.inspect(p)['metadata_HTTP_exact_status'],'UNKNOWN_NOT_LOGGED')

    def test_different_script_requires_manual_review(self):
        r=copy.deepcopy(read(self.runs[0]));r['script_sha256']='0'*64
        with self.assertRaises(ValueError):self.inspect(self.runs[0],r)

    def test_different_exception_not_inferred(self):
        r=copy.deepcopy(read(self.runs[0]));r['error']='unrelated failure'
        with self.assertRaises(ValueError):self.inspect(self.runs[0],r)

    def test_proposed_source_binding_offline_only(self):
        identity=read(ROOT/'reports/qa/WP12/gemma1b_candidate_v1/model_identity.json')
        for p in self.runs:
            r=read(p)
            self.assertNotEqual(r['expected_digest'],r['observed_digest'])
            self.assertEqual(identity['source_manifest_digest'],r['observed_digest'])
            self.assertFalse(self.inspect(p)['initial_combined_gate_recomputed_pass'])


if __name__=='__main__':unittest.main(verbosity=2)
