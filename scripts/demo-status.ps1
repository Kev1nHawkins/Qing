[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Continue"

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$PidFile = Join-Path $RepoRoot "work\demo-host.pid.json"
Set-Location -LiteralPath $RepoRoot

$dockerVersion = (docker info --format "{{.ServerVersion}}" 2>$null | Out-String).Trim()
$dockerOk = $LASTEXITCODE -eq 0
$mysqlState = if ($dockerOk) {
    (docker compose ps mysql --format json 2>$null | Out-String).Trim()
} else {
    ""
}

$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1

$savedPid = $null
$savedPidAlive = $false
$savedPidMatches = $false
if (Test-Path -LiteralPath $PidFile) {
    try {
        $metadata = Get-Content -LiteralPath $PidFile -Raw | ConvertFrom-Json
        $savedPid = [int]$metadata.pid
        $process = Get-CimInstance Win32_Process -Filter "ProcessId=$savedPid"
        $savedPidAlive = $null -ne $process
        $savedPidMatches = $savedPidAlive -and
            ([string]$process.CommandLine -match 'uvicorn') -and
            ([string]$process.CommandLine -match 'app\.main:app')
    } catch {
        $savedPidMatches = $false
    }
}

$healthStatus = "unavailable"
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing -TimeoutSec 5
    $payload = $response.Content | ConvertFrom-Json
    $healthStatus = "HTTP $([int]$response.StatusCode), code=$($payload.code)"
} catch {
    $healthStatus = "unreachable"
}

$branch = (git branch --show-current 2>$null | Out-String).Trim()
$gitDirty = -not [string]::IsNullOrWhiteSpace((@(git status --porcelain 2>$null) -join ""))

[ordered]@{
    repoRoot = $RepoRoot
    dockerEngine = if ($dockerOk) { "running ($dockerVersion)" } else { "unavailable" }
    mysqlHealthy = $mysqlState -match '"Health":"healthy"'
    port8000Listening = $null -ne $listener
    port8000Pid = if ($listener) { $listener.OwningProcess } else { $null }
    savedUvicornPid = $savedPid
    savedPidAlive = $savedPidAlive
    savedPidMatchesUvicorn = $savedPidMatches
    health = $healthStatus
    gitBranch = $branch
    gitWorkingTree = if ($gitDirty) { "dirty" } else { "clean" }
} | Format-List
