"""S16-only scope, all prior ledgers retained."""
from decimal import Decimal
import wp12_openai_S04_execution_v1 as prior
from wp12_api_security import public_sha,is_private_path
ROOT=prior.ROOT
QA=ROOT/'reports/qa/WP12/openai_S16_preparation_v1'
CONTROL=QA/'control'
POLICY=ROOT/'configs/WP12_OPENAI_S16_SINGLE_EXECUTION_v1.json'

def aggregate(policy):
    return prior.base.aggregate(policy,roots=[*prior.base.PRIOR_ROOTS,prior.base.CONTROL,prior.CONTROL,CONTROL])

def projected(policy,*,HTTP=0,inference=0):
    v=aggregate(policy)
    money=Decimal(v['reserved_USD'])+HTTP*Decimal(policy['reservation_per_HTTP_USD'])+inference*Decimal(policy['reservation_per_inference_USD'])
    return prior.base.summary(v['HTTP_reservations_total']+HTTP,v['inference_reservations_total']+inference,money,policy)

def verify(policy=None):
    p=prior.verify();cfg=prior.base.old.c.read(POLICY)
    for n,h in cfg['public_files_sha256'].items():
        if is_private_path(n) or public_sha(ROOT/n)!=h:raise ValueError('PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED')
    if cfg['only_executable_scenario']!='S16' or cfg['maximum_attempts']!=1:raise ValueError('SCENARIO_NOT_IN_VERSION')
    if not aggregate(p)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
    return {**p,'execution_scope_version':cfg['version']}
