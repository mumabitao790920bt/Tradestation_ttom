#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安期货实时数据收集器
支持多时间周期：1m, 3m, 5m, 10m, 15m, 30m, 60m
数据存储到对应的数据库表中：min1_data, min3_data, min5_data, min10_data, min15_data, min30_data, min60_data

特性：
- 实时获取K线数据
- 多周期并行收集
- 自动重连和异常处理
- 数据库去重存储
- 支持历史数据补全
"""

import requests
import sqlite3
import time
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional
import configparser
import os


class BinanceDataCollector:
    def __init__(self, db_path: str = "binance_futures_data.db", symbol: str = "BTCUSDT", use_futures: bool = True):
        self.db_path = db_path
        self.symbol = symbol
        self.use_futures = use_futures
        # 根据选择使用期货或现货API
        if use_futures:
            self.api_base = "https://fapi.binance.com"  # 期货API
            print("📊 使用币安期货API (永续合约)")
        else:
            self.api_base = "https://api.binance.com"   # 现货API
            print("📊 使用币安现货API")
        self.running = False
        self.threads = {}
        
        # 支持的时间周期和对应的表名
        # 注意：币安API的interval格式
        self.timeframes = {
            '1m': 'min1_data',
            '3m': 'min3_data', 
            '5m': 'min5_data',
            '10m': 'min10_data',  # 需要从5m合成
            '15m': 'min15_data',
            '30m': 'min30_data',
            '1h': 'min60_data'  # 币安用1h表示60分钟
        }
        
        # 需要合成的周期（从其他周期合成）
        self.synthetic_timeframes = {
            '10m': '5m'  # 10分钟从5分钟合成
        }
        
        # 初始化数据库
        self.init_database()
        
    def init_database(self):
        """初始化数据库和所有表"""
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
        
    def fetch_klines(self, interval: str, limit: int = 500) -> List[List]:
        """获取K线数据"""
        if self.use_futures:
            url = f"{self.api_base}/fapi/v1/klines"
        else:
            url = f"{self.api_base}/api/v3/klines"
        params = {
            'symbol': self.symbol,
            'interval': interval,
            'limit': limit
        }
        
        # 增加重试机制和更长的超时时间
        max_retries = 3
        timeout = 30  # 增加到30秒
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                data = response.json()
                
                if isinstance(data, dict) and 'code' in data:
                    raise RuntimeError(f"API错误: {data}")
                    
                return data
            except requests.exceptions.Timeout as e:
                print(f"⏳ 获取{interval}数据超时 (第{attempt+1}次尝试): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间
                    print(f"⏳ 等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 获取{interval}数据失败: 超时重试{max_retries}次后放弃")
                    return []
            except Exception as e:
                print(f"❌ 获取{interval}数据失败 (第{attempt+1}次尝试): {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 1
                    print(f"⏳ 等待{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    print(f"❌ 获取{interval}数据失败: 重试{max_retries}次后放弃")
                    return []
    
    def insert_data(self, table_name: str, rows: List[tuple]) -> int:
        """插入数据到指定表"""
        if not rows:
            return 0
            
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            cur.executemany(f"""
                INSERT OR IGNORE INTO {table_name} (time, high, low, open, close, vol, code)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, rows)
            conn.commit()
            inserted = cur.rowcount
            return inserted
        except Exception as e:
            print(f"❌ 插入{table_name}数据失败: {e}")
            return 0
        finally:
            conn.close()
    
    def ms_to_utc_text(self, ms: int) -> str:
        """毫秒时间戳转换为UTC文本"""
        try:
            # 转换毫秒时间戳为UTC时间
            utc_time = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"❌ 时间戳转换失败: {ms} -> {e}")
            # 返回当前时间作为备用
            return datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    def synthesize_klines(self, source_klines: List[List], target_interval: str) -> List[List]:
        """合成K线数据"""
        if target_interval == '10m':
            # 从5分钟合成10分钟
            return self._synthesize_10m_from_5m(source_klines)
        return []
    
    def _synthesize_10m_from_5m(self, klines_5m: List[List]) -> List[List]:
        """从5分钟K线合成10分钟K线"""
        if not klines_5m:
            return []
        
        synthesized = []
        i = 0
        
        while i < len(klines_5m):
            # 取2个5分钟K线合成1个10分钟K线
            if i + 1 < len(klines_5m):
                k1 = klines_5m[i]      # 第一个5分钟
                k2 = klines_5m[i + 1]  # 第二个5分钟
                
                # 合成规则：
                # 时间：第一个5分钟的开始时间
                # 开盘价：第一个5分钟的开盘价
                # 最高价：两个5分钟的最高价
                # 最低价：两个5分钟的最低价
                # 收盘价：第二个5分钟的收盘价
                # 成交量：两个5分钟的成交量之和
                
                open_time = int(k1[0])
                open_price = float(k1[1])
                high_price = max(float(k1[2]), float(k2[2]))
                low_price = min(float(k1[3]), float(k2[3]))
                close_price = float(k2[4])
                volume = float(k1[5]) + float(k2[5])
                
                # 构造合成K线（格式与原始K线一致）
                synthesized_kline = [
                    open_time,           # 开盘时间
                    str(open_price),     # 开盘价
                    str(high_price),     # 最高价
                    str(low_price),      # 最低价
                    str(close_price),    # 收盘价
                    str(volume),         # 成交量
                    k1[6],              # 收盘时间
                    k1[7],              # 成交额
                    k1[8],              # 成交笔数
                    k1[9],              # 主动买入成交量
                    k1[10],             # 主动买入成交额
                    k1[11]              # 忽略
                ]
                
                synthesized.append(synthesized_kline)
                i += 2  # 跳过已处理的两个5分钟K线
            else:
                # 如果只剩一个5分钟K线，单独处理
                k1 = klines_5m[i]
                synthesized.append(k1)
                i += 1
        
        return synthesized
    
    def collect_all_timeframes(self):
        """收集所有时间周期的数据"""
        print("🚀 开始收集所有时间周期数据")
        
        while self.running:
            try:
                print(f"\n📊 开始新一轮数据收集 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 80)
                
                # 依次处理每个时间周期
                for interval, table_name in self.timeframes.items():
                    try:
                        print(f"\n🔄 处理 {interval} 数据...")
                        
                        # 在请求之间添加小间隔，避免API限流
                        time.sleep(0.5)
                        
                        # 检查是否需要合成数据
                        if interval in self.synthetic_timeframes:
                            # 获取源数据（如5分钟数据）
                            source_interval = self.synthetic_timeframes[interval]
                            source_klines = self.fetch_klines(source_interval, limit=200)
                            
                            if not source_klines:
                                print(f"⚠️ {interval} 源数据({source_interval})无数据")
                                continue
                            
                            # 合成K线数据
                            klines = self.synthesize_klines(source_klines, interval)
                            print(f"📊 {interval}: 从{source_interval}合成 {len(klines)} 条数据")
                            
                        else:
                            # 直接获取API数据
                            klines = self.fetch_klines(interval, limit=200)
                            
                            if not klines:
                                print(f"⚠️ {interval} 无数据")
                                continue
                        
                        # 准备数据行
                        rows = []
                        for i, kline in enumerate(klines):
                            # kline格式: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, ...]
                            open_time = int(kline[0])
                            open_price = kline[1]
                            high_price = kline[2] 
                            low_price = kline[3]
                            close_price = kline[4]
                            volume = kline[5]
                            
                            time_text = self.ms_to_utc_text(open_time)
                            
                            # 调试：显示前3条数据的时间戳
                            if i < 3:
                                print(f"  🔍 调试 {interval}: 时间戳={open_time} -> {time_text}")
                            
                            rows.append((time_text, high_price, low_price, open_price, close_price, volume, self.symbol))
                        
                        # 插入数据库（自动去重）
                        inserted = self.insert_data(table_name, rows)
                        
                        if inserted > 0:
                            print(f"✅ {interval}: 插入 {inserted} 条新数据")
                        else:
                            print(f"ℹ️ {interval}: 无新数据（已存在）")
                            
                    except Exception as e:
                        print(f"❌ {interval} 处理异常: {e}")
                
                # 每轮完成后打印各表最新5条数据
                self.print_latest_data()
                
                # 等待下一轮
                print(f"\n⏰ 等待下一轮收集...")
                time.sleep(90)  # 增加到90秒，避免API限流
                
            except Exception as e:
                print(f"❌ 收集轮次异常: {e}")
                time.sleep(30)
    
    def print_latest_data(self):
        """打印各表最新5条数据"""
        print(f"\n📈 各表最新5条数据:")
        print("=" * 80)
        
        for interval, table_name in self.timeframes.items():
            try:
                conn = sqlite3.connect(self.db_path)
                cur = conn.cursor()
                
                cur.execute(f"""
                    SELECT time, high, low, open, close, vol, code 
                    FROM {table_name} 
                    ORDER BY time DESC 
                    LIMIT 5
                """)
                rows = cur.fetchall()
                
                if rows:
                    print(f"\n🔹 {interval} ({table_name}):")
                    for i, (time_str, high, low, open_price, close, vol, code) in enumerate(rows, 1):
                        print(f"  #{i}: {time_str} O={open_price} H={high} L={low} C={close} V={vol}")
                else:
                    print(f"\n🔹 {interval} ({table_name}): 无数据")
                    
                conn.close()
                    
            except Exception as e:
                print(f"\n🔹 {interval} ({table_name}): 查询失败 - {e}")
    
    def collect_timeframe_data(self, interval: str, table_name: str):
        """收集指定时间周期的数据（保留原方法用于兼容）"""
        # 这个方法现在不再使用，改为使用 collect_all_timeframes
        pass
    
    def get_sleep_time(self, interval: str) -> int:
        """根据时间周期计算睡眠时间"""
        sleep_times = {
            '1m': 30,   # 1分钟周期，每30秒更新
            '3m': 60,   # 3分钟周期，每1分钟更新  
            '5m': 120,  # 5分钟周期，每2分钟更新
            '10m': 300, # 10分钟周期，每5分钟更新
            '15m': 300, # 15分钟周期，每5分钟更新
            '30m': 600, # 30分钟周期，每10分钟更新
            '1h': 1200  # 60分钟周期，每20分钟更新
        }
        return sleep_times.get(interval, 60)
    
    def start_collection(self, timeframes: Optional[List[str]] = None):
        """开始数据收集"""
        self.running = True
        print(f"🎯 开始收集 {self.symbol} 数据")
        print(f"📊 支持的时间周期: {list(self.timeframes.keys())}")
        print(f"🔧 合成周期: {list(self.synthetic_timeframes.keys())}")
        
        # 启动单线程收集所有时间周期
        thread = threading.Thread(
            target=self.collect_all_timeframes,
            daemon=True
        )
        thread.start()
        self.threads['all'] = thread
        print(f"🚀 数据收集已启动，使用单线程模式")
    
    def stop_collection(self):
        """停止数据收集"""
        print("🛑 正在停止数据收集...")
        self.running = False
        
        # 创建字典副本进行遍历，避免迭代冲突
        threads_to_stop = list(self.threads.items())
        self.threads.clear()  # 先清空字典，避免并发修改
        
        # 等待所有线程结束
        for interval, thread in threads_to_stop:
            thread.join(timeout=5)
            print(f"✅ {interval} 线程已停止")
        
        print("🎉 数据收集已完全停止")
    
    def get_latest_data(self, timeframe: str, limit: int = 10) -> List[tuple]:
        """获取最新数据"""
        if timeframe not in self.timeframes:
            return []
        
        table_name = self.timeframes[timeframe]
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            cur.execute(f"""
                SELECT time, high, low, open, close, vol, code 
                FROM {table_name} 
                WHERE code = ? 
                ORDER BY time DESC 
                LIMIT ?
            """, (self.symbol, limit))
            return cur.fetchall()
        finally:
            conn.close()
    
    def get_data_count(self) -> Dict[str, int]:
        """获取各表数据统计"""
        counts = {}
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            for timeframe, table_name in self.timeframes.items():
                cur.execute(f"SELECT COUNT(*) FROM {table_name} WHERE code = ?", (self.symbol,))
                counts[timeframe] = cur.fetchone()[0]
            return counts
        finally:
            conn.close()


def main():
    """主函数 - 演示用法"""
    # 创建数据收集器 - 使用现货API
    collector = BinanceDataCollector(
        db_path="binance_spot_data.db",
        symbol="BTCUSDT",
        use_futures=False  # 使用现货API
    )
    
    try:
        # 开始收集所有时间周期的数据
        collector.start_collection()
        
        # 持续运行
        print("\n⏰ 数据收集持续运行中... (按Ctrl+C停止)")
        print("📋 每轮收集流程:")
        print("   1. 依次处理 1m, 3m, 5m, 10m(合成), 15m, 30m, 1h")
        print("   2. 每次获取200条数据")
        print("   3. 自动去重写入数据库")
        print("   4. 每轮完成后显示各表最新5条数据")
        print("   5. 每分钟执行一轮")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    finally:
        collector.stop_collection()


if __name__ == "__main__":
    main()
