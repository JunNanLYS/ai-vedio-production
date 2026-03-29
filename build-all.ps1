# AI Video Production - 完整打包脚本
# 前端: Electron + Vue 3
# 后端: Python + FastAPI (Nuitka)

param(
    [string]$Platform = "win",  # win, mac, linux
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false,
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI Video Production - 完整打包脚本" -ForegroundColor Cyan
Write-Host "  前端: Electron + Vue 3" -ForegroundColor Cyan
Write-Host "  后端: Python + FastAPI (Nuitka)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 切换到项目根目录
Set-Location $ProjectRoot

# 步骤1: 打包 Python 后端
if (-not $SkipBackend) {
    Write-Host "[步骤 1/3] 打包 Python 后端..." -ForegroundColor Yellow
    Write-Host ""
    
    $BuildBackendScript = Join-Path $ProjectRoot "build-backend.ps1"
    if (-not (Test-Path $BuildBackendScript)) {
        Write-Host "[错误] 找不到 build-backend.ps1 脚本！" -ForegroundColor Red
        exit 1
    }
    
    $BackendBuildArgs = @{}
    if ($Clean) { $BackendBuildArgs["Clean"] = $true }
    
    & $BuildBackendScript @BackendBuildArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 后端打包失败！" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "[步骤 1/3] 后端打包完成！" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[步骤 1/3] 跳过后端打包" -ForegroundColor Gray
    Write-Host ""
}

# 步骤2: 构建 Electron 前端
if (-not $SkipFrontend) {
    Write-Host "[步骤 2/3] 构建 Electron 前端..." -ForegroundColor Yellow
    Write-Host ""
    
    npm run build
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[错误] 前端构建失败！" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "[步骤 2/3] 前端构建完成！" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "[步骤 2/3] 跳过前端构建" -ForegroundColor Gray
    Write-Host ""
}

# 步骤3: 使用 electron-builder 打包
Write-Host "[步骤 3/3] 打包 Electron 应用..." -ForegroundColor Yellow
Write-Host "目标平台: $Platform" -ForegroundColor Gray
Write-Host ""

$BuildCommand = switch ($Platform) {
    "win" { "build:win" }
    "mac" { "build:mac" }
    "linux" { "build:linux" }
    default { "build:win" }
}

npm run $BuildCommand

if ($LASTEXITCODE -ne 0) {
    Write-Host "[错误] Electron 打包失败！" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  打包完成！" -ForegroundColor Cyan
Write-Host "  输出目录: $ProjectRoot\dist" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 显示输出文件
$DistDir = Join-Path $ProjectRoot "dist"
if (Test-Path $DistDir) {
    Write-Host "生成的文件:" -ForegroundColor Green
    Get-ChildItem $DistDir -File | ForEach-Object {
        $SizeMB = [math]::Round($_.Length / 1MB, 2)
        Write-Host "  - $($_.Name) ($SizeMB MB)" -ForegroundColor Gray
    }
}
