# Windows 环境安装指南（PowerContext 1.4.0）

> 官方要求 macOS / Linux，Windows 标注为 `experimental`。所以按"先试 A，不行换 B"来。

---

## 方案 A：原生 Windows（先试这个，约 15 分钟）

### A1 装工具

PowerShell（普通权限即可）：

```powershell
winget install --id astral-sh.uv -e --accept-source-agreements --accept-package-agreements
winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
winget install --id GitHub.cli -e --accept-source-agreements --accept-package-agreements
```

装完**关闭并重开 PowerShell**，验证：

```powershell
uv --version
git --version
gh --version
```

### A2 装 Python 3.12（不要动系统的 3.14）

```powershell
uv python install 3.12
uv python list --only-installed
```

### A3 装 PowerContext

```powershell
$env:UV_DEFAULT_INDEX="https://pypi.tuna.tsinghua.edu.cn/simple"
uv tool install --force "powercontext[cli,server]==1.4.0"
powercontext --version
```

### A4 初始化并启动

```powershell
mkdir $HOME\powercontext-demo
cd $HOME\powercontext-demo
powercontext config init --language zh --output .env
powercontext config validate --env-file .env
powercontext server run --env-file .env
```

向导里的选择：

| 问题 | 选什么 | 原因 |
|---|---|---|
| Storage | **SQLite** | 零依赖，先跑通 |
| Usage | Only on this machine | 本机演示 |
| Memory capabilities | **Basic memory** | 不需要任何模型 API Key |
| Dashboard | 开 | 演示时能截图，很加分 |
| Agent | 先跳过或选 DSH | 后面再接 |

### A5 另开一个终端验证

```powershell
cd $HOME\powercontext-demo
$env:POWERCONTEXT_SERVER_HTTP_PORT = (Select-String -Path .env -Pattern '^POWERCONTEXT_SERVER_HTTP_PORT=').Line.Split('=')[1]
Get-Content .env | ForEach-Object { if($_ -match '^([A-Z_]+)=(.*)$'){ Set-Item -Path "env:$($matches[1])" -Value $matches[2] } }
powercontext ready
powercontext capabilities
```

看到 `ready` 就成了。

---

## 方案 B：WSL2 + Ubuntu（A 失败再用，约 30–40 分钟）

需要管理员权限，可能要重启一次。

```powershell
# 管理员 PowerShell
wsl --install -d Ubuntu-22.04
```

重启后设置 Linux 用户名密码，然后：

```bash
sudo apt update && sudo apt install -y git curl
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.local/bin/env
uv tool install --force "powercontext[cli,server]==1.4.0"
powercontext --version
```

之后所有命令都在 WSL 里执行，Windows 侧用 `\\wsl$\Ubuntu-22.04\home\<user>\...` 访问文件。

---

## 常见报错对照

| 报错 / 现象 | 原因 | 处理 |
|---|---|---|
| `powercontext: 无法将...识别` | PATH 没刷新 | 关掉终端重开；或 `$HOME\.local\bin` 加进 PATH |
| pip 下载超时 | 国内网络 | 设 `UV_DEFAULT_INDEX` 为清华源 |
| `config validate` 报缺字段 | 向导没走完 | 重新 `config init` |
| `ready` 返回 `degraded` | 推理依赖没配 | Basic memory 下可忽略，看 capabilities 里 memory 是否为 true |
| 端口被占用 | 之前起过 Server | `Get-NetTCPConnection -LocalPort <端口>` 找到进程结束 |
| Dashboard 打不开 | 认证开了但没填 token | 看 `.env` 里的 `POWERCONTEXT_SERVER_AUTH_TOKEN` |
| `server run` 秒退 | 数据库文件权限 / 路径含中文 | 换到 `C:\pc-demo` 这类纯英文路径 |

---

## 装完要给我的四条输出

```powershell
uv --version
git --version
powercontext --version
powercontext ready
```

贴给我之后，我接着做：fork 仓库、写 `seed.py` 灌 5 个场景、跑第一轮 A/B 对照。
