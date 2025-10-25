"""
Tradestation API客户端 - 基于官方OAuth2认证
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from urllib.parse import urlencode, urlparse, parse_qs
import webbrowser
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

from app.core.config import settings


class TradestationAPIClient:
    """Tradestation API客户端 - OAuth2认证"""
    
    def __init__(self):
        self.client_id = settings.tradestation_api_key
        self.client_secret = settings.tradestation_secret
        self.base_url = "https://api.tradestation.com/v3"
        self.auth_url = "https://signin.tradestation.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None
        
        # 尝试加载已保存的令牌
        self._load_tokens()
        
    def _load_tokens(self):
        """从文件加载令牌"""
        try:
            with open("tokens.json", "r") as f:
                tokens = json.load(f)
            
            self.access_token = tokens.get("access_token")
            self.refresh_token = tokens.get("refresh_token")
            
            expires_at_str = tokens.get("expires_at")
            if expires_at_str:
                self.token_expires_at = datetime.fromisoformat(expires_at_str)
                
        except FileNotFoundError:
            # 令牌文件不存在，这是正常的
            pass
        except Exception as e:
            print(f"⚠️ 加载令牌文件时出错: {e}")
    
    def _save_tokens(self):
        """保存令牌到文件"""
        try:
            tokens = {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "expires_at": self.token_expires_at.isoformat() if self.token_expires_at else None,
                "saved_at": datetime.now().timestamp()
            }
            
            with open("tokens.json", "w") as f:
                json.dump(tokens, f, indent=2)
                
        except Exception as e:
            print(f"⚠️ 保存令牌文件时出错: {e}")
        
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    def get_authorization_url(self, redirect_uri: str = "http://localhost:8080") -> str:
        """获取授权URL"""
        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "audience": "https://api.tradestation.com",  # 必需参数
            "redirect_uri": redirect_uri,
            "scope": "openid profile MarketData ReadAccount Trade offline_access",
            "state": "xyzABC123"
        }
        
        auth_url = f"{self.auth_url}/authorize?" + urlencode(params)
        return auth_url
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str = "http://localhost:8080") -> Dict:
        """使用授权码换取访问令牌"""
        token_url = f"{self.auth_url}/oauth/token"
        
        data = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "redirect_uri": redirect_uri
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data, headers=headers) as response:
                response.raise_for_status()
                token_data = await response.json()
                
                self.access_token = token_data["access_token"]
                self.refresh_token = token_data["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])
                
                return token_data
    
    async def refresh_access_token(self) -> Dict:
        """刷新访问令牌"""
        if not self.refresh_token:
            raise Exception("没有刷新令牌")
        
        token_url = f"{self.auth_url}/oauth/token"
        
        data = {
            "grant_type": "refresh_token",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(token_url, data=data, headers=headers) as response:
                response.raise_for_status()
                token_data = await response.json()
                
                self.access_token = token_data["access_token"]
                if "refresh_token" in token_data:
                    self.refresh_token = token_data["refresh_token"]
                self.token_expires_at = datetime.now() + timedelta(seconds=token_data["expires_in"])
                
                # 保存刷新后的令牌到文件
                self._save_tokens()
                
                return token_data
    
    def is_token_valid(self) -> bool:
        """检查令牌是否有效"""
        if not self.access_token or not self.token_expires_at:
            return False
        return datetime.now() < self.token_expires_at - timedelta(minutes=5)
    
    async def _ensure_valid_token(self):
        """确保有有效的访问令牌"""
        if not self.is_token_valid():
            if self.refresh_token:
                await self.refresh_access_token()
            else:
                raise Exception("需要重新授权")
    
    async def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None) -> Dict:
        """发送API请求"""
        if not self.session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        await self._ensure_valid_token()
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        try:
            async with self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data
            ) as response:
                response.raise_for_status()
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise Exception(f"API请求失败: {str(e)}")
    
    # ========== 市场数据相关 ==========
    
    async def get_symbols(self, exchange: str = None) -> Dict:
        """获取交易品种列表"""
        params = {}
        if exchange:
            params["exchange"] = exchange
            
        return await self._make_request("GET", "/marketdata/symbols", params=params)
    
    async def get_market_data(self, symbol: str, interval: int = 1, unit: str = "minute", 
                            barsback: int = 10, start_date: str = None) -> Dict:
        """获取K线数据"""
        params = {
            "interval": interval,
            "unit": unit,
            "barsback": barsback
        }
        
        if start_date:
            params["startdate"] = start_date
            
        return await self._make_request("GET", f"/marketdata/barcharts/{symbol}", params=params)
    
    async def get_quote(self, symbol: str) -> Dict:
        """获取即时价格"""
        params = {"symbols": symbol}
        return await self._make_request("GET", "/marketdata/quotes", params=params)
    
    # ========== 账户相关 ==========
    
    async def get_accounts(self) -> Dict:
        """获取账户列表"""
        return await self._make_request("GET", "/brokerage/accounts")
    
    async def get_account_info(self, account_id: str) -> Dict:
        """获取账户基本信息"""
        return await self._make_request("GET", f"/brokerage/accounts/{account_id}")
    
    async def get_account_balance(self, account_id: str) -> Dict:
        """查询资金"""
        return await self._make_request("GET", f"/brokerage/accounts/{account_id}/balances")
    
    async def get_positions(self, account_id: str) -> Dict:
        """查询持仓"""
        return await self._make_request("GET", f"/brokerage/accounts/{account_id}/positions")
    
    async def get_orders(self, account_id: str) -> Dict:
        """查询委托/订单"""
        return await self._make_request("GET", f"/brokerage/accounts/{account_id}/orders")
    
    # ========== 交易相关 ==========
    
    async def place_market_order(self, account_id: str, symbol: str, quantity: int, 
                                side: str) -> Dict:
        """市价买入/卖出"""
        data = {
            "AccountID": account_id,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": "Market",
            "TradeAction": side  # Buy, Sell, BuyToCover, SellShort
        }
        
        return await self._make_request("POST", "/orders", data=data)
    
    async def place_limit_order(self, account_id: str, symbol: str, quantity: int, 
                               side: str, limit_price: float) -> Dict:
        """限价买入/卖出"""
        data = {
            "AccountID": account_id,
            "Symbol": symbol,
            "Quantity": quantity,
            "OrderType": "Limit",
            "TradeAction": side,
            "LimitPrice": limit_price
        }
        
        return await self._make_request("POST", "/orders", data=data)
    
    async def close_position(self, account_id: str, symbol: str, quantity: int) -> Dict:
        """市价平仓"""
        # 先获取当前持仓
        positions = await self.get_positions(account_id)
        
        # 找到对应品种的持仓
        position = None
        for pos in positions.get("Positions", []):
            if pos["Symbol"] == symbol:
                position = pos
                break
        
        if not position:
            raise Exception(f"未找到 {symbol} 的持仓")
        
        # 确定平仓方向
        side = "Sell" if position["Quantity"] > 0 else "BuyToCover"
        
        return await self.place_market_order(account_id, symbol, abs(quantity), side)
    
    async def buy_long(self, account_id: str, symbol: str, quantity: int) -> Dict:
        """市价做多买入"""
        return await self.place_market_order(account_id, symbol, quantity, "Buy")
    
    async def sell_short(self, account_id: str, symbol: str, quantity: int) -> Dict:
        """市价做空卖出"""
        return await self.place_market_order(account_id, symbol, quantity, "SellShort")
    
    async def buy_to_cover(self, account_id: str, symbol: str, quantity: int) -> Dict:
        """市价做多平仓"""
        return await self.place_market_order(account_id, symbol, quantity, "BuyToCover")
    
    async def sell_to_close(self, account_id: str, symbol: str, quantity: int) -> Dict:
        """市价做空平仓"""
        return await self.place_market_order(account_id, symbol, quantity, "Sell")


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """OAuth回调处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path.startswith('/'):
            # 解析查询参数
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            
            if 'code' in query_params:
                code = query_params['code'][0]
                # 这里可以存储code或触发token交换
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write(f"""
                <html>
                <body>
                    <h1>授权成功!</h1>
                    <p>授权码: {code}</p>
                    <p>请关闭此窗口并返回应用程序。</p>
                </body>
                </html>
                """.encode())
            else:
                self.send_response(400)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                self.wfile.write("<html><body><h1>授权失败</h1></body></html>".encode())


def start_auth_server(port: int = 8080):
    """启动认证服务器"""
    server = HTTPServer(('localhost', port), AuthCallbackHandler)
    server.timeout = 300  # 5分钟超时
    return server


async def interactive_auth():
    """交互式认证"""
    client = TradestationAPIClient()
    
    # 获取授权URL
    auth_url = client.get_authorization_url()
    print(f"请在浏览器中打开以下URL进行授权:")
    print(auth_url)
    
    # 启动本地服务器接收回调
    server = start_auth_server()
    
    try:
        # 打开浏览器
        webbrowser.open(auth_url)
        
        # 等待回调
        print("等待授权回调...")
        server.handle_request()
        
        # 这里需要手动输入授权码
        code = input("请输入授权码: ")
        
        # 交换令牌
        token_data = await client.exchange_code_for_token(code)
        print("认证成功!")
        print(f"访问令牌: {token_data['access_token'][:20]}...")
        
        return client
        
    finally:
        server.server_close()


# 使用示例
async def test_api_connection():
    """测试API连接"""
    try:
        # 交互式认证
        client = await interactive_auth()
        
        async with client as c:
            # 测试获取账户信息
            accounts = await c.get_accounts()
            print("API连接成功!")
            print(f"账户列表: {accounts}")
            
            if accounts.get("Accounts"):
                account_id = accounts["Accounts"][0]["AccountID"]
                
                # 测试获取账户余额
                balance = await c.get_account_balance(account_id)
                print(f"账户余额: {balance}")
                
                # 测试获取交易品种
                symbols = await c.get_symbols()
                print(f"交易品种数量: {len(symbols.get('Symbols', []))}")
            
    except Exception as e:
        print(f"API连接失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_api_connection())
