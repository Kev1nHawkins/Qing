[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$BackendRoot = Join-Path $RepoRoot "backend"
$PidFile = Join-Path $RepoRoot "work\demo-host.pid.json"

if (-not (Test-Path -LiteralPath $PidFile)) {
    Write-Host "Project PID file not found; no Python process will be stopped."
    exit 0
}

$metadata = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
$pidValue = [int]$metadata.pid

if ([IO.Path]::GetFullPath([string]$metadata.repoRoot) -ne $RepoRoot) {
    throw "PID metadata belongs to another project path; refusing to stop the process."
}

$process = Get-CimInstance Win32_Process -Filter "ProcessId=$pidValue"
if (-not $process) {
    Remove-Item -LiteralPath $PidFile -Force
    Write-Host "PID $pidValue no longer exists; stale PID metadata was removed."
    exit 0
}

$command = [string]$process.CommandLine
$backendPattern = [regex]::Escape($BackendRoot)
if (
    $process.Name -ne "python.exe" -or
    $command -notmatch 'uvicorn' -or
    $command -notmatch 'app\.main:app' -or
    $command -notmatch $backendPattern
) {
    throw "PID $pidValue does not match this project's Uvicorn command; refusing to stop it."
}

Stop-Process -Id $pidValue -ErrorAction Stop

for ($attempt = 1; $attempt -le 20; $attempt++) {
    if (-not (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
        break
    }
    Start-Sleep -Milliseconds 500
}

if (Get-Process -Id $pidValue -ErrorAction SilentlyContinue) {
    throw "PID $pidValue did not stop within the allowed time."
}

Remove-Item -LiteralPath $PidFile -Force
Write-Host "Stopped this project's Uvicorn PID $pidValue."
Write-Host "MySQL and Docker Desktop were not stopped."
