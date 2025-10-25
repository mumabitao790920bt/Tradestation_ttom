#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
"""

import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import threading

class BaoStockCompleteDataCollectorV2:
    def __init__(self):
        self.data_folder = r'gupiao_lssj'
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        # 修正后的时间周期映射 - 根据API文档，只支持d、w、m
        self.frequency_mapping = {
            'daily': {'level': 4, 'frequency': 'd', 'table': 'daily_data'},
            'weekly': {'level': 5, 'frequency': 'w', 'table': 'weekly_data'},
            'monthly': {'level': 6, 'frequency': 'm', 'table': 'monthly_data'}

        }
        
        # 不同频率的字段映射 - 根据API文档
        self.fields_mapping = {
            'd': "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,psTTM,pcfNcfTTM,pbMRQ,isST",  # 日线包含preclose
            'w': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg",  # 周线不包含preclose
            'm': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg"   # 月线不包含preclose
        }
        
    def login_baostock(self):
        """登录lssj系统"""
        lg = bs.login()
        if lg.error_code != '0':
            print(f'登录失败: {lg.error_code} - {lg.error_msg}')
            return False
        print('lssj登录成功')
        return True
    
    def logout_baostock(self):
        """登出lssj系统"""
        bs.logout()
        print('lssj已登出')
    
    def check_and_update_table_structure(self, conn, table_name):
        """检查并更新数据库表结构，自动添加缺失字段"""
        cursor = conn.cursor()
        
        try:
            # 获取当前表的所有列
            cursor.execute(f"PRAGMA table_info({table_name})")
            existing_columns = {row[1] for row in cursor.fetchall()}
            
            # 定义完整的字段映射
            field_mapping = {
                'date': 'TEXT',
                'code': 'TEXT', 
                'open': 'REAL',
                'high': 'REAL',
                'low': 'REAL',
                'close': 'REAL',
                'preclose': 'REAL',
                'volume': 'REAL',
                'amount': 'REAL',
                'adjustflag': 'TEXT',
                'turn': 'REAL',
                'tradestatus': 'TEXT',
                'pctChg': 'REAL',
                'peTTM': 'REAL',
                'psTTM': 'REAL',
                'pcfNcfTTM': 'REAL',
                'pbMRQ': 'REAL',
                'isST': 'TEXT'
            }
            
            # 检查并添加缺失的字段
            missing_columns = []
            for field, field_type in field_mapping.items():
                if field not in existing_columns:
                    missing_columns.append((field, field_type))
            
            if missing_columns:
                print(f"表 {table_name} 需要添加 {len(missing_columns)} 个字段")
                for field, field_type in missing_columns:
                    try:
                        alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {field} {field_type}"
                        cursor.execute(alter_sql)
                        print(f"  添加字段: {field} ({field_type})")
                    except Exception as e:
                        print(f"  添加字段 {field} 失败: {e}")
                
                conn.commit()
                print(f"表 {table_name} 结构更新完成")
            else:
                print(f"表 {table_name} 结构已是最新")
                
        except Exception as e:
            print(f"检查表结构时出错: {e}")
        finally:
            cursor.close()
    
    def create_database_tables(self, conn):
        """创建数据库表 - 根据API文档完整字段"""
        cursor = conn.cursor()
        
        # 创建基础K线数据表
        for period_name, period_info in self.frequency_mapping.items():
            table_name = period_info['table']
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            table_exists = cursor.fetchone() is not None
            
            if not table_exists:
                # 创建新表
                create_table_sql = f"""
                CREATE TABLE {table_name} (
                    date TEXT,
                    code TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    preclose REAL,
                    volume REAL,
                    amount REAL,
                    adjustflag TEXT,
                    turn REAL,
                    tradestatus TEXT,
                    pctChg REAL,
                    peTTM REAL,
                    psTTM REAL,
                    pcfNcfTTM REAL,
                    pbMRQ REAL,
                    isST TEXT,
                    PRIMARY KEY (date, code)
                )
                """
                cursor.execute(create_table_sql)
                print(f"创建表 {table_name} 完成")
            else:
                # 检查并更新现有表结构
                self.check_and_update_table_structure(conn, table_name)
        
        # 创建数据表（季度、年度）
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quarterly_data (
                date TEXT,
                code TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                turnover_rate REAL,
                circulating_shares REAL,
                quarter TEXT,
                PRIMARY KEY (date, code)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS yearly_data (
                date TEXT,
                code TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                turnover_rate REAL,
                circulating_shares REAL,
                year TEXT,
                PRIMARY KEY (date, code)
            )
        """)
        
        conn.commit()
        cursor.close()
        print("数据库表创建/更新完成（包含完整字段）")
    
    def get_stock_history_data(self, code, frequency_info, start_date='1990-01-01', max_retries=3):
        """获取单只股票的历史数据 - 包含重试机制"""
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 根据频率选择对应的字段
        frequency = frequency_info['frequency']
        fields = self.fields_mapping.get(frequency, self.fields_mapping['d'])
        
        print(f"正在获取 {code} 的 {frequency} 数据...")
        
        for attempt in range(max_retries):
            try:
                # 查询历史数据
                rs = bs.query_history_k_data_plus(
                    code,
                    fields,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    adjustflag="3"  # 不复权
                )
                
                if rs.error_code != '0':
                    print(f"获取 {code} {frequency} 数据失败 (尝试 {attempt+1}/{max_retries}): {rs.error_code} - {rs.error_msg}")
                    if attempt < max_retries - 1:
                        time.sleep(1)  # 等待1秒后重试
                        continue
                    else:
                        return []
                
                data_list = []
                while (rs.error_code == '0') & rs.next():
                    data_list.append(rs.get_row_data())
                
                print(f"获取到 {len(data_list)} 条 {frequency} 数据")
                return data_list
                
            except Exception as e:
                print(f"获取 {code} {frequency} 数据异常 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # 等待1秒后重试
                    continue
                else:
                    return []
        
        return []
    
    def process_and_save_data(self, conn, code, data_list, table_name, frequency):
        """处理并保存数据到数据库 - 根据频率处理不同字段"""
        if not data_list:
            print(f"{code} {table_name} 没有数据需要保存")
            return 0
        
        cursor = conn.cursor()
        batch_data = []
        
        for data in data_list:
            try:
                # 根据频率处理不同数量的字段
                if frequency == 'd':  # 日线数据 - 18个字段
                    date_str = data[0] if len(data) > 0 else ''
                    code_str = data[1] if len(data) > 1 else code
                    open_price = float(data[2]) if len(data) > 2 and data[2] else 0
                    high_price = float(data[3]) if len(data) > 3 and data[3] else 0
                    low_price = float(data[4]) if len(data) > 4 and data[4] else 0
                    close_price = float(data[5]) if len(data) > 5 and data[5] else 0
                    preclose_price = float(data[6]) if len(data) > 6 and data[6] else 0
                    volume = float(data[7]) if len(data) > 7 and data[7] else 0
                    amount = float(data[8]) if len(data) > 8 and data[8] else 0
                    adjustflag = data[9] if len(data) > 9 else '3'
                    turn = float(data[10]) if len(data) > 10 and data[10] else 0
                    tradestatus = data[11] if len(data) > 11 else '1'
                    pctChg = float(data[12]) if len(data) > 12 and data[12] else 0
                    peTTM = float(data[13]) if len(data) > 13 and data[13] else 0
                    psTTM = float(data[14]) if len(data) > 14 and data[14] else 0
                    pcfNcfTTM = float(data[15]) if len(data) > 15 and data[15] else 0
                    pbMRQ = float(data[16]) if len(data) > 16 and data[16] else 0
                    isST = data[17] if len(data) > 17 else '0'
                    
                    batch_data.append([
                        date_str, code_str, open_price, high_price, low_price, 
                        close_price, preclose_price, volume, amount, adjustflag,
                        turn, tradestatus, pctChg, peTTM, psTTM, pcfNcfTTM, 
                        pbMRQ, isST
                    ])
                    
                else:  # 周线和月线数据 - 11个字段
                    date_str = data[0] if len(data) > 0 else ''
                    code_str = data[1] if len(data) > 1 else code
                    open_price = float(data[2]) if len(data) > 2 and data[2] else 0
                    high_price = float(data[3]) if len(data) > 3 and data[3] else 0
                    low_price = float(data[4]) if len(data) > 4 and data[4] else 0
                    close_price = float(data[5]) if len(data) > 5 and data[5] else 0
                    volume = float(data[6]) if len(data) > 6 and data[6] else 0
                    amount = float(data[7]) if len(data) > 7 and data[7] else 0
                    adjustflag = data[8] if len(data) > 8 else '3'
                    turn = float(data[9]) if len(data) > 9 and data[9] else 0
                    pctChg = float(data[10]) if len(data) > 10 and data[10] else 0
                    
                    # 周线和月线不包含的字段设为默认值
                    preclose_price = 0
                    tradestatus = '1'
                    peTTM = 0
                    psTTM = 0
                    pcfNcfTTM = 0
                    pbMRQ = 0
                    isST = '0'
                    
                    batch_data.append([
                        date_str, code_str, open_price, high_price, low_price, 
                        close_price, preclose_price, volume, amount, adjustflag,
                        turn, tradestatus, pctChg, peTTM, psTTM, pcfNcfTTM, 
                        pbMRQ, isST
                    ])
                
            except (ValueError, IndexError) as e:
                print(f"处理数据时出错: {e}, 数据: {data}")
                continue
        
        # 批量插入数据
        if batch_data:
            insert_query = f"""
            INSERT OR REPLACE INTO {table_name} 
            (date, code, open, high, low, close, preclose, volume, amount, 
             adjustflag, turn, tradestatus, pctChg, peTTM, psTTM, pcfNcfTTM, 
             pbMRQ, isST) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            try:
                cursor.executemany(insert_query, batch_data)
                conn.commit()
                print(f"{code} {table_name} 数据保存完成，共 {len(batch_data)} 条记录")
                return len(batch_data)
            except Exception as e:
                print(f"保存数据时出错: {e}")
                conn.rollback()
                return 0
        
        cursor.close()
        return 0
    
    def get_circulating_shares_history(self, code, monthly_data):
        """获取流通股本历史数据 - 完全版：前后都用最近的实际数据填充，支持增量更新"""
        print(f"正在获取 {code} 的流通股本历史数据...")
        if not monthly_data:
            print("没有月K线数据，无法确定时间范围")
            return {}
        
        # 1. 解析所有需要的季度
        first_month = monthly_data[0][0]
        last_month = monthly_data[-1][0]
        first_date = datetime.datetime.strptime(first_month, '%Y-%m-%d')
        last_date = datetime.datetime.strptime(last_month, '%Y-%m-%d')
        start_year = first_date.year
        end_year = last_date.year
        
        # 生成所有需要的季度key，按顺序
        all_quarters = []
        for year in range(start_year, end_year + 1):
            for quarter in range(1, 5):
                # 检查季度是否在月K线时间范围内
                quarter_end_month = 3 * quarter
                quarter_date = datetime.datetime(year, quarter_end_month, 1)
                quarter_start_date = datetime.datetime(year, 3 * (quarter - 1) + 1, 1)
                if quarter_date < first_date or quarter_start_date > last_date:
                    continue
                all_quarters.append(f"{year}Q{quarter}")
        
        # 2. 获取所有实际有数据的季度流通股本
        actual_data = {}
        for year in range(start_year, end_year + 2):  # +2保证覆盖未来季度
            for quarter in range(1, 5):
                date_key = f"{year}Q{quarter}"
                try:
                    rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
                    if rs.error_code == '0':
                        while rs.next():
                            data = rs.get_row_data()
                            if len(data) >= 11:
                                liqa_share_str = data[10]
                                if liqa_share_str and liqa_share_str != '' and liqa_share_str != 'None':
                                    try:
                                        liqa_share = float(liqa_share_str)
                                        if liqa_share > 0:
                                            actual_data[date_key] = liqa_share
                                            # print(f"  {date_key}: {liqa_share:,.0f} 股 (实际数据)")
                                    except (ValueError, TypeError):
                                        continue
                    time.sleep(0.05)
                except Exception as e:
                    print(f"  获取 {date_key} 数据失败: {e}")
                    continue
        
        # 3. 按顺序为所有需要的季度填充数据
        circulating_shares_data = {}
        sorted_actual = sorted(actual_data.items())
        actual_quarters = [q for q, _ in sorted_actual]
        actual_quarters_sorted = sorted(actual_quarters)
        
        for q in all_quarters:
            if q in actual_data:
                circulating_shares_data[q] = actual_data[q]
            else:
                # 找到距离q最近的实际数据
                before = [aq for aq in actual_quarters_sorted if aq < q]
                after = [aq for aq in actual_quarters_sorted if aq > q]
                if before and after:
                    # 取最近的一个
                    nearest = before[-1] if (q > before[-1]) else after[0]
                elif before:
                    nearest = before[-1]
                elif after:
                    nearest = after[0]
                else:
                    nearest = None
                if nearest:
                    circulating_shares_data[q] = actual_data[nearest]
                    # print(f"  {q}: 使用最近的 {nearest} 数据 {actual_data[nearest]:,.0f} 股 (填充)")
                else:
                    circulating_shares_data[q] = 0
                    print(f"  {q}: 无法获取流通股本，填充为0")
        print(f"最终生成 {len(circulating_shares_data)} 个季度的流通股本数据")
        return circulating_shares_data
    
    def get_latest_circulating_shares(self, code):
        """获取最新流通股本数据作为备用"""
        print(f"正在获取 {code} 的最新流通股本数据...")
        
        try:
            # 尝试获取最新的财务数据
            current_year = datetime.datetime.now().year
            current_quarter = (datetime.datetime.now().month - 1) // 3 + 1
            
            # 尝试最近几个季度
            for year in range(current_year, current_year - 2, -1):
                for quarter in range(4, 0, -1):
                    if year == current_year and quarter > current_quarter:
                        continue
                    
                    try:
                        rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
                        
                        if rs.error_code == '0':
                            while rs.next():
                                data = rs.get_row_data()
                                
                                if len(data) >= 11:
                                    liqa_share_str = data[10]  # 修正：使用索引10
                                    if liqa_share_str and liqa_share_str != '' and liqa_share_str != 'None':
                                        try:
                                            liqa_share = float(liqa_share_str)
                                            if liqa_share > 0:
                                                # 使用这个值作为所有季度的默认值
                                                default_data = {}
                                                for y in range(2003, current_year + 1):
                                                    for q in range(1, 5):
                                                        if y == current_year and q > current_quarter:
                                                            continue
                                                        default_data[f"{y}Q{q}"] = liqa_share
                                                
                                                print(f"  使用 {year}Q{quarter} 的流通股本 {liqa_share:,.0f} 作为默认值")
                                                return default_data
                                        except (ValueError, TypeError):
                                            continue
                        
                        time.sleep(0.1)
                        
                    except Exception as e:
                        print(f"  备用方法获取 {year}Q{quarter} 失败: {e}")
                        continue
            
            print("无法获取有效的流通股本数据，将使用默认值")
            return {}
            
        except Exception as e:
            print(f"备用方法异常: {e}")
            return {}
    
    def synthesize_quarterly_data(self, monthly_data, circulating_shares):
        """季度K线数据"""
        print("开始合季度K线数据...")
        
        quarterly_data = []
        
        for i in range(0, len(monthly_data), 3):
            if i + 2 < len(monthly_data):
                three_months = monthly_data[i:i+3]
                
                first_month_date = three_months[0][0]
                date_obj = datetime.datetime.strptime(first_month_date, '%Y-%m-%d')
                year = date_obj.year
                quarter = (date_obj.month - 1) // 3 + 1
                quarter_key = f"{year}Q{quarter}"
                
                quarter_open = float(three_months[0][2])
                quarter_high = max(float(m[3]) for m in three_months)
                quarter_low = min(float(m[4]) for m in three_months)
                quarter_close = float(three_months[2][5])
                quarter_volume = sum(float(m[6]) for m in three_months)
                quarter_amount = sum(float(m[7]) for m in three_months)
                
                circulating_share = circulating_shares.get(quarter_key, 0)
                
                turnover_rate = 0
                if circulating_share > 0:
                    turnover_rate = (quarter_volume / circulating_share) * 100
                
                quarter_data = {
                    'date': first_month_date,
                    'code': three_months[0][1],
                    'open': quarter_open,
                    'high': quarter_high,
                    'low': quarter_low,
                    'close': quarter_close,
                    'volume': quarter_volume,
                    'amount': quarter_amount,
                    'turnover_rate': turnover_rate,
                    'circulating_shares': circulating_share,
                    'quarter': quarter_key
                }
                
                quarterly_data.append(quarter_data)
                print(f"  季度: {quarter_key}, 换手率: {turnover_rate:.2f}%")
        
        print(f"成功 {len(quarterly_data)} 个季度数据")
        return quarterly_data
    
    def synthesize_yearly_data(self, monthly_data, circulating_shares):
        """年度K线数据"""
        print("开始年度K线数据...")
        
        yearly_data = []
        
        for i in range(0, len(monthly_data), 12):
            if i + 11 < len(monthly_data):
                twelve_months = monthly_data[i:i+12]
                
                first_month_date = twelve_months[0][0]
                date_obj = datetime.datetime.strptime(first_month_date, '%Y-%m-%d')
                year = date_obj.year
                year_key = str(year)
                
                year_open = float(twelve_months[0][2])
                year_high = max(float(m[3]) for m in twelve_months)
                year_low = min(float(m[4]) for m in twelve_months)
                year_close = float(twelve_months[11][5])
                year_volume = sum(float(m[6]) for m in twelve_months)
                year_amount = sum(float(m[7]) for m in twelve_months)
                
                year_circulating_share = 0
                for quarter in range(1, 5):
                    quarter_key = f"{year}Q{quarter}"
                    if quarter_key in circulating_shares:
                        year_circulating_share = circulating_shares[quarter_key]
                        break
                
                turnover_rate = 0
                if year_circulating_share > 0:
                    turnover_rate = (year_volume / year_circulating_share) * 100
                
                year_data = {
                    'date': first_month_date,
                    'code': twelve_months[0][1],
                    'open': year_open,
                    'high': year_high,
                    'low': year_low,
                    'close': year_close,
                    'volume': year_volume,
                    'amount': year_amount,
                    'turnover_rate': turnover_rate,
                    'circulating_shares': year_circulating_share,
                    'year': year_key
                }
                
                yearly_data.append(year_data)
                print(f"  年度: {year_key}, 换手率: {turnover_rate:.2f}%")
        
        print(f"成功 {len(yearly_data)} 个年度数据")
        return yearly_data
    
    def save_synthesized_data(self, conn, code, quarterly_data, yearly_data):
        """保存的数据到数据库"""
        cursor = conn.cursor()
        
        # 保存季度数据
        if quarterly_data:
            quarter_values = [
                (d['date'], d['code'], d['open'], d['high'], d['low'], d['close'],
                d['volume'], d['amount'], d['turnover_rate'], d['circulating_shares'], d['quarter'])
                for d in quarterly_data
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO quarterly_data 
                (date, code, open, high, low, close, volume, amount, turnover_rate, circulating_shares, quarter)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, quarter_values)
            print(f"保存 {len(quarterly_data)} 条季度数据")
        
        # 保存年度数据
        if yearly_data:
            year_values = [
                (d['date'], d['code'], d['open'], d['high'], d['low'], d['close'],
                d['volume'], d['amount'], d['turnover_rate'], d['circulating_shares'], d['year'])
                for d in yearly_data
            ]
            cursor.executemany("""
                INSERT OR REPLACE INTO yearly_data 
                (date, code, open, high, low, close, volume, amount, turnover_rate, circulating_shares, year)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, year_values)
            print(f"保存 {len(yearly_data)} 条年度数据")
        
        conn.commit()
        cursor.close()
    
    def collect_complete_stock_data(self, stock_code, stock_name):
        """采集单只股票的完整数据"""
        print(f"\n{'='*60}")
        print(f"开始采集 {stock_name}({stock_code}) 的完整数据")
        print(f"{'='*60}")
        
        # 创建数据库连接
        db_path = os.path.join(self.data_folder, f"{stock_code}_complete_data.db")
        conn = sqlite3.connect(db_path)
        
        try:
            # 创建数据库表
            self.create_database_tables(conn)
            
            # 1. 采集基础K线数据（日线、周线、月线）
            for period_name, period_info in self.frequency_mapping.items():
                print(f"\n--- 处理{period_name}数据 ---")
                
                # 获取历史数据
                data_list = self.get_stock_history_data(stock_code, period_info)
                
                # 保存数据
                saved_count = self.process_and_save_data(conn, stock_code, data_list, period_info['table'], period_info['frequency'])
                
                if saved_count > 0:
                    print(f"{period_name}数据采集完成，保存 {saved_count} 条记录")
                else:
                    print(f"{period_name}数据采集失败或无新数据")
                
                time.sleep(1)  # 避免请求过于频繁
            
            # 2. 季度和年度数据
            print(f"\n--- 季度和年度数据 ---")
            
            # 获取月线数据用于
            monthly_data = self.get_stock_history_data(stock_code, self.frequency_mapping['monthly'])
            if not monthly_data:
                print("未获取到月线数据，无法季度和年度数据")
                return
            
            # 获取流通股本数据 - 传递月K线数据以确定时间范围
            circulating_shares = self.get_circulating_shares_history(stock_code, monthly_data)
            
            # 季度数据
            quarterly_data = self.synthesize_quarterly_data(monthly_data, circulating_shares)
            
            # 年度数据
            yearly_data = self.synthesize_yearly_data(monthly_data, circulating_shares)
            
            # 保存数据
            self.save_synthesized_data(conn, stock_code, quarterly_data, yearly_data)
            
            print(f"\n{stock_name}({stock_code}) 完整数据采集完成！")
            print(f"数据保存到: {db_path}")
            
        except Exception as e:
            print(f"采集 {stock_code} 数据时发生错误: {e}")
        finally:
            conn.close()

def main():
    """主函数"""
    collector = BaoStockCompleteDataCollectorV2()
    
    print("=== lssj 完整数据采集器 V2 ===")
    print("一体化采集：日线、周线、月线 + 季度、年度")
    print("支持数据补全更新和跳过已存在数据")
    
    # 登录lssj
    if not collector.login_baostock():
        return
    
    try:
        while True:
            print("\n" + "="*50)
            stock_code = input("请输入股票代码 (例如: sh.600000 或 sz.000001): ").strip()
            
            if not stock_code:
                print("股票代码不能为空")
                continue
            
            if stock_code.lower() == 'quit' or stock_code.lower() == 'exit':
                break
            
            stock_name = input("请输入股票名称: ").strip()
            if not stock_name:
                stock_name = stock_code
            
            # 开始采集数据
            collector.collect_complete_stock_data(stock_code, stock_name)
            
            print("\n" + "="*50)
            continue_input = input("是否继续采集其他股票? (y/n): ").strip().lower()
            if continue_input not in ['y', 'yes', '是']:
                break
    
    finally:
        collector.logout_baostock()
        print("\n程序结束")

if __name__ == "__main__":
    main() 