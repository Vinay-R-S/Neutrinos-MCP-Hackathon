@echo off
echo ===================================================
echo Intelligent Intake and Triage System - Windows Setup
echo ===================================================

echo.
echo 1. Creating virtual environment...
if not exist .venv (
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.
echo 2. Installing dependencies...
call .venv\Scripts\activate
pip install --upgrade pip
echo Installing Backend requirements...
pip install -r mcp_server/requirements.txt
echo Installing Client requirements...
pip install -r mcp_client/requirements.txt

echo.
echo 3. Setting up environment variables...
if not exist .env (
    if exist mcp_server\.env.example (
        copy mcp_server\.env.example .env
        echo Created .env from example. 
        echo PLEASE EDIT .env WITH YOUR API KEYS!
    ) else (
        echo Warning: mcp_server\.env.example not found.
    )
) else (
    echo .env already exists.
)

echo.
echo ===================================================
echo Setup Complete!
echo.
echo To run the backend: run_backend.bat
echo To run the client: run_client.bat
echo ===================================================
pause
