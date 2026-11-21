"""Kullanıcı yetkili farklı-hesap S01 denemesi; v1 kaynak/metot ve kayıtlar sabit.

Eski billing-stop silinmez. Yeni scope en fazla bir üretim denemesidir. Bütçe
eski ve yeni ledger toplamıyla kontrol edilir. Yalnız normal kullanıcı Windows.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime
from decimal import Decimal
from pathlib import Path
import uuid
import json
import wp12_openai_client as original
import wp12_openai_adapter as adapter
from wp12_api_security import load_key,public_sha,is_private_path,Evidence

ROOT=adapter.c.ROOT
QA=ROOT/'reports/qa/WP12/openai_corrected_account_preparation_v1'
POLICY=ROOT/'configs/WP12_OPENAI_CORRECTED_ACCOUNT_S01_v1.json'
CONTROL=QA/'control'
PRIOR_CONTROL=adapter.QA/'control'
RUN_ROOT=ROOT/'reports/qa/WP12/openai_corrected_account_user_runs_v1'


def project_key():
    # Kullanıcı yeni anahtarı .env'ye yazdı: miras alınan eski process key kullanılmaz.
    return load_key(ROOT,environ={})


def aggregate_budget(policy,roots=None):
    roots=[PRIOR_CONTROL,CONTROL] if roots is None else roots
    http=0;inferences=0;reserved=Decimal('0')
    for root in roots:
        for p in Path(root).glob('http_*.json'):
            row=original.c.read(p)
            amount=Decimal(row['extra_budget_guard_USD'])
            if amount!=Decimal(policy['reservation_per_HTTP_USD']):raise ValueError('LEDGER_HTTP_RESERVATION_CHANGED')
            http+=1;reserved+=amount
        for p in Path(root).glob('inference_reservation_*.json'):
            row=original.c.read(p);amount=Decimal(row['reserved_USD'])
            if amount!=Decimal(policy['reservation_per_inference_USD']):raise ValueError('LEDGER_INFERENCE_RESERVATION_CHANGED')
            inferences+=1;reserved+=amount
    allowed=(http<=policy['max_total_HTTP_requests'] and inferences<=policy['max_inference_requests']
        and reserved<=Decimal(policy['operational_reservation_ceiling_USD']) and reserved<Decimal(policy['pilot_target_USD']))
    return {'HTTP_attempt_reservations_all_accounts':http,'inference_reservations_all_accounts':inferences,
        'reserved_USD_all_accounts':str(reserved),'within_original_pilot_caps':allowed,
        'prior_unknown_cost_not_refunded':True,'actual_invoice_cost':None}


def verify_public_inputs(config):
    for relative,digest in config['protected_prior_public_files_sha256'].items():
        if is_private_path(relative) or public_sha(ROOT/relative)!=digest:raise ValueError('PRIOR_PUBLIC_RECORD_CHANGED_STOP')
    for relative,digest in config['new_executor_public_files_sha256'].items():
        if is_private_path(relative) or public_sha(ROOT/relative)!=digest:raise ValueError('NEW_EXECUTOR_CHANGED_STOP')


def verify():
    base=original.verify_policy() # aynı fiyat zamanı, model, kaynaklar ve istek; ağ yok.
    config=original.c.read(POLICY)
    if public_sha(adapter.POLICY)!=config['original_policy_sha256']:raise ValueError('ORIGINAL_POLICY_CHANGED_STOP')
    if config['one_additional_S01_attempt_authorized'] is not True:raise ValueError('NEW_SCOPE_NOT_AUTHORIZED')
    verify_public_inputs(config)
    totals=aggregate_budget(base)
    if not totals['within_original_pilot_caps']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
    return base,config


@contextmanager
def isolated_control():
    # V1 fonksiyonuna yeni ledger scope'u verilir; kaynak dosyası değiştirilmez.
    previous=original.CONTROL
    original.CONTROL=CONTROL
    try:yield
    finally:original.CONTROL=previous


def perform(folder,key,base,config,send=original.transport):
    verify_public_inputs(config)
    evidence=Evidence(folder,key)
    evidence.json('attempt_identity.json',{'attempt_version':'corrected-account-S01-v1',
        'previous_attempt_outcome':'HTTP_429_credit_balance_exhausted',
        'wrong_account_cause':'USER_REPORTED_NOT_INDEPENDENTLY_ACCOUNT_VERIFIED',
        'credential_source':'project_dotenv_OPENAI_API_KEY_only','credential_available':True,
        'same_model_prompt_sources_schema':True,'automatic_retry':False,'automatic_publication':False,
        'previous_stop_and_reservations_preserved':True,'account_id_or_key_digest_not_recorded':True})
    actual_transport_attempts=[]
    def guarded_send(method,path,payload,credential):
        verify_public_inputs(config)
        # original.perform ilgili slotu bu çağrıdan ÖNCE atomik olarak ayırmıştır.
        totals=aggregate_budget(base)
        n=totals['HTTP_attempt_reservations_all_accounts']
        evidence.json(f'aggregate_budget_before_HTTP_{n:02d}.json',totals)
        if not totals['within_original_pilot_caps']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
        actual_transport_attempts.append({'method':method,'path':path})
        return send(method,path,payload,credential)
    with isolated_control():
        result=original.perform(folder,key,base,send=guarded_send)
    evidence.json('aggregate_budget_after_run.json',aggregate_budget(base))
    evidence.json('actual_transport_attempts.json',{'HTTP_transport_attempts':actual_transport_attempts,
        'inference_transport_attempts':sum(x['path']=='/responses' for x in actual_transport_attempts),
        'gate_denial_is_not_a_network_send':True})
    return result


def main():
    class SafeParser(argparse.ArgumentParser):
        def error(self,message):print('INVALID_ARGUMENTS_NO_VALUES_ECHOED');raise SystemExit(2)
    parser=SafeParser();parser.add_argument('--run-single-s01',action='store_true');args=parser.parse_args()
    if not args.run_single_s01:
        print(json.dumps({'status':'OFFLINE_READY_USER_EXECUTION_REQUIRED','api_key_available':bool(project_key()),'new_API_requests':0}));return 0
    key=None;folder=None
    try:
        if original.is_appcontainer():raise ValueError('APPCONTAINER_STOP_NO_API')
        base,config=verify();key=project_key()
        if not key:
            print(json.dumps({'status':'PROJECT_DOTENV_KEY_ABSENT_STOP','api_key_available':False,'API_requests':0}));return 2
        folder=RUN_ROOT/(datetime.now().strftime('%Y%m%d_%H%M%S')+'_'+uuid.uuid4().hex)
        folder.mkdir(parents=True,exist_ok=False)
        result=perform(folder,key,base,config)
        hashes={p.name:public_sha(p) for p in folder.iterdir() if not is_private_path(p) and p.is_file()}
        Evidence(folder,key).json('file_hashes.json',hashes)
        print(json.dumps({'status':result['status'],'api_key_available':True,'Evidence_directory':str(folder)}))
        return 0 if result['status']=='PENDING_SOURCE_AND_HUMAN_REVIEW' else 2
    except BaseException as error:
        # Exception içeriği veya secret/hash/başlık yazılmaz. Eski safe-reason whitelist'i.
        print(json.dumps({'status':'SAFE_STOP_NO_RETRY','reason':original.safe_reason(error),
            'api_key_available':bool(key),'Evidence_directory':str(folder) if folder else None}));return 1


if __name__=='__main__':raise SystemExit(main())
