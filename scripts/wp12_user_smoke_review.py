"""Kullanıcının bağımsız PowerShell çıktısını ağ/LLM çağrısı olmadan doğrula.

Hash, dosya tutarlılığıdır; gerçek host çalışmasını kriptografik olarak tasdik etmez.
Hiçbir kayıt otomatik PDF açıklaması veya klinik doğruluk onayı haline gelmez.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import re
import uuid

ROOT=Path(__file__).resolve().parents[1]
MODEL='qwen3:4b-instruct-2507-q4_K_M'
DIGEST='sha256:0edcdef34593eac1aa2be9c7d06c432dcf81945adca5eca2f27662c18f168ba0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unique_object(pairs):
    result={}
    for k,v in pairs:
        if k in result: raise ValueError('duplicate JSON key: '+k)
        result[k]=v
    return result


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'),object_pairs_hook=unique_object)


def require(condition, message):
    if not condition: raise ValueError(message)


def verify_file_manifest(folder):
    folder=folder.resolve()
    m=read(folder/'file_hashes.json')
    require(isinstance(m,dict) and 'run_record.json' in m,'missing run record hash')
    names={p.name for p in folder.iterdir() if p.is_file() and p.name!='file_hashes.json'}
    require(set(m)==names,'manifest and physical file list differ')
    for name,h in m.items():
        require(isinstance(name,str) and '/' not in name and '\\' not in name and name not in ('.','..'),'unsafe manifest path')
        p=folder/name
        require(p.resolve().parent==folder and not p.is_symlink(),'source escapes run directory')
        require(re.fullmatch(r'[0-9a-f]{64}',h) is not None and sha(p)==h,'file hash mismatch: '+name)
    return m


def validate_run(folder):
    folder=Path(folder).resolve();manifest=verify_file_manifest(folder)
    r=read(folder/'run_record.json')
    require(r['schema_version']=='WP12-user-smoke-run-v1','unknown run version')
    require(r['model']==MODEL and r['expected_digest']==DIGEST,'selected model changed')
    require(r['thresholds']=={'host_free_bytes':3221225472,'GPU_free_MiB':2560},'safety threshold changed')
    require(r['frozen_scenarios_sha256']==sha(ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json'),'scenario lock mismatch')
    require(r['source_contract_sha256']==sha(ROOT/'docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md'),'contract lock mismatch')
    require(r['script_sha256']==sha(ROOT/'scripts/WP12_UserPowerShellSmoke_v1.ps1'),'runner script hash mismatch')
    require(r['inference_attempts'] in (0,1),'more than one inference attempted')
    require(r['new_downloads']==r['models_pulled']==r['processes_terminated']==r['real_scenario_repeats']==0,'forbidden action reported')
    require(r['service_started'] is False and r['security_changed'] is False and r['automatic_release'] is False,'forbidden state change')
    base={'file_hashes_valid':True,'verified_files':len(manifest),'model':MODEL,
          'status':'EXTERNAL_RECORD_CONSISTENT_NO_SMOKE_PASS','run_status':r['status'],
          'origin_authentication':'NOT_CRYPTOGRAPHICALLY_ATTESTED; user supplied record',
          'human_semantic_review':'NOT_PERFORMED_TECHNICAL_ECHO_ONLY',
          'auto_release':False,'PDF_explanation_quality':'NOT_TESTED','real_scenarios_executed':0}
    if r['inference_attempts']==0:
        require(not r['status'].startswith('SMOKE_TECHNICAL_PASS'),'pass claimed without inference')
        return base
    require(r['is_appcontainer'] is False,'inference was not run in independent host context')
    require(r['observed_digest']==DIGEST,'runtime model digest mismatch')
    for key in ('memory_before','memory_immediately_before'):
        require(r[key]['available_bytes']>=3221225472,'inference started below RAM gate')
    for key in ('GPU_before','GPU_immediately_before'):
        require(r[key]['free_MiB']>=2560,'inference started below VRAM gate')
    require(r['already_loaded_models']==0,'preexisting loaded model was not isolated')
    metadata_version=read(folder/'metadata_1_version.json')
    require(metadata_version['version']==r['server_version'],'server version mismatch')
    tags=read(folder/'metadata_2_tags.json')
    found=[x for x in tags['models'] if x.get('name')==MODEL]
    require(len(found)==1,'selected model not unique in tags')
    require('sha256:'+found[0]['digest'].removeprefix('sha256:')==DIGEST,'API tags digest mismatch')
    require(not read(folder/'metadata_3_ps.json')['models'],'model was already loaded')
    request=read(folder/'smoke_request.json')
    require(request=={
        'model':MODEL,'stream':False,'think':False,'keep_alive':0,
        'messages':[{'role':'user','content':'Technical echo only. Return exactly {"probe":"WP12_LOCAL_SMOKE_V1"}. No medical content, no explanation.'}],
        'format':{'type':'object','properties':{'probe':{'type':'string','enum':['WP12_LOCAL_SMOKE_V1']}},'required':['probe'],'additionalProperties':False},
        'options':{'num_ctx':2048,'num_predict':384,'temperature':0,'seed':20261108}},'request differs from frozen technical smoke')
    require(sha(folder/'smoke_request.json')==r['request_sha256'],'request hash mismatch')
    # Hatalı/timeout kayıtları saklanır; başarıya çevrilmez.
    if 'smoke_response_raw.json' not in manifest:
        require(r['status']!='SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW','missing response despite pass')
        base['status']='EXTERNAL_SMOKE_FAILED_OR_INCOMPLETE';return base
    require(sha(folder/'smoke_response_raw.json')==r['response_sha256'],'response hash mismatch')
    response=read(folder/'smoke_response_raw.json')
    if r['status']!='SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW':
        base['status']='EXTERNAL_SMOKE_FAILED_OR_INCOMPLETE';return base
    require(r['HTTP_status']==200 and response['done'] is True and response['done_reason']=='stop','response not completed successfully')
    require(response['model']==MODEL,'response model changed')
    require(not response['message'].get('thinking') and not response['message'].get('tool_calls'),'unexpected thinking/tool output')
    echo=json.loads(response['message']['content'],object_pairs_hook=unique_object)
    require(echo=={'probe':'WP12_LOCAL_SMOKE_V1'},'echo schema mismatch')
    require(isinstance(response['prompt_eval_count'],int) and 0<response['prompt_eval_count']<=1536,'prompt budget not demonstrated')
    require(isinstance(response['eval_count'],int) and 0<response['eval_count']<=384,'output budget invalid')
    require(response['prompt_eval_count']==r['prompt_eval_count'] and response['eval_count']==r['eval_count'],'token count log mismatch')
    samples=read(folder/'memory_samples.json')
    require(isinstance(samples,list) and len(samples)>=2,'missing memory samples')
    base.update(status='EXTERNAL_TECHNICAL_ECHO_PASS_PENDING_USER_REVIEW',
                observed_min_host_available_bytes=min(s['available_bytes'] for s in samples),
                memory_measurement='sampled host memory, not exact inference peak RAM/VRAM',
                schema_conclusion='one schema-bearing request accepted and output consistent; not general semantic guarantee',
                comparative_cause='if host succeeds while Codex fails, evidence for environment-specific access issue; exact filter unproven')
    return base


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run_directory',type=Path)
    args=parser.parse_args()
    allowed=(ROOT/'reports/qa/WP12/user_smoke_runs').resolve()
    folder=args.run_directory.resolve()
    if folder.parent!=allowed: raise ValueError('Only a direct user_smoke_runs child is accepted')
    target=ROOT/'reports/qa/WP12/user_smoke_reviews'/uuid.uuid4().hex
    target.mkdir(parents=True,exist_ok=False)
    try:result=validate_run(folder)
    except Exception as e:result={'status':'REJECTED_OR_INCOMPLETE_EXTERNAL_EVIDENCE','error_type':type(e).__name__,'error':str(e),'auto_release':False}
    result.update(reviewed_at=datetime.datetime.now().astimezone().isoformat(),source_directory=str(folder))
    (target/'review.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    print('New review record:',target)


if __name__=='__main__':
    main()
