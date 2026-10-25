# -*- coding: utf-8 -*-
"""数据库访问层：PyMySQL 直连 OceanBase（127.0.0.1:2881）。

★ 线程安全：FastAPI 的同步接口跑在线程池里，多个请求会并发执行。
  PyMySQL 的连接对象不是线程安全的，所以这里用 threading.local() 给每个线程
  单独一条连接（懒创建、断线自动重连），避免并发时串数据。
"""

import threading

import pymysql
from pymysql.cursors import DictCursor

import config

_local = threading.local()


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


def conn():
    """取当前线程的连接（没有就创建；断了就重连）。"""
    c = getattr(_local, "conn", None)
    if c is None:
        c = _connect()
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
        c = _connect()
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
    except Exception as exc:
        info["error"] = "{}: {}".format(type(exc).__name__, exc)
    return info
