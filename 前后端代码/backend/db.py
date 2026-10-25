# -*- coding: utf-8 -*-
"""数据库访问层：PyMySQL 直连 OceanBase（127.0.0.1:2881）。"""

import pymysql
from pymysql.cursors import DictCursor

import config

_conn = None


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
    """可复用连接，断线自动重连。"""
    global _conn
    if _conn is None:
        _conn = _connect()
        return _conn
    try:
        _conn.ping(reconnect=True)
    except Exception:
        try:
            _conn.close()
        except Exception:
            pass
        _conn = _connect()
    return _conn


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
    """健康检查：把"到底连没连上数据库、端口是多少"直接返回给前端。"""
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
        info["tables"] = scalar("SELECT COUNT(*) AS c FROM information_schema.tables "
                                "WHERE table_schema=%s", (config.DB["database"],))
        info["users"] = scalar("SELECT COUNT(*) AS c FROM `user`")
        info["records"] = scalar("SELECT COUNT(*) AS c FROM `chat_record`")
        info["ok"] = True
    except Exception as exc:
        info["error"] = "{}: {}".format(type(exc).__name__, exc)
    return info
