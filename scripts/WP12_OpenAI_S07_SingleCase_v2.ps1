# V2 butce onayi ve sadece bir S07; S04 calistirilamaz.
[CmdletBinding()]
param([switch]$AcceptBudgetV2,[switch]$RunS07)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
if ($RunS07 -and -not $AcceptBudgetV2) { throw 'BUDGET_V2_EXPLICIT_ACCEPTANCE_REQUIRED_NO_API' }
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policy=Join-Path $root 'configs/WP12_OPENAI_SMALL_PILOT_BUDGET_v2.json'
if ((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'ba86c3e58d8e54c32be3eb6a8b6a4fdf4c4679a5f6cbf7341277068e1d160b49') { throw 'V2_POLICY_HASH_CHANGED_STOP' }
$entry=Join-Path $PSScriptRoot 'wp12_openai_S07_v2_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '8c7d37c80e29f3f40a4e2e367ddedf0a497114476897d261c21bd01866a7fe02') { throw 'V2_CLIENT_HASH_CHANGED_STOP' }
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
if ($RunS07) { & $python -B -X utf8 $entry --accept-budget-v2 --run-s07 } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
