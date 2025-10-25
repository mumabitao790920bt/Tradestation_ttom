import requests
import json
from datetime import datetime, timezone

def test_binance_api():
    """测试Binance API返回的数据"""
    
    # 测试永续合约API
    url = "https://fapi.binance.com/fapi/v1/klines"
    
    # 获取2025-08-25 06:00:00附近的数据
    target_time = datetime(2025, 8, 25, 6, 0, 0, tzinfo=timezone.utc)
    start_time_ms = int(target_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1小时后
    
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 5
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print("正在测试Binance永续合约API...")
        print(f"目标时间: {target_time}")
        print(f"API参数: {params}")
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API返回数据:")
            print(f"数据条数: {len(data)}")
            
            for i, item in enumerate(data):
                open_time_ms = int(item[0])
                dt = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
                
                print(f"\n第{i+1}条数据:")
                print(f"  时间: {dt} ({dt.strftime('%Y-%m-%d %H:%M:%S')})")
                print(f"  开盘价: {float(item[1]):.1f}")
                print(f"  最高价: {float(item[2]):.1f}")
                print(f"  最低价: {float(item[3]):.1f}")
                print(f"  收盘价: {float(item[4]):.1f}")
                print(f"  成交量: {float(item[5]):.1f}")
                
                # 检查是否是目标时间
                if dt.hour == 6 and dt.day == 25:
                    print(f"  *** 这是目标时间的数据！***")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_binance_api()
