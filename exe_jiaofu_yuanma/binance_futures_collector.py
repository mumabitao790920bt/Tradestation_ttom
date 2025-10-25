#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
币安永续合约数据收集器
获取BTCUSDT永续合约价格数据
"""

from binance_data_collector import BinanceDataCollector
import time


def main():
    """主函数 - 永续合约数据收集"""
    print("📊 币安永续合约数据收集器")
    print("=" * 60)
    
    # 创建永续合约数据收集器
    collector = BinanceDataCollector(
        db_path="binance_futures_data.db",
        symbol="BTCUSDT",
        use_futures=True  # 使用永续合约API
    )
    
    try:
        # 开始收集所有时间周期的数据
        collector.start_collection()
        
        # 持续运行
        print("\n⏰ 永续合约数据收集持续运行中... (按Ctrl+C停止)")
        print("📋 每轮收集流程:")
        print("   1. 依次处理 1m, 3m, 5m, 10m(合成), 15m, 30m, 1h")
        print("   2. 每次获取200条数据")
        print("   3. 自动去重写入数据库")
        print("   4. 每轮完成后显示各表最新5条数据")
        print("   5. 每分钟执行一轮")
        print("📁 数据存储到: binance_futures_data.db")
        
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号")
    finally:
        collector.stop_collection()


if __name__ == "__main__":
    main()
