[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$BackendRoot = Join-Path $RepoRoot "backend"
$PythonPath = Join-Path $RepoRoot ".venv\Scripts\python.exe"
$WorkRoot = Join-Path $RepoRoot "work"
$PidFile = Join-Path $WorkRoot "demo-host.pid.json"

Set-Location -LiteralPath $RepoRoot

$mysqlTcpReady = (Test-NetConnection 127.0.0.1 -Port 3306 -WarningAction SilentlyContinue).TcpTestSucceeded
if (-not $mysqlTcpReady) {
    docker info --format "{{.ServerVersion}}" | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "MySQL is unreachable and Docker Engine is unavailable. Start Docker Desktop normally and retry."
    }

    $mysqlState = (docker compose ps mysql --format json | Out-String).Trim()
    if ($mysqlState -notmatch '"Health":"healthy"') {
        Write-Host "Starting the existing MySQL service without build or pull..."
        docker compose up -d --no-build --pull never mysql
        if ($LASTEXITCODE -ne 0) {
            throw "MySQL failed to start. Confirm that mysql:8.4 and the existing volume are present."
        }
    }

    $mysqlReady = $false
    for ($attempt = 1; $attempt -le 24; $attempt++) {
        $mysqlState = (docker compose ps mysql --format json | Out-String).Trim()
        if ($mysqlState -match '"Health":"healthy"') {
            $mysqlReady = $true
            break
        }
        Start-Sleep -Seconds 5
    }
    if (-not $mysqlReady) {
        throw "MySQL did not become healthy within 120 seconds. Run scripts\demo-status.ps1."
    }
} else {
    Write-Host "MySQL is already reachable on 127.0.0.1:3306; Docker checks are skipped."
}

if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Project virtual environment is missing: $PythonPath"
}

$listener = Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener) {
    throw "Port 8000 is already owned by PID $($listener.OwningProcess). A second Uvicorn will not be started."
}

if (-not (Test-Path -LiteralPath $WorkRoot)) {
    New-Item -ItemType Directory -Path $WorkRoot | Out-Null
}

$envFile = Join-Path $RepoRoot ".env"
if (-not (Test-Path -LiteralPath $envFile)) {
    $envFile = Join-Path $RepoRoot ".env.example"
    Write-Warning ".env is missing; development defaults from .env.example will be used. Create and review .env before the demo."
}

Get-Content -LiteralPath $envFile | ForEach-Object {
    if ($_ -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(.*)$') {
        $name = $matches[1]
        $value = $matches[2].Trim().Trim([char[]]@("'", '"'))
        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }
}

if ([string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw "DATABASE_URL is not configured."
}
$env:DATABASE_URL = $env:DATABASE_URL -replace '@mysql:3306/', '@127.0.0.1:3306/'
$env:PYTHONUTF8 = "1"

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$stdoutLog = Join-Path $WorkRoot "demo-host-$stamp.out.log"
$stderrLog = Join-Path $WorkRoot "demo-host-$stamp.err.log"
$arguments = @(
    "-m", "uvicorn", "app.main:app",
    "--app-dir", $BackendRoot,
    "--host", "127.0.0.1",
    "--port", "8000"
)

$process = Start-Process `
    -FilePath $PythonPath `
    -ArgumentList $arguments `
    -WorkingDirectory $BackendRoot `
    -RedirectStandardOutput $stdoutLog `
    -RedirectStandardError $stderrLog `
    -PassThru

$started = $false
$listenerPid = $null
$listenerProcess = $null
$foreignListener = $false
$backendPattern = [regex]::Escape($BackendRoot)
for ($attempt = 1; $attempt -le 30; $attempt++) {
    $listener = Get-NetTCPConnection `
        -LocalAddress "127.0.0.1" `
        -LocalPort 8000 `
        -State Listen `
        -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($listener) {
        $listenerPid = [int]$listener.OwningProcess
        $listenerProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$listenerPid"
        $command = [string]$listenerProcess.CommandLine
        if (
            $listenerProcess.Name -ne "python.exe" -or
            $command -notmatch 'uvicorn' -or
            $command -notmatch 'app\.main:app' -or
            $command -notmatch $backendPattern
        ) {
            $foreignListener = $true
            break
        }
        $started = $true
        break
    }
    Start-Sleep -Seconds 2
}

if (-not $started) {
    if (
        -not $foreignListener -and
        -not $process.HasExited
    ) {
        Stop-Process -Id $process.Id
    }
    Remove-Item -LiteralPath $PidFile -Force -ErrorAction SilentlyContinue
    $tail = if (Test-Path -LiteralPath $stderrLog) {
        Get-Content -LiteralPath $stderrLog -Tail 100
    }
    if ($foreignListener) {
        throw "Port 8000 is owned by a process that does not match this project; it was not stopped."
    }
    throw "This project's Uvicorn did not listen on port 8000 within 60 seconds. stderr:`n$($tail -join "`n")"
}

[ordered]@{
    pid = $listenerPid
    launcherPid = $process.Id
    repoRoot = $RepoRoot
    backendRoot = $BackendRoot
    startedAt = (Get-Date).ToString("o")
    stdoutLog = $stdoutLog
    stderrLog = $stderrLog
} | ConvertTo-Json | Set-Content -LiteralPath $PidFile -Encoding UTF8

$health = Invoke-RestMethod -Uri "http://127.0.0.1:8000/health" -TimeoutSec 10
if ($health.code -ne 0) {
    throw "Uvicorn is listening, but /health returned a non-zero business code."
}

Write-Host "Lingchao host backend started."
Write-Host "PID: $listenerPid"
Write-Host "Launcher PID: $($process.Id)"
Write-Host "Health: http://127.0.0.1:8000/health"
Write-Host "Swagger: http://127.0.0.1:8000/docs"
Write-Host "Stop command: .\scripts\demo-stop-host.ps1"
