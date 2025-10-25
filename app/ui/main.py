"""
基础UI界面 - 品种选择和数据展示
"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from app.data.processor import DataProcessor
from app.data.storage import DataStorage
from app.services.tradestation_client import TradestationAPIClient


class TradingUI:
    """交易界面"""
    
    def __init__(self):
        self.processor = DataProcessor()
        self.storage = DataStorage()
        self.client = TradestationAPIClient()
        
    def run(self):
        """运行UI界面"""
        st.set_page_config(
            page_title="Tradestation 自动化交易策略",
            page_icon="📈",
            layout="wide"
        )
        
        st.title("📈 Tradestation 自动化交易策略系统")
        st.markdown("---")
        
        # 侧边栏 - 品种选择
        self._render_sidebar()
        
        # 主界面
        self._render_main_content()
    
    def _render_sidebar(self):
        """渲染侧边栏"""
        st.sidebar.title("🔧 控制面板")
        
        # 品种选择
        st.sidebar.subheader("📊 交易品种")
        
        # 获取可用品种
        symbols = self._get_available_symbols()
        selected_symbol = st.sidebar.selectbox(
            "选择交易品种",
            symbols,
            index=0 if symbols else None
        )
        
        # 时间周期选择
        intervals = ["1min", "5min", "15min", "30min", "1hour", "4hour", "1day"]
        selected_interval = st.sidebar.selectbox(
            "选择时间周期",
            intervals,
            index=0
        )
        
        # 数据范围选择
        st.sidebar.subheader("📅 数据范围")
        days_back = st.sidebar.slider("数据天数", 1, 30, 7)
        
        # 刷新按钮
        if st.sidebar.button("🔄 刷新数据"):
            st.rerun()
        
        # 存储选择到session state
        st.session_state.selected_symbol = selected_symbol
        st.session_state.selected_interval = selected_interval
        st.session_state.days_back = days_back
    
    def _render_main_content(self):
        """渲染主内容"""
        if not hasattr(st.session_state, 'selected_symbol'):
            st.info("请在左侧选择交易品种")
            return
        
        symbol = st.session_state.selected_symbol
        interval = st.session_state.selected_interval
        days_back = st.session_state.days_back
        
        # 显示品种信息
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("交易品种", symbol)
        with col2:
            st.metric("时间周期", interval)
        with col3:
            st.metric("数据天数", days_back)
        
        st.markdown("---")
        
        # 加载数据
        with st.spinner(f"正在加载 {symbol} 数据..."):
            df = self._load_data(symbol, interval, days_back)
        
        if df.empty:
            st.error(f"未找到 {symbol} 的数据")
            return
        
        # 显示数据统计
        self._render_data_stats(df)
        
        # 显示图表
        self._render_charts(df, symbol)
        
        # 显示数据表
        self._render_data_table(df)
    
    def _get_available_symbols(self) -> List[str]:
        """获取可用交易品种"""
        # 从数据库获取已存储的品种
        db_symbols = self.storage.get_symbols_from_db()
        
        # 默认品种列表
        default_symbols = [
            "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA",
            "NVDA", "META", "NFLX", "AMD", "INTC",
            "SPY", "QQQ", "IWM", "GLD", "TLT"
        ]
        
        # 合并并去重
        all_symbols = list(set(db_symbols + default_symbols))
        return sorted(all_symbols)
    
    def _load_data(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """加载数据"""
        try:
            # 计算时间范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            # 先从缓存获取
            cache_key = f"{symbol}_{interval}_{days_back}"
            cached_data = self.storage.get_cached_data(cache_key)
            
            if cached_data is not None:
                return cached_data
            
            # 从数据库获取
            df = self.storage.get_market_data(
                symbol, interval, start_date, end_date
            )
            
            if df.empty:
                # 如果数据库没有数据，尝试从API获取
                df = asyncio.run(self._fetch_from_api(symbol, interval, days_back))
                
                if not df.empty:
                    # 保存到数据库
                    self.storage.save_market_data(df, symbol, interval)
            
            # 缓存数据
            if not df.empty:
                self.storage.cache_data(cache_key, df)
            
            return df
            
        except Exception as e:
            st.error(f"加载数据失败: {str(e)}")
            return pd.DataFrame()
    
    async def _fetch_from_api(self, symbol: str, interval: str, days_back: int) -> pd.DataFrame:
        """从API获取数据"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            
            df = await self.processor.get_and_process_data(
                symbol, interval, 
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d")
            )
            return df
            
        except Exception as e:
            print(f"从API获取数据失败: {str(e)}")
            return pd.DataFrame()
    
    def _render_data_stats(self, df: pd.DataFrame):
        """渲染数据统计"""
        st.subheader("📊 数据统计")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("数据条数", len(df))
        
        with col2:
            latest_price = df['close'].iloc[-1]
            st.metric("最新价格", f"${latest_price:.2f}")
        
        with col3:
            price_change = df['close'].iloc[-1] - df['close'].iloc[0]
            st.metric("价格变化", f"${price_change:.2f}")
        
        with col4:
            volume_avg = df['volume'].mean()
            st.metric("平均成交量", f"{volume_avg:,.0f}")
    
    def _render_charts(self, df: pd.DataFrame, symbol: str):
        """渲染图表"""
        st.subheader("📈 价格图表")
        
        # 创建子图
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.1,
            subplot_titles=(f"{symbol} 价格走势", "成交量"),
            row_heights=[0.7, 0.3]
        )
        
        # K线图
        fig.add_trace(
            go.Candlestick(
                x=df['timestamp'],
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name="K线"
            ),
            row=1, col=1
        )
        
        # 移动平均线
        if 'ma_20' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['ma_20'],
                    name="MA20",
                    line=dict(color='orange', width=1)
                ),
                row=1, col=1
            )
        
        # 成交量
        fig.add_trace(
            go.Bar(
                x=df['timestamp'],
                y=df['volume'],
                name="成交量",
                marker_color='lightblue'
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title=f"{symbol} 技术分析图表",
            xaxis_rangeslider_visible=False,
            height=600,
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 技术指标图表
        if 'rsi' in df.columns:
            self._render_technical_indicators(df)
    
    def _render_technical_indicators(self, df: pd.DataFrame):
        """渲染技术指标"""
        st.subheader("🔍 技术指标")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # RSI
            fig_rsi = go.Figure()
            fig_rsi.add_trace(
                go.Scatter(
                    x=df['timestamp'],
                    y=df['rsi'],
                    name="RSI",
                    line=dict(color='purple')
                )
            )
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="red", annotation_text="超买")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="green", annotation_text="超卖")
            fig_rsi.update_layout(title="RSI指标", height=300)
            st.plotly_chart(fig_rsi, use_container_width=True)
        
        with col2:
            # MACD
            if 'macd' in df.columns:
                fig_macd = go.Figure()
                fig_macd.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['macd'],
                        name="MACD",
                        line=dict(color='blue')
                    )
                )
                fig_macd.add_trace(
                    go.Scatter(
                        x=df['timestamp'],
                        y=df['macd_signal'],
                        name="Signal",
                        line=dict(color='red')
                    )
                )
                fig_macd.add_trace(
                    go.Bar(
                        x=df['timestamp'],
                        y=df['macd_histogram'],
                        name="Histogram",
                        marker_color='gray'
                    )
                )
                fig_macd.update_layout(title="MACD指标", height=300)
                st.plotly_chart(fig_macd, use_container_width=True)
    
    def _render_data_table(self, df: pd.DataFrame):
        """渲染数据表"""
        st.subheader("📋 数据详情")
        
        # 显示最新20条数据
        display_df = df.tail(20).copy()
        display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # 下载按钮
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 下载数据",
            data=csv,
            file_name=f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )


def main():
    """主函数"""
    ui = TradingUI()
    ui.run()


if __name__ == "__main__":
    main()
