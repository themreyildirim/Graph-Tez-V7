# Normal kullanici PowerShell'i; ilk S01 icin kullanici onayi sonrasi tek komut.
[CmdletBinding()]
param([switch]$RunFirstCase)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$policy=Join-Path $projectRoot 'configs/WP12_OPENAI_API_PILOT_v1.json'
if ((Get-FileHash -LiteralPath $policy -Algorithm SHA256).Hash.ToLowerInvariant() -cne '9c347cb6c5c8a47def803a881403e7bbccb2eb2c40b801c9bdb38d71047e4989') { throw 'POLICY_CHANGED_SAFE_STOP' }
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
$entry=Join-Path $PSScriptRoot 'wp12_openai_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '811612946a555b72730dd1f7890c4782974c0bdbb2a1b0038e3c97a6e966957d') { throw 'CLIENT_CHANGED_SAFE_STOP' }
# Key env/dotenv'den Python icinde yuklenir; argv/header/transcript/env dump yok.
if ($RunFirstCase) { & $python -B -X utf8 $entry --run-first-case } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
