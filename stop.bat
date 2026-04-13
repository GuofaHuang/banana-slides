@echo off
setlocal EnableDelayedExpansion

echo  ========================================
echo   Banana Slides - Stop All Services
echo  ========================================
echo.

set FOUND=0

echo Stopping backend (port 5000) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /T /F >nul 2>&1
    echo   Killed PID %%a and child processes
    set FOUND=1
)
if "!FOUND!"=="0" echo   No service on port 5000

set FOUND=0
echo Stopping frontend (port 3000) ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 " ^| findstr "LISTENING"') do (
    taskkill /PID %%a /T /F >nul 2>&1
    echo   Killed PID %%a and child processes
    set FOUND=1
)
if "!FOUND!"=="0" echo   No service on port 3000

echo.
echo All services stopped.
timeout /t 3
