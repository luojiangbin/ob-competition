@echo off
chcp 65001 >nul
cd /d "%~dp0experiments"
set PYTHONIOENCODING=utf-8

if not exist "..\.venv\Scripts\python.exe" (
    echo 还没安装运行环境，请先回到上级目录双击「安装环境.bat」
    pause
    exit /b 1
)

echo [1/2] 灌入 5 个场景...
"..\.venv\Scripts\python.exe" seed.py
echo.
echo [2/2] 跑 20 条召回测试...
"..\.venv\Scripts\python.exe" evaluate.py
echo.
echo 其他对照组：
echo   ..\.venv\Scripts\python.exe evaluate.py --cases cases_synonym.jsonl --expand
echo   ..\.venv\Scripts\python.exe stress.py
pause
