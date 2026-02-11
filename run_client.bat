@echo off
title MCP Client UI
echo Starting MCP Client UI...
echo Opening in browser...
start http://127.0.0.1:8001
call .venv\Scripts\activate
python -m uvicorn mcp_client.app:app --host 0.0.0.0 --port 8001 --reload
pause
