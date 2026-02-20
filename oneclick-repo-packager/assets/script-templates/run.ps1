$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
  Write-Error "Python not found. Install Python 3 first."
  exit 1
}

$req = Join-Path $Root "webui\requirements.txt"
if (Test-Path $req) {
  python -m pip install --user -r $req
}

$port = 7860
$cfgPath = Join-Path $Root "webui\config.json"
if (Test-Path $cfgPath) {
  try {
    $cfg = Get-Content -Raw $cfgPath | ConvertFrom-Json
    if ($cfg.webui_port) { $port = [int]$cfg.webui_port }
  } catch {}
}

Start-Process -FilePath "python" -ArgumentList "webui\app.py" -WorkingDirectory $Root
Start-Sleep -Seconds 2
Start-Process "http://localhost:$port"
