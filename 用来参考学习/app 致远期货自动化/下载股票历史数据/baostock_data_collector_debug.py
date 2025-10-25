import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import os

class BaoStockDataCollectorDebug:
    def __init__(self):
        self.data_folder = r'gupiao_baostock'
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)
        
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
    
    def debug_stock_data(self, code, frequency='d'):
        """调试单只股票的数据结构"""
        end_date = datetime.datetime.now().strftime('%Y-%m-%d')
        start_date = '2024-01-01'  # 只获取最近的数据用于调试
        
        # 根据频率选择对应的字段
        fields = self.fields_mapping.get(frequency, self.fields_mapping['d'])
        
        print(f"=== 调试 {code} 的 {frequency} 数据 ===")
        print(f"请求字段: {fields}")
        print(f"字段数量: {len(fields.split(','))}")
        
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
                print(f"获取数据失败: {rs.error_code} - {rs.error_msg}")
                return
            
            data_list = []
            while (rs.error_code == '0') & rs.next():
                data_list.append(rs.get_row_data())
            
            if data_list:
                print(f"获取到 {len(data_list)} 条数据")
                print(f"第一条数据字段数量: {len(data_list[0])}")
                print(f"第一条数据内容: {data_list[0]}")
                
                # 显示字段映射
                field_names = fields.split(',')
                print("\n字段映射:")
                for i, field in enumerate(field_names):
                    if i < len(data_list[0]):
                        print(f"  {i}: {field} = {data_list[0][i]}")
                    else:
                        print(f"  {i}: {field} = (缺失)")
                
                # 保存到CSV文件进行详细检查
                df = pd.DataFrame(data_list, columns=field_names)
                csv_filename = f"debug_{code}_{frequency}_data.csv"
                df.to_csv(csv_filename, index=False, encoding='utf-8-sig')
                print(f"\n详细数据已保存到: {csv_filename}")
                
            else:
                print("未获取到数据")
                
        except Exception as e:
            print(f"调试时发生异常: {e}")

def main():
    """主函数"""
    debugger = BaoStockDataCollectorDebug()
    
    print("=== BaoStock 数据调试工具 ===")
    
    if not debugger.login_baostock():
        return
    
    try:
        # 调试中信证券的数据
        stock_code = "sh.600030"
        
        # 调试日线数据
        debugger.debug_stock_data(stock_code, 'd')
        print("\n" + "="*50 + "\n")
        
        # 调试周线数据
        debugger.debug_stock_data(stock_code, 'w')
        print("\n" + "="*50 + "\n")
        
        # 调试月线数据
        debugger.debug_stock_data(stock_code, 'm')
        
    finally:
        debugger.logout_baostock()

if __name__ == "__main__":
    main() 