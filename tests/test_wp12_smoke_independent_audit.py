"""Gerçek başarılı kaydın bellek/içerik regresyonu; mutation yalnız RAM kopyasında."""
import copy
import json
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from wp12_smoke_independent_audit import audit_content
from jsonschema.exceptions import ValidationError

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))


class IndependentAuditTests(unittest.TestCase):
    def setUp(self):
        self.args=[read(SOURCE/n) for n in ['run_record.json','smoke_request.json','smoke_response_raw.json','memory_samples.json']]
        self.args.append(read(ROOT/'configs/WP12_GEMMA1B_IDENTITY_FIX_v2_1.json'))

    def test_real_output_and_sampled_memory_pass(self):
        d=audit_content(*self.args);self.assertEqual(d['status'],'TECHNICAL_SMOKE_VERIFIED')
        self.assertEqual(d['runtime_host_samples'],28);self.assertFalse(d['automatic_release'])

    def test_wrong_API_digest_rejected(self):
        self.args[0]['observed_digest']='sha256:'+'0'*64
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_extra_output_field_rejected(self):
        self.args[2]['message']['content']='{"probe":"WP12_GEMMA1B_SMOKE_V2","extra":1}'
        with self.assertRaises(ValidationError):audit_content(*self.args)

    def test_incomplete_response_rejected(self):
        self.args[2]['done']=False
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_second_request_rejected(self):
        self.args[0]['inference_attempts']=2
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_below_start_RAM_rejected(self):
        self.args[0]['memory_immediately_before']['available_bytes']=2684354559
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_runtime_warning_rejected(self):
        self.args[3][10]['available_bytes']=1073741823
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_short_stability_rejected(self):
        self.args[0]['admission_samples'][-1]['at']=self.args[0]['admission_samples'][0]['at']
        with self.assertRaises(ValueError):audit_content(*self.args)

    def test_download_flag_rejected(self):
        self.args[0]['new_downloads']=1
        with self.assertRaises(ValueError):audit_content(*self.args)


if __name__=='__main__':unittest.main(verbosity=2)
