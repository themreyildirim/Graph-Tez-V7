"""Yalnız geçici teknik echo fixture'ları; gerçek kullanıcı/LLM sonucu değildir."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import wp12_gemma_smoke_review as v


class ExternalReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.folder=Path(self.temp.name)
        self.request={'model':v.MODEL,'stream':False,'think':False,'keep_alive':0,
            'messages':[{'role':'user','content':'Technical echo only. Return exactly {"probe":"WP12_GEMMA1B_SMOKE_V1"}. No medical content, no explanation.'}],
            'format':{'type':'object','properties':{'probe':{'type':'string','enum':['WP12_GEMMA1B_SMOKE_V1']}},'required':['probe'],'additionalProperties':False},
            'options':{'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108}}
        self.response={'model':v.MODEL,'done':True,'done_reason':'stop','message':{'content':'{"probe":"WP12_GEMMA1B_SMOKE_V1"}'},'prompt_eval_count':60,'eval_count':15}
        self.record={'schema_version':'WP12-gemma1b-user-smoke-run-v1','model':v.MODEL,'expected_digest':v.DIGEST,
            'thresholds':{'host_free_bytes':3221225472,'GPU_free_MiB':2560},
            'frozen_scenarios_sha256':v.sha(v.ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'),
            'source_contract_sha256':v.sha(v.ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),
            'script_sha256':v.sha(v.ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v1.ps1'),
            'inference_attempts':1,'new_downloads':0,'models_pulled':0,'processes_terminated':0,'real_scenario_repeats':0,
            'service_started':False,'security_changed':False,'automatic_release':False,
            'status':'SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW','is_appcontainer':False,'observed_digest':v.DIGEST,
            'memory_before':{'available_bytes':4*2**30},'memory_immediately_before':{'available_bytes':4*2**30},
            'GPU_before':{'free_MiB':3935},'GPU_immediately_before':{'free_MiB':3935},'already_loaded_models':0,
            'server_version':'TEST_FIXTURE_NOT_REAL_SERVER','HTTP_status':200,'prompt_eval_count':60,'eval_count':15}
        self.save('metadata_1_version.json',{'version':self.record['server_version']})
        self.save('metadata_2_tags.json',{'models':[{'name':v.MODEL,'digest':v.DIGEST}]})
        self.save('metadata_3_ps.json',{'models':[]})
        self.save('memory_samples.json',[{'available_bytes':4*2**30},{'available_bytes':3*2**30}])
        self.save('smoke_request.json',self.request);self.save('smoke_response_raw.json',self.response)

    def save(self,name,value):
        (self.folder/name).write_text(json.dumps(value),encoding='utf-8')

    def seal(self):
        self.record['request_sha256']=v.sha(self.folder/'smoke_request.json')
        if (self.folder/'smoke_response_raw.json').exists():self.record['response_sha256']=v.sha(self.folder/'smoke_response_raw.json')
        self.save('run_record.json',self.record)
        self.save('file_hashes.json',{p.name:v.sha(p) for p in self.folder.iterdir() if p.name!='file_hashes.json'})

    def test_consistent_technical_fixture_does_not_auto_release(self):
        self.seal();r=v.validate_run(self.folder)
        self.assertEqual(r['status'],'EXTERNAL_TECHNICAL_ECHO_PASS_PENDING_USER_REVIEW')
        self.assertFalse(r['auto_release']);self.assertEqual(r['PDF_explanation_quality'],'NOT_TESTED')

    def test_below_three_GiB_rejected(self):
        self.record['memory_immediately_before']['available_bytes']=3221225471;self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_changed_threshold_rejected(self):
        self.record['thresholds']['host_free_bytes']=1;self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_appcontainer_inference_rejected(self):
        self.record['is_appcontainer']=True;self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_multiple_calls_rejected(self):
        self.record['inference_attempts']=2;self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_changed_model_rejected(self):
        self.record['model']='another:model';self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_response_without_hash_match_rejected(self):
        self.seal();self.save('smoke_response_raw.json',{'not':'original'})
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_duplicate_echo_keys_rejected(self):
        self.response['message']['content']='{"probe":"bad","probe":"WP12_GEMMA1B_SMOKE_V1"}'
        self.save('smoke_response_raw.json',self.response);self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_changed_seed_rejected(self):
        self.request['options']['seed']=1;self.save('smoke_request.json',self.request);self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_path_traversal_rejected(self):
        self.seal();m=v.read(self.folder/'file_hashes.json');m['../escape']='0'*64
        self.save('file_hashes.json',m)
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_zero_calls_cannot_claim_pass(self):
        self.record['inference_attempts']=0;self.seal()
        with self.assertRaises(ValueError):v.validate_run(self.folder)

    def test_no_smoke_is_not_failed_quality(self):
        self.record['inference_attempts']=0;self.record['status']='STOP_MEMORY_GATE';self.seal()
        r=v.validate_run(self.folder)
        self.assertEqual(r['status'],'EXTERNAL_RECORD_CONSISTENT_NO_SMOKE_PASS')


if __name__=='__main__':unittest.main(verbosity=2)
