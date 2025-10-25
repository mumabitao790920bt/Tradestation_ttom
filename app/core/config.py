"""
Tradestation项目核心配置
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基础配置
    app_name: str = "Tradestation 自动化交易策略"
    app_version: str = "1.0.0"
    debug: bool = True
    
    # Tradestation API配置
    tradestation_api_key: str = "7nTEG6CTvOomXQ4Fo9vGVkrDeRs0iFA5"
    tradestation_secret: str = "X18iJpHmso8Rt7rUhEBRQ9hUAufzQ1qKyLs-hHQVsVo-NaK5H9Bzp_UqTEE97Yg5"
    tradestation_base_url: str = "https://api.tradestation.com"
    
    # 数据库配置
    database_url: str = "sqlite:///./tradestation.db"
    
    # Redis配置
    redis_url: str = "redis://localhost:6379"
    
    # 日志配置
    log_level: str = "INFO"
    log_file: str = "logs/tradestation.log"
    
    # 数据缓存配置
    cache_ttl: int = 300  # 5分钟
    max_cache_size: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局配置实例
settings = Settings()
