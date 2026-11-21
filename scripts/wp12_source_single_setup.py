"""S01-R1 normal kullanıcı PowerShell paketi. Ollama/API/inference çalıştırmaz."""
import copy
import json
from pathlib import Path
import sys

from wp12_source_case import ROOT,QA,context,request_for,case_schema,dump
from wp12_vocab_counter import RUNTIME,GGUF,sha,template_from_gguf


def save(path,value):
    path=Path(path)
    if path.exists():raise ValueError('new output already exists: '+str(path))
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def main():
    target=ROOT/'scripts/WP12_SourceSingleCase_v1.ps1';assert not target.exists()
    base=(ROOT/'scripts/WP12_Gemma1B_UserPowerShellSmoke_v2_1.ps1').read_text(encoding='utf-8')
    text=base.replace('param([switch]$RunSmoke)','param([switch]$RunFirstCase)')
    text=text.replace('$RunSmoke','$RunFirstCase')
    text=text.replace('run_smoke_requested','run_first_case_requested')
    text=text.replace('NOT_PERFORMED_TECHNICAL_ECHO_ONLY','NOT_PERFORMED_NO_SOURCE_OUTPUT_YET')
    text=text.replace('gemma1b_v2_1_user_smoke_runs','source_single_case_user_runs')
    text=text.replace('WP12-gemma1b-user-smoke-run-v2_1','WP12-source-single-case-run-v1')
    text=text.replace("    memory_policy = 'WP12-gemma1b-memory-v2'",
        "    scenario_id = 'S01'; repeat = 1; maximum_generation_requests = 1\n    semantic_success = $null\n    memory_policy = 'WP12-gemma1b-memory-v2'")
    text=text.replace("if ([version]$version.version -lt [version]'0.30.0') { throw 'RUNTIME_TOO_OLD_FOR_LOCAL_ARTIFACT' }",
        "if ($version.version -cne '0.40.6') { throw 'UNVERIFIED_OLLAMA_VERSION_FOR_PINNED_TOKEN_RENDERER' }")
    start=text.index("    $record['admission_samples'] = @()")
    end=text.index('    $schema = @{',start)
    stable=text[start:end];text=text[:start]+text[end:]
    start=text.index('    $schema = @{');end=text.index("    $record['memory_immediately_before']",start)
    preflight='''    $record['python_preflight_exit_code'] = Invoke-PythonStage 'preflight'
    if ($record.python_preflight_exit_code -ne 0) { $record.status = 'SOURCE_PREFLIGHT_FAILED_NO_GENERATION'; return }
    $preflight = Get-Content -LiteralPath (Join-Path $runDir 'python_preflight_result.json') -Raw -Encoding UTF8 | ConvertFrom-Json
    $record['input_token_count'] = $preflight.input_token_count
    if (-not $preflight.admitted -or $preflight.status -cne 'PREFLIGHT_PASS') {
        $record.status = 'CONTEXT_BUDGET_REJECTED_NO_GENERATION'; return
    }
    $requestText = Get-Content -LiteralPath (Join-Path $runDir 'source_request.json') -Raw -Encoding UTF8
    $record['request_sha256'] = (Get-FileHash -LiteralPath (Join-Path $runDir 'source_request.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($record.request_sha256 -cne $preflight.request_sha256) { throw 'SOURCE_REQUEST_HASH_MISMATCH' }
    $record['technical_probe_scope'] = 'REAL_PDF_S01_R1_SOURCE_EXPLANATION_NOT_ECHO'
'''
    verify_code='''    $casePolicyPath = Join-Path $projectRoot 'configs\\WP12_SOURCE_SINGLE_CASE_v1.json'
    $record['case_policy_sha256'] = (Get-FileHash -LiteralPath $casePolicyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $casePolicy = Get-Content -LiteralPath $casePolicyPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($record.script_sha256 -cne $casePolicy.runner_sha256) { throw 'SOURCE_RUNNER_HASH_MISMATCH' }
    foreach ($relative in @('scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')) {
        $expected = $casePolicy.immutable_inputs_sha256.PSObject.Properties[$relative].Value
        $actual = (Get-FileHash -LiteralPath (Join-Path $projectRoot $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -cne $expected) { throw 'SOURCE_UTILITY_CODE_HASH_MISMATCH' }
    }
'''
    text=text[:start]+verify_code+preflight+stable+text[end:]
    text=text.replace("Save-Text 'smoke_response_raw.json' $body","Save-Text 'source_response_raw.json' $body")
    start=text.index('        $parsed = $body | ConvertFrom-Json')
    end=text.index('    } finally {',start)
    review='''        if (-not $response.IsSuccessStatusCode) { throw 'SOURCE_HTTP_ERROR: raw response retained' }
        $parsed = $body | ConvertFrom-Json
        $record['response_model'] = $parsed.model
        $record['done'] = $parsed.done; $record['done_reason'] = $parsed.done_reason
        $record['prompt_eval_count'] = $parsed.prompt_eval_count; $record['eval_count'] = $parsed.eval_count
        $record['python_review_exit_code'] = Invoke-PythonStage 'review'
        if ($record.python_review_exit_code -ne 0) { $record.status = 'SOURCE_REVIEW_UTILITY_FAILED'; return }
        $review = Get-Content -LiteralPath (Join-Path $runDir 'structural_review.json') -Raw -Encoding UTF8 | ConvertFrom-Json
        $record['structural_review_status'] = $review.status
        $record.status = $review.status
        $record['automatic_release'] = $false
        $record['human_semantic_review'] = 'PENDING_HUMAN_REVIEW'
'''
    text=text[:start]+review+text[end:]
    text=text.replace("$record['inference_attempts'] = 1","$record['inference_attempts'] = 1\n    $record['real_scenario_repeats'] = 1")
    text=text.replace('SMOKE_CLIENT_CANCELLED_MEMORY_WARNING','SOURCE_CLIENT_CANCELLED_MEMORY_WARNING')
    text=text.replace('# Identity fix only; memory policy v2 and request payload unchanged.','# Source single-case pilot: v2 memory and generation parameters preserved.')
    text=text.replace('SMOKE_IN_PROGRESS','SOURCE_EXPLANATION_IN_PROGRESS')
    text=text.replace('SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW','SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW')
    text=text.replace('SMOKE_COMPLETED_WITH_MEMORY_WARNING','SOURCE_COMPLETED_WITH_MEMORY_WARNING')
    # Ağsız Python ön/son kontrolü; native vocabulary işlemi model ağırlığı yüklemez.
    py=str(Path(sys.executable)).replace("'","''")
    utility='''
$pythonExe = '__PYTHON__'
$sourceUtility = Join-Path $PSScriptRoot 'wp12_source_case.py'
function Invoke-PythonStage([string]$Action) {
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = $pythonExe
    $info.Arguments = '-X utf8 "' + $sourceUtility + '" ' + $Action + ' --run-directory "' + $runDir + '"'
    $info.UseShellExecute = $false; $info.CreateNoWindow = $true
    $info.RedirectStandardOutput = $true; $info.RedirectStandardError = $true
    $info.StandardOutputEncoding = [Text.Encoding]::UTF8; $info.StandardErrorEncoding = [Text.Encoding]::UTF8
    $child = New-Object System.Diagnostics.Process; $child.StartInfo = $info
    $null = $child.Start()
    $stdout = $child.StandardOutput.ReadToEndAsync(); $stderr = $child.StandardError.ReadToEndAsync()
    if (-not $child.WaitForExit(60000)) {
        $record['python_child_completion'] = 'UNKNOWN_TIMEOUT_NO_PROCESS_KILL'
        throw 'PYTHON_UTILITY_TIMEOUT_NO_GENERATION_RETRY'
    }
    Save-Text ('python_' + $Action + '_stdout.txt') $stdout.GetAwaiter().GetResult()
    Save-Text ('python_' + $Action + '_stderr.txt') $stderr.GetAwaiter().GetResult()
    $exitCode = $child.ExitCode; $child.Dispose()
    return $exitCode
}
'''.replace('__PYTHON__',py)
    text=text.replace('$apiClient = $null',utility+'\n$apiClient = $null',1)
    # Yalnız ilk vaka; bu parametre/sürümde batch/57 döngüsü yoktur.
    text='# S01-R1 only. Real PDF source; no bulk flag, no automatic continuation.\n'+text
    target.write_text(text,encoding='utf-8')
    immutable=[
        'AGENTS.md','docs/plan/ROADMAP_V7.md','docs/plan/WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md',
        'docs/plan/WP12_DOCUMENT_DATA_CONTRACT_v1.md','docs/schemas/WP12_local_llm_candidate_v1.schema.json',
        'reports/qa/WP12/llm_design_v1/frozen_scenarios.json','reports/qa/WP12/llm_design_v1/acceptance_criteria.csv',
        'reports/qa/WP12/pilot_v1/source_evidence_bundle.json','reports/qa/WP12/pilot_v1/source_context_annotations.json',
        'scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/WP12_GemmaIdentity_v1.ps1','scripts/wp12_llm_contract.py',
        'reports/qa/WP12/source_single_case_v1/package/request.json','reports/qa/WP12/source_single_case_v1/package/context.json']
    native={n:sha(RUNTIME/n) for n in ['libllama.dll','ggml.dll','ggml-base.dll']}
    cfg={
        'version':'WP12-source-single-case-v1','status':'S01_R1_READY_FOR_USER_ONLY',
        'model':'gemma3:1b-it-q4_K_M',
        'API_model_digest':'sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c',
        'model_blob_sha256':'2f8c3d137f2496dcb4019e17a50f2974b89c1be1a742db3c80cc86f91cafeeef',
        'server_version_pinned':'0.40.6','native_build_commit':'620d2225c',
        'native_tokenizer_files_sha256':native,
        'chat_template_sha256':__import__('hashlib').sha256(template_from_gguf()['tokenizer.chat_template'].encode()).hexdigest(),
        'immutable_inputs_sha256':{p:sha(ROOT/p) for p in immutable},
        'memory_policy':'WP12-gemma1b-memory-v2','RAM_floor_bytes':2684354560,'GPU_floor_MiB':2048,'commit_floor_bytes':3221225472,
        'HTTP_timeout_seconds':60,'num_ctx':2048,'input_token_limit':1536,'num_predict':384,'reserve_tokens':128,
        'num_batch':32,'temperature':0,'seed':20261108,'think':False,'stream':False,'keep_alive':0,
        'truncate':False,'shift':False,'scenario_id':'S01','repeat':1,'max_generation_requests':1,
        'stage2_enabled':False,'automatic_continuation':False,'automatic_publication':False,
        'structural_pass_is_semantic_success':False,'human_review_required':True,'runner_sha256':sha(target),
        'runner':target.relative_to(ROOT).as_posix(),'python_executable':str(Path(sys.executable)),
        'download_or_training':False}
    save(ROOT/'configs/WP12_SOURCE_SINGLE_CASE_v1.json',cfg)
    scenarios=json.loads((ROOT/'reports/qa/WP12/llm_design_v1/frozen_scenarios.json').read_text(encoding='utf-8'))
    slots=[{'scenario_id':s['scenario_id'],'repeat':r,'status':'WAIT_FIRST_CASE_REVIEW' if s['scenario_id']=='S01' and r==1 else 'BLOCKED_STAGE2_NOT_ENABLED',
            'immutable_question':s['question_tr'],'immutable_acceptance':s['acceptance_criteria_tr']}
           for s in scenarios for r in [1,2,3]]
    save(QA/'stage2_plan_NOT_EXECUTABLE.json',{
        'status':'PREPARED_PLAN_ONLY_BLOCKED_UNTIL_FIRST_CASE_HUMAN_REVIEW',
        'planned_evaluation_slots':57,'first_slot':'S01-R1','remaining_slots_if_first_accepted':56,
        'reuse_first_actual_S01_R1_only_if_same_prompt_model_config_hashes_and_human_accepted':True,
        'max_generation_requests_may_be_less_due_to_preflight_refusals':True,
        'bulk_executor_shipped':False,'actual_requests_started':0,'automatic_continuation':False,'slots':slots})
    # Özellikle istenen inceleme kapsamları gerçek kaynaklarla, LLM yanıtı olmadan.
    critical={}
    for sid in ['S04','S06','S07','S17']:
        c=context(sid);critical[sid]={'frozen_scenario':c['scenario'],'actual_sources':c['sources'],
            'LLM_status':'NOT_RUN','semantic_review':'NOT_PERFORMED',
            'review_focus':{'S04':'Erythromycin bilinmeyen sıklık ve p4-p5 devam bağlamı',
                'S06':'tetracycline sınıfını doğrudan doxycycline kanıtına yükseltmeme',
                'S07':'BUN sınıf ifadesi + sınıf girişi + doxycycline istisnasının ikisi de',
                'S17':'kaynak dışı skor/SHAP/Δz/MedDRA talebinde ret'}[sid]}
    save(QA/'critical_scenario_review_materials_NOT_RUN.json',critical)
    print('Single real S01-R1 runner prepared; stage2 plan57 slots BLOCKED; no inference')


if __name__=='__main__':main()
