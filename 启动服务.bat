@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\powercontext.exe" (
    echo ==========================================
    echo  还没安装运行环境
    echo  请先双击「安装环境.bat」，装完再运行这个
    echo ==========================================
    pause
    exit /b 1
)
if not exist "tools\tmp" mkdir "tools\tmp"

set POWERCONTEXT_HOME=%~dp0data
set TMP=%~dp0tools\tmp
set TEMP=%~dp0tools\tmp

echo ==========================================
echo  PowerContext 服务启动中...
echo  启动后浏览器打开： http://127.0.0.1:8000/docs
echo  这个窗口不要关，关了服务就停了
echo ==========================================
".venv\Scripts\powercontext.exe" server run
echo.
echo 服务已退出。
pause
