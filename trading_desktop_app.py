"""
Tradestation 桌面版交易测试程序 - PyQt5
简单直接的桌面应用程序
"""
import sys
import json
import asyncio
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QGridLayout, QLabel, QPushButton, 
                             QLineEdit, QTextEdit, QComboBox, QTabWidget,
                             QTableWidget, QTableWidgetItem, QMessageBox,
                             QGroupBox, QSpinBox, QDoubleSpinBox, QProgressBar)
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from app.services.tradestation_client import TradestationAPIClient


class APIClientThread(QThread):
    """API客户端线程"""
    result_ready = pyqtSignal(str, object)  # 信号：操作类型，结果数据
    error_occurred = pyqtSignal(str, str)   # 信号：操作类型，错误信息
    
    def __init__(self):
        super().__init__()
        self.client = None
        self.operation = None
        self.params = {}
        
    def load_tokens(self):
        """加载令牌"""
        try:
            with open("tokens.json", "r") as f:
                tokens = json.load(f)
            
            self.client = TradestationAPIClient()
            self.client.access_token = tokens["access_token"]
            self.client.refresh_token = tokens["refresh_token"]
            
            if tokens["expires_at"]:
                from datetime import datetime
                self.client.token_expires_at = datetime.fromisoformat(tokens["expires_at"])
            
            return True
        except Exception as e:
            self.error_occurred.emit("load_tokens", str(e))
            return False
    
    def set_operation(self, operation, **params):
        """设置操作"""
        self.operation = operation
        self.params = params
    
    def run(self):
        """运行API操作"""
        if not self.client:
            if not self.load_tokens():
                return
        
        try:
            if self.operation == "get_accounts":
                result = asyncio.run(self._get_accounts())
            elif self.operation == "get_balance":
                result = asyncio.run(self._get_balance())
            elif self.operation == "get_positions":
                result = asyncio.run(self._get_positions())
            elif self.operation == "get_orders":
                result = asyncio.run(self._get_orders())
            elif self.operation == "get_quote":
                result = asyncio.run(self._get_quote())
            elif self.operation == "get_market_data":
                result = asyncio.run(self._get_market_data())
            elif self.operation == "place_order":
                result = asyncio.run(self._place_order())
            elif self.operation == "close_position":
                result = asyncio.run(self._close_position())
            else:
                result = None
            
            self.result_ready.emit(self.operation, result)
            
        except Exception as e:
            self.error_occurred.emit(self.operation, str(e))
    
    async def _get_accounts(self):
        """获取账户列表"""
        async with self.client as c:
            return await c.get_accounts()
    
    async def _get_balance(self):
        """获取账户余额"""
        async with self.client as c:
            return await c.get_account_balance(self.params['account_id'])
    
    async def _get_positions(self):
        """获取持仓"""
        async with self.client as c:
            return await c.get_positions(self.params['account_id'])
    
    async def _get_orders(self):
        """获取订单"""
        async with self.client as c:
            return await c.get_orders(self.params['account_id'])
    
    async def _get_quote(self):
        """获取报价"""
        async with self.client as c:
            return await c.get_quote(self.params['symbol'])
    
    async def _get_market_data(self):
        """获取市场数据"""
        async with self.client as c:
            return await c.get_market_data(
                self.params['symbol'], 
                self.params.get('interval', '1min'),
                count=self.params.get('count', 100)
            )
    
    async def _place_order(self):
        """下单"""
        async with self.client as c:
            return await c.place_order(
                self.params['account_id'],
                self.params['symbol'],
                self.params['quantity'],
                self.params['side'],
                self.params.get('order_type', 'Market'),
                self.params.get('price')
            )
    
    async def _close_position(self):
        """平仓"""
        async with self.client as c:
            return await c.close_position(
                self.params['account_id'],
                self.params['symbol'],
                self.params['quantity'],
                self.params['side']
            )


class TradingApp(QMainWindow):
    """交易应用程序主窗口"""
    
    def __init__(self):
        super().__init__()
        self.api_thread = APIClientThread()
        self.api_thread.result_ready.connect(self.on_api_result)
        self.api_thread.error_occurred.connect(self.on_api_error)
        
        self.accounts = []
        self.selected_account = None
        
        self.init_ui()
        self.setup_connections()
        
    def init_ui(self):
        """初始化UI"""
        self.setWindowTitle("Tradestation 交易测试系统")
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中央widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # 创建各个标签页
        self.create_account_tab()
        self.create_trading_tab()
        self.create_market_data_tab()
        self.create_orders_tab()
        
        # 状态栏
        self.statusBar().showMessage("就绪")
        
    def create_account_tab(self):
        """创建账户查询标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 账户选择区域
        account_group = QGroupBox("账户选择")
        account_layout = QHBoxLayout(account_group)
        
        self.account_combo = QComboBox()
        self.account_combo.setMinimumWidth(200)
        account_layout.addWidget(QLabel("选择账户:"))
        account_layout.addWidget(self.account_combo)
        
        refresh_accounts_btn = QPushButton("刷新账户")
        refresh_accounts_btn.clicked.connect(self.refresh_accounts)
        account_layout.addWidget(refresh_accounts_btn)
        
        layout.addWidget(account_group)
        
        # 账户信息区域
        info_group = QGroupBox("账户信息")
        info_layout = QGridLayout(info_group)
        
        self.account_id_label = QLabel("账户ID: -")
        self.account_type_label = QLabel("账户类型: -")
        self.account_status_label = QLabel("状态: -")
        
        info_layout.addWidget(self.account_id_label, 0, 0)
        info_layout.addWidget(self.account_type_label, 0, 1)
        info_layout.addWidget(self.account_status_label, 1, 0)
        
        layout.addWidget(info_group)
        
        # 查询按钮区域
        query_group = QGroupBox("查询操作")
        query_layout = QGridLayout(query_group)
        
        balance_btn = QPushButton("查询余额")
        balance_btn.clicked.connect(self.query_balance)
        query_layout.addWidget(balance_btn, 0, 0)
        
        positions_btn = QPushButton("查询持仓")
        positions_btn.clicked.connect(self.query_positions)
        query_layout.addWidget(positions_btn, 0, 1)
        
        orders_btn = QPushButton("查询订单")
        orders_btn.clicked.connect(self.query_orders)
        query_layout.addWidget(orders_btn, 0, 2)
        
        layout.addWidget(query_group)
        
        # 结果显示区域
        result_group = QGroupBox("查询结果")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setMaximumHeight(200)
        result_layout.addWidget(self.result_text)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "📊 账户查询")
        
    def create_trading_tab(self):
        """创建交易操作标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 交易设置区域
        settings_group = QGroupBox("交易设置")
        settings_layout = QGridLayout(settings_group)
        
        settings_layout.addWidget(QLabel("交易代码:"), 0, 0)
        self.symbol_input = QLineEdit()
        self.symbol_input.setText("AAPL")
        settings_layout.addWidget(self.symbol_input, 0, 1)
        
        settings_layout.addWidget(QLabel("数量:"), 0, 2)
        self.quantity_input = QSpinBox()
        self.quantity_input.setRange(1, 10000)
        self.quantity_input.setValue(100)
        settings_layout.addWidget(self.quantity_input, 0, 3)
        
        layout.addWidget(settings_group)
        
        # 做多操作区域
        long_group = QGroupBox("📈 做多操作")
        long_layout = QGridLayout(long_group)
        
        long_layout.addWidget(QLabel("限价:"), 0, 0)
        self.long_price_input = QDoubleSpinBox()
        self.long_price_input.setRange(0.01, 10000.0)
        self.long_price_input.setValue(150.0)
        self.long_price_input.setDecimals(2)
        long_layout.addWidget(self.long_price_input, 0, 1)
        
        market_long_btn = QPushButton("市价做多")
        market_long_btn.clicked.connect(lambda: self.place_order("Buy", "Market"))
        long_layout.addWidget(market_long_btn, 0, 2)
        
        limit_long_btn = QPushButton("限价做多")
        limit_long_btn.clicked.connect(lambda: self.place_order("Buy", "Limit"))
        long_layout.addWidget(limit_long_btn, 0, 3)
        
        close_long_btn = QPushButton("做多平仓")
        close_long_btn.clicked.connect(lambda: self.close_position("Long"))
        long_layout.addWidget(close_long_btn, 1, 2)
        
        layout.addWidget(long_group)
        
        # 做空操作区域
        short_group = QGroupBox("📉 做空操作")
        short_layout = QGridLayout(short_group)
        
        short_layout.addWidget(QLabel("限价:"), 0, 0)
        self.short_price_input = QDoubleSpinBox()
        self.short_price_input.setRange(0.01, 10000.0)
        self.short_price_input.setValue(150.0)
        self.short_price_input.setDecimals(2)
        short_layout.addWidget(self.short_price_input, 0, 1)
        
        market_short_btn = QPushButton("市价做空")
        market_short_btn.clicked.connect(lambda: self.place_order("Sell", "Market"))
        short_layout.addWidget(market_short_btn, 0, 2)
        
        limit_short_btn = QPushButton("限价做空")
        limit_short_btn.clicked.connect(lambda: self.place_order("Sell", "Limit"))
        short_layout.addWidget(limit_short_btn, 0, 3)
        
        close_short_btn = QPushButton("做空平仓")
        close_short_btn.clicked.connect(lambda: self.close_position("Short"))
        short_layout.addWidget(close_short_btn, 1, 2)
        
        layout.addWidget(short_group)
        
        # 交易结果显示
        trade_result_group = QGroupBox("交易结果")
        trade_result_layout = QVBoxLayout(trade_result_group)
        
        self.trade_result_text = QTextEdit()
        self.trade_result_text.setMaximumHeight(150)
        trade_result_layout.addWidget(self.trade_result_text)
        
        layout.addWidget(trade_result_group)
        
        self.tab_widget.addTab(tab, "💰 交易操作")
        
    def create_market_data_tab(self):
        """创建市场数据标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 查询设置区域
        query_group = QGroupBox("查询设置")
        query_layout = QGridLayout(query_group)
        
        query_layout.addWidget(QLabel("交易代码:"), 0, 0)
        self.market_symbol_input = QLineEdit()
        self.market_symbol_input.setText("AAPL")
        query_layout.addWidget(self.market_symbol_input, 0, 1)
        
        query_layout.addWidget(QLabel("时间周期:"), 0, 2)
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1min", "5min", "15min", "1hour", "1day"])
        query_layout.addWidget(self.interval_combo, 0, 3)
        
        query_layout.addWidget(QLabel("数据条数:"), 1, 0)
        self.count_input = QSpinBox()
        self.count_input.setRange(10, 1000)
        self.count_input.setValue(100)
        query_layout.addWidget(self.count_input, 1, 1)
        
        quote_btn = QPushButton("获取即时价格")
        quote_btn.clicked.connect(self.get_quote)
        query_layout.addWidget(quote_btn, 1, 2)
        
        kline_btn = QPushButton("获取K线数据")
        kline_btn.clicked.connect(self.get_market_data)
        query_layout.addWidget(kline_btn, 1, 3)
        
        layout.addWidget(query_group)
        
        # 结果显示区域
        result_group = QGroupBox("市场数据")
        result_layout = QVBoxLayout(result_group)
        
        self.market_result_text = QTextEdit()
        result_layout.addWidget(self.market_result_text)
        
        layout.addWidget(result_group)
        
        self.tab_widget.addTab(tab, "📈 市场数据")
        
    def create_orders_tab(self):
        """创建订单管理标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # 刷新按钮
        refresh_group = QGroupBox("刷新操作")
        refresh_layout = QHBoxLayout(refresh_group)
        
        refresh_orders_btn = QPushButton("刷新订单")
        refresh_orders_btn.clicked.connect(self.query_orders)
        refresh_layout.addWidget(refresh_orders_btn)
        
        refresh_positions_btn = QPushButton("刷新持仓")
        refresh_positions_btn.clicked.connect(self.query_positions)
        refresh_layout.addWidget(refresh_positions_btn)
        
        layout.addWidget(refresh_group)
        
        # 订单表格
        orders_group = QGroupBox("订单列表")
        orders_layout = QVBoxLayout(orders_group)
        
        self.orders_table = QTableWidget()
        self.orders_table.setColumnCount(6)
        self.orders_table.setHorizontalHeaderLabels(["订单ID", "代码", "方向", "数量", "价格", "状态"])
        orders_layout.addWidget(self.orders_table)
        
        layout.addWidget(orders_group)
        
        # 持仓表格
        positions_group = QGroupBox("持仓列表")
        positions_layout = QVBoxLayout(positions_group)
        
        self.positions_table = QTableWidget()
        self.positions_table.setColumnCount(5)
        self.positions_table.setHorizontalHeaderLabels(["代码", "方向", "数量", "成本价", "市值"])
        positions_layout.addWidget(self.positions_table)
        
        layout.addWidget(positions_group)
        
        self.tab_widget.addTab(tab, "📋 订单管理")
        
    def setup_connections(self):
        """设置信号连接"""
        self.account_combo.currentTextChanged.connect(self.on_account_changed)
        
    def refresh_accounts(self):
        """刷新账户列表"""
        self.statusBar().showMessage("正在刷新账户...")
        self.api_thread.set_operation("get_accounts")
        self.api_thread.start()
        
    def on_account_changed(self, text):
        """账户选择改变"""
        if text and self.accounts:
            for account in self.accounts:
                if f"{account['AccountID']} ({account['AccountType']})" == text:
                    self.selected_account = account
                    self.update_account_info()
                    break
                    
    def update_account_info(self):
        """更新账户信息显示"""
        if self.selected_account:
            self.account_id_label.setText(f"账户ID: {self.selected_account['AccountID']}")
            self.account_type_label.setText(f"账户类型: {self.selected_account['AccountType']}")
            self.account_status_label.setText(f"状态: {self.selected_account['Status']}")
        else:
            self.account_id_label.setText("账户ID: -")
            self.account_type_label.setText("账户类型: -")
            self.account_status_label.setText("状态: -")
            
    def query_balance(self):
        """查询余额"""
        if not self.selected_account:
            QMessageBox.warning(self, "警告", "请先选择账户!")
            return
            
        self.statusBar().showMessage("正在查询余额...")
        self.api_thread.set_operation("get_balance", account_id=self.selected_account['AccountID'])
        self.api_thread.start()
        
    def query_positions(self):
        """查询持仓"""
        if not self.selected_account:
            QMessageBox.warning(self, "警告", "请先选择账户!")
            return
            
        self.statusBar().showMessage("正在查询持仓...")
        self.api_thread.set_operation("get_positions", account_id=self.selected_account['AccountID'])
        self.api_thread.start()
        
    def query_orders(self):
        """查询订单"""
        if not self.selected_account:
            QMessageBox.warning(self, "警告", "请先选择账户!")
            return
            
        self.statusBar().showMessage("正在查询订单...")
        self.api_thread.set_operation("get_orders", account_id=self.selected_account['AccountID'])
        self.api_thread.start()
        
    def get_quote(self):
        """获取报价"""
        symbol = self.market_symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "警告", "请输入交易代码!")
            return
            
        self.statusBar().showMessage(f"正在获取 {symbol} 的报价...")
        self.api_thread.set_operation("get_quote", symbol=symbol)
        self.api_thread.start()
        
    def get_market_data(self):
        """获取市场数据"""
        symbol = self.market_symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "警告", "请输入交易代码!")
            return
            
        self.statusBar().showMessage(f"正在获取 {symbol} 的K线数据...")
        self.api_thread.set_operation("get_market_data", 
                                     symbol=symbol,
                                     interval=self.interval_combo.currentText(),
                                     count=self.count_input.value())
        self.api_thread.start()
        
    def place_order(self, side, order_type):
        """下单"""
        if not self.selected_account:
            QMessageBox.warning(self, "警告", "请先选择账户!")
            return
            
        # 检查账户状态
        account_status = self.selected_account.get('Status', '')
        if account_status == 'Closing Transactions Only':
            reply = QMessageBox.question(self, "⚠️ 实盘账户警告", 
                                       f"当前账户状态: {account_status}\n"
                                       f"这是实盘账户，下单将使用真实资金！\n\n"
                                       f"确定要继续吗？",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return
        
        symbol = self.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "警告", "请输入交易代码!")
            return
            
        quantity = self.quantity_input.value()
        price = None
        
        if order_type == "Limit":
            if side == "Buy":
                price = self.long_price_input.value()
            else:
                price = self.short_price_input.value()
        
        self.statusBar().showMessage(f"正在提交{side}订单...")
        self.api_thread.set_operation("place_order",
                                     account_id=self.selected_account['AccountID'],
                                     symbol=symbol,
                                     quantity=quantity,
                                     side=side,
                                     order_type=order_type,
                                     price=price)
        self.api_thread.start()
        
    def close_position(self, side):
        """平仓"""
        if not self.selected_account:
            QMessageBox.warning(self, "警告", "请先选择账户!")
            return
            
        symbol = self.symbol_input.text().strip()
        if not symbol:
            QMessageBox.warning(self, "警告", "请输入交易代码!")
            return
            
        quantity = self.quantity_input.value()
        
        self.statusBar().showMessage(f"正在平仓{side}...")
        self.api_thread.set_operation("close_position",
                                     account_id=self.selected_account['AccountID'],
                                     symbol=symbol,
                                     quantity=quantity,
                                     side=side)
        self.api_thread.start()
        
    def on_api_result(self, operation, result):
        """API结果处理"""
        self.statusBar().showMessage("操作完成")
        
        if operation == "get_accounts":
            self.accounts = result.get("Accounts", [])
            self.account_combo.clear()
            for account in self.accounts:
                self.account_combo.addItem(f"{account['AccountID']} ({account['AccountType']})")
            self.result_text.append(f"✅ 加载了 {len(self.accounts)} 个账户")
            
        elif operation == "get_balance":
            balances = result.get("Balances", [])
            if balances:
                balance = balances[0]
                balance_text = f"""
✅ 账户余额查询成功!
现金余额: ${balance.get('CashBalance', '0')}
购买力: ${balance.get('BuyingPower', '0')}
权益: ${balance.get('Equity', '0')}
市值: ${balance.get('MarketValue', '0')}
今日盈亏: ${balance.get('TodaysProfitLoss', '0')}
"""
                self.result_text.append(balance_text)
            else:
                self.result_text.append("❌ 未找到余额信息")
                
        elif operation == "get_positions":
            positions = result.get("Positions", [])
            if positions:
                self.result_text.append(f"✅ 查询到 {len(positions)} 个持仓")
                # 更新持仓表格
                self.positions_table.setRowCount(len(positions))
                for i, pos in enumerate(positions):
                    self.positions_table.setItem(i, 0, QTableWidgetItem(str(pos.get('Symbol', ''))))
                    self.positions_table.setItem(i, 1, QTableWidgetItem(str(pos.get('Side', ''))))
                    self.positions_table.setItem(i, 2, QTableWidgetItem(str(pos.get('Quantity', ''))))
                    self.positions_table.setItem(i, 3, QTableWidgetItem(str(pos.get('AveragePrice', ''))))
                    self.positions_table.setItem(i, 4, QTableWidgetItem(str(pos.get('MarketValue', ''))))
            else:
                self.result_text.append("📭 当前无持仓")
                
        elif operation == "get_orders":
            orders = result.get("Orders", [])
            if orders:
                self.result_text.append(f"✅ 查询到 {len(orders)} 个订单")
                # 更新订单表格
                self.orders_table.setRowCount(len(orders))
                for i, order in enumerate(orders):
                    self.orders_table.setItem(i, 0, QTableWidgetItem(str(order.get('OrderID', ''))))
                    self.orders_table.setItem(i, 1, QTableWidgetItem(str(order.get('Symbol', ''))))
                    self.orders_table.setItem(i, 2, QTableWidgetItem(str(order.get('Side', ''))))
                    self.orders_table.setItem(i, 3, QTableWidgetItem(str(order.get('Quantity', ''))))
                    self.orders_table.setItem(i, 4, QTableWidgetItem(str(order.get('Price', ''))))
                    self.orders_table.setItem(i, 5, QTableWidgetItem(str(order.get('Status', ''))))
            else:
                self.result_text.append("📭 当前无订单")
                
        elif operation == "get_quote":
            self.market_result_text.append(f"✅ {self.market_symbol_input.text()} 报价: {result}")
            
        elif operation == "get_market_data":
            bars = result.get("Bars", [])
            if bars:
                self.market_result_text.append(f"✅ 获取到 {len(bars)} 条K线数据")
                # 显示前几条数据
                for i, bar in enumerate(bars[:5]):
                    self.market_result_text.append(f"  {i+1}. 时间: {bar.get('Time', '')}, 开盘: {bar.get('Open', '')}, 收盘: {bar.get('Close', '')}")
            else:
                self.market_result_text.append("❌ 未获取到K线数据")
                
        elif operation == "place_order":
            if result:
                self.trade_result_text.append("✅ 订单提交成功!")
            else:
                self.trade_result_text.append("❌ 订单提交失败!")
                
        elif operation == "close_position":
            if result:
                self.trade_result_text.append("✅ 平仓成功!")
            else:
                self.trade_result_text.append("❌ 平仓失败!")
                
    def on_api_error(self, operation, error):
        """API错误处理"""
        self.statusBar().showMessage("操作失败")
        
        if operation == "load_tokens":
            QMessageBox.critical(self, "错误", f"加载令牌失败: {error}\n请先运行认证程序!")
        else:
            QMessageBox.warning(self, "错误", f"{operation} 操作失败: {error}")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("Tradestation 交易测试系统")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = TradingApp()
    window.show()
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
