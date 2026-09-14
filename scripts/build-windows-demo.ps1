param(
    [string]$PythonExe = ""
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot
$sourceRoot = Join-Path $repoRoot "tools\windows-demo-launcher"
$artifactRoot = Join-Path $sourceRoot "artifacts"
$releaseRoot = Join-Path $repoRoot "release\windows-demo"

if (-not $PythonExe) {
    $venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
    $PythonExe = if (Test-Path -LiteralPath $venvPython) { $venvPython } else { "python" }
}

& $PythonExe -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "缺少唯一构建依赖 PyInstaller。请先在受信任的 Python 环境中安装 PyInstaller。"
}

if (Test-Path -LiteralPath $artifactRoot) {
    Remove-Item -LiteralPath $artifactRoot -Recurse -Force
}
if (Test-Path -LiteralPath $releaseRoot) {
    # This directory only contains generated release artifacts.
    Remove-Item -LiteralPath $releaseRoot -Recurse -Force
}
New-Item -ItemType Directory -Path $artifactRoot, $releaseRoot -Force | Out-Null

foreach ($entry in @(
    @{ Script = "launcher.py"; Name = "岭潮共创-启动" },
    @{ Script = "stopper.py"; Name = "岭潮共创-停止" }
)) {
    & $PythonExe -m PyInstaller `
        --noconfirm `
        --clean `
        --onefile `
        --console `
        --name $entry.Name `
        --paths $sourceRoot `
        --distpath $artifactRoot `
        --workpath (Join-Path $artifactRoot "work-$($entry.Name)") `
        --specpath $artifactRoot `
        (Join-Path $sourceRoot $entry.Script)
    if ($LASTEXITCODE -ne 0) { throw "$($entry.Name) 构建失败。" }
}

Copy-Item -LiteralPath (Join-Path $artifactRoot "岭潮共创-启动.exe") -Destination $releaseRoot -Force
Copy-Item -LiteralPath (Join-Path $artifactRoot "岭潮共创-停止.exe") -Destination $releaseRoot -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot "README-评委必看.txt") -Destination $releaseRoot -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "docker-compose.yml") -Destination $releaseRoot -Force
Copy-Item -LiteralPath (Join-Path $repoRoot "docker-compose.demo.yml") -Destination $releaseRoot -Force
Copy-Item -LiteralPath (Join-Path $repoRoot ".env.demo.example") -Destination $releaseRoot -Force
New-Item -ItemType Directory -Path (Join-Path $releaseRoot "docker-images"), (Join-Path $releaseRoot "launcher-logs") -Force | Out-Null

Write-Host "Windows 启停器已生成：$releaseRoot"
