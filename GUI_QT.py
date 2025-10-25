#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tradestation策略GUI界面 - 复刻版
基于参考项目的GUI_QT.py，适配Tradestation API和期货品种
"""

import sys
import os
from PyQt5 import QtWidgets, QtCore, QtGui
import sqlite3
try:
    from PyQt5.QtWebEngineWidgets import QWebEngineView
except Exception:
    QWebEngineView = None
    print("警告: PyQt5.QtWebEngineWidgets 导入失败，图表预览将使用外部浏览器")

# 引入策略对外函数（暂时注释，等策略模块完成后再启用）
# from strategy_part2 import run_strategy_once
import requests
import json


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
            
            # 暂时模拟策略执行结果，等策略模块完成后再启用真实策略
            # res = run_strategy_once(**self.params)
            
            # 模拟策略执行结果
            res = {
                'stats': {
                    'long_signals': 1,
                    'short_signals': 0
                },
                'current_position': 1,
                'stop_ref_price': 5000.0,
                'latest_close_price': 5050.0,
                'chart_path': None  # 暂时没有图表
            }
            
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
        self.setWindowTitle('Tradestation 量化- 参数面板')
        self.resize(720, 520)

        # 控件
        self.db_path_edit = QtWidgets.QLineEdit('ES_futures_data.db')  # 默认数据库路径
        self.db_browse_btn = QtWidgets.QPushButton('选择数据库...')
        self.code_edit = QtWidgets.QLineEdit('ES')  # 默认与合约选择一致
        self.table_low_edit = QtWidgets.QLineEdit('min15_data')
        self.table_high_edit = QtWidgets.QLineEdit('min60_data')

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
        self.trading_symbol_combo.addItems(['ES', 'NQZ25'])  # Tradestation期货品种
        self.trading_symbol_combo.setCurrentText('ES')
        
        # 连接合约选择变化事件
        self.trading_symbol_combo.currentTextChanged.connect(self.on_contract_changed)
        
        # 添加刷新合约列表按钮
        self.refresh_symbols_btn = QtWidgets.QPushButton('刷新合约列表')
        self.refresh_symbols_btn.setStyleSheet("QPushButton { background-color: #2196F3; color: white; }")

        # 添加Tradestation API配置
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
        
        # 添加聚合数据并绘图按钮
        self.aggregate_btn = QtWidgets.QPushButton('聚合数据并绘图')
        self.aggregate_btn.setStyleSheet("QPushButton { background-color: #FF5722; color: white; font-weight: bold; }")

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
        
        # 创建需要隐藏的行，但不添加到表单中
        self.table_high_row = ('大周期表:', self.table_high_edit)
        self.limit_row = ('加载数据量(小周期):', self.limit_spin)
        self.take_profit_row = ('盈亏比(take_profit_factor):', self.take_profit_factor_double)
        self.st_60_row = ('大周期 ST length / multiplier:', self._hbox(self.st_len_60, self.st_mul_60))
        
        form.addRow('运算间隔(分钟):', self.interval_combo)
        # 隐藏"按盈亏比平仓"复选框
        # form.addRow('', self.take_profit_checkbox)
        form.addRow('小周期 ST length / multiplier:', self._hbox(self.st_len, self.st_mul))
        form.addRow('交易模式:', self.trade_mode_combo)
        form.addRow('合约数量(1份=):', self.contract_size_spin)
        form.addRow('交易合约选择:', self._hbox(self.trading_symbol_combo, self.refresh_symbols_btn))
        form.addRow('Tradestation API Key:', self.api_key_edit)
        form.addRow('Tradestation Secret Key:', self.secret_key_edit)
        form.addRow('API连接测试:', self.test_api_btn)
        form.addRow(self.auto_trade_check)
        form.addRow(self.backtest_check)
        form.addRow(self.aggregate_btn)
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
        self.aggregate_btn.clicked.connect(self.on_aggregate_data)
        
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
            db_path = f"{contract_symbol.lower()}_futures_data.db"
            self.db_path_edit.setText(db_path)
            
            self.append_log(f'🔄 已切换到合约: {contract_symbol}')
            self.append_log(f'📁 数据库路径: {db_path}')

    def load_default_api_config(self):
        """从tradestation_config.ini加载默认API配置"""
        try:
            import configparser
            config = configparser.ConfigParser()
            config.read('tradestation_config.ini', encoding='utf-8')
            
            if 'tradestation' in config:
                api_key = config['tradestation'].get('api_key', '')
                api_secret = config['tradestation'].get('api_secret', '')
                
                if api_key and api_secret:
                    self.api_key_edit.setText(api_key)
                    self.secret_key_edit.setText(api_secret)
                    self.append_log('已加载默认API配置')
        except Exception as e:
            self.append_log(f'加载默认API配置失败: {e}')

    def on_test_api(self):
        """测试Tradestation API连接"""
        api_key = self.api_key_edit.text().strip()
        secret_key = self.secret_key_edit.text().strip()
        
        if not api_key or not secret_key:
            self.append_log('❌ 请先输入API Key和Secret Key')
            return
        
        self.append_log('🔍 正在测试Tradestation API连接...')
        self.test_api_btn.setEnabled(False)
        self.test_api_btn.setText('测试中...')
        
        try:
            # 导入Tradestation API客户端
            from app.services.tradestation_client import TradestationAPIClient
            
            # 测试API连接
            client = TradestationAPIClient()
            
            # 检查令牌是否有效
            if client.is_token_valid():
                self.append_log('✅ Tradestation API连接成功！')
                self.append_log('🎉 访问令牌有效，可以正常使用API')
                
                # 测试获取账户信息
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        account_info = loop.run_until_complete(client.get_accounts())
                        if account_info:
                            self.append_log(f'💰 账户信息获取成功')
                            for account in account_info:
                                account_id = account.get('Key', 'Unknown')
                                account_type = account.get('Type', 'Unknown')
                                self.append_log(f'   账户ID: {account_id}, 类型: {account_type}')
                    finally:
                        loop.close()
                except Exception as e:
                    self.append_log(f'⚠️ 获取账户信息失败: {e}')
                
                self.test_api_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; }")
                self.append_log('🎉 API测试完成，密钥有效！')
            else:
                self.append_log('❌ 访问令牌已过期，需要重新认证')
                self.append_log('💡 请运行 auth_helper_persistent.py 进行认证')
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
            self.code_edit.setText(config.get('code', 'ES'))
            self.table_low_edit.setText(config.get('table_low', 'min15_data'))
            self.table_high_edit.setText(config.get('table_high', 'min60_data'))
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
            self.trading_symbol_combo.setCurrentText(config.get('trading_symbol', 'ES'))
            
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
                    # 暂时注释，等交易模块完成后再启用
                    # from auto_trading import execute_trading_logic
                    # execute_trading_logic(...)
                    self.append_log(f"✅ 自动交易功能待实现，目标持仓: {current_position}，合约: {self.trading_symbol_combo.currentText()}")
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
        """获取Tradestation期货可交易合约列表"""
        try:
            # Tradestation期货品种列表
            symbols = ['ES', 'NQZ25', 'YM', 'RTY', 'NQ', 'EMD', 'GC', 'SI', 'CL', 'NG', 'ZB', 'ZN', 'ZF', 'ZT']
            return sorted(symbols)
        except Exception as e:
            self.append_log(f"获取合约列表异常: {e}")
            return ['ES', 'NQZ25']  # 返回默认合约

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
    
    def on_aggregate_data(self):
        """聚合数据并绘图"""
        try:
            symbol = self.trading_symbol_combo.currentText().strip()
            db_path = self.db_path_edit.text().strip()
            
            if not symbol or not db_path:
                self.append_log("❌ 请先选择交易合约和数据库路径")
                return
            
            if not os.path.exists(db_path):
                self.append_log(f"❌ 数据库文件不存在: {db_path}")
                return
            
            self.append_log(f"🚀 开始聚合 {symbol} 数据并绘图...")
            self.aggregate_btn.setEnabled(False)
            self.aggregate_btn.setText("处理中...")
            
            # 从数据库获取数据
            data = self.get_kline_data_from_db(db_path, symbol)
            
            if not data:
                self.append_log("❌ 未获取到K线数据")
                return
            
            # 生成图表
            chart_path = self.create_kline_chart(data, symbol)
            
            if chart_path and os.path.exists(chart_path):
                # 在图表区域显示
                file_url = QtCore.QUrl.fromLocalFile(os.path.abspath(chart_path))
                if self.web_view is not None:
                    self.web_view.load(file_url)
                else:
                    self.chart_link.setText(f"<a href='file:///{os.path.abspath(chart_path)}'>打开图表: {os.path.basename(chart_path)}</a>")
                
                self.append_log(f"✅ 图表生成成功: {chart_path}")
            else:
                self.append_log("❌ 图表生成失败")
                
        except Exception as e:
            self.append_log(f"❌ 聚合数据失败: {e}")
        finally:
            self.aggregate_btn.setEnabled(True)
            self.aggregate_btn.setText("聚合数据并绘图")
    
    def get_kline_data_from_db(self, db_path, symbol):
        """从数据库获取K线数据"""
        try:
            import sqlite3
            import pandas as pd
            
            conn = sqlite3.connect(db_path)
            
            # 获取所有表名
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            if not tables:
                self.append_log("❌ 数据库中没有任何表")
                return None
            
            # 选择第一个表（通常是min1_data）
            table_name = tables[0][0]
            self.append_log(f"📊 从表 {table_name} 获取数据")
            
            # 查询数据
            query = f"SELECT * FROM {table_name} ORDER BY time DESC LIMIT 1000"
            df = pd.read_sql_query(query, conn)
            
            conn.close()
            
            if df.empty:
                self.append_log("❌ 表中没有数据")
                return None
            
            # 转换数据格式并计算移动平均线
            data = []
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            for _, row in df.iterrows():
                data.append({
                    'datetime': row['time'],  # 直接使用time字段
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['vol']),  # 使用vol字段
                    'ma20': float(row['ma20']) if not pd.isna(row['ma20']) else 0,
                    'ma60': float(row['ma60']) if not pd.isna(row['ma60']) else 0
                })
            
            self.append_log(f"✅ 获取到 {len(data)} 条K线数据")
            return data
            
        except Exception as e:
            self.append_log(f"❌ 获取数据库数据失败: {e}")
            return None
    
    def create_kline_chart(self, data, symbol):
        """使用huatu_bb.py创建K线图表"""
        try:
            # 导入您的绘图脚本
            import sys
            import os
            import pandas as pd
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            from huatu_bb import huatucs
            
            # 将数据转换为DataFrame
            df = pd.DataFrame(data)
            
            # 添加date列（huatucs函数需要）
            df['date'] = pd.to_datetime(df['datetime'])
            
            # 添加一些空列（huatucs函数可能需要但我们现在不需要的）
            df['买60'] = 0
            df['卖60'] = 0
            
            # 确保ma20和ma60列存在且为数值类型

            
            # 调用huatucs函数（其内部写文件但不返回路径）
            huatucs(df.to_dict('records'), symbol, "1分钟", "ma")
            
            # 根据huatu_bb的命名规则构造文件名：kdj_chart_{code}{zhibiaomc}.html
            chart_path = f"kdj_chart_{symbol}ma.html"
            
            self.append_log(f"使用huatu_bb生成图表: {chart_path}")
            return chart_path
            
        except Exception as e:
            self.append_log(f"❌ 创建图表失败: {e}")
            import traceback
            traceback.print_exc()
            return None


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
    app = QtWidgets.QApplication(sys.argv)
    w = StrategyGUI()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
