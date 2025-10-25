import requests
from datetime import datetime, timezone, timedelta

def test_timezone_data():
    """测试时区问题"""
    
    # 中国时间 2025-08-25 06:00:00
    china_time = datetime(2025, 8, 25, 6, 0, 0)
    china_tz = timezone(timedelta(hours=8))
    china_time_with_tz = china_time.replace(tzinfo=china_tz)
    
    # 转换为UTC时间
    utc_time = china_time_with_tz.astimezone(timezone.utc)
    
    print(f"中国时间: {china_time_with_tz}")
    print(f"对应UTC时间: {utc_time}")
    
    # 测试UTC时间的数据
    start_time_ms = int(utc_time.timestamp() * 1000)
    end_time_ms = start_time_ms + 3600000  # 1小时后
    
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {
        "symbol": "BTCUSDT",
        "interval": "1h",
        "startTime": start_time_ms,
        "endTime": end_time_ms,
        "limit": 3
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        print(f"\n正在获取UTC时间 {utc_time} 的数据...")
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"获取到 {len(data)} 条数据")
            
            for i, item in enumerate(data):
                open_time_ms = int(item[0])
                dt = datetime.fromtimestamp(open_time_ms / 1000.0, tz=timezone.utc)
                china_dt = dt.astimezone(timezone(timedelta(hours=8)))
                
                print(f"\n第{i+1}条数据:")
                print(f"  UTC时间: {dt}")
                print(f"  中国时间: {china_dt}")
                print(f"  开盘价: {float(item[1]):.1f}")
                print(f"  最高价: {float(item[2]):.1f}")
                print(f"  最低价: {float(item[3]):.1f}")
                print(f"  收盘价: {float(item[4]):.1f}")
                
                # 检查是否是中国时间06:00
                if china_dt.hour == 6 and china_dt.day == 25:
                    print(f"  *** 这是中国时间06:00的数据！***")
                    print(f"  对比Binance软件数据:")
                    print(f"    软件显示: 开盘112947.2, 最高113456.0, 最低112561.1, 收盘113400.6")
                    print(f"    API数据:  开盘{float(item[1]):.1f}, 最高{float(item[2]):.1f}, 最低{float(item[3]):.1f}, 收盘{float(item[4]):.1f}")
        else:
            print(f"❌ API请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")

if __name__ == "__main__":
    test_timezone_data()
