"""
币安期货自动交易模块
根据策略信号自动执行交易操作
"""

import hmac
import hashlib
import time
import requests
import json
from typing import Dict, List, Optional
from decimal import Decimal, ROUND_DOWN


class BinanceFuturesTrader:
    """币安期货交易类"""
    
    def __init__(self, api_key: str, secret_key: str, testnet: bool = False):
        """
        初始化交易器
        
        Args:
            api_key: API密钥
            secret_key: 密钥
            testnet: 是否使用测试网
        """
        self.api_key = api_key
        self.secret_key = secret_key
        
        if testnet:
            self.base_url = "https://testnet.binancefuture.com"
        else:
            self.base_url = "https://fapi.binance.com"
            
        self.symbol = "BTCUSDT"  # 交易对
        # 符号过滤器缓存（精度/限额）
        self._symbol_filters_cache = {}
        # 保护单状态
        self._protective_state = {}
        
    def _generate_signature(self, params: str) -> str:
        """生成签名"""
        return hmac.new(
            self.secret_key.encode('utf-8'),
            params.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, params: Dict = None, signed: bool = False, max_retries: int = 3) -> Dict:
        """发送请求，支持重试机制"""
        if params is None:
            params = {}
            
        url = f"{self.base_url}{endpoint}"
        headers = {'X-MBX-APIKEY': self.api_key}
        
        for attempt in range(max_retries):
            try:
                if signed:
                    # 使用智能时间戳计算，带容错处理
                    timestamp, recv_window = self._calculate_timestamp_with_tolerance()
                    params['timestamp'] = timestamp
                    params['recvWindow'] = recv_window
                    
                    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
                    params['signature'] = self._generate_signature(query_string)
                
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=10)
                elif method == 'POST':
                    response = requests.post(url, data=params, headers=headers, timeout=10)
                elif method == 'DELETE':
                    response = requests.delete(url, params=params, headers=headers, timeout=10)
                else:
                    raise ValueError(f"不支持的HTTP方法: {method}")
                    
                # 检查响应状态
                if response.status_code == 200:
                    return response.json()
                else:
                    try:
                        error_data = response.json()
                        error_msg = error_data.get('msg', 'Unknown error')
                        error_code = error_data.get('code', -1)
                        
                        # 检查是否是时间戳错误，如果是则重试
                        if error_code == -1021 and attempt < max_retries - 1:
                            print(f"⏰ 时间戳错误，第{attempt + 1}次重试...")
                            time.sleep(1)  # 等待1秒后重试
                            continue
                        
                        print(f"请求失败: {response.status_code} - {response.text}")
                        return {'error': error_msg, 'code': error_code}
                    except:
                        print(f"请求失败: {response.status_code} - {response.text}")
                        return {'error': response.text, 'code': response.status_code}
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    print(f"🌐 网络异常，第{attempt + 1}次重试: {e}")
                    time.sleep(2)  # 网络异常等待2秒
                    continue
                else:
                    print(f"请求异常: {e}")
                    return {'error': str(e), 'code': -1}
        
        # 所有重试都失败了
        return {'error': f'请求失败，已重试{max_retries}次', 'code': -1}
    
    def _get_server_time(self) -> int:
        """获取币安服务器时间，带容错处理"""
        try:
            response = requests.get(f"{self.base_url}/fapi/v1/time", timeout=5)
            if response.status_code == 200:
                server_time = response.json()['serverTime']
                # 考虑网络延迟，增加一点偏移
                network_delay = 100  # 100ms网络延迟补偿
                return server_time + network_delay
            else:
                return int(time.time() * 1000)
        except:
            return int(time.time() * 1000)
    
    def _calculate_timestamp_with_tolerance(self) -> tuple:
        """
        计算带容错的时间戳
        
        Returns:
            (timestamp, recvWindow): 时间戳和接收窗口
        """
        # 获取服务器时间
        server_time = self._get_server_time()
        local_time = int(time.time() * 1000)
        
        # 计算时间差
        time_diff = server_time - local_time
        
        # 基础时间戳
        base_timestamp = int(time.time() * 1000) + time_diff
        
        # 容错设置
        # 币安API默认recvWindow是5000ms，我们设置更大的容错范围
        recv_window = 10000  # 10秒容错窗口
        
        # 为了确保在窗口内，稍微提前一点时间戳
        safety_offset = 1000  # 1秒安全偏移
        final_timestamp = base_timestamp - safety_offset
        
        # 调试信息（只在第一次调用时显示）
        if not hasattr(self, '_timestamp_debug_shown'):
            print(f"🕐 时间戳调试信息:")
            print(f"   本地时间: {local_time}")
            print(f"   服务器时间: {server_time}")
            print(f"   时间差: {time_diff}ms")
            print(f"   基础时间戳: {base_timestamp}")
            print(f"   最终时间戳: {final_timestamp}")
            print(f"   接收窗口: {recv_window}ms")
            self._timestamp_debug_shown = True
        
        return final_timestamp, recv_window
    
    def get_account_info(self) -> Dict:
        """获取账户信息"""
        return self._make_request('GET', '/fapi/v2/account', signed=True)
    
    def get_position_info(self) -> List[Dict]:
        """获取持仓信息"""
        result = self._make_request('GET', '/fapi/v2/account', signed=True)
        
        # 检查请求是否成功
        if 'error' in result:
            print(f"❌ 获取持仓信息失败: {result['error']}")
            return None  # 返回None表示获取失败
        
        positions = result.get('positions', [])
        # 只返回有持仓的
        return [pos for pos in positions if float(pos['positionAmt']) != 0]
    
    def get_position_info_with_retry(self, max_groups: int = 10) -> List[Dict]:
        """
        持仓查询验证：每次查询2次，如果一致就确认；失败时重试
        
        Args:
            max_groups: 最大重试组数，默认10组（每组2次查询）
            
        Returns:
            如果两次查询结果一致，返回持仓信息；否则返回None
        """
        print(f"🔍 开始持仓查询验证（最多{max_groups}组，每组2次查询）...")
        
        for group in range(max_groups):
            print(f"📊 第{group + 1}组查询:")
            
            # 每组查询2次
            results = []
            for i in range(2):
                attempt_num = group * 2 + i + 1
                print(f"   第{attempt_num}次查询持仓...")
                
                positions = self.get_position_info()
                
                if positions is None:
                    print(f"   ❌ 第{attempt_num}次查询失败")
                    break
                
                # 转换为可比较的格式
                position_summary = []
                for pos in positions:
                    if pos['symbol'] == self.symbol:
                        position_summary.append({
                            'symbol': pos['symbol'],
                            'positionAmt': float(pos['positionAmt']),
                            'entryPrice': float(pos['entryPrice'])
                        })
                
                results.append(position_summary)
                print(f"   ✅ 第{attempt_num}次查询结果: {position_summary}")
                
                # 如果不是第2次查询，等待1秒
                if i == 0:
                    time.sleep(1)
            
            # 检查这组2次查询是否都成功且一致
            if len(results) == 2:
                if results[0] == results[1]:
                    print(f"✅ 第{group + 1}组查询结果一致，确认持仓信息")
                    return results[0]
                else:
                    print(f"❌ 第{group + 1}组查询结果不一致:")
                    print(f"   第1次: {results[0]}")
                    print(f"   第2次: {results[1]}")
            else:
                print(f"❌ 第{group + 1}组查询失败，无法获取完整结果")
            
            # 如果不是最后一组，等待2秒后重试
            if group < max_groups - 1:
                print(f"⏳ 等待2秒后开始第{group + 2}组查询...")
                time.sleep(2)
        
        print(f"❌ 所有{max_groups}组查询都失败，无法确认真实持仓")
        return None
    
    def get_current_price(self) -> float:
        """获取当前价格"""
        ticker = self._make_request('GET', '/fapi/v1/ticker/price', {'symbol': self.symbol})
        return float(ticker.get('price', 0))
    
    def get_mark_price(self) -> float:
        """获取标记价格(MARK_PRICE)用于条件单触发判断"""
        data = self._make_request('GET', '/fapi/v1/premiumIndex', {'symbol': self.symbol})
        try:
            return float(data.get('markPrice'))
        except Exception:
            # 退化到最新成交价
            return self.get_current_price()

    def get_exchange_info(self) -> Dict:
        """获取交易所信息"""
        return self._make_request('GET', '/fapi/v1/exchangeInfo')

    def _get_symbol_filters(self, symbol: str) -> Dict:
        """获取并缓存交易对的过滤器(价格精度/数量步长/最小名义等)"""
        if symbol in self._symbol_filters_cache:
            return self._symbol_filters_cache[symbol]
        info = self.get_exchange_info()
        price_tick = 0.01
        step_size = 0.001
        min_notional = 5.0
        if info and 'symbols' in info:
            for s in info['symbols']:
                if s.get('symbol') == symbol:
                    filters = {f['filterType']: f for f in s.get('filters', [])}
                    if 'PRICE_FILTER' in filters:
                        price_tick = float(filters['PRICE_FILTER'].get('tickSize', price_tick))
                    if 'LOT_SIZE' in filters:
                        step_size = float(filters['LOT_SIZE'].get('stepSize', step_size))
                    if 'NOTIONAL' in filters:
                        min_notional = float(filters['NOTIONAL'].get('minNotional', min_notional))
                    break
        data = {'price_tick': price_tick, 'step_size': step_size, 'min_notional': min_notional}
        self._symbol_filters_cache[symbol] = data
        return data

    def _floor_to_step(self, value: float, step: float) -> float:
        if step <= 0:
            return value
        n = int(value / step)
        return n * step

    def format_price(self, symbol: str, price: float) -> str:
        """按交易对tickSize格式化价格，向下取整以避免超精度"""
        f = self._get_symbol_filters(symbol)
        tick = f.get('price_tick', 0.01)
        adj = self._floor_to_step(float(price), float(tick))
        # 依据tick的小数位输出
        decimals = max(0, str(tick)[::-1].find('.')) if '.' in str(tick) else 0
        return f"{adj:.{decimals}f}"

    def format_quantity(self, symbol: str, qty: float) -> str:
        """按交易对stepSize格式化数量，向下取整以避免超精度"""
        f = self._get_symbol_filters(symbol)
        step = f.get('step_size', 0.001)
        adj = self._floor_to_step(float(qty), float(step))
        decimals = max(0, str(step)[::-1].find('.')) if '.' in str(step) else 0
        return f"{adj:.{decimals}f}"
    
    def place_order(self, side: str, quantity: float, order_type: str = 'MARKET', symbol: str = None, position_side: str = 'LONG') -> Dict:
        """
        下单
        
        Args:
            side: BUY 或 SELL
            quantity: 数量
            order_type: 订单类型，默认MARKET
            symbol: 交易对，默认使用self.symbol
            position_side: 持仓方向 LONG/SHORT，默认LONG
        """
        if symbol is None:
            symbol = self.symbol
            
        params = {
            'symbol': symbol,
            'side': side,
            'type': order_type,
            'quantity': self.format_quantity(symbol, quantity),
            'positionSide': position_side,  # 添加持仓方向
        }
        
        # 只有限价单才需要timeInForce参数
        if order_type == 'LIMIT':
            params['timeInForce'] = 'GTC'
        
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)
    
    def place_stop_market(self, stop_price: float, position_side: str) -> Dict:
        """在持仓方向上挂保护性止损(条件单)，不要求数量，使用 closePosition。"""
        params = {
            'symbol': self.symbol,
            'side': 'SELL' if position_side == 'LONG' else 'BUY',
            'type': 'STOP_MARKET',
            'stopPrice': self.format_price(self.symbol, stop_price),
            'closePosition': True,
            'workingType': 'MARK_PRICE',
            'timeInForce': 'GTC',
            'positionSide': position_side,
        }
        return self._make_request('POST', '/fapi/v1/order', params, signed=True)

    def get_open_orders(self) -> List[Dict]:
        """查询当前挂单"""
        res = self._make_request('GET', '/fapi/v1/openOrders', {'symbol': self.symbol}, signed=True)
        return res if isinstance(res, list) else []

    def manage_protective_stop(self, position_side: str, new_stop_price: float) -> Dict:
        """
        管理保护性止损单
        
        Args:
            position_side: 持仓方向 'LONG' 或 'SHORT'
            new_stop_price: 新的止损价格
            
        Returns:
            操作结果
        """
        try:
            # 1. 查询所有挂单
            orders = self.get_open_orders()
            print(f"🔍 查询到 {len(orders)} 个挂单")
            
            # 2. 筛选出同方向的STOP_MARKET保护单
            protective_orders = []
            for o in orders:
                if (o.get('type') == 'STOP_MARKET' and 
                    o.get('positionSide') == position_side and
                    o.get('closePosition') == True):
                    protective_orders.append(o)
                    print(f"🔍 找到保护单: stopPrice={o.get('stopPrice')}, orderId={o.get('orderId')}")
            
            # 3. 格式化新价格
            new_stop_price_fmt = self.format_price(self.symbol, new_stop_price)
            new_stop_price_float = float(new_stop_price_fmt)
            
            print(f"🔍 新保护单价格: {new_stop_price_fmt}")
            
            # 4. 判断操作
            if not protective_orders:
                # 情况1：没有保护单，直接挂新的
                print(f"🆕 无保护单，挂新保护单: {position_side} @ {new_stop_price_fmt}")
                return self.place_stop_market(new_stop_price_float, position_side)
            
            else:
                # 情况2：有保护单，检查价格是否变化
                existing_price = float(protective_orders[0].get('stopPrice', '0'))
                price_diff = abs(existing_price - new_stop_price_float)
                tick_size = float(self._get_symbol_filters(self.symbol).get('price_tick', 0.01))
                
                print(f"🔍 现有保护单价格: {existing_price}, 价格差: {price_diff}, tick: {tick_size}")
                
                if price_diff <= tick_size:
                    # 价格没有变化，无需操作
                    print(f"✅ 保护单价格无变化，无需操作")
                    return {'status': 'no_action', 'message': '保护单价格无变化'}
                else:
                    # 价格有变化，先撤销所有保护单，再挂新的
                    print(f"🔄 保护单价格有变化，先撤销再重挂")
                    
                    # 撤销所有同方向保护单
                    for order in protective_orders:
                        order_id = order.get('orderId')
                        print(f"🗑️ 撤销保护单: {order_id}")
                        cancel_result = self._make_request('DELETE', '/fapi/v1/order', {
                            'symbol': self.symbol,
                            'orderId': order_id
                        }, signed=True)
                        print(f"撤销结果: {cancel_result}")
                    
                    # 挂新的保护单
                    print(f"🆕 挂新保护单: {position_side} @ {new_stop_price_fmt}")
                    return self.place_stop_market(new_stop_price_float, position_side)
                    
        except Exception as e:
            print(f"❌ 管理保护单异常: {e}")
            return {'error': str(e)}

    def close_position(self, side: str) -> Dict:
        """平仓"""
        positions = self.get_position_info()
        for pos in positions:
            if pos['symbol'] == self.symbol:
                position_amt = float(pos['positionAmt'])
                if position_amt != 0:
                    # 平仓数量为持仓数量的绝对值
                    quantity = abs(position_amt)
                    # 平仓方向与持仓方向相反
                    close_side = 'SELL' if position_amt > 0 else 'BUY'
                    return self.place_order(close_side, quantity)
        return {}
    
    def adjust_position(self, target_quantity: float, positions: List[Dict] = None) -> Dict:
        """
        调整持仓到目标数量
        
        Args:
            target_quantity: 目标持仓数量（正数为多头，负数为空头，0为平仓）
            positions: 外部传入的持仓信息，如果为None则重新查询
        """
        if positions is None:
            positions = self.get_position_info()
            if positions is None:
                return {'error': '无法获取持仓信息'}
        
        current_position = 0
        
        # 获取当前持仓
        for pos in positions:
            if pos['symbol'] == self.symbol:
                current_position = float(pos['positionAmt'])
                break
        
        print(f"当前持仓: {current_position}, 目标持仓: {target_quantity}")
        
        # 如果持仓已经正确，无需调整
        if abs(current_position - target_quantity) < 0.001:
            print("持仓已正确，无需调整")
            return {'status': 'no_action'}
        
        # 情况1：目标持仓为0（完全平仓）
        if abs(target_quantity) < 0.001:
            if abs(current_position) > 0.001:
                # 平掉所有持仓
                close_side = 'BUY' if current_position < 0 else 'SELL'  # 空头用BUY平，多头用SELL平
                quantity = abs(current_position)
                print(f"完全平仓: {close_side} {quantity}")
                return self.place_order(close_side, quantity, position_side='LONG' if current_position > 0 else 'SHORT')
            else:
                print("已无持仓，无需平仓")
                return {'status': 'no_action'}
        
        # 情况2：目标持仓与当前持仓方向相反
        if (target_quantity > 0 and current_position < 0) or (target_quantity < 0 and current_position > 0):
            # 先平掉当前持仓
            close_side = 'BUY' if current_position < 0 else 'SELL'
            close_quantity = abs(current_position)
            print(f"平掉反向持仓: {close_side} {close_quantity}")
            close_result = self.place_order(close_side, close_quantity, position_side='LONG' if current_position > 0 else 'SHORT')
            
            # 再开目标持仓
            open_side = 'BUY' if target_quantity > 0 else 'SELL'
            open_quantity = abs(target_quantity)
            print(f"开目标持仓: {open_side} {open_quantity}")
            return self.place_order(open_side, open_quantity, position_side='LONG' if target_quantity > 0 else 'SHORT')
        
        # 情况3：目标持仓与当前持仓方向相同，但数量不同
        if (target_quantity > 0 and current_position >= 0) or (target_quantity < 0 and current_position <= 0):
            diff = abs(target_quantity) - abs(current_position)
            if abs(diff) < 0.001:
                print("持仓数量已正确")
                return {'status': 'no_action'}
            
            if diff > 0:
                # 需要增加持仓
                side = 'BUY' if target_quantity > 0 else 'SELL'
                quantity = diff
                position_side = 'LONG' if target_quantity > 0 else 'SHORT'
                print(f"增加持仓: {side} {quantity}")
                return self.place_order(side, quantity, position_side=position_side)
            else:
                # 需要减少持仓（平掉部分）
                side = 'BUY' if target_quantity < 0 else 'SELL'  # 空头用BUY平，多头用SELL平
                quantity = abs(diff)
                position_side = 'LONG' if target_quantity > 0 else 'SHORT'
                print(f"减少持仓: {side} {quantity}")
                return self.place_order(side, quantity, position_side=position_side)
        
        return {'error': '未知的持仓调整情况'}

    def cancel_all_open_orders(self) -> Dict:
        """撤销所有挂单"""
        try:
            result = self._make_request('DELETE', '/fapi/v1/allOpenOrders', {'symbol': self.symbol}, signed=True)
            if isinstance(result, dict) and 'code' in result:
                print(f"撤销所有挂单失败: {result}")
                return result
            else:
                print(f"✅ 已撤销所有挂单: {result}")
                return result
        except Exception as e:
            print(f"撤销挂单异常: {e}")
            return {'error': str(e)}


def execute_trading_logic(target_position: int, contract_size: float, api_key: str, secret_key: str, symbol: str = 'BTCUSDT', stop_ref_price: float = None, latest_close_price: float = None):
    """
    执行交易逻辑
    
    Args:
        target_position: 策略目标持仓 (-1, 0, 1)
        contract_size: 合约数量（1份对应的实际合约数量）
        api_key: 币安API密钥
        secret_key: 币安密钥
        symbol: 交易合约符号，默认为BTCUSDT
    """
    if not api_key or not secret_key:
        print("API密钥未配置，跳过自动交易")
        return
    
    try:
        trader = BinanceFuturesTrader(api_key, secret_key, testnet=False)
        trader.symbol = symbol  # 设置交易合约
        
        # 获取当前价格
        current_price = trader.get_current_price()
        print(f"当前{symbol}价格: {current_price}")
        
        # 获取合约信息，检查最小名义价值要求
        exchange_info = trader.get_exchange_info()
        min_notional = 5.0  # 默认最小名义价值
        
        if exchange_info and 'symbols' in exchange_info:
            for s in exchange_info['symbols']:
                if s['symbol'] == symbol:
                    # 获取最小名义价值
                    for filter_info in s.get('filters', []):
                        if filter_info['filterType'] == 'NOTIONAL':
                            min_notional = float(filter_info['minNotional'])
                            break
                    break
        
        print(f"{symbol}最小名义价值要求: {min_notional} USDT")
        
        # 计算满足最小名义价值的交易数量
        min_quantity = min_notional / current_price
        print(f"满足最小名义价值的最小数量: {min_quantity:.6f} {symbol}")
        
        # 获取当前持仓（使用连续查询验证）
        positions = trader.get_position_info_with_retry()
        
        if positions is None:
            print("❌ 无法获取准确的持仓信息，跳过本次交易")
            return {'error': '无法获取准确的持仓信息，跳过交易'}
        
        print(f"✅ 确认当前持仓: {positions}")
        
        # 根据策略信号执行交易
        if target_position == 1:
            # 策略要求持有多头仓位
            target_quantity = contract_size
            print(f"策略信号: 持有多头仓位 {target_quantity} {symbol}")
            
            # 检查是否满足最小名义价值要求
            notional_value = target_quantity * current_price
            if notional_value < min_notional:
                print(f"❌ 交易数量不足！")
                print(f"   设定数量: {target_quantity} {symbol}")
                print(f"   名义价值: {notional_value:.2f} USDT")
                print(f"   最小要求: {min_notional} USDT")
                print(f"   建议数量: {min_quantity:.6f} {symbol}")
                print(f"   请调整合约数量参数或选择其他合约")
                return {'error': f'交易数量不足，名义价值{notional_value:.2f}USDT < 最小要求{min_notional}USDT'}
            
            result = trader.adjust_position(target_quantity, positions)
            # 成交后管理保护性止损单
            try:
                positions_after = trader.get_position_info_with_retry()
                if positions_after and stop_ref_price is not None:
                    pos_amt = 0.0
                    for p in positions_after:
                        if p['symbol'] == symbol:
                            pos_amt = float(p['positionAmt'])
                            break
                    
                    if pos_amt > 0:  # 持有多头仓位
                        # 使用标记价格进行合理性判断与偏移
                        mark = trader.get_mark_price()
                        f = trader._get_symbol_filters(symbol)
                        tick = float(f.get('price_tick', 0.01))
                        # 期望：多仓止损价应显著低于标记价
                        stop_price = stop_ref_price
                        if not (stop_price < mark - 2 * tick):
                            # 至少下移3个tick避免立即触发
                            stop_price = mark - 3 * tick
                        
                        print(f"🛡️ 管理多头保护单: stop_ref={stop_ref_price}, mark={mark}, adj={stop_price}")
                        trader.manage_protective_stop('LONG', stop_price)
                    else:
                        print(f"⚠️ 跳过挂多仓保护单，无多头持仓")
            except Exception as _e:
                print(f"保护单管理异常: {_e}")
            
        elif target_position == -1:
            # 策略要求持有空头仓位
            target_quantity = -contract_size
            print(f"策略信号: 持有空头仓位 {target_quantity} {symbol}")
            
            # 检查是否满足最小名义价值要求
            notional_value = abs(target_quantity) * current_price
            if notional_value < min_notional:
                print(f"❌ 交易数量不足！")
                print(f"   设定数量: {abs(target_quantity)} {symbol}")
                print(f"   名义价值: {notional_value:.2f} USDT")
                print(f"   最小要求: {min_notional} USDT")
                print(f"   建议数量: {min_quantity:.6f} {symbol}")
                print(f"   请调整合约数量参数或选择其他合约")
                return {'error': f'交易数量不足，名义价值{notional_value:.2f}USDT < 最小要求{min_notional}USDT'}
            
            result = trader.adjust_position(target_quantity, positions)
            # 成交后管理保护性止损单
            try:
                positions_after = trader.get_position_info_with_retry()
                if positions_after and stop_ref_price is not None:
                    pos_amt = 0.0
                    for p in positions_after:
                        if p['symbol'] == symbol:
                            pos_amt = float(p['positionAmt'])
                            break
                    
                    if pos_amt < 0:  # 持有空头仓位
                        # 使用标记价格进行合理性判断与偏移
                        mark = trader.get_mark_price()
                        f = trader._get_symbol_filters(symbol)
                        tick = float(f.get('price_tick', 0.01))
                        # 期望：空仓止损价应显著高于标记价
                        stop_price = stop_ref_price
                        if not (stop_price > mark + 2 * tick):
                            # 至少上移3个tick避免立即触发
                            stop_price = mark + 3 * tick
                        
                        print(f"🛡️ 管理空头保护单: stop_ref={stop_ref_price}, mark={mark}, adj={stop_price}")
                        trader.manage_protective_stop('SHORT', stop_price)
                    else:
                        print(f"⚠️ 跳过挂空仓保护单，无空头持仓")
            except Exception as _e:
                print(f"保护单管理异常: {_e}")
            
        elif target_position == 0:
            # 策略要求平仓 - 检查是否有持仓
            current_positions = []
            for pos in positions:
                if pos['symbol'] == symbol:
                    position_amt = float(pos['positionAmt'])
                    if position_amt != 0:
                        current_positions.append(pos)
            
            if not current_positions:
                print(f"策略信号: 平仓所有持仓 {symbol}")
                print(f"✅ 当前无持仓，无需平仓操作")
                return {'status': 'no_action', 'message': '当前无持仓，无需平仓'}
            else:
                print(f"策略信号: 平仓所有持仓 {symbol}")
                position_info = [f"{p['symbol']}: {p['positionAmt']}" for p in current_positions]
                print(f"📊 当前持仓: {position_info}")
                
                # 平仓前先撤销所有保护性止损单
                print("🔄 平仓前撤销所有挂单...")
                trader.cancel_all_open_orders()
                
                result = trader.adjust_position(0, positions)
            
        else:
            print(f"未知的策略信号: {target_position}")
            return
        
        print(f"交易结果: {result}")
        
    except Exception as e:
        print(f"自动交易执行失败: {e}")


def test_trading_module():
    """测试交易模块"""
    print("测试自动交易模块...")
    
    # 这里使用测试用的API密钥，实际使用时需要替换为真实的
    test_api_key = "your_api_key_here"
    test_secret_key = "your_secret_key_here"
    
    if test_api_key == "your_api_key_here":
        print("请配置真实的API密钥进行测试")
        return
    
    # 测试不同的持仓信号
    test_cases = [
        (1, 0.001),   # 持有多头0.001
        (-1, 0.001),  # 持有空头0.001
        (0, 0.001),   # 平仓
    ]
    
    for target_pos, contract_size in test_cases:
        print(f"\n测试持仓信号: {target_pos}, 合约数量: {contract_size}")
        execute_trading_logic(target_pos, contract_size, test_api_key, test_secret_key)
        time.sleep(2)  # 避免请求过于频繁


if __name__ == "__main__":
    test_trading_module()
