"""Onay sonrası normal kullanıcı ortamında çalışan tek-S01 Responses istemcisi.

Stdlib HTTP, otomatik retry/redirect/proxy yok. Offline testlerde transport enjekte
edilir. API anahtarı yalnız env veya kök dotenv'den belleğe alınır; başlık yazılmaz.
"""
import argparse
from pathlib import Path
import json
import os
import ssl
import time
import uuid
from datetime import datetime,timezone
from urllib.request import Request,build_opener,ProxyHandler,HTTPSHandler,HTTPRedirectHandler
from urllib.error import HTTPError
import wp12_source_case as c
import wp12_openai_adapter as adapter
from wp12_api_security import load_key,key_available,public_sha,is_private_path,Evidence,safe_request_id,safe_error_fields,SecretBlocked,git_privacy_state

RUN_ROOT=c.ROOT/'reports/qa/WP12/openai_api_user_runs_v1'
CONTROL=adapter.QA/'control'

# Yalnız kod içinde tanımlı nedenler; key içerebilecek exception metni basılmaz.
SAFE_REASONS=frozenset('REQUEST_OR_BUDGET_SLOT_LIMIT_STOP UNAPPROVED_ENDPOINT RESPONSE_SIZE_LIMIT NORMAL_WINDOWS_USER_HOST_REQUIRED HOST_MEASUREMENT_MISSING HARD_BUDGET_OR_TOKEN_POLICY_STOP PRIVATE_FILE_TRACKED_BY_GIT_STOP PRICE_SNAPSHOT_EXPIRED_REFRESH_OFFICIAL_DOCS PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED APPROVED_REQUEST_CHANGED PILOT_BILLING_STOP_ALREADY_SET HTTP_ERROR_RECORDED_NO_RETRY MODEL_ACCESS_NOT_CONFIRMED INPUT_TOKEN_CAP_STOP_NO_INFERENCE PER_REQUEST_COST_CAP_STOP APPCONTAINER_STOP_NO_API DUPLICATE_JSON_KEY NON_JSON_CONSTANT'.split())


def safe_reason(error):
    value=error.args[0] if isinstance(error,ValueError) and error.args else None
    return value if isinstance(value,str) and value in SAFE_REASONS else 'UNCLASSIFIED_EXCEPTION_NO_DETAILS_LOGGED'


def parse_json(body):
    def pairs(items):
        d={}
        for k,v in items:
            if k in d:raise ValueError('DUPLICATE_JSON_KEY')
            d[k]=v
        return d
    def invalid(value):raise ValueError('NON_JSON_CONSTANT')
    return json.loads(body,object_pairs_hook=pairs,parse_constant=invalid)


def claim_slot(folder,stem,limit,data):
    """Kalıcı CreateNew slotu; belirsiz hata sonrası yeniden kullanılmaz."""
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    for number in range(1,limit+1):
        path=folder/f'{stem}_{number:02d}.json'
        try:fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL)
        except FileExistsError:continue
        with os.fdopen(fd,'w',encoding='utf-8') as f:json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False)
        return number
    raise ValueError('REQUEST_OR_BUDGET_SLOT_LIMIT_STOP')


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None


def transport(method,path,payload,key):
    if (method,path) not in {('GET','/models/gpt-5.4-mini'),('POST','/responses/input_tokens'),('POST','/responses')}:
        raise ValueError('UNAPPROVED_ENDPOINT')
    # OPENAI_BASE_URL, proxy ve key dışındaki dotenv alanları kullanılmaz.
    opener=build_opener(ProxyHandler({}),HTTPSHandler(context=ssl.create_default_context()),NoRedirect())
    data=None if payload is None else c.dump(payload).encode('utf-8')
    req=Request('https://api.openai.com/v1'+path,data=data,method=method,
        headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    started=time.monotonic()
    try:
        with opener.open(req,timeout=90) as response:
            status=response.status;body=response.read(4*1024*1024+1);request_id=response.headers.get('x-request-id')
    except HTTPError as error:
        status=error.code;body=error.read(4*1024*1024+1);request_id=error.headers.get('x-request-id')
    if len(body)>4*1024*1024:raise ValueError('RESPONSE_SIZE_LIMIT')
    return {'HTTP_status':status,'body':body.decode('utf-8'),'request_id':safe_request_id(request_id,key),
        'elapsed_seconds':time.monotonic()-started}


def is_appcontainer():
    if os.name!='nt':raise ValueError('NORMAL_WINDOWS_USER_HOST_REQUIRED')
    import ctypes as C
    token=C.c_void_p();adv=C.WinDLL('advapi32',use_last_error=True);kernel=C.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=C.c_void_p
    adv.OpenProcessToken.argtypes=[C.c_void_p,C.c_uint32,C.POINTER(C.c_void_p)]
    adv.GetTokenInformation.argtypes=[C.c_void_p,C.c_int,C.c_void_p,C.c_uint32,C.c_void_p]
    kernel.CloseHandle.argtypes=[C.c_void_p]
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(),8,C.byref(token)):raise ValueError('HOST_MEASUREMENT_MISSING')
    try:
        value=C.c_int();length=C.c_uint32()
        if not adv.GetTokenInformation(token,29,C.byref(value),4,C.byref(length)):raise ValueError('HOST_MEASUREMENT_MISSING')
        return bool(value.value)
    finally:kernel.CloseHandle(token)


def verify_policy():
    p=c.read(adapter.POLICY)
    from decimal import Decimal
    reserved=(Decimal(p['max_inference_requests'])*Decimal(p['reservation_per_inference_USD'])
        +Decimal(p['max_total_HTTP_requests'])*Decimal(p['reservation_per_HTTP_USD']))
    if (not 1<=p['max_inference_requests']<=10 or not 1<=p['max_total_HTTP_requests']<=10
        or reserved>Decimal('0.24') or p['input_token_cap']!=6000 or p['max_output_tokens']!=1200):
        raise ValueError('HARD_BUDGET_OR_TOKEN_POLICY_STOP')
    if git_privacy_state(c.ROOT)['tracked_private_files_detected']:raise ValueError('PRIVATE_FILE_TRACKED_BY_GIT_STOP')
    if datetime.now(timezone.utc)>datetime.fromisoformat(p['pricing_valid_until_UTC']):raise ValueError('PRICE_SNAPSHOT_EXPIRED_REFRESH_OFFICIAL_DOCS')
    for relative,digest in p['immutable_public_inputs_sha256'].items():
        if public_sha(c.ROOT/relative)!=digest:raise ValueError('PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED')
    if adapter.build_request()!=c.read(adapter.QA/'S01_Responses_request_NOT_SENT.json'):raise ValueError('APPROVED_REQUEST_CHANGED')
    return p


def perform(folder,key,policy,send=transport):
    """Tüm ağ yalnız bu açık fonksiyonda. İlk tek vaka sonrası her zaman durur."""
    evidence=Evidence(folder,key);request=adapter.build_request()
    # Önce hiçbir secret içermediğini denetle; içerik key ile çakışırsa gönderme.
    evidence.json('source_request.json',request)
    evidence.json('source_provenance.json',adapter.source_payload())
    import hashlib
    evidence.json('prompt_components_sha256.json',{
        'instructions_sha256':hashlib.sha256(request['instructions'].encode('utf-8')).hexdigest(),
        'user_content_sha256':hashlib.sha256(request['input'][0]['content'][0]['text'].encode('utf-8')).hexdigest(),
        'JSON_schema_sha256':hashlib.sha256(c.dump(request['text']['format']['schema']).encode('utf-8')).hexdigest(),
        'source_quote_sha256':[s['quote_sha256'] for s in adapter.source_payload()['sources']]})
    record={'model_requested':adapter.MODEL,'scenario_id':'S01','inference_attempts':0,'http_attempts':0,
        'api_key_available':True,'automatic_retry':False,'automatic_release':False,'human_review':'PENDING',
        'status':'PREFLIGHT','source_request_sha256':public_sha(Path(folder)/'source_request.json')}
    def call(method,path,payload,label):
        number=claim_slot(CONTROL,'http',policy['max_total_HTTP_requests'],{'method':method,'path':path,
            'label':label,'run_directory':str(folder),'extra_budget_guard_USD':policy['reservation_per_HTTP_USD']})
        record['http_attempts']+=1
        if path=='/responses':record['inference_attempts']=1
        response=send(method,path,payload,key)
        metadata={k:response[k] for k in ['HTTP_status','elapsed_seconds']}
        metadata['request_id']=safe_request_id(response.get('request_id'),key);metadata['HTTP_slot']=number
        evidence.json(label+'_HTTP_metadata.json',metadata)
        if not 200<=response['HTTP_status']<300:
            evidence.json(label+'_error_redacted.json',safe_error_fields(response['body'],key))
            raise ValueError('HTTP_ERROR_RECORDED_NO_RETRY')
        evidence.text(label+'_response_raw.json',response['body'])
        return parse_json(response['body']),metadata
    try:
        if (CONTROL/'BILLING_OR_LIMIT_STOP.json').exists():raise ValueError('PILOT_BILLING_STOP_ALREADY_SET')
        claim_slot(CONTROL,'S01_attempt',1,{'scenario':'S01','run_directory':str(folder),'automatic_retry':False})
        model,model_meta=call('GET','/models/gpt-5.4-mini',None,'model_access')
        if model.get('id') not in {adapter.MODEL,'gpt-5.4-mini-2026-03-17'}:raise ValueError('MODEL_ACCESS_NOT_CONFIRMED')
        counted,count_meta=call('POST','/responses/input_tokens',adapter.token_count_payload(request),'input_token_count')
        estimate=adapter.estimate_upper(counted.get('input_tokens'),policy)
        evidence.json('cost_preflight.json',estimate)
        record['inference_budget_slot']=claim_slot(CONTROL,'inference_reservation',policy['max_inference_requests'],
            {'scenario':'S01','run_directory':str(folder),'reserved_USD':policy['reservation_per_inference_USD'],
             'estimate':estimate,'failure_does_not_release_reservation':True})
        response,response_meta=call('POST','/responses',request,'inference')
        record.update(model_returned=response.get('model'),response_id=response.get('id'),API_request_id=response_meta['request_id'],
            HTTP_status=response_meta['HTTP_status'],completion_status=response.get('status'),latency_seconds=response_meta['elapsed_seconds'])
        billing=adapter.usage_cost(response.get('usage'),policy);evidence.json('usage_and_token_cost.json',billing)
        assessment=adapter.assess_response(response);evidence.json('structural_and_language_review.json',assessment)
        if 'parsed_json' in assessment:evidence.json('validated_JSON.json',assessment['parsed_json'])
        record['status']=assessment['status'];record['cost_status']=billing['status']
        record['estimated_actual_token_cost_USD']=billing.get('actual_token_cost_USD')
        record['raw_response_sha256']=public_sha(Path(folder)/'inference_response_raw.json')
        if (billing['status']!='CALCULATED_FROM_USAGE' or billing.get('input_tokens',0)>policy['input_token_cap']
            or billing.get('output_tokens_total',0)>policy['max_output_tokens']
            or __import__('decimal').Decimal(billing['actual_token_cost_USD'])>__import__('decimal').Decimal(policy['reservation_per_inference_USD'])):
            Evidence(CONTROL,key).json('BILLING_OR_LIMIT_STOP.json',{'status':'UNKNOWN_OR_UNEXPECTED_USAGE_STOP','no_automatic_resume':True})
            record['status']='BILLING_OR_USAGE_REVIEW_REQUIRED_STOP'
    except BaseException as error:
        # İstisna metni, traceback, request/header repr veya dotenv değeri yazılmaz.
        record['status']='FAILED_STOP_NO_RETRY';record['error_type']=type(error).__name__ if type(error).__name__ in {'ValueError','SecretBlocked'} else 'TRANSPORT_OR_SYSTEM_ERROR'
        record['failure_reason']=safe_reason(error)
        if record['inference_attempts'] and not (Path(folder)/'usage_and_token_cost.json').exists():
            if not (CONTROL/'BILLING_OR_LIMIT_STOP.json').exists():
                Evidence(CONTROL,key).json('BILLING_OR_LIMIT_STOP.json',{'status':'INFERENCE_COMPLETION_OR_COST_UNKNOWN_NO_RETRY'})
    finally:evidence.json('run_record.json',record)
    return record


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self,message):
            print('INVALID_ARGUMENTS_NO_VALUES_ECHOED');raise SystemExit(2)
    parser=SafeParser();parser.add_argument('--run-first-case',action='store_true');args=parser.parse_args()
    # Kullanıcı istemedikçe anahtar yükleyip API'ye bağlanılmaz; hazırlık durumu yalnız bool.
    if not args.run_first_case:
        print(c.dump({'status':'OFFLINE_ONLY_WAIT_USER_APPROVAL','api_key_available':key_available(c.ROOT),'API_requests':0}));return 0
    folder=None;key=None
    try:
        if is_appcontainer():raise ValueError('APPCONTAINER_STOP_NO_API')
        policy=verify_policy();key=load_key(c.ROOT)
        if not key:
            print(c.dump({'status':'API_KEY_ABSENT_STOP','api_key_available':False,'API_requests':0}));return 2
        name=datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex
        folder=RUN_ROOT/name;folder.mkdir(parents=True,exist_ok=False)
        result=perform(folder,key,policy)
        public={p.name:public_sha(p) for p in folder.iterdir() if p.is_file() and not is_private_path(p)}
        Evidence(folder,key).json('file_hashes.json',public)
        print(c.dump({'status':result['status'],'api_key_available':True,'Evidence_directory':str(folder)}))
        return 0 if result['status']=='PENDING_SOURCE_AND_HUMAN_REVIEW' else 2
    except BaseException as error:
        # Anahtar yüklendikten sonra bile beklenmeyen hata stdout'a değer taşımaz.
        print(c.dump({'status':'SAFE_STOP_NO_RETRY','reason':safe_reason(error),'api_key_available':bool(key),'Evidence_directory':str(folder) if folder else None}));return 1


if __name__=='__main__':raise SystemExit(main())
