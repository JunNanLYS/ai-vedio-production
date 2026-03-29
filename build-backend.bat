@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo ========================================
echo   AI Video Production - 后端打包脚本
echo   使用 Nuitka 编译 Python 后端
echo ========================================
echo.

REM 设置变量
set PROJECT_ROOT=%~dp0
set DIST_DIR=%PROJECT_ROOT%dist-backend
set BUILD_DIR=%PROJECT_ROOT%build-backend

REM 清理旧的构建文件 (默认不清理，保留缓存加速二次编译)
REM 如需清理，请手动删除 dist-backend 和 build-backend 目录
REM 或使用 PowerShell 脚本: .\build-backend.ps1 -Clean

echo.
echo 开始 Nuitka 编译...
echo 使用 uv run 调用虚拟环境中的 Python
echo.

REM Nuitka 编译命令 (使用 uv run 调用虚拟环境中的 Python)
REM 简化配置，让 Nuitka 自动检测依赖
REM --include-package 已经会包含整个包，不需要额外的 --include-data-files
uv run python -m nuitka ^
    --standalone ^
    --output-filename=ai-video-backend.exe ^
    --output-dir="%DIST_DIR%" ^
    --follow-imports ^
    --include-package=models ^
    --include-package=routers ^
    --windows-console-mode=attach ^
    --assume-yes-for-downloads ^
    --jobs=8 ^
    main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo [错误] Nuitka 编译失败！
    exit /b 1
)

echo.
echo ========================================
echo   编译完成！
echo   输出目录: %DIST_DIR%
echo ========================================
echo.

REM 复制必要的资源文件
echo 复制资源文件...
if not exist "%DIST_DIR%\models" mkdir "%DIST_DIR%\models"
if not exist "%DIST_DIR%\routers" mkdir "%DIST_DIR%\routers"

xcopy /Y /Q "%PROJECT_ROOT%\models\*.py" "%DIST_DIR%\models\"
xcopy /Y /Q "%PROJECT_ROOT%\routers\*.py" "%DIST_DIR%\routers\"
copy /Y "%PROJECT_ROOT%\database.py" "%DIST_DIR%\"

echo.
echo 后端打包完成！
echo 可执行文件: %DIST_DIR%\ai-video-backend.exe

pause
