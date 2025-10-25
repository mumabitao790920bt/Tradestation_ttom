#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径修复模块 - 解决交付后路径变化问题
自动检测当前运行目录并找到正确的数据库文件路径
"""

import os
import sys
from pathlib import Path

def get_project_root():
    """获取项目根目录（当前脚本所在目录）"""
    # 获取当前脚本的绝对路径
    if getattr(sys, 'frozen', False):
        # 如果是打包后的exe
        return Path(sys.executable).parent
    else:
        # 如果是Python脚本
        return Path(__file__).parent

def find_database_file(db_name, search_paths=None):
    """
    智能查找数据库文件
    
    Args:
        db_name: 数据库文件名，如 'btc_data.db'
        search_paths: 额外的搜索路径列表
    
    Returns:
        找到的数据库文件完整路径，如果没找到返回None
    """
    project_root = get_project_root()
    
    # 默认搜索路径
    default_search_paths = [
        project_root,  # 当前目录
        project_root / "gupiao_baostock",  # 子目录
        project_root.parent,  # 上级目录
        project_root.parent / "gupiao_baostock",  # 上级目录的子目录
    ]
    
    # 合并自定义搜索路径
    if search_paths:
        default_search_paths.extend([Path(p) for p in search_paths])
    
    # 搜索数据库文件
    for search_path in default_search_paths:
        if not search_path.exists():
            continue
            
        db_path = search_path / db_name
        if db_path.exists():
            return str(db_path)
    
    return None

def get_database_path(code, db_mode='auto'):
    """
    根据代码和模式获取数据库路径
    
    Args:
        code: 股票代码或加密货币代码
        db_mode: 数据库模式 ('crypto', 'baostock', 'legacy', 'auto')
    
    Returns:
        (db_path, table_name) 元组
    """
    if db_mode == 'auto':
        # 自动检测模式
        if code in ['BTC', 'btc']:
            db_mode = 'crypto'
        elif code in ['ETH', 'eth']:
            db_mode = 'crypto'
        elif code.startswith(('sh.', 'sz.')):
            db_mode = 'baostock'
        else:
            db_mode = 'legacy'
    
    if db_mode == 'crypto':
        if code.upper() in ['BTC', 'btc']:
            db_name = 'btc_data.db'
            table_name = 'btc_daily'
        elif code.upper() in ['ETH', 'eth']:
            db_name = 'eth_data.db'
            table_name = 'eth_daily'
        else:
            raise ValueError(f'不支持的加密货币代码: {code}')
        
        db_path = find_database_file(db_name)
        if not db_path:
            raise FileNotFoundError(f'未找到数据库文件: {db_name}')
        
        return db_path, table_name
        
    elif db_mode == 'baostock':
        db_name = f'{code}_data.db'
        db_path = find_database_file(db_name)
        if not db_path:
            raise FileNotFoundError(f'未找到数据库文件: {db_name}')
        
        return db_path, code
        
    elif db_mode == 'legacy':
        # 原有模式，使用固定路径
        db_name = f'{code}_data.db'
        db_path = find_database_file(db_name)
        if not db_path:
            raise FileNotFoundError(f'未找到数据库文件: {db_name}')
        
        return db_path, code
    
    else:
        raise ValueError(f'不支持的数据库模式: {db_mode}')

def verify_database_files():
    """验证所有必需的数据库文件是否存在"""
    print("正在验证数据库文件...")
    
    # 检查加密货币数据库
    crypto_dbs = ['btc_data.db', 'eth_data.db', 'bitcoin_data.db']
    for db_name in crypto_dbs:
        db_path = find_database_file(db_name)
        if db_path:
            print(f"✓ 找到: {db_name} -> {db_path}")
        else:
            print(f"⚠ 未找到: {db_name}")
    
    # 检查股票数据库
    stock_codes = ['sh.600030', 'sh.600031']
    for code in stock_codes:
        try:
            db_path, table_name = get_database_path(code, 'baostock')
            print(f"✓ 找到: {code} -> {db_path}")
        except FileNotFoundError:
            print(f"⚠ 未找到: {code} 数据库")
    
    print("数据库验证完成")

if __name__ == "__main__":
    # 测试路径修复功能
    verify_database_files()
    
    # 测试获取路径
    print("\n测试路径获取:")
    try:
        btc_path, btc_table = get_database_path('BTC')
        print(f"BTC数据库: {btc_path}, 表: {btc_table}")
    except Exception as e:
        print(f"BTC路径获取失败: {e}")
    
    try:
        eth_path, eth_table = get_database_path('ETH')
        print(f"ETH数据库: {eth_path}, 表: {eth_table}")
    except Exception as e:
        print(f"ETH路径获取失败: {e}")
    
    try:
        stock_path, stock_table = get_database_path('sh.600030')
        print(f"股票数据库: {stock_path}, 表: {stock_table}")
    except Exception as e:
        print(f"股票路径获取失败: {e}")
