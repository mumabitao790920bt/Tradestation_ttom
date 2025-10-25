import sqlite3
import pandas as pd
from pathlib import Path

def read_standard_table_structure():
    """读取标准数据表结构"""
    
    db_path = Path("D:/qihuo_sql/KQ.m@SHFE.cu_data.db")
    
    if not db_path.exists():
        print(f"❌ 标准数据库文件不存在: {db_path}")
        return None
    
    try:
        conn = sqlite3.connect(db_path)
        
        # 查看所有表
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("📋 数据库中的所有表:")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 查看 min_data60 表结构
        print(f"\n📋 min_data60 表结构:")
        cursor.execute("PRAGMA table_info(min_data60)")
        columns = cursor.fetchall()
        
        print("字段详情:")
        for col in columns:
            print(f"  {col[1]} ({col[2]}) - {'NOT NULL' if col[3] else 'NULL'} - {'PRIMARY KEY' if col[5] else ''}")
        
        # 获取完整的CREATE TABLE语句
        print(f"\n📋 完整的CREATE TABLE语句:")
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='min_data60'")
        create_sql = cursor.fetchone()
        if create_sql:
            print(create_sql[0])
        
        # 查看数据样本
        print(f"\n📊 min_data60 数据样本 (最新5条):")
        df = pd.read_sql_query("SELECT * FROM min_data60 ORDER BY time DESC LIMIT 5", conn)
        print(df.to_string(index=False))
        
        # 查看数据统计
        cursor.execute("SELECT COUNT(*) FROM min_data60")
        total_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT MIN(time), MAX(time) FROM min_data60")
        time_range = cursor.fetchone()
        
        print(f"\n📈 数据统计:")
        print(f"  总条数: {total_count}")
        print(f"  时间范围: {time_range[0]} 到 {time_range[1]}")
        
        conn.close()
        
        return columns
        
    except Exception as e:
        print(f"❌ 读取标准表失败: {e}")
        return None

if __name__ == "__main__":
    read_standard_table_structure()
