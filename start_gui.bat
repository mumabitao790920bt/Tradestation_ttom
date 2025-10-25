@echo off
echo 启动Tradestation策略GUI界面...
echo.

REM 激活虚拟环境
call conda activate yolov5_menv

REM 启动GUI界面
python GUI_QT.py

pause
