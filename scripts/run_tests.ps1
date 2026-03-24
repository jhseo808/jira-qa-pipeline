# QA 파이프라인 단위 테스트 실행 (Windows PowerShell)
# 사용: .\scripts\run_tests.ps1
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) {
    $Py = "python"
}

& $Py -m pytest tests -v --tb=short @args
exit $LASTEXITCODE
