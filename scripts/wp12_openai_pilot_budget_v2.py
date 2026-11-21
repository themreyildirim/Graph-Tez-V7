"""V2: eski6HTTP/2rezervi koruyan,30HTTP/10inference/$0.25 küçük pilot kapısı."""
from datetime import datetime,timezone
from decimal import Decimal
from pathlib import Path
import wp12_openai_scenarios_v2 as s
import wp12_openai_client as old
from wp12_api_security import public_sha,is_private_path,git_privacy_state

ROOT=s.ROOT
POLICY=ROOT/'configs/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.json'
CONTROL=s.QA/'control'
PRIOR_ROOTS=[ROOT/'reports/qa/WP12/openai_api_pilot_v1/control',
    ROOT/'reports/qa/WP12/openai_corrected_account_preparation_v1/control']


def aggregate(policy,roots=None):
    roots=[*PRIOR_ROOTS,CONTROL] if roots is None else roots
    h=0;i=0;reserve=Decimal('0')
    for root in roots:
        for p in Path(root).glob('http_*.json'):
            row=old.c.read(p);amount=Decimal(row['extra_budget_guard_USD'])
            if amount!=Decimal(policy['reservation_per_HTTP_USD']):raise ValueError('HTTP_RESERVATION_MISMATCH')
            h+=1;reserve+=amount
        for p in Path(root).glob('inference_reservation_*.json'):
            row=old.c.read(p);amount=Decimal(row['reserved_USD'])
            if amount!=Decimal(policy['reservation_per_inference_USD']):raise ValueError('INFERENCE_RESERVATION_MISMATCH')
            i+=1;reserve+=amount
    return summary(h,i,reserve,policy)


def summary(h,i,reserve,policy):
    return {'HTTP_reservations_total':h,'inference_reservations_total':i,'reserved_USD':str(reserve),
        'within_limits':h<=policy['max_total_HTTP_requests'] and i<=policy['max_inference_requests'] and
            reserve<=Decimal(policy['operational_reservation_ceiling_USD']),
        'unknown_prior_cost_not_refunded':True,'actual_invoice_total':'UNKNOWN_NOT_QUERIED'}


def projected(policy,*,HTTP=0,inference=0):
    old_state=aggregate(policy)
    money=Decimal(old_state['reserved_USD'])+HTTP*Decimal(policy['reservation_per_HTTP_USD'])+inference*Decimal(policy['reservation_per_inference_USD'])
    return summary(old_state['HTTP_reservations_total']+HTTP,old_state['inference_reservations_total']+inference,money,policy)


def verify(policy=None):
    p=old.c.read(POLICY) if policy is None else policy
    if (p['model']!='gpt-5.4-mini' or p['max_inference_requests']!=10 or p['max_total_HTTP_requests']!=30
        or p['operational_reservation_ceiling_USD']!='0.25' or p['input_token_cap']!=6000 or p['max_output_tokens']!=1200
        or p['only_executable_scenario']!='S07' or p['reservation_per_inference_USD']!='0.02' or p['reservation_per_HTTP_USD']!='0.001'):
        raise ValueError('HARD_V2_POLICY_MISMATCH')
    if datetime.now(timezone.utc)>datetime.fromisoformat(p['pricing_valid_until_UTC']):raise ValueError('PRICE_SNAPSHOT_EXPIRED_REFRESH_OFFICIAL_DOCS')
    if git_privacy_state(ROOT)['tracked_private_files_detected']:raise ValueError('PRIVATE_FILE_TRACKED_BY_GIT_STOP')
    for name,digest in p['immutable_public_inputs_sha256'].items():
        if is_private_path(name) or public_sha(ROOT/name)!=digest:raise ValueError('PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED')
    for name,digest in p['prior_public_records_sha256'].items():
        if is_private_path(name) or public_sha(ROOT/name)!=digest:raise ValueError('PRIOR_PUBLIC_RECORD_CHANGED_STOP')
    for case in ['S07','S04']:
        if s.request(case)!=old.c.read(s.QA/f'{case}_request_NOT_SENT.json'):raise ValueError('FROZEN_SCENARIO_REQUEST_CHANGED')
    if not aggregate(p)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
    return p
