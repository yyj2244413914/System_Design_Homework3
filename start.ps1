# 智能课堂 · 一键启动
# 用法：双击「一键启动.bat」（可发送到桌面做快捷方式）
# 做的事：① 检查数据库 2881（没起就尝试启动 OceanBase）
#          ② 检查后端 8000（没起就启动）  ③ 等端口就绪  ④ 打开浏览器

$ErrorActionPreference = 'SilentlyContinue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

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

Write-Host '============================================================'
Write-Host ' 智能课堂 · 一键启动'
Write-Host '============================================================'
Write-Host ''

# 数据库 2881
if (Test-Port 2881) {
    Write-Host '[1/3] 数据库 2881 已经在运行'
} else {
    Write-Host '[1/3] 数据库 2881 未启动，尝试拉起 OceanBase ...'
    Start-Process -FilePath 'wsl.exe' -ArgumentList '-d', 'oceanbase-desktop'
    Write-Host '      已弹出 WSL 窗口，等待数据库就绪（最多 40 秒）...'
    if (Wait-Port 2881 40) {
        Write-Host '      数据库已就绪'
    } else {
        Write-Host '      [!] 数据库未能自动启动，请手动执行： wsl -d oceanbase-desktop'
    }
}

# 后端 8000
if (Test-Port 8000) {
    Write-Host '[2/3] 后端 8000 已经在运行'
} else {
    Write-Host '[2/3] 启动后端服务 ...'
    Start-Process -FilePath 'python' -ArgumentList 'app.py' -WorkingDirectory (Join-Path $root 'backend') -WindowStyle Hidden
    if (Wait-Port 8000 20) {
        Write-Host '      后端已就绪'
    } else {
        Write-Host '      [!] 后端启动失败，请手动执行：'
        Write-Host ('          cd "' + (Join-Path $root 'backend') + '" ; python app.py')
    }
}

# 打开浏览器
Write-Host '[3/3] 打开登录页 ...'
Start-Process 'http://127.0.0.1:8000/login.html'

Write-Host ''
Write-Host '============================================================'
Write-Host ' 完成。登录页右侧会显示数据库连接状态（绿点 = 已连通）'
Write-Host ' 本窗口可关闭，后端已在后台运行'
Write-Host '============================================================'
Start-Sleep -Seconds 4
