import baostock as bs
import pandas as pd
import datetime
import time

def test_stock_list_retrieval():
    """测试获取股票列表的不同方法"""
    
    print("=== BaoStock 股票列表获取测试 ===")
    
    # 登录BaoStock
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败: {lg.error_code} - {lg.error_msg}')
        return
    
    print('BaoStock登录成功')
    
    # 测试不同的日期
    test_dates = [
        datetime.datetime.now().strftime('%Y-%m-%d'),  # 当前日期
        '2024-12-19',  # 最近的交易日
        '2024-12-18',  # 另一个可能的交易日
        '2024-12-17',  # 再往前一天
        '2024-12-16',  # 周一
        '2024-12-15',  # 周日
        '2024-12-14',  # 周六
    ]
    
    for test_date in test_dates:
        print(f"\n--- 测试日期: {test_date} ---")
        
        try:
            # 获取股票列表
            rs = bs.query_all_stock(day=test_date)
            
            if rs.error_code != '0':
                print(f"错误: {rs.error_code} - {rs.error_msg}")
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
            
            print(f"获取到 {len(stock_list)} 只A股股票")
            
            if len(stock_list) > 0:
                print("前5只股票示例:")
                for i, stock in enumerate(stock_list[:5]):
                    print(f"  {i+1}. {stock['code']} - {stock['name']}")
                
                # 保存成功的股票列表
                df = pd.DataFrame(stock_list)
                filename = f'stock_list_{test_date.replace("-", "")}.csv'
                df.to_csv(filename, index=False, encoding='utf-8-sig')
                print(f"股票列表已保存到 {filename}")
                break
                
        except Exception as e:
            print(f"测试日期 {test_date} 时发生异常: {e}")
    
    # 测试其他获取股票的方法
    print("\n=== 测试其他获取股票的方法 ===")
    
    # 方法1: 获取上证50成分股
    print("\n1. 获取上证50成分股:")
    try:
        rs = bs.query_sz50_stocks(date='2024-12-19')
        sz50_stocks = []
        while (rs.error_code == '0') & rs.next():
            sz50_stocks.append(rs.get_row_data())
        
        if sz50_stocks:
            print(f"获取到 {len(sz50_stocks)} 只上证50成分股")
            for i, stock in enumerate(sz50_stocks[:3]):
                print(f"  {i+1}. {stock}")
        else:
            print("未获取到上证50成分股")
    except Exception as e:
        print(f"获取上证50成分股时发生异常: {e}")
    
    # 方法2: 获取沪深300成分股
    print("\n2. 获取沪深300成分股:")
    try:
        rs = bs.query_hs300_stocks(date='2024-12-19')
        hs300_stocks = []
        while (rs.error_code == '0') & rs.next():
            hs300_stocks.append(rs.get_row_data())
        
        if hs300_stocks:
            print(f"获取到 {len(hs300_stocks)} 只沪深300成分股")
            for i, stock in enumerate(hs300_stocks[:3]):
                print(f"  {i+1}. {stock}")
        else:
            print("未获取到沪深300成分股")
    except Exception as e:
        print(f"获取沪深300成分股时发生异常: {e}")
    
    # 方法3: 获取中证500成分股
    print("\n3. 获取中证500成分股:")
    try:
        rs = bs.query_zz500_stocks(date='2024-12-19')
        zz500_stocks = []
        while (rs.error_code == '0') & rs.next():
            zz500_stocks.append(rs.get_row_data())
        
        if zz500_stocks:
            print(f"获取到 {len(zz500_stocks)} 只中证500成分股")
            for i, stock in enumerate(zz500_stocks[:3]):
                print(f"  {i+1}. {stock}")
        else:
            print("未获取到中证500成分股")
    except Exception as e:
        print(f"获取中证500成分股时发生异常: {e}")
    
    # 登出BaoStock
    bs.logout()
    print("\nBaoStock已登出")

def get_stock_list_with_fallback():
    """使用备用方法获取股票列表"""
    
    print("=== 使用备用方法获取股票列表 ===")
    
    # 登录BaoStock
    lg = bs.login()
    if lg.error_code != '0':
        print(f'登录失败: {lg.error_code} - {lg.error_msg}')
        return []
    
    print('BaoStock登录成功')
    
    all_stocks = []
    
    # 方法1: 尝试不同的日期
    test_dates = ['2024-12-19', '2024-12-18', '2024-12-17', '2024-12-16']
    
    for date in test_dates:
        print(f"尝试日期: {date}")
        try:
            rs = bs.query_all_stock(day=date)
            
            if rs.error_code == '0':
                stock_list = []
                while (rs.error_code == '0') & rs.next():
                    stock_data = rs.get_row_data()
                    code = stock_data[0]
                    name = stock_data[1]
                    market = stock_data[2]
                    
                    if code.startswith('sh.') or code.startswith('sz.'):
                        stock_list.append({
                            'code': code,
                            'name': name,
                            'market': market
                        })
                
                if stock_list:
                    print(f"成功获取到 {len(stock_list)} 只股票 (日期: {date})")
                    all_stocks = stock_list
                    break
                else:
                    print(f"日期 {date} 未获取到股票")
            else:
                print(f"日期 {date} 查询失败: {rs.error_code} - {rs.error_msg}")
                
        except Exception as e:
            print(f"日期 {date} 发生异常: {e}")
    
    # 方法2: 如果方法1失败，尝试组合成分股
    if not all_stocks:
        print("\n尝试组合成分股获取股票列表...")
        
        try:
            # 获取上证50
            rs = bs.query_sz50_stocks(date='2024-12-19')
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                if stock_data[0].startswith('sh.') or stock_data[0].startswith('sz.'):
                    all_stocks.append({
                        'code': stock_data[0],
                        'name': stock_data[1],
                        'market': '上证50'
                    })
            
            # 获取沪深300
            rs = bs.query_hs300_stocks(date='2024-12-19')
            while (rs.error_code == '0') & rs.next():
                stock_data = rs.get_row_data()
                if stock_data[0].startswith('sh.') or stock_data[0].startswith('sz.'):
                    all_stocks.append({
                        'code': stock_data[0],
                        'name': stock_data[1],
                        'market': '沪深300'
                    })
            
            # 获取中证500
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
            
            all_stocks = unique_stocks
            print(f"通过成分股获取到 {len(all_stocks)} 只股票")
            
        except Exception as e:
            print(f"获取成分股时发生异常: {e}")
    
    # 登出BaoStock
    bs.logout()
    print("BaoStock已登出")
    
    return all_stocks

if __name__ == "__main__":
    print("选择测试方法:")
    print("1. 测试不同日期获取股票列表")
    print("2. 使用备用方法获取股票列表")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        test_stock_list_retrieval()
    elif choice == "2":
        stocks = get_stock_list_with_fallback()
        if stocks:
            df = pd.DataFrame(stocks)
            df.to_csv('stock_list_fallback.csv', index=False, encoding='utf-8-sig')
            print(f"\n成功获取 {len(stocks)} 只股票，已保存到 stock_list_fallback.csv")
        else:
            print("\n未能获取到股票列表")
    else:
        print("无效选择") 