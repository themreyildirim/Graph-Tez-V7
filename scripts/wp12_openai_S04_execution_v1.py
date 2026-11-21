"""Yeni S04 tek-deneme yetkisi; frozen v2 finans/model/metot değişmez."""
from decimal import Decimal
import wp12_openai_pilot_budget_v2 as base
from wp12_api_security import public_sha,is_private_path

ROOT=base.ROOT
QA=ROOT/'reports/qa/WP12/openai_S04_preparation_v1'
POLICY=ROOT/'configs/WP12_OPENAI_S04_SINGLE_EXECUTION_v1.json'
CONTROL=QA/'control'


def aggregate(policy):
    # S07'nin dahil olduğu eski3root + yeni S04; sayaç/rezerv sıfırlanmaz.
    return base.aggregate(policy,roots=[*base.PRIOR_ROOTS,base.CONTROL,CONTROL])


def projected(policy,*,HTTP=0,inference=0):
    state=aggregate(policy)
    money=Decimal(state['reserved_USD'])+HTTP*Decimal(policy['reservation_per_HTTP_USD'])+inference*Decimal(policy['reservation_per_inference_USD'])
    return base.summary(state['HTTP_reservations_total']+HTTP,state['inference_reservations_total']+inference,money,policy)


def verify(policy=None):
    p=base.verify() # mevcut kaynaklar, v2 fiyat zamanı ve 30/10/.25 sınırları
    cfg=base.old.c.read(POLICY)
    if cfg['only_executable_scenario']!='S04' or cfg['max_current_attempts']!=1 or not cfg['authorized_by_explicit_user_request']:
        raise ValueError('S04_SCOPE_NOT_AUTHORIZED')
    if public_sha(base.POLICY)!=cfg['base_budget_policy_sha256']:raise ValueError('BASE_BUDGET_POLICY_CHANGED')
    for collection in ['protected_prior_public_files_sha256','new_executor_public_files_sha256']:
        for name,digest in cfg[collection].items():
            if is_private_path(name) or public_sha(ROOT/name)!=digest:raise ValueError('PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED')
    if not aggregate(p)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
    # Yeni kayıtlar maliyet protokolüyle yürütüm yetkisinin sürümlerini ayrı taşır.
    return {**p,'execution_scope_version':cfg['version']}
