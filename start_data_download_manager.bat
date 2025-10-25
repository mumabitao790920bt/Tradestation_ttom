@echo off
echo 启动Tradestation数据下载管理器...
echo.

REM 激活conda环境
call conda activate yolov5_menv

REM 检查环境是否激活成功
if errorlevel 1 (
    echo 错误: 无法激活yolov5_menv环境
    pause
    exit /b 1
)

echo 环境激活成功，启动数据下载管理器...
echo.

REM 启动数据下载管理器
python data_download_manager.py

pause
