# Offline identity-only regression. Does not execute the smoke runner or any HTTP.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$OutputPath)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $root 'scripts\WP12_GemmaIdentity_v1.ps1')
$cache=Join-Path ([Environment]::GetFolderPath('UserProfile')) '.ollama\models'
$results=New-Object 'System.Collections.Generic.List[object]'
function Check([string]$Name,[scriptblock]$Action) {
    try { $null=& $Action; $results.Add(@{test=$Name;status='PASS'}) }
    catch { $results.Add(@{test=$Name;status='FAIL';error=$_.Exception.ToString()}) }
}
function Must-Fail([scriptblock]$Action,[string]$Expected) {
    $caught=$false
    try { $null=& $Action } catch {
        if ($_.Exception.Message -notlike ('*'+$Expected+'*')) { throw }
        $caught=$true
    }
    if (-not $caught) { throw 'Expected identity rejection was not raised' }
}
$api='sha256:97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
$wrapper='sha256:313f48e331f7326ce703657512ab64022d8813bbaa512e06d0ace43cb026cf16'
Check 'real_cache_correct_API_source_digest_passes' {
    $x=Assert-WP12GemmaIdentity -ModelRoot $cache -ApiDigest $api
    if (-not $x.identity_binding_valid -or $x.local_wrapper_manifest_file_sha256 -cne $wrapper) { throw 'wrong roles' }
}
Check 'bare_API_digest_passes' { $null=Assert-WP12GemmaIdentity -ModelRoot $cache -ApiDigest $api.Substring(7) }
Check 'wrapper_hash_is_rejected_as_API_identity' {
    Must-Fail { Assert-WP12GemmaIdentity -ModelRoot $cache -ApiDigest $wrapper } 'MODEL_DIGEST_MISMATCH'
}
Check 'unrelated_API_digest_rejected' {
    Must-Fail { Assert-WP12GemmaIdentity -ModelRoot $cache -ApiDigest ('sha256:'+('0'*64)) } 'MODEL_DIGEST_MISMATCH'
}
$tempRoot=[IO.Path]::GetFullPath([IO.Path]::GetTempPath())
$scratch=Join-Path $tempRoot ('WP12_GemmaIdentity_test_'+[Guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory -Path $scratch
try {
    $relative='manifests\registry.ollama.ai\library\gemma3\1b-it-q4_K_M'
    $testWrapper=Join-Path $scratch $relative
    $null=New-Item -ItemType Directory -Path (Split-Path $testWrapper)
    $null=New-Item -ItemType Directory -Path (Join-Path $scratch 'blobs')
    Copy-Item -LiteralPath (Join-Path $cache $relative) -Destination $testWrapper
    $sourceName='sha256-97558784bdc9175075a72655bf360b15da17df6b3b9e5182af9f8c0c8e58ba7c'
    $sourceOriginal=Join-Path $cache ('blobs\'+$sourceName)
    $sourceTest=Join-Path $scratch ('blobs\'+$sourceName)
    Copy-Item -LiteralPath $sourceOriginal -Destination $sourceTest
    Check 'metadata_only_copy_validates_without_weight_load' { $null=Assert-WP12GemmaIdentity -ModelRoot $scratch -ApiDigest $api }
    [IO.File]::AppendAllText($testWrapper,' ')
    Check 'changed_wrapper_bytes_rejected_separately' {
        Must-Fail { Assert-WP12GemmaIdentity -ModelRoot $scratch -ApiDigest $api } 'LOCAL_WRAPPER_SHA256_MISMATCH'
    }
    Copy-Item -LiteralPath (Join-Path $cache $relative) -Destination $testWrapper -Force
    [IO.File]::AppendAllText($sourceTest,' ')
    Check 'changed_source_manifest_bytes_rejected' {
        Must-Fail { Assert-WP12GemmaIdentity -ModelRoot $scratch -ApiDigest $api } 'SOURCE_MANIFEST_SHA256_MISMATCH'
    }
} finally {
    # Only the explicitly named test directory, checked inside system TEMP, is removed.
    $resolved=[IO.Path]::GetFullPath($scratch)
    if (-not $resolved.StartsWith($tempRoot,[StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($resolved) -notlike 'WP12_GemmaIdentity_test_*') { throw 'unsafe test cleanup path' }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
$oldRuns=Get-ChildItem -LiteralPath (Join-Path $root 'reports\qa\WP12\gemma1b_v2_user_smoke_runs') -Directory
foreach($d in $oldRuns) {
    $p=Join-Path $d.FullName 'run_record.json'
    $r=Get-Content -LiteralPath $p -Raw -Encoding UTF8 | ConvertFrom-Json
    Check ('actual_failed_run_API_identity_now_validates_'+$d.Name) {
        if ($r.inference_attempts -ne 0 -or $r.expected_digest -cne $wrapper) { throw 'unexpected original record' }
        $null=Assert-WP12GemmaIdentity -ModelRoot $cache -ApiDigest $r.observed_digest
    }
}
$final=@{scope='OFFLINE_IDENTITY_ONLY_NO_HTTP_NO_INFERENCE';count=$results.Count;results=@($results.ToArray())}
$utf8=New-Object System.Text.UTF8Encoding($false)
if(Test-Path -LiteralPath $OutputPath){throw 'Test log already exists'}
[IO.File]::WriteAllText($OutputPath,($final|ConvertTo-Json -Depth 12),$utf8)
if(@($results|Where-Object {$_.status -ne 'PASS'}).Count){exit 1}
Write-Output ('Offline PowerShell identity regressions passed: '+$results.Count)
