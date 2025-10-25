import sqlite3
import pandas as pd
from pathlib import Path

def verify_btc_perp_data():
    """验证BTC永续合约数据"""
    db_path = Path("btc_perp_60m.db")
    
    if not db_path.exists():
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    
    # 查看表结构
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(btcusdt_perp_60m)")
    columns = cursor.fetchall()
    
    print("📋 表结构:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    # 查看数据样本
    df = pd.read_sql_query("SELECT * FROM btcusdt_perp_60m ORDER BY datetime DESC LIMIT 10", conn)
    
    print(f"\n📊 最新10条数据样本:")
    print(df.to_string(index=False))
    
    # 查看数据统计
    cursor.execute("SELECT COUNT(*) FROM btcusdt_perp_60m")
    total_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(datetime), MAX(datetime) FROM btcusdt_perp_60m")
    time_range = cursor.fetchone()
    
    print(f"\n📈 数据统计:")
    print(f"  总条数: {total_count}")
    print(f"  时间范围: {time_range[0]} 到 {time_range[1]}")
    
    conn.close()

if __name__ == "__main__":
    verify_btc_perp_data()
