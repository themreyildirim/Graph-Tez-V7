"""Onaylı Gemma V2 tek-istek yürütücüsünün AĞSIZ ön/son kontrolü.

HTTP yalnız normal kullanıcı PowerShell betiğindedir; burada inference yok.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys
import wp12_source_case as c
import wp12_source_low_memory as low
import wp12_method_v2 as method
from wp12_vocab_counter import VocabCounter
from jsonschema import Draft202012Validator

QA=c.ROOT/'reports/qa/WP12/conditional_local_llm_v1'
CONFIG=c.ROOT/'configs/WP12_GEMMA_V2_SINGLE_RUN_v1.json'
RUN_ROOT=c.ROOT/'reports/qa/WP12/gemma_v2_user_runs_v1'


def verify():
    cfg=c.read(CONFIG)
    for path,digest in cfg['immutable_inputs_sha256'].items():
        if c.sha(c.ROOT/path)!=digest:raise ValueError('APPROVED_DEPENDENCY_CHANGED: '+path)
    if c.sha(c.ROOT/cfg['runner'])!=cfg['runner_sha256']:raise ValueError('APPROVED_RUNNER_CHANGED')
    policy,meta=low.verify()
    if cfg['model_digest']!=policy['API_model_digest']:raise ValueError('MODEL_DIGEST_CHANGED')
    for key in ['RAM_floor_bytes','GPU_floor_MiB','commit_floor_bytes','runtime_RAM_floor_bytes','runtime_commit_floor_bytes','HTTP_timeout_seconds']:
        if cfg[key]!=policy[key]:raise ValueError('MEMORY_OR_TIMEOUT_POLICY_CHANGED')
    if method.request_for_S01()!=c.read(method.QA/'S01_request_v2_PROPOSED_NOT_SENT.json'):
        raise ValueError('ACCEPTED_V2_REQUEST_CHANGED')
    return cfg,policy,meta


def preflight(folder):
    cfg,policy,meta=verify();entry=c.read(folder/'preflight_measurements.json')
    if not low.entry_gate(entry['memory'],entry['GPU'],policy):raise ValueError('ENTRY_GATE_FAILED')
    import psutil
    if psutil.virtual_memory().available<policy['RAM_floor_bytes']:raise ValueError('RAM_CHANGED_BEFORE_VOCAB')
    req=method.request_for_S01();ctx=method.verified_S01_context()
    with VocabCounter() as counter:
        old=c.read(c.ROOT/'reports/qa/WP12/gemma1b_v2_1_user_smoke_runs/20261108_044905_6e8ec7c39c704fcfaaaeeef681c61586/smoke_request.json')
        if c.make_token_proof(old,counter,meta['tokenizer.chat_template'])['input_token_count']!=41:
            raise ValueError('TOKENIZER_ALIGNMENT_FAILED')
        proof=method.token_proof(req,counter,meta['tokenizer.chat_template'])
    if proof!=c.read(method.QA/'v2_actual_token_proof.json'):raise ValueError('ACCEPTED_V2_TOKEN_PROOF_CHANGED')
    c.save_new(folder/'token_budget.json',proof)
    c.save_new(folder/'case_context.json',{'scenario':ctx['scenario'],'sources':ctx['sources']})
    c.save_new(folder/'approved_case_schema.json',req['format'])
    c.save_new(folder/'method_dependencies.json',{'method':'WP12-local-llm-candidate-v2',
        'inputs_sha256':cfg['immutable_inputs_sha256'],'runner_sha256':cfg['runner_sha256'],
        'config_sha256':c.sha(CONFIG),'model_digest':cfg['model_digest'],
        'source_quotes_count':2,'source_chars':537,'no_new_source_or_model':True})
    with (folder/'source_request.json').open('x',encoding='utf-8') as f:f.write(c.dump(req))
    result={'status':'PREFLIGHT_PASS' if proof['admitted'] else 'CONTEXT_BUDGET',
        'admitted':proof['admitted'],'input_token_count':proof['input_token_count'],
        'request_sha256':c.sha(folder/'source_request.json'),'trial_id':cfg['trial_id'],
        'single_generation_slot_required':True,'actual_inference_in_python':0}
    c.save_new(folder/'python_preflight_result.json',result);return result


def assess_response(response,proof):
    """Teknik/şema/uygulama/dil ayrımı; insan kaynak onayı VERMEZ."""
    base={'automatic_release':False,'semantic_success':None,'human_review':'PENDING',
        'method':'WP12-local-llm-candidate-v2','source_faithfulness':'PENDING_AGENT_AND_HUMAN_REVIEW',
        'language_quality':'PENDING','schema_status':'NOT_EVALUABLE','application_status':'NOT_EVALUABLE'}
    if response.get('model')!='gemma3:1b-it-q4_K_M':
        return {**base,'status':'RESPONSE_MODEL_MISMATCH','technical_status':'FAIL'}
    if response.get('done') is not True or response.get('done_reason')!='stop':
        return {**base,'status':'GENERATION_INCOMPLETE','technical_status':'FAIL'}
    if response.get('prompt_eval_count')!=proof['input_token_count']:
        return {**base,'status':'TOKEN_COUNT_ALIGNMENT_FAILED','technical_status':'FAIL',
            'expected_prompt_tokens':proof['input_token_count'],'server_prompt_tokens':response.get('prompt_eval_count')}
    count=response.get('eval_count')
    if type(count) is not int or not 0<count<=384:
        return {**base,'status':'OUTPUT_TOKEN_BUDGET_OR_COUNT_INVALID','technical_status':'FAIL'}
    if response.get('message',{}).get('thinking') or response.get('message',{}).get('tool_calls'):
        return {**base,'status':'UNEXPECTED_OUTPUT_CHANNEL','technical_status':'FAIL'}
    text=response.get('message',{}).get('content')
    if not isinstance(text,str) or not text:
        return {**base,'status':'EMPTY_MODEL_CONTENT','technical_status':'FAIL'}
    def pairs(items):
        out={}
        for k,v in items:
            if k in out:raise ValueError('DUPLICATE_CANDIDATE_KEY')
            out[k]=v
        return out
    def invalid_constant(value):raise ValueError('NON_JSON_CONSTANT: '+value)
    try:candidate=json.loads(text,object_pairs_hook=pairs,parse_constant=invalid_constant)
    except (ValueError,TypeError) as e:
        return {**base,'status':'V2_JSON_SYNTAX_FAIL','technical_status':'PASS','schema_status':'FAIL',
            'application_status':'FAIL','error':str(e),'model_produced_response':True}
    check=method.inspect_candidate(candidate)
    schema=bool(check['schema_valid']);application=schema and check['source_contract_valid'] and not check['errors']
    lang='FAIL' if 'OBVIOUS_NON_TURKISH' in check['errors'] else 'PENDING'
    return {**base,'status':'V2_CANDIDATE_PENDING_HUMAN_REVIEW' if application else 'V2_SCHEMA_OR_APPLICATION_FAIL',
        'technical_status':'PASS','model_produced_response':True,'schema_status':'PASS' if schema else 'FAIL',
        'generic_schema_valid':Draft202012Validator(method.generic_schema()).is_valid(candidate),
        'application_status':'PASS' if application else 'FAIL','language_quality':lang,
        'task_coverage':check.get('task_coverage','NOT_EVALUABLE'),'candidate':candidate,'validation':check,
        'first_case_quality_gate':'PENDING_OR_FAIL_NEVER_AUTOMATIC_PASS'}


def review(folder):
    cfg,_,meta=verify();req=c.read(folder/'source_request.json');proof=c.read(folder/'token_budget.json')
    if req!=method.request_for_S01():raise ValueError('SAVED_REQUEST_CHANGED')
    if proof!=c.read(method.QA/'v2_actual_token_proof.json'):raise ValueError('SAVED_TOKEN_PROOF_CHANGED')
    rendered=method.render_request(req,meta['tokenizer.chat_template'])
    if hashlib.sha256(rendered.encode()).hexdigest()!=proof['rendered_prompt_sha256']:raise ValueError('PROMPT_BINDING_CHANGED')
    result=assess_response(c.read(folder/'source_response_raw.json'),proof)
    result['trial_id']=cfg['trial_id']
    c.save_new(folder/'structural_review.json',result)
    form=c.read(method.QA/'human_review_required_v2_PROPOSED.json')
    form.update(raw_response_ref=str(folder/'source_response_raw.json'),raw_response_sha256=c.sha(folder/'source_response_raw.json'))
    c.save_new(folder/'human_review_PENDING.json',form)
    return result


def next_action(actual_response_present=False,technical='NOT_RUN',schema='NOT_RUN',application='NOT_RUN',
                language='PENDING',source='PENDING',task='PENDING',human='PENDING'):
    """Kullanıcı koşullu iznini uygular; yükleme hatasını semantik FAIL saymaz."""
    if not actual_response_present:
        return 'WAIT_USER_STAGE_A_RUN' if technical=='NOT_RUN' else 'REPORT_TECHNICAL_BLOCK_QUALITY_NOT_EVALUABLE'
    if technical!='PASS':return 'REPORT_TECHNICAL_BLOCK_QUALITY_NOT_EVALUABLE'
    if 'FAIL' in [schema,application,language,source,task]:return 'PREPARE_QWEN_WITH_SEPARATE_MEMORY_AND_IDENTITY_AUDIT'
    if human=='PASS' and language=='PASS' and source=='PASS' and task=='PASS':
        return 'PRESENT_SINGLE_CASE_RESULTS_STOP_BEFORE_19X3'
    return 'REVIEW_ACTUAL_RESPONSE_AND_WAIT_HUMAN_SEMANTIC_DECISION'


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['preflight','review']);p.add_argument('--run-directory',type=Path,required=True)
    arg=p.parse_args();folder=arg.run_directory.resolve()
    if folder.parent!=RUN_ROOT.resolve() or not folder.is_dir():raise ValueError('INVALID_STAGE_A_RUN_DIRECTORY')
    try:result=preflight(folder) if arg.action=='preflight' else review(folder)
    except Exception as e:
        result={'status':'V2_'+arg.action.upper()+'_FAILED_NO_RETRY','error_type':type(e).__name__,
            'error':str(e),'automatic_release':False,'semantic_success':None}
        c.save_new(folder/('python_'+arg.action+'_failure.json'),result)
        print(c.dump(result));return 1
    print(c.dump({'status':result['status']}));return 0


if __name__=='__main__':raise SystemExit(main())
