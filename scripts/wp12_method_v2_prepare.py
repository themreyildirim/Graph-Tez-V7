"""Yalnız v2 öneri paketini oluşturur; ağ veya LLM inference içermez."""
import sys
import json
sys.dont_write_bytecode=True
import wp12_source_case as c
import wp12_method_v2 as v2
from wp12_vocab_counter import template_from_gguf,VocabCounter
from jsonschema import Draft202012Validator


def main():
    schema=v2.generic_schema();Draft202012Validator.check_schema(schema)
    c.save_new(v2.SCHEMA,schema)
    case=v2.case_schema();Draft202012Validator.check_schema(case)
    c.save_new(v2.QA/'S01_case_schema_v2_PROPOSED.json',case)
    req=v2.request_for_S01()
    c.save_new(v2.QA/'S01_request_v2_PROPOSED_NOT_SENT.json',req)
    c.save_new(v2.QA/'S01_refusal_eligibility.json',v2.S01_refusal_policy())
    policy=c.read(c.ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json')
    plan={'version':'WP12-source-method-v2-PROPOSED','status':'AWAITING_METHOD_APPROVAL_NO_EXECUTOR',
        'new_method_after_observed_failure':True,'independent_validation':False,
        'future_trial_id':'WP12-method-v2-S01-R1-validation-01','frozen_scenario':'S01','scenario_repeat_label':'S01-R1',
        'max_future_generation_attempts':1,'actual_new_generation_attempts':0,'automatic_retry':False,
        'method_changes_do_not_erase_v1_failure':True,'user_approval_required_before_execution':True,
        'model':policy['model'],'API_model_digest':policy['API_model_digest'],
        'hardware_policy_reference':'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json',
        'hardware_policy_sha256':c.sha(c.ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json'),
        'RAM_floor_bytes':policy['RAM_floor_bytes'],'GPU_floor_MiB':policy['GPU_floor_MiB'],
        'commit_floor_bytes':policy['commit_floor_bytes'],'runtime_RAM_floor_bytes':policy['runtime_RAM_floor_bytes'],
        'runtime_commit_floor_bytes':policy['runtime_commit_floor_bytes'],'OS_pressure_signal_required':True,
        'HTTP_timeout_seconds':policy['HTTP_timeout_seconds'],'generation_options':req['options'],
        'think':False,'stream':False,'keep_alive':0,'truncate':False,'shift':False,
        'input_token_limit':1536,'output_reserve':384,'safety_reserve':128,
        'future_request_gate':'normal user PowerShell only; memory/API/source/digest/schema/token gates remeasured; no AppContainer bypass',
        'first_future_response_policy':'retain raw response/refusal/failure; no repair, translation or retry; schema/source/language then human semantic review',
        'future_server_prompt_count_must_match_offline_count':True,
        'all19x3_enabled':False,'WP13_enabled':False,'automatic_publication':False,
        'runtime_grammar_support_for_this_exact_v2_schema':'UNVERIFIED_NO_API_CALL_THIS_STAGE'}
    c.save_new(c.ROOT/'configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json',plan)
    print('V2 proposed package only. No network, inference, training or execution client.')


if __name__=='__main__':main()
