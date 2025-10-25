import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import os
import csv
from concurrent.futures import ThreadPoolExecutor
import threading

class BaoStockDataCollectorFinal:
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
        
        # 不同频率的字段映射 - 根据API文档
        self.fields_mapping = {
            'd': "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,psTTM,pcfNcfTTM,pbMRQ,isST",  # 日线包含preclose
            'w': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg",  # 周线不包含preclose
            'm': "date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg"   # 月线不包含preclose
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
    
    def get_all_stock_codes(self):
        """获取所有A股股票代码 - 修正版"""
        print("正在获取所有A股股票代码...")
        
        # 首先尝试从已保存的文件读取
        if os.path.exists('stock_list_20241219.csv'):
            print("从已保存的文件读取股票列表...")
            
            # 尝试多种编码格式
            encodings = ['utf-8-sig', 'utf-8', 'gbk', 'gb2312', 'big5', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv('stock_list_20241219.csv', encoding=encoding)
                    stock_list = df.to_dict('records')
                    if stock_list:
                        print(f"使用 {encoding} 编码成功读取到 {len(stock_list)} 只股票")
                        return stock_list
                except Exception as e:
                    print(f"使用 {encoding} 编码读取失败: {e}")
                    continue
            
            print("所有编码格式都无法读取文件，将重新获取股票列表")
        
        # 尝试不同的日期来获取股票列表
        test_dates = [
            '2024-12-19',  # 最近的交易日
            '2024-12-18',  # 另一个可能的交易日
            '2024-12-17',  # 再往前一天
            '2024-12-16',  # 周一
            datetime.datetime.now().strftime('%Y-%m-%d'),  # 当前日期
        ]
        
        for date in test_dates:
            print(f"尝试日期: {date}")
            try:
                # 获取所有股票信息
                rs = bs.query_all_stock(day=date)
                
                if rs.error_code != '0':
                    print(f"日期 {date} 查询失败: {rs.error_code} - {rs.error_msg}")
                    continue
                
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
                
                if stock_list:
                    print(f"成功获取到 {len(stock_list)} 只A股股票 (日期: {date})")
                    # 保存股票列表到CSV（使用utf-8-sig编码）
                    df_stocks = pd.DataFrame(stock_list)
                    df_stocks.to_csv('stock_list_20241219.csv', index=False, encoding='utf-8-sig')
                    print("股票列表已保存到 stock_list_20241219.csv")
                    return stock_list
                else:
                    print(f"日期 {date} 未获取到股票")
                    
            except Exception as e:
                print(f"日期 {date} 发生异常: {e}")
        
        # 如果所有日期都失败，尝试备用方法
        print("\n尝试备用方法：通过成分股获取股票列表...")
        return self.get_stock_codes_from_index()
    
    def get_stock_codes_from_index(self):
        """通过成分股获取股票列表"""
        all_stocks = []
        
        try:
            # 获取上证50成分股
            print("获取上证50成分股...")
            rs = bs.query_sz50_stocks(date='2024-12-19')
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                if stock_data[0].startswith('sh.') or stock_data[0].startswith('sz.'):
                    all_stocks.append({
                        'code': stock_data[0],
                        'name': stock_data[1],
                        'market': '上证50'
                    })
            
            # 获取沪深300成分股
            print("获取沪深300成分股...")
            rs = bs.query_hs300_stocks(date='2024-12-19')
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                if stock_data[0].startswith('sh.') or stock_data[0].startswith('sz.'):
                    all_stocks.append({
                        'code': stock_data[0],
                        'name': stock_data[1],
                        'market': '沪深300'
                    })
            
            # 获取中证500成分股
            print("获取中证500成分股...")
            rs = bs.query_zz500_stocks(date='2024-12-19')
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                if stock_data[0].startswith('sh.') or stock_data[0].startswith('sz.'):
                    all_stocks.append({
                        'code': stock_data[0],
                        'name': stock_data[1],
                        'market': '中证500'
                    })
            
            # 去重
            seen_codes = set()
            unique_stocks = []
            for stock in all_stocks:
                if stock['code'] not in seen_codes:
                    unique_stocks.append(stock)
                    seen_codes.add(stock['code'])
            
            print(f"通过成分股获取到 {len(unique_stocks)} 只股票")
            return unique_stocks
            
        except Exception as e:
            print(f"获取成分股时发生异常: {e}")
            return []
    
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
                        time.sleep(1)  # 等待2秒后重试
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
                    time.sleep(1)  # 等待2秒后重试
                    continue
                else:
                    return []
        
        return []
    
    def process_and_save_data(self, conn, code, data_list, table_name, frequency):
        """处理并保存数据到数据库 - 根据频率处理不同字段"""
        if not data_list:
            print(f"{code} {table_name} 没有数据需要保存")
            return
        
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
                self.process_and_save_data(conn, code, data_list, period_info['table'], period_info['frequency'])
                
                # 避免请求过于频繁
                time.sleep(1)  # 增加等待时间到1秒
            
            print(f"{name}({code}) 数据采集完成")
            
        except Exception as e:
            print(f"采集 {code} 数据时发生错误: {e}")
        finally:
            conn.close()
    
    def collect_all_stocks_data(self, max_workers=1):  # 改为单线程
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
            df_stocks.to_csv('all_stocks_baostock_final.csv', index=False, encoding='utf-8-sig')
            print("股票列表已保存到 all_stocks_baostock_final.csv")
            
            # 单线程顺序采集
            print(f"开始顺序采集数据，共 {len(stock_list)} 只股票...")
            
            completed = 0
            for stock in stock_list:
                try:
                    print(f"\n进度: {completed+1}/{len(stock_list)} - 正在采集 {stock['name']}({stock['code']})")
                    self.collect_single_stock_data(stock)
                    completed += 1
                    
                    # 每采集10只股票后稍作休息
                    if completed % 10 == 0:
                        print(f"已采集 {completed} 只股票，休息5秒...")
                        time.sleep(5)
                    else:
                        # 每只股票之间稍作休息
                        time.sleep(1)
                        
                except Exception as e:
                    print(f"采集 {stock['code']} 时发生错误: {e}")
                    continue
            
            print(f"\n所有股票数据采集完成！共成功采集 {completed} 只股票")
            
        finally:
            # 登出BaoStock
            self.logout_baostock()

def main():
    """主函数"""
    collector = BaoStockDataCollectorFinal()
    
    print("=== BaoStock A股历史数据采集工具 (最终修正版) ===")
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
                df.to_csv('stock_list_baostock_final.csv', index=False, encoding='utf-8-sig')
                print(f"已保存 {len(stock_list)} 只股票代码到 stock_list_baostock_final.csv")
            else:
                print("未能获取到股票列表")
            collector.logout_baostock()
        
    else:
        print("无效选择")

if __name__ == "__main__":
    main() 