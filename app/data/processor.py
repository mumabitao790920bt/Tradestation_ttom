"""
数据处理模块
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
from app.services.tradestation_client import TradestationAPIClient
from app.core.config import settings


class DataProcessor:
    """数据处理器"""
    
    def __init__(self):
        self.client = TradestationAPIClient()
        
    def clean_market_data(self, raw_data: Dict) -> pd.DataFrame:
        """清洗市场数据"""
        try:
            # 提取K线数据
            bars = raw_data.get('data', [])
            if not bars:
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame(bars)
            
            # 重命名列
            column_mapping = {
                'TimeStamp': 'timestamp',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 数据类型转换
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 数据验证
            df = self._validate_data(df)
            
            # 排序
            df = df.sort_values('timestamp').reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"数据清洗失败: {str(e)}")
            return pd.DataFrame()
    
    def _validate_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据验证"""
        # 移除空值
        df = df.dropna()
        
        # 验证OHLC逻辑
        invalid_rows = (
            (df['high'] < df['low']) |
            (df['high'] < df['open']) |
            (df['high'] < df['close']) |
            (df['low'] > df['open']) |
            (df['low'] > df['close'])
        )
        
        if invalid_rows.any():
            print(f"发现 {invalid_rows.sum()} 行无效的OHLC数据，已移除")
            df = df[~invalid_rows]
        
        # 验证价格合理性
        price_cols = ['open', 'high', 'low', 'close']
        for col in price_cols:
            df = df[df[col] > 0]
        
        return df
    
    def calculate_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        if df.empty:
            return df
            
        # 移动平均线
        df['ma_5'] = df['close'].rolling(window=5).mean()
        df['ma_20'] = df['close'].rolling(window=20).mean()
        df['ma_50'] = df['close'].rolling(window=50).mean()
        
        # RSI
        df['rsi'] = self._calculate_rsi(df['close'])
        
        # MACD
        macd_data = self._calculate_macd(df['close'])
        df['macd'] = macd_data['macd']
        df['macd_signal'] = macd_data['signal']
        df['macd_histogram'] = macd_data['histogram']
        
        # 布林带
        bb_data = self._calculate_bollinger_bands(df['close'])
        df['bb_upper'] = bb_data['upper']
        df['bb_middle'] = bb_data['middle']
        df['bb_lower'] = bb_data['lower']
        
        return df
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def _calculate_macd(self, prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict:
        """计算MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        signal_line = macd.ewm(span=signal).mean()
        histogram = macd - signal_line
        
        return {
            'macd': macd,
            'signal': signal_line,
            'histogram': histogram
        }
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20, std_dev: float = 2) -> Dict:
        """计算布林带"""
        middle = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = middle + (std * std_dev)
        lower = middle - (std * std_dev)
        
        return {
            'upper': upper,
            'middle': middle,
            'lower': lower
        }
    
    def resample_data(self, df: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """重采样数据到指定时间周期"""
        if df.empty:
            return df
            
        df = df.set_index('timestamp')
        
        # 重采样规则
        resample_rules = {
            '1min': '1T',
            '5min': '5T',
            '15min': '15T',
            '30min': '30T',
            '1hour': '1H',
            '4hour': '4H',
            '1day': '1D'
        }
        
        rule = resample_rules.get(timeframe, '1T')
        
        # 重采样
        resampled = df.resample(rule).agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum'
        }).dropna()
        
        return resampled.reset_index()
    
    async def get_and_process_data(self, symbol: str, interval: str = "1min", 
                                 start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """获取并处理数据"""
        try:
            async with self.client as client:
                # 获取原始数据
                raw_data = await client.get_market_data(symbol, interval, start_date, end_date)
                
                # 清洗数据
                df = self.clean_market_data(raw_data)
                
                if df.empty:
                    print(f"未获取到 {symbol} 的数据")
                    return df
                
                # 计算技术指标
                df = self.calculate_technical_indicators(df)
                
                print(f"成功处理 {symbol} 数据，共 {len(df)} 条记录")
                return df
                
        except Exception as e:
            print(f"数据处理失败: {str(e)}")
            return pd.DataFrame()


# 使用示例
async def test_data_processing():
    """测试数据处理"""
    processor = DataProcessor()
    
    # 获取并处理数据
    df = await processor.get_and_process_data("AAPL", "1min")
    
    if not df.empty:
        print("数据处理成功!")
        print(f"数据形状: {df.shape}")
        print(f"列名: {df.columns.tolist()}")
        print(f"最新数据:\n{df.tail()}")
    else:
        print("数据处理失败")


if __name__ == "__main__":
    asyncio.run(test_data_processing())
