"""Yeni deneysel tek-istek paketi üretir; Ollama'ya bağlanmaz."""
from pathlib import Path
import sys
import wp12_source_case as c

QA=c.ROOT/'reports/qa/WP12/experimental_low_memory_v1'
POLICY=c.ROOT/'configs/WP12_EXPERIMENTAL_LOW_MEMORY_v1.json'


def main():
    QA.mkdir(parents=True,exist_ok=False)
    prior=c.read(c.QA/'prior_artifacts_sha256.json')
    paths=set(prior)
    for p in c.QA.rglob('*'):
        if p.is_file():paths.add(p.relative_to(c.ROOT).as_posix())
    for p in ['scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_source_single_setup.py',
              'scripts/wp12_source_case_evidence.py','scripts/WP12_SourceSingleCase_v1.ps1','tests/test_wp12_source_single_case.py',
              'configs/WP12_SOURCE_SINGLE_CASE_v1.json','reports/WP12_SOURCE_SINGLE_CASE_PREPARATION.md',
              'notebooks/WP12_source_single_case_preparation.ipynb']:
        paths.add(p)
    for p in (c.ROOT/'reports/figures/WP12/source_single_case_v1').glob('*.png'):paths.add(p.relative_to(c.ROOT).as_posix())
    c.save_new(QA/'previous_files_sha256.json',{p:c.sha(c.ROOT/p) for p in sorted(paths)})
    (QA/'run_status_before.md').write_bytes((c.ROOT/'run_status.md').read_bytes())
    base=(c.ROOT/'scripts/WP12_SourceSingleCase_v1.ps1').read_text(encoding='utf-8')
    text=base.replace('WP12-source-single-case-run-v1','WP12-experimental-low-memory-single-run-v1')
    text=text.replace('source_single_case_user_runs','experimental_low_memory_user_runs_v1')
    text=text.replace('WP12-gemma1b-memory-v2','EXPERIMENTAL_LOW_MEMORY_v1')
    text=text.replace('WP12_SOURCE_SINGLE_CASE_v1.json','WP12_EXPERIMENTAL_LOW_MEMORY_v1.json')
    text=text.replace("'wp12_source_case.py'","'wp12_source_low_memory.py'")
    text=text.replace("@('scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')",
        "@('scripts/wp12_source_low_memory.py','scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')")
    text=text.replace('2684354560','1610612736').replace('GPU_free_MiB = 2048','GPU_free_MiB = 1024')
    text=text.replace('.free_MiB -lt 2048','.free_MiB -lt 1024')
    text=text.replace('1073741824','805306368')
    text=text.replace("    status = 'INITIALIZING';", "    safety_guarantee = $false\n    runtime_commit_floor_bytes = 1073741824\n    runtime_RAM_floor_bytes = 805306368\n    status = 'INITIALIZING';")
    start=text.index("    if (-not ('WP12GemmaSmokeNativeV2'")
    end=text.index('    function Sample-GPU',start)
    helper=c.sha(c.ROOT/'scripts/WP12_LowMemoryObservation_v1.ps1')
    text=text[:start]+f'''    $observationHelper = Join-Path $PSScriptRoot 'WP12_LowMemoryObservation_v1.ps1'
    $record['observation_helper_sha256'] = (Get-FileHash -LiteralPath $observationHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($record.observation_helper_sha256 -cne '{helper}') {{ throw 'OBSERVATION_HELPER_HASH_MISMATCH' }}
    . $observationHelper
    Initialize-WP12LowMemoryNative
    function Sample-Memory {{ return (Get-WP12LowMemorySample) }}
'''+text[end:]
    text=text.replace('WP12GemmaSmokeNativeV2','WP12LowMemoryNativeV1')
    text=text.replace("    $record['memory_before'] = Sample-Memory", "    if ($record.is_appcontainer) { $record.status = 'STOP_APPContainer_NO_API_ATTEMPT'; return }\n    $record['memory_before'] = Sample-Memory")
    text=text.replace("$record.memory_before.commit_available_bytes -lt 3221225472)",
        "$record.memory_before.commit_available_bytes -lt 3221225472 -or $record.memory_before.low_memory_notification)")
    text=text.replace("$sample.commit_available_bytes -lt 3221225472)",
        "$sample.commit_available_bytes -lt 3221225472 -or $sample.low_memory_notification)")
    text=text.replace("$record.memory_immediately_before.commit_available_bytes -lt 3221225472)",
        "$record.memory_immediately_before.commit_available_bytes -lt 3221225472 -or $record.memory_immediately_before.low_memory_notification)")
    text=text.replace("    $record['python_preflight_exit_code'] = Invoke-PythonStage 'preflight'",
        "    Save-Json 'preflight_measurements.json' @{ memory=(Sample-Memory); GPU=(Sample-GPU) }\n    $record['python_preflight_exit_code'] = Invoke-PythonStage 'preflight'")
    text=text.replace('CONTEXT_BUDGET_REJECTED_NO_GENERATION','CONTEXT_BUDGET')
    text=text.replace('if ($sample.available_bytes -lt 805306368)',
        'if ($sample.available_bytes -lt 805306368 -or $sample.commit_available_bytes -lt 1073741824 -or $sample.low_memory_notification)')
    text=text.replace("$record['memory_warning'] = $true", "$record['memory_warning'] = $true\n                $record['memory_warning_sample'] = $sample")
    text=text.replace('HOST_RAM_BELOW_1GiB: HTTP cancellation only;',
        'EXPERIMENTAL_RUNTIME_RAM_COMMIT_OR_OS_PRESSURE: HTTP cancellation only;')
    old='''        $samples.Add((Sample-Memory)); Save-Json 'memory_samples.json' @($samples.ToArray())
        $record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU
        if ($record.memory_after.available_bytes -lt 805306368 -and $record.status -ceq 'SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW') { $record.status = 'SOURCE_COMPLETED_WITH_MEMORY_WARNING' }'''
    new='''        try { $samples.Add((Sample-Memory)) } catch { $record['final_sample_error'] = $_.Exception.ToString() }
        Save-Json 'memory_samples.json' @($samples.ToArray())
        try {
            $record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU
            if ($record.memory_after.available_bytes -lt 805306368 -or $record.memory_after.commit_available_bytes -lt 1073741824 -or $record.memory_after.low_memory_notification) {
                $record.status = 'SOURCE_COMPLETED_WITH_MEMORY_WARNING_NO_CONTINUATION'
            }
        } catch { $record['post_measurement_error'] = $_.Exception.ToString(); $record.status = 'SOURCE_POST_MEASUREMENT_MISSING_NO_CONTINUATION' }'''
    assert old in text;text=text.replace(old,new)
    # Ölçüm hatasında da istemciyi kapat; sunucunun bitişi UNKNOWN kalır.
    text=text.replace("    $record['error'] = $_.Exception.ToString()", "    if ($null -ne $apiClient) { $apiClient.CancelPendingRequests() }\n    $record['error'] = $_.Exception.ToString()")
    text=text.replace('# Source single-case pilot: v2 memory and generation parameters preserved.',
        '# Separate EXPERIMENTAL_LOW_MEMORY_v1; original v2 and source v1 remain immutable.')
    text=text.replace('STOP_V2_STABILITY_OR_COMMIT_GATE','STOP_EXPERIMENTAL_STABILITY_COMMIT_OR_PRESSURE_GATE')
    text=text.replace('# v2: explicitly separate policy; v1 files and decisions remain immutable.','# Only this experimental run uses lower admission limits; old v2 remains unchanged.')
    text='# EXPERIMENTAL: user-authorized lower entry limits; no safety guarantee.\n'+text
    target=c.ROOT/'scripts/WP12_ExperimentalLowMemorySingleCase_v1.ps1'
    with target.open('x',encoding='utf-8') as f:f.write(text)
    original=c.read(c.CONFIG)
    inputs=dict(original['immutable_inputs_sha256'])
    for name in ['configs/WP12_SOURCE_SINGLE_CASE_v1.json','scripts/WP12_SourceSingleCase_v1.ps1',
                 'scripts/wp12_source_low_memory.py','scripts/WP12_LowMemoryObservation_v1.ps1']:
        inputs[name]=c.sha(c.ROOT/name)
    policy={'version':'EXPERIMENTAL_LOW_MEMORY_v1','experiment_only':True,'safety_guarantee':False,
        'model':original['model'],'API_model_digest':original['API_model_digest'],
        'RAM_floor_bytes':1610612736,'GPU_floor_MiB':1024,'commit_floor_bytes':3221225472,
        'runtime_RAM_floor_bytes':805306368,'runtime_commit_floor_bytes':1073741824,
        'OS_low_memory_notification_required':True,'OS_pressure_at_entry_must_be':False,
        'stability_samples':5,'stability_interval_ms':1000,'runtime_sample_ms':250,'HTTP_timeout_seconds':60,
        'scenario_id':'S01','repeat':1,'max_generation_requests':1,'automatic_retry':False,'stage2_enabled':False,
        'automatic_publication':False,'human_semantic_review_required':True,
        'original_policy_unchanged':'WP12-gemma1b-memory-v2; RAM2.5GiB/GPU2GiB',
        'source_prompt_and_generation_config':'unchanged WP12_SOURCE_SINGLE_CASE_v1 S01-R1',
        'inflight_cancellation_semantics':'HTTP client cancellation only; server completion UNKNOWN on error; no kill/unload',
        'immutable_inputs_sha256':inputs,'runner':target.relative_to(c.ROOT).as_posix(),'runner_sha256':c.sha(target)}
    c.save_new(POLICY,policy)
    print({'new_policy':policy['version'],'previous_files_snapshotted':len(paths),'runner_sha256':policy['runner_sha256']})


if __name__=='__main__':main()
