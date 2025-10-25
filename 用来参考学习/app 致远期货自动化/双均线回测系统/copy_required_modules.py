#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精确复制程序运行所需的模块文件
只复制真正需要的文件，避免浪费空间
"""

import os
import shutil
from pathlib import Path

def copy_required_modules():
    """复制程序运行所需的模块文件"""
    print("正在复制程序运行所需的模块文件...")
    
    # 源目录和目标目录
    source_dir = Path("下载股票历史数据")
    target_dir = Path("客户交付/非加密交付/下载股票历史数据")
    
    # 创建目标目录
    target_dir.mkdir(exist_ok=True)
    
    # 根据代码分析，程序实际需要的文件列表
    required_files = [
        # 核心下载模块
        "downloader_bridge.py",           # GUI_QT.py 引用
        "crypto_downloader.py",           # GUI_QT.py 引用
        "bitcoin_downloader.py",          # GUI_QT.py 引用
        "baostock_data_collector_final.py", # downloader_bridge.py 引用
        
        # 必要的依赖文件（如果存在）
        "requirements.txt",               # 依赖说明
        "README.md",                      # 使用说明
    ]
    
    # 复制必需文件
    copied_count = 0
    for file_name in required_files:
        source_file = source_dir / file_name
        target_file = target_dir / file_name
        
        if source_file.exists():
            shutil.copy2(source_file, target_file)
            print(f"✓ 复制: {file_name}")
            copied_count += 1
        else:
            print(f"⚠ 文件不存在: {file_name}")
    
    # 检查是否有其他隐藏依赖
    print(f"\n✓ 模块文件复制完成，共复制 {copied_count} 个文件")
    
    # 验证复制结果
    print(f"\n目标目录内容:")
    for item in target_dir.iterdir():
        if item.is_file():
            size = item.stat().st_size
            print(f"  {item.name} ({size} bytes)")
    
    return True

def create_init_file():
    """创建__init__.py文件，使目录成为Python包"""
    target_dir = Path("客户交付/非加密交付/下载股票历史数据")
    init_file = target_dir / "__init__.py"
    
    init_content = '''# -*- coding: utf-8 -*-
"""
下载股票历史数据模块
包含股票和加密货币数据下载功能
"""

# 导出主要函数
from .downloader_bridge import download_daily_to_sqlite
from .crypto_downloader import download_and_save_crypto_data
from .bitcoin_downloader import download_bitcoin_data

__all__ = [
    'download_daily_to_sqlite',
    'download_and_save_crypto_data', 
    'download_bitcoin_data'
]
'''
    
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)
    
    print("✓ 创建 __init__.py 文件")

def main():
    """主函数"""
    print("=" * 50)
    print("精确复制程序运行所需的模块文件")
    print("=" * 50)
    
    try:
        # 复制必需文件
        if copy_required_modules():
            # 创建__init__.py文件
            create_init_file()
            
            print("\n" + "=" * 50)
            print("✓ 模块文件复制完成！")
            print("=" * 50)
            
            # 显示文件大小统计
            target_dir = Path("客户交付/非加密交付/下载股票历史数据")
            total_size = sum(f.stat().st_size for f in target_dir.iterdir() if f.is_file())
            print(f"📊 模块目录总大小: {total_size / 1024:.1f} KB")
            
        else:
            print("\n❌ 复制失败")
            
    except Exception as e:
        print(f"❌ 复制过程中出现错误: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main()
