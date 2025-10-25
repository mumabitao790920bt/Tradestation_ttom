@echo off
echo 启动 Tradestation 桌面版交易测试系统
echo.

REM 激活环境
call conda activate yolov5_menv

REM 检查认证状态
if not exist "tokens.json" (
    echo ❌ 未找到认证令牌文件
    echo 请先运行认证程序: python auth_helper_persistent.py
    echo.
    pause
    exit /b 1
)

echo ✅ 认证令牌文件存在
echo.

REM 检查PyQt5是否安装
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo 📦 正在安装 PyQt5...
    pip install PyQt5
    if errorlevel 1 (
        echo ❌ PyQt5 安装失败
        pause
        exit /b 1
    )
    echo ✅ PyQt5 安装成功
)

echo 🖥️ 启动桌面应用程序...
python trading_desktop_app.py

pause

