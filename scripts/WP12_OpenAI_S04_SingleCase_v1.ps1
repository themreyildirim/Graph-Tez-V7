# Yalniz S04: frozen prompt/schema; v2 30HTTP/10inference/$0.25 degismez.
[CmdletBinding()]
param([switch]$RunS04)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policy=Join-Path $root 'configs/WP12_OPENAI_S04_SINGLE_EXECUTION_v1.json'
if ((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'afad3cce7b13096b52ecafdbfa3b4088f33764f5ccb59a88a6886b81daae2208') { throw 'S04_SCOPE_CONFIG_HASH_CHANGED_STOP' }
$entry=Join-Path $PSScriptRoot 'wp12_openai_S04_v1_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '97c47b04c63ed5f62c40697961cc668435b11d8963905e83d95c0b88595cd992') { throw 'S04_CLIENT_HASH_CHANGED_STOP' }
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
if ($RunS04) { & $python -B -X utf8 $entry --run-s04 } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
