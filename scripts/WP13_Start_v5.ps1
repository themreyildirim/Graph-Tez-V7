[CmdletBinding()]
param([ValidateRange(1024,65535)][int]$Port=8530)
$ErrorActionPreference='Stop'
$projectRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location -LiteralPath $projectRoot
& (Join-Path $projectRoot '.venv_wp13/Scripts/python.exe') -B -m streamlit run apps/arayuz_v5.py `
  --server.address=127.0.0.1 `
  --server.port=$Port `
  --server.headless=true `
  --browser.gatherUsageStats=false `
  --theme.base=light `
  --server.maxUploadSize=20 `
  --client.toolbarMode=minimal
exit $LASTEXITCODE
