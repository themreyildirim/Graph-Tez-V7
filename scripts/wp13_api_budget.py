from decimal import Decimal
from pathlib import Path
import wp12_openai_S15_execution_v1 as prior
from wp12_api_security import public_sha,is_private_path
ROOT=prior.ROOT
CONTROL=ROOT/'reports/qa/WP13/api_control_v1'
POLICY=ROOT/'configs/WP13_API_v1.json'

def aggregate(p):
    return prior.base.aggregate(p,roots=[*prior.base.PRIOR_ROOTS,prior.base.CONTROL,
        prior.prior.prior.CONTROL,prior.prior.CONTROL,prior.CONTROL,CONTROL])

def projected(p,*,HTTP=0,inference=0):
    v=aggregate(p)
    money=Decimal(v['reserved_USD'])+HTTP*Decimal(p['reservation_per_HTTP_USD'])+inference*Decimal(p['reservation_per_inference_USD'])
    return prior.base.summary(v['HTTP_reservations_total']+HTTP,v['inference_reservations_total']+inference,money,p)

def verify(policy=None):
    p=prior.verify();cfg=prior.base.old.c.read(POLICY)
    if cfg['max_live_inference']!=1 or cfg['max_HTTP']!=3:raise ValueError('HARD_V2_POLICY_MISMATCH')
    for n,h in cfg['source_pins'].items():
        if is_private_path(n) or public_sha(ROOT/n)!=h:raise ValueError('PUBLIC_SOURCE_OR_METHOD_HASH_CHANGED')
    if not aggregate(p)['within_limits']:raise ValueError('AGGREGATE_PILOT_BUDGET_STOP')
    return {**p,'execution_scope_version':cfg['version']}
