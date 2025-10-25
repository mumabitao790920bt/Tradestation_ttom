import os
from dotenv import load_dotenv

# 加载环境变量（作为备用）
load_dotenv()

class Config:
    """配置类"""
    
    # API配置 - 请在此处填入您的API密钥
    # 获取方式：登录OKX官网 -> 账户中心 -> API管理 -> 创建API密钥
    # 权限设置：需要开启"交易权限"和"读取权限"
    
    # 方法1：直接在此处配置（推荐）
    # 示例格式（请替换为您的实际密钥）：
    # API_KEY = "12345678-1234-1234-1234-123456789abc"
    # SECRET_KEY = "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    # PASSPHRASE = "your_passphrase_here"
    
    API_KEY = "3c3e0628-cbd9-4b27-8d87-b4822a07396d"  # 请替换为您的API Key
    SECRET_KEY = "C9E3DAACCD05680A4105FECD438DD78B"  # 请替换为您的Secret Key
    PASSPHRASE = "Zrq20090311*"  # 请替换为您的Passphrase
    
    # 方法2：从环境变量读取（备用）
    # 如果上面的密钥未设置，则从环境变量读取
    if API_KEY == "your_api_key_here":
        API_KEY = os.getenv('OKX_API_KEY', '')
    if SECRET_KEY == "your_secret_key_here":
        SECRET_KEY = os.getenv('OKX_SECRET_KEY', '')
    if PASSPHRASE == "your_passphrase_here":
        PASSPHRASE = os.getenv('OKX_PASSPHRASE', '')
    
    # 交易配置
    FLAG = "0"  # 0: 实盘交易, 1: 模拟交易
    
    # 默认交易对
    DEFAULT_INSTRUMENT = "BTC-USDT-SWAP"
    
    # 交易参数
    DEFAULT_LEVERAGE = 10
    DEFAULT_SIZE = 1  # 合约张数
    
    # 风险控制
    MAX_POSITION_SIZE = 100  # 最大持仓张数
    STOP_LOSS_PERCENTAGE = 0.05  # 止损百分比 5%
    
    @classmethod
    def validate_config(cls):
        """验证配置是否完整"""
        if not cls.API_KEY or cls.API_KEY == "your_api_key_here":
            print("❌ API_KEY 未配置")
            print("   请在 config.py 文件中设置您的 API_KEY")
            print("   示例：API_KEY = '12345678-1234-1234-1234-123456789abc'")
            return False
        if not cls.SECRET_KEY or cls.SECRET_KEY == "your_secret_key_here":
            print("❌ SECRET_KEY 未配置")
            print("   请在 config.py 文件中设置您的 SECRET_KEY")
            print("   示例：SECRET_KEY = 'abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'")
            return False
        if not cls.PASSPHRASE or cls.PASSPHRASE == "your_passphrase_here":
            print("❌ PASSPHRASE 未配置")
            print("   请在 config.py 文件中设置您的 PASSPHRASE")
            print("   示例：PASSPHRASE = 'your_passphrase_here'")
            return False
        return True 