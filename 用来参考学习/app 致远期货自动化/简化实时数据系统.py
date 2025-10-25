#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化实时数据系统
所有功能合并到一个文件，确保每分钟都聚合K线数据
"""

import requests
import sqlite3
import pymysql
import threading
import time
from datetime import datetime, timedelta
import signal
import sys


class SimpleRealtimeSystem:
    """
    简化实时数据系统
    """
    
    def __init__(self):
        # 本地数据库
        self.local_db_path = "hsi_realtime_temp.db"
        self.init_local_db()
        
        # 远程数据库配置
        self.mysql_config = {
            'host': '115.159.44.226',
            'port': 3306,
            'user': 'qihuo',
            'password': 'Hejdf3KdfaTt4h3w',
            'database': 'qihuo',
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # 系统状态
        self.is_running = False
        self.last_aggregated_minute = None
        
        # 采集控制：非交易时段仅做心跳，不写库
        self.collect_out_of_session = False
        self.heartbeat_interval_seconds = 60
        self.fetch_interval_seconds = 5

        # 新浪财经配置
        self.hsi_code = "hf_HSI"
        self.headers = {
            "Referer": "http://finance.sina.com.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # 设置信号处理
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
        # 需要额外聚合的周期（单位：分钟）
        self.extra_periods = [3, 5, 10, 15, 30, 60]
        # 启动增量重建窗口天数
        self.startup_recent_days = 2

    def init_local_db(self):
        """
        初始化本地数据库
        """
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            create_table_sql = """
            CREATE TABLE IF NOT EXISTS temp_hsi_realtime (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                datetime TEXT NOT NULL,
                price REAL NOT NULL,
                volume REAL DEFAULT 0,
                timestamp REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            
            cursor.execute(create_table_sql)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_temp_datetime ON temp_hsi_realtime(datetime)")
            
            conn.commit()
            conn.close()
            
            print(f"✅ 本地数据库初始化成功: {self.local_db_path}")
            
        except Exception as e:
            print(f"❌ 本地数据库初始化失败: {e}")
    
    def is_hsi_trading_time(self, dt):
        """
        判断是否为恒指期货交易时间（香港时间UTC+8）
        交易时间：
        - 日盘：09:15-12:00, 13:00-16:30
        - 夜盘：17:15-次日03:00
        """
        hour = dt.hour
        minute = dt.minute
        
        # 日盘：09:15-12:00
        if hour == 9 and minute >= 15:
            return True
        if hour in [10, 11]:
            return True
        if hour == 12 and minute == 0:
            return True
        
        # 日盘：13:00-16:30
        if hour in [13, 14, 15]:
            return True
        if hour == 16 and minute <= 30:
            return True
        
        # 夜盘：17:15-次日03:00
        if hour == 17 and minute >= 15:
            return True
        if hour in [18, 19, 20, 21, 22, 23]:
            return True
        if hour in [0, 1, 2]:
            return True
        if hour == 3 and minute == 0:
            return True
        
        return False
    
    def fetch_hsi_data(self):
        """
        从新浪财经获取恒指期货数据
        """
        try:
            url = f"http://hq.sinajs.cn/list={self.hsi_code}"
            
            response = requests.get(url, timeout=10, headers=self.headers)
            response.encoding = 'gbk'
            data = response.text
            
            if '"' in data:
                content = data.split('"')[1]
                fields = content.split(',')
                
                if len(fields) >= 8:
                    # 尝试解析价格数据
                    for i, field in enumerate(fields):
                        try:
                            price = float(field)
                            if 20000 <= price <= 30000:  # 恒指期货价格范围
                                return {
                                    'price': price,
                                    'datetime': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                    'success': True
                                }
                        except:
                            continue
            
            return {'success': False, 'error': '无法解析价格数据'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def insert_realtime_data(self, price, volume=0):
        """
        插入实时数据到本地数据库
        """
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            now = datetime.now()
            datetime_str = now.strftime("%Y-%m-%d %H:%M:%S")
            timestamp = now.timestamp()
            
            insert_sql = """
            INSERT INTO temp_hsi_realtime (datetime, price, volume, timestamp)
            VALUES (?, ?, ?, ?)
            """
            
            cursor.execute(insert_sql, (datetime_str, price, volume, timestamp))
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ 插入实时数据失败: {e}")
            return False
    
    def get_minute_data(self, minute_datetime):
        """
        获取指定分钟的数据
        """
        try:
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # 计算时间范围：该分钟的00秒到59秒
            minute_start = minute_datetime  # 2025-09-29 10:16:00
            minute_end = (datetime.strptime(minute_datetime, "%Y-%m-%d %H:%M:%S") + timedelta(minutes=1)).strftime("%Y-%m-%d %H:%M:%S")  # 2025-09-29 10:17:00
            
            query_sql = """
            SELECT datetime, price, volume, timestamp
            FROM temp_hsi_realtime
            WHERE datetime >= ? AND datetime < ?
            ORDER BY timestamp ASC
            """
            
            cursor.execute(query_sql, (minute_start, minute_end))
            results = cursor.fetchall()
            
            conn.close()
            
            data = []
            for row in results:
                data.append({
                    'datetime': row[0],
                    'price': row[1],
                    'volume': row[2],
                    'timestamp': row[3]
                })
            
            return data
            
        except Exception as e:
            print(f"❌ 获取分钟数据失败: {e}")
            return []
    
    def aggregate_minute_data(self, minute_datetime):
        """
        聚合指定分钟的数据为1分钟K线
        """
        try:
            # 获取该分钟内的所有数据
            raw_data = self.get_minute_data(minute_datetime)
            
            if not raw_data:
                print(f"⚠️  {minute_datetime} 没有数据")
                return None
            
            # 按时间排序
            raw_data.sort(key=lambda x: x['timestamp'])
            
            # 计算K线数据
            prices = [item['price'] for item in raw_data]
            volumes = [item['volume'] for item in raw_data]
            
            kline_data = {
                'datetime': minute_datetime,
                'open': prices[0],      # 开盘价（第一笔价格）
                'high': max(prices),    # 最高价
                'low': min(prices),     # 最低价
                'close': prices[-1],    # 收盘价（最后一笔价格）
                'volume': sum(volumes), # 总成交量
                'count': len(raw_data), # 数据条数
                'raw_data': raw_data    # 原始数据
            }
            
            print(f"✅ K线聚合成功: 开盘{prices[0]} 最高{max(prices)} 最低{min(prices)} 收盘{prices[-1]} (共{len(raw_data)}条)")
            return kline_data
            
        except Exception as e:
            print(f"❌ 聚合分钟数据失败: {e}")
            return None
    
    def sync_to_remote(self, kline_data):
        """
        同步K线数据到远程数据库
        """
        try:
            # 确保1分钟表存在
            self.ensure_mysql_table(1)
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO hf_HSI_min1 (datetime, open, high, low, close, volume, code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                code = VALUES(code)
            """
            
            data = (
                kline_data['datetime'],
                kline_data['open'],
                kline_data['high'],
                kline_data['low'],
                kline_data['close'],
                kline_data['volume'],
                'hf_HSI'
            )
            
            cursor.execute(sql, data)
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ 同步到远程数据库失败: {e}")
            return False

    def ensure_mysql_table(self, period_minutes):
        """
        确保远程MySQL存在对应的周期表 hf_HSI_min{N}
        字段与 min1 相同，datetime 唯一键
        """
        try:
            table = f"hf_HSI_min{period_minutes}"
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            create_sql = f"""
            CREATE TABLE IF NOT EXISTS {table} (
                id INT AUTO_INCREMENT PRIMARY KEY,
                datetime DATETIME NOT NULL,
                open DOUBLE,
                high DOUBLE,
                low DOUBLE,
                close DOUBLE,
                volume DOUBLE,
                code VARCHAR(32),
                UNIQUE KEY uniq_datetime (datetime)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            cursor.execute(create_sql)
            conn.close()
        except Exception as e:
            print(f"❌ 创建/检查远程表失败: {e}")

    def mysql_table_exists(self, table_name: str) -> bool:
        """检查远程表是否存在"""
        try:
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            exists = cursor.fetchone() is not None
            conn.close()
            return exists
        except Exception as e:
            print(f"❌ 检查表是否存在失败 {table_name}: {e}")
            return False

    def sync_multi_to_remote(self, period_minutes, kline_data):
        """
        将多分钟聚合K线写入远程 hf_HSI_min{N}
        """
        try:
            table = f"hf_HSI_min{period_minutes}"
            self.ensure_mysql_table(period_minutes)
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            sql = f"""
            INSERT INTO {table} (datetime, open, high, low, close, volume, code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                code = VALUES(code)
            """
            data = (
                kline_data['datetime'],
                kline_data['open'],
                kline_data['high'],
                kline_data['low'],
                kline_data['close'],
                kline_data['volume'],
                'hf_HSI'
            )
            cursor.execute(sql, data)
            conn.close()
            return True
        except Exception as e:
            print(f"❌ 多周期K线写入失败({period_minutes}): {e}")
            return False

    def aggregate_multi_minutes(self, end_minute_dt, period_minutes):
        """
        聚合[end_minute - period_minutes + 1, end_minute]区间的多分钟K线。
        以已有的1分钟聚合（从本地raw聚合）派生：
        - open: 第一有数据分钟的open
        - high: 各分钟high的最大值
        - low: 各分钟low的最小值
        - close: 最后一有数据分钟的close
        - volume: 各分钟volume之和
        """
        try:
            minute_klines = []
            for i in range(period_minutes):
                m_dt = (end_minute_dt - timedelta(minutes=period_minutes - 1 - i))
                m_str = m_dt.strftime("%Y-%m-%d %H:%M:%S")
                k1 = self.aggregate_minute_data(m_str)
                if k1:
                    minute_klines.append(k1)
            if not minute_klines:
                return None
            open_price = None
            high_price = None
            low_price = None
            close_price = None
            total_volume = 0.0
            for idx, k in enumerate(minute_klines):
                if open_price is None:
                    open_price = k['open']
                high_price = k['high'] if high_price is None else max(high_price, k['high'])
                low_price = k['low'] if low_price is None else min(low_price, k['low'])
                close_price = k['close']
                total_volume += float(k.get('volume', 0) or 0)
            return {
                'datetime': end_minute_dt.strftime("%Y-%m-%d %H:%M:%S"),
                'open': open_price,
                'high': high_price,
                'low': low_price,
                'close': close_price,
                'volume': total_volume
            }
        except Exception as e:
            print(f"❌ 多分钟聚合失败({period_minutes}): {e}")
            return None
    
    def startup_full_update(self):
        """
        启动时数据完整性保障：
        - 若远程周期表不存在：全量从本地原始表构建
        - 若已存在：仅重建最近N天（默认2天）并覆盖更新
        """
        try:
            print("📊 第1步：准备分钟时间列表与构建范围...")
            
            # 扫描本地数据库中的所有分钟
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # 全量与增量的起始时间
            cutoff_dt = datetime.now() - timedelta(days=self.startup_recent_days)
            cutoff_str = cutoff_dt.strftime("%Y-%m-%d %H:%M:%S")

            # 统计原始表数量（近N天与全量）
            cursor.execute("SELECT COUNT(*) FROM temp_hsi_realtime")
            total_all = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM temp_hsi_realtime WHERE datetime >= ?", (cutoff_str,))
            total_recent = cursor.fetchone()[0]
            print(f"📊 原始数据量: 全量={total_all} | 近{self.startup_recent_days}天={total_recent}")
            
            # 获取所有不同的分钟（全量）
            cursor.execute(
                """
                SELECT DISTINCT 
                    strftime('%Y-%m-%d %H:%M:00', datetime) as minute_time
                FROM temp_hsi_realtime 
                ORDER BY minute_time ASC
                """
            )
            minute_times_all = cursor.fetchall()

            # 获取近N天分钟
            cursor.execute(
                """
                SELECT DISTINCT 
                    strftime('%Y-%m-%d %H:%M:00', datetime) as minute_time
                FROM temp_hsi_realtime 
                WHERE datetime >= ?
                ORDER BY minute_time ASC
                """,
                (cutoff_str,)
            )
            minute_times_recent = cursor.fetchall()
            
            # 显示扫描到的分钟
            print(f"📊 分钟样例(全量前5条): {[r[0] for r in minute_times_all[:5]]}")
            print(f"📊 分钟样例(近{self.startup_recent_days}天前5条): {[r[0] for r in minute_times_recent[:5]]}")
            
            conn.close()
            
            if not minute_times_all:
                print("ℹ️  本地数据库中没有数据，跳过全量更新")
                return
            
            print(f"📊 全量分钟数={len(minute_times_all)} | 近{self.startup_recent_days}天分钟数={len(minute_times_recent)}")
            
            # 决定min1构建范围：若远程min1不存在→全量；存在→近N天
            min1_table = 'hf_HSI_min1'
            min1_exists = self.mysql_table_exists(min1_table)
            minute_times_for_min1 = minute_times_all if not min1_exists else minute_times_recent
            print(f"📊 第2步：处理 {min1_table}（存在={min1_exists}） | 目标分钟数={len(minute_times_for_min1)}")
            
            kline_list = []
            for minute_row in minute_times_for_min1:
                minute_time = minute_row[0]
                
                # 聚合该分钟的数据
                kline_data = self.aggregate_minute_data(minute_time)
                
                if kline_data:
                    kline_list.append(kline_data)
                    print(f"✅ 聚合 {minute_time}: 开盘{kline_data['open']} 最高{kline_data['high']} 最低{kline_data['low']} 收盘{kline_data['close']}")
            
            if not kline_list:
                print("ℹ️  没有有效的K线数据需要更新")
                return
            
            print(f"📊 第3步：批量更新到远程数据库 (min1)...")
            
            # 批量更新到远程数据库
            success_count = self.batch_sync_to_remote(kline_list)
            
            print(f"🎉 启动时min1更新完成！")
            print(f"📊 min1 聚合K线: {len(kline_list)} 条")
            print(f"📊 min1 更新成功: {success_count} 条")

            # 多周期批量聚合与更新
            periods = [3, 5, 10, 15, 30, 60]
            for p in periods:
                table_p = f'hf_HSI_min{p}'
                exists_p = self.mysql_table_exists(table_p)
                # 选择边界分钟来源：全量或近N天
                boundary_source = minute_times_all if not exists_p else minute_times_recent
                print(f"\n📊 第4步：批量聚合并更新到远程数据库 ({table_p})，存在={exists_p} 目标边界数={len(boundary_source)}...")
                # 对分钟时间点进行周期边界过滤：只在周期边界生成结束K线
                boundary_minutes = []
                for minute_row in boundary_source:
                    minute_time = minute_row[0]
                    dt = datetime.strptime(minute_time, "%Y-%m-%d %H:%M:%S")
                    if dt.minute % p == 0:
                        boundary_minutes.append(dt)
                multi_k_list = []
                for end_dt in boundary_minutes:
                    mk = self.aggregate_multi_minutes(end_dt, p)
                    if mk:
                        multi_k_list.append(mk)
                        print(f"✅ 聚合 min{p} {mk['datetime']}: O{mk['open']} H{mk['high']} L{mk['low']} C{mk['close']}")
                if not multi_k_list:
                    print(f"ℹ️  min{p} 无可更新数据")
                    continue
                # 批量写入
                succ = self.batch_sync_multi_to_remote(p, multi_k_list)
                print(f"🎉 启动时min{p}更新完成！")
                print(f"📊 min{p} 聚合K线: {len(multi_k_list)} 条")
                print(f"📊 min{p} 更新成功: {succ} 条")
            
        except Exception as e:
            print(f"❌ 启动时全量更新失败: {e}")
            import traceback
            traceback.print_exc()
    
    def batch_sync_to_remote(self, kline_list):
        """
        批量同步K线数据到远程数据库
        """
        try:
            # 确保1分钟表存在
            self.ensure_mysql_table(1)
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            
            sql = """
            INSERT INTO hf_HSI_min1 (datetime, open, high, low, close, volume, code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                code = VALUES(code)
            """
            
            data_list = []
            for kline_data in kline_list:
                data_list.append((
                    kline_data['datetime'],
                    kline_data['open'],
                    kline_data['high'],
                    kline_data['low'],
                    kline_data['close'],
                    kline_data['volume'],
                    'hf_HSI'
                ))
            
            cursor.executemany(sql, data_list)
            conn.close()
            
            print(f"✅ 批量同步完成: {len(kline_list)} 条K线数据")
            return len(kline_list)
            
        except Exception as e:
            print(f"❌ 批量同步到远程数据库失败: {e}")
            return 0

    def batch_sync_multi_to_remote(self, period_minutes, kline_list):
        """
        批量同步多周期K线数据到远程数据库 hf_HSI_min{N}
        """
        try:
            table = f"hf_HSI_min{period_minutes}"
            self.ensure_mysql_table(period_minutes)
            conn = pymysql.connect(**self.mysql_config)
            cursor = conn.cursor()
            sql = f"""
            INSERT INTO {table} (datetime, open, high, low, close, volume, code)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open = VALUES(open),
                high = VALUES(high),
                low = VALUES(low),
                close = VALUES(close),
                volume = VALUES(volume),
                code = VALUES(code)
            """
            data_list = []
            for k in kline_list:
                data_list.append((
                    k['datetime'],
                    k['open'],
                    k['high'],
                    k['low'],
                    k['close'],
                    k['volume'],
                    'hf_HSI'
                ))
            cursor.executemany(sql, data_list)
            conn.close()
            print(f"✅ 批量同步完成(min{period_minutes}): {len(kline_list)} 条K线数据")
            return len(kline_list)
        except Exception as e:
            print(f"❌ 批量同步到远程数据库失败(min{period_minutes}): {e}")
            return 0
    
    def start_system(self):
        """
        启动系统
        """
        if self.is_running:
            print("⚠️  系统已在运行中")
            return
        
        print("=" * 80)
        print("🚀 启动简化实时数据系统")
        print("=" * 80)
        
        # 启动时数据完整性保障
        print("\n🔧 启动时数据完整性保障...")
        self.startup_full_update()
        
        self.is_running = True
        
        # 启动数据获取线程
        fetch_thread = threading.Thread(target=self._fetch_loop)
        fetch_thread.daemon = True
        fetch_thread.start()
        
        # 启动聚合线程
        aggregate_thread = threading.Thread(target=self._aggregate_loop)
        aggregate_thread.daemon = True
        aggregate_thread.start()
        
        print(f"\n✅ 系统启动成功！")
        print(f"📊 数据获取间隔: 5 秒")
        print(f"📊 K线聚合: 每分钟的00秒时聚合上一分钟数据")
    
    def stop_system(self):
        """
        停止系统
        """
        self.is_running = False
        print("🛑 系统已停止")
    
    def _fetch_loop(self):
        """
        数据获取循环
        """
        while self.is_running:
            try:
                now = datetime.now()
                # 非交易时段：仅心跳不写库
                if not self.is_hsi_trading_time(now):
                    hb = self.fetch_hsi_data()
                    stamp = now.strftime('%H:%M:%S')
                    if hb['success']:
                        print(f"💓 心跳 {stamp} 网络正常，价格={hb['price']}")
                    else:
                        print(f"💓 心跳 {stamp} 网络异常: {hb['error']}")
                    time.sleep(self.heartbeat_interval_seconds)
                    continue

                # 交易时段：正常5秒采集与落库
                data = self.fetch_hsi_data()
                if data['success']:
                    price = data['price']
                    success = self.insert_realtime_data(price)
                    if success:
                        current_minute = now.strftime("%M")
                        print(f"✅ {data['datetime']}: 价格 {price} 已存储 | 当前分钟: {current_minute}")
                    else:
                        print(f"❌ {data['datetime']}: 价格 {price} 存储失败")
                else:
                    print(f"❌ 获取数据失败: {data['error']}")
                time.sleep(self.fetch_interval_seconds)
                
            except Exception as e:
                print(f"❌ 数据获取循环出错: {e}")
                time.sleep(self.fetch_interval_seconds)
    
    def _aggregate_loop(self):
        """
        聚合循环
        """
        while self.is_running:
            try:
                current_time = datetime.now()
                current_minute = current_time.replace(second=0, microsecond=0)
                
                # 检测分钟变化
                if current_minute != self.last_aggregated_minute:
                    print(f"🕐 {current_time.strftime('%H:%M:%S')} - 检测到新分钟，开始聚合...")
                    self.last_aggregated_minute = current_minute
                    
                    # 聚合上一分钟的数据
                    target_minute = current_minute - timedelta(minutes=1)
                    target_minute_str = target_minute.strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 检查是否为交易时间
                    if not self.is_hsi_trading_time(target_minute):
                        print(f"⏰ {target_minute_str} 为停牌时间，跳过数据聚合")
                        continue
                    
                    print(f"🔄 聚合 {target_minute_str} 的数据...")
                    
                    kline_data = self.aggregate_minute_data(target_minute_str)
                    
                    if kline_data:
                        print(f"🔄 开始同步到远程数据库...")
                        success = self.sync_to_remote(kline_data)
                        
                        if success:
                            print(f"\n🎉 {current_time.strftime('%H:%M:%S')} - 1分钟K线已成功写入远程数据库!")
                            print(f"   📊 时间: {kline_data['datetime']}")
                            print(f"   📊 开盘: {kline_data['open']} | 最高: {kline_data['high']} | 最低: {kline_data['low']} | 收盘: {kline_data['close']}")
                            print(f"   📊 成交量: {kline_data['volume']} | 数据条数: {kline_data['count']}")
                            print(f"   ✅ 远程数据库更新成功!\n")
                            # 在边界分钟触发多周期聚合与写入（以上一分钟为结束）
                            try:
                                end_dt = datetime.strptime(kline_data['datetime'], "%Y-%m-%d %H:%M:%S")
                                end_minute = end_dt
                                minute_val = end_minute.minute
                                for p in self.extra_periods:
                                    if minute_val % p == 0:
                                        mk = self.aggregate_multi_minutes(end_minute, p)
                                        if mk:
                                            ok = self.sync_multi_to_remote(p, mk)
                                            if ok:
                                                print(f"   ✅ 已写入远程 hf_HSI_min{p}: {mk['datetime']}")
                                            else:
                                                print(f"   ❌ 写入远程 hf_HSI_min{p} 失败: {mk['datetime']}")
                            except Exception as e:
                                print(f"❌ 多周期聚合/写入流程异常: {e}")
                        else:
                            print(f"❌ {current_time.strftime('%H:%M:%S')} - K线数据同步失败")
                    else:
                        print(f"ℹ️  {current_time.strftime('%H:%M:%S')} - {target_minute_str} 无数据")
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                print(f"❌ 聚合循环出错: {e}")
                time.sleep(5)
    
    def _signal_handler(self, signum, frame):
        """
        信号处理器
        """
        print(f"\n📡 收到信号 {signum}，正在安全关闭系统...")
        self.stop_system()
        sys.exit(0)


def main():
    """
    主函数
    """
    print("🚀 简化实时数据系统")
    print("确保每分钟都有准确的1分钟K线数据")
    print("=" * 80)
    
    # 创建系统实例
    system = SimpleRealtimeSystem()
    
    try:
        # 启动系统
        system.start_system()
        
        # 主循环
        while True:
            try:
                time.sleep(30)  # 每30秒打印一次状态
                
            except KeyboardInterrupt:
                print(f"\n📡 收到中断信号，正在安全关闭系统...")
                break
                
    except Exception as e:
        print(f"❌ 系统运行出错: {e}")
    
    finally:
        # 停止系统
        system.stop_system()
        print(f"\n🎉 系统已安全关闭")


if __name__ == "__main__":
    main()
