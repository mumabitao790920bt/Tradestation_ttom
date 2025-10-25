# 双均线回测系统

## 系统说明
这是一个基于双均线策略的量化交易回测系统，支持股票和数字货币的历史数据回测。

## 文件说明

### 主要程序文件
- `GUI_QT.py` - 主程序界面（非加密版本）
- `GUI_QT_Interactive.py` - 交互式回测界面（非加密版本）
- `encrypted_GUI_QT.py` - 加密版本主程序
- `encrypted_GUI_QT_Interactive.py` - 加密版本交互式界面

### 数据文件
- `*.db` - SQLite数据库文件，包含历史价格数据
- `xlsys.ini` - 系统配置文件

## 安装和运行

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行程序
#### 非加密版本（可查看源代码）
```bash
python GUI_QT.py
# 或
python GUI_QT_Interactive.py
```

#### 加密版本（源代码已加密）
```bash
python encrypted_GUI_QT.py
# 或
python encrypted_GUI_QT_Interactive.py
```

## 功能特性
- 支持股票和数字货币数据
- 双均线策略回测
- 交互式图表显示
- 历史数据管理
- 回测结果分析

## 注意事项
- 首次运行可能需要下载数据
- 确保有足够的磁盘空间存储数据
- 建议在Python 3.7+环境下运行

## 技术支持
如有问题请联系技术支持团队。
