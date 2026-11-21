"""Gerçek Gemma V2 run'ını değiştirmeden inceler; koşullu Qwen salt ön hazırlığı."""
from pathlib import Path
import hashlib
import struct
import json
import copy
import sys
import wp12_source_case as c
import wp12_method_v2 as method
import wp12_gemma_v2_user_run as oldrunner
import wp12_source_low_memory as low
import wp12_registered_templates as got
from wp12_vocab_counter import VocabCounter

QA=c.ROOT/'reports/qa/WP12/gemma_v2_review_qwen_preparation_v1'
RUN=c.ROOT/'reports/qa/WP12/gemma_v2_user_runs_v1/20261108_074723_6a9844b7f6d249c08bb38033d1ce218e'
MODEL_ROOT=Path('C:/Users/emrey/.ollama/models')
GEMMA_TEMPLATE='e0a42594d802e5d31cdc786deb4823edb8adff66094d49de8fffe976d753e348'
QWEN_TEMPLATE='eade0a07cac7712787bbce23d12f9306adb4781d873d1df6e16f7840fa37afec'


def registered_template(digest):
    path=MODEL_ROOT/'blobs'/('sha256-'+digest)
    if c.sha(path)!=digest:raise ValueError('REGISTERED_TEMPLATE_HASH_MISMATCH')
    return path.read_text(encoding='utf-8')


def audit():
    r=c.read(RUN/'run_record.json');raw=c.read(RUN/'source_response_raw.json')
    hashes=c.read(RUN/'file_hashes.json')
    assert {p.name for p in RUN.iterdir() if p.is_file()}==set(hashes)|{'file_hashes.json'}
    assert all(c.sha(RUN/name)==digest for name,digest in hashes.items())
    cfg,policy,_=oldrunner.verify()
    assert c.sha(oldrunner.CONFIG)==r['case_policy_sha256']
    assert c.sha(c.ROOT/cfg['runner'])==r['script_sha256']==cfg['runner_sha256']
    assert c.sha(RUN/'source_request.json')==r['request_sha256']
    assert c.sha(RUN/'source_response_raw.json')==r['response_sha256']
    assert c.read(RUN/'source_request.json')==method.request_for_S01()
    assert c.read(RUN/'case_context.json')==c.read(c.QA/'package/context.json')
    tags=c.read(RUN/'metadata_2_tags.json');tag=next(x for x in tags['models'] if x['name']==cfg['model'])
    norm=lambda d:d if d.startswith('sha256:') else 'sha256:'+d
    assert norm(tag['digest'])==r['expected_digest']==r['observed_digest']==cfg['model_digest']
    identity=r['identity_validation']
    assert 'sha256:'+c.sha(Path(identity['local_wrapper_path']))==identity['local_wrapper_manifest_file_sha256']
    assert 'sha256:'+c.sha(Path(identity['source_manifest_path']))==cfg['model_digest']
    claim=c.ROOT/cfg['generation_slot']
    assert c.sha(claim)==c.sha(RUN/'generation_claim_copy.json')
    assert c.read(claim)['run_directory']==str(RUN)
    assert r['inference_attempts']==1 and raw['done'] is True and raw['done_reason']=='stop' and r['HTTP_status']==200
    proof=c.read(RUN/'token_budget.json')
    original=oldrunner.assess_response(raw,proof)
    original['trial_id']=cfg['trial_id']
    assert original==c.read(RUN/'structural_review.json')
    candidate=json.loads(raw['message']['content'])
    diagnostic=method.inspect_candidate(candidate) # Gerçek server token sayısı taklit edilmez; saf ayrı içerik denetimi.
    assert diagnostic['schema_valid'] and diagnostic['source_contract_valid']
    # Sınırlı marker kontrolü ilk İngilizce cümleyi kaçırıyor: insan/ajan dil incelemesi bu nedenle zorunlu.
    semantic={'review_kind':'AGENT_SOURCE_AND_LANGUAGE_COMPARISON_NOT_HUMAN_APPROVAL',
        'language':'FAIL','source_faithfulness':'CORE_CLAIMS_SUPPORTED_WITH_OMISSIONS',
        'primary_quote_kind_alignment':'PASS','task_scope':'BOTH_PURPOSES_PRESENT_IN_ENGLISH_PRODUCT_DETAILS_OMITTED',
        'human_review':'PENDING','automatic_release':False,'new_ADR_score_or_label':False,
        'v2_source_improvement_is_not_generalization_evidence':True,
        'findings':[
            {'item':0,'model_text':candidate['items'][0]['explanation_tr'],
             'source':'Physical1: Erythromycin Tablets BP250mg; active erythromycin; macrolide antibiotics.',
             'assessment':'İngilizce. Etkin madde ve sınıf kaynakta var. BP250mg ürün tanımı atlanmış; yeni klinik olgu yok.',
             'translation_reviewer_NOT_MODEL':'Erythromycin Tablets, etkin madde erythromycin içeren farmasötik bir üründür. Erythromycin bir makrolid antibiyotiktir.'},
            {'item':1,'model_text':candidate['items'][1]['explanation_tr'],
             'source':'Physical6: red, round, biconvex, enteric-coated tablets; packaging counts.',
             'assessment':'İngilizce. Renk/şekil/enterik kaplama alıntıyla uyumlu. Ambalaj sayıları atlanmış; birincil quote-ID ve kind doğru.',
             'translation_reviewer_NOT_MODEL':'Erythromycin Tablets kırmızı renkli, yuvarlak, bikonveks, enterik kaplı tabletlerdir.'}],
        'refusal':'NO_REFUSAL; V1 yanlış görsel-metni reti bu yanıtta yok.',
        'uncertainty':'S01 alıntılarında unknown/might qualifier yok; S04/S07 ayrıca çalıştırılmış sayılmaz.',
        'language_declaration_tr_is_false_for_actual_sentence_language':True}
    samples=c.read(RUN/'memory_samples.json');entry=c.read(RUN/'preflight_measurements.json')
    all_entries=[r['memory_before'],entry['memory'],*r['admission_samples'],r['memory_immediately_before']]
    assert all(low.entry_gate(x,r['GPU_before'],policy) for x in all_entries)
    assert all(not low.runtime_warning(x,policy) for x in samples)
    return {'raw_files':len(hashes)+1,'hashes_valid':True,'identity_and_sources_valid':True,'claim_consumed_and_preserved':True,
        'transport_generation':{'HTTP':200,'done':True,'done_reason':'stop','server_prompt_tokens':raw['prompt_eval_count'],
            'offline_planned_tokens':proof['input_token_count'],'output_tokens':raw['eval_count'],
            'server_total_seconds':raw['total_duration']/1e9,'server_load_seconds':raw['load_duration']/1e9,
            'client_block_plus_review_seconds':r['elapsed_seconds'],'generation_completed':True},
        'original_pipeline_status_preserved':original,'independent_posthoc_content_check':diagnostic,
        'semantic_agent_review':semantic,'memory':{'samples':len(samples),
            'entry_RAM_GiB':r['memory_before']['available_bytes']/2**30,
            'immediate_RAM_GiB':r['memory_immediately_before']['available_bytes']/2**30,
            'sampled_min_RAM_GiB':min(x['available_bytes'] for x in samples)/2**30,
            'sampled_min_commit_GiB':min(x['commit_available_bytes'] for x in samples)/2**30,
            'OS_pressure_samples_true':sum(x['low_memory_notification'] for x in samples),
            'GPU_before_after_MiB':[r['GPU_before']['free_MiB'],r['GPU_after']['free_MiB']],
            'peak_GPU_and_process_RAM':'UNKNOWN','experimental_warnings_observed':False},
        'branch_B':{'authorized':True,'reason':'Completed real output is English despite mandatory Turkish; NOT because of token mismatch.',
            'Gemma_A_remains_FAIL':True,'new_inference':0,'no_Gemma_retry_or_claim_reset':True}}


def gguf_architecture(path):
    """Metadata≤16MiB; token listeleri tutulmaz; ağırlıklar okunmaz."""
    keys={'general.architecture','general.name','qwen3.block_count','qwen3.embedding_length',
        'qwen3.attention.head_count','qwen3.attention.head_count_kv','qwen3.attention.key_length','qwen3.attention.value_length',
        'tokenizer.ggml.add_bos_token','tokenizer.ggml.add_eos_token','tokenizer.ggml.bos_token_id','tokenizer.ggml.eos_token_id'}
    with Path(path).open('rb') as f:
        def take(n):
            if f.tell()+n>16*2**20:raise ValueError('METADATA_LIMIT')
            b=f.read(n)
            if len(b)!=n:raise ValueError('TRUNCATED_GGUF')
            return b
        def number(fmt):return struct.unpack('<'+fmt,take(struct.calcsize('<'+fmt)))[0]
        def string(keep):
            n=number('Q')
            if keep:return take(n).decode('utf-8')
            if f.tell()+n>16*2**20:raise ValueError('METADATA_LIMIT')
            f.seek(n,1)
        def value(kind,keep):
            if kind==8:return string(keep)
            if kind==9:
                sub=number('I');count=number('Q')
                if count>1000000 or sub==9:raise ValueError('ARRAY_LIMIT')
                for _ in range(count):value(sub,False)
                return None
            return number({0:'B',1:'b',2:'H',3:'h',4:'I',5:'i',6:'f',7:'?',10:'Q',11:'q',12:'d'}[kind])
        if take(4)!=b'GGUF' or number('I')!=3:raise ValueError('GGUF3_REQUIRED')
        number('Q');count=number('Q');out={}
        for _ in range(count):
            key=string(True);v=value(number('I'),key in keys)
            if key in keys:out[key]=v
        return out


def qwen_identity_and_resources():
    p=MODEL_ROOT/'manifests/registry.ollama.ai/library/qwen3/4b-instruct-2507-q4_K_M'
    historic=c.read(c.ROOT/'configs/WP12_user_host_smoke_FROZEN_v1.json')
    digest='sha256:'+c.sha(p);assert digest==historic['manifest_digest']
    manifest=c.read(p);layers=manifest['layers'];details=[]
    for ref in [manifest['config'],*layers]:
        blob=MODEL_ROOT/'blobs'/ref['digest'].replace(':','-')
        assert blob.stat().st_size==ref['size'] and 'sha256:'+c.sha(blob)==ref['digest']
        details.append({'mediaType':ref['mediaType'],'size':ref['size'],'digest':ref['digest'],'SHA_verified':True})
    model=next(x for x in layers if x['mediaType']=='application/vnd.ollama.image.model')
    path=MODEL_ROOT/'blobs'/model['digest'].replace(':','-');dims=gguf_architecture(path)
    kv=dims['qwen3.block_count']*2048*dims['qwen3.attention.head_count_kv']*(dims['qwen3.attention.key_length']+dims['qwen3.attention.value_length'])*2
    # Qwen'e özel plan: eski3GiB RAM tabanı korunur, GPU dosya+KV+0,75GiB marjıyla yukarı yuvarlanır.
    import math
    gpu_gib=math.ceil((model['size']/2**30+kv/2**30+.75)*4)/4
    return {'model':'qwen3:4b-instruct-2507-q4_K_M','local_registered_digest':digest,
        'historic_frozen_digest_matches':True,'API_digest_current':'PENDING_NORMAL_USER_POWERSHELL_NO_APPCONTAINER_CALL',
        'registered_manifest_path':str(p),'layer_hashes':details,'model_file':str(path),'model_bytes':model['size'],
        'architecture':dims,'full_FP16_KV_bytes_at_2048':kv,'actual_runtime_peak':'UNKNOWN_NO_MODEL_LOAD',
        'memory_policy':{'version':'WP12-QWEN4B-CONDITIONAL-MEMORY-v1','RAM_floor_bytes':3221225472,
            'GPU_floor_MiB':int(gpu_gib*1024),'commit_floor_bytes':4294967296,
            'runtime_RAM_floor_bytes':1073741824,'runtime_commit_floor_bytes':1073741824,
            'OS_pressure_signal_required':True,'automatic_threshold_lowering':False,'safety_guarantee':False,
            'basis':'Existing Qwen3GiB host floor retained; GPU ceil0.25GiB(model file+full FP16 KV+0.75GiB unmeasured runtime allowance); commit4GiB; assumptions not measured peak.'}}


def token_diagnostics(resources):
    import psutil
    if psutil.virtual_memory().available<1610612736:
        return {'status':'BLOCKED_VOCAB_ONLY_RAM_GUARD','counts':'UNKNOWN','inference':0}
    req=c.read(RUN/'source_request.json');template=registered_template(GEMMA_TEMPLATE)
    gemma_render=got.execute(template,req['messages'])
    qreq=copy.deepcopy(req);qreq['model']=resources['model']
    qwen_render=got.execute(registered_template(QWEN_TEMPLATE),qreq['messages'])
    results={'status':'VOCAB_ONLY_PROBE_COMPLETED_NO_INFERENCE','Gemma_actual_registered_template_SHA256':GEMMA_TEMPLATE,
        'Gemma_Go_rendered_prompt':gemma_render,'Gemma_Jinja_saved_prompt':c.read(RUN/'token_budget.json')['rendered_prompt'],
        'Qwen_registered_template_SHA256':QWEN_TEMPLATE,'Qwen_rendered_prompt':qwen_render,
        'Qwen_request_same_except_model':True,'inference':0,'weights_loaded':False,'server_prompt_bytes_captured':False}
    with VocabCounter() as counter:
        results['Gemma_registered_with_special_tokens']=len(counter.tokens(gemma_render,True))
        results['Gemma_registered_without_special_tokens']=len(counter.tokens(gemma_render,False))
        results['Gemma_saved_Jinja_count']=len(counter.tokens(results['Gemma_Jinja_saved_prompt'],False))
        results['Gemma_recorded_server_count']=c.read(RUN/'source_response_raw.json')['prompt_eval_count']
        results['Gemma_registered_matches_server_count']=results['Gemma_registered_with_special_tokens']==results['Gemma_recorded_server_count']
    if psutil.virtual_memory().available<1610612736:
        results['Qwen_count_status']='BLOCKED_VOCAB_ONLY_RAM_GUARD';return results
    with VocabCounter(model_path=Path(resources['model_file'])) as counter:
        results['Qwen_registered_with_special_tokens']=len(counter.tokens(qwen_render,True))
        results['Qwen_registered_without_special_tokens']=len(counter.tokens(qwen_render,False))
        results['Qwen_count_status']='OFFLINE_ONLY_NO_SERVER_VERIFICATION'
        results['Qwen_context_admitted']=results['Qwen_registered_with_special_tokens']<=1536
    c.save_new(QA/'Qwen_S01_v2_request_NOT_SENT.json',qreq)
    return results
