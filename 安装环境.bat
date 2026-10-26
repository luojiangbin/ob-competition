@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ==========================================
echo  首次使用：安装运行环境
echo  需要系统已装 Python 3.11+（python --version 能跑）
echo ==========================================
echo.

python --version 2>nul
if errorlevel 1 (
    echo [错误] 没找到 python 命令。
    echo 请先装 Python 3.11 或更高版本，安装时勾选 "Add to PATH"。
    pause
    exit /b 1
)

if exist ".venv\Scripts\powercontext.exe" (
    echo 环境已存在，跳过安装。
    goto :verify
)

echo [1/2] 创建虚拟环境...
python -m venv .venv
if not exist ".venv\Scripts\python.exe" (
    echo       标准方式失败，改用无 pip 模式...
    python -m venv --without-pip .venv
)

echo [2/2] 安装 PowerContext 1.4.0（约 3-5 分钟）...
if exist ".venv\Scripts\pip.exe" (
    ".venv\Scripts\pip.exe" install "powercontext[cli,server]==1.4.0" -i https://pypi.tuna.tsinghua.edu.cn/simple
) else (
    python -m pip --python ".venv\Scripts\python.exe" install "powercontext[cli,server]==1.4.0" -i https://pypi.tuna.tsinghua.edu.cn/simple
)

if not exist "tools\tmp" mkdir "tools\tmp"

:verify
echo.
".venv\Scripts\powercontext.exe" --version
if errorlevel 1 (
    echo [失败] 安装没成功，把上面的报错拍下来。
    pause
    exit /b 1
)
echo.
echo 安装完成。接下来双击「启动服务.bat」。
pause
