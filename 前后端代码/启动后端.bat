@echo off
chcp 65001 >nul
title 智能课堂 · 后端服务
cd /d "%~dp0backend"

echo ============================================================
echo  智能课堂 · 后端服务启动中
echo  数据库: 127.0.0.1:2881 / Intelligent_Classroom / root@sys
echo  前端  : http://127.0.0.1:8000/login.html
echo  接口文档: http://127.0.0.1:8000/api/docs
echo ============================================================
echo.

python app.py

echo.
echo 服务已停止，按任意键关闭窗口。
pause >nul
