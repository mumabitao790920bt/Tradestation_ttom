#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BaoStock 季度和年度数据合成器
基于月线数据合成季度和年度K线数据，并精确计算换手率
"""

import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import os
from concurrent.futures import ThreadPoolExecutor

class BaoStockQuarterlyYearlySynthesizer:
    def __init__(self):
        self.data_folder = r'gupiao_baostock'
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        # 字段映射 - 基于baostock_data_collector_final.py的成功经验
        self.fields_mapping = {
            'd': "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,psTTM,pcfNcfTTM,pbMRQ,isST",
            'w': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg",
            'm': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg"
        }
        
    def login_baostock(self):
        """登录BaoStock系统"""
        lg = bs.login()
        if lg.error_code != '0':
            print(f'登录失败: {lg.error_code} - {lg.error_msg}')
            return False
        print('BaoStock登录成功')
        return True
    
    def logout_baostock(self):
        """登出BaoStock系统"""
        bs.logout()
        print('BaoStock已登出')
    
    def get_monthly_data(self, code, start_date='1990-01-01'):
        """获取月线数据"""
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        fields = self.fields_mapping['m']
        
        print(f"正在获取 {code} 的月线数据...")
        
        try:
            rs = bs.query_history_k_data_plus(
                code,
                fields,
                start_date=start_date,
                end_date=end_date,
                frequency='m',
                adjustflag="3"  # 不复权
            )
            
            if rs.error_code != '0':
                print(f"获取 {code} 月线数据失败: {rs.error_code} - {rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            print(f"获取到 {len(data_list)} 条月线数据")
            return data_list
            
        except Exception as e:
            print(f"获取 {code} 月线数据异常: {e}")
            return []
    
    def get_circulating_shares_history(self, code):
        """获取流通股本历史数据"""
        print(f"正在获取 {code} 的流通股本历史数据...")
        
        circulating_shares_data = {}
        
        try:
            # 获取当前年份和季度
            current_year = datetime.datetime.now().year
            current_quarter = (datetime.datetime.now().month - 1) // 3 + 1
            
            # 获取最近几年的流通股本数据
            for year in range(current_year - 5, current_year + 1):
                for quarter in range(1, 5):
                    try:
                        rs = bs.query_profit_data(code=code, year=year, quarter=quarter)
                        
                        if rs.error_code == '0':
                            while rs.next():
                                data = rs.get_row_data()
                                if len(data) >= 8:  # 确保有足够的数据
                                    date_key = f"{year}Q{quarter}"
                                    liqa_share = float(data[7]) if data[7] else 0  # liqaShare字段
                                    circulating_shares_data[date_key] = liqa_share
                                    print(f"  {date_key}: {liqa_share:,.0f} 股")
                        
                        time.sleep(0.1)  # 避免请求过于频繁
                        
                    except Exception as e:
                        print(f"  获取 {year}Q{quarter} 数据失败: {e}")
                        continue
            
            print(f"获取到 {len(circulating_shares_data)} 个季度的流通股本数据")
            return circulating_shares_data
            
        except Exception as e:
            print(f"获取流通股本历史数据异常: {e}")
            return {}
    
    def synthesize_quarterly_data(self, monthly_data, circulating_shares):
        """合成季度K线数据"""
        print("开始合成季度K线数据...")
        
        quarterly_data = []
        
        for i in range(0, len(monthly_data), 3):
            if i + 2 < len(monthly_data):
                # 取3个月数据
                three_months = monthly_data[i:i+3]
                
                # 解析第一个月的日期来确定季度
                first_month_date = three_months[0][0]  # 日期字符串
                date_obj = datetime.datetime.strptime(first_month_date, '%Y-%m-%d')
                year = date_obj.year
                quarter = (date_obj.month - 1) // 3 + 1
                quarter_key = f"{year}Q{quarter}"
                
                # 合成基础数据
                quarter_open = float(three_months[0][2])  # 第一个月开盘价
                quarter_high = max(float(m[3]) for m in three_months)  # 3个月最高价
                quarter_low = min(float(m[4]) for m in three_months)   # 3个月最低价
                quarter_close = float(three_months[2][5])  # 第三个月收盘价
                quarter_volume = sum(float(m[6]) for m in three_months)  # 成交量之和
                quarter_amount = sum(float(m[7]) for m in three_months)  # 成交额之和
                
                # 获取流通股本
                circulating_share = circulating_shares.get(quarter_key, 0)
                
                # 计算换手率
                turnover_rate = 0
                if circulating_share > 0:
                    turnover_rate = (quarter_volume / circulating_share) * 100
                
                # 构建季度数据
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
                print(f"  合成季度: {quarter_key}, 换手率: {turnover_rate:.2f}%")
        
        print(f"成功合成 {len(quarterly_data)} 个季度数据")
        return quarterly_data
    
    def synthesize_yearly_data(self, monthly_data, circulating_shares):
        """合成年度K线数据"""
        print("开始合成年度K线数据...")
        
        yearly_data = []
        
        for i in range(0, len(monthly_data), 12):
            if i + 11 < len(monthly_data):
                # 取12个月数据
                twelve_months = monthly_data[i:i+12]
                
                # 解析第一个月的日期来确定年份
                first_month_date = twelve_months[0][0]  # 日期字符串
                date_obj = datetime.datetime.strptime(first_month_date, '%Y-%m-%d')
                year = date_obj.year
                year_key = str(year)
                
                # 合成基础数据
                year_open = float(twelve_months[0][2])  # 第一个月开盘价
                year_high = max(float(m[3]) for m in twelve_months)  # 12个月最高价
                year_low = min(float(m[4]) for m in twelve_months)   # 12个月最低价
                year_close = float(twelve_months[11][5])  # 第十二个月收盘价
                year_volume = sum(float(m[6]) for m in twelve_months)  # 成交量之和
                year_amount = sum(float(m[7]) for m in twelve_months)  # 成交额之和
                
                # 获取年度流通股本（使用第四季度数据）
                year_circulating_share = 0
                for quarter in range(1, 5):
                    quarter_key = f"{year}Q{quarter}"
                    if quarter_key in circulating_shares:
                        year_circulating_share = circulating_shares[quarter_key]
                        break
                
                # 计算换手率
                turnover_rate = 0
                if year_circulating_share > 0:
                    turnover_rate = (year_volume / year_circulating_share) * 100
                
                # 构建年度数据
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
                print(f"  合成年度: {year_key}, 换手率: {turnover_rate:.2f}%")
        
        print(f"成功合成 {len(yearly_data)} 个年度数据")
        return yearly_data
    
    def save_synthesized_data(self, code, quarterly_data, yearly_data):
        """保存合成的数据到数据库"""
        db_path = os.path.join(self.data_folder, f"{code}_synthesized_data.db")
        conn = sqlite3.connect(db_path)
        
        try:
            cursor = conn.cursor()
            
            # 创建季度数据表
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
            
            # 创建年度数据表
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
            print(f"数据保存完成: {db_path}")
            
        except Exception as e:
            print(f"保存数据时出错: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def synthesize_single_stock(self, stock_code, stock_name):
        """合成单只股票的季度和年度数据"""
        print(f"\n开始合成 {stock_name}({stock_code}) 的季度和年度数据...")
        
        try:
            # 1. 获取月线数据
            monthly_data = self.get_monthly_data(stock_code)
            if not monthly_data:
                print(f"未获取到 {stock_code} 的月线数据")
                return
            
            # 2. 获取流通股本历史数据
            circulating_shares = self.get_circulating_shares_history(stock_code)
            
            # 3. 合成季度数据
            quarterly_data = self.synthesize_quarterly_data(monthly_data, circulating_shares)
            
            # 4. 合成年度数据
            yearly_data = self.synthesize_yearly_data(monthly_data, circulating_shares)
            
            # 5. 保存数据
            self.save_synthesized_data(stock_code, quarterly_data, yearly_data)
            
            print(f"{stock_name}({stock_code}) 合成完成！")
            print(f"  季度数据: {len(quarterly_data)} 条")
            print(f"  年度数据: {len(yearly_data)} 条")
            
        except Exception as e:
            print(f"合成 {stock_code} 数据时发生错误: {e}")

def main():
    """主函数"""
    synthesizer = BaoStockQuarterlyYearlySynthesizer()
    
    print("=== BaoStock 季度和年度数据合成器 ===")
    print("基于月线数据合成季度和年度K线数据，并精确计算换手率")
    
    # 登录BaoStock
    if not synthesizer.login_baostock():
        return
    
    try:
        # 测试股票列表
        test_stocks = [
            {'code': 'sh.600000', 'name': '浦发银行'},
            {'code': 'sz.000001', 'name': '平安银行'},
            {'code': 'sh.600036', 'name': '招商银行'}
        ]
        
        print("\n开始合成测试股票数据...")
        
        for stock in test_stocks:
            synthesizer.synthesize_single_stock(stock['code'], stock['name'])
            time.sleep(2)  # 避免请求过于频繁
        
        print("\n所有测试股票合成完成！")
        
    finally:
        synthesizer.logout_baostock()

if __name__ == "__main__":
    main() 