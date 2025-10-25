import sqlite3
import pandas as pd
import os

def verify_data_save():
    """验证数据保存是否完整"""
    
    # 检查中信证券的数据库文件
    db_path = r'gupiao_baostock\sh.600030_data.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件不存在: {db_path}")
        return
    
    print(f"=== 验证数据库: {db_path} ===")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查表结构
        tables = ['daily_data', 'weekly_data', 'monthly_data']
        
        for table in tables:
            print(f"\n--- 检查表 {table} ---")
            
            # 获取表结构
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"表字段数量: {len(columns)}")
            print("字段列表:")
            for col in columns:
                print(f"  {col[1]} ({col[2]})")
            
            # 获取数据统计
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"数据条数: {count}")
            
            if count > 0:
                # 获取前3条数据
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                rows = cursor.fetchall()
                
                print("前3条数据:")
                for i, row in enumerate(rows):
                    print(f"  第{i+1}条: {row}")
                
                # 检查关键字段是否有数据
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE volume > 0")
                volume_count = cursor.fetchone()[0]
                print(f"有成交量的记录数: {volume_count}")
                
                cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE amount > 0")
                amount_count = cursor.fetchone()[0]
                print(f"有成交金额的记录数: {amount_count}")
                
                if table == 'daily_data':
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE preclose > 0")
                    preclose_count = cursor.fetchone()[0]
                    print(f"有昨收价的记录数: {preclose_count}")
                    
                    cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE peTTM > 0")
                    pe_count = cursor.fetchone()[0]
                    print(f"有市盈率的记录数: {pe_count}")
        
        # 导出CSV文件进行详细检查
        print(f"\n--- 导出数据到CSV文件 ---")
        for table in tables:
            try:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                csv_filename = f"verify_{table}_data.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"  {table} 数据已导出到: {csv_filename}")
                print(f"  数据形状: {df.shape}")
                print(f"  列名: {list(df.columns)}")
            except Exception as e:
                print(f"  导出 {table} 失败: {e}")
    
    except Exception as e:
        print(f"验证时发生错误: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    verify_data_save() 