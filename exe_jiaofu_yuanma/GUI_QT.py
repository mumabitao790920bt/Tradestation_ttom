import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
import pymysql
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None
    print("警告: PyQt5.QtWebEngineWidgets 导入失败，图表预览将使用外部浏览器")

# 引入策略对外函数
from strategy_part2 import run_strategy_once
import requests
import json


def check_remote_authorization():
    """检查远程授权（与 main_app.py 一致的方式）"""
    try:
        db_config = {
            'host': '115.159.44.226',
            'port': 3306,
            'user': 'xianyu',
            'password': 'zxz2jwwRTYmMkpyT',
            'database': 'xianyu',
            'charset': 'utf8mb4'
        }
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM xianyu_account WHERE phone = 'pengpeng'"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] > 0
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
        return False


class StrategyThread(QtCore.QThread):
    """策略执行线程"""
    
    # 定义信号
    strategy_finished = QtCore.pyqtSignal(dict)  # 策略执行完成信号
    strategy_error = QtCore.pyqtSignal(str)      # 策略执行错误信号
    
    def __init__(self, params):
        super().__init__()
        self.params = params
        self.is_running = True
    
    def run(self):
        """在线程中执行策略"""
        try:
            if not self.is_running:
                return
            
            # 执行策略计算
            res = run_strategy_once(**self.params)
            
            if not self.is_running:
                return
            
            # 发送完成信号
            self.strategy_finished.emit(res)
                
        except Exception as e:
            if self.is_running:
                self.strategy_error.emit(str(e))
    
    def stop(self):
        """停止线程"""
        self.is_running = False


class StrategyGUI(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('超级趋势 双周期策略 - 参数面板')
        self.resize(720, 520)

        # 控件
        self.db_path_edit = QtWidgets.QLineEdit('BTCUSDT_futures_data.db')  # 默认数据库路径
        self.db_browse_btn = QtWidgets.QPushButton('选择数据库...')
        self.code_edit = QtWidgets.QLineEdit('BTCUSDT')  # 默认与合约选择一致
        self.table_low_edit = QtWidgets.QLineEdit('min_data15')
        self.table_high_edit = QtWidgets.QLineEdit('min_data60')

        self.limit_spin = QtWidgets.QSpinBox()
        self.limit_spin.setRange(100, 200000)
        self.limit_spin.setValue(4000)

        self.interval_combo = QtWidgets.QComboBox()
        self.interval_combo.addItems(['1', '5', '10', '15'])
        self.interval_combo.setCurrentText('5')

        self.take_profit_factor_double = QtWidgets.QDoubleSpinBox()
        self.take_profit_factor_double.setRange(0.1, 10.0)
        self.take_profit_factor_double.setSingleStep(0.1)
        self.take_profit_factor_double.setValue(2.0)
        
        # 添加"按盈亏比平仓"复选框
        self.take_profit_checkbox = QtWidgets.QCheckBox('按盈亏比平仓（不按盈亏比则不设止盈直至15分钟信号线变色再全平）')
        self.take_profit_checkbox.setChecked(False)  # 默认不勾选，即no_TakeProfit=1

        self.st_len = QtWidgets.QSpinBox(); self.st_len.setRange(1, 200); self.st_len.setValue(10)
        self.st_mul = QtWidgets.QDoubleSpinBox(); self.st_mul.setRange(0.1, 20.0); self.st_mul.setSingleStep(0.1); self.st_mul.setValue(3.0)

        self.st_len_60 = QtWidgets.QSpinBox(); self.st_len_60.setRange(1, 200); self.st_len_60.setValue(10)
        self.st_mul_60 = QtWidgets.QDoubleSpinBox(); self.st_mul_60.setRange(0.1, 20.0); self.st_mul_60.setSingleStep(0.1); self.st_mul_60.setValue(3.0)

        self.trade_mode_combo = QtWidgets.QComboBox()
        self.trade_mode_combo.addItems(['both', 'long_only', 'short_only'])

        # 添加合约数量参数
        self.contract_size_spin = QtWidgets.QDoubleSpinBox()
        self.contract_size_spin.setRange(0.001, 10.0)
        self.contract_size_spin.setSingleStep(0.001)
        self.contract_size_spin.setValue(0.001)
        self.contract_size_spin.setDecimals(3)
        
        # 添加交易合约选择下拉菜单
        self.trading_symbol_combo = QtWidgets.QComboBox()
        self.trading_symbol_combo.setEditable(True)
        self.trading_symbol_combo.setMinimumWidth(150)
        self.trading_symbol_combo.addItem('BTCUSDT')  # 默认值
        self.trading_symbol_combo.setCurrentText('BTCUSDT')
        
        # 连接合约选择变化事件
        self.trading_symbol_combo.currentTextChanged.connect(self.on_contract_changed)
        
        # 添加刷新合约列表按钮
        self.refresh_symbols_btn = QtWidgets.QPushButton('刷新合约列表')
        self.refresh_symbols_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")

        # 添加币安API配置
        self.api_key_edit = QtWidgets.QLineEdit()
        self.api_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        self.secret_key_edit = QtWidgets.QLineEdit()
        self.secret_key_edit.setEchoMode(QtWidgets.QLineEdit.Password)
        
        # 添加API测试按钮
        self.test_api_btn = QtWidgets.QPushButton('测试API连接')
        self.test_api_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
        
        # 添加自动交易开关
        self.auto_trade_check = QtWidgets.QCheckBox('启用自动交易')
        self.auto_trade_check.setChecked(False)

        self.start_btn = QtWidgets.QPushButton('启动策略')
        self.stop_btn = QtWidgets.QPushButton('停止')
        self.stop_btn.setEnabled(False)
        
        # 添加保存和加载按钮
        self.save_btn = QtWidgets.QPushButton('保存配置')
        self.load_btn = QtWidgets.QPushButton('加载配置')
        
        # 添加数据下载管理按钮
        self.data_download_btn = QtWidgets.QPushButton('打开数据下载')
        self.data_download_btn.setStyleSheet("QPushButton { background-color: #FF9800; color: white; font-weight: bold; }")
        
        # 添加控制台输出按钮
        self.console_btn = QtWidgets.QPushButton('打开控制台')
        self.console_btn.setStyleSheet("QPushButton { background-color: #9C27B0; color: white; font-weight: bold; }")

        # 是否执行回测（生成HTML图表）
        self.backtest_check = QtWidgets.QCheckBox('执行回测并展示图表(HTML)')
        self.backtest_check.setChecked(True)

        self.log_edit = QtWidgets.QPlainTextEdit()
        self.log_edit.setReadOnly(True)

        # HTML 图表展示区域（可用则内嵌，否则用超链接+外部打开）
        self.chart_label = QtWidgets.QLabel('图表预览:')
        if QWebEngineView is not None:
            self.web_view = QWebEngineView()
            self.web_view.setMinimumHeight(260)
        else:
            self.web_view = None
            self.chart_link = QtWidgets.QLabel()
            self.chart_link.setOpenExternalLinks(True)

        # 顶部参数表单布局（放在上方）
        form = QtWidgets.QFormLayout()
        form.addRow('数据库路径:', self._hbox(self.db_path_edit, self.db_browse_btn))
        form.addRow('代码(code):', self.code_edit)
        form.addRow('小周期表:', self.table_low_edit)
        form.addRow('大周期表:', self.table_high_edit)
        form.addRow('加载数据量(小周期):', self.limit_spin)
        form.addRow('运算间隔(分钟):', self.interval_combo)
        form.addRow('盈亏比(take_profit_factor):', self.take_profit_factor_double)
        form.addRow('', self.take_profit_checkbox)
        form.addRow('小周期 ST length / multiplier:', self._hbox(self.st_len, self.st_mul))
        form.addRow('大周期 ST length / multiplier:', self._hbox(self.st_len_60, self.st_mul_60))
        form.addRow('交易模式:', self.trade_mode_combo)
        form.addRow('合约数量(1份=):', self.contract_size_spin)
        form.addRow('交易合约选择:', self._hbox(self.trading_symbol_combo, self.refresh_symbols_btn))
        form.addRow('币安API Key:', self.api_key_edit)
        form.addRow('币安Secret Key:', self.secret_key_edit)
        form.addRow('API连接测试:', self.test_api_btn)
        form.addRow(self.auto_trade_check)
        form.addRow(self.backtest_check)
        form.addRow(self._hbox(self.start_btn, self.stop_btn))
        form.addRow(self._hbox(self.save_btn, self.load_btn))
        form.addRow(self._hbox(self.data_download_btn, self.console_btn))
        # 主垂直布局：上-参数表单，中-图表，下-日志（缩小）
        main_v = QtWidgets.QVBoxLayout()
        main_v.addLayout(form)

        # 图表区域
        chart_box = QtWidgets.QVBoxLayout()
        chart_box.addWidget(self.chart_label)
        if self.web_view is not None:
            chart_box.addWidget(self.web_view, 1)
        else:
            chart_box.addWidget(self.chart_link, 1)
        main_v.addLayout(chart_box, 1)

        # 日志区域置底且高度缩小为整体约1/10
        log_label = QtWidgets.QLabel('日志:')
        main_v.addWidget(log_label)
        self.log_edit.setMaximumHeight(80)
        self.log_edit.setMinimumHeight(50)
        main_v.addWidget(self.log_edit)

        self.setLayout(main_v)

        # 计时器
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.run_once)

        # 事件
        self.db_browse_btn.clicked.connect(self.on_browse_db)
        self.start_btn.clicked.connect(self.on_start)
        self.stop_btn.clicked.connect(self.on_stop)
        self.save_btn.clicked.connect(self.on_save_config)
        self.load_btn.clicked.connect(self.on_load_config)
        self.test_api_btn.clicked.connect(self.on_test_api)
        self.refresh_symbols_btn.clicked.connect(self.on_refresh_symbols)
        self.data_download_btn.clicked.connect(self.on_open_data_download)
        self.console_btn.clicked.connect(self.on_open_console)
        
        # 自动加载配置
        self.on_load_config()
        
        # 策略执行线程
        self.strategy_thread = None

    def _hbox(self, *widgets):
        w = QtWidgets.QWidget()
        lay = QtWidgets.QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        for x in widgets:
            lay.addWidget(x)
        return w

    def on_browse_db(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, '选择SQLite数据库', os.getcwd(), 'DB Files (*.db *.sqlite);;All Files (*)')
        if path:
            self.db_path_edit.setText(path)

    def on_start(self):
        if not self.db_path_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, '提示', '请选择数据库路径')
            return
        self.append_log('启动策略...')
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        # 立即跑一次
        self.run_once()
        # 按设定间隔循环
        minutes = int(self.interval_combo.currentText())
        self.timer.start(minutes * 60 * 1000)

    def on_stop(self):
        self.timer.stop()
        
        # 停止策略线程
        if self.strategy_thread and self.strategy_thread.isRunning():
            self.strategy_thread.stop()
            self.strategy_thread.wait()
            self.append_log('🛑 策略线程已停止')
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.append_log('✅ 策略已停止')

    def append_log(self, text: str):
        self.log_edit.appendPlainText(text)

    def on_contract_changed(self, contract_symbol):
        """当合约选择变化时，自动更新代码和数据库路径"""
        if contract_symbol:
            # 更新代码(code)字段
            self.code_edit.setText(contract_symbol)
            
            # 更新数据库路径
            db_path = f"{contract_symbol}_futures_data.db"
            self.db_path_edit.setText(db_path)
            
            self.append_log(f'🔄 已切换到合约: {contract_symbol}')
            self.append_log(f'📁 数据库路径: {db_path}')

    def load_default_api_config(self):
        """从binance_config.ini加载默认API配置"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('binance_config.ini', encoding='utf-8')
            
            if 'binance' in config:
                api_key = config['binance'].get('api_key', '')
                api_secret = config['binance'].get('api_secret', '')
                
                if api_key and api_secret:
                    self.api_key_edit.setText(api_key)
                    self.secret_key_edit.setText(api_secret)
                    self.append_log('已加载默认API配置')
        except Exception as e:
            self.append_log(f'加载默认API配置失败: {e}')

    def on_test_api(self):
        """测试API连接"""
        api_key = self.api_key_edit.text().strip()
        secret_key = self.secret_key_edit.text().strip()
        
        if not api_key or not secret_key:
            self.append_log('❌ 请先输入API Key和Secret Key')
            return
        
        self.append_log('🔍 正在测试API连接...')
        self.test_api_btn.setEnabled(False)
        self.test_api_btn.setText('测试中...')
        
        try:
            from auto_trading import BinanceFuturesTrader
            trader = BinanceFuturesTrader(api_key, secret_key, testnet=False)
            
            # 测试获取账户信息
            account_info = trader.get_account_info()
            if account_info:
                total_balance = account_info.get('totalWalletBalance', '0')
                self.append_log(f'✅ API连接成功！')
                self.append_log(f'💰 账户总余额: {total_balance} USDT')
                
                # 测试获取当前价格
                current_price = trader.get_current_price()
                if current_price:
                    self.append_log(f'📈 BTC当前价格: {current_price} USDT')
                
                # 测试获取持仓信息
                positions = trader.get_position_info()
                if positions:
                    self.append_log(f'📊 当前持仓数量: {len(positions)} 个')
                    for pos in positions:
                        symbol = pos.get('symbol', '')
                        amount = pos.get('positionAmt', '0')
                        if symbol == 'BTCUSDT':
                            self.append_log(f'   BTC持仓: {amount}')
                else:
                    self.append_log('📊 当前无持仓')
                
                self.test_api_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
                self.append_log('🎉 API测试完成，密钥有效！')
            else:
                self.append_log('❌ API连接失败，请检查密钥是否正确')
                self.test_api_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
            
        except Exception as e:
            self.append_log(f'❌ API测试失败: {e}')
            self.test_api_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; }")
        finally:
            self.test_api_btn.setEnabled(True)
            self.test_api_btn.setText('测试API连接')

    def on_save_config(self):
        """保存配置到文件"""
        import json
        config = {
            'db_path': self.db_path_edit.text().strip(),
            'code': self.code_edit.text().strip(),
            'table_low': self.table_low_edit.text().strip(),
            'table_high': self.table_high_edit.text().strip(),
            'limit_num': self.limit_spin.value(),
            'interval': self.interval_combo.currentText(),
            'take_profit_factor': self.take_profit_factor_double.value(),
            'take_profit_enabled': self.take_profit_checkbox.isChecked(),
            'no_TakeProfit': 1 if not self.take_profit_checkbox.isChecked() else 0,
            'st_len': self.st_len.value(),
            'st_mul': self.st_mul.value(),
            'st_len_60': self.st_len_60.value(),
            'st_mul_60': self.st_mul_60.value(),
            'trade_mode': self.trade_mode_combo.currentText(),
            'contract_size': self.contract_size_spin.value(),
            'trading_symbol': self.trading_symbol_combo.currentText().strip(),
            'api_key': self.api_key_edit.text().strip(),
            'secret_key': self.secret_key_edit.text().strip(),
            'auto_trade': self.auto_trade_check.isChecked(),
            'backtest': self.backtest_check.isChecked(),
        }
        
        try:
            with open('strategy_config.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            self.append_log('配置已保存到 strategy_config.json')
        except Exception as e:
            self.append_log(f'保存配置失败: {e}')

    def on_load_config(self):
        """从文件加载配置"""
        import json
        
        # 首先加载默认API配置
        self.load_default_api_config()
        
        try:
            with open('strategy_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # 加载配置到界面
            self.db_path_edit.setText(config.get('db_path', ''))
            self.code_edit.setText(config.get('code', 'KQ.m@SHFE.rb'))
            self.table_low_edit.setText(config.get('table_low', 'min_data15'))
            self.table_high_edit.setText(config.get('table_high', 'min_data60'))
            self.limit_spin.setValue(config.get('limit_num', 4000))
            self.interval_combo.setCurrentText(config.get('interval', '5'))
            self.take_profit_factor_double.setValue(config.get('take_profit_factor', 2.0))
            self.take_profit_checkbox.setChecked(config.get('take_profit_enabled', False))
            self.st_len.setValue(config.get('st_len', 10))
            self.st_mul.setValue(config.get('st_mul', 3.0))
            self.st_len_60.setValue(config.get('st_len_60', 10))
            self.st_mul_60.setValue(config.get('st_mul_60', 3.0))
            self.trade_mode_combo.setCurrentText(config.get('trade_mode', 'both'))
            self.contract_size_spin.setValue(config.get('contract_size', 0.001))
            self.trading_symbol_combo.setCurrentText(config.get('trading_symbol', 'BTCUSDT'))
            
            # 如果策略配置中有API密钥，则使用策略配置的，否则使用默认的
            if config.get('api_key'):
                self.api_key_edit.setText(config.get('api_key', ''))
            if config.get('secret_key'):
                self.secret_key_edit.setText(config.get('secret_key', ''))
                
            self.auto_trade_check.setChecked(config.get('auto_trade', False))
            self.backtest_check.setChecked(config.get('backtest', True))
            
            self.append_log('配置已从 strategy_config.json 加载')
        except FileNotFoundError:
            self.append_log('未找到配置文件，使用默认配置')
        except Exception as e:
            self.append_log(f'加载配置失败: {e}')

    def gather_params(self):
        params = dict(
            db_path=self.db_path_edit.text().strip(),
            table_low=self.table_low_edit.text().strip(),
            table_high=self.table_high_edit.text().strip(),
            code=self.code_edit.text().strip(),
            limit_num=int(self.limit_spin.value()),
            take_profit_factor=float(self.take_profit_factor_double.value()),
            no_TakeProfit=1 if not self.take_profit_checkbox.isChecked() else 0,
            supertrend_length=int(self.st_len.value()),
            supertrend_multiplier=float(self.st_mul.value()),
            supertrend_length_60=int(self.st_len_60.value()),
            supertrend_multiplier_60=float(self.st_mul_60.value()),
            trade_mode=self.trade_mode_combo.currentText(),
            do_backtest=bool(self.backtest_check.isChecked()),
            initial_cash=1000000.0,
            stake_qty=1,
        )
        return params

    def run_once(self):
        """启动策略执行线程"""
        try:
            # 如果已有线程在运行，先停止
            if self.strategy_thread and self.strategy_thread.isRunning():
                self.strategy_thread.stop()
                self.strategy_thread.wait()
            
            # 收集参数
            p = self.gather_params()
            
            # 创建并启动策略线程
            self.strategy_thread = StrategyThread(p)
            self.strategy_thread.strategy_finished.connect(self.on_strategy_finished)
            self.strategy_thread.strategy_error.connect(self.on_strategy_error)
            self.strategy_thread.start()
            
            self.append_log("🚀 策略执行已启动（后台运行）...")
            
        except Exception as e:
            self.append_log(f"启动策略失败: {e}")
    
    def on_strategy_finished(self, res):
        """策略执行完成回调"""
        try:
            stats = res.get('stats', {})
            current_position = res.get('current_position', 0)
            
            self.append_log(f"✅ 策略计算完成: long={stats.get('long_signals', 0)}, short={stats.get('short_signals', 0)}, 持仓={current_position}")

            # 如果启用自动交易，执行交易逻辑
            if self.auto_trade_check.isChecked() and self.api_key_edit.text().strip() and self.secret_key_edit.text().strip():
                try:
                    from auto_trading import execute_trading_logic
                    execute_trading_logic(
                        target_position=current_position,
                        contract_size=float(self.contract_size_spin.value()),
                        api_key=self.api_key_edit.text().strip(),
                        secret_key=self.secret_key_edit.text().strip(),
                        symbol=self.trading_symbol_combo.currentText().strip(),
                        stop_ref_price=res.get('stop_ref_price'),
                        latest_close_price=res.get('latest_close_price')
                    )
                    self.append_log(f"✅ 自动交易执行完成，目标持仓: {current_position}，合约: {self.trading_symbol_combo.currentText()}")
                except Exception as e:
                    self.append_log(f"❌ 自动交易执行失败: {e}")

            # 展示HTML图表
            chart_path = res.get('chart_path')
            if self.backtest_check.isChecked() and chart_path and os.path.exists(chart_path):
                file_url = QtCore.QUrl.fromLocalFile(os.path.abspath(chart_path))
                if self.web_view is not None:
                    self.web_view.load(file_url)
                else:
                    self.chart_link.setText(f"<a href='file:///{os.path.abspath(chart_path)}'>打开图表: {os.path.basename(chart_path)}</a>")
                self.append_log(f"📊 图表已更新: {chart_path}")
            else:
                self.append_log("📊 未生成图表或回测未启用")
                
        except Exception as e:
            self.append_log(f"❌ 处理策略结果失败: {e}")
    
    def on_strategy_error(self, error_msg):
        """策略执行错误回调"""
        self.append_log(f"❌ 策略执行失败: {error_msg}")

    def get_trading_symbols(self):
        """获取币安期货可交易合约列表"""
        try:
            url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                symbols = []
                for symbol_info in data['symbols']:
                    if symbol_info['status'] == 'TRADING' and symbol_info['contractType'] == 'PERPETUAL':
                        symbols.append(symbol_info['symbol'])
                return sorted(symbols)
            else:
                self.append_log(f"获取合约列表失败: HTTP {response.status_code}")
                return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # 返回默认合约
        except Exception as e:
            self.append_log(f"获取合约列表异常: {e}")
            return ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']  # 返回默认合约

    def on_refresh_symbols(self):
        """刷新合约列表"""
        self.append_log("正在获取合约列表...")
        symbols = self.get_trading_symbols()
        
        # 保存当前选择的合约
        current_symbol = self.trading_symbol_combo.currentText()
        
        # 清空并重新填充下拉菜单
        self.trading_symbol_combo.clear()
        self.trading_symbol_combo.addItems(symbols)
        
        # 恢复之前的选择，如果不存在则选择第一个
        if current_symbol in symbols:
            self.trading_symbol_combo.setCurrentText(current_symbol)
        else:
            self.trading_symbol_combo.setCurrentIndex(0)
        
        self.append_log(f"已加载 {len(symbols)} 个可交易合约")

    def on_open_data_download(self):
        """打开独立的数据下载管理窗口"""
        try:
            # 导入数据下载管理器
            from data_download_manager import DataDownloadManager
            
            # 创建独立的数据下载管理窗口
            self.data_download_window = DataDownloadManager()
            
            # 显示窗口（独立运行，不依赖主窗口）
            self.data_download_window.show()
            
            self.append_log("已打开数据下载管理窗口")
            
        except ImportError as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "错误", 
                f"无法导入数据下载管理器: {str(e)}\n请确保 data_download_manager.py 文件存在"
            )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "错误", 
                f"打开数据下载窗口失败: {str(e)}"
            )
    
    def on_open_console(self):
        """打开控制台输出窗口"""
        try:
            # 创建控制台窗口
            self.console_window = ConsoleWindow()
            
            # 显示窗口（独立运行，不依赖主窗口）
            self.console_window.show()
            
            self.append_log("已打开控制台输出窗口")
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, 
                "错误", 
                f"打开控制台窗口失败: {str(e)}"
            )


class ConsoleWindow(QtWidgets.QWidget):
    """控制台输出窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle('控制台输出')
        self.setGeometry(100, 100, 800, 600)
        
        # 创建布局
        layout = QtWidgets.QVBoxLayout()
        
        # 控制按钮
        button_layout = QtWidgets.QHBoxLayout()
        self.clear_btn = QtWidgets.QPushButton('清空')
        self.clear_btn.clicked.connect(self.clear_console)
        self.save_btn = QtWidgets.QPushButton('保存日志')
        self.save_btn.clicked.connect(self.save_log)
        
        button_layout.addWidget(self.clear_btn)
        button_layout.addWidget(self.save_btn)
        button_layout.addStretch()
        
        # 控制台文本区域
        self.console_text = QtWidgets.QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setFont(QtGui.QFont('Consolas', 9))
        self.console_text.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #333333;
            }
        """)
        
        layout.addLayout(button_layout)
        layout.addWidget(self.console_text)
        
        self.setLayout(layout)
        
        # 重定向标准输出
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = self
        sys.stderr = self
        
    def write(self, text):
        """重写write方法，将输出重定向到控制台"""
        if text.strip():  # 只显示非空内容
            self.console_text.append(text.strip())
            # 自动滚动到底部
            scrollbar = self.console_text.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
    
    def flush(self):
        """重写flush方法"""
        pass
    
    def clear_console(self):
        """清空控制台"""
        self.console_text.clear()
    
    def save_log(self):
        """保存日志到文件"""
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, '保存日志', 'console_log.txt', 'Text Files (*.txt)'
        )
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(self.console_text.toPlainText())
                QtWidgets.QMessageBox.information(self, '成功', f'日志已保存到: {filename}')
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, '错误', f'保存失败: {e}')
    
    def closeEvent(self, event):
        """窗口关闭时恢复标准输出"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        event.accept()


def main():
    # 远程授权验证
    if not check_remote_authorization():
        print("授权验证失败，程序退出")
        QtWidgets.QMessageBox.critical(None, '验证程序完整性失败', '程序将退出。')
        sys.exit(1)

    app = QtWidgets.QApplication(sys.argv)
    w = StrategyGUI()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()