"""Onaylı koşullu WP12 planı + tek-vaka Gemma V2 PowerShell paketi."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import wp12_source_case as c
import wp12_method_v2 as v
import wp12_gemma_v2_user_run as runner


def main():
    old=c.ROOT/'scripts/WP12_ExperimentalLowMemorySingleCase_v1.ps1'
    target=c.ROOT/'scripts/WP12_GemmaV2_UserSingleCase_v1.ps1'
    text=old.read_text(encoding='utf-8')
    text=text.replace('WP12-experimental-low-memory-single-run-v1','WP12-gemma-v2-user-single-run-v1')
    text=text.replace('experimental_low_memory_user_runs_v1','gemma_v2_user_runs_v1')
    text=text.replace('WP12_EXPERIMENTAL_LOW_MEMORY_v1.json','WP12_GEMMA_V2_SINGLE_RUN_v1.json')
    text=text.replace("'wp12_source_low_memory.py'","'wp12_gemma_v2_user_run.py'")
    text=text.replace("@('scripts/wp12_source_low_memory.py','scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')",
        "@('scripts/wp12_gemma_v2_user_run.py','scripts/wp12_method_v2.py','scripts/wp12_source_low_memory.py','scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')")
    text=text.replace("    scenario_id = 'S01'; repeat = 1; maximum_generation_requests = 1",
        "    scenario_id = 'S01'; repeat = 1; maximum_generation_requests = 1\n    trial_id = 'WP12-method-v2-S01-R1-validation-01'\n    method = 'WP12-local-llm-candidate-v2'\n    no_automatic_stage_B_or_D = $true")
    marker="    $record['memory_before'] = Sample-Memory"
    gate="""    $slotPath = Join-Path $projectRoot 'reports\\qa\\WP12\\conditional_local_llm_v1\\control\\stage_A_generation_claim.json'
    $record['generation_slot_path'] = $slotPath
    if (Test-Path -LiteralPath $slotPath) { $record.status = 'STOP_STAGE_A_SINGLE_ATTEMPT_ALREADY_CLAIMED_NO_API'; return }
"""
    text=text.replace(marker,gate+marker,1)
    marker="    $record['inference_attempts'] = 1"
    claim="""    # Atomik, proje genelinde tek slot: bu surumde reset/force/retry secenegi yok.
    $claimText = ([ordered]@{trial_id=$record.trial_id;run_directory=$runDir;request_sha256=$record.request_sha256;claimed_at=[DateTimeOffset]::Now.ToString('o');server_completion='UNKNOWN_UNTIL_RESPONSE'}) | ConvertTo-Json -Depth 10
    $claimFile = [IO.File]::Open($slotPath,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
    try { $claimBytes=$utf8.GetBytes($claimText);$claimFile.Write($claimBytes,0,$claimBytes.Length) } finally { $claimFile.Dispose() }
    Save-Text 'generation_claim_copy.json' $claimText
    $record['generation_slot_claimed'] = $true
"""
    text=text.replace(marker,claim+marker,1)
    text='# Gemma V2 approved; unchanged request/schema/system/source; one lifetime generation slot.\n'+text
    with target.open('x',encoding='utf-8') as f:f.write(text)
    policy=c.read(c.ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json')
    conditional={'version':'WP12-conditional-local-LLM-v1','authorization':'USER_EXPLICIT_CONDITIONAL_PLAN',
        'active_WP':'WP12','stage_A':{'method':'accepted-v2','model':policy['model'],'digest':policy['API_model_digest'],
            'max_generation_attempts':1,'status':'NOT_RUN_WAIT_USER_POWERSHELL','retry':False},
        'stage_B':{'model':'qwen3:4b-instruct-2507-q4_K_M','status':'NOT_RUN_CONDITION_NOT_TRIGGERED',
            'prepare_without_new_method_permission_on':'completed real Gemma V2 response with schema/application/language/source/task FAIL',
            'technical_no_response_is_not_quality_failure':True,'download':False,'max_generation_attempts':1,
            'digest':'NOT_VERIFIED_THIS_STAGE','same_S01_sources_question_acceptance':True,
            'same_v2_method_unless_mandatory_model_specific_adaptation':True,
            'separate_model_bytes_KV_runtime_RAM_GPU_commit_OS_assessment_required':True,
            'copy_Gemma_low_memory_thresholds':False,'automatic_threshold_reduction':False,
            'user_PowerShell_command_required_when_safe':True,'retry':False},
        'stage_C':{'status':'PARTIAL_ONLY_V1_REAL_RESULT_AVAILABLE','axes':['schema','application','Turkish_quality','PDF_faithfulness','page_quote_alignment','unsupported_refusal_missing_information_invention','tokens_latency_memory','human_review_limits'],
            'NOT_RUN_for_unexecuted_experiments':True,'PENDING_for_unreviewed_semantics':True,
            'all_raw_responses_and_failures_preserved':True,'same_case_method_development_not_independent_generalization':True},
        'stage_D':{'19x3_status':'NOT_AUTHORIZED_TO_AUTOSTART','requires_user_results_review':True},
        'new_training':False,'automatic_publication':False,'WP13':False,'new_models_downloaded':False}
    plan_path=c.ROOT/'configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json';c.save_new(plan_path,conditional)
    inputs=dict(policy['immutable_inputs_sha256'])
    for rel in ['configs/WP12_METHOD_CORRECTION_v2_PROPOSED.json','configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json',
        'configs/WP12_CONDITIONAL_LOCAL_LLM_v1.json','scripts/wp12_gemma_v2_user_run.py','scripts/wp12_method_v2.py',
        'docs/schemas/WP12_local_llm_candidate_v2_PROPOSED.schema.json','docs/prompts/WP12_SOURCE_EXPLANATION_SYSTEM_v2_PROPOSED.txt',
        'reports/qa/WP12/method_correction_v2/S01_case_schema_v2_PROPOSED.json',
        'reports/qa/WP12/method_correction_v2/S01_request_v2_PROPOSED_NOT_SENT.json',
        'reports/qa/WP12/method_correction_v2/v2_actual_token_proof.json',
        'reports/qa/WP12/method_correction_v2/human_review_required_v2_PROPOSED.json']:
        inputs[rel]=c.sha(c.ROOT/rel)
    cfg={'version':'WP12-Gemma-v2-single-run-v1','method_approved':True,'trial_id':'WP12-method-v2-S01-R1-validation-01',
        'model':policy['model'],'model_digest':policy['API_model_digest'],'immutable_inputs_sha256':inputs,
        'runner':target.relative_to(c.ROOT).as_posix(),'runner_sha256':c.sha(target),
        'generation_slot':'reports/qa/WP12/conditional_local_llm_v1/control/stage_A_generation_claim.json',
        'max_generation_attempts_across_invocations':1,'automatic_retry':False,
        'hardware_policy_reference':'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json','hardware_fields_only_inherited':True,
        'RAM_floor_bytes':policy['RAM_floor_bytes'],'GPU_floor_MiB':policy['GPU_floor_MiB'],
        'commit_floor_bytes':policy['commit_floor_bytes'],'runtime_RAM_floor_bytes':policy['runtime_RAM_floor_bytes'],
        'runtime_commit_floor_bytes':policy['runtime_commit_floor_bytes'],'HTTP_timeout_seconds':policy['HTTP_timeout_seconds'],
        'actual_generation_started':False,'expected_prompt_tokens':724,'automatic_publication':False}
    c.save_new(runner.CONFIG,cfg)
    print('Stage A prepared; B conditional only; D blocked. No inference or API calls.')


if __name__=='__main__':main()
