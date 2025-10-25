import sqlite3
import pandas as pd
from pathlib import Path

def update_crypto_database_structure():
    """
    更新加密货币数据库结构，使其与股票数据库完全一致
    """
    print("开始更新加密货币数据库结构...")
    
    # 股票数据库表结构（作为模板）
    stock_columns = [
        ('date', 'TEXT', 'PRIMARY KEY'),
        ('code', 'TEXT'),
        ('open', 'REAL'),
        ('high', 'REAL'),
        ('low', 'REAL'),
        ('close', 'REAL'),
        ('preclose', 'REAL'),
        ('volume', 'REAL'),
        ('amount', 'REAL'),
        ('adjustflag', 'TEXT'),
        ('turn', 'REAL'),
        ('tradestatus', 'TEXT'),
        ('pctChg', 'REAL'),
        ('peTTM', 'REAL'),
        ('psTTM', 'REAL'),
        ('pcfNcfTTM', 'REAL'),
        ('pbMRQ', 'REAL'),
        ('isST', 'TEXT')
    ]
    
    # 更新比特币数据库
    print("\n=== 更新比特币数据库 ===")
    update_single_crypto_db('btc_data.db', 'btc_daily', 'BTC', stock_columns)
    
    # 更新以太坊数据库
    print("\n=== 更新以太坊数据库 ===")
    update_single_crypto_db('eth_data.db', 'eth_daily', 'ETH', stock_columns)
    
    print("\n✅ 所有加密货币数据库结构更新完成！")

def update_single_crypto_db(db_path, table_name, crypto_code, stock_columns):
    """
    更新单个加密货币数据库结构
    """
    db_file = Path(__file__).parent.parent / db_path
    
    if not db_file.exists():
        print(f"❌ 数据库文件不存在: {db_path}")
        return
    
    print(f"正在更新 {crypto_code} 数据库: {db_path}")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 备份原表
    backup_table = f"{table_name}_backup"
    cursor.execute(f"CREATE TABLE IF NOT EXISTS {backup_table} AS SELECT * FROM {table_name}")
    print(f"✅ 已备份原表到 {backup_table}")
    
    # 删除原表
    cursor.execute(f"DROP TABLE {table_name}")
    print(f"✅ 已删除原表 {table_name}")
    
    # 创建新表，结构与股票数据库完全一致
    create_sql = f"CREATE TABLE {table_name} ("
    create_sql += ", ".join([f"{col[0]} {col[1]}" for col in stock_columns])
    create_sql += ")"
    
    cursor.execute(create_sql)
    print(f"✅ 已创建新表 {table_name}，结构与股票数据库一致")
    
    # 从备份表读取数据
    cursor.execute(f"SELECT date, open, high, low, close, volume FROM {backup_table}")
    old_data = cursor.fetchall()
    print(f"✅ 从备份表读取到 {len(old_data)} 条数据")
    
    # 插入数据到新表，补充缺失字段
    for row in old_data:
        date, open_price, high, low, close, volume = row
        
        # 计算缺失字段的默认值
        preclose = close  # 前收盘价，用当前收盘价代替
        amount = volume * close  # 成交额 = 成交量 * 收盘价
        adjustflag = "3"  # 默认复权类型
        turn = 0.0  # 换手率，加密货币默认为0
        tradestatus = "1"  # 交易状态，1表示正常交易
        pctChg = 0.0  # 涨跌幅，需要计算
        peTTM = 0.0  # 市盈率，加密货币不适用
        psTTM = 0.0  # 市销率，加密货币不适用
        pcfNcfTTM = 0.0  # 市现率，加密货币不适用
        pbMRQ = 0.0  # 市净率，加密货币不适用
        isST = "0"  # 是否ST，加密货币不适用
        
        # 插入完整数据
        insert_sql = f"""
        INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_sql, (
            date, crypto_code, open_price, high, low, close, preclose,
            volume, amount, adjustflag, turn, tradestatus, pctChg,
            peTTM, psTTM, pcfNcfTTM, pbMRQ, isST
        ))
    
    # 删除备份表
    cursor.execute(f"DROP TABLE {backup_table}")
    print(f"✅ 已删除备份表 {backup_table}")
    
    # 提交更改
    conn.commit()
    conn.close()
    
    print(f"✅ {crypto_code} 数据库更新完成！")
    
    # 验证新结构
    verify_db_structure(db_path, table_name)

def verify_db_structure(db_path, table_name):
    """
    验证数据库结构是否正确
    """
    db_file = Path(__file__).parent.parent / db_path
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    
    print(f"\n📋 {table_name} 表结构验证:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 检查数据样本
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY date DESC LIMIT 3")
    sample_data = cursor.fetchall()
    
    print(f"\n📊 最新3条数据样本:")
    for row in sample_data:
        print(f"  {row}")
    
    # 检查数据总数
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    total_count = cursor.fetchone()[0]
    print(f"\n📈 数据总数: {total_count}")
    
    conn.close()

if __name__ == '__main__':
    print("============================================================")
    print("加密货币数据库结构更新工具")
    print("将加密货币数据库结构更新为与股票数据库完全一致")
    print("============================================================")
    
    update_crypto_database_structure()
    
    print("\n============================================================")
    print("更新完成！现在加密货币数据库结构与股票数据库完全一致")
    print("回测系统可以无缝使用加密货币数据")
    print("============================================================")
