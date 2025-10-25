import os
import sqlite3
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import json


def download_from_coingecko(days_back=3650):
    """
    从CoinGecko API获取比特币历史数据
    
    Args:
        days_back (int): 获取多少天的历史数据，默认10年
    
    Returns:
        list: 包含历史数据的列表
    """
    print(f"正在从CoinGecko获取{days_back}天的比特币历史数据...")
    
    try:
        # CoinGecko API免费版本 - 使用更简单的端点
        url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart"
        params = {
            'vs_currency': 'usd',
            'days': str(days_back),
            'interval': 'daily'
        }
        
        print("正在连接CoinGecko API...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            print(f"CoinGecko API状态码: {response.status_code}")
            if response.status_code == 429:
                print("API请求频率限制，等待后重试...")
                time.sleep(2)
                response = requests.get(url, params=params, headers=headers, timeout=30)
                if response.status_code != 200:
                    raise Exception(f"CoinGecko API重试后仍然失败: {response.status_code}")
            else:
                raise Exception(f"CoinGecko API请求失败: {response.status_code}")
        
        data = response.json()
        
        if 'prices' not in data:
            raise Exception("CoinGecko API返回数据格式错误")
        
        prices = data['prices']
        volumes = data.get('total_volumes', [])
        
        print(f"CoinGecko返回 {len(prices)} 条价格数据")
        
        # 转换数据格式
        btc_data = []
        for i, price_point in enumerate(prices):
            timestamp_ms = price_point[0]
            price = price_point[1]
            volume = volumes[i][1] if i < len(volumes) else 0
            
            date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
            
            # CoinGecko只提供收盘价，我们用收盘价作为开盘价、最高价、最低价
            btc_data.append({
                'date': date_str,
                'open': price,
                'high': price * 1.02,  # 简单估算：假设高点比收盘价高2%
                'low': price * 0.98,   # 简单估算：假设低点比收盘价低2%
                'close': price,
                'volume': volume
            })
        
        return btc_data
        
    except Exception as e:
        print(f"CoinGecko数据获取失败: {e}")
        return []


def download_from_binance_api():
    """
    从Binance API获取比特币历史数据
    """
    print("正在尝试从Binance API获取数据...")
    
    try:
        # Binance API获取K线数据
        url = "https://api.binance.com/api/v3/klines"
        params = {
            'symbol': 'BTCUSDT',
            'interval': '1d',
            'limit': 1000  # 最多1000条
        }
        
        print("正在连接Binance API...")
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Binance API请求失败: {response.status_code}")
        
        data = response.json()
        
        print(f"Binance返回 {len(data)} 条K线数据")
        
        # 转换数据格式
        btc_data = []
        for item in data:
            timestamp_ms = item[0]
            date_str = datetime.fromtimestamp(timestamp_ms / 1000).strftime('%Y-%m-%d')
            
            btc_data.append({
                'date': date_str,
                'open': float(item[1]),
                'high': float(item[2]),
                'low': float(item[3]),
                'close': float(item[4]),
                'volume': float(item[5])
            })
        
        return btc_data
        
    except Exception as e:
        print(f"Binance API数据获取失败: {e}")
        return []


def download_from_yahoo_finance():
    """
    从Yahoo Finance获取比特币历史数据
    """
    print("正在尝试从Yahoo Finance获取数据...")
    
    try:
        # 使用Yahoo Finance的CSV下载链接，不需要API key
        # 直接下载最近几年的数据
        url = "https://query1.finance.yahoo.com/v8/finance/chart/BTC-USD"
        params = {
            'range': '10y',  # 10年数据
            'interval': '1d',
            'includePrePost': 'false'
        }
        
        print("正在连接Yahoo Finance...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Yahoo Finance请求失败: {response.status_code}")
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            raise Exception("Yahoo Finance返回数据格式错误")
        
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        # 提取OHLCV数据
        opens = quote.get('open', [])
        highs = quote.get('high', [])
        lows = quote.get('low', [])
        closes = quote.get('close', [])
        volumes = quote.get('volume', [])
        
        print(f"Yahoo Finance返回 {len(timestamps)} 条数据")
        
        # 转换数据格式
        btc_data = []
        for i, timestamp in enumerate(timestamps):
            if i < len(opens) and opens[i] is not None:
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                btc_data.append({
                    'date': date_str,
                    'open': float(opens[i]),
                    'high': float(highs[i]) if i < len(highs) and highs[i] is not None else float(opens[i]),
                    'low': float(lows[i]) if i < len(lows) and lows[i] is not None else float(opens[i]),
                    'close': float(closes[i]) if i < len(closes) and closes[i] is not None else float(opens[i]),
                    'volume': float(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0
                })
        
        return btc_data
        
    except Exception as e:
        print(f"Yahoo Finance数据获取失败: {e}")
        return []


def download_bitcoin_data(days_back=3650):
    """
    使用多个免费数据源下载比特币历史数据
    
    Args:
        days_back (int): 获取多少天的历史数据，默认10年
    
    Returns:
        str: 数据库文件路径
    """
    # 数据库路径
    db_path = Path(__file__).parent.parent / "bitcoin_data.db"
    
    print(f"开始使用多个免费数据源获取{days_back}天的比特币历史数据...")
    
    all_data = []
    
    # 数据源1: CoinGecko (免费，每秒100次请求)
    coingecko_data = download_from_coingecko(days_back)
    if coingecko_data:
        all_data.extend(coingecko_data)
        print(f"从CoinGecko获取到 {len(coingecko_data)} 条数据")
    
    # 数据源2: Binance API (免费，高质量K线数据)
    binance_data = download_from_binance_api()
    if binance_data:
        # 合并数据，避免重复日期，优先使用Binance的更准确数据
        existing_dates = {item['date'] for item in all_data}
        new_data = []
        updated_data = []
        
        for item in binance_data:
            if item['date'] in existing_dates:
                # 更新现有日期的数据（使用更准确的Binance数据）
                for i, existing_item in enumerate(all_data):
                    if existing_item['date'] == item['date']:
                        all_data[i] = item
                        updated_data.append(item['date'])
                        break
            else:
                # 新增数据
                new_data.append(item)
        
        all_data.extend(new_data)
        print(f"从Binance新增 {len(new_data)} 条数据，更新 {len(updated_data)} 条数据")
    
    # 数据源3: Yahoo Finance (免费，长期历史数据)
    yahoo_data = download_from_yahoo_finance()
    if yahoo_data:
        # 合并数据，避免重复日期
        existing_dates = {item['date'] for item in all_data}
        new_data = [item for item in yahoo_data if item['date'] not in existing_dates]
        all_data.extend(new_data)
        print(f"从Yahoo Finance新增 {len(new_data)} 条数据")
    
    if not all_data:
        raise Exception("所有数据源都获取失败，无法获得比特币数据")
    
    try:
        # 转换为DataFrame并按日期排序
        print(f"原始数据条数: {len(all_data)}")
        df = pd.DataFrame(all_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"排序后数据条数: {len(df)}")
        
        # 去重（可能有重复数据）
        before_dedup = len(df)
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        after_dedup = len(df)
        print(f"去重前: {before_dedup} 条，去重后: {after_dedup} 条")
        
        # 数据质量检查
        df = df[df['close'] > 0]  # 移除无效价格
        df = df[df['low'] <= df['high']]  # 移除无效的高低价
        
        # 将日期转换为字符串格式用于数据库存储
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        print(f"成功下载 {len(df)} 条真实比特币数据")
        print(f"数据范围: {df['date'].iloc[0]} 到 {df['date'].iloc[-1]}")
        print(f"价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # 保存到SQLite数据库
        conn = sqlite3.connect(db_path)
        
        # 创建表
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS bitcoin_daily (
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL
        )
        """
        conn.execute(create_table_sql)
        
        # 清空现有数据
        conn.execute("DELETE FROM bitcoin_daily")
        
        # 插入新数据
        df.to_sql('bitcoin_daily', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        
        print(f"比特币数据已保存到: {db_path}")
        print(f"数据条数: {len(df)}")
        
        return str(db_path)
        
    except Exception as e:
        print(f"数据处理或保存失败: {e}")
        raise


def get_bitcoin_data_from_db(limit_num=None):
    """
    从数据库读取比特币数据
    
    Args:
        limit_num: 限制读取的数据条数
    
    Returns:
        pandas.DataFrame: 比特币历史数据
    """
    db_path = Path(__file__).parent.parent / "bitcoin_data.db"
    
    if not db_path.exists():
        print("数据库不存在，请先运行下载数据")
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db_path)
        
        if limit_num:
            sql = f"SELECT * FROM bitcoin_daily ORDER BY date DESC LIMIT {limit_num}"
        else:
            sql = "SELECT * FROM bitcoin_daily ORDER BY date DESC"
        
        df = pd.read_sql_query(sql, conn)
        conn.close()
        
        # 按日期正序排列
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"从数据库读取 {len(df)} 条比特币数据")
        return df
        
    except Exception as e:
        print(f"读取数据库失败: {e}")
        return pd.DataFrame()


if __name__ == "__main__":
    try:
        # 下载比特币数据
        db_path = download_bitcoin_data(days_back=3650)  # 获取10年数据
        print(f"✅ 比特币数据下载成功: {db_path}")
        
        # 测试读取数据
        df = get_bitcoin_data_from_db(limit_num=10)
        if not df.empty:
            print("✅ 数据读取测试成功，最新10条数据:")
            print(df.tail())
        else:
            print("❌ 数据读取测试失败")
            
    except Exception as e:
        print(f"❌ 比特币数据下载失败: {e}")