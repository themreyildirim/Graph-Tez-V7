"""Gerçek smoke içeriği/belleği için ağsız ikinci kontrol. Inference çalıştırmaz."""
import datetime
import json
from jsonschema import Draft202012Validator


def require(value,message):
    if not value:raise ValueError(message)


def parse_unique(text):
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('duplicate response JSON key')
            out[k]=v
        return out
    return json.loads(text,object_pairs_hook=pairs)


def audit_content(r,request,response,samples,cfg):
    model=cfg['model'];api=cfg['expected_API_model_digest'];wrapper=cfg['local_wrapper_manifest_file_sha256']
    require(r['model']==request['model']==response['model']==model,'model mismatch')
    iv=r['identity_validation']
    require(r['expected_digest']==r['observed_digest']==iv['observed_API_model_digest']==iv['expected_API_model_digest']==iv['source_manifest_file_sha256']==api,'API identity mismatch')
    require(r['local_wrapper_expected_sha256']==iv['local_wrapper_manifest_file_sha256']==wrapper,'wrapper identity mismatch')
    require(iv['identity_binding_valid'] is True and iv['config_and_layer_references_equal'] is True,'lineage not valid')
    require(type(r['inference_attempts']) is int and r['inference_attempts']==1,'exactly one recorded inference required')
    require(r['new_downloads']==r['models_pulled']==r['real_scenario_repeats']==0,'unexpected download or real scenario')
    require(r['automatic_release'] is False and r['is_appcontainer'] is False,'origin/release condition')
    require(r['HTTP_status']==200 and response['done'] is True and response['done_reason']=='stop','incomplete response')
    require(r['done'] is True and r['done_reason']==response['done_reason'],'completion record mismatch')
    require(request['options']=={k:cfg[k] for k in ['num_ctx','num_predict','temperature','seed','num_batch']},'request options changed')
    require(request['think'] is False and request['stream'] is False and request['keep_alive']==0,'request switches changed')
    expected_schema={'type':'object','properties':{'probe':{'type':'string','enum':['WP12_GEMMA1B_SMOKE_V2']}},'required':['probe'],'additionalProperties':False}
    require(request['format']==expected_schema,'technical schema changed')
    Draft202012Validator.check_schema(request['format'])
    echo=parse_unique(response['message']['content'])
    Draft202012Validator(request['format']).validate(echo)
    require(echo=={'probe':'WP12_GEMMA1B_SMOKE_V2'},'unexpected echo')
    require(not response['message'].get('thinking') and not response['message'].get('tool_calls'),'unexpected output channel')
    for key,limit in [('prompt_eval_count',1536),('eval_count',384)]:
        require(type(response[key]) is int and 0<response[key]<=limit and r[key]==response[key],'token count/budget mismatch')
    host=cfg['v2_admission']['host_available_bytes'];gpu=cfg['v2_admission']['GPU_free_MiB'];commit=cfg['v2_admission']['system_commit_available_bytes']
    stable=r['admission_samples'];require(len(stable)==5,'stability count')
    starts=[r['memory_before'],*stable,r['memory_immediately_before']]
    require(all(x['available_bytes']>=host and x['commit_available_bytes']>=commit for x in starts),'admission memory/commit gate')
    require(all(r[k]['free_MiB']>=gpu for k in ['GPU_before','GPU_immediately_before']),'admission GPU gate')
    dt=datetime.datetime.fromisoformat
    span=(dt(stable[-1]['at'])-dt(stable[0]['at'])).total_seconds()
    require(span>=4,'stability interval')
    require(isinstance(samples,list) and len(samples)>=2,'runtime samples missing')
    require(all(x['available_bytes']>=cfg['runtime_host_warning_bytes'] for x in samples),'runtime host warning threshold')
    require(r['memory_after']['available_bytes']>=cfg['runtime_host_warning_bytes'],'final host warning threshold')
    times=[dt(x['at']) for x in samples]
    require(all(a<=b for a,b in zip(times,times[1:])),'sample time order')
    require(dt(r['started_at'])<=times[0]<=times[-1]<=dt(r['finished_at']),'sample bounds')
    created=dt(response['created_at'].replace('Z','+00:00'))
    require(dt(r['started_at'])<=created<=dt(r['finished_at']),'response time outside run')
    require(r['elapsed_seconds']<cfg['HTTP_timeout_seconds'],'recorded duration exceeds timeout')
    require(0<=response['load_duration']<=response['total_duration'],'invalid server durations')
    return {'status':'TECHNICAL_SMOKE_VERIFIED','JSON_Schema_valid':True,'echo':echo,
        'HTTP_status':200,'done':True,'done_reason':'stop','recorded_inference_requests':1,
        'download_requests_in_record':0,'stability_samples':len(stable),'stability_span_seconds':span,
        'initial_available_RAM_GiB':r['memory_before']['available_bytes']/2**30,
        'pre_inference_available_RAM_GiB':r['memory_immediately_before']['available_bytes']/2**30,
        'stability_min_RAM_GiB':min(x['available_bytes'] for x in stable)/2**30,
        'runtime_host_samples':len(samples),'sampled_min_available_RAM_GiB':min(x['available_bytes'] for x in samples)/2**30,
        'sampled_min_commit_available_GiB':min(x['commit_available_bytes'] for x in samples)/2**30,
        'post_available_RAM_GiB':r['memory_after']['available_bytes']/2**30,
        'GPU_before_free_MiB':r['GPU_before']['free_MiB'],'GPU_immediate_free_MiB':r['GPU_immediately_before']['free_MiB'],
        'GPU_after_free_MiB':r['GPU_after']['free_MiB'],'runtime_peak_GPU_memory':'UNKNOWN_NOT_SAMPLED',
        'exact_runtime_peak_host_memory':'UNKNOWN_SAMPLED_HOST_TOTAL_ONLY',
        'client_elapsed_seconds':r['elapsed_seconds'],'server_total_seconds':response['total_duration']/1e9,
        'server_load_seconds':response['load_duration']/1e9,'prompt_tokens':response['prompt_eval_count'],'output_tokens':response['eval_count'],
        'readiness':'TECHNICAL_GATE_PASSED_FOR_NEXT_CONTROLLED_19x3_STAGE; NOT_STARTED',
        'full_source_prompt_quality':'NOT_TESTED','automatic_release':False,
        'scope_limit':'user log+matching runner evidence; not system-wide network audit or cryptographic runtime attestation'}
