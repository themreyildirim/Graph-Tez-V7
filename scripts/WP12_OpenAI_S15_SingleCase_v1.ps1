[CmdletBinding()]
param([switch]$RunS15)
Set-StrictMode -Version Latest
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$config=Join-Path $root 'configs/WP12_OPENAI_S15_SINGLE_EXECUTION_v1.json'
if ((Get-FileHash -LiteralPath $config -Algorithm SHA256).Hash.ToLowerInvariant() -cne '2aea9dfe4a9af05949f541556a9a17d806cd1c654d2142245c31780641109d86') {throw 'S15_CONFIG_HASH_CHANGED_STOP'}
$entry=Join-Path $PSScriptRoot 'wp12_openai_S15_v1_client.py'
if ((Get-FileHash -LiteralPath $entry -Algorithm SHA256).Hash.ToLowerInvariant() -cne 'feb0eaa8559f5c868bdd02e17ed35b63e752e4d734bcc956eeaef2e2a6059f69') {throw 'S15_CLIENT_HASH_CHANGED_STOP'}
$python='C:\Users\emrey\AppData\Local\Programs\Python\Python311\python.exe'
if ($RunS15) { & $python -B -X utf8 $entry --run-s15 } else { & $python -B -X utf8 $entry }
exit $LASTEXITCODE
