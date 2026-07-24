[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
Set-Location -LiteralPath $RepoRoot

docker compose stop
if ($LASTEXITCODE -ne 0) {
    throw "Compose services failed to stop. Run docker compose ps to inspect status."
}

Write-Host "Compose services stopped. Containers, images, and volumes were preserved."
