@echo off
setlocal EnableDelayedExpansion

title Banana Slides - Quick Start

echo.
echo  ========================================
echo   Banana Slides Windows Quick Start
echo  ========================================
echo.

cd /d "%~dp0"

REM ===== Step 1: Check Python =====
echo [1/5] Checking Python ...
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    echo         Download: https://www.python.org/downloads/
    echo         Make sure to check "Add Python to PATH" during installation
    goto :error_exit
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo       Found: !PY_VER!

REM ===== Step 2: Check Node.js =====
echo [2/5] Checking Node.js ...
where node >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 18+
    echo         Download: https://nodejs.org/
    goto :error_exit
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo       Found: !NODE_VER!

REM ===== Step 3: Check/Install uv =====
echo [3/5] Checking uv ...
where uv >nul 2>&1
if errorlevel 1 (
    echo       uv not found, installing automatically...
    pip install uv -i https://mirrors.cloud.tencent.com/pypi/simple/ 2>nul
    if errorlevel 1 (
        pip install uv
    )
    where uv >nul 2>&1
    if errorlevel 1 (
        echo [ERROR] uv install failed. Please run manually: pip install uv
        goto :error_exit
    )
)
for /f "tokens=*" %%v in ('uv --version 2^>^&1') do set UV_VER=%%v
echo       Found: !UV_VER!

REM ===== Step 4: Check .env =====
echo [4/5] Checking .env config ...
if not exist ".env" (
    echo       .env not found, creating from template...
    copy ".env.example" ".env" >nul
    echo.
    echo  ========================================================
    echo   [.env created] Please edit it to set your API Key!
    echo.
    echo   Required:
    echo     AI_PROVIDER_FORMAT=gemini   (or openai / anthropic)
    echo     GOOGLE_API_KEY=your-key     (or OPENAI_API_KEY)
    echo  ========================================================
    echo.
    notepad ".env"
    echo Please re-run this script after configuring .env
    goto :error_exit
)

findstr /C:"your-api-key-here" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [WARN] .env still contains default API key placeholders
    echo        If AI features don't work, please edit .env with real keys
    echo.
)
echo       .env config ready

REM ===== Step 5: Install deps and start =====
echo [5/5] Installing dependencies and starting ...

echo.
echo   -- Backend deps --
if not exist ".venv\Scripts\python.exe" (
    echo       First run - installing Python deps (may take a few minutes)...
    uv sync
    if errorlevel 1 (
        echo [ERROR] Python dependency install failed. Check your network.
        goto :error_exit
    )
) else (
    echo       Python deps already installed
)

echo   -- Frontend deps --
if not exist "frontend\node_modules" (
    echo       First run - installing frontend deps (may take a few minutes)...
    pushd frontend
    call npm install
    popd
    if errorlevel 1 (
        echo [ERROR] Frontend dependency install failed. Check your network.
        goto :error_exit
    )
) else (
    echo       Frontend deps already installed
)

if not exist "backend\instance" mkdir "backend\instance"
if not exist "uploads" mkdir "uploads"

echo.
echo  ========================================================
echo   All ready. Starting services...
echo  ========================================================
echo.

REM -- Start backend (hidden window) --
echo   Starting backend on port 5000 (hidden) ...
powershell -Command "Start-Process cmd -ArgumentList '/c','cd /d \"%~dp0\" && uv run --directory backend alembic upgrade head && uv run --directory backend python app.py' -WindowStyle Hidden"

echo   Waiting for backend to start ...
timeout /t 5 /nobreak >nul

REM -- Start frontend (hidden window) --
echo   Starting frontend on port 3000 (hidden) ...
powershell -Command "Start-Process cmd -ArgumentList '/c','cd /d \"%~dp0\frontend\" && npm run dev' -WindowStyle Hidden"

echo.
echo  ========================================
echo          Started successfully!
echo  ========================================
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:5000
echo  ----------------------------------------
echo   Close this window won't stop services
echo   Run stop.bat to stop all services
echo  ========================================
echo.

REM Auto-open browser
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo Press any key to close this window (services keep running) ...
pause >nul
goto :eof

:error_exit
echo.
echo Press any key to exit ...
pause >nul
exit /b 1
