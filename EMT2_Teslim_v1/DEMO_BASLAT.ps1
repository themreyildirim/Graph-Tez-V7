[CmdletBinding()]param([ValidateRange(1024,65535)][int]$Port=8527)
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python=Join-Path $root '.venv_wp13/Scripts/python.exe'
$app=Join-Path $PSScriptRoot 'demo/uygulama.py'
Push-Location -LiteralPath $root
try { & $python -B -m streamlit run $app --server.address=127.0.0.1 --server.port=$Port --server.headless=true --browser.gatherUsageStats=false --theme.base=light --server.maxUploadSize=20 }
finally {Pop-Location}
