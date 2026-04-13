@echo off
echo ====================================
echo   Banana Slides Frontend
echo ====================================
echo.

echo [1/3] Checking dependencies...
if not exist "node_modules\" (
    echo Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo npm install failed. Please run manually: npm install
        pause
        exit /b 1
    )
) else (
    echo Dependencies OK
)

echo.
echo [2/3] Checking environment...
echo.
echo [3/3] Starting dev server...
echo Frontend: http://localhost:3000
echo Make sure backend is running at http://localhost:5000
echo.
echo Press Ctrl+C to stop
echo.

call npm run dev

pause
