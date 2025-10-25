#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通达信API数据测试脚本
测试各种K线类型的数据字段
"""

from pytdx.hq import TdxHq_API
import pandas as pd
import time

def test_pytdx_kline_data():
    """测试通达信API的各种K线数据"""
    
    # 创建API实例
    api = TdxHq_API()
    
    # 测试股票代码（平安银行）
    test_code = '000001'
    market = 0  # 深圳市场
    
    # K线类型映射 - 根据官方文档修正
    kline_types = {
        '日K线': {'category': 4, 'name': '日K线'},  # 修正：日K线是4
        '周K线': {'category': 5, 'name': '周K线'},
        '月K线': {'category': 6, 'name': '月K线'},
        '季K线': {'category': 10, 'name': '季K线'},
        '年K线': {'category': 11, 'name': '年K线'}
    }
    
    print("=== 通达信API K线数据测试 ===\n")
    
    # 连接服务器
    servers = [
        ('121.36.81.195', 7709),
    ]
    
    connected = False
    for host, port in servers:
        print(f"尝试连接服务器: {host}:{port}")
        if api.connect(host, port):
            print(f"✅ 连接成功: {host}:{port}")
            connected = True
            break
        else:
            print(f"❌ 连接失败: {host}:{port}")
    
    if not connected:
        print("❌ 所有服务器连接失败")
        return
    
    try:
        # 测试每种K线类型
        for kline_name, kline_info in kline_types.items():
            print(f"\n{'='*50}")
            print(f"测试 {kline_name} (category={kline_info['category']})")
            print(f"{'='*50}")
            
            try:
                # 获取K线数据 - 使用正确的API方法和参数顺序
                # get_security_bars(category, market, stockcode, start, count)
                data = api.get_security_bars(kline_info['category'], market, test_code, 0, 5)
                
                if data and len(data) > 0:
                    print(f"✅ 成功获取到 {len(data)} 条数据")
                    
                    # 打印第一条数据的字段
                    first_record = data[0]
                    print(f"\n📊 数据字段结构:")
                    print(f"{'字段名':<15} {'类型':<10} {'示例值':<20}")
                    print("-" * 50)
                    
                    for key, value in first_record.items():
                        value_str = str(value)[:18] + "..." if len(str(value)) > 18 else str(value)
                        print(f"{key:<15} {type(value).__name__:<10} {value_str:<20}")
                    
                    # 转换为DataFrame查看
                    df = pd.DataFrame(data)
                    print(f"\n📋 完整数据预览:")
                    print(df.head())
                    
                    # 检查关键字段是否存在 - 修正字段名
                    key_fields = ['open', 'high', 'low', 'close', 'vol', 'amount']  # vol而不是volume
                    missing_fields = []
                    
                    for field in key_fields:
                        if field in df.columns:
                            print(f"✅ {field}: 存在")
                        else:
                            print(f"❌ {field}: 缺失")
                            missing_fields.append(field)
                    
                    if missing_fields:
                        print(f"\n⚠️  缺失关键字段: {missing_fields}")
                    else:
                        print(f"\n✅ 所有关键字段都存在")
                        
                else:
                    print(f"❌ 未获取到数据")
                    
            except Exception as e:
                print(f"❌ 获取 {kline_name} 数据时出错: {e}")
            
            # 等待一下，避免请求过于频繁
            time.sleep(1)
        
        # 额外测试：获取股票基本信息
        print(f"\n{'='*50}")
        print("测试股票基本信息")
        print(f"{'='*50}")
        
        try:
            # 获取股票列表
            stock_list = api.get_security_list(market, 0)
            if stock_list:
                print(f"✅ 成功获取股票列表，共 {len(stock_list)} 只股票")
                print(f"前5只股票:")
                for i, stock in enumerate(stock_list[:5]):
                    print(f"  {i+1}. {stock}")
            else:
                print("❌ 获取股票列表失败")
        except Exception as e:
            print(f"❌ 获取股票列表时出错: {e}")
            
    finally:
        # 断开连接
        api.disconnect()
        print(f"\n🔌 已断开连接")

def test_volume_and_turnover():
    """专门测试成交量和换手率字段"""
    
    print(f"\n{'='*60}")
    print("专门测试成交量和换手率字段")
    print(f"{'='*60}")
    
    api = TdxHq_API()
    
    # 使用相同的服务器地址
    if api.connect('121.36.81.195', 7709):
        try:
            # 测试股票
            test_codes = ['000001', '600000']  # 平安银行、浦发银行
            
            for code in test_codes:
                market = 0 if code.startswith('00') else 1
                print(f"\n测试股票: {code} (市场: {'深圳' if market == 0 else '上海'})")
                
                # 获取日K线数据 - 使用正确的API方法
                data = api.get_security_bars(4, market, code, 0, 3)  # 日K线category=4
                
                if data:
                    print(f"日K线数据字段:")
                    for key, value in data[0].items():
                        print(f"  {key}: {value}")
                    
                    # 检查是否有换手率相关字段
                    df = pd.DataFrame(data)
                    turnover_fields = [col for col in df.columns if 'turn' in col.lower() or '换手' in col]
                    if turnover_fields:
                        print(f"✅ 发现换手率相关字段: {turnover_fields}")
                    else:
                        print("❌ 未发现换手率字段")
                        
                time.sleep(1)
                
        finally:
            api.disconnect()

def test_turnover_calculation():
    """测试换手率计算方案"""
    
    print(f"\n{'='*60}")
    print("测试换手率计算方案")
    print(f"{'='*60}")
    
    api = TdxHq_API()
    
    if api.connect('121.36.81.195', 7709):
        try:
            test_code = '000001'
            market = 0
            
            # 获取日K线数据
            data = api.get_security_bars(4, market, test_code, 0, 5)
            
            if data:
                df = pd.DataFrame(data)
                print(f"获取到 {len(df)} 条日K线数据")
                
                # 计算换手率
                # 换手率 = 成交量 / 流通股本 * 100%
                # 这里需要获取流通股本信息
                
                print(f"\n📊 数据示例:")
                for i, row in df.head().iterrows():
                    print(f"日期: {row['datetime']}")
                    print(f"  开盘: {row['open']}, 收盘: {row['close']}")
                    print(f"  最高: {row['high']}, 最低: {row['low']}")
                    print(f"  成交量: {row['vol']:,} 手")
                    print(f"  成交额: {row['amount']:,} 元")
                    print()
                
                # 尝试获取股票基本信息来计算换手率
                print("尝试获取股票基本信息...")
                
                # 获取股票列表中的详细信息
                stock_list = api.get_security_list(market, 0)
                if stock_list:
                    # 查找目标股票
                    target_stock = None
                    for stock in stock_list:
                        if stock.get('code') == test_code:
                            target_stock = stock
                            break
                    
                    if target_stock:
                        print(f"股票信息: {target_stock}")
                        # 这里可以进一步处理换手率计算
                    else:
                        print(f"未找到股票 {test_code} 的详细信息")
                        
        finally:
            api.disconnect()

if __name__ == "__main__":
    print("开始测试通达信API数据...")
    test_pytdx_kline_data()
    test_volume_and_turnover()
    test_turnover_calculation()
    print("\n测试完成！") 