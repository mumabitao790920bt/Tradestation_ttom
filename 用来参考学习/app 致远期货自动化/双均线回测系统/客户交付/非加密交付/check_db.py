#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查数据库表结构
"""

import sqlite3
import os

def check_database():
    """检查数据库文件"""
    print("检查数据库文件...")
    
    # 检查当前目录下的数据库文件
    db_files = ['btc_data.db', 'eth_data.db', 'bitcoin_data.db']
    
    for db_file in db_files:
        if os.path.exists(db_file):
            print(f"\n✓ 找到数据库: {db_file}")
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # 获取所有表名
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                
                print(f"  数据库中的表: {[table[0] for table in tables]}")
                
                # 检查每个表的结构
                for table in tables:
                    table_name = table[0]
                    cursor.execute(f"PRAGMA table_info({table_name})")
                    columns = cursor.fetchall()
                    print(f"    表 {table_name} 的列: {[col[1] for col in columns]}")
                    
                    # 检查数据行数
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    print(f"    表 {table_name} 的数据行数: {count}")
                
                conn.close()
                
            except Exception as e:
                print(f"  检查数据库失败: {e}")
        else:
            print(f"\n⚠ 数据库文件不存在: {db_file}")

if __name__ == "__main__":
    check_database()


