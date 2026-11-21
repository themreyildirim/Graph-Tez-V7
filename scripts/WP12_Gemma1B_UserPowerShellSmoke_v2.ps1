# v2: explicitly separate policy; v1 files and decisions remain immutable.
# Kullanici PowerShell'i icindir. Codex bu betigi calistirmaz.
# Indirme/servis baslatma/guvenlik degisikligi/19x3 calismasi YOK.
[CmdletBinding()]
param([switch]$RunSmoke)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runName = (Get-Date -Format 'yyyyMMdd_HHmmss') + '_' + [Guid]::NewGuid().ToString('N')
$runDir = Join-Path $projectRoot ('reports\qa\WP12\gemma1b_v2_user_smoke_runs\' + $runName)
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
    schema_version = 'WP12-gemma1b-user-smoke-run-v2'
    memory_policy = 'WP12-gemma1b-memory-v2'
    status = 'INITIALIZING'; started_at = [DateTimeOffset]::Now.ToString('o')
    execution_origin = 'USER_POWERSHELL_SELF_REPORT_NOT_AUTHENTICATION'
    model = 'gemma3:1b-it-q4_K_M'
    expected_digest = 'sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16'
    thresholds = @{ host_free_bytes = 2684354560; GPU_free_MiB = 2048 }
    run_smoke_requested = [bool]$RunSmoke; inference_attempts = 0
    new_downloads = 0; models_pulled = 0; service_started = $false
    security_changed = $false; processes_terminated = 0; real_scenario_repeats = 0
    automatic_release = $false; human_semantic_review = 'NOT_PERFORMED_TECHNICAL_ECHO_ONLY'
    source_contract_sha256 = (Get-FileHash (Join-Path $projectRoot 'docs\plan\WP12_LOCAL_LLM_OUTPUT_CONTRACT_v1.md') -Algorithm SHA256).Hash.ToLowerInvariant()
    frozen_scenarios_sha256 = (Get-FileHash (Join-Path $projectRoot 'reports\qa\WP12\llm_design_v1\frozen_scenarios.json') -Algorithm SHA256).Hash.ToLowerInvariant()
    script_sha256 = (Get-FileHash $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
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
    if ([version]$version.version -lt [version]'0.30.0') { throw 'RUNTIME_TOO_OLD_FOR_LOCAL_ARTIFACT' }
    $tags = Read-LocalMetadata 'tags'
    $found = @($tags.models | Where-Object { $_.name -ceq $record.model })
    if ($found.Count -ne 1) { throw 'EXACT_SELECTED_MODEL_NOT_INSTALLED: no pull attempted' }
    $digest = ([string]$found[0].digest).ToLowerInvariant()
    if (-not $digest.StartsWith('sha256:')) { $digest = 'sha256:' + $digest }
    $record['observed_digest'] = $digest
    if ($digest -cne $record.expected_digest) { throw 'MODEL_DIGEST_MISMATCH: do not silently switch model' }
    $loaded = Read-LocalMetadata 'ps'
    $record['already_loaded_models'] = @($loaded.models).Count
    if ($record.is_appcontainer) { $record.status = 'STOP_APPContainer_NOT_USER_HOST'; return }
    if ($record.memory_before.available_bytes -lt 2684354560 -or $record.GPU_before.free_MiB -lt 2048 -or $record.memory_before.commit_available_bytes -lt 3221225472) {
        $record.status = 'STOP_MEMORY_GATE'; return
    }
    if (-not $RunSmoke) { $record.status = 'METADATA_ONLY_READY_NO_INFERENCE'; return }
    # Baska oturumun yuklu modelini etkilememek icin otomatik unload/keepalive degisikligi yok.
    if ($record.already_loaded_models -ne 0) { $record.status = 'STOP_MODEL_ALREADY_LOADED'; return }
    $record['admission_samples'] = @()
    for ($j=0; $j -lt 5; $j++) {
        $sample = Sample-Memory
        $record.admission_samples += $sample
        if ($sample.available_bytes -lt 2684354560 -or $sample.commit_available_bytes -lt 3221225472) {
            $record.status = 'STOP_V2_STABILITY_OR_COMMIT_GATE'; return
        }
        if ($j -lt 4) { Start-Sleep -Milliseconds 1000 }
    }
    $schema = @{ type = 'object'; properties = @{ probe = @{ type = 'string'; enum = @('WP12_GEMMA1B_SMOKE_V2') } }; required = @('probe'); additionalProperties = $false }
    $payload = [ordered]@{
        model = $record.model; stream = $false; think = $false; keep_alive = 0
        messages = @(@{role='user';content='Technical echo only. Return exactly {"probe":"WP12_GEMMA1B_SMOKE_V2"}. No medical content, no explanation.'})
        format = $schema
        options = @{ num_ctx = 2048; num_predict = 384; temperature = 0; seed = 20261108; num_batch = 32 }
    }
    $requestText = $payload | ConvertTo-Json -Depth 20 -Compress
    Save-Text 'smoke_request.json' $requestText
    $record['request_sha256'] = Hash-Text $requestText
    $record['technical_probe_scope'] = 'ONE_NONCLINICAL_SCHEMA_ECHO_NOT_PDF_EXPLANATION'
    $record['memory_immediately_before'] = Sample-Memory
    $record['GPU_immediately_before'] = Sample-GPU
    if ($record.memory_immediately_before.available_bytes -lt 2684354560 -or $record.GPU_immediately_before.free_MiB -lt 2048 -or $record.memory_immediately_before.commit_available_bytes -lt 3221225472) {
        $record.status = 'STOP_MEMORY_GATE_RECHECK'; return
    }
    $content = New-Object System.Net.Http.StringContent($requestText, $utf8, 'application/json')
    $record['inference_attempts'] = 1
    $record.status = 'SMOKE_IN_PROGRESS'
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
                $record.status = 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING'
                $apiClient.CancelPendingRequests()
                break
            }
            Start-Sleep -Milliseconds 250
        }
        if ($record.status -ceq 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING') {
            throw 'HOST_RAM_BELOW_1GiB: HTTP cancellation only; server completion is unknown; no retry or process termination'
        }
        $response = $task.GetAwaiter().GetResult()
        $body = $response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        Save-Text 'smoke_response_raw.json' $body
        $record['HTTP_status'] = [int]$response.StatusCode
        $record['response_sha256'] = Hash-Text $body
        $parsed = $body | ConvertFrom-Json
        if (-not $response.IsSuccessStatusCode) { throw 'SMOKE_HTTP_ERROR: raw response retained' }
        $record['response_model'] = $parsed.model
        $record['done'] = $parsed.done; $record['done_reason'] = $parsed.done_reason
        $record['prompt_eval_count'] = $parsed.prompt_eval_count
        $record['eval_count'] = $parsed.eval_count
        $echoOK = ([string]$parsed.message.content) -cmatch '^\s*\{\s*"probe"\s*:\s*"WP12_GEMMA1B_SMOKE_V2"\s*\}\s*$'
        $record['schema_echo_exact'] = $echoOK
        if ($parsed.done -ne $true -or $parsed.done_reason -cne 'stop' -or $parsed.model -cne $record.model -or -not $echoOK -or $parsed.prompt_eval_count -gt 1536) {
            $record.status = 'SMOKE_INVALID_RESPONSE'
        } else { $record.status = 'SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW' }
    } finally {
        $record['elapsed_seconds'] = ([DateTimeOffset]::Now - $started).TotalSeconds
        $samples.Add((Sample-Memory)); Save-Json 'memory_samples.json' @($samples.ToArray())
        $record['memory_after'] = Sample-Memory; $record['GPU_after'] = Sample-GPU
        if ($record.memory_after.available_bytes -lt 1073741824 -and $record.status -ceq 'SMOKE_TECHNICAL_PASS_PENDING_EXTERNAL_REVIEW') { $record.status = 'SMOKE_COMPLETED_WITH_MEMORY_WARNING' }
    }
} catch {
    $record['error'] = $_.Exception.ToString()
    if ($record.status -cne 'SMOKE_CLIENT_CANCELLED_MEMORY_WARNING') { $record.status = 'FAILED_OR_TIMED_OUT_NO_RETRY' }
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
