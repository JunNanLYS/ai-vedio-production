# AI Video Production - 后端打包脚本 (PowerShell)
# 使用 Nuitka 编译 Python 后端

param(
    [string]$Mode = "standalone",  # standalone 或 onefile
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot
$DistDir = Join-Path $ProjectRoot "dist-backend"
$BuildDir = Join-Path $ProjectRoot "build-backend"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Video Production - 后端打包脚本" -ForegroundColor Cyan
Write-Host "  使用 Nuitka 编译 Python 后端" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 清理旧的构建文件 (只有显式指定 -Clean 时才清理，保留缓存加速二次编译)
if ($Clean) {
    Write-Host "清理旧的构建目录..." -ForegroundColor Yellow
    if (Test-Path $DistDir) { Remove-Item -Recurse -Force $DistDir }
    if (Test-Path $BuildDir) { Remove-Item -Recurse -Force $BuildDir }
}

Write-Host ""
Write-Host "开始 Nuitka 编译..." -ForegroundColor Green
Write-Host "模式: $Mode" -ForegroundColor Green
Write-Host ""

# 基础参数 - 简化配置，让 Nuitka 自动检测依赖
# --include-package 已经会包含整个包，不需要额外的 --include-data-files
$NuitkaArgs = @(
    "--standalone",
    "--output-filename=ai-video-backend.exe",
    "--output-dir=`"$DistDir`"",
    "--follow-imports",
    "--include-package=models",
    "--include-package=routers",
    "--include-package=aiosqlite",
    "--windows-console-mode=attach",
    "--assume-yes-for-downloads",
    "--jobs=8",
    "main.py"
)

# 根据模式添加参数
if ($Mode -eq "onefile") {
    $NuitkaArgs = @("--onefile") + $NuitkaArgs
}

# 执行 Nuitka 编译 (使用 uv run 调用虚拟环境中的 Python)
$NuitkaCmd = "uv run python -m nuitka " + ($NuitkaArgs -join " ")
Write-Host "执行命令: $NuitkaCmd" -ForegroundColor Gray
Write-Host ""

& uv run python -m nuitka @NuitkaArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] Nuitka 编译失败！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  编译完成！" -ForegroundColor Cyan
Write-Host "  输出目录: $DistDir" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 对于 standalone 模式，复制必要的资源文件
if ($Mode -eq "standalone") {
    Write-Host "复制资源文件..." -ForegroundColor Yellow
    
    # 复制 models 目录
    $ModelsDir = Join-Path $DistDir "main.dist\models"
    if (-not (Test-Path $ModelsDir)) { New-Item -ItemType Directory -Path $ModelsDir -Force | Out-Null }
    Copy-Item -Path (Join-Path $ProjectRoot "models\*.py") -Destination $ModelsDir -Force
    
    # 复制 routers 目录
    $RoutersDir = Join-Path $DistDir "main.dist\routers"
    if (-not (Test-Path $RoutersDir)) { New-Item -ItemType Directory -Path $RoutersDir -Force | Out-Null }
    Copy-Item -Path (Join-Path $ProjectRoot "routers\*.py") -Destination $RoutersDir -Force
    
    # 复制 database.py
    Copy-Item -Path (Join-Path $ProjectRoot "database.py") -Destination (Join-Path $DistDir "main.dist\") -Force
    
    # 复制 http_client.py
    Copy-Item -Path (Join-Path $ProjectRoot "http_client.py") -Destination (Join-Path $DistDir "main.dist\") -Force
    
    # 复制 cache.py
    Copy-Item -Path (Join-Path $ProjectRoot "cache.py") -Destination (Join-Path $DistDir "main.dist\") -Force
    
    Write-Host "资源文件复制完成！" -ForegroundColor Green
}

Write-Host ""
Write-Host "后端打包完成！" -ForegroundColor Green
Write-Host "可执行文件: $DistDir\ai-video-backend.exe (或 main.dist\ai-video-backend.exe)" -ForegroundColor Green
