@echo off
chcp 65001
setlocal EnableDelayedExpansion

title Banana Slides - 一键启动

echo.
echo ╔══════════════════════════════════════╗
echo ║   Banana Slides Windows 一键启动    ║
echo ╚══════════════════════════════════════╝
echo.

REM ── 切换到脚本所在目录 ──
cd /d "%~dp0"

REM ══════════════════════════════════════
REM  第1步：检查 Python
REM ══════════════════════════════════════
echo [1/5] 检查 Python ...
where python >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Python，请安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    goto :error_exit
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PY_VER=%%v
echo       已找到: !PY_VER!

REM ══════════════════════════════════════
REM  第2步：检查 Node.js
REM ══════════════════════════════════════
echo [2/5] 检查 Node.js ...
where node >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Node.js，请安装 Node.js 18+
    echo 下载地址: https://nodejs.org/
    goto :error_exit
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do set NODE_VER=%%v
echo       已找到: !NODE_VER!

REM ══════════════════════════════════════
REM  第3步：安装/检查 uv
REM ══════════════════════════════════════
echo [3/5] 检查 uv (Python 包管理器) ...
where uv >nul 2>&1
if errorlevel 1 (
    echo       未检测到 uv，正在自动安装...
    pip install uv -i https://mirrors.cloud.tencent.com/pypi/simple/ 2>nul
    if errorlevel 1 (
        pip install uv
    )
    where uv >nul 2>&1
    if errorlevel 1 (
        echo [错误] uv 安装失败，请手动安装: pip install uv
        goto :error_exit
    )
)
for /f "tokens=*" %%v in ('uv --version 2^>^&1') do set UV_VER=%%v
echo       已找到: !UV_VER!

REM ══════════════════════════════════════
REM  第4步：检查 .env 配置文件
REM ══════════════════════════════════════
echo [4/5] 检查环境配置 ...
if not exist ".env" (
    echo       .env 不存在，从模板创建...
    copy ".env.example" ".env" >nul
    echo.
    echo ══════════════════════════════════════════════════════
    echo   [.env 已创建] 请先编辑 .env 文件配置你的 API Key！
    echo.
    echo   必填项:
    echo     AI_PROVIDER_FORMAT=gemini     (或 openai / anthropic)
    echo     GOOGLE_API_KEY=你的API密钥     (或 OPENAI_API_KEY)
    echo ══════════════════════════════════════════════════════
    echo.
    notepad ".env"
    echo 配置完成后请重新运行此脚本
    goto :error_exit
)

REM 检查 .env 中是否还是默认占位符（仅警告，不阻止启动）
findstr /C:"your-api-key-here" ".env" >nul 2>&1
if not errorlevel 1 (
    echo.
    echo [警告] .env 中的 API Key 仍为默认占位符
    echo        如果 AI 功能无法使用，请编辑 .env 文件配置正确的 API Key
    echo.
)
echo       .env 配置文件已就绪

REM ══════════════════════════════════════
REM  第5步：安装依赖 & 启动服务
REM ══════════════════════════════════════
echo [5/5] 安装依赖并启动服务 ...

REM ── 安装 Python 后端依赖 ──
echo.
echo   ── 后端依赖 ──
if not exist ".venv\Scripts\python.exe" (
    echo       首次运行，安装 Python 依赖 (可能需要几分钟)...
    uv sync
    if errorlevel 1 (
        echo [错误] Python 依赖安装失败，请检查网络连接
        goto :error_exit
    )
) else (
    echo       Python 依赖已安装
)

REM ── 安装 Node.js 前端依赖 ──
echo   ── 前端依赖 ──
if not exist "frontend\node_modules" (
    echo       首次运行，安装前端依赖 (可能需要几分钟)...
    pushd frontend
    call npm install
    popd
    if errorlevel 1 (
        echo [错误] 前端依赖安装失败，请检查网络连接
        goto :error_exit
    )
) else (
    echo       前端依赖已安装
)

REM ── 创建必要目录 ──
if not exist "backend\instance" mkdir "backend\instance"
if not exist "uploads" mkdir "uploads"

echo.
echo ══════════════════════════════════════════════════════
echo   所有准备就绪，正在启动服务...
echo ══════════════════════════════════════════════════════
echo.

REM ── 启动后端 (隐藏窗口) ──
echo   启动后端服务 (端口 5000，后台运行) ...
powershell -Command "Start-Process cmd -ArgumentList '/c','cd /d \"%~dp0\" && uv run --directory backend alembic upgrade head && uv run --directory backend python app.py' -WindowStyle Hidden"

REM 等待后端就绪
echo   等待后端启动 ...
timeout /t 5 /nobreak >nul

REM ── 启动前端 (隐藏窗口) ──
echo   启动前端服务 (端口 3000，后台运行) ...
powershell -Command "Start-Process cmd -ArgumentList '/c','cd /d \"%~dp0\frontend\" && npm run dev' -WindowStyle Hidden"

echo.
echo ╔══════════════════════════════════════╗
echo ║          启动完成！                  ║
echo ╠══════════════════════════════════════╣
echo ║  前端地址: http://localhost:3000     ║
echo ║  后端地址: http://localhost:5000     ║
echo ╠══════════════════════════════════════╣
echo ║  关闭此窗口不影响已启动的服务        ║
echo ║  双击 stop.bat 可停止所有服务        ║
echo ╚══════════════════════════════════════╝
echo.

REM 尝试自动打开浏览器
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo 按任意键关闭此窗口 (服务将继续运行) ...
pause >nul
goto :eof

:error_exit
echo.
echo 按任意键退出 ...
pause >nul
exit /b 1
