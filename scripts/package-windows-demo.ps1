param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$releaseRoot = Join-Path $repoRoot "release\windows-demo"
$imagesDir = Join-Path $releaseRoot "docker-images"
$imageArchive = Join-Path $imagesDir "lingchao-demo-images.tar"
$zipPath = Join-Path $repoRoot "release\岭潮共创-Windows一键演示包.zip"

& (Join-Path $PSScriptRoot "build-windows-demo.ps1") -PythonExe $PythonExe

Push-Location $repoRoot
try {
    docker compose build backend frontend-user frontend-admin
    if ($LASTEXITCODE -ne 0) { throw "Docker 镜像构建失败。" }

    docker tag lingchao-co-create-backend:latest lingchao/backend:demo
    docker tag lingchao-co-create-frontend-user:latest lingchao/frontend-user:demo
    docker tag lingchao-co-create-frontend-admin:latest lingchao/frontend-admin:demo
    docker tag docker.1ms.run/library/mysql:8.4 mysql:8.4

    New-Item -ItemType Directory -Path $imagesDir -Force | Out-Null
    docker save -o $imageArchive lingchao/backend:demo lingchao/frontend-user:demo lingchao/frontend-admin:demo mysql:8.4
    if ($LASTEXITCODE -ne 0) { throw "离线镜像导出失败。" }
}
finally {
    Pop-Location
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
if (Test-Path -LiteralPath $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    $releaseRoot,
    $zipPath,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)

$hash = Get-FileHash -LiteralPath $zipPath -Algorithm SHA256
Write-Host "发布包：$zipPath"
Write-Host "SHA-256：$($hash.Hash)"
