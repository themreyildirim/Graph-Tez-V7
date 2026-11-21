# Kullanici onayli farkli-hesap S01; eski run/kilit/rezervler degismez.
[CmdletBinding()]
param([switch]$RunS01)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policy=Join-Path $projectRoot 'configs/WP12_OPENAI_CORRECTED_ACCOUNT_S01_v1.json'
if ((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash.ToLowerInvariant() -cne '98280ecfdb2f80da82ca0672f2b87793c5fcb7b758a0e2c49f77098af3df84b0') { throw 'CORRECTED_ACCOUNT_POLICY_CHANGED_STOP' }
$entry=Join-Path $PSScriptRoot 'wp12_openai_corrected_account_v1.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '076644dd80668d35e6b2af70cad1d7a431404a1479211b0cdaafcb2d86f83b82') { throw 'CORRECTED_ACCOUNT_EXECUTOR_CHANGED_STOP' }
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
# API key yalniz proje .env icinde Python tarafindan okunur; argv/log/env dump yok.
if ($RunS01) { & $python -B -X utf8 $entry --run-single-s01 } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
