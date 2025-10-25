"""
Tradestation OAuth认证助手 - 固定浏览器端口版本
支持持久化登录状态，避免重复认证
"""
import asyncio
import json
import webbrowser
import threading
import time
from pathlib import Path
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import os

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.services.tradestation_client import TradestationAPIClient


class AuthCallbackHandler(BaseHTTPRequestHandler):
    """处理OAuth回调的HTTP服务器"""
    
    def do_GET(self):
        """处理GET请求"""
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            # 获取授权码
            code = query_params['code'][0]
            state = query_params.get('state', [''])[0]
            
            # 保存授权码到全局变量
            AuthCallbackHandler.auth_code = code
            AuthCallbackHandler.state = state
            
            # 返回成功页面
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>认证成功</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                    }
                    .container {
                        background: rgba(255,255,255,0.1);
                        padding: 30px;
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                    }
                    .success { color: #4CAF50; font-size: 24px; }
                    .info { margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">✅ 认证成功！</h1>
                    <p class="info">您已成功授权 Tradestation 自动化交易策略系统</p>
                    <p class="info">现在可以关闭此页面，返回程序继续操作</p>
                    <p class="info">系统将自动获取访问令牌...</p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
            
        else:
            # 错误处理
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>认证失败</title>
                <meta charset="utf-8">
                <style>
                    body { 
                        font-family: Arial, sans-serif; 
                        text-align: center; 
                        padding: 50px;
                        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                        color: white;
                    }
                    .container {
                        background: rgba(255,255,255,0.1);
                        padding: 30px;
                        border-radius: 10px;
                        backdrop-filter: blur(10px);
                    }
                    .error { color: #ff4757; font-size: 24px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="error">❌ 认证失败</h1>
                    <p>请检查授权流程是否正确</p>
                </div>
            </body>
            </html>
            """
            
            self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """禁用默认日志输出"""
        pass


class PersistentAuthServer:
    """持久化认证服务器"""
    
    def __init__(self, port=8080):
        self.port = port
        self.server = None
        self.server_thread = None
        self.running = False
        
    def start(self):
        """启动服务器"""
        if self.running:
            return
            
        try:
            self.server = HTTPServer(('localhost', self.port), AuthCallbackHandler)
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.daemon = True
            self.server_thread.start()
            self.running = True
            print(f"🌐 认证服务器已启动: http://localhost:{self.port}")
        except Exception as e:
            print(f"❌ 启动服务器失败: {e}")
            
    def stop(self):
        """停止服务器"""
        if self.server and self.running:
            self.server.shutdown()
            self.server.server_close()
            self.running = False
            print("🛑 认证服务器已停止")


async def save_tokens(client: TradestationAPIClient):
    """保存令牌到文件"""
    tokens = {
        "access_token": client.access_token,
        "refresh_token": client.refresh_token,
        "expires_at": client.token_expires_at.isoformat() if client.token_expires_at else None,
        "saved_at": time.time()
    }
    
    with open("tokens.json", "w") as f:
        json.dump(tokens, f, indent=2)
    
    print("✅ 令牌已保存到 tokens.json")


async def load_tokens(client: TradestationAPIClient) -> bool:
    """从文件加载令牌"""
    try:
        with open("tokens.json", "r") as f:
            tokens = json.load(f)
        
        # 检查令牌是否过期
        if tokens.get("expires_at"):
            from datetime import datetime
            expires_at = datetime.fromisoformat(tokens["expires_at"])
            if datetime.now() >= expires_at:
                print("⚠️ 访问令牌已过期，尝试刷新...")
                client.access_token = tokens["access_token"]
                client.refresh_token = tokens["refresh_token"]
                client.token_expires_at = expires_at
                
                # 尝试刷新令牌
                try:
                    await client.refresh_access_token()
                    await save_tokens(client)
                    print("✅ 令牌已刷新")
                    return True
                except:
                    print("❌ 刷新令牌失败，需要重新认证")
                    return False
        
        client.access_token = tokens["access_token"]
        client.refresh_token = tokens["refresh_token"]
        
        if tokens["expires_at"]:
            from datetime import datetime
            client.token_expires_at = datetime.fromisoformat(tokens["expires_at"])
        
        print("✅ 令牌已从文件加载")
        return True
        
    except FileNotFoundError:
        print("❌ 未找到令牌文件")
        return False
    except Exception as e:
        print(f"❌ 加载令牌失败: {str(e)}")
        return False


async def interactive_auth_with_persistent_server():
    """使用持久化服务器的交互式认证"""
    # 启动持久化服务器
    auth_server = PersistentAuthServer(port=8080)
    auth_server.start()
    
    try:
        async with TradestationAPIClient() as client:
            # 生成授权URL
            auth_url = client.get_authorization_url()
            
            print("🔐 开始OAuth认证流程")
            print("=" * 50)
            print(f"授权URL: {auth_url}")
            print()
            
            # 自动打开浏览器
            print("🌐 正在打开浏览器...")
            webbrowser.open(auth_url)
            
            print("📋 认证步骤:")
            print("1. 浏览器将自动打开 Tradestation 登录页面")
            print("2. 输入您的 TradeStation 用户名和密码")
            print("3. 授权应用程序访问您的账户")
            print("4. 系统将自动获取访问令牌")
            print()
            print("⏳ 等待授权回调...")
            
            # 等待授权回调
            max_wait_time = 300  # 5分钟超时
            wait_time = 0
            
            while wait_time < max_wait_time:
                if hasattr(AuthCallbackHandler, 'auth_code') and AuthCallbackHandler.auth_code:
                    code = AuthCallbackHandler.auth_code
                    print(f"✅ 收到授权码: {code[:20]}...")
                    
                    # 交换令牌
                    print("🔄 正在交换访问令牌...")
                    await client.exchange_code_for_token(code)
                    
                    print("✅ 认证成功!")
                    print(f"访问令牌: {client.access_token[:20]}...")
                    print(f"刷新令牌: {client.refresh_token[:20]}...")
                    
                    return client
                
                await asyncio.sleep(1)
                wait_time += 1
                
                if wait_time % 30 == 0:  # 每30秒显示一次进度
                    print(f"⏳ 等待中... ({wait_time}/{max_wait_time}秒)")
            
            print("❌ 认证超时，请重试")
            return None
            
    finally:
        # 停止服务器
        auth_server.stop()


async def test_authenticated_api():
    """测试已认证的API调用"""
    async with TradestationAPIClient() as client:
        # 尝试加载已保存的令牌
        if not await load_tokens(client):
            print("需要重新认证...")
            client = await interactive_auth_with_persistent_server()
            if client:
                await save_tokens(client)
            else:
                return
        
        try:
            # 测试获取账户信息
            print("🔍 测试获取账户信息...")
            accounts = await client.get_accounts()
            print(f"✅ 账户列表: {accounts}")
            
            if accounts.get("Accounts"):
                account_id = accounts["Accounts"][0]["AccountID"]
                print(f"📊 使用账户: {account_id}")
                
                # 测试获取账户余额
                print("💰 测试获取账户余额...")
                balance = await client.get_account_balance(account_id)
                print(f"✅ 账户余额: {balance}")
                
                # 测试获取持仓
                print("📈 测试获取持仓...")
                positions = await client.get_positions(account_id)
                print(f"✅ 持仓信息: {positions}")
                
                # 测试获取订单
                print("📋 测试获取订单...")
                orders = await client.get_orders(account_id)
                print(f"✅ 订单信息: {orders}")
            
            # 测试获取交易品种
            print("🔍 测试获取交易品种...")
            symbols = await client.get_symbols()
            print(f"✅ 交易品种数量: {len(symbols.get('Symbols', []))}")
            
            # 测试获取市场数据
            print("📊 测试获取市场数据...")
            market_data = await client.get_market_data("AAPL", "1min")
            print(f"✅ 市场数据: {len(market_data.get('Bars', []))} 条K线")
            
            # 测试获取即时价格
            print("💲 测试获取即时价格...")
            quote = await client.get_quote("AAPL")
            print(f"✅ 即时价格: {quote}")
            
            print("\n🎉 所有API测试通过!")
            
        except Exception as e:
            print(f"❌ API测试失败: {str(e)}")
            print("可能需要重新认证...")


async def main():
    """主函数"""
    print("🔐 Tradestation OAuth认证助手 - 固定端口版本")
    print("=" * 60)
    print("💡 特性:")
    print("   - 固定端口 8080，避免重复认证")
    print("   - 自动保存和加载访问令牌")
    print("   - 自动刷新过期令牌")
    print("   - 持久化登录状态")
    print("=" * 60)
    
    while True:
        print("\n请选择操作:")
        print("1. 进行OAuth认证")
        print("2. 测试API功能")
        print("3. 查看保存的令牌")
        print("4. 清除保存的令牌")
        print("5. 退出")
        
        choice = input("请输入选择 (1-5): ").strip()
        
        if choice == "1":
            try:
                client = await interactive_auth_with_persistent_server()
                if client:
                    await save_tokens(client)
                    print("✅ 认证完成!")
                else:
                    print("❌ 认证失败")
            except Exception as e:
                print(f"❌ 认证失败: {str(e)}")
        
        elif choice == "2":
            try:
                await test_authenticated_api()
            except Exception as e:
                print(f"❌ 测试失败: {str(e)}")
        
        elif choice == "3":
            try:
                if os.path.exists("tokens.json"):
                    with open("tokens.json", "r") as f:
                        tokens = json.load(f)
                    print("📄 保存的令牌信息:")
                    print(f"   访问令牌: {tokens.get('access_token', 'N/A')[:20]}...")
                    print(f"   刷新令牌: {tokens.get('refresh_token', 'N/A')[:20]}...")
                    print(f"   过期时间: {tokens.get('expires_at', 'N/A')}")
                    print(f"   保存时间: {time.ctime(tokens.get('saved_at', 0))}")
                else:
                    print("❌ 未找到令牌文件")
            except Exception as e:
                print(f"❌ 读取令牌失败: {str(e)}")
        
        elif choice == "4":
            try:
                if os.path.exists("tokens.json"):
                    os.remove("tokens.json")
                    print("✅ 令牌文件已清除")
                else:
                    print("❌ 未找到令牌文件")
            except Exception as e:
                print(f"❌ 清除令牌失败: {str(e)}")
        
        elif choice == "5":
            print("👋 再见!")
            break
        
        else:
            print("❌ 无效选择，请重新输入")


if __name__ == "__main__":
    asyncio.run(main())

