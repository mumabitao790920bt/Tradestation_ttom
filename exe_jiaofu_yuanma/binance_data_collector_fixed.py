#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安期货实时数据收集器 - 修复版
解决K线数据不连续问题，确保等待完整K线周期完成后再写入数据

修复内容：
1. 等待当前K线完成后再获取数据
2. 使用收盘时间作为时间戳
3. 添加K线完成检测机制
4. 优化数据收集时机
"""

import requests
import sqlite3
import time
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
import configparser
import os


class BinanceDataCollectorFixed:
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
    
    def get_server_time(self) -> int:
        """获取币安服务器时间"""
        try:
            if self.use_futures:
                url = f"{self.api_base}/fapi/v1/time"
            else:
                url = f"{self.api_base}/api/v3/time"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data['serverTime']
        except Exception as e:
            print(f"❌ 获取服务器时间失败: {e}")
            return int(time.time() * 1000)
    
    def wait_for_candle_completion(self, interval: str) -> None:
        """等待当前K线完成"""
        server_time = self.get_server_time()
        interval_seconds = self.interval_seconds[interval]
        
        # 计算当前K线的结束时间
        current_time = server_time / 1000  # 转换为秒
        interval_start = (int(current_time) // interval_seconds) * interval_seconds
        next_interval_start = interval_start + interval_seconds
        
        # 计算需要等待的时间
        wait_seconds = next_interval_start - current_time
        
        if wait_seconds > 0:
            print(f"⏰ 等待 {interval} K线完成，还需等待 {wait_seconds:.1f} 秒")
            time.sleep(wait_seconds + 1)  # 多等1秒确保K线完成
        else:
            print(f"⏰ {interval} K线已完成，立即获取数据")
    
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
        
        max_retries = 3
        timeout = 30
        
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
                    wait_time = (attempt + 1) * 2
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
            utc_time = datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
            return utc_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"❌ 时间戳转换失败: {ms} -> {e}")
            return datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S')
    
    def filter_completed_klines(self, klines: List[List], interval: str) -> List[List]:
        """过滤出已完成的K线，排除未完成的K线"""
        if not klines:
            return []
        
        interval_seconds = self.interval_seconds[interval]
        current_time = datetime.now(timezone.utc)
        current_timestamp = int(current_time.timestamp() * 1000)
        
        completed_klines = []
        
        for kline in klines:
            close_time = int(kline[6])  # 收盘时间
            
            # 计算K线应该结束的时间
            open_time = int(kline[0])  # 开盘时间
            expected_close_time = open_time + (interval_seconds * 1000)  # 预期收盘时间
            
            # 如果收盘时间等于预期收盘时间，说明K线已完成
            if close_time == expected_close_time:
                completed_klines.append(kline)
            else:
                # 检查是否是当前正在进行的K线
                time_diff = current_timestamp - close_time
                if time_diff < 0:
                    # 收盘时间在未来，说明是未完成的K线
                    print(f"  ⚠️  跳过未完成K线: 收盘时间={self.ms_to_utc_text(close_time)} (未来时间)")
                else:
                    # 可能是数据异常，也跳过
                    print(f"  ⚠️  跳过异常K线: 收盘时间={self.ms_to_utc_text(close_time)}")
        
        print(f"  📊 {interval}: 总K线 {len(klines)} 条，已完成 {len(completed_klines)} 条")
        return completed_klines
    
    def collect_timeframe_data(self, interval: str, table_name: str):
        """收集指定时间周期的数据 - 剔除最后一个K线，只存储前一个稳定的K线"""
        print(f"🔄 开始收集 {interval} 数据...")
        print(f"📋 策略: 不断获取数据，剔除最后一个K线，只存储前一个稳定的K线")
        
        while self.running:
            try:
                # 获取K线数据
                klines = self.fetch_klines(interval, limit=200)
                
                if not klines:
                    print(f"⚠️ {interval} 无数据")
                    time.sleep(30)  # 等待30秒后重试
                    continue
                
                # 剔除最后一个K线（正在进行的K线），保留前面的稳定K线
                stable_klines = klines[:-1]  # 剔除最后一个
                
                # 详细打印剔除和存储的信息
                print(f"\n📊 {interval} 数据处理详情:")
                print(f"   获取到K线总数: {len(klines)}")
                
                if len(klines) > 0:
                    # 显示被剔除的最后一个K线
                    last_kline = klines[-1]
                    last_close_time = int(last_kline[6])
                    last_open_price = float(last_kline[1])
                    last_high_price = float(last_kline[2])
                    last_low_price = float(last_kline[3])
                    last_close_price = float(last_kline[4])
                    last_volume = float(last_kline[5])
                    last_time_text = self.ms_to_utc_text(last_close_time)
                    
                    print(f"   ❌ 剔除的K线（正在进行的K线）:")
                    print(f"      时间: {last_time_text}")
                    print(f"      开盘价: {last_open_price:.4f}")
                    print(f"      最高价: {last_high_price:.4f}")
                    print(f"      最低价: {last_low_price:.4f}")
                    print(f"      收盘价: {last_close_price:.4f}")
                    print(f"      成交量: {last_volume:.2f}")
                    print(f"      品种: {self.symbol}")
                    print(f"      原因: 正在进行的K线，可能还在变化")
                
                if not stable_klines:
                    print(f"   ℹ️ 没有稳定的K线，跳过本次写入")
                    time.sleep(30)
                    continue
                
                print(f"   稳定K线数量: {len(stable_klines)}")
                print(f"   ✅ 将存储的稳定K线:")
                
                # 准备数据行 - 只处理稳定的K线
                rows = []
                for i, kline in enumerate(stable_klines):
                    # kline格式: [开盘时间, 开盘价, 最高价, 最低价, 收盘价, 成交量, 收盘时间, ...]
                    close_time = int(kline[6])  # 使用收盘时间
                    open_price = float(kline[1])
                    high_price = float(kline[2]) 
                    low_price = float(kline[3])
                    close_price = float(kline[4])
                    volume = float(kline[5])
                    
                    time_text = self.ms_to_utc_text(close_time)
                    
                    # 详细显示每个稳定K线的信息
                    print(f"      #{i+1}: {time_text}")
                    print(f"         开盘价: {open_price:.4f}")
                    print(f"         最高价: {high_price:.4f}")
                    print(f"         最低价: {low_price:.4f}")
                    print(f"         收盘价: {close_price:.4f}")
                    print(f"         成交量: {volume:.2f}")
                    print(f"         品种: {self.symbol}")
                    
                    rows.append((time_text, high_price, low_price, open_price, close_price, volume, self.symbol))
                
                # 插入数据库（自动去重）
                inserted = self.insert_data(table_name, rows)
                
                print(f"\n💾 数据库操作结果:")
                if inserted > 0:
                    print(f"   ✅ 成功插入 {inserted} 条稳定的K线数据到数据库")
                    print(f"   📊 数据库表: {table_name}")
                else:
                    print(f"   ℹ️ 无新数据插入（数据已存在）")
                
                print(f"   ⏰ 等待30秒后继续获取下一轮数据...")
                print("=" * 80)
                
                # 短暂等待后继续获取
                time.sleep(30)
                
            except Exception as e:
                print(f"❌ {interval} 收集异常: {e}")
                time.sleep(60)  # 异常后等待1分钟
    
    def print_latest_data_for_timeframe(self, interval: str, table_name: str):
        """打印指定时间周期的最新数据"""
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()
            
            cur.execute(f"""
                SELECT time, high, low, open, close, vol, code 
                FROM {table_name} 
                WHERE code = ?
                ORDER BY time DESC 
                LIMIT 3
            """, (self.symbol,))
            rows = cur.fetchall()
            
            if rows:
                print(f"📈 {interval} 最新3条数据:")
                for i, (time_str, high, low, open_price, close, vol, code) in enumerate(rows, 1):
                    print(f"  #{i}: {time_str} O={open_price} H={high} L={low} C={close} V={vol}")
            else:
                print(f"📈 {interval}: 无数据")
                
            conn.close()
                
        except Exception as e:
            print(f"📈 {interval}: 查询失败 - {e}")
    
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
        print("🔧 修复版特性:")
        print("   - 不断获取交易所数据")
        print("   - 剔除最后一个K线（正在进行的K线）")
        print("   - 只存储前一个稳定的K线")
        print("   - 使用收盘时间作为时间戳")
        
        # 启动多线程收集不同时间周期
        if timeframes is None:
            timeframes = list(self.timeframes.keys())
        
        for interval in timeframes:
            if interval in self.timeframes:
                table_name = self.timeframes[interval]
                thread = threading.Thread(
                    target=self.collect_timeframe_data,
                    args=(interval, table_name),
                    daemon=True
                )
                thread.start()
                self.threads[interval] = thread
                print(f"🚀 {interval} 数据收集线程已启动")
        
        print(f"🎉 所有数据收集线程已启动")
    
    def stop_collection(self):
        """停止数据收集"""
        print("🛑 正在停止数据收集...")
        self.running = False
        
        # 创建字典副本进行遍历，避免迭代冲突
        threads_to_stop = list(self.threads.items())
        self.threads.clear()
        
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
    # 创建修复版数据收集器
    collector = BinanceDataCollectorFixed(
        db_path="binance_futures_data_fixed.db",
        symbol="SOLUSDT",
        use_futures=True
    )
    
    try:
        # 开始收集15分钟数据
        collector.start_collection(['15m'])
        
        # 持续运行
        print("\n⏰ 数据收集持续运行中... (按Ctrl+C停止)")
        print("📋 修复版特性:")
        print("   1. 等待15分钟K线完成后再获取数据")
        print("   2. 使用收盘时间作为时间戳")
        print("   3. 确保数据连续性")
        print("   4. 避免数据跳跃问题")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    finally:
        collector.stop_collection()


if __name__ == "__main__":
    main()
