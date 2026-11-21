"""İki gerçek v2 denemesinin ağsız/salt okunur teşhisi; hiçbir trainer/LLM çağrısı yok."""
import datetime
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def diagnose(record, version, tags, *, script_hash, filenames):
    """Bu özel guard hatasını yalnız aynı betik hash'i ve metadata kanıtıyla tanımlar."""
    if record['script_sha256']!=script_hash:raise ValueError('runner version not verified')
    found=[x for x in tags['models'] if x['name']==record['model']]
    if len(found)!=1:raise ValueError('model metadata not unique')
    observed='sha256:'+found[0]['digest'].removeprefix('sha256:')
    if observed!=record['observed_digest']:raise ValueError('run/API digest inconsistency')
    if version['version']!=record['server_version']:raise ValueError('server version mismatch')
    exact_guard=('System.Management.Automation.RuntimeException: MODEL_DIGEST_MISMATCH: do not silently switch model')
    if record['error']!=exact_guard or record['inference_attempts']!=0:
        raise ValueError('outside verified digest-guard failure case; do not infer cause')
    if any(x in filenames for x in ('smoke_request.json','smoke_response_raw.json','metadata_3_ps.json')):
        raise ValueError('unexpected stage evidence; manual review required')
    ram=record['memory_before']['available_bytes'];gpu=record['GPU_before']['free_MiB']
    commit=record['memory_before']['commit_available_bytes']
    elapsed=(datetime.datetime.fromisoformat(record['finished_at'])-datetime.datetime.fromisoformat(record['started_at'])).total_seconds()
    return {'started_at':record['started_at'],'finished_at':record['finished_at'],
        'wall_clock_elapsed_seconds':elapsed,'duration_scope':'whole script, not HTTP latency',
        'record_status':record['status'],'confirmed_failure':'MODEL_DIGEST_MISMATCH',
        'failure_stage':'DIGEST_GUARD_BEFORE_API_PS_BEFORE_MEMORY_GATE_BEFORE_CHAT',
        'exception':record['error'],'timeout_stage':'NOT_REACHED_EXPLICIT_GUARD_EXCEPTION',
        'timeout_detected':False,'server_access':'VERIFIED_METADATA_RESPONSES',
        'server_version':version['version'],'is_appcontainer':record['is_appcontainer'],
        'metadata_HTTP_exact_status':'UNKNOWN_NOT_LOGGED','metadata_HTTP_success_class':'2xx inferred from successful GetStringAsync',
        'chat_HTTP_status':'NOT_APPLICABLE_REQUEST_NOT_SENT','inference_request_sent':False,
        'inference_attempts':0,'model_load_requested_by_this_script':False,
        'server_model_residency':'UNKNOWN_NO_API_PS_RESPONSE_OR_SERVER_LOAD_LOG',
        'RAM_available_bytes':ram,'RAM_available_GiB':ram/2**30,
        'RAM_deficit_MiB':max(0,2684354560-ram)/2**20,
        'GPU_free_MiB':gpu,'commit_available_GiB':commit/2**30,
        'memory_gate_executed':False,'stability_gate_executed':False,
        'initial_RAM_recomputed_pass':ram>=2684354560,'initial_GPU_recomputed_pass':gpu>=2048,
        'initial_commit_recomputed_pass':commit>=3221225472,
        'initial_combined_gate_recomputed_pass':ram>=2684354560 and gpu>=2048 and commit>=3221225472,
        'expected_digest_in_script':record['expected_digest'],'observed_API_digest':observed,
        'source_contract_sha256':record['source_contract_sha256'],
        'frozen_scenarios_sha256':record['frozen_scenarios_sha256']}
