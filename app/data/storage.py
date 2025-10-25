"""
数据存储模块
"""
import pandas as pd
import sqlite3
import json
import redis
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


Base = declarative_base()


class MarketData(Base):
    """市场数据模型"""
    __tablename__ = "market_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    interval = Column(String(10), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DataStorage:
    """数据存储管理器"""
    
    def __init__(self):
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocreate=False, autoflush=False, bind=self.engine)
        self.redis_client = redis.from_url(settings.redis_url)
        
    def create_tables(self):
        """创建数据库表"""
        Base.metadata.create_all(bind=self.engine)
        print("数据库表创建成功")
    
    def save_market_data(self, df: pd.DataFrame, symbol: str, interval: str):
        """保存市场数据到数据库"""
        if df.empty:
            return
            
        try:
            session = self.SessionLocal()
            
            # 准备数据
            records = []
            for _, row in df.iterrows():
                record = MarketData(
                    symbol=symbol,
                    timestamp=row['timestamp'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    interval=interval
                )
                records.append(record)
            
            # 批量插入
            session.bulk_save_objects(records)
            session.commit()
            session.close()
            
            print(f"成功保存 {len(records)} 条 {symbol} 数据到数据库")
            
        except Exception as e:
            print(f"保存数据到数据库失败: {str(e)}")
    
    def get_market_data(self, symbol: str, interval: str = "1min", 
                       start_date: datetime = None, end_date: datetime = None) -> pd.DataFrame:
        """从数据库获取市场数据"""
        try:
            session = self.SessionLocal()
            
            query = session.query(MarketData).filter(MarketData.symbol == symbol)
            query = query.filter(MarketData.interval == interval)
            
            if start_date:
                query = query.filter(MarketData.timestamp >= start_date)
            if end_date:
                query = query.filter(MarketData.timestamp <= end_date)
            
            results = query.order_by(MarketData.timestamp).all()
            session.close()
            
            if not results:
                return pd.DataFrame()
            
            # 转换为DataFrame
            data = []
            for result in results:
                data.append({
                    'timestamp': result.timestamp,
                    'open': result.open,
                    'high': result.high,
                    'low': result.low,
                    'close': result.close,
                    'volume': result.volume
                })
            
            df = pd.DataFrame(data)
            print(f"从数据库获取 {len(df)} 条 {symbol} 数据")
            return df
            
        except Exception as e:
            print(f"从数据库获取数据失败: {str(e)}")
            return pd.DataFrame()
    
    def cache_data(self, key: str, data: Any, ttl: int = None):
        """缓存数据到Redis"""
        try:
            if isinstance(data, pd.DataFrame):
                data_json = data.to_json(orient='records')
            else:
                data_json = json.dumps(data)
            
            ttl = ttl or settings.cache_ttl
            self.redis_client.setex(key, ttl, data_json)
            print(f"数据已缓存到Redis: {key}")
            
        except Exception as e:
            print(f"缓存数据失败: {str(e)}")
    
    def get_cached_data(self, key: str) -> Optional[Any]:
        """从Redis获取缓存数据"""
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                data_json = cached_data.decode('utf-8')
                try:
                    # 尝试解析为DataFrame
                    data = pd.read_json(data_json, orient='records')
                    print(f"从Redis获取缓存数据: {key}")
                    return data
                except:
                    # 解析为普通JSON
                    data = json.loads(data_json)
                    print(f"从Redis获取缓存数据: {key}")
                    return data
            return None
            
        except Exception as e:
            print(f"获取缓存数据失败: {str(e)}")
            return None
    
    def delete_cache(self, key: str):
        """删除缓存"""
        try:
            self.redis_client.delete(key)
            print(f"已删除缓存: {key}")
        except Exception as e:
            print(f"删除缓存失败: {str(e)}")
    
    def get_cache_keys(self, pattern: str = "*") -> List[str]:
        """获取缓存键列表"""
        try:
            keys = self.redis_client.keys(pattern)
            return [key.decode('utf-8') for key in keys]
        except Exception as e:
            print(f"获取缓存键失败: {str(e)}")
            return []
    
    def clear_all_cache(self):
        """清空所有缓存"""
        try:
            self.redis_client.flushdb()
            print("已清空所有缓存")
        except Exception as e:
            print(f"清空缓存失败: {str(e)}")
    
    def get_symbols_from_db(self) -> List[str]:
        """从数据库获取所有交易品种"""
        try:
            session = self.SessionLocal()
            symbols = session.query(MarketData.symbol).distinct().all()
            session.close()
            return [symbol[0] for symbol in symbols]
        except Exception as e:
            print(f"获取交易品种失败: {str(e)}")
            return []
    
    def get_latest_data(self, symbol: str, interval: str = "1min") -> Optional[Dict]:
        """获取最新数据"""
        try:
            session = self.SessionLocal()
            latest = session.query(MarketData).filter(
                MarketData.symbol == symbol,
                MarketData.interval == interval
            ).order_by(MarketData.timestamp.desc()).first()
            session.close()
            
            if latest:
                return {
                    'timestamp': latest.timestamp,
                    'open': latest.open,
                    'high': latest.high,
                    'low': latest.low,
                    'close': latest.close,
                    'volume': latest.volume
                }
            return None
            
        except Exception as e:
            print(f"获取最新数据失败: {str(e)}")
            return None


# 使用示例
def test_data_storage():
    """测试数据存储"""
    storage = DataStorage()
    
    # 创建表
    storage.create_tables()
    
    # 测试数据
    test_data = pd.DataFrame({
        'timestamp': [datetime.now()],
        'open': [100.0],
        'high': [105.0],
        'low': [95.0],
        'close': [102.0],
        'volume': [1000]
    })
    
    # 保存数据
    storage.save_market_data(test_data, "TEST", "1min")
    
    # 获取数据
    df = storage.get_market_data("TEST", "1min")
    print(f"获取到数据: {len(df)} 条")
    
    # 缓存测试
    storage.cache_data("test_key", {"test": "data"})
    cached = storage.get_cached_data("test_key")
    print(f"缓存数据: {cached}")


if __name__ == "__main__":
    test_data_storage()
