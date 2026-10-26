# -*- coding: utf-8 -*-
"""智能课堂 · 后端 API（FastAPI）

链路：浏览器(HTML+CSS+JS) --fetch--> 本服务 /api/* --PyMySQL--> OceanBase 127.0.0.1:2881

启动：python app.py          （或 uvicorn app:app --host 127.0.0.1 --port 8000）
打开：http://127.0.0.1:8000
"""

import os
import secrets
import time

from fastapi import Body, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import pymysql

import config
import db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

app = FastAPI(title="智能课堂 · 前后端分离示例", docs_url="/api/docs", redoc_url=None)

# 前端可能来自：后端托管（同源）、VSCode Live Server（5500）、或直接双击 file://
# 用 Bearer Token 认证，因此这里可以放开为 "*"（不依赖 Cookie 跨域）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 会话：演示用内存字典（重启后需重新登录）──
SESSIONS = {}


def _purge_expired():
    """顺手清掉过期会话，避免 SESSIONS 无限增长。"""
    now = time.time()
    for key in [k for k, v in SESSIONS.items() if v["expire_at"] < now]:
        SESSIONS.pop(key, None)


def new_session(user):
    _purge_expired()
    token = secrets.token_hex(16)
    SESSIONS[token] = {"user_id": user["user_id"],
                       "username": user["username"],
                       "expire_at": time.time() + config.SESSION_TTL_MINUTES * 60}
    return token


def _token_of(request: Request):
    """优先取 Authorization: Bearer，其次取 Cookie —— 两种打开方式都支持。"""
    auth = request.headers.get("authorization") or ""
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        if token:
            return token
    return request.cookies.get(config.SESSION_COOKIE)


def current_user(request: Request):
    token = _token_of(request)
    sess = SESSIONS.get(token)
    if not sess:
        return None
    if sess["expire_at"] < time.time():
        SESSIONS.pop(token, None)
        return None
    row = db.query_one(
        "SELECT user_id, username, major, grade FROM `user` WHERE user_id=%s",
        (sess["user_id"],))
    if not row:
        SESSIONS.pop(token, None)
        return None
    return row


# ───────────────────────── 登录 ─────────────────────────


class LoginIn(BaseModel):
    username: str
    password: str


@app.post("/api/login")
def login(payload: LoginIn, response: Response):
    row = db.query_one(
        "SELECT user_id, username, password, major, grade FROM `user` WHERE username=%s",
        (payload.username.strip(),))
    if not row or row["password"] != payload.password:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = new_session(row)
    response.set_cookie(config.SESSION_COOKIE, token, httponly=True,
                        samesite="lax", max_age=config.SESSION_TTL_MINUTES * 60)
    row.pop("password", None)
    # 同时把 token 返回给前端：双击 HTML（file://）时靠它做认证
    return {"code": 0, "data": {"user": row, "token": token}, "msg": "登录成功"}


@app.post("/api/logout")
def logout(request: Request, response: Response):
    token = _token_of(request)
    SESSIONS.pop(token, None)
    response.delete_cookie(config.SESSION_COOKIE)
    return {"code": 0, "data": None, "msg": "已退出"}


# ───────────────────────── 数据库连通性（前端登录页会调用）─────────────────────────


@app.get("/api/health")
def health():
    info = db.health()
    return {"code": 0 if info["ok"] else 1, "data": info,
            "msg": "数据库连接正常" if info["ok"] else info["error"]}


# ───────────────────────── 当前用户 + 我的课堂 ─────────────────────────


@app.get("/api/me")
def me(request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    courses = db.query(
        "SELECT c.course_id, c.course_name, c.class_time, c.classroom, c.hours, c.credits, "
        "       r.role_id AS my_role_id, r.role_name AS my_role, cm.member_id "
        "FROM `class_member` cm "
        "JOIN `course` c ON c.course_id = cm.course_id "
        "JOIN `role` r ON r.role_id = cm.role_id "
        "WHERE cm.user_id=%s ORDER BY c.course_id", (user["user_id"],))
    roles = db.query(
        "SELECT r.role_id, r.role_name FROM `user_role` ur "
        "JOIN `role` r ON r.role_id = ur.role_id WHERE ur.user_id=%s ORDER BY r.role_id",
        (user["user_id"],))
    return {"code": 0, "data": {"user": user, "roles": roles, "courses": courses}, "msg": "ok"}


# ───────────────────────── 聊天室：本课身份 + 可用按钮 ─────────────────────────


def _member(course_id: int, user_id: int):
    return db.query_one(
        "SELECT cm.member_id, cm.role_id, r.role_name, c.course_name, c.class_time, "
        "       c.classroom, c.hours, c.credits, cr.room_id "
        "FROM `class_member` cm "
        "JOIN `role` r ON r.role_id = cm.role_id "
        "JOIN `course` c ON c.course_id = cm.course_id "
        "LEFT JOIN `chat_room` cr ON cr.course_id = cm.course_id "
        "WHERE cm.course_id=%s AND cm.user_id=%s", (course_id, user_id))


@app.get("/api/rooms/{course_id}/me")
def room_me(course_id: int, request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    member = _member(course_id, user["user_id"])
    if not member:
        raise HTTPException(status_code=403, detail="你不是这门课的成员，无法进入该聊天室")

    # ★ 权限来源：class_member.role_id → role_menu → menu
    menus = db.query(
        "SELECT m.menu_id, m.menu_name, m.menu_url FROM `role_menu` rm "
        "JOIN `menu` m ON m.menu_id = rm.menu_id "
        "WHERE rm.role_id=%s ORDER BY m.menu_id", (member["role_id"],))
    members = db.query(
        "SELECT u.username, r.role_name FROM `class_member` cm "
        "JOIN `user` u ON u.user_id = cm.user_id "
        "JOIN `role` r ON r.role_id = cm.role_id "
        "WHERE cm.course_id=%s ORDER BY cm.role_id, u.user_id", (course_id,))
    return {"code": 0, "msg": "ok",
            "data": {"course": {"course_id": course_id,
                                "course_name": member["course_name"],
                                "class_time": member["class_time"],
                                "classroom": member["classroom"],
                                "hours": member["hours"],
                                "credits": float(member["credits"])},
                     "room_id": member["room_id"],
                     "member_id": member["member_id"],
                     "my_role_id": member["role_id"],
                     "my_role": member["role_name"],
                     "menus": menus,
                     "members": members}}


@app.get("/api/rooms/{course_id}/messages")
def room_messages(course_id: int, request: Request):
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    member = _member(course_id, user["user_id"])
    if not member:
        raise HTTPException(status_code=403, detail="你不是这门课的成员")

    rows = db.query(
        "SELECT cr.record_id, cr.menu_id, cr.content, u.username, r.role_name, "
        "       m.menu_name "
        "FROM `chat_record` cr "
        "JOIN `chat_room_record` rr ON rr.record_id = cr.record_id "
        "JOIN `class_member` cm ON cm.member_id = cr.member_id "
        "JOIN `user` u ON u.user_id = cm.user_id "
        "JOIN `role` r ON r.role_id = cm.role_id "
        "LEFT JOIN `menu` m ON m.menu_id = cr.menu_id "
        "WHERE rr.room_id=%s ORDER BY cr.record_id", (member["room_id"],))
    return {"code": 0, "data": rows, "msg": "ok"}


class ActionIn(BaseModel):
    menu_id: int
    content: str = ""


@app.post("/api/rooms/{course_id}/action")
def room_action(course_id: int, payload: ActionIn, request: Request):
    """功能按钮统一入口：点哪个按钮就提交哪个 menu_id。

    后端必须再校验一次"这个角色的 role_menu 里到底有没有这个 menu_id" ——
    前端隐藏按钮只是体验，这里才是安全边界。
    """
    user = current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="未登录")
    member = _member(course_id, user["user_id"])
    if not member:
        raise HTTPException(status_code=403, detail="你不是这门课的成员")

    allowed = db.query_one(
        "SELECT m.menu_name FROM `role_menu` rm JOIN `menu` m ON m.menu_id = rm.menu_id "
        "WHERE rm.role_id=%s AND rm.menu_id=%s",
        (member["role_id"], payload.menu_id))
    if not allowed:
        raise HTTPException(
            status_code=403,
            detail="当前角色（{}）没有该功能权限（menu_id={}）".format(
                member["role_name"], payload.menu_id))

    text = (payload.content or "").strip()
    if text and not text.startswith("【"):
        text = "【{}】{}".format(allowed["menu_name"], text)
    elif not text:
        text = "【{}】已执行".format(allowed["menu_name"])

    record_id = db.execute(
        "INSERT INTO `chat_record`(member_id, menu_id, content) VALUES (%s,%s,%s)",
        (member["member_id"], payload.menu_id, text[:2000]))
    db.execute(
        "INSERT INTO `chat_room_record`(room_id, record_id) VALUES (%s,%s)",
        (member["room_id"], record_id))

    return {"code": 0, "msg": "已记录到聊天室",
            "data": {"record_id": record_id, "menu_id": payload.menu_id,
                     "menu_name": allowed["menu_name"], "content": text}}


# ───────────────────────── 统一错误格式 ─────────────────────────


@app.exception_handler(HTTPException)
async def http_error(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code,
                        content={"code": exc.status_code, "data": None,
                                 "msg": exc.detail})


@app.exception_handler(pymysql.err.MySQLError)
async def database_error(request: Request, exc):
    """数据库连不上时给友好提示（而不是 500 Internal Server Error）。

    常见场景：OceanBase 没启动。前端据此提示用户去双击 启动智慧课堂.bat。
    """
    msg = "数据库未连接，请先启动 OceanBase(2881) 后重试"
    if isinstance(exc, pymysql.err.OperationalError):
        msg = "数据库未连接（127.0.0.1:{}），请先启动 OceanBase 后重试".format(
            config.DB["port"])
    return JSONResponse(status_code=503,
                        content={"code": 503, "data": None, "msg": msg})


# ───────────────────────── 静态前端（必须放在最后）─────────────────────────

@app.get("/")
def root():
    return RedirectResponse("/login.html")


app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("=" * 66)
    print(" 智能课堂 · 后端启动")
    print(" 数据库 : {}:{} / {} / {}".format(
        config.DB["host"], config.DB["port"], config.DB["database"], config.DB["user"]))
    print(" 前端   : http://{}:{}/login.html".format(config.SERVER_HOST, config.SERVER_PORT))
    print(" 接口文档: http://{}:{}/api/docs".format(config.SERVER_HOST, config.SERVER_PORT))
    print("=" * 66)
    uvicorn.run(app, host=config.SERVER_HOST, port=config.SERVER_PORT, log_level="info")
