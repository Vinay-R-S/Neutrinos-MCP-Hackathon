@echo off
title MCP Backend Server
echo Starting MCP Backend Server...
call .venv\Scripts\activate
python mcp_server/server.py
pause
