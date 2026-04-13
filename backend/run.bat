@echo off
REM Banana Slides Backend Startup Script for Windows (uv-based)

echo ====================================
echo   Banana Slides API Server
echo ====================================
echo.

REM Check if .env exists
if not exist .env (
    echo .env file not found. Creating from .env.example...
    copy .env.example .env
    echo .env file created. Please edit it with your API keys.
    echo.
)

REM Create instance folder if not exists
if not exist instance mkdir instance
if not exist ..\uploads mkdir ..\uploads

echo Starting server...
echo.

REM Run the application with uv
uv run alembic upgrade head && uv run python app.py
