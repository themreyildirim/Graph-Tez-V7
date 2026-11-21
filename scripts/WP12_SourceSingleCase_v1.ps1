# S01-R1 only. Real PDF source; no bulk flag, no automatic continuation.
# Source single-case pilot: v2 memory and generation parameters preserved.
# v2: explicitly separate policy; v1 files and decisions remain immutable.
# Kullanici PowerShell'i icindir. Codex bu betigi calistirmaz.
# Indirme/servis baslatma/guvenlik degisikligi/19x3 calismasi YOK.
[CmdletBinding()]
param([switch]$RunFirstCase)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runName = (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N')
$runDir = Join-Path $projectRoot ('reports\qa\WP12\source_single_case_user_runs\' + $runName)
$null = New-Item -ItemType Directory -Path $runDir
$utf8 = New-Object System.Text.UTF8Encoding($false)
function Save-Text([string]$Name, [string]$Value) {
    $p = Join-Path $runDir $Name
    $f = [IO.File]::Open($p, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try { $bytes = $utf8.GetBytes($Value); $f.Write($bytes, 0, $bytes.Length) } finally { $f.Dispose() }
}
function Save-Json([string]$Name, $Value) { Save-Text $Name ($Value | ConvertTo-Json -Depth 40) }
function Hash-Text([string]$Value) {
    $h = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($h.ComputeHash($utf8.GetBytes($Value)))).Replace('-', '').ToLowerInvariant() }
    finally { $h.Dispose() }
}
$record = [ordered]@{
    schema_version = 'WP12-source-single-case-run-v1'
    scenario_id = 'S01'; repeat = 1; maximum_generation_requests = 1
    semantic_success = $null
    memory_policy = 'WP12-gemma1b-memory-v2'
    status = 'INITIALIZING'; started_at = [DateTimeOffset]::Now.ToString('o')
    execution_origin = 'USER_POWERSHELL_SELF_REPORT_NOT_AUTHENTICATION'
    model = 'gemma3:1b-it-q4_K_M'
    expected_digest = 'sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
    local_wrapper_expected_sha256 = 'sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16'
    identity_binding_version = 'WP12-gemma-api-source-v1'
    identity_helper_sha256 = '27fb36d02fb9c6017450fdb8b9a54e9b3819d46465cdfdd3f697a352b60ef6f4'
    thresholds = @{ host_free_bytes = 2684354560; GPU_free_MiB = 2048 }
    run_first_case_requested = [bool]$RunFirstCase; inference_attempts = 0
    new_downloads = 0; models_pulled = 0; service_started = $false
    security_changed = $false; processes_terminated = 0; real_scenario_repeats = 0
    automatic_release = $false; human_semantic_review = 'NOT_PERFORMED_NO_SOURCE_OUTPUT_YET'
    source_contract_sha256 = (Get-FileHash (Join-Path $projectRoot 'docs\plan\WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    frozen_scenarios_sha256 = (Get-FileHash (Join-Path $projectRoot 'reports\qa\WP12\llm_design_v1\frozen_scenarios.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    script_sha256 = (Get-FileHash $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
}

$pythonExe = 'C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
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

$apiClient = $null
try {
    if (-not ('WP12GemmaSmokeNativeV2' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
public static class WP12GemmaSmokeNativeV2 {
 [StructLayout(LayoutKind.Sequential)] public struct Memory {
  public uint length, load; public ulong total, available, totalPage, freePage, totalVirtual, freeVirtual, extended;
 }
 [DllImport("kernel32.dll", SetLastError=true)] static extern bool GlobalMemoryStatusEx(ref Memory m);
 [DllImport("kernel32.dll")] static extern IntPtr GetCurrentProcess();
 [DllImport("advapi32.dll", SetLastError=true)] static extern bool OpenProcessToken(IntPtr p, uint a, out IntPtr t);
 [DllImport("advapi32.dll", SetLastError=true)] static extern bool GetTokenInformation(IntPtr t, int k, out int v, int n, out int r);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr h);
 [StructLayout(LayoutKind.Sequential)] public struct Performance {
  public uint cb; public UIntPtr CommitTotal,CommitLimit,CommitPeak,PhysicalTotal,PhysicalAvailable,SystemCache,KernelTotal,KernelPaged,KernelNonpaged,PageSize;
  public uint HandleCount,ProcessCount,ThreadCount;
 }
 [DllImport("psapi.dll", SetLastError=true)] static extern bool GetPerformanceInfo(ref Performance p,uint cb);
 public static ulong ReadCommitAvailable() { Performance p=new Performance(); p.cb=(uint)Marshal.SizeOf(typeof(Performance));
  if(!GetPerformanceInfo(ref p,p.cb)) throw new Win32Exception();
  return (p.CommitLimit.ToUInt64()-p.CommitTotal.ToUInt64())*p.PageSize.ToUInt64(); }
 public static Memory ReadMemory() { Memory m = new Memory(); m.length=(uint)Marshal.SizeOf(typeof(Memory));
  if(!GlobalMemoryStatusEx(ref m)) throw new Win32Exception(); return m; }
 public static bool IsAppContainer() { IntPtr t; if(!OpenProcessToken(GetCurrentProcess(),8,out t)) throw new Win32Exception();
  try {int v,r; if(!GetTokenInformation(t,29,out v,4,out r)) throw new Win32Exception(); return v!=0;} finally {CloseHandle(t);} }
}
'@
    }
    function Sample-Memory {
        $m = [WP12GemmaSmokeNativeV2]::ReadMemory()
        return @{ at = [DateTimeOffset]::Now.ToString('o'); available_bytes = $m.available; total_bytes = $m.total; load_percent = $m.load; commit_available_bytes = [WP12GemmaSmokeNativeV2]::ReadCommitAvailable() }
    }
    function Sample-GPU {
        $lines = @(& nvidia-smi --query-gpu=name,memory.total,memory.free,driver_version --format=csv,noheader,nounits 2>&1)
        if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 1) { throw 'GPU_QUERY_UNAVAILABLE_OR_MULTIPLE_GPUS: no inference' }
        $parts = ([string]$lines[0]).Split(',')
        if ($parts.Count -ne 4) { throw 'GPU_QUERY_PARSE_FAILED' }
        return @{ name = $parts[0].Trim(); total_MiB = [int]$parts[1].Trim(); free_MiB = [int]$parts[2].Trim(); driver = $parts[3].Trim() }
    }
    $record['is_appcontainer'] = [WP12GemmaSmokeNativeV2]::IsAppContainer()
    $record['memory_before'] = Sample-Memory
    $record['GPU_before'] = Sample-GPU
    $record['powershell_version'] = $PSVersionTable.PSVersion.ToString()
    Add-Type -AssemblyName System.Net.Http
    $handler = New-Object System.Net.Http.HttpClientHandler
    $handler.UseProxy = $false; $handler.AllowAutoRedirect = $false
    $apiClient = New-Object System.Net.Http.HttpClient($handler)
    $apiClient.Timeout = [TimeSpan]::FromSeconds(60)
    $callNumber = 0
    function Read-LocalMetadata([string]$Route) {
        $script:callNumber++
        $url = 'http://127.0.0.1:11434/api/' + $Route
        $text = $apiClient.GetStringAsync($url).GetAwaiter().GetResult()
        Save-Text ('metadata_' + $script:callNumber + '_' + $Route + '.json') $text
        return ($text | ConvertFrom-Json)
    }
    # Metadata okunabilirligi RAM kapisindan bagimsizdir; hicbir model yuklemez.
    $version = Read-LocalMetadata 'version'; $record['server_version'] = $version.version
    if ($version.version -cne '0.40.6') { throw 'UNVERIFIED_OLLAMA_VERSION_FOR_PINNED_TOKEN_RENDERER' }
    $tags = Read-LocalMetadata 'tags'
    $found = @($tags.models | Where-Object { $_.name -ceq $record.model })
    if ($found.Count -ne 1) { throw 'EXACT_SELECTED_MODEL_NOT_INSTALLED: no pull attempted' }
    $digest = ([string]$found[0].digest).ToLowerInvariant()
    if (-not $digest.StartsWith('sha256:')) { $digest = 'sha256:' + $digest }
    $record['observed_digest'] = $digest
    $identityHelper = Join-Path $PSScriptRoot 'WP12_GemmaIdentity_v1.ps1'
    $actualHelperHash = (Get-FileHash -LiteralPath $identityHelper -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($actualHelperHash -cne $record.identity_helper_sha256) { throw 'IDENTITY_HELPER_SHA256_MISMATCH' }
    . $identityHelper
    $modelRoot = if ($env:OLLAMA_MODELS) { $env:OLLAMA_MODELS } else { Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ollama\models' }
    $record['identity_validation'] = Assert-WP12GemmaIdentity -ModelRoot $modelRoot -ApiDigest $digest
    $loaded = Read-LocalMetadata 'ps'
    $record['already_loaded_models'] = @($loaded.models).Count
    if ($record.is_appcontainer) { $record.status = 'STOP_APPContainer_NOT_USER_HOST'; return }
    if ($record.memory_before.available_bytes -lt 2684354560 -or $record.GPU_before.free_MiB -lt 2048 -or $record.memory_before.commit_available_bytes -lt 3221225472) {
        $record.status = 'STOP_MEMORY_GATE'; return
    }
    if (-not $RunFirstCase) { $record.status = 'METADATA_ONLY_READY_NO_INFERENCE'; return }
    # Baska oturumun yuklu modelini etkilememek icin otomatik unload/keepalive degisikligi yok.
    if ($record.already_loaded_models -ne 0) { $record.status = 'STOP_MODEL_ALREADY_LOADED'; return }
    $casePolicyPath = Join-Path $projectRoot 'configs\WP12_SOURCE_SINGLE_CASE_v1.json'
    $record['case_policy_sha256'] = (Get-FileHash -LiteralPath $casePolicyPath -Algorithm SHA256).Hash.ToLowerInvariant()
    $casePolicy = Get-Content -LiteralPath $casePolicyPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($record.script_sha256 -cne $casePolicy.runner_sha256) { throw 'SOURCE_RUNNER_HASH_MISMATCH' }
    foreach ($relative in @('scripts/wp12_source_case.py','scripts/wp12_vocab_counter.py','scripts/wp12_llm_contract.py')) {
        $expected = $casePolicy.immutable_inputs_sha256.PSObject.Properties[$relative].Value
        $actual = (Get-FileHash -LiteralPath (Join-Path $projectRoot $relative) -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actual -cne $expected) { throw 'SOURCE_UTILITY_CODE_HASH_MISMATCH' }
    }
    $record['python_preflight_exit_code'] = Invoke-PythonStage 'preflight'
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
    $record['admission_samples'] = @()
    for ($j=0; $j -lt 5; $j++) {
        $sample = Sample-Memory
        $record.admission_samples += $sample
        if ($sample.available_bytes -lt 2684354560 -or $sample.commit_available_bytes -lt 3221225472) {
            $record.status = 'STOP_V2_STABILITY_OR_COMMIT_GATE'; return
        }
        if ($j -lt 4) { Start-Sleep -Milliseconds 1000 }
    }
    $record['memory_immediately_before'] = Sample-Memory
    $record['GPU_immediately_before'] = Sample-GPU
    if ($record.memory_immediately_before.available_bytes -lt 2684354560 -or $record.GPU_immediately_before.free_MiB -lt 2048 -or $record.memory_immediately_before.commit_available_bytes -lt 3221225472) {
        $record.status = 'STOP_MEMORY_GATE_RECHECK'; return
    }
    $content = New-Object System.Net.Http.StringContent($requestText, $utf8, 'application/json')
    $record['inference_attempts'] = 1
    $record['real_scenario_repeats'] = 1
    $record.status = 'SOURCE_EXPLANATION_IN_PROGRESS'
    $samples = New-Object 'System.Collections.Generic.List[object]'
    $samples.Add($record.memory_immediately_before)
    $started = [DateTimeOffset]::Now
    # Tek istek; retry/fallback/ensemble yok. HTTP timeout sunucunun durdugunu kanitlamaz.
    $task = $apiClient.PostAsync('http://127.0.0.1:11434/api/chat', $content)
    try {
        while (-not $task.IsCompleted) {
            $sample = Sample-Memory; $samples.Add($sample)
            if ($sample.available_bytes -lt 1073741824) {
                $record['memory_warning'] = $true
                $record.status = 'SOURCE_CLIENT_CANCELLED_MEMORY_WARNING'
                $apiClient.CancelPendingRequests()
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if ($record.status -ceq 'SOURCE_CLIENT_CANCELLED_MEMORY_WARNING') {
            throw 'HOST_RAM_BELOW_1GiB: HTTP cancellation only; server completion is unknown; no retry or process termination'
        }
        $response = $task.GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        Save-Text 'source_response_raw.json' $body
        $record['HTTP_status'] = [int]$response.StatusCode
        $record['response_sha256'] = Hash-Text $body
        if (-not $response.IsSuccessStatusCode) { throw 'SOURCE_HTTP_ERROR: raw response retained' }
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
    } finally {
        $record['elapsed_seconds'] = ([DateTimeOffset]::Now - $started).TotalSeconds
        $samples.Add((Sample-Memory)); Save-Json 'memory_samples.json' @($samples.ToArray())
        $record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU
        if ($record.memory_after.available_bytes -lt 1073741824 -and $record.status -ceq 'SOURCE_CANDIDATE_PENDING_HUMAN_REVIEW') { $record.status = 'SOURCE_COMPLETED_WITH_MEMORY_WARNING' }
    }
} catch {
    $record['error'] = $_.Exception.ToString()
    if ($record.status -cne 'SOURCE_CLIENT_CANCELLED_MEMORY_WARNING') { $record.status = 'FAILED_OR_TIMED_OUT_NO_RETRY' }
    $record['server_completion_if_request_started'] = 'UNKNOWN_ON_CLIENT_ERROR; no process killed or forced unload'
} finally {
    if ($null -ne $apiClient) { $apiClient.Dispose() }
    $record['finished_at'] = [DateTimeOffset]::Now.ToString('o')
    Save-Json 'run_record.json' $record
    $manifest = [ordered]@{}
    Get-ChildItem -LiteralPath $runDir -File | Sort-Object Name | ForEach-Object {
        $manifest[$_.Name] = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    }
    Save-Json 'file_hashes.json' $manifest
    Write-Host ('WP12 status: ' + $record.status)
    Write-Host ('Evidence directory: ' + $runDir)
}
