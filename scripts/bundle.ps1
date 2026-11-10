$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
& '.\.venv\Scripts\python.exe' 'scripts\bundle.py'
if ($LASTEXITCODE -ne 0) { throw 'Source bundle creation failed.' }
