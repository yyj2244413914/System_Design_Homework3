# 智能课堂 · 前后端代码

> 前端：纯 HTML + CSS + JavaScript（无框架、无构建工具）
> 后端：Python FastAPI + PyMySQL
> 数据库：OceanBase `127.0.0.1:2881` / 库 `Intelligent_Classroom`（10 张表）

---

## 一、链路：数据库端口是怎么"连到"前端的

```
┌────────────────────────┐
│  浏览器（前端三件套）    │   login.html / index.html / room.html
│  HTML + CSS + JS       │   js/api.js 里统一用 fetch(..., {credentials:'include'})
└───────────┬────────────┘
            │  HTTP + JSON + Cookie（同源，默认 8000 端口）
            ▼
┌────────────────────────┐
│  后端 FastAPI :8000    │   backend/app.py
│  /api/login            │   ← 校验 user 表密码，下发 Cookie
│  /api/health           │   ← 把数据库连接状态原样返回给前端
│  /api/rooms/{id}/me    │   ← 按"本课角色"算出可用按钮
│  /api/rooms/{id}/action│   ← 校验 + 落库
└───────────┬────────────┘
            │  PyMySQL 直连 TCP
            ▼
┌────────────────────────┐
│  OceanBase :2881       │   backend/db.py + backend/config.py
│  库 Intelligent_Classroom │   ★ 端口 2881 就配在 backend/config.py 里
│  10 张表 / 90 条记录     │
└────────────────────────┘
```

**一句话**：浏览器只认识 `http://127.0.0.1:8000/api/...`，后端在 `config.py` 里拿着 `127.0.0.1:2881` 去连 OceanBase。
前端**不直接连数据库**（浏览器也做不到），它是通过后端这层"翻译"拿到数据的。

打开登录页，右侧"数据库连接状态"面板就是前端调 `GET /api/health` 拿到的真实结果 ——
能看到 `127.0.0.1:2881`、库名、OceanBase 版本号、10 张表、30 个用户、90 条记录。**这就是端口连通的直接证据。**

---

## 二、怎么运行

### 一步

双击 **`启动器\启动智慧课堂.bat`**

它会自动做完三件事，最后把登录页在浏览器里打开：

```
[1/3] 数据库 2881 ........... 已在运行 / 未运行则自动拉起 OceanBase
[2/3] 后端 8000 ............. 已在运行 / 未运行则后台启动 app.py
[3/3] 打开登录页 ............ http://127.0.0.1:8000/login.html
```

窗口**不会一闪而过**，会停住让你看结果；全过程写入 `启动器\startup.log`。

> **页面全关 = 自动停服**：所有页面关闭 30 秒后（前端心跳超时），后端会自动停掉数据库并退出，
> 释放 `2881` / `8000`。重新使用双击 `启动器\启动智慧课堂.bat` 即可。

### 手动方式（想自己控制时）

```bat
cd backend
python app.py
```

然后浏览器打开 `http://127.0.0.1:8000/login.html`。

打开后页面会**自动连接数据库**，右侧面板显示连接状态：

```
状态      ● 连接正常
主机:端口  127.0.0.1:2881
数据库     intelligent_classroom
版本       5.7.25-OceanBase seekdb-v1.2.0.0
表数量     10 张     用户数 30 人     聊天记录 90 条
```

绿点 = 已连通；红点 + "后端未启动" = 后端没起。也可以直接双击 `frontend\login.html`
打开（页面会自动去连 8000 端口），但同样要求后端在跑。

### 数据库

库已经建好（`Intelligent_Classroom`，10 张表 / 30 用户 / 90 条聊天记录）。
换一台机器部署时，先执行 `..\sql\` 下的两个脚本：

```
sql\01_建库建表.sql     -- 建库 + 10 张表
sql\02_初始化数据.sql   -- 灌数据
```

依赖（若提示缺包）：`pip install -r backend\requirements.txt`

---

## 三、演示账号（密码都是 `123456`）

| 账号 | 全局角色 | 课程1 身份 | 课程2 身份 | 课程3 身份 |
|---|---|---|---|---|
| `t01` | 授课教师 | 授课教师 | — | — |
| `t02` | 授课教师 | — | 授课教师 | — |
| `t03` | 授课教师 | — | — | 授课教师 |
| `a01` | 助教 + 学生 | **助教** | — | **学生** |
| `a02`~`a06` | 助教 | 助教 | 助教 | 助教 |
| `s01`~`s21` | 学生 | 学生 | 学生 | 学生 |

★ **用 `a01` 登录**，先点"数据库系统原理"（身份=助教，按钮 5/7/8），再回列表点"操作系统"（身份=学生，按钮 1/3/5/6）——
同一个人、同一个前端页面，按钮完全不同，原因只在 `class_member.role_id`。

---

## 四、接口清单

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/health` | 数据库连通状态（主机、端口、库、版本、表数、数据量） |
| GET | `/api/ping` | 前端心跳（页面每 5 秒一次；30 秒无心跳则自动停库退出） |
| POST | `/api/login` | `{username, password}` → 下发 Cookie |
| POST | `/api/logout` | 退出 |
| GET | `/api/me` | 当前用户 + 全局角色 + 我加入的课堂 |
| GET | `/api/rooms/{course_id}/me` | 本课身份 + **可用功能按钮** + 成员列表 |
| GET | `/api/rooms/{course_id}/messages` | 聊天记录（含作者、角色、menu_id、menu_name） |
| POST | `/api/rooms/{course_id}/action` | `{menu_id, content}` → 校验权限 → 写入聊天记录 |

接口文档（FastAPI 自动生成）：<http://127.0.0.1:8000/api/docs>

---

## 五、权限是前后端怎么配合的（重点）

```
① 前端进聊天室 → GET /api/rooms/1/me
② 后端算：class_member.role_id → role_menu → menu
   返回 {"my_role":"学生","menus":[{menu_id:1,"请假申请"},{3,"查看本人考勤"},{5,"查看作业内容"},{6,"提交作业"}]}
③ 前端按 menus 渲染按钮 → 学生看不到【批改作业】按钮
④ 点按钮 → POST /api/rooms/1/action {menu_id:1, content:"发烧请假"}
⑤ 后端【再校验一次】role_menu 里有没有 (本课role_id, 1)
   ├─ 有 → 写 chat_record + chat_room_record → 200
   └─ 无 → 403 {"msg":"当前角色（学生）没有该功能权限（menu_id=8）"}
```

**前端隐藏按钮只是体验，后端校验才是安全边界。**
实测：学生手工 `POST /api/rooms/1/action {"menu_id":8}` 会拿到 **403**，不会写进数据库。

---

## 六、目录结构

```
前后端代码/
├── 启动器/
│   ├── 启动智慧课堂.bat          ★ 双击启动（检查数据库 → 启动后端 → 开浏览器）
│   ├── start.ps1                启动逻辑（bat 调用；UTF-8 BOM）
│   ├── ensure_db.ps1 / .vbs     数据库守护脚本（备用）
│   └── startup.log              每次启动的日志（可删，已被 gitignore）
├── README.md                    本文件
├── backend/
│   ├── app.py                   FastAPI 入口 + 8 个 API + 静态托管
│   ├── db.py                    PyMySQL 连接层 + health()
│   ├── config.py                ★ 数据库地址/端口 2881 在这里（支持环境变量覆盖）
│   └── requirements.txt
├── frontend/
│   ├── login.html               登录 + 数据库连接状态面板
│   ├── index.html               我的课堂（课程卡片）
│   ├── room.html                聊天室（消息流 + 输入框 + 功能按钮）
│   ├── css/style.css            全部样式
│   └── js/api.js                fetch 统一封装（Cookie / Bearer Token 双认证）
└── docs/
    ├── DFD-顶层图.png / DFD-0层图.png
    ├── DFD-1层图-P2读取权限菜单.png / DFD-1层图-P4执行功能按钮.png
    ├── 数据字典.md
    ├── uml-类图.puml / uml-组件图.puml / uml-时序图.puml
    └── UML类图.png
```

---

## 七、想前后端完全分开部署？

前端单独用 VSCode Live Server 跑在 `5500` 端口时：

1. 后端 `config.py` 的 `ALLOW_ORIGINS` 里已经写了 `http://127.0.0.1:5500`；
2. `app.py` 里已配置 `allow_credentials=True` （否则 Cookie 传不过去）；
3. 前端 `js/api.js` 里把 `fetch(url, ...)` 的 `url` 改成绝对地址
   `http://127.0.0.1:8000 + url`，或直接访问后端的 8000 端口（同源，最省事）。

**注意**：`allow_origins` 不能写 `"*"`，否则浏览器会因为 `credentials` 报 CORS 错误 —— 必须写具体源。
