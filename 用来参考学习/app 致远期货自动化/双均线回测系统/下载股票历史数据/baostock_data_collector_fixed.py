import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import threading

class BaoStockDataCollectorFixed:
    def __init__(self):
        self.data_folder = r'gupiao_baostock'
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
        # 修正后的时间周期映射 - 根据API文档，只支持d、w、m
        self.frequency_mapping = {
            'daily': {'level': 4, 'frequency': 'd', 'table': 'daily_data'},
            'weekly': {'level': 5, 'frequency': 'w', 'table': 'weekly_data'},
            'monthly': {'level': 6, 'frequency': 'm', 'table': 'monthly_data'}
            # 注意：BaoStock API不支持季度和年K线
        }
        
        # 数据库字段
        self.fields = ['time', 'high', 'low', 'open', 'close', 'vol', 'code']
        
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
    
    def get_all_stock_codes(self):
        """获取所有A股股票代码"""
        print("正在获取所有A股股票代码...")
        
        # 获取当前日期
        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        try:
            # 获取所有股票信息
            rs = bs.query_all_stock(day=current_date)
            
            if rs.error_code != '0':
                print(f"获取股票列表失败: {rs.error_code} - {rs.error_msg}")
                return []
            
            stock_list = []
            
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                code = stock_data[0]  # 股票代码
                name = stock_data[1]  # 股票名称
                market = stock_data[2]  # 交易所
                
                # 只获取A股股票（上海和深圳）
                if code.startswith('sh.') or code.startswith('sz.'):
                    stock_list.append({
                        'code': code,
                        'name': name,
                        'market': market
                    })
            
            print(f"共获取到 {len(stock_list)} 只A股股票")
            return stock_list
            
        except Exception as e:
            print(f"获取股票代码时发生异常: {e}")
            return []
    
    def create_database_tables(self, conn):
        """创建数据库表"""
        cursor = conn.cursor()
        
        for period_name, period_info in self.frequency_mapping.items():
            table_name = period_info['table']
            create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                time DATETIME,
                high FLOAT,
                low FLOAT,
                open FLOAT,
                close FLOAT,
                vol FLOAT,
                code TEXT,
                PRIMARY KEY (time, code)
            )
            """
            cursor.execute(create_table_sql)
        
        conn.commit()
        cursor.close()
        print("数据库表创建完成")
    
    def get_stock_history_data(self, code, frequency_info, start_date='1990-01-01'):
        """获取单只股票的历史数据"""
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        
        # 构建查询字段 - 日、周、月数据使用相同字段
        fields = "date,code,open,high,low,close,volume,amount,adjustflag"
        
        print(f"正在获取 {code} 的 {frequency_info['frequency']} 数据...")
        
        # 查询历史数据
        rs = bs.query_history_k_data_plus(
            code,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency_info['frequency'],
            adjustflag="3"  # 不复权
        )
        
        if rs.error_code != '0':
            print(f"获取 {code} {frequency_info['frequency']} 数据失败: {rs.error_code} - {rs.error_msg}")
            return []
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        print(f"获取到 {len(data_list)} 条 {frequency_info['frequency']} 数据")
        return data_list
    
    def process_and_save_data(self, conn, code, data_list, table_name):
        """处理并保存数据到数据库"""
        if not data_list:
            print(f"{code} {table_name} 没有数据需要保存")
            return
        
        cursor = conn.cursor()
        batch_data = []
        
        for data in data_list:
            try:
                # 处理时间格式 - 日、周、月数据
                date_str = data[0]
                time_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                
                # 格式化时间
                time_formatted = time_obj.strftime('%Y-%m-%d %H:%M:%S')
                
                # 提取数据
                open_price = float(data[3]) if data[3] else 0
                high_price = float(data[4]) if data[4] else 0
                low_price = float(data[5]) if data[5] else 0
                close_price = float(data[6]) if data[6] else 0
                volume = float(data[7]) if data[7] else 0
                
                batch_data.append([
                    time_formatted,
                    high_price,
                    low_price,
                    open_price,
                    close_price,
                    volume,
                    code
                ])
                
            except (ValueError, IndexError) as e:
                print(f"处理数据时出错: {e}, 数据: {data}")
                continue
        
        # 批量插入数据
        if batch_data:
            insert_query = f"INSERT OR REPLACE INTO {table_name} (time, high, low, open, close, vol, code) VALUES (?, ?, ?, ?, ?, ?, ?)"
            try:
                cursor.executemany(insert_query, batch_data)
                conn.commit()
                print(f"{code} {table_name} 数据保存完成，共 {len(batch_data)} 条记录")
            except Exception as e:
                print(f"保存数据时出错: {e}")
                conn.rollback()
        
        cursor.close()
    
    def collect_single_stock_data(self, stock_info):
        """采集单只股票的所有周期数据"""
        code = stock_info['code']
        name = stock_info['name']
        
        print(f"开始采集 {name}({code}) 的历史数据...")
        
        # 创建数据库连接
        db_path = os.path.join(self.data_folder, f"{code}_data.db")
        conn = sqlite3.connect(db_path)
        
        try:
            # 创建数据库表
            self.create_database_tables(conn)
            
            # 采集各个周期的数据
            for period_name, period_info in self.frequency_mapping.items():
                print(f"正在采集 {code} 的{period_name}数据...")
                
                # 获取历史数据
                data_list = self.get_stock_history_data(code, period_info)
                
                # 保存数据
                self.process_and_save_data(conn, code, data_list, period_info['table'])
                
                # 避免请求过于频繁
                time.sleep(0.1)
            
            print(f"{name}({code}) 数据采集完成")
            
        except Exception as e:
            print(f"采集 {code} 数据时发生错误: {e}")
        finally:
            conn.close()
    
    def collect_all_stocks_data(self, max_workers=3):
        """批量采集所有股票数据"""
        # 登录BaoStock
        if not self.login_baostock():
            return
        
        try:
            # 获取所有股票代码
            stock_list = self.get_all_stock_codes()
            
            if not stock_list:
                print("未获取到股票列表，请检查网络连接")
                return
            
            # 保存股票列表到CSV
            df_stocks = pd.DataFrame(stock_list)
            df_stocks.to_csv('all_stocks_baostock.csv', index=False, encoding='utf-8-sig')
            print("股票列表已保存到 all_stocks_baostock.csv")
            
            # 使用线程池批量采集
            print(f"开始批量采集数据，使用 {max_workers} 个线程...")
            
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = []
                for stock in stock_list:
                    future = executor.submit(self.collect_single_stock_data, stock)
                    futures.append(future)
                
                # 等待所有任务完成
                completed = 0
                for future in futures:
                    try:
                        future.result()
                        completed += 1
                        print(f"进度: {completed}/{len(stock_list)}")
                    except Exception as e:
                        print(f"任务执行出错: {e}")
            
            print("所有股票数据采集完成！")
            
        finally:
            # 登出BaoStock
            self.logout_baostock()

def main():
    """主函数"""
    collector = BaoStockDataCollectorFixed()
    
    print("=== BaoStock A股历史数据采集工具 (修正版) ===")
    print("1. 采集所有股票数据")
    print("2. 采集指定股票数据")
    print("3. 仅获取股票代码列表")
    
    choice = input("请选择操作 (1/2/3): ").strip()
    
    if choice == "1":
        print("开始采集所有A股历史数据...")
        collector.collect_all_stocks_data()
        
    elif choice == "2":
        stock_code = input("请输入股票代码 (例如: sh.600000): ").strip()
        stock_name = input("请输入股票名称: ").strip()
        
        if not collector.login_baostock():
            return
        
        try:
            stock_info = {'code': stock_code, 'name': stock_name}
            collector.collect_single_stock_data(stock_info)
        finally:
            collector.logout_baostock()
            
    elif choice == "3":
        print("正在获取股票代码列表...")
        if collector.login_baostock():
            stock_list = collector.get_all_stock_codes()
            if stock_list:
                df = pd.DataFrame(stock_list)
                df.to_csv('stock_list_baostock.csv', index=False, encoding='utf-8-sig')
                print(f"已保存 {len(stock_list)} 只股票代码到 stock_list_baostock.csv")
            collector.logout_baostock()
        
    else:
        print("无效选择")

if __name__ == "__main__":
    main() 