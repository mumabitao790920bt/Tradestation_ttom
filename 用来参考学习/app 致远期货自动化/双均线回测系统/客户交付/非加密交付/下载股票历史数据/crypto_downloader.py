import os
import sqlite3
import pandas as pd
import requests
import time
from datetime import datetime, timedelta
from pathlib import Path
import json


def download_crypto_from_yahoo(symbol, crypto_name, days_back=3650):
    """
    从Yahoo Finance获取加密货币历史数据
    
    Args:
        symbol (str): Yahoo Finance符号，如 'BTC-USD', 'ETH-USD'
        crypto_name (str): 加密货币名称，用于显示
        days_back (int): 获取多少天的历史数据，默认10年
    
    Returns:
        list: 包含历史数据的列表
    """
    print(f"正在从Yahoo Finance获取{crypto_name}({symbol}) {days_back}天的历史数据...")
    
    try:
        # 使用Yahoo Finance的图表API
        url = "https://query1.finance.yahoo.com/v8/finance/chart/" + symbol
        params = {
            'range': '10y',  # 10年数据
            'interval': '1d',
            'includePrePost': 'false'
        }
        
        print(f"正在连接Yahoo Finance获取{crypto_name}数据...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Yahoo Finance请求失败: {response.status_code}")
        
        data = response.json()
        
        if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
            raise Exception(f"Yahoo Finance返回{crypto_name}数据格式错误")
        
        result = data['chart']['result'][0]
        timestamps = result['timestamp']
        quote = result['indicators']['quote'][0]
        
        # 提取OHLCV数据
        opens = quote.get('open', [])
        highs = quote.get('high', [])
        lows = quote.get('low', [])
        closes = quote.get('close', [])
        volumes = quote.get('volume', [])
        
        print(f"Yahoo Finance返回{crypto_name} {len(timestamps)} 条数据")
        
        # 转换数据格式
        crypto_data = []
        for i, timestamp in enumerate(timestamps):
            if i < len(opens) and opens[i] is not None:
                date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
                
                crypto_data.append({
                    'date': date_str,
                    'open': float(opens[i]),
                    'high': float(highs[i]) if i < len(highs) and highs[i] is not None else float(opens[i]),
                    'low': float(lows[i]) if i < len(lows) and lows[i] is not None else float(opens[i]),
                    'close': float(closes[i]) if i < len(closes) and closes[i] is not None else float(opens[i]),
                    'volume': float(volumes[i]) if i < len(volumes) and volumes[i] is not None else 0
                })
        
        return crypto_data
        
    except Exception as e:
        print(f"{crypto_name}数据获取失败: {e}")
        return []


def save_crypto_to_database(crypto_data, crypto_code, crypto_name):
    """
    保存加密货币数据到独立的数据库
    
    Args:
        crypto_data (list): 加密货币历史数据
        crypto_code (str): 加密货币代码，如 'BTC', 'ETH'
        crypto_name (str): 加密货币名称，如 '比特币', '以太坊'
    
    Returns:
        str: 数据库文件路径
    """
    if not crypto_data:
        raise Exception(f"没有{crypto_name}数据可保存")
    
    # 数据库路径 - 每个币种独立的数据库
    db_path = Path(__file__).parent.parent / f"{crypto_code.lower()}_data.db"
    
    try:
        # 转换为DataFrame并按日期排序
        print(f"正在处理{crypto_name}数据...")
        df = pd.DataFrame(crypto_data)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        
        # 数据质量检查
        df = df[df['close'] > 0]  # 移除无效价格
        df = df[df['low'] <= df['high']]  # 移除无效的高低价
        
        # 去重
        df = df.drop_duplicates(subset=['date']).reset_index(drop=True)
        
        # 将日期转换为字符串格式用于数据库存储
        df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        
        print(f"{crypto_name}数据处理完成: {len(df)} 条")
        print(f"数据范围: {df['date'].iloc[0]} 到 {df['date'].iloc[-1]}")
        print(f"价格范围: ${df['low'].min():.2f} - ${df['high'].max():.2f}")
        
        # 保存到SQLite数据库
        conn = sqlite3.connect(db_path)
        
        # 创建表 - 使用与股票数据相同的表结构
        create_table_sql = f"""
        CREATE TABLE IF NOT EXISTS {crypto_code.lower()}_daily (
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
        conn.execute(f"DELETE FROM {crypto_code.lower()}_daily")
        
        # 插入新数据
        df.to_sql(f'{crypto_code.lower()}_daily', conn, if_exists='append', index=False)
        conn.commit()
        conn.close()
        
        print(f"{crypto_name}数据已保存到: {db_path}")
        print(f"数据表名: {crypto_code.lower()}_daily")
        print(f"数据条数: {len(df)}")
        
        return str(db_path)
        
    except Exception as e:
        print(f"{crypto_name}数据处理或保存失败: {e}")
        raise


def get_crypto_data_from_db(crypto_code, limit_num=None):
    """
    从数据库读取加密货币数据
    
    Args:
        crypto_code (str): 加密货币代码，如 'BTC', 'ETH'
        limit_num (int): 限制读取的数据条数
    
    Returns:
        pandas.DataFrame: 加密货币历史数据
    """
    db_path = Path(__file__).parent.parent / f"{crypto_code.lower()}_data.db"
    
    if not db_path.exists():
        print(f"{crypto_code}数据库不存在，请先运行下载数据")
        return pd.DataFrame()
    
    try:
        conn = sqlite3.connect(db_path)
        
        if limit_num:
            sql = f"SELECT * FROM {crypto_code.lower()}_daily ORDER BY date DESC LIMIT {limit_num}"
        else:
            sql = f"SELECT * FROM {crypto_code.lower()}_daily ORDER BY date DESC"
        
        df = pd.read_sql_query(sql, conn)
        conn.close()
        
        # 按日期正序排列
        df = df.sort_values('date').reset_index(drop=True)
        
        print(f"从数据库读取{crypto_code} {len(df)} 条数据")
        return df
        
    except Exception as e:
        print(f"读取{crypto_code}数据库失败: {e}")
        return pd.DataFrame()


def download_all_crypto_data():
    """
    下载所有支持的加密货币数据
    """
    # 定义支持的加密货币
    crypto_configs = [
        {
            'yahoo_symbol': 'BTC-USD',
            'crypto_code': 'BTC',
            'crypto_name': '比特币',
            'display_name': 'Bitcoin (BTC)'
        },
        {
            'yahoo_symbol': 'ETH-USD',
            'crypto_code': 'ETH',
            'crypto_name': '以太坊',
            'display_name': 'Ethereum (ETH)'
        }
    ]
    
    print("=" * 60)
    print("开始下载所有加密货币历史数据")
    print("=" * 60)
    
    results = {}
    
    for config in crypto_configs:
        print(f"\n{'='*20} {config['display_name']} {'='*20}")
        
        try:
            # 下载数据
            crypto_data = download_crypto_from_yahoo(
                config['yahoo_symbol'], 
                config['crypto_name'],
                days_back=3650  # 10年数据
            )
            
            if crypto_data:
                # 保存到数据库
                db_path = save_crypto_to_database(
                    crypto_data,
                    config['crypto_code'],
                    config['crypto_name']
                )
                
                results[config['crypto_code']] = {
                    'success': True,
                    'db_path': db_path,
                    'data_count': len(crypto_data),
                    'crypto_name': config['crypto_name']
                }
                
                print(f"✅ {config['crypto_name']}数据下载成功!")
                
                # 测试读取数据
                test_df = get_crypto_data_from_db(config['crypto_code'], limit_num=5)
                if not test_df.empty:
                    print(f"✅ {config['crypto_name']}数据读取测试成功")
                    print("最新5条数据预览:")
                    print(test_df.tail())
                else:
                    print(f"❌ {config['crypto_name']}数据读取测试失败")
                    
            else:
                results[config['crypto_code']] = {
                    'success': False,
                    'error': '数据下载失败',
                    'crypto_name': config['crypto_name']
                }
                print(f"❌ {config['crypto_name']}数据下载失败")
                
        except Exception as e:
            results[config['crypto_code']] = {
                'success': False,
                'error': str(e),
                'crypto_name': config['crypto_name']
            }
            print(f"❌ {config['crypto_name']}处理失败: {e}")
        
        # 避免API限制，稍作延迟
        time.sleep(1)
    
    # 打印总结报告
    print("\n" + "=" * 60)
    print("加密货币数据下载总结报告")
    print("=" * 60)
    
    for crypto_code, result in results.items():
        if result['success']:
            print(f"✅ {result['crypto_name']} ({crypto_code}): {result['data_count']} 条数据")
            print(f"   数据库路径: {result['db_path']}")
        else:
            print(f"❌ {result['crypto_name']} ({crypto_code}): {result['error']}")
    
    # 生成回测系统使用说明
    print("\n" + "=" * 60)
    print("回测系统使用说明")
    print("=" * 60)
    print("在回测系统界面中，可以使用以下代码:")
    for config in crypto_configs:
        if config['crypto_code'] in results and results[config['crypto_code']]['success']:
            print(f"- 代码: {config['crypto_code']} (数据表: {config['crypto_code'].lower()}_daily)")
            print(f"  名称: {config['crypto_name']}")
            print(f"  数据库: {config['crypto_code'].lower()}_data.db")
    
    return results


if __name__ == "__main__":
    try:
        # 下载所有加密货币数据
        results = download_all_crypto_data()
        print(f"\n🎉 加密货币数据下载任务完成!")
        
    except Exception as e:
        print(f"❌ 加密货币数据下载任务失败: {e}")
