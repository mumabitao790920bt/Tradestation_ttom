import os
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

from 回测示例 import run_backtest
from 下载股票历史数据.downloader_bridge import download_daily_to_sqlite
from 下载股票历史数据.bitcoin_downloader import download_bitcoin_data


class Worker(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    done = QtCore.pyqtSignal()
    chart_ready = QtCore.pyqtSignal(str)

    def run_download(self, code: str, data_source: str):
        try:
            if data_source == '数字货币':
                self.log.emit(f'开始下载 {code} 历史数据...')
                if code == 'BTC':
                    from 下载股票历史数据.crypto_downloader import download_and_save_crypto_data
                    db_path = download_and_save_crypto_data("BTC-USD", "btc_data.db", "btc_daily")
                elif code == 'ETH':
                    from 下载股票历史数据.crypto_downloader import download_and_save_crypto_data
                    db_path = download_and_save_crypto_data("ETH-USD", "eth_data.db", "eth_daily")
                else:
                    self.log.emit(f'不支持的加密货币代码: {code}')
                    return
                self.log.emit(f'下载完成: {db_path}')
            elif data_source == '指定期货':
                self.log.emit(f'指定期货 {code} 数据来自远程数据库')
            elif data_source == '国内期货':
                self.log.emit(f'国内期货 {code} 数据下载功能待开发')
            else:
                self.log.emit(f'开始下载 {code} 历史数据...')
                db_path = download_daily_to_sqlite(code, code)
                self.log.emit(f'下载完成: {db_path}')
        except Exception as e:
            self.log.emit(f'下载失败: {e}')
        finally:
            self.done.emit()

    def run_aggregate(self, params: dict):
        """运行数据聚合和绘图"""
        try:
            self.log.emit('开始数据聚合和绘图...')
            
            # 获取参数
            code = params['code']
            data_source = params['data_source']
            period = params['period']
            limit_num = params['limit_num']
            
            # 根据数据源获取数据
            if data_source == '指定期货':
                # 从远程数据库获取恒指期货数据
                data = self.get_futures_data_from_remote(limit_num)
            elif data_source == '国内期货':
                self.log.emit('国内期货数据聚合功能待开发')
                return
            elif data_source == '数字货币':
                # 从本地数据库获取数字货币数据
                data = self.get_crypto_data_from_local(code, limit_num)
            else:
                self.log.emit(f'不支持的数据源: {data_source}')
                return
            
            if not data:
                self.log.emit('未获取到数据')
                return
            
            # 数据聚合
            period_minutes = int(period.replace('分钟', ''))
            aggregated_data = self.aggregate_kline_data(data, period_minutes)
            
            if not aggregated_data:
                self.log.emit('数据聚合失败')
                return
            
            # 计算均线
            aggregated_data = self.calculate_moving_averages(aggregated_data)
            
            # 生成图表 - 使用huatu_bb绘图
            chart_path = self.create_chart_with_huatu(aggregated_data, code, period)
            
            if chart_path and os.path.exists(chart_path):
                self.log.emit(f'图表生成成功: {chart_path}')
                self.chart_ready.emit(os.path.abspath(chart_path))
            else:
                self.log.emit('图表生成失败')
                
        except Exception as e:
            self.log.emit(f'聚合失败: {e}')
            import traceback
            traceback.print_exc()
        finally:
            self.done.emit()

    def get_futures_data_from_remote(self, limit_num):
        """从远程数据库获取期货数据"""
        try:
            import pymysql
            
            # 远程数据库配置（参考简化实时数据系统）
            mysql_config = {
                'host': '115.159.44.226',
                'port': 3306,
                'user': 'qihuo',
                'password': 'Hejdf3KdfaTt4h3w',
                'database': 'qihuo',
                'charset': 'utf8mb4',
                'autocommit': True
            }
            
            conn = pymysql.connect(**mysql_config)
            cursor = conn.cursor()
            
            sql = """
            SELECT datetime, open, high, low, close, volume
            FROM hf_HSI_min1 
            ORDER BY datetime DESC 
            LIMIT %s
            """
            
            cursor.execute(sql, (limit_num,))
            results = cursor.fetchall()
            conn.close()
            
            # 转换为DataFrame格式
            import pandas as pd
            data = []
            for row in results:
                data.append({
                    'datetime': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': float(row[5])
                })
            
            self.log.emit(f'从远程数据库获取到 {len(data)} 条数据')
            return data
            
        except Exception as e:
            self.log.emit(f'从远程数据库获取数据失败: {e}')
            return None

    def get_crypto_data_from_local(self, code, limit_num):
        """从本地数据库获取数字货币数据"""
        try:
            import sqlite3
            import pandas as pd
            
            if code == 'BTC':
                db_path = 'btc_data.db'
                table_name = 'btc_daily'
            elif code == 'ETH':
                db_path = 'eth_data.db'
                table_name = 'eth_daily'
            else:
                self.log.emit(f'不支持的加密货币: {code}')
                return None
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            sql = f"""
            SELECT datetime, open, high, low, close, volume
            FROM {table_name}
            ORDER BY datetime DESC
            LIMIT ?
            """
            
            cursor.execute(sql, (limit_num,))
            results = cursor.fetchall()
            conn.close()
            
            data = []
            for row in results:
                data.append({
                    'datetime': row[0],
                    'open': float(row[1]),
                    'high': float(row[2]),
                    'low': float(row[3]),
                    'close': float(row[4]),
                    'volume': float(row[5])
                })
            
            self.log.emit(f'从本地数据库获取到 {len(data)} 条数据')
            return data
            
        except Exception as e:
            self.log.emit(f'从本地数据库获取数据失败: {e}')
            return None

    def aggregate_kline_data(self, data, period_minutes):
        """将1分钟数据聚合为指定周期的K线数据"""
        try:
            import pandas as pd
            from datetime import datetime, timedelta
            
            if not data:
                return None
            
            # 转换为DataFrame
            df = pd.DataFrame(data)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime')
            
            # 设置时间索引
            df.set_index('datetime', inplace=True)
            
            # 按指定周期重新采样
            resampled = df.resample(f'{period_minutes}T').agg({
                'open': 'first',
                'high': 'max',
                'low': 'min',
                'close': 'last',
                'volume': 'sum'
            }).dropna()
            
            # 转换回列表格式
            aggregated_data = []
            for idx, row in resampled.iterrows():
                aggregated_data.append({
                    'datetime': idx.strftime('%Y-%m-%d %H:%M:%S'),
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume'])
                })
            
            self.log.emit(f'数据聚合完成: {len(aggregated_data)} 条 {period_minutes}分钟K线')
            return aggregated_data
            
        except Exception as e:
            self.log.emit(f'数据聚合失败: {e}')
            return None

    def calculate_moving_averages(self, data):
        """计算M20和M60均线（按照huatu_mz.py的要求）"""
        try:
            import pandas as pd
            
            df = pd.DataFrame(data)
            df['close'] = pd.to_numeric(df['close'])
            
            # 计算M20和M60均线（按照huatu_mz.py的要求）
            df['ma20'] = df['close'].rolling(window=20).mean()
            df['ma60'] = df['close'].rolling(window=60).mean()
            
            # 转换回列表格式
            result = []
            for _, row in df.iterrows():
                result.append({
                    'datetime': row['datetime'],
                    'open': float(row['open']),
                    'high': float(row['high']),
                    'low': float(row['low']),
                    'close': float(row['close']),
                    'volume': float(row['volume']),
                    'ma20': float(row['ma20']) if pd.notna(row['ma20']) else None,
                    'ma60': float(row['ma60']) if pd.notna(row['ma60']) else None
                })
            
            self.log.emit('均线计算完成（M20和M60）')
            return result
            
        except Exception as e:
            self.log.emit(f'均线计算失败: {e}')
            return data  # 返回原始数据

    def create_chart_with_huatu(self, data, code, period):
        """使用huatu_bb.py的方法创建图表"""
        try:
            import pandas as pd
            from huatu_bb import huatucs
            
            # 将数据转换为huatucs函数需要的格式
            df = pd.DataFrame(data)
            
            # 添加date列（huatucs函数需要）
            df['date'] = pd.to_datetime(df['datetime'])
            
            # 添加一些空列（huatucs函数可能需要但我们现在不需要的）
            df['买60'] = 0
            df['卖60'] = 0
            
            # 确保ma20和ma60列存在且为数值类型
            df['ma20'] = pd.to_numeric(df['ma20'], errors='coerce')
            df['ma60'] = pd.to_numeric(df['ma60'], errors='coerce')
            
            # 调用huatucs函数（其内部写文件但不返回路径）
            huatucs(df.to_dict('records'), code, period, "ma")
            
            # 根据huatu_bb的命名规则构造文件名：kdj_chart_{code}{zhibiaomc}.html
            chart_path = f"kdj_chart_{code}ma.html"
            
            self.log.emit(f"使用huatu_bb生成图表: {chart_path}")
            return chart_path
            
        except Exception as e:
            self.log.emit(f"使用huatu_bb生成图表失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def run_strategy(self, params: dict):
        """运行策略计算并生成策略图表"""
        try:
            self.log.emit('开始策略运行...')
            
            # 导入二阶段策略部分
            from 二阶段策略部分 import run_backtest
            
            # 构建策略参数
            strategy_params = {
                'code': params['code'],
                'table_name': params['table_name'],
                'limit_num': params['limit_num'],
                'initial_cash': params['initial_cash'],
                'ma_short': params['ma_short'],
                'ma_long': params['ma_long'],
                'db_mode': params['db_mode'],
                'db_folder': params.get('db_folder'),
                'stake_qty': params['stake_qty'],
                'trade_mode': params['trade_mode'],
                'jx1': params['jx1'],
                'jx2': params['jx2'],
                'jx3': params['jx3'],
                'jx4': params['jx4'],
                'jx5': params['jx5'],
                '粘合阈值': params['粘合阈值'],
                'ma4附近阈值': params['ma4附近阈值']
            }
            
            # 执行策略计算
            result = run_backtest(**strategy_params)
            
            self.log.emit(
                f"策略运行完成 期末资产: {result['final_value']:.2f}  盈亏: {result['profit']:.2f}  胜率: {result['win_rate']}%  盈亏比: {result['profit_loss_ratio']}"
            )
            
            # 获取策略图表路径
            chart = result.get('chart_path')
            if chart and os.path.exists(chart):
                self.log.emit(f'策略图表生成成功: {chart}')
                self.chart_ready.emit(os.path.abspath(chart))
            else:
                self.log.emit('策略图表生成失败')
                
        except Exception as e:
            self.log.emit(f'策略运行失败: {e}')
            import traceback
            traceback.print_exc()
        finally:
            self.done.emit()

    def run_backtest(self, params: dict):
        try:
            self.log.emit('开始回测...')
            result = run_backtest(**params)
            self.log.emit(
                f"回测完成 期末资产: {result['final_value']:.2f}  盈亏: {result['profit']:.2f}  胜率: {result['win_rate']}%  盈亏比: {result['profit_loss_ratio']}"
            )
            chart = result.get('chart_path')
            if chart and os.path.exists(chart):
                self.log.emit(f'图表: {chart}')
                self.chart_ready.emit(os.path.abspath(chart))
            else:
                self.log.emit('未找到图表文件')
        except Exception as e:
            self.log.emit(f'回测失败: {e}')
        finally:
            self.done.emit()


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('双均线回测系统 - 参数配置与可视化 (PyQt)')
        self.resize(1200, 820)
        self._build_ui()

    def _build_ui(self):
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        vbox = QtWidgets.QVBoxLayout(cw)

        self.form_layout = QtWidgets.QGridLayout()
        vbox.addLayout(self.form_layout)

        # 数据源选择（放在最前面）
        self.data_source = QtWidgets.QComboBox()
        self.data_source.addItems(['指定期货', '国内期货', '数字货币'])
        self.data_source.currentTextChanged.connect(self.on_data_source_changed)
        
        # 添加数据源说明标签
        self.data_source_label = QtWidgets.QLabel('数据源说明：指定期货=恒指期货等, 国内期货=国内期货品种, 数字货币=BTC/ETH等')
        self.data_source_label.setStyleSheet("color: blue; font-size: 10px;")
        
        # 使用QStackedWidget来管理代码/币种输入控件
        self.code_stack = QtWidgets.QStackedWidget()
        
        # 指定期货选择下拉框
        self.futures_combo = QtWidgets.QComboBox()
        self.futures_combo.addItems(['恒指期货'])
        self.futures_combo.currentTextChanged.connect(self.on_futures_code_changed)
        
        # 国内期货选择下拉框
        self.domestic_futures_combo = QtWidgets.QComboBox()
        self.domestic_futures_combo.addItems(['沪深300', '中证500', '上证50'])  # 可后续扩展
        self.domestic_futures_combo.currentTextChanged.connect(self.on_domestic_futures_code_changed)
        
        # 加密货币选择下拉框
        self.crypto_combo = QtWidgets.QComboBox()
        self.crypto_combo.addItems(['BTC', 'ETH'])
        
        # 将三个控件添加到堆叠控件中
        self.code_stack.addWidget(self.futures_combo)  # 索引0：指定期货下拉框
        self.code_stack.addWidget(self.domestic_futures_combo)  # 索引1：国内期货下拉框
        self.code_stack.addWidget(self.crypto_combo)  # 索引2：加密货币下拉框
        
        # 交易周期选择
        self.trading_period = QtWidgets.QComboBox()
        self.trading_period.addItems(['1分钟', '3分钟', '5分钟', '10分钟', '15分钟', '30分钟'])
        self.trading_period.currentTextChanged.connect(self.on_period_changed)
        
        # K线数量（保留用于数据查询）
        self.limit_num = QtWidgets.QSpinBox()
        self.limit_num.setRange(100, 200000)
        self.limit_num.setValue(4000)
        
        # 策略方向选择
        self.trade_mode_combo = QtWidgets.QComboBox()
        self.trade_mode_combo.addItems(['多空双向', '只做多', '只做空'])
        self.trade_mode_combo.setCurrentText('多空双向')

        # 策略参数输入框
        self.粘合阈值_input = QtWidgets.QLineEdit("0.0015")
        self.ma4附近阈值_input = QtWidgets.QLineEdit("0.002")
        
        # 均线参数输入框
        self.jx1_input = QtWidgets.QSpinBox()
        self.jx1_input.setRange(1, 200)
        self.jx1_input.setValue(5)
        
        self.jx2_input = QtWidgets.QSpinBox()
        self.jx2_input.setRange(1, 200)
        self.jx2_input.setValue(10)
        
        self.jx3_input = QtWidgets.QSpinBox()
        self.jx3_input.setRange(1, 200)
        self.jx3_input.setValue(20)
        
        self.jx4_input = QtWidgets.QSpinBox()
        self.jx4_input.setRange(1, 200)
        self.jx4_input.setValue(30)
        
        self.jx5_input = QtWidgets.QSpinBox()
        self.jx5_input.setRange(1, 200)
        self.jx5_input.setValue(60)

        r = 0
        self.form_layout.addWidget(QtWidgets.QLabel('数据源'), r, 0)
        self.form_layout.addWidget(self.data_source, r, 1)
        self.form_layout.addWidget(self.data_source_label, r, 2, 1, 4)  # 跨4列显示说明
        r += 1
        self.form_layout.addWidget(QtWidgets.QLabel('品种选择'), r, 0)
        self.form_layout.addWidget(self.code_stack, r, 1)  # 使用堆叠控件
        self.form_layout.addWidget(QtWidgets.QLabel('交易周期'), r, 2)
        self.form_layout.addWidget(self.trading_period, r, 3)
        r += 1
        # 参数分组框
        self.param_group = QtWidgets.QGroupBox('策略参数')
        param_layout = QtWidgets.QGridLayout(self.param_group)
        pr = 0
        param_layout.addWidget(QtWidgets.QLabel('策略方向'), pr, 0)
        param_layout.addWidget(self.trade_mode_combo, pr, 1)
        param_layout.addWidget(QtWidgets.QLabel('K线数量'), pr, 2)
        param_layout.addWidget(self.limit_num, pr, 3)
        pr += 1
        param_layout.addWidget(QtWidgets.QLabel('粘合阈值'), pr, 0)
        param_layout.addWidget(self.粘合阈值_input, pr, 1)
        param_layout.addWidget(QtWidgets.QLabel('ma4附近阈值'), pr, 2)
        param_layout.addWidget(self.ma4附近阈值_input, pr, 3)
        pr += 1
        param_layout.addWidget(QtWidgets.QLabel('jx1'), pr, 0)
        param_layout.addWidget(self.jx1_input, pr, 1)
        param_layout.addWidget(QtWidgets.QLabel('jx2'), pr, 2)
        param_layout.addWidget(self.jx2_input, pr, 3)
        pr += 1
        param_layout.addWidget(QtWidgets.QLabel('jx3'), pr, 0)
        param_layout.addWidget(self.jx3_input, pr, 1)
        param_layout.addWidget(QtWidgets.QLabel('jx4'), pr, 2)
        param_layout.addWidget(self.jx4_input, pr, 3)
        pr += 1
        param_layout.addWidget(QtWidgets.QLabel('jx5'), pr, 0)
        param_layout.addWidget(self.jx5_input, pr, 1)

        self.form_layout.addWidget(self.param_group, r, 0, 1, 4)
        r += 1

        btn_bar = QtWidgets.QHBoxLayout()
        vbox.addLayout(btn_bar)
        self.btn_dl = QtWidgets.QPushButton('下载数据')
        self.btn_aggregate = QtWidgets.QPushButton('聚合数据并绘图')
        self.btn_bt = QtWidgets.QPushButton('策略运行')
        self.btn_start_strategy = QtWidgets.QPushButton('启动策略自动运行')
        self.btn_stop_strategy = QtWidgets.QPushButton('停止策略自动运行')
        btn_bar.addWidget(self.btn_dl)
        btn_bar.addWidget(self.btn_aggregate)
        btn_bar.addWidget(self.btn_bt)
        btn_bar.addWidget(self.btn_start_strategy)
        btn_bar.addWidget(self.btn_stop_strategy)
        btn_bar.addStretch(1)

        # 隐藏下载数据按钮（暂不提供该入口）
        self.btn_dl.setVisible(False)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        vbox.addWidget(self.log)

        self.web = QWebEngineView()
        vbox.addWidget(self.web, 1)

        self.btn_dl.clicked.connect(self.handle_download)
        self.btn_aggregate.clicked.connect(self.handle_aggregate)
        self.btn_bt.clicked.connect(self.handle_backtest)
        self.btn_start_strategy.clicked.connect(self.start_strategy_auto_run)
        self.btn_stop_strategy.clicked.connect(self.stop_strategy_auto_run)
        
        # 初始化时设置指定期货模式
        self.on_data_source_changed('指定期货')

        # 初始化自动聚合定时器（每分钟触发一次）
        self.is_busy = False
        self.auto_timer = QtCore.QTimer(self)
        self.auto_timer.setInterval(60 * 1000)
        self.auto_timer.timeout.connect(self.auto_aggregate)
        self.auto_timer.start()
        
        # 初始化策略运行定时器（每分钟触发一次）
        self.strategy_running = False
        self.strategy_timer = QtCore.QTimer(self)
        self.strategy_timer.setInterval(60 * 1000)
        self.strategy_timer.timeout.connect(self.auto_strategy_run)
        # 策略定时器默认不启动，需要用户手动启动

    def on_data_source_changed(self, source: str):
        """数据源改变时的处理"""
        if source == '指定期货':
            # 指定期货模式：显示恒指期货下拉框
            self.code_stack.setCurrentIndex(0)  # 显示指定期货下拉框
            self.futures_combo.setCurrentText('恒指期货')
            
        elif source == '国内期货':
            # 国内期货模式：显示国内期货下拉框
            self.code_stack.setCurrentIndex(1)  # 显示国内期货下拉框
            self.domestic_futures_combo.setCurrentText('沪深300')
            
        elif source == '数字货币':
            # 数字货币模式：显示加密货币下拉框
            self.code_stack.setCurrentIndex(2)  # 显示加密货币下拉框
            self.crypto_combo.setCurrentText('BTC')
    
    def on_futures_code_changed(self, code: str):
        """指定期货代码改变时的处理"""
        pass  # 恒指期货暂时只有一个选项
    
    def on_domestic_futures_code_changed(self, code: str):
        """国内期货代码改变时的处理"""
        pass  # 后续可扩展
    
    def on_period_changed(self, period: str):
        """交易周期改变时的处理"""
        pass  # 周期变化处理

    def _start_thread(self, fn, *args):
        self.btn_dl.setEnabled(False)
        self.btn_aggregate.setEnabled(False)
        self.btn_bt.setEnabled(False)
        self.btn_start_strategy.setEnabled(False)
        self.btn_stop_strategy.setEnabled(False)
        self.is_busy = True
        th = QtCore.QThread(self)
        wk = Worker()
        wk.moveToThread(th)
        wk.log.connect(self.append_log)
        wk.done.connect(th.quit)
        wk.done.connect(lambda: self.btn_dl.setEnabled(True))
        wk.done.connect(lambda: self.btn_aggregate.setEnabled(True))
        wk.done.connect(lambda: self.btn_bt.setEnabled(True))
        wk.done.connect(lambda: self.btn_start_strategy.setEnabled(True))
        wk.done.connect(lambda: self.btn_stop_strategy.setEnabled(True))
        wk.done.connect(lambda: setattr(self, 'is_busy', False))
        wk.chart_ready.connect(self.load_chart)
        th.started.connect(lambda: fn(wk, *args))
        th.finished.connect(wk.deleteLater)
        th.start()

    def handle_download(self):
        data_source = self.data_source.currentText()
        
        # 根据数据源获取代码
        if data_source == '指定期货':
            code = self.futures_combo.currentText()
        elif data_source == '国内期货':
            code = self.domestic_futures_combo.currentText()
        elif data_source == '数字货币':
            code = self.crypto_combo.currentText()
        else:
            self.append_log('请选择数据源')
            return
        
        self._start_thread(lambda w: w.run_download(code, data_source))

    def handle_aggregate(self):
        """处理数据聚合和绘图"""
        data_source = self.data_source.currentText()
        period = self.trading_period.currentText()
        
        # 如果策略自动运行中，禁止手动聚合
        if getattr(self, 'strategy_running', False):
            self.append_log('策略自动运行中，已暂停“聚合数据并绘图”。')
            return
        
        # 根据数据源获取代码
        if data_source == '指定期货':
            code = self.futures_combo.currentText()
        elif data_source == '国内期货':
            code = self.domestic_futures_combo.currentText()
        elif data_source == '数字货币':
            code = self.crypto_combo.currentText()
        else:
            self.append_log('请选择数据源')
            return
        
        params = {
            'code': code,
            'data_source': data_source,
            'period': period,
            'limit_num': int(self.limit_num.value())
        }
        
        self._start_thread(lambda w: w.run_aggregate(params))

    def handle_backtest(self):
        """处理策略运行功能"""
        data_source = self.data_source.currentText()
        period = self.trading_period.currentText()
        
        # 根据数据源获取代码
        if data_source == '指定期货':
            code = self.futures_combo.currentText()
            table_name = "min_data5"  # 根据交易周期动态设置
            db_mode = 'remote'  # 使用远程数据库
        elif data_source == '国内期货':
            code = self.domestic_futures_combo.currentText()
            table_name = "min_data5"
            db_mode = 'baostock'  # 使用本地baostock数据库
        elif data_source == '数字货币':
            code = self.crypto_combo.currentText()
            table_name = f"{code.lower()}_daily"
            db_mode = 'crypto'  # 使用本地crypto数据库
        else:
            self.append_log('请选择数据源')
            return
        
        # 根据交易周期设置table_name
        period_minutes = int(period.replace('分钟', ''))
        if period_minutes == 1:
            table_name = "min_data1"
        elif period_minutes == 3:
            table_name = "min_data3"
        elif period_minutes == 5:
            table_name = "min_data5"
        elif period_minutes == 10:
            table_name = "min_data10"
        elif period_minutes == 15:
            table_name = "min_data15"
        elif period_minutes == 30:
            table_name = "min_data30"
        
        params = {
            'code': code,
            'table_name': table_name,
            'limit_num': int(self.limit_num.value()),
            'initial_cash': 100000.0,  # 默认初始资金
            'ma_short': 20,  # 默认短均线
            'ma_long': 60,  # 默认长均线
            'db_mode': db_mode,
            'stake_qty': 1,  # 默认每次下单数量（避免资金不足导致下单被拒）
            'trade_mode': self._get_trade_mode(),
            'jx1': int(self.jx1_input.value()),
            'jx2': int(self.jx2_input.value()),
            'jx3': int(self.jx3_input.value()),
            'jx4': int(self.jx4_input.value()),
            'jx5': int(self.jx5_input.value()),
            '粘合阈值': float(self.粘合阈值_input.text()),
            'ma4附近阈值': float(self.ma4附近阈值_input.text())
        }
        
        self._start_thread(lambda w: w.run_strategy(params))

    @QtCore.pyqtSlot(str)
    def append_log(self, text: str):
        self.log.append(text)

    @QtCore.pyqtSlot(str)
    def load_chart(self, abspath: str):
        self.web.load(QUrl.fromLocalFile(abspath))

    def auto_aggregate(self):
        """定时自动执行聚合与绘图（每分钟一次），避免并发。"""
        if self.is_busy:
            return
        # 策略自动运行时，停止自动聚合
        if getattr(self, 'strategy_running', False):
            return
        self.handle_aggregate()
    
    def auto_strategy_run(self):
        """定时自动执行策略运行（每分钟一次），避免并发。"""
        if self.is_busy or not self.strategy_running:
            self.append_log(f'自动策略运行跳过: is_busy={self.is_busy}, strategy_running={self.strategy_running}')
            return
        self.append_log('自动策略运行开始...')
        self.handle_backtest()
    
    def start_strategy_auto_run(self):
        """启动策略自动运行"""
        self.strategy_running = True
        # 启动策略定时器，停止聚合定时器
        self.strategy_timer.start()
        if hasattr(self, 'auto_timer'):
            self.auto_timer.stop()
        # 禁用聚合按钮，避免手动触发
        if hasattr(self, 'btn_aggregate'):
            self.btn_aggregate.setEnabled(False)
        self.append_log('策略自动运行已启动（每分钟执行一次）；聚合已停止。')
        self.append_log(f'当前状态: is_busy={self.is_busy}, strategy_running={self.strategy_running}')
        
        # 立即执行一次策略运行
        if not self.is_busy:
            self.append_log('立即执行第一次策略运行...')
            self.handle_backtest()

    def _get_trade_mode(self) -> str:
        text = self.trade_mode_combo.currentText()
        if text == '只做多':
            return 'long_only'
        if text == '只做空':
            return 'short_only'
        return 'both'
    
    def stop_strategy_auto_run(self):
        """停止策略自动运行"""
        self.strategy_running = False
        self.strategy_timer.stop()
        # 恢复聚合定时器与按钮
        if hasattr(self, 'auto_timer'):
            self.auto_timer.start()
        if hasattr(self, 'btn_aggregate'):
            self.btn_aggregate.setEnabled(True)
        self.append_log('策略自动运行已停止；聚合已恢复。')


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


