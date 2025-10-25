#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX历史数据补充脚本
基于get_btc_15m_http_after_to_db.py修改

功能：
- 补充缺失的历史数据，不覆盖现有数据
- 支持15分钟和60分钟数据
- 将OKX代码转换为币安格式（如BTC → BTCUSDT）
- 只补充200根K线之前的历史数据
"""

import requests
import sqlite3
import time
import os
from datetime import datetime, timezone
from typing import List, Tuple, Optional


API_BASE = "https://www.okx.com"

# OKX到币安的代码映射
SYMBOL_MAPPING = {
    "BTC-USDT-SWAP": "BTCUSDT",
    "ETH-USDT-SWAP": "ETHUSDT", 
    "SOL-USDT-SWAP": "SOLUSDT",
    "ADA-USDT-SWAP": "ADAUSDT",
    "DOT-USDT-SWAP": "DOTUSDT",
    "LINK-USDT-SWAP": "LINKUSDT",
    "UNI-USDT-SWAP": "UNIUSDT",
    "LTC-USDT-SWAP": "LTCUSDT",
    "BCH-USDT-SWAP": "BCHUSDT",
    "XRP-USDT-SWAP": "XRPUSDT",
}


def to_ms_utc(dt_str: str) -> int:
    """将UTC时间字符串转换为毫秒时间戳"""
    return int(datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp() * 1000)


def ms_to_utc_text(ms: int) -> str:
    """将毫秒时间戳转换为UTC时间字符串"""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def get_binance_symbol(okx_symbol: str) -> str:
    """将OKX代码转换为币安格式"""
    return SYMBOL_MAPPING.get(okx_symbol, okx_symbol.replace('-USDT-SWAP', 'USDT'))


def init_db(db_path: str, table_name: str) -> None:
    """初始化数据库表"""
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
          time TEXT PRIMARY KEY,
          high TEXT,
          low TEXT,
          open TEXT,
          close TEXT,
          vol TEXT,
          code TEXT
        )
        """
    )
    cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_time ON {table_name}(time)')
    cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_code ON {table_name}(code)')
    conn.commit()
    conn.close()


def get_existing_data_range(db_path: str, table_name: str, symbol: str) -> Optional[Tuple[int, int]]:
    """
    获取数据库中现有数据的时间范围
    
    Returns:
        (earliest_time_ms, latest_time_ms) 或 None（如果没有数据）
    """
    if not os.path.exists(db_path):
        return None
        
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    try:
        # 查询该symbol的数据范围
        cur.execute(
            f"""
            SELECT MIN(time), MAX(time) 
            FROM {table_name} 
            WHERE code = ?
            """,
            (symbol,)
        )
        result = cur.fetchone()
        
        if result and result[0] and result[1]:
            earliest_ms = to_ms_utc(result[0])
            latest_ms = to_ms_utc(result[1])
            return (earliest_ms, latest_ms)
        else:
            return None
            
    except sqlite3.OperationalError:
        # 表不存在
        return None
    finally:
        conn.close()


def insert_rows(db_path: str, table_name: str, rows: List[Tuple]) -> int:
    """插入数据行，使用INSERT OR IGNORE避免重复"""
    if not rows:
        return 0
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executemany(
        f"""
        INSERT OR IGNORE INTO {table_name} (time, high, low, open, close, vol, code)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        rows,
    )
    conn.commit()
    n = cur.rowcount
    conn.close()
    return n


def fetch_history_after(inst_id: str, bar: str, after_ms: int, limit: int = 300) -> List:
    """从OKX获取历史K线数据"""
    url = f"{API_BASE}/api/v5/market/history-candles"
    params = {
        'instId': inst_id,
        'bar': bar,
        'after': str(after_ms),
        'limit': str(limit),
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data or data.get('code') != '0':
        raise RuntimeError(f"history-candles error: {data}")
    return data.get('data', [])  # 倒序，新->旧


def supplement_history_data(okx_symbol: str, bar: str, db_path: str, table_name: str) -> None:
    """
    补充历史数据 - 采用原始脚本逻辑
    
    Args:
        okx_symbol: OKX合约代码（如BTC-USDT-SWAP）
        bar: 时间周期（15m或1H）
        db_path: 数据库路径
        table_name: 表名
    """
    binance_symbol = get_binance_symbol(okx_symbol)
    
    # 设置时间范围
    start_text = "2024-07-01 00:00:00"
    start_ts = to_ms_utc(start_text)
    end_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    # 初始化数据库
    init_db(db_path, table_name)
    
    print(f"💾 目标数据库: {db_path} 表 {table_name}")
    print(f"🕒 区间(UTC): {start_text} -> now")
    print(f"📊 合约: {okx_symbol} -> {binance_symbol}")
    
    # 采用原始脚本逻辑：从现在开始往前获取历史数据
    after_ms = end_ts  # 从现在开始，按官方语义获取更早的数据
    page = 0
    total = 0
    written_total = 0
    no_progress = 0

    while after_ms > start_ts:
        page += 1
        print(f"📄 第{page}页 after={ms_to_utc_text(after_ms)}")

        tries = 0
        while True:
            tries += 1
            try:
                data = fetch_history_after(okx_symbol, bar, after_ms, limit=300)
                break
            except Exception as e:
                wait = min(2.0, 0.2 * tries)
                print(f"⏳ 请求异常({e}), 第{tries}次重试，等待{wait}s...")
                time.sleep(wait)
                if tries >= 5:
                    print("🛑 放弃该页")
                    data = []
                    break

        if not data:
            print("📄 无更多数据，结束")
            break

        # 反转为旧->新，便于打印与写库
        data.reverse()

        # 打印并准备写库
        rows = []
        for idx, (ts, o, h, l, c, vol, _v1, _v2, _cnf) in enumerate(data, start=1):
            ts_i = int(ts)
            if ts_i > end_ts:
                continue
            print(f"   #{idx:03d} time={ms_to_utc_text(ts_i)} o={o} h={h} l={l} c={c} vol={vol}")
            rows.append((ms_to_utc_text(ts_i), str(h), str(l), str(o), str(c), str(vol), binance_symbol))

        written = insert_rows(db_path, table_name, rows)
        total += len(data)
        written_total += written
        print(f"✅ 本页记录: {len(data)}，累计拉取 {total} 条，写库 {written}，累计写库 {written_total}")

        # 推进游标：使用本页最旧（最小）时间戳作为新的 after（继续向过去请求更早的数据）
        oldest_ts = int(data[0][0]) if data else after_ms
        if oldest_ts >= after_ms:
            no_progress += 1
            step = (15 if bar == "15m" else 60) * 60 * 1000
            after_ms -= step
            print(f"⚠️ 无进展第{no_progress}次，强制推进 -{step}ms -> {ms_to_utc_text(after_ms)}")
            if no_progress >= 3:
                print("🛑 连续无进展，结束")
                break
        else:
            no_progress = 0
            after_ms = oldest_ts - 1  # 再往更早推进一毫秒，避免重复

        time.sleep(0.1)

    print(f"\n🎉 {binance_symbol} ({okx_symbol}) {bar}历史数据补充完成，共写库 {written_total} 条")


def main():
    """主函数"""
    print("🚀 OKX历史数据补充工具")
    print("=" * 50)
    
    # 配置参数
    symbols_to_supplement = [
        ("BTC-USDT-SWAP", "BTCUSDT"),
        ("ETH-USDT-SWAP", "ETHUSDT"),
        ("SOL-USDT-SWAP", "SOLUSDT"),
    ]
    
    bars = ["15m", "1H"]  # 15分钟和1小时
    
    for okx_symbol, binance_symbol in symbols_to_supplement:
        # 每个合约使用独立的数据库文件
        db_path = f"{binance_symbol.lower()}_futures_data.db"
        
        for bar in bars:
            if bar == "15m":
                table_name = "min15_data"  # 正确的表名
            elif bar == "1H":
                table_name = "min60_data"  # 正确的表名
            else:
                continue
                
            try:
                print(f"\n{'='*60}")
                print(f"📊 开始补充 {binance_symbol} 的{bar}数据")
                print(f"📁 数据库: {db_path}")
                print(f"📋 表名: {table_name}")
                print(f"{'='*60}")
                
                supplement_history_data(okx_symbol, bar, db_path, table_name)
            except Exception as e:
                print(f"❌ 补充 {okx_symbol} {bar} 数据失败: {e}")
                continue
    
    print("\n🎉 所有历史数据补充完成！")


if __name__ == "__main__":
    main()
