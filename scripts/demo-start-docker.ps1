[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location -LiteralPath $RepoRoot

docker info --format "{{.ServerVersion}}" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Docker Engine is unavailable. Start Docker Desktop normally and retry."
}

docker compose config --quiet
if ($LASTEXITCODE -ne 0) {
    throw "docker-compose.yml validation failed."
}

Write-Host "Starting existing images only; no build or pull will be performed."
docker compose up -d --no-build --pull never
if ($LASTEXITCODE -ne 0) {
    throw "Compose startup failed. If an image is missing, build it after Docker Hub connectivity is restored."
}

docker compose ps
Write-Host "User frontend: http://127.0.0.1:5173"
Write-Host "Admin frontend: http://127.0.0.1:5174"
Write-Host "Swagger: http://127.0.0.1:8000/docs"
