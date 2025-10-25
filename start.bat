@echo off
echo 🚀 Tradestation 自动化交易策略系统
echo ================================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python环境
    echo 请确保已激活 yolov5_menv 环境
    pause
    exit /b 1
)

echo ✅ Python环境检查通过
echo.

REM 显示菜单
echo 请选择操作:
echo 1. 系统测试
echo 2. 初始化数据库
echo 3. 启动Web界面
echo 4. OAuth认证
echo 5. 退出
echo.

set /p choice="请输入选择 (1-5): "

if "%choice%"=="1" (
    echo.
    echo 🔍 运行系统测试...
    python test_system.py
    pause
) else if "%choice%"=="2" (
    echo.
    echo 🗄️ 初始化数据库...
    python main.py init
    pause
) else if "%choice%"=="3" (
    echo.
    echo 🌐 启动Web界面...
    echo 请在浏览器中打开: http://localhost:8501
    echo 按 Ctrl+C 停止服务
    echo.
    streamlit run app/ui/main.py --server.port 8501 --server.address localhost
) else if "%choice%"=="4" (
    echo.
    echo 🔐 启动OAuth认证...
    python auth_helper.py
    pause
) else if "%choice%"=="5" (
    echo 👋 再见!
    exit /b 0
) else (
    echo ❌ 无效选择
    pause
)

goto :eof