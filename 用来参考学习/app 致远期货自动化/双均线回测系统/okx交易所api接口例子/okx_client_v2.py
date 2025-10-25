#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OKX API客户端 - 适配okx 0.4.0版本
"""

# okx 2.1.2 版本：API 类在 okx.api 子模块下
from okx.api import Account, Trade, Market, Public
# 重命名以保持兼容性
MarketData = Market
PublicData = Public
from config import Config
import pandas as pd
import time

class OKXClientV2:
    """OKX API客户端 - 新版本"""
    
    def __init__(self):
        """初始化客户端"""
        self.flag = Config.FLAG
        self.api_key = Config.API_KEY
        self.secret_key = Config.SECRET_KEY
        self.passphrase = Config.PASSPHRASE
        
        # 初始化API客户端 - okx 2.1.2 版本直接使用类
        self.account_client = Account(
            key=self.api_key,
            secret=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag  # 0: 实盘, 1: 模拟
        )
        
        self.trade_client = Trade(
            key=self.api_key,
            secret=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag
        )
        
        self.market_client = MarketData(
            key=self.api_key,
            secret=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag
        )
        
        self.public_client = PublicData(
            key=self.api_key,
            secret=self.secret_key,
            passphrase=self.passphrase,
            flag=self.flag
        )
    
    def get_tickers(self, inst_type="SWAP"):
        """获取市场行情数据"""
        try:
            result = self.market_client.get_tickers(instType=inst_type)
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取行情数据失败: {result}")
                return None
        except Exception as e:
            print(f"获取行情数据异常: {e}")
            return None
    
    def get_ticker(self, inst_id):
        """获取单个交易对的价格信息"""
        try:
            result = self.market_client.get_ticker(instId=inst_id)
            if result['code'] == '0':
                return result
            else:
                print(f"获取价格信息失败: {result}")
                return None
        except Exception as e:
            print(f"获取价格信息异常: {e}")
            return None
    
    def get_instruments(self, inst_type="SWAP"):
        """获取可交易的交易对信息"""
        try:
            result = self.public_client.get_instruments(instType=inst_type)
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取交易对信息失败: {result}")
                return None
        except Exception as e:
            print(f"获取交易对信息异常: {e}")
            return None
    
    def get_account_balance(self):
        """获取账户余额"""
        try:
            # okx 2.1.2 使用 get_balance 方法
            result = self.account_client.get_balance()
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取账户余额失败: {result}")
                return None
        except Exception as e:
            print(f"获取账户余额异常: {e}")
            return None
    
    def get_account_config(self):
        """获取账户配置"""
        try:
            result = self.account_client.get_account_config()
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取账户配置失败: {result}")
                return None
        except Exception as e:
            print(f"获取账户配置异常: {e}")
            return None
    
    def set_leverage(self, inst_id, lever, mgn_mode="isolated", pos_side=None):
        """设置杠杆"""
        try:
            params = {
                'instId': inst_id,
                'lever': lever,
                'mgnMode': mgn_mode
            }
            if pos_side:
                params['posSide'] = pos_side
            
            result = self.account_client.set_leverage(**params)
            if result['code'] == '0':
                print(f"设置杠杆成功: {lever}倍")
                return True
            else:
                print(f"设置杠杆失败: {result}")
                return False
        except Exception as e:
            print(f"设置杠杆异常: {e}")
            return False
    
    def place_order(self, inst_id, td_mode, side, pos_side, ord_type, sz, px=None, cl_ord_id=None):
        """下单"""
        try:
            params = {
                'instId': inst_id,
                'tdMode': td_mode,
                'side': side,
                'posSide': pos_side,
                'ordType': ord_type,
                'sz': sz
            }
            if px:
                params['px'] = px
            if cl_ord_id:
                params['clOrdId'] = cl_ord_id
            
            # okx 2.1.2 使用 set_order 方法
            result = self.trade_client.set_order(**params)
            print(f"[DEBUG] set_order 原始返回: {result}")  # 调试输出
            if result and result.get('code') == '0':
                print(f"下单成功: {side} {sz}张 {inst_id}")
                return result['data'][0]
            else:
                print(f"下单失败: {result}")
                return None
        except Exception as e:
            print(f"下单异常: {e}")
            return None
    
    def get_order(self, inst_id, ord_id=None, cl_ord_id=None):
        """查询订单详情（支持 ordId 或 clOrdId）"""
        try:
            kwargs = {'instId': inst_id}
            if ord_id:
                kwargs['ordId'] = ord_id
            if cl_ord_id:
                kwargs['clOrdId'] = cl_ord_id
            result = self.trade_client.get_order(**kwargs)
            if result['code'] == '0':
                return result['data'][0]
            else:
                print(f"查询订单失败: {result}")
                return None
        except Exception as e:
            print(f"查询订单异常: {e}")
            return None
    
    def cancel_order(self, inst_id, ord_id):
        """取消订单"""
        try:
            # okx 2.1.2 使用 set_cancel_order 方法
            result = self.trade_client.set_cancel_order(instId=inst_id, ordId=ord_id)
            print(f"[DEBUG] set_cancel_order 原始返回: {result}")  # 调试输出
            if result and result.get('code') == '0':
                print(f"取消订单成功: {ord_id}")
                return True
            else:
                print(f"取消订单失败: {result}")
                return False
        except Exception as e:
            print(f"取消订单异常: {e}")
            return False
    
    def get_positions(self):
        """获取持仓信息"""
        try:
            # okx 2.1.2 需要 instType 参数
            result = self.account_client.get_positions(instType='SWAP')
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取持仓信息失败: {result}")
                return None
        except Exception as e:
            print(f"获取持仓信息异常: {e}")
            return None
    
    def get_order_list(self):
        """获取当前委托列表"""
        try:
            # okx 2.1.2 使用 get_orders_pending 方法
            result = self.trade_client.get_orders_pending(instType='SWAP')
            print(f"[DEBUG] get_orders_pending 原始返回: {result}")  # 调试输出
            if result and result.get('code') == '0':
                data = result.get('data', [])
                print(f"[DEBUG] get_orders_pending 返回数据: {len(data) if data else 0}条订单")  # 调试输出
                return data
            else:
                print(f"获取委托列表失败: {result}")
                return []  # 返回空列表而不是None
        except Exception as e:
            print(f"获取委托列表异常: {e}")
            return []  # 返回空列表而不是None
    
    def get_order_history(self, inst_id=None, state=None, limit=100):
        """获取历史委托记录"""
        try:
            # okx 2.1.2 的 get_orders_history 需要 instType 作为必需参数
            params = {'instType': 'SWAP', 'limit': str(limit)}
            if inst_id:
                params['instId'] = inst_id
            if state:
                params['state'] = state
            
            result = self.trade_client.get_orders_history(**params)
            print(f"[DEBUG] get_orders_history 原始返回: {result}")  # 调试输出
            if result and result.get('code') == '0':
                return result['data']
            else:
                print(f"获取历史委托失败: {result}")
                return None
        except Exception as e:
            print(f"获取历史委托异常: {e}")
            return None

    def get_recent_fills(self, inst_id=None, limit=1):
        """获取最近成交（用于获取最后成交价）"""
        try:
            params = {'instType': 'SWAP', 'limit': limit}
            if inst_id:
                params['instId'] = inst_id
            # OKX v5: /api/v5/trade/fills
            result = self.trade_client.get_fills(**params)
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取最近成交失败: {result}")
                return None
        except Exception as e:
            print(f"获取最近成交异常: {e}")
            return None
    
    def get_trades_history(self, inst_id=None, limit=100):
        """获取历史成交记录"""
        try:
            params = {'instType': 'SWAP', 'limit': limit}
            if inst_id:
                params['instId'] = inst_id
            
            result = self.trade_client.get_fills_history(**params)
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取历史成交失败: {result}")
                return None
        except Exception as e:
            print(f"获取历史成交异常: {e}")
            return None
    
    def get_trades(self, inst_id=None, limit=100):
        """获取最近成交记录"""
        try:
            params = {'instType': 'SWAP', 'limit': limit}
            if inst_id:
                params['instId'] = inst_id
            
            result = self.trade_client.get_fills(**params)
            if result['code'] == '0':
                return result['data']
            else:
                print(f"获取成交记录失败: {result}")
                return None
        except Exception as e:
            print(f"获取成交记录异常: {e}")
            return None 