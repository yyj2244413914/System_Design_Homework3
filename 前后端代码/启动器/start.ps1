# 智能课堂 · 启动逻辑
# ① 检查/启动 数据库 2881   ② 检查/启动 后端 8000   ③ 等端口就绪   ④ 打开登录页
# 全过程写入 启动日志.txt，方便排查

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

# 后端目录：本脚本在 前后端代码\启动器\ 里，backend 在上一级
$backend = Join-Path $root '..\backend'
if (-not (Test-Path $backend)) { $backend = Join-Path $root '..\..\前后端代码\backend' }

$log = Join-Path $root 'startup.log'

function Log([string]$msg) {
    Write-Host $msg
    Add-Content -Path $log -Value ('[{0}] {1}' -f (Get-Date -Format 'HH:mm:ss'), $msg) -Encoding UTF8
}

function Test-Port([int]$p) {
    $c = New-Object System.Net.Sockets.TcpClient
    try { $c.Connect('127.0.0.1', $p); $c.Close(); return $true }
    catch { $c.Dispose(); return $false }
}

function Wait-Port([int]$p, [int]$seconds) {
    for ($i = 0; $i -lt ($seconds * 2); $i++) {
        if (Test-Port $p) { return $true }
        Start-Sleep -Milliseconds 500
    }
    return (Test-Port $p)
}

Set-Content -Path $log -Value ('启动智慧课堂  ' + (Get-Date)) -Encoding UTF8
Log '============================================================'
Log '   智能课堂 · 启动'
Log '============================================================'
Log ''

# 在发行版内部脱管一个常驻进程把 WSL 撑住：发行版一停，里面的 seekdb.service 就跟着停。
# 用 setsid/nohup，即使 wsl.exe 客户端退出，发行版仍保持 Running。
function Start-OceanBase() {
    & wsl.exe -d oceanbase-desktop -u root -- bash -lc `
        'pgrep -f "sleep 100000" >/dev/null || setsid nohup sleep 100000 >/dev/null 2>&1 </dev/null &' | Out-Null
}

# ───────── ① 数据库 2881 ─────────
if (Test-Port 2881) {
    Log '[1/3] 数据库 2881 ........... 已在运行'
} else {
    Log '[1/3] 数据库 2881 ........... 未运行，正在启动 OceanBase'
    if (Get-Command wsl.exe -ErrorAction SilentlyContinue) {
        Start-OceanBase
        Log '      已拉起 WSL 常驻会话，等待数据库端口就绪（最多 45 秒）...'
    } else {
        Log '      本机没有 wsl.exe，请手动启动数据库'
    }
    if (Wait-Port 2881 45) {
        Log '      数据库已就绪'
    } else {
        Log '      端口拒绝连接，疑似 WSL 端口转发失效，重置后重试...'
        Start-Process -FilePath 'wsl.exe' -ArgumentList '--shutdown' -Wait -WindowStyle Hidden
        Start-Sleep -Seconds 3
        Start-OceanBase
        Log '      已重新拉起，再等最多 60 秒...'
        if (Wait-Port 2881 60) {
            Log '      数据库已就绪'
        } else {
            Log '      [!] 数据库仍未就绪。请手动启动 OceanBase 后再运行本脚本'
            Log '      [!] 不影响继续：后端仍会启动，只是登录后没有数据'
        }
    }
}
Log ''

# ───────── ② 后端 8000 ─────────
if (Test-Port 8000) {
    Log '[2/3] 后端 8000 ............. 已在运行'
} else {
    Log '[2/3] 后端 8000 ............. 未运行，正在启动'
    $py = Get-Command python -ErrorAction SilentlyContinue
    if (-not $py) {
        Log '      [!] 找不到 python，请先安装 Python 并加入 PATH'
    } else {
        Start-Process -FilePath 'python' -ArgumentList 'app.py' `
            -WorkingDirectory $backend -WindowStyle Hidden
        if (Wait-Port 8000 20) {
            Log '      后端已就绪'
        } else {
            Log '      [!] 后端启动失败。手动执行：'
            Log ('          cd "' + $backend + '"')
            Log '          python app.py'
        }
    }
}
Log ''

# ───────── ③ 打开登录页 ─────────
if (Test-Port 8000) {
    Log '[3/3] 打开登录页 ............ http://127.0.0.1:8000/login.html'
    Start-Process 'http://127.0.0.1:8000/login.html'
    Log ''
    Log '============================================================'
    Log '   启动完成！浏览器里登录页右侧应显示绿点「连接正常」'
    Log '   本窗口可以关掉，后端已在后台运行'
    Log '============================================================'
} else {
    Log '[3/3] 跳过打开浏览器（后端没起来）'
    Log ''
    Log '============================================================'
    Log '   启动失败，请查看上面的提示'
    Log '   日志文件：启动日志.txt'
    Log '============================================================'
}
