"""Yalnız kullanıcı PowerShell'inde bir S04; frozen S04 prompt/şema değişmez."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from decimal import Decimal
import uuid
import wp12_openai_scenarios_v2 as s
import wp12_openai_S04_execution_v1 as b
import wp12_openai_client as old
from wp12_api_security import Evidence,load_key,public_sha,is_private_path,safe_error_fields,safe_request_id

RUN_ROOT=s.ROOT/'reports/qa/WP12/openai_S04_user_runs_v1'
EXTRA_SAFE={'BUDGET_V2_EXPLICIT_ACCEPTANCE_REQUIRED','HARD_V2_POLICY_MISMATCH','AGGREGATE_PILOT_BUDGET_STOP',
    'PRIOR_PUBLIC_RECORD_CHANGED_STOP','FROZEN_SCENARIO_REQUEST_CHANGED','CONTEXT_BUDGET','S04_EXECUTION_LOCKED'}


def safe_reason(error):
    value=error.args[0] if isinstance(error,ValueError) and error.args else None
    return value if isinstance(value,str) and value in EXTRA_SAFE|old.SAFE_REASONS else 'UNCLASSIFIED_EXCEPTION_NO_DETAILS_LOGGED'


def project_key():return load_key(s.ROOT,environ={})


def perform(folder,key,policy,send=old.transport):
    evidence=Evidence(folder,key);request=s.request('S04');ctx,payload,_,_=s.context('S04')
    evidence.json('source_request.json',request);evidence.json('source_provenance.json',payload)
    evidence.json('prompt_components_sha256.json',{
        'instructions_sha256':hashlib.sha256(request['instructions'].encode()).hexdigest(),
        'input_text_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode()).hexdigest(),
        'schema_sha256':hashlib.sha256(s.old.c.dump(request['text']['format']['schema']).encode()).hexdigest(),
        'quote_sha256':[x['quote_sha256'] for x in payload['sources']]})
    evidence.json('execution_scope.json',{'scenario':'S04','one_attempt_only':True,'other_scenarios':'NOT_AUTHORIZED_IN_THIS_EXECUTOR',
        'existing_budget_v2_limits_preserved':True,'model':'gpt-5.4-mini',
        'S01_formal_human_QA':'UNCHANGED_PENDING','S04_authority':'explicit user request after S07 review and normal-user command',
        'S07_formal_human_QA':'UNCHANGED_PENDING',
        'source_request_sha256':public_sha(folder/'source_request.json')})
    record={'scenario_id':'S04','model_requested':'gpt-5.4-mini','inference_attempts':0,'http_attempts':0,
        'automatic_retry':False,'human_review':'PENDING','automatic_release':False,'status':'PREFLIGHT',
        'budget_policy_version':policy['version'],'execution_scope_version':policy['execution_scope_version'],'api_key_available':True}

    def call(method,path,data,label):
        b.verify(policy)
        gate=b.projected(policy,HTTP=1)
        if not gate['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
        slot=old.claim_slot(b.CONTROL,'http',policy['max_total_HTTP_requests'],{
            'method':method,'path':path,'label':label,'scenario':'S04','run_directory':str(folder),
            'extra_budget_guard_USD':policy['reservation_per_HTTP_USD']})
        evidence.json(label+'_pre_HTTP_gate.json',{'aggregate_after_reservation':b.aggregate(policy),
            'source_hashes_and_dependencies_verified':True,'source_truncated':False,
            'inference_exact_token_gate_passed':(folder/'cost_preflight.json').exists() if path=='/responses' else 'NOT_AN_INFERENCE',
            'HTTP_local_slot':slot})
        record['http_attempts']+=1
        if path=='/responses':record['inference_attempts']=1
        response=send(method,path,data,key)
        meta={k:response[k] for k in ['HTTP_status','elapsed_seconds']}
        meta['request_id']=safe_request_id(response.get('request_id'),key)
        evidence.json(label+'_HTTP_metadata.json',meta)
        if not 200<=response['HTTP_status']<300:
            evidence.json(label+'_error_redacted.json',safe_error_fields(response['body'],key))
            record['failed_HTTP_stage']=label;record['HTTP_status']=response['HTTP_status'];record['API_request_id']=meta['request_id']
            raise ValueError('HTTP_ERROR_RECORDED_NO_RETRY')
        evidence.text(label+'_response_raw.json',response['body'])
        return old.parse_json(response['body']),meta

    try:
        if (b.CONTROL/'BILLING_OR_LIMIT_STOP.json').exists():raise ValueError('PILOT_BILLING_STOP_ALREADY_SET')
        old.claim_slot(b.CONTROL,'S04_attempt',1,{'scenario':'S04','run_directory':str(folder),'automatic_retry':False})
        # Bütün3HTTP+1inference rezervi sığmıyorsa henüz ilk HTTP bile gönderilmez.
        if not b.projected(policy,HTTP=3,inference=1)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
        model,_=call('GET','/models/gpt-5.4-mini',None,'model_access')
        if model.get('id') not in {'gpt-5.4-mini','gpt-5.4-mini-2026-03-17'}:raise ValueError('MODEL_ACCESS_NOT_CONFIRMED')
        counted,_=call('POST','/responses/input_tokens',s.old.token_count_payload(request),'input_token_count')
        try:estimate=s.old.estimate_upper(counted.get('input_tokens'),policy)
        except ValueError:raise ValueError('CONTEXT_BUDGET')
        evidence.json('cost_preflight.json',estimate)
        if not b.projected(policy,HTTP=1,inference=1)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
        record['inference_reservation_slot']=old.claim_slot(b.CONTROL,'inference_reservation',policy['max_inference_requests'],
            {'scenario':'S04','run_directory':str(folder),'reserved_USD':policy['reservation_per_inference_USD'],
                'estimate':estimate,'failure_does_not_release_reservation':True})
        response,meta=call('POST','/responses',request,'inference')
        record.update(model_returned=response.get('model'),response_id=response.get('id'),HTTP_status=meta['HTTP_status'],
            API_request_id=meta['request_id'],completion_status=response.get('status'),latency_seconds=meta['elapsed_seconds'])
        cost=s.old.usage_cost(response.get('usage'),policy);evidence.json('usage_and_token_cost.json',cost)
        result=s.assess(response,'S04');evidence.json('technical_and_review_gates.json',result)
        if 'parsed_json' in result:evidence.json('validated_JSON.json',result['parsed_json'])
        record['status']=result['status'];record['cost_status']=cost['status'];record['usage_token_cost_USD']=cost.get('actual_token_cost_USD')
        record['raw_response_sha256']=public_sha(folder/'inference_response_raw.json')
        if (cost['status']!='CALCULATED_FROM_USAGE' or cost.get('input_tokens',0)>6000 or cost.get('output_tokens_total',0)>1200
            or Decimal(cost['actual_token_cost_USD'])>Decimal(policy['reservation_per_inference_USD'])):
            Evidence(b.CONTROL,key).json('BILLING_OR_LIMIT_STOP.json',{'status':'UNEXPECTED_OR_UNKNOWN_USAGE_NO_RETRY'})
            record['status']='BILLING_OR_USAGE_REVIEW_REQUIRED_STOP'
    except BaseException as error:
        record['status']='FAILED_STOP_NO_RETRY';record['failure_reason']=safe_reason(error)
        if record['inference_attempts'] and not (folder/'usage_and_token_cost.json').exists() and not (b.CONTROL/'BILLING_OR_LIMIT_STOP.json').exists():
            Evidence(b.CONTROL,key).json('BILLING_OR_LIMIT_STOP.json',{'status':'INFERENCE_COST_OR_COMPLETION_UNKNOWN_NO_RETRY'})
    finally:
        evidence.json('run_record.json',record)
        evidence.json('aggregate_budget_after_run.json',b.aggregate(policy))
    return record


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self,message):print('INVALID_ARGUMENTS_NO_VALUES_ECHOED');raise SystemExit(2)
    parser=SafeParser();parser.add_argument('--run-s04',action='store_true')
    args=parser.parse_args();key=None;folder=None
    if not args.run_s04:
        print(json.dumps({'status':'OFFLINE_READY_S04_ONLY','api_key_available':bool(project_key()),'new_API_requests':0}));return 0
    try:
        if old.is_appcontainer():raise ValueError('APPCONTAINER_STOP_NO_API')
        policy=b.verify();key=project_key()
        if not key:
            print(json.dumps({'status':'PROJECT_DOTENV_KEY_ABSENT_STOP','api_key_available':False,'API_requests':0}));return 2
        folder=RUN_ROOT/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex);folder.mkdir(parents=True,exist_ok=False)
        result=perform(folder,key,policy)
        hashes={p.name:public_sha(p) for p in folder.iterdir() if not is_private_path(p) and p.is_file()}
        Evidence(folder,key).json('file_hashes.json',hashes)
        print(json.dumps({'status':result['status'],'api_key_available':True,'Evidence_directory':str(folder)}))
        return 0 if result['status']=='STRUCTURE_VALID_PENDING_AGENT_AND_HUMAN_REVIEW' else 2
    except BaseException as error:
        print(json.dumps({'status':'SAFE_STOP_NO_RETRY','reason':safe_reason(error),'api_key_available':bool(key),
            'Evidence_directory':str(folder) if folder else None}));return 1


if __name__=='__main__':raise SystemExit(main())
