@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   AI Video Production - 完整打包脚本
echo   前端: Electron + Vue 3
echo   后端: Python + FastAPI (Nuitka)
echo ========================================
echo.

set PROJECT_ROOT=%~dp0
cd /d "%PROJECT_ROOT%"

REM 步骤1: 打包 Python 后端
echo [步骤 1/3] 打包 Python 后端...
echo.
call build-backend.bat
if %ERRORLEVEL% neq 0 (
    echo [错误] 后端打包失败！
    exit /b 1
)

echo.
echo [步骤 1/3] 后端打包完成！
echo.

REM 步骤2: 构建 Electron 前端
echo [步骤 2/3] 构建 Electron 前端...
echo.
call npm run build
if %ERRORLEVEL% neq 0 (
    echo [错误] 前端构建失败！
    exit /b 1
)

echo.
echo [步骤 2/3] 前端构建完成！
echo.

REM 步骤3: 使用 electron-builder 打包
echo [步骤 3/3] 打包 Electron 应用...
echo.
call npm run build:win
if %ERRORLEVEL% neq 0 (
    echo [错误] Electron 打包失败！
    exit /b 1
)

echo.
echo ========================================
echo   打包完成！
echo   输出目录: %PROJECT_ROOT%dist
echo ========================================
echo.

pause
