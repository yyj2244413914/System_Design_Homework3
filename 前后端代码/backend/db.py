# -*- coding: utf-8 -*-
"""数据库访问层：PyMySQL 直连 OceanBase（127.0.0.1:2881）。

★ 线程安全：FastAPI 的同步接口跑在线程池里，多个请求会并发执行。
  PyMySQL 的连接对象不是线程安全的，所以这里用 threading.local() 给每个线程
  单独一条连接（懒创建、断线自动重连），避免并发时串数据。
"""

import socket
import subprocess
import threading
import time

import pymysql
from pymysql.cursors import DictCursor

import config

_local = threading.local()
_recovery_lock = threading.Lock()
_last_recovery = 0.0


def _port_open(host, port, timeout=2.0):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _start_wsl():
    """在 WSL 发行版内部脱管一个常驻进程，把 oceanbase-desktop 撑住。"""
    try:
        subprocess.run(
            ["wsl.exe", "-d", "oceanbase-desktop", "-u", "root", "--",
             "bash", "-lc",
             'pgrep -f "sleep 100000" >/dev/null || setsid nohup sleep 100000 >/dev/null 2>&1 </dev/null & disown'],
            timeout=10,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except Exception:
        pass


def ensure_oceanbase(wait_seconds=25):
    """发现数据库断联时自动拉起 OceanBase 并等 2881 就绪。

    30 秒内只尝试一次，避免请求风暴反复拉起；分两段：
    ① 直接拉起发行版并等待；② 仍不通则 wsl --shutdown 重置转发后再拉。
    """
    global _last_recovery
    host, port = config.DB["host"], config.DB["port"]
    if _port_open(host, port):
        return True
    with _recovery_lock:
        if time.time() - _last_recovery < 30:
            return False
        _last_recovery = time.time()

        _start_wsl()
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if _port_open(host, port):
                time.sleep(1.0)
                return True
            time.sleep(1.0)

        # 端口转发失效（在监听但拒绝连接）→ 重置 WSL 再拉一次
        try:
            subprocess.run(["wsl.exe", "--shutdown"], timeout=10,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        except Exception:
            pass
        time.sleep(3)
        _start_wsl()
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if _port_open(host, port):
                time.sleep(1.0)
                return True
            time.sleep(1.0)
    return False


def _connect(with_db: bool = True):
    kw = dict(
        host=config.DB["host"],
        port=config.DB["port"],
        user=config.DB["user"],
        password=config.DB["password"],
        charset=config.DB["charset"],
        cursorclass=DictCursor,
        autocommit=True,
        connect_timeout=5,
    )
    if with_db:
        kw["database"] = config.DB["database"]
    return pymysql.connect(**kw)


def _connect_with_recovery():
    try:
        return _connect()
    except pymysql.err.OperationalError:
        ensure_oceanbase()
        return _connect()


def conn():
    """取当前线程的连接（没有就创建；断了就重连；连不上就自动拉起 OceanBase）。"""
    c = getattr(_local, "conn", None)
    if c is None:
        c = _connect_with_recovery()
        _local.conn = c
        return c
    try:
        c.ping(reconnect=True)
        return c
    except Exception:
        try:
            c.close()
        except Exception:
            pass
        c = _connect_with_recovery()
        _local.conn = c
        return c


def query(sql, params=None):
    with conn().cursor() as cur:
        cur.execute(sql, params or ())
        return list(cur.fetchall())


def query_one(sql, params=None):
    rows = query(sql, params)
    return rows[0] if rows else None


def scalar(sql, params=None):
    row = query_one(sql, params)
    return list(row.values())[0] if row else None


def execute(sql, params=None):
    with conn().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid


def health():
    """健康检查：把"连没连上数据库、端口是多少、有多少数据"直接返回给前端。"""
    info = {
        "db_host": config.DB["host"],
        "db_port": config.DB["port"],
        "database": config.DB["database"],
        "user": config.DB["user"],
        "ok": False,
        "error": None,
        "version": None,
        "tables": None,
        "users": None,
        "records": None,
    }
    for attempt in (1, 2):
        try:
            row = query_one("SELECT VERSION() AS v, DATABASE() AS d")
            info["version"] = row["v"]
            info["database"] = row["d"]
            info["tables"] = scalar(
                "SELECT COUNT(*) AS c FROM information_schema.tables WHERE table_schema=%s",
                (config.DB["database"],))
            info["users"] = scalar("SELECT COUNT(*) AS c FROM `user`")
            info["records"] = scalar("SELECT COUNT(*) AS c FROM `chat_record`")
            info["ok"] = True
            break
        except Exception as exc:
            info["error"] = "{}: {}".format(type(exc).__name__, exc)
            if attempt == 1:
                ensure_oceanbase()
    return info
