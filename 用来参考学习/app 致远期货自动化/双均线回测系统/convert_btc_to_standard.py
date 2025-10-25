import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime, timezone, timedelta

def convert_btc_to_standard_format():
    """将比特币数据转换为标准格式"""
    
    # 读取现有的比特币数据
    source_db = Path("btc_perp_60m.db")
    if not source_db.exists():
        print("❌ 比特币数据库不存在，请先运行下载脚本")
        return
    
    # 创建标准格式的数据库
    target_db = Path("btc_standard_60m.db")
    
    print("🔄 开始转换比特币数据到标准格式...")
    
    # 连接源数据库
    source_conn = sqlite3.connect(source_db)
    
    # 读取数据
    df = pd.read_sql_query("SELECT * FROM btcusdt_perp_60m ORDER BY datetime", source_conn)
    print(f"📊 读取到 {len(df)} 条原始数据")
    
    # 转换数据格式
    converted_data = []
    
    for _, row in df.iterrows():
        # 转换时间格式：从字符串转为时间戳
        dt = datetime.strptime(row['datetime'], '%Y-%m-%d %H:%M:%S')
        # 转换为中国时间（UTC+8）
        china_tz = timezone(timedelta(hours=8))
        dt_china = dt.replace(tzinfo=timezone.utc).astimezone(china_tz)
        # 转换为时间戳（秒）- 确保是INTEGER类型
        timestamp = int(dt_china.timestamp())
        
        converted_data.append({
            'time': timestamp,  # INTEGER Unix时间戳
            'high': str(row['high']),
            'low': str(row['low']),
            'open': str(row['open']),
            'close': str(row['close']),
            'vol': str(row['volume']),
            'code': 'BTCUSDT'
        })
    
    print(f"✅ 转换完成，共 {len(converted_data)} 条数据")
    
    # 创建标准格式数据库
    target_conn = sqlite3.connect(target_db)
    
    # 创建标准表结构
    create_sql = """
    CREATE TABLE IF NOT EXISTS min_data60 (
        time INTEGER,
        high TEXT,
        low TEXT,
        open TEXT,
        close TEXT,
        vol TEXT,
        code TEXT,
        UNIQUE(time, vol)
    )
    """
    target_conn.execute(create_sql)
    
    # 清空现有数据
    target_conn.execute("DELETE FROM min_data60")
    
    # 插入转换后的数据
    insert_sql = """
    INSERT INTO min_data60 (time, high, low, open, close, vol, code)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    
    for data in converted_data:
        target_conn.execute(insert_sql, (
            data['time'],
            data['high'],
            data['low'],
            data['open'],
            data['close'],
            data['vol'],
            data['code']
        ))
    
    target_conn.commit()
    
    # 验证数据
    print(f"\n📋 验证标准格式数据:")
    cursor = target_conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM min_data60")
    count = cursor.fetchone()[0]
    print(f"  总条数: {count}")
    
    # 查看最新5条数据
    df_verify = pd.read_sql_query("SELECT * FROM min_data60 ORDER BY time DESC LIMIT 5", target_conn)
    print(f"\n📊 最新5条数据:")
    print(df_verify.to_string(index=False))
    
    # 查看时间范围
    cursor.execute("SELECT MIN(time), MAX(time) FROM min_data60")
    time_range = cursor.fetchone()
    min_time = datetime.fromtimestamp(time_range[0], tz=timezone(timedelta(hours=8)))
    max_time = datetime.fromtimestamp(time_range[1], tz=timezone(timedelta(hours=8)))
    print(f"\n📈 时间范围:")
    print(f"  最早: {min_time}")
    print(f"  最晚: {max_time}")
    
    source_conn.close()
    target_conn.close()
    
    print(f"\n✅ 转换完成！标准格式数据已保存到: {target_db}")
    print(f"📋 表结构完全匹配标准 min_data60 表")
    print(f"🎯 可以直接用于您的策略系统")

if __name__ == "__main__":
    convert_btc_to_standard_format()
