"""EXPERIMENTAL_LOW_MEMORY_v1: eski2,5GiB modülünü değiştirmeyen tek-vaka adaptörü."""
from pathlib import Path
import argparse
import sys
import wp12_source_case as c
from wp12_vocab_counter import VocabCounter

POLICY=c.ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json'
QA=c.ROOT/'reports/qa/WP12/experimental_low_memory_v1'
RUN_ROOT=c.ROOT/'reports/qa/WP12/experimental_low_memory_user_runs_v1'


def entry_gate(sample,gpu,policy):
    required={'available_bytes','commit_available_bytes','low_memory_notification'}
    if not required<=set(sample) or 'free_MiB' not in gpu:raise ValueError('MISSING_REQUIRED_MEASUREMENT')
    if type(sample['low_memory_notification']) is not bool:raise ValueError('MISSING_OS_PRESSURE_SIGNAL')
    for key in ['available_bytes','commit_available_bytes']:
        if not isinstance(sample[key],int) or isinstance(sample[key],bool) or sample[key]<0:raise ValueError('INVALID_MEMORY_MEASUREMENT')
    if not isinstance(gpu['free_MiB'],int) or isinstance(gpu['free_MiB'],bool):raise ValueError('INVALID_GPU_MEASUREMENT')
    return (sample['available_bytes']>=policy['RAM_floor_bytes'] and
            sample['commit_available_bytes']>=policy['commit_floor_bytes'] and
            gpu['free_MiB']>=policy['GPU_floor_MiB'] and not sample['low_memory_notification'])


def runtime_warning(sample,policy):
    if not {'available_bytes','commit_available_bytes','low_memory_notification'}<=set(sample):
        raise ValueError('MISSING_RUNTIME_MEASUREMENT')
    if type(sample['low_memory_notification']) is not bool:raise ValueError('MISSING_OS_PRESSURE_SIGNAL')
    if any(type(sample[key]) is not int or sample[key]<0 for key in ['available_bytes','commit_available_bytes']):
        raise ValueError('INVALID_RUNTIME_MEASUREMENT')
    return (sample['available_bytes']<policy['runtime_RAM_floor_bytes'] or
            sample['commit_available_bytes']<policy['runtime_commit_floor_bytes'] or sample['low_memory_notification'])


def verify():
    policy=c.read(POLICY)
    for path,digest in policy['immutable_inputs_sha256'].items():
        if c.sha(c.ROOT/path)!=digest:raise ValueError('experimental dependency changed: '+path)
    if c.sha(c.ROOT/policy['runner'])!=policy['runner_sha256']:raise ValueError('experimental runner changed')
    cfg=c.read(c.CONFIG);meta=c.verify_frozen_inputs(cfg)
    if policy['API_model_digest']!=cfg['API_model_digest']:raise ValueError('MODEL_IDENTITY_CHANGED')
    return policy,meta


def preflight(folder):
    policy,meta=verify()
    entry=c.read(folder/'preflight_measurements.json')
    if not entry_gate(entry['memory'],entry['GPU'],policy):raise ValueError('EXPERIMENTAL_ENTRY_GATE_FAILED')
    import psutil
    if psutil.virtual_memory().available<policy['RAM_floor_bytes']:raise ValueError('RAM_CHANGED_BEFORE_VOCAB')
    ctx=c.context('S01');req=c.request_for(ctx)
    if req!=c.read(c.QA/'package/request.json'):raise ValueError('FROZEN_SOURCE_PROMPT_CHANGED')
    with VocabCounter() as counter:
        old=c.read(c.ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586/smoke_request.json')
        if c.make_token_proof(old,counter,meta['tokenizer.chat_template'])['input_token_count']!=41:
            raise ValueError('TOKENIZER_ALIGNMENT_FAILED')
        proof=c.make_token_proof(req,counter,meta['tokenizer.chat_template'])
    c.save_new(folder/'token_budget.json',proof)
    c.save_new(folder/'case_context.json',{'scenario':ctx['scenario'],'sources':ctx['sources']})
    with (folder/'source_request.json').open('x',encoding='utf-8') as f:f.write(c.dump(req))
    result={'status':'PREFLIGHT_PASS' if proof['admitted'] else 'CONTEXT_BUDGET',
        'admitted':proof['admitted'],'input_token_count':proof['input_token_count'],
        'request_sha256':c.sha(folder/'source_request.json'),'memory_policy':'EXPERIMENTAL_LOW_MEMORY_v1',
        'safety_guarantee':False,'source_dependencies_verified':True}
    c.save_new(folder/'python_preflight_result.json',result);return result


def review(folder):
    verify()
    # Eski modülün saf kaynak/JSON/çıktı incelemesi;2,5GiB preflight'ı çağrılmaz.
    return c.review(folder)


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','review']);p.add_argument('--run-directory',type=Path,required=True)
    a=p.parse_args();folder=a.run_directory.resolve()
    if folder.parent!=RUN_ROOT.resolve() or not folder.is_dir():raise ValueError('INVALID_NEW_EXPERIMENTAL_RUN_DIRECTORY')
    try:result=preflight(folder) if a.action=='preflight' else review(folder)
    except Exception as e:
        result={'status':'EXPERIMENTAL_'+a.action.upper()+'_FAILED_NO_RETRY',
            'error_type':type(e).__name__,'error':str(e),'automatic_release':False}
        c.save_new(folder/('python_'+a.action+'_failure.json'),result);print(c.dump(result));return 1
    print(c.dump({'status':result['status']}));return 0


if __name__=='__main__':raise SystemExit(main())
