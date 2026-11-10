param([int]$Port = 8765)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) { throw 'Run scripts/setup.ps1 first.' }
& '.\.venv\Scripts\python.exe' -m backend.cli serve --port $Port
