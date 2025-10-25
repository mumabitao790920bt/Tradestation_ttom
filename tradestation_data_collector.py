#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tradestation期货实时数据收集器 - 简化版
基于Tradestation API的数据收集器，完全复刻币安数据收集器的功能和数据库结构
"""

import sqlite3
import time
import threading
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import os
import sys
import warnings

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.services.tradestation_client import TradestationAPIClient

# 设置事件循环策略以避免Windows上的警告
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 忽略asyncio警告
warnings.filterwarnings("ignore", category=RuntimeWarning, module="asyncio")


class TradestationDataCollector:
    def __init__(self, db_path: str = "tradestation_futures_data.db", symbol: str = "ES"):
        self.db_path = db_path
        self.symbol = symbol
        
        print(f"📊 使用Tradestation API收集 {symbol} 数据")
        
        self.running = False
        self.threads = {}
        
        # 支持的时间周期和对应的表名 - 完全复刻币安的结构
        self.timeframes = {
            '1m': 'min1_data',
            '3m': 'min3_data', 
            '5m': 'min5_data',
            '10m': 'min10_data',
            '15m': 'min15_data',
            '30m': 'min30_data',
            '1h': 'min60_data'
        }
        
        # 时间周期对应的秒数
        self.interval_seconds = {
            '1m': 60,
            '3m': 180,
            '5m': 300,
            '10m': 600,
            '15m': 900,
            '30m': 1800,
            '1h': 3600
        }
        
        # Tradestation API时间周期映射
        self.tradestation_intervals = {
            '1m': (1, 'minute'),
            '3m': (3, 'minute'),
            '5m': (5, 'minute'),
            '10m': (10, 'minute'),
            '15m': (15, 'minute'),
            '30m': (30, 'minute'),
            '1h': (60, 'minute')
        }
        
        # 初始化数据库
        self.init_database()
        
    def init_database(self):
        """初始化数据库和所有表 - 完全复刻币安的数据结构"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        for timeframe, table_name in self.timeframes.items():
            cur.execute(f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    time TEXT PRIMARY KEY,
                    high TEXT,
                    low TEXT,
                    open TEXT,
                    close TEXT,
                    vol TEXT,
                    code TEXT
                )
            """)
            cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_time ON {table_name}(time)')
            cur.execute(f'CREATE INDEX IF NOT EXISTS idx_{table_name}_code ON {table_name}(code)')
        
        conn.commit()
        conn.close()
        print(f"✅ 数据库初始化完成: {self.db_path}")
    
    def get_server_time(self) -> int:
        """获取Tradestation服务器时间"""
        try:
            # 使用当前时间作为服务器时间
            return int(datetime.now(timezone.utc).timestamp() * 1000)
        except Exception as e:
            print(f"❌ 获取服务器时间失败: {e}")
            return int(time.time() * 1000)
    
    def wait_for_next_candle(self, timeframe: str) -> int:
        """等待下一个K线周期开始"""
        server_time = self.get_server_time()
        interval_ms = self.interval_seconds[timeframe] * 1000
        
        # 计算下一个K线开始时间
        next_candle_time = ((server_time // interval_ms) + 1) * interval_ms
        wait_time = (next_candle_time - server_time) / 1000.0
        
        if wait_time > 0:
            print(f"⏰ 等待 {timeframe} K线周期开始，等待时间: {wait_time:.1f}秒")
            time.sleep(wait_time)
        
        return next_candle_time
    
    def get_kline_data_sync(self, timeframe: str, limit: int = 1) -> List[Dict]:
        """同步方式获取K线数据 - 使用requests避免asyncio问题"""
        try:
            interval, unit = self.tradestation_intervals[timeframe]
            
            # 直接使用requests而不是asyncio
            import requests
            import json
            
            # 从TradestationAPIClient获取认证信息
            try:
                client = TradestationAPIClient()
                
                # 检查令牌是否有效，如果无效则自动刷新
                if not client.is_token_valid():
                    print("🔄 访问令牌已过期，正在自动刷新...")
                    try:
                        # 使用同步方式刷新令牌
                        import asyncio
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(client.refresh_access_token())
                            print("✅ 访问令牌刷新成功")
                            # 刷新后重新加载令牌
                            client._load_tokens()
                        finally:
                            loop.close()
                    except Exception as refresh_error:
                        print(f"❌ 刷新令牌失败: {refresh_error}")
                        print("❌ 需要重新运行认证流程")
                        return []
                
                # 获取当前有效的令牌
                if not client.access_token:
                    print("❌ 未找到有效的访问令牌")
                    return []
                
                # 使用client的access_token而不是从文件重新加载
                access_token = client.access_token
                    
            except Exception as e:
                print(f"❌ 获取访问令牌失败: {e}")
                return []
            
            # 构建API请求
            url = f"https://api.tradestation.com/v3/marketdata/barcharts/{self.symbol}"
            headers = {
                'Authorization': f"Bearer {access_token}",
                'Content-Type': 'application/json'
            }
            params = {
                'interval': interval,
                'unit': unit,
                'barsback': limit
            }
            
            # 发送请求
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                
                if result and 'Bars' in result:
                    bars = result['Bars']
                    kline_data = []
                    
                    for bar in bars:
                        # 转换Tradestation数据格式为币安格式
                        kline = {
                            'open_time': int(datetime.fromisoformat(bar['TimeStamp'].replace('Z', '+00:00')).timestamp() * 1000),
                            'close_time': int(datetime.fromisoformat(bar['TimeStamp'].replace('Z', '+00:00')).timestamp() * 1000) + self.interval_seconds[timeframe] * 1000 - 1,
                            'symbol': self.symbol,
                            'interval': timeframe,
                            'first_trade_id': 0,
                            'last_trade_id': 0,
                            'open': str(bar['Open']),
                            'high': str(bar['High']),
                            'low': str(bar['Low']),
                            'close': str(bar['Close']),
                            'volume': str(bar.get('Volume', '0')),
                            'quote_asset_volume': '0',
                            'number_of_trades': 0,
                            'taker_buy_base_asset_volume': '0',
                            'taker_buy_quote_asset_volume': '0',
                            'ignore': '0'
                        }
                        kline_data.append(kline)
                    
                    return kline_data
                else:
                    print(f"❌ 获取 {self.symbol} {timeframe} 数据失败")
                    return []
            else:
                print(f"❌ API请求失败: {response.status_code}")
                return []
                
        except Exception as e:
            print(f"❌ 获取K线数据出错: {e}")
            return []
    
    def save_kline_data(self, timeframe: str, kline_data: List[Dict]):
        """保存K线数据到数据库"""
        if not kline_data:
            return
        
        table_name = self.timeframes[timeframe]
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            for kline in kline_data:
                # 使用收盘时间作为时间戳
                timestamp = datetime.fromtimestamp(kline['close_time'] / 1000).strftime('%Y-%m-%d %H:%M:%S')
                
                cur.execute(f"""
                    INSERT OR REPLACE INTO {table_name} 
                    (time, high, low, open, close, vol, code)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    timestamp,
                    kline['high'],
                    kline['low'],
                    kline['open'],
                    kline['close'],
                    kline['volume'],
                    self.symbol
                ))
            
            conn.commit()
            conn.close()
            
            print(f"✅ 已保存 {len(kline_data)} 条 {self.symbol} {timeframe} 数据")
            
        except Exception as e:
            print(f"❌ 保存数据失败: {e}")
    
    def collect_timeframe_data(self, timeframe: str):
        """收集指定时间周期的数据"""
        print(f"🚀 开始收集 {self.symbol} {timeframe} 数据...")
        
        # 首先批量下载历史数据
        self.download_historical_data(timeframe)
        
        # 然后开始实时收集
        while self.running:
            try:
                # 等待下一个K线周期
                self.wait_for_next_candle(timeframe)
                
                # 获取K线数据
                kline_data = self.get_kline_data_sync(timeframe, limit=1)
                
                if kline_data:
                    # 保存数据
                    self.save_kline_data(timeframe, kline_data)
                else:
                    print(f"⚠️ 未获取到 {self.symbol} {timeframe} 数据")
                
                # 等待一段时间再继续
                time.sleep(1)
                
            except Exception as e:
                print(f"❌ 收集 {timeframe} 数据出错: {e}")
                time.sleep(5)  # 出错后等待5秒再重试
    
    def download_historical_data(self, timeframe: str):
        """批量下载历史数据"""
        print(f"📥 开始批量下载 {self.symbol} {timeframe} 历史数据...")
        
        try:
            # 获取1000条历史数据
            kline_data = self.get_kline_data_sync(timeframe, limit=1000)
            
            if kline_data:
                print(f"✅ 获取到 {len(kline_data)} 条 {timeframe} 历史数据")
                
                # 保存所有历史数据
                self.save_kline_data(timeframe, kline_data)
                
                print(f"🎉 已保存 {len(kline_data)} 条 {self.symbol} {timeframe} 历史数据")
            else:
                print(f"❌ 未获取到 {self.symbol} {timeframe} 历史数据")
                
        except Exception as e:
            print(f"❌ 下载历史数据失败: {e}")
    
    def start_collection(self, timeframes: List[str]):
        """开始数据收集"""
        if self.running:
            print("⚠️ 数据收集已在运行中")
            return
        
        self.running = True
        print(f"🚀 开始收集 {self.symbol} 数据，时间周期: {', '.join(timeframes)}")
        
        # 为每个时间周期创建线程
        for timeframe in timeframes:
            if timeframe in self.timeframes:
                thread = threading.Thread(
                    target=self.collect_timeframe_data,
                    args=(timeframe,),
                    daemon=True
                )
                thread.start()
                self.threads[timeframe] = thread
                print(f"✅ {timeframe} 数据收集线程已启动")
            else:
                print(f"❌ 不支持的时间周期: {timeframe}")
    
    def stop_collection(self):
        """停止数据收集"""
        if not self.running:
            print("⚠️ 数据收集未在运行")
            return
        
        self.running = False
        print(f"🛑 停止收集 {self.symbol} 数据...")
        
        # 等待所有线程结束
        for timeframe, thread in self.threads.items():
            thread.join(timeout=5)
            print(f"✅ {timeframe} 数据收集线程已停止")
        
        self.threads.clear()
        print(f"✅ {self.symbol} 数据收集已完全停止")
    
    def get_latest_data(self, timeframe: str, limit: int = 100) -> List[Dict]:
        """获取最新数据"""
        table_name = self.timeframes.get(timeframe)
        if not table_name:
            return []
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute(f"""
                SELECT time, high, low, open, close, vol, code
                FROM {table_name}
                WHERE code = ?
                ORDER BY time DESC
                LIMIT ?
            """, (self.symbol, limit))
            
            rows = cur.fetchall()
            conn.close()
            
            data = []
            for row in rows:
                data.append({
                    'time': row[0],
                    'high': row[1],
                    'low': row[2],
                    'open': row[3],
                    'close': row[4],
                    'volume': row[5],
                    'symbol': row[6]
                })
            
            return data
            
        except Exception as e:
            print(f"❌ 获取最新数据失败: {e}")
            return []
    
    def get_data_count(self, timeframe: str) -> int:
        """获取数据条数"""
        table_name = self.timeframes.get(timeframe)
        if not table_name:
            return 0
        
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute(f"""
                SELECT COUNT(*)
                FROM {table_name}
                WHERE code = ?
            """, (self.symbol,))
            
            count = cur.fetchone()[0]
            conn.close()
            
            return count
            
        except Exception as e:
            print(f"❌ 获取数据条数失败: {e}")
            return 0


def main():
    """测试函数"""
    collector = TradestationDataCollector("test_es_data.db", "ES")
    
    try:
        # 开始收集数据
        collector.start_collection(['1m', '5m'])
        
        # 运行一段时间
        time.sleep(60)
        
    finally:
        # 停止收集
        collector.stop_collection()
        
        # 显示数据统计
        for timeframe in ['1m', '5m']:
            count = collector.get_data_count(timeframe)
            print(f"📊 {timeframe} 数据条数: {count}")


if __name__ == "__main__":
    main()