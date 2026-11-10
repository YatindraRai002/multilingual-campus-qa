param([switch]$WithML)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
New-Item -ItemType Directory -Force -Path '.cache\uv','.cache\tmp','.runtime\python','results' | Out-Null
$env:UV_CACHE_DIR = Join-Path $projectRoot '.cache\uv'
$env:UV_PYTHON_INSTALL_DIR = Join-Path $projectRoot '.runtime\python'
$env:UV_PYTHON_BIN_DIR = Join-Path $projectRoot '.runtime\bin'
$env:TEMP = Join-Path $projectRoot '.cache\tmp'
$env:TMP = $env:TEMP
$env:HF_HOME = Join-Path $projectRoot '.cache\huggingface'
if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw 'Install uv from https://docs.astral.sh/uv/getting-started/installation/ and rerun this script.' }
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    uv python install 3.11.14
    if ($LASTEXITCODE -ne 0) { throw 'Python installation failed.' }
    uv venv --python 3.11.14 .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}
uv pip install --python '.venv\Scripts\python.exe' -e '.[test]'
if ($LASTEXITCODE -ne 0) { throw 'Core dependency installation failed.' }
if ($WithML) {
    uv pip install --python '.venv\Scripts\python.exe' 'torch==2.7.1' --index-url https://download.pytorch.org/whl/cu126
    if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed.' }
    uv pip install --python '.venv\Scripts\python.exe' -e '.[ml,test]'
    if ($LASTEXITCODE -ne 0) { throw 'ML dependency installation failed.' }
}
& '.\.venv\Scripts\python.exe' -m backend.cli audit --check-torch
if ($LASTEXITCODE -ne 0) { throw 'Hardware audit failed.' }
Write-Host 'Setup complete. Run .\.venv\Scripts\python.exe -m backend.cli serve'
