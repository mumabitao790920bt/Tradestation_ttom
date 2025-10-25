#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
客户交付文件自动创建脚本
自动复制相关文件并创建加密和非加密版本
"""

import os
import shutil
import base64
import zlib
from pathlib import Path

def create_directories():
    """创建必要的目录结构"""
    print("正在创建目录结构...")
    
    # 创建主交付目录
    delivery_dir = Path("客户交付")
    delivery_dir.mkdir(exist_ok=True)
    
    # 创建加密和非加密子目录
    encrypted_dir = delivery_dir / "加密交付"
    unencrypted_dir = delivery_dir / "非加密交付"
    
    encrypted_dir.mkdir(exist_ok=True)
    unencrypted_dir.mkdir(exist_ok=True)
    
    print(f"✓ 目录创建完成: {delivery_dir}")
    return delivery_dir, encrypted_dir, unencrypted_dir

def copy_files_to_unencrypted(unencrypted_dir):
    """复制文件到非加密目录"""
    print("正在复制文件到非加密目录...")
    
    # 需要复制的主要Python文件
    python_files = [
        "GUI_QT.py",
        "GUI_QT_Interactive.py", 
        "data_processing.py",
        "trend_line_processing.py",
        "huatu_mz.py",
        "interactive_backtest.py",
        "回测示例.py"
    ]
    
    # 复制Python文件
    for file_name in python_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, unencrypted_dir)
            print(f"✓ 复制: {file_name}")
        else:
            print(f"⚠ 文件不存在: {file_name}")
    
    # 复制配置文件
    config_files = ["xlsys.ini"]
    for file_name in config_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, unencrypted_dir)
            print(f"✓ 复制: {file_name}")
    
    # 复制数据库文件
    db_files = [
        "btc_data.db",
        "eth_data.db", 
        "bitcoin_data.db"
    ]
    for file_name in db_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, unencrypted_dir)
            print(f"✓ 复制: {file_name}")
    
    # 复制gupiao_baostock目录中的数据库
    gupiao_dir = Path("gupiao_baostock")
    if gupiao_dir.exists():
        for db_file in gupiao_dir.glob("*.db"):
            shutil.copy2(db_file, unencrypted_dir)
            print(f"✓ 复制: {db_file.name}")
    
    print("✓ 非加密目录文件复制完成")

def encrypt_python_file(file_path, output_dir):
    """加密Python文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 压缩并编码源代码
        compressed = zlib.compress(content.encode('utf-8'))
        encoded = base64.b64encode(compressed).decode('ascii')
        
        # 创建加密后的Python文件
        encrypted_content = f'''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
加密的Python文件 - {os.path.basename(file_path)}
"""

import base64
import zlib
import sys
import types

def decrypt_and_run():
    """解密并执行代码"""
    # 加密的源代码
    encoded_source = """{encoded}"""
    
    try:
        # 解码和解压缩
        compressed = base64.b64decode(encoded_source.encode('ascii'))
        source_code = zlib.decompress(compressed).decode('utf-8')
        
        # 创建模块并执行
        module = types.ModuleType("__main__")
        exec(source_code, module.__dict__)
        
    except Exception as e:
        print(f"执行错误: {{e}}")
        sys.exit(1)

if __name__ == "__main__":
    decrypt_and_run()
'''
        
        # 保存加密文件
        output_file = output_dir / f"encrypted_{os.path.basename(file_path)}"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(encrypted_content)
        
        return True
    except Exception as e:
        print(f"加密失败 {file_path}: {e}")
        return False

def create_encrypted_files(unencrypted_dir, encrypted_dir):
    """创建加密版本的文件"""
    print("正在创建加密版本...")
    
    # 需要加密的Python文件
    python_files = [
        "GUI_QT.py",
        "GUI_QT_Interactive.py",
        "data_processing.py", 
        "trend_line_processing.py",
        "huatu_mz.py",
        "interactive_backtest.py",
        "回测示例.py"
    ]
    
    encrypted_count = 0
    for file_name in python_files:
        file_path = unencrypted_dir / file_name
        if file_path.exists():
            if encrypt_python_file(file_path, encrypted_dir):
                encrypted_count += 1
                print(f"✓ 加密: {file_name}")
            else:
                print(f"✗ 加密失败: {file_name}")
    
    # 复制非Python文件到加密目录（不加密）
    for item in unencrypted_dir.iterdir():
        if item.is_file() and not item.suffix == '.py':
            shutil.copy2(item, encrypted_dir)
            print(f"✓ 复制到加密目录: {item.name}")
    
    print(f"✓ 加密完成，共加密 {encrypted_count} 个Python文件")

def create_requirements_file(delivery_dir):
    """创建requirements.txt文件"""
    print("正在创建依赖文件...")
    
    requirements_content = """# 双均线回测系统依赖包
# 请使用以下命令安装依赖：
# pip install -r requirements.txt

pandas>=1.3.0
numpy>=1.21.0
matplotlib>=3.4.0
plotly>=5.0.0
PyQt5>=5.15.0
sqlite3
datetime
"""
    
    requirements_file = delivery_dir / "requirements.txt"
    with open(requirements_file, 'w', encoding='utf-8') as f:
        f.write(requirements_content)
    
    print("✓ requirements.txt 创建完成")

def create_readme_file(delivery_dir):
    """创建README说明文件"""
    print("正在创建说明文件...")
    
    readme_content = """# 双均线回测系统

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
"""
    
    readme_file = delivery_dir / "README.md"
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("✓ README.md 创建完成")

def main():
    """主函数"""
    print("=" * 50)
    print("双均线回测系统 - 客户交付文件自动创建")
    print("=" * 50)
    
    try:
        # 1. 创建目录结构
        delivery_dir, encrypted_dir, unencrypted_dir = create_directories()
        
        # 2. 复制文件到非加密目录
        copy_files_to_unencrypted(unencrypted_dir)
        
        # 3. 创建加密版本
        create_encrypted_files(unencrypted_dir, encrypted_dir)
        
        # 4. 创建依赖文件
        create_requirements_file(delivery_dir)
        
        # 5. 创建说明文件
        create_readme_file(delivery_dir)
        
        print("\n" + "=" * 50)
        print("✓ 客户交付文件创建完成！")
        print(f"📁 交付目录: {delivery_dir.absolute()}")
        print(f"🔓 非加密版本: {unencrypted_dir.absolute()}")
        print(f"🔒 加密版本: {encrypted_dir.absolute()}")
        print("=" * 50)
        
        # 显示文件统计
        unencrypted_count = len(list(unencrypted_dir.iterdir()))
        encrypted_count = len(list(encrypted_dir.iterdir()))
        print(f"📊 非加密目录文件数: {unencrypted_count}")
        print(f"📊 加密目录文件数: {encrypted_count}")
        
    except Exception as e:
        print(f"❌ 创建过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
