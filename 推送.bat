@echo off
chcp 65001 >nul
cd /d "%~dp0"
set GIT=%~dp0tools\git\cmd\git.exe

echo ==========================================
echo 把本地提交推送到 GitHub
echo ==========================================
echo.
echo 请先在 GitHub 上新建一个空仓库（不要勾选 Add README），
echo 然后把它给你的地址粘贴到下面，例如：
echo   https://github.com/luojiangbin2026/ob-competition.git
echo.
set /p REMOTE=仓库地址：

if "%REMOTE%"=="" (
    echo 没有输入地址，退出。
    pause
    exit /b 1
)

"%GIT%" remote remove origin 2>nul
"%GIT%" remote add origin %REMOTE%
echo.
echo 开始推送。如果弹出用户名/密码：
echo   用户名 = 你的 GitHub 用户名
echo   密码   = Personal Access Token（不是登录密码）
echo.
"%GIT%" push -u origin main
echo.
echo 推送结束。成功的话去网页刷新看看。
pause
