"""Tek vaka hazırlığı: gerçek kaynaklar ve yerel vocab; hiçbir inference yapılmaz.

Yanıt fixture'ları yalnız teknik testtir, gerçek model yanıtı sayılmaz.
"""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import wp12_source_case as c
from wp12_vocab_counter import Params,VocabCounter,template_from_gguf,render_single_user
from jsonschema import Draft202012Validator


class SourceCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ctx=c.context();cls.cfg=c.read(c.CONFIG)
        cls.proof=c.read(c.QA/'package/offline_token_proof.json')
        cls.runner=(ROOT/cls.cfg['runner']).read_text(encoding='utf-8')

    def fixture(self):
        src=self.ctx['sources'][0]
        return {'schema_version':'WP12-local-llm-candidate-v1','status':'candidate','refusal_code':None,
            'items':[{'explanation_tr':'TEKNİK TEST ADAYI; model çıktısı değildir.',
                      'source_scope':src['scope'],'statement_kind':src['kind'],'evidence_ids':[src['quote_id']]}]}

    def response(self,candidate=None):
        return {'model':self.cfg['model'],'done':True,'done_reason':'stop',
                'prompt_eval_count':self.proof['input_token_count'],'eval_count':30,
                'message':{'role':'assistant','content':c.dump(self.fixture() if candidate is None else candidate)}}

    def validate(self,x):return c.validate_response(x,self.ctx,self.proof)

    def test_01_real_44_spans_and_first_frozen_case(self):
        q,p,a=c.source_index(self.ctx['bundle'],self.ctx['annotations'])
        self.assertEqual((len(q),len(p),len(a)),(44,17,44))
        self.assertEqual(self.ctx['scenario']['scenario_id'],'S01')
        self.assertEqual([s['physical_page'] for s in self.ctx['sources']],[1,6])
        self.assertEqual(sum(len(s['quote']) for s in self.ctx['sources']),537)

    def test_02_all_19_frozen_dependencies(self):
        frozen=c.read(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json')
        self.assertEqual(len(frozen),19)
        for case in frozen:
            self.assertEqual(c.context(case['scenario_id'])['scenario'],case)

    def test_03_BUN_context_and_exception_present(self):
        ctx=c.context('S07');ann={x['key']:x for x in ctx['annotations']}
        ids=ctx['scenario']['evidence_ids']
        self.assertIn(ann['D_BUN_exception']['quote_id'],ids)
        self.assertIn(ann['D_class_renal']['quote_id'],ids)

    def test_04_package_matches_source_request(self):
        self.assertEqual(c.request_for(self.ctx),c.read(c.QA/'package/request.json'))

    def test_05_schema_is_v1_subset(self):
        value=self.fixture()
        Draft202012Validator(c.case_schema(self.ctx)).validate(value)
        Draft202012Validator(c.read(ROOT/'docs/schemas/WP12_local_llm_candidate_v1.schema.json')).validate(value)

    def test_06_structural_pass_not_semantic_pass(self):
        result=self.validate(self.response())
        self.assertEqual(result['status'],'SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW')
        self.assertTrue(result['structural_valid']);self.assertIsNone(result['semantic_success'])
        self.assertFalse(result['automatic_release'])

    def test_07_trusted_envelope_has_exact_citations(self):
        env=self.validate(self.response())['review_envelope']
        citation=env['reported_in_PDF'][0]['citations'][0]
        self.assertEqual(citation['source_sentence'],self.ctx['sources'][0]['quote'])
        self.assertEqual(citation['page_number'],1)
        self.assertIsNone(env['predicted_by_GNN']['artifact_ref'])

    def test_08_missing_evidence_rejected(self):
        x=self.fixture();x['items'][0]['evidence_ids']=[]
        self.assertFalse(self.validate(self.response(x))['structural_valid'])

    def test_09_wrong_or_unselected_ID_rejected(self):
        x=self.fixture();x['items'][0]['evidence_ids']=['invented']
        self.assertFalse(self.validate(self.response(x))['structural_valid'])

    def test_10_scope_promotion_rejected(self):
        x=self.fixture();x['items'][0]['source_scope']='drug_direct'
        self.assertFalse(self.validate(self.response(x))['structural_valid'])

    def test_11_new_score_field_rejected(self):
        x=self.fixture();x['items'][0]['model_score']=.9
        self.assertFalse(self.validate(self.response(x))['structural_valid'])

    def test_12_out_of_source_claim_never_auto_passes(self):
        x=self.fixture();x['items'][0]['explanation_tr']='Kaynakta bulunmayan bir ifade.'
        result=self.validate(self.response(x))
        self.assertIsNone(result['semantic_success']);self.assertFalse(result['automatic_release'])
        self.assertEqual(result['semantic_review']['status'],'PENDING_HUMAN_REVIEW')

    def test_13_refusal_is_recorded_not_success(self):
        x={'schema_version':'WP12-local-llm-candidate-v1','status':'refused','refusal_code':'UNCERTAIN_EVIDENCE','items':[]}
        r=self.validate(self.response(x))
        self.assertEqual(r['status'],'MODEL_REFUSAL_RECORDED');self.assertIsNone(r['semantic_success'])

    def test_14_token_count_mismatch_stops_review(self):
        x=self.response();x['prompt_eval_count']+=1
        self.assertEqual(self.validate(x)['status'],'TOKEN_COUNT_ALIGNMENT_FAILED')

    def test_15_length_stop_and_incomplete_fail(self):
        for done,reason in [(True,'length'),(False,'stop')]:
            x=self.response();x.update(done=done,done_reason=reason)
            self.assertEqual(self.validate(x)['status'],'GENERATION_INCOMPLETE')

    def test_16_duplicate_JSON_keys_rejected(self):
        x=self.response();x['message']['content']='{"status":"candidate","status":"refused"}'
        self.assertFalse(self.validate(x)['structural_valid'])

    def test_17_no_thinking_or_tools_channel(self):
        x=self.response();x['message']['thinking']='unexpected'
        self.assertEqual(self.validate(x)['status'],'UNEXPECTED_OUTPUT_CHANNEL')

    def test_18_model_identity_rejected(self):
        x=self.response();x['model']='other'
        with self.assertRaises(ValueError):self.validate(x)

    def test_19_response_budget_rejected(self):
        x=self.response();x['eval_count']=385
        with self.assertRaises(ValueError):self.validate(x)

    def test_20_no_network_in_source_or_review(self):
        with patch('socket.socket',side_effect=AssertionError('network forbidden')):
            self.assertTrue(self.validate(self.response())['structural_valid'])

    def test_21_all_configured_input_hashes(self):
        for p,h in self.cfg['immutable_inputs_sha256'].items():
            self.assertEqual(c.sha(ROOT/p),h,p)
        self.assertEqual(c.sha(ROOT/self.cfg['runner']),self.cfg['runner_sha256'])

    def test_22_v2_memory_and_generation_settings_unchanged(self):
        self.assertEqual((self.cfg['RAM_floor_bytes'],self.cfg['GPU_floor_MiB'],self.cfg['HTTP_timeout_seconds']),
                         (2684354560,2048,60))
        req=c.request_for(self.ctx)
        self.assertEqual(req['options'],{'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108,'num_batch':32})
        self.assertFalse(req['truncate']);self.assertFalse(req['shift'])

    def test_23_one_request_no_bulk_switch(self):
        self.assertEqual(self.runner.count('.PostAsync('),1)
        self.assertIn('param([switch]$RunFirstCase)',self.runner)
        self.assertEqual((self.cfg['max_generation_requests'],self.cfg['stage2_enabled']),(1,False))

    def test_24_second_phase_all_57_slots_blocked(self):
        plan=c.read(c.QA/'stage2_plan_NOT_EXECUTABLE.json')
        # Slotların sayısı ve kapsamı mevcut frozen19×3 ile aynı; bu çalıştırıcı değildir.
        lists=[x for x in plan.values() if isinstance(x,list)]
        slots=next(x for x in lists if len(x)==57)
        self.assertEqual({(x['scenario_id'],x['repeat']) for x in slots},
                         {(f'S{i:02}',r) for i in range(1,20) for r in (1,2,3)})
        self.assertTrue(all(x['status']=='BLOCKED_STAGE2_NOT_ENABLED' for x in slots if (x['scenario_id'],x['repeat'])!=('S01',1)))
        first=next(x for x in slots if (x['scenario_id'],x['repeat'])==('S01',1))
        self.assertIn('FIRST',first['status'])

    def test_25_token_proof_covers_schema_question_and_quotes(self):
        req=c.request_for(self.ctx);render=self.proof['rendered_prompt']
        for text in ['CIKTI_SEMASI=',self.ctx['scenario']['question_tr'],*map(lambda s:s['quote'],self.ctx['sources'])]:
            # JSON içindeki yeni satırlar escaped olduğundan kaynak metnini tam request'ten doğrula.
            if text.startswith('CIKTI_') or text==self.ctx['scenario']['question_tr']:self.assertIn(text,render)
        data=json.loads(req['messages'][0]['content'].split('KAYNAK_VERI=',1)[1])
        self.assertEqual(data['sources'],self.ctx['sources'])
        self.assertEqual(self.proof['input_token_count'],919)


class NativeTokenizerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psutil
        # Yalnız vocabulary utility için guard; model inference kapısı2,5GiB kalır.
        if psutil.virtual_memory().available<1.5*2**30:raise unittest.SkipTest('VOCAB_ONLY_UTILITY_RAM_GUARD')
        cls.counter=VocabCounter();cls.template=template_from_gguf()['tokenizer.chat_template']

    @classmethod
    def tearDownClass(cls):cls.counter.close()

    def test_26_native_ABI_no_context(self):
        import ctypes
        self.assertEqual(ctypes.sizeof(Params),80);self.assertEqual(Params.vocab_only.offset,72)
        text=(ROOT/'scripts/wp12_vocab_counter.py').read_text(encoding='utf-8')
        self.assertIn('params.vocab_only=True',text)
        self.assertNotIn('llama_decode(',text);self.assertNotIn('llama_init_from_model(',text)

    def test_27_previous_actual_smoke_alignment(self):
        old=c.read(ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586/smoke_request.json')
        proof=c.make_token_proof(old,self.counter,self.template)
        self.assertEqual(proof['input_token_count'],41)
        rendered=render_single_user(old['messages'][0]['content'],self.template)
        self.assertEqual(len(self.counter.tokens(rendered,True)),42)

    def test_28_real_S01_count_and_repeatability(self):
        req=c.request_for(c.context());a=c.make_token_proof(req,self.counter,self.template)
        self.assertEqual(a,c.make_token_proof(req,self.counter,self.template))
        self.assertEqual(a['input_token_count'],919);self.assertTrue(a['admitted'])
        self.assertFalse(a['weights_loaded']);self.assertFalse(a['context_or_decode_created'])

    def test_29_oversized_input_rejected_without_cutting(self):
        req=c.request_for(c.context());req['messages'][0]['content']+='\nTEST_ONLY_TEXT '*2000
        proof=c.make_token_proof(req,self.counter,self.template)
        self.assertFalse(proof['admitted']);self.assertGreater(proof['input_token_count'],1536)
        # Gemma'nın özgün Jinja trim'i yalnız dış boşluğu alır; kanıt kesilmez.
        self.assertEqual(proof['rendered_prompt'].count('TEST_ONLY_TEXT'),2000)
        self.assertIn(req['messages'][0]['content'].strip(),proof['rendered_prompt'])

    def test_30_exact_render_hash(self):
        import hashlib
        proof=c.read(c.QA/'package/offline_token_proof.json')
        actual=render_single_user(c.request_for(c.context())['messages'][0]['content'],self.template)
        self.assertEqual(hashlib.sha256(actual.encode()).hexdigest(),proof['rendered_prompt_sha256'])


if __name__=='__main__':unittest.main(verbosity=2)
