@echo off
echo 启动 Tradestation 自动化交易策略系统...
echo.

REM 激活环境
call conda activate yolov5_menv

REM 检查环境
echo 检查环境...
python -c "import streamlit; print('Streamlit 版本:', streamlit.__version__)"

REM 启动 Streamlit
echo.
echo 启动 Web 界面...
echo 请在浏览器中访问: http://localhost:8501
echo.
streamlit run app/ui/main.py --server.port 8501

pause

