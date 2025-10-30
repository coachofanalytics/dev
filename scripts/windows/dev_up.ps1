Param(
    [int]$Port = 8000,
    [string]$Settings = "clone",
    [switch]$Https
)

Write-Host "=== CODA Dev Up (PowerShell) ===" -ForegroundColor Cyan
Write-Host "Port     : $Port"
Write-Host "Settings : $Settings"
Write-Host "HTTPS    : $Https"

# Move to repo root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
Set-Location $RepoRoot

# Prefer Git Bash if available
$bash = (Get-Command bash -ErrorAction SilentlyContinue)
if ($bash) {
    $args = @("scripts/dev/dev_server.sh", "--port", "$Port", "--settings", "$Settings")
    if ($Https) { $args += "--https" }
    & bash @args
    exit $LASTEXITCODE
}

# Fallback: run using python directly (HTTP)
Write-Warning "bash not found. Starting Django directly (HTTP)."
Set-Location "$RepoRoot\coda"
$settingsModule = if ($Settings -eq "clone") { "coda_project.coda_settings.local_prod_clone_settings" } else { "coda_project.coda_settings.local_settings" }
python manage.py runserver 0.0.0.0:$Port --settings=$settingsModule
