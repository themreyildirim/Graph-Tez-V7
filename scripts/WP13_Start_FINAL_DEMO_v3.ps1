[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=8501)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectRoot
& (Join-Path $projectRoot '.venv_wp13/Scripts/python.exe') -B -m streamlit run apps/drug_safety_explorer_FINAL_v3.py --server.address=127.0.0.1 --server.port=$Port --theme.base=light --browser.gatherUsageStats=false --server.headless=true --server.maxUploadSize=20
exit $LASTEXITCODE
