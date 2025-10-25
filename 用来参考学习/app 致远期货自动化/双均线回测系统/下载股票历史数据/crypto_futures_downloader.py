import os
import time
import math
import sqlite3
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional, Tuple

import requests
from pathlib import Path


BINANCE_FUTURES_BASE = "https://fapi.binance.com"
# 备用API端点
BINANCE_FUTURES_BACKUP = "https://api.binance.com"  # 现货API作为备用


def _binance_klines_perp(symbol: str, interval: str, start_time_ms: int, end_time_ms: int, limit: int = 1500) -> List[List]:
    """
    从 Binance USDT 永续合约接口获取K线原始数据（无需API Key）。

    文档: https://binance-docs.github.io/apidocs/futures/cn/#kline

    返回的是原始数组，字段顺序如下：
    [
      0 开盘时间, 1 开盘价, 2 最高价, 3 最低价, 4 收盘价, 5 成交量,
      6 收盘时间, 7 成交额, 8 成交笔数, 9 主动买入成交量, 10 主动买入成交额, 11 忽略
    ]
    """
    # 尝试多个API端点
    endpoints = [
        f"{BINANCE_FUTURES_BASE}/fapi/v1/klines",  # 永续合约
        f"{BINANCE_FUTURES_BACKUP}/api/v3/klines",  # 现货作为备用
    ]
    
    params = {
        "symbol": symbol.upper(),
        "interval": interval,
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": min(max(limit, 1), 1500),
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for i, url in enumerate(endpoints):
        for retry in range(3):  # 每个端点重试3次
            try:
                print(f"尝试连接API端点 {i+1} (重试 {retry+1}/3): {url}")
                resp = requests.get(url, params=params, headers=headers, timeout=60)
                if resp.status_code == 200:
                    print(f"✅ 成功连接到: {url}")
                    return resp.json()
                else:
                    print(f"❌ API返回错误: {resp.status_code}")
                    if retry < 2:
                        print(f"等待 {5*(retry+1)} 秒后重试...")
                        time.sleep(5*(retry+1))
            except Exception as e:
                print(f"❌ 连接失败: {e}")
                if retry < 2:
                    print(f"等待 {5*(retry+1)} 秒后重试...")
                    time.sleep(5*(retry+1))
                continue
        
        if i < len(endpoints) - 1:
            print("尝试下一个端点...")
            time.sleep(3)
    
    raise RuntimeError("所有API端点都无法连接")


def fetch_perp_klines(symbol: str, interval: str = "1h", days_back: int = 365 * 3, sleep_s: float = 0.8) -> List[Dict]:
    """
    批量拉取 Binance USDT 永续合约K线，并转换为结构化字典列表。

    - symbol: 交易对，如 BTCUSDT、ETHUSDT（USDT永续）
    - interval: K线周期，如 "1h"、"15m"、"1d" 等
    - days_back: 向历史回溯的天数
    """
    end_dt = datetime.now(tz=timezone.utc)
    start_dt = end_dt - timedelta(days=days_back)

    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)

    # 每批最多1500根K线，按周期估计每批跨度
    interval_to_minutes = {
        "1m": 1, "3m": 3, "5m": 5, "15m": 15, "30m": 30,
        "1h": 60, "2h": 120, "4h": 240, "6h": 360, "8h": 480, "12h": 720,
        "1d": 1440, "3d": 4320, "1w": 10080, "1M": 43200,
    }
    if interval not in interval_to_minutes:
        raise ValueError(f"不支持的周期: {interval}")

    step_minutes = interval_to_minutes[interval] * 1500
    step_ms = step_minutes * 60 * 1000

    klines: List[Dict] = []
    cursor = start_ms
    while cursor < end_ms:
        batch_end = min(cursor + step_ms - 1, end_ms)
        raw = _binance_klines_perp(symbol, interval, cursor, batch_end)
        # 若无数据，推进时间游标，避免死循环
        if not raw:
            cursor = batch_end + 1
            time.sleep(sleep_s)
            continue

        for item in raw:
            open_time_ms = int(item[0])
            dt_utc = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
            # 转换为中国时间 (UTC+8)
            china_tz = timezone(timedelta(hours=8))
            dt_china = dt_utc.astimezone(china_tz)
            klines.append({
                "datetime": dt_china.strftime("%Y-%m-%d %H:%M:%S"),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5]),
            })

        # 推进到最后一根K线之后
        last_open_time = int(raw[-1][0])
        next_time = last_open_time + interval_to_minutes[interval] * 60 * 1000
        cursor = max(cursor + 1, next_time)
        time.sleep(sleep_s)

    # 去重并按时间排序
    klines = { k["datetime"]: k for k in klines }.values()
    klines = sorted(klines, key=lambda x: x["datetime"])
    return list(klines)


def ensure_db_table(conn: sqlite3.Connection, table_name: str):
    sql = """
    CREATE TABLE IF NOT EXISTS min_data60 (
        time TEXT,
        high TEXT,
        low TEXT,
        open TEXT,
        close TEXT,
        vol TEXT,
        code TEXT,
        UNIQUE(time, vol)
    )
    """
    conn.execute(sql)


def save_klines_to_sqlite(db_path: Path, table_name: str, klines: List[Dict]):
    if not klines:
        raise ValueError("没有可保存的K线数据")

    conn = sqlite3.connect(db_path)
    try:
        ensure_db_table(conn, table_name)
        # 清空旧数据
        conn.execute("DELETE FROM min_data60")
        
        # 转换数据格式
        rows = []
        for k in klines:
            # 直接使用中国时间字符串格式
            rows.append((
                k["datetime"],     # time TEXT (格式: 2020-09-04 20:00:00)
                str(k["high"]),    # high TEXT
                str(k["low"]),     # low TEXT
                str(k["open"]),    # open TEXT
                str(k["close"]),   # close TEXT
                str(k["volume"]),  # vol TEXT
                "BTCUSDT"          # code TEXT
            ))
        
        conn.executemany(
            "INSERT INTO min_data60 (time, high, low, open, close, vol, code) VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def download_btc_perp_60m(days_back: int = 365 * 3) -> Tuple[str, str]:
    """
    下载 BTCUSDT 永续合约 60分钟K线，并保存到SQLite。

    返回 (数据库文件路径, 表名)
    """
    print("开始下载 Binance 永续合约 BTCUSDT 60m 历史K线...")
    klines = fetch_perp_klines(symbol="BTCUSDT", interval="1h", days_back=days_back)
    print(f"获取到 {len(klines)} 条K线")

    db_path = Path(__file__).parent.parent / "btc_perp_60m.db"
    table_name = "min_data60"
    save_klines_to_sqlite(db_path, table_name, klines)
    print(f"已保存到 {db_path} 表 {table_name}")
    return str(db_path), table_name


if __name__ == "__main__":
    try:
        db, table = download_btc_perp_60m(days_back=365 * 5)
        print(f"✅ 完成，数据库: {db}，表: {table}")
    except Exception as e:
        print(f"❌ 失败: {e}")


