[CmdletBinding()]
param([switch]$RunS16)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$config=Join-Path $root 'configs/WP12_OPENAI_S16_SINGLE_EXECUTION_v1.json'
if ((Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash.ToLowerInvariant() -cne '8b89344b632ecfd48762d2c55988a43a179e6de4bc63e4aa8c0148015ba71e93') {throw 'S16_CONFIG_HASH_CHANGED_STOP'}
$entry=Join-Path $PSScriptRoot 'wp12_openai_S16_v1_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne '00c0ba642fc6bac9c52d68eaedc46624234db0ff070d96e6673a8a4a1f80c507') {throw 'S16_CLIENT_HASH_CHANGED_STOP'}
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
if ($RunS16) { & $python -B -X utf8 $entry --run-s16 } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
