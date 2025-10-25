"""
Tradestation 完整功能测试程序 - 带UI界面
包含所有交易和查询功能
"""
import streamlit as st
import asyncio
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.services.tradestation_client import TradestationAPIClient


class TradingUI:
    """交易UI界面"""
    
    def __init__(self):
        self.client = None
        self.accounts = []
        self.selected_account = None
        self.symbols = []
        self.market_data = {}
        
    async def initialize_client(self):
        """初始化API客户端"""
        if not self.client:
            self.client = TradestationAPIClient()
            
            # 加载保存的令牌
            try:
                with open("tokens.json", "r") as f:
                    tokens = json.load(f)
                
                self.client.access_token = tokens["access_token"]
                self.client.refresh_token = tokens["refresh_token"]
                
                if tokens["expires_at"]:
                    from datetime import datetime
                    self.client.token_expires_at = datetime.fromisoformat(tokens["expires_at"])
                
                return True
            except Exception as e:
                st.error(f"加载令牌失败: {e}")
                return False
        return True
    
    async def load_accounts(self):
        """加载账户信息"""
        try:
            async with self.client as c:
                accounts_data = await c.get_accounts()
                self.accounts = accounts_data.get("Accounts", [])
                return True
        except Exception as e:
            st.error(f"加载账户失败: {e}")
            return False
    
    async def load_symbols(self):
        """加载交易品种"""
        try:
            # 这里先使用一些常见的股票代码
            # 实际应该调用API获取
            self.symbols = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", 
                "META", "NVDA", "NFLX", "AMD", "INTC",
                "SPY", "QQQ", "IWM", "GLD", "TLT"
            ]
            return True
        except Exception as e:
            st.error(f"加载交易品种失败: {e}")
            return False
    
    async def get_account_balance(self, account_id):
        """获取账户余额"""
        try:
            async with self.client as c:
                balance_data = await c.get_account_balance(account_id)
                return balance_data
        except Exception as e:
            st.error(f"获取账户余额失败: {e}")
            return None
    
    async def get_positions(self, account_id):
        """获取持仓信息"""
        try:
            async with self.client as c:
                positions_data = await c.get_positions(account_id)
                return positions_data
        except Exception as e:
            st.error(f"获取持仓失败: {e}")
            return None
    
    async def get_orders(self, account_id):
        """获取订单信息"""
        try:
            async with self.client as c:
                orders_data = await c.get_orders(account_id)
                return orders_data
        except Exception as e:
            st.error(f"获取订单失败: {e}")
            return None
    
    async def get_quote(self, symbol):
        """获取即时价格"""
        try:
            async with self.client as c:
                quote_data = await c.get_quote(symbol)
                return quote_data
        except Exception as e:
            st.error(f"获取即时价格失败: {e}")
            return None
    
    async def get_market_data(self, symbol, interval="1min", count=100):
        """获取K线数据"""
        try:
            async with self.client as c:
                market_data = await c.get_market_data(symbol, interval, count=count)
                return market_data
        except Exception as e:
            st.error(f"获取K线数据失败: {e}")
            return None
    
    async def place_order(self, account_id, symbol, quantity, side, order_type="Market", price=None):
        """下单"""
        try:
            async with self.client as c:
                if order_type == "Market":
                    if side == "Buy":
                        result = await c.buy_long(account_id, symbol, quantity)
                    elif side == "Sell":
                        result = await c.sell_short(account_id, symbol, quantity)
                elif order_type == "Limit":
                    result = await c.place_limit_order(account_id, symbol, quantity, side, price)
                
                return result
        except Exception as e:
            st.error(f"下单失败: {e}")
            return None
    
    async def close_position(self, account_id, symbol, quantity, side):
        """平仓"""
        try:
            async with self.client as c:
                if side == "Long":
                    result = await c.sell_to_close(account_id, symbol, quantity)
                elif side == "Short":
                    result = await c.buy_to_cover(account_id, symbol, quantity)
                
                return result
        except Exception as e:
            st.error(f"平仓失败: {e}")
            return None


def main():
    """主函数"""
    st.set_page_config(
        page_title="Tradestation 交易测试系统",
        page_icon="📈",
        layout="wide"
    )
    
    st.title("🚀 Tradestation 交易测试系统")
    st.markdown("---")
    
    # 创建UI实例
    ui = TradingUI()
    
    # 侧边栏 - 账户选择
    st.sidebar.title("📊 账户信息")
    
    # 初始化客户端
    if st.sidebar.button("🔄 初始化连接"):
        with st.spinner("正在初始化..."):
            success = asyncio.run(ui.initialize_client())
            if success:
                st.sidebar.success("✅ 连接成功!")
            else:
                st.sidebar.error("❌ 连接失败!")
    
    # 加载账户
    if st.sidebar.button("📋 加载账户"):
        with st.spinner("正在加载账户..."):
            success = asyncio.run(ui.load_accounts())
            if success:
                st.sidebar.success(f"✅ 加载了 {len(ui.accounts)} 个账户")
            else:
                st.sidebar.error("❌ 加载账户失败!")
    
    # 显示账户列表
    if ui.accounts:
        account_options = [f"{acc['AccountID']} ({acc['AccountType']})" for acc in ui.accounts]
        selected_account_idx = st.sidebar.selectbox("选择账户:", range(len(account_options)), 
                                                   format_func=lambda x: account_options[x])
        ui.selected_account = ui.accounts[selected_account_idx]
        
        st.sidebar.markdown("---")
        st.sidebar.markdown(f"**账户ID:** {ui.selected_account['AccountID']}")
        st.sidebar.markdown(f"**账户类型:** {ui.selected_account['AccountType']}")
        st.sidebar.markdown(f"**状态:** {ui.selected_account['Status']}")
    
    # 主界面
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 账户查询", "💰 交易操作", "📈 市场数据", "📋 订单管理", "⚙️ 系统设置"])
    
    with tab1:
        st.header("📊 账户查询")
        
        if ui.selected_account:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("💰 查询余额"):
                    with st.spinner("正在查询余额..."):
                        balance_data = asyncio.run(ui.get_account_balance(ui.selected_account['AccountID']))
                        if balance_data:
                            st.success("✅ 余额查询成功!")
                            balances = balance_data.get('Balances', [])
                            if balances:
                                balance = balances[0]
                                st.metric("现金余额", f"${balance.get('CashBalance', '0')}")
                                st.metric("购买力", f"${balance.get('BuyingPower', '0')}")
                                st.metric("权益", f"${balance.get('Equity', '0')}")
                                st.metric("市值", f"${balance.get('MarketValue', '0')}")
                                st.metric("今日盈亏", f"${balance.get('TodaysProfitLoss', '0')}")
            
            with col2:
                if st.button("📈 查询持仓"):
                    with st.spinner("正在查询持仓..."):
                        positions_data = asyncio.run(ui.get_positions(ui.selected_account['AccountID']))
                        if positions_data:
                            st.success("✅ 持仓查询成功!")
                            positions = positions_data.get('Positions', [])
                            if positions:
                                df = pd.DataFrame(positions)
                                st.dataframe(df)
                            else:
                                st.info("📭 当前无持仓")
            
            with col3:
                if st.button("📋 查询订单"):
                    with st.spinner("正在查询订单..."):
                        orders_data = asyncio.run(ui.get_orders(ui.selected_account['AccountID']))
                        if orders_data:
                            st.success("✅ 订单查询成功!")
                            orders = orders_data.get('Orders', [])
                            if orders:
                                df = pd.DataFrame(orders)
                                st.dataframe(df)
                            else:
                                st.info("📭 当前无订单")
        else:
            st.warning("⚠️ 请先选择账户")
    
    with tab2:
        st.header("💰 交易操作")
        
        if ui.selected_account:
            # 交易品种选择
            col1, col2 = st.columns([2, 1])
            
            with col1:
                symbol = st.text_input("交易代码:", value="AAPL", placeholder="输入股票代码")
            
            with col2:
                if st.button("🔍 获取价格"):
                    with st.spinner("正在获取价格..."):
                        quote_data = asyncio.run(ui.get_quote(symbol))
                        if quote_data:
                            st.success(f"✅ {symbol} 价格获取成功!")
                            # 这里需要根据实际API返回格式显示价格
                            st.info(f"当前价格: ${quote_data}")
            
            st.markdown("---")
            
            # 交易操作
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 做多操作")
                
                quantity_long = st.number_input("做多数量:", min_value=1, value=100, key="long_qty")
                
                col1_1, col1_2 = st.columns(2)
                with col1_1:
                    if st.button("🚀 市价做多", key="market_long"):
                        with st.spinner("正在下单..."):
                            result = asyncio.run(ui.place_order(
                                ui.selected_account['AccountID'], 
                                symbol, 
                                quantity_long, 
                                "Buy", 
                                "Market"
                            ))
                            if result:
                                st.success("✅ 做多订单提交成功!")
                            else:
                                st.error("❌ 做多订单提交失败!")
                
                with col1_2:
                    limit_price_long = st.number_input("限价:", min_value=0.01, value=150.0, step=0.01, key="long_price")
                    if st.button("🎯 限价做多", key="limit_long"):
                        with st.spinner("正在下单..."):
                            result = asyncio.run(ui.place_order(
                                ui.selected_account['AccountID'], 
                                symbol, 
                                quantity_long, 
                                "Buy", 
                                "Limit", 
                                limit_price_long
                            ))
                            if result:
                                st.success("✅ 限价做多订单提交成功!")
                            else:
                                st.error("❌ 限价做多订单提交失败!")
                
                if st.button("🔴 做多平仓", key="close_long"):
                    with st.spinner("正在平仓..."):
                        result = asyncio.run(ui.close_position(
                            ui.selected_account['AccountID'], 
                            symbol, 
                            quantity_long, 
                            "Long"
                        ))
                        if result:
                            st.success("✅ 做多平仓成功!")
                        else:
                            st.error("❌ 做多平仓失败!")
            
            with col2:
                st.subheader("📉 做空操作")
                
                quantity_short = st.number_input("做空数量:", min_value=1, value=100, key="short_qty")
                
                col2_1, col2_2 = st.columns(2)
                with col2_1:
                    if st.button("🚀 市价做空", key="market_short"):
                        with st.spinner("正在下单..."):
                            result = asyncio.run(ui.place_order(
                                ui.selected_account['AccountID'], 
                                symbol, 
                                quantity_short, 
                                "Sell", 
                                "Market"
                            ))
                            if result:
                                st.success("✅ 做空订单提交成功!")
                            else:
                                st.error("❌ 做空订单提交失败!")
                
                with col2_2:
                    limit_price_short = st.number_input("限价:", min_value=0.01, value=150.0, step=0.01, key="short_price")
                    if st.button("🎯 限价做空", key="limit_short"):
                        with st.spinner("正在下单..."):
                            result = asyncio.run(ui.place_order(
                                ui.selected_account['AccountID'], 
                                symbol, 
                                quantity_short, 
                                "Sell", 
                                "Limit", 
                                limit_price_short
                            ))
                            if result:
                                st.success("✅ 限价做空订单提交成功!")
                            else:
                                st.error("❌ 限价做空订单提交失败!")
                
                if st.button("🟢 做空平仓", key="close_short"):
                    with st.spinner("正在平仓..."):
                        result = asyncio.run(ui.close_position(
                            ui.selected_account['AccountID'], 
                            symbol, 
                            quantity_short, 
                            "Short"
                        ))
                        if result:
                            st.success("✅ 做空平仓成功!")
                        else:
                            st.error("❌ 做空平仓失败!")
        else:
            st.warning("⚠️ 请先选择账户")
    
    with tab3:
        st.header("📈 市场数据")
        
        # 交易品种选择
        col1, col2 = st.columns([2, 1])
        
        with col1:
            symbol_market = st.text_input("查询代码:", value="AAPL", placeholder="输入股票代码", key="market_symbol")
        
        with col2:
            if st.button("🔍 获取即时价格", key="get_quote"):
                with st.spinner("正在获取价格..."):
                    quote_data = asyncio.run(ui.get_quote(symbol_market))
                    if quote_data:
                        st.success(f"✅ {symbol_market} 价格获取成功!")
                        st.metric("当前价格", f"${quote_data}")
                    else:
                        st.error("❌ 价格获取失败!")
        
        st.markdown("---")
        
        # K线数据
        st.subheader("📊 K线数据")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            interval = st.selectbox("时间周期:", ["1min", "5min", "15min", "1hour", "1day"])
        
        with col2:
            count = st.number_input("数据条数:", min_value=10, max_value=1000, value=100)
        
        with col3:
            if st.button("📈 获取K线数据"):
                with st.spinner("正在获取K线数据..."):
                    market_data = asyncio.run(ui.get_market_data(symbol_market, interval, count))
                    if market_data:
                        st.success("✅ K线数据获取成功!")
                        
                        # 这里需要根据实际API返回格式处理数据
                        # 假设返回格式为 {'Bars': [{'Time': '...', 'Open': 100, 'High': 105, 'Low': 95, 'Close': 102, 'Volume': 1000}]}
                        bars = market_data.get('Bars', [])
                        if bars:
                            # 创建K线图
                            fig = go.Figure(data=go.Candlestick(
                                x=[bar.get('Time', '') for bar in bars],
                                open=[bar.get('Open', 0) for bar in bars],
                                high=[bar.get('High', 0) for bar in bars],
                                low=[bar.get('Low', 0) for bar in bars],
                                close=[bar.get('Close', 0) for bar in bars]
                            ))
                            
                            fig.update_layout(
                                title=f"{symbol_market} K线图 ({interval})",
                                xaxis_title="时间",
                                yaxis_title="价格",
                                height=500
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("📭 无K线数据")
                    else:
                        st.error("❌ K线数据获取失败!")
    
    with tab4:
        st.header("📋 订单管理")
        
        if ui.selected_account:
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🔄 刷新订单"):
                    with st.spinner("正在刷新订单..."):
                        orders_data = asyncio.run(ui.get_orders(ui.selected_account['AccountID']))
                        if orders_data:
                            st.success("✅ 订单刷新成功!")
                            orders = orders_data.get('Orders', [])
                            if orders:
                                df = pd.DataFrame(orders)
                                st.dataframe(df)
                            else:
                                st.info("📭 当前无订单")
            
            with col2:
                if st.button("📊 刷新持仓"):
                    with st.spinner("正在刷新持仓..."):
                        positions_data = asyncio.run(ui.get_positions(ui.selected_account['AccountID']))
                        if positions_data:
                            st.success("✅ 持仓刷新成功!")
                            positions = positions_data.get('Positions', [])
                            if positions:
                                df = pd.DataFrame(positions)
                                st.dataframe(df)
                            else:
                                st.info("📭 当前无持仓")
        else:
            st.warning("⚠️ 请先选择账户")
    
    with tab5:
        st.header("⚙️ 系统设置")
        
        st.subheader("🔐 认证状态")
        
        # 显示令牌信息
        try:
            with open("tokens.json", "r") as f:
                tokens = json.load(f)
            
            st.success("✅ 认证令牌已加载")
            st.info(f"访问令牌: {tokens.get('access_token', '')[:20]}...")
            st.info(f"刷新令牌: {tokens.get('refresh_token', '')[:20]}...")
            st.info(f"过期时间: {tokens.get('expires_at', 'N/A')}")
            
        except FileNotFoundError:
            st.error("❌ 未找到认证令牌文件")
            st.info("请先运行认证程序: python auth_helper_persistent.py")
        
        st.markdown("---")
        
        st.subheader("📊 系统信息")
        st.info(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        st.info(f"Python版本: {sys.version}")
        st.info(f"Streamlit版本: {st.__version__}")


if __name__ == "__main__":
    import subprocess
    import sys
    
    # 检查是否是直接运行
    if len(sys.argv) > 1 and sys.argv[1] == "--server.port":
        # 如果传入了端口参数，启动streamlit
        port = sys.argv[2] if len(sys.argv) > 2 else "8502"
        subprocess.run([sys.executable, "-m", "streamlit", "run", __file__, "--server.port", port])
    else:
        # 否则直接运行main函数
        main()
