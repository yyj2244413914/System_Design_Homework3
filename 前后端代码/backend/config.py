# -*- coding: utf-8 -*-
"""后端配置：数据库连接（含端口）与服务器参数。

★ 前端拿不到数据库，是靠后端这一层去连 127.0.0.1:2881 的 OceanBase；
  前端只跟后端的 /api/* 打交道。这就是"数据库端口与前端连接起来"的链路。

★ 账号密码支持用环境变量覆盖（默认值 = 本地演示环境），这样代码可以安全上传到仓库：
     set DB_PASSWORD=你的密码
     set DB_USER=root
"""

import os

# ── 数据库连接（OceanBase / MySQL 通用）──
DB = {
    "host": os.environ.get("DB_HOST", "127.0.0.1"),
    "port": int(os.environ.get("DB_PORT", "2881")),      # ★ OceanBase 端口；MySQL 一般 3306
    "user": os.environ.get("DB_USER", "root@sys"),       # OceanBase 用户名要带租户：root@sys
    "password": os.environ.get("DB_PASSWORD", ""),
    "charset": "utf8mb4",
    "database": os.environ.get("DB_NAME", "Intelligent_Classroom"),
}

# ── 后端服务 ──
SERVER_HOST = os.environ.get("SERVER_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8000"))

# ── 会话 ──
SESSION_COOKIE = "sid"
SESSION_TTL_MINUTES = 120

# ── 跨域（前端单独部署、不同端口时才需要）──
ALLOW_ORIGINS = [
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]
