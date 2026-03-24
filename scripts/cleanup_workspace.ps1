# Workspace cleanup (safe-by-default)
# - Removes caches/tmp folders created during local runs
# - Moves legacy root artifacts into output/<ticket>/legacy instead of deleting
#
# Usage:
#   .\scripts\cleanup_workspace.ps1
#   .\scripts\cleanup_workspace.ps1 -Aggressive   # also removes heavy Playwright artifacts under output/
#
param(
  [switch]$Aggressive = $false,
  [string]$Ticket = "PA-21"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function TryRemovePath([string]$Path) {
  try {
    if (Test-Path $Path) {
      Remove-Item -Recurse -Force -LiteralPath $Path -ErrorAction Stop
      Write-Host "[Cleanup] removed: $Path"
    }
  } catch {
    Write-Host "[Cleanup] skip (cannot remove): $Path"
    Write-Host "          $($_.Exception.Message)"
  }
}

function TryMoveToLegacy([string]$FilePath) {
  try {
    if (-not (Test-Path $FilePath)) { return }
    $legacyDir = Join-Path $Root ("output\" + $Ticket + "\legacy")
    New-Item -ItemType Directory -Force -Path $legacyDir | Out-Null
    $ts = Get-Date -Format "yyyyMMdd-HHmmss"
    $name = Split-Path -Leaf $FilePath
    $dest = Join-Path $legacyDir ($ts + "-" + $name)
    Move-Item -Force -LiteralPath $FilePath -Destination $dest
    Write-Host "[Cleanup] moved to legacy: $FilePath -> $dest"
  } catch {
    Write-Host "[Cleanup] skip (cannot move): $FilePath"
    Write-Host "          $($_.Exception.Message)"
  }
}

# 1) Move legacy root artifacts (keep history instead of deleting)
TryMoveToLegacy "qa_dashboard_PA21.html"
TryMoveToLegacy "qa_plan_PA-21.md"

# 2) Remove common caches/tmp
@(
  ".pytest_cache",
  ".pytest_tmp",
  ".ruff_cache",
  "__pycache__",
  "test_tmp",
  "pytest_basetemp",
  "pytest_basetemp2",
  "pytest_basetemp_ok",
  "output/_pytest_tmp"
) | ForEach-Object { TryRemovePath $_ }

# 3) Delete stray compiled python files under repo (best-effort)
try {
  Get-ChildItem -Recurse -Force -File -Filter *.pyc -ErrorAction SilentlyContinue |
    ForEach-Object {
      try { Remove-Item -Force -LiteralPath $_.FullName -ErrorAction Stop } catch {}
    }
} catch {}

# 4) Optional aggressive cleanup: heavy Playwright artifacts under output/
if ($Aggressive) {
  $pwDir = Join-Path $Root ("output\" + $Ticket + "\playwright")
  TryRemovePath (Join-Path $pwDir "node_modules")
  TryRemovePath (Join-Path $pwDir "test-results")
  TryRemovePath (Join-Path $pwDir "package-lock.json")

  # playwright-cli logs/artifacts (optional)
  TryRemovePath ".playwright-cli"
  TryRemovePath ".playwright"
}

Write-Host "[Cleanup] done."
