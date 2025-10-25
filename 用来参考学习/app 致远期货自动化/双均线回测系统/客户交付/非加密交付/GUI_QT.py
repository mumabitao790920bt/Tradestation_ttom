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
            if data_source == 'crypto':
                self.log.emit(f'开始下载 {code} 历史数据...')
                if code == 'BTC':
                    from 下载股票历史数据.crypto_downloader import download_crypto_from_yahoo, save_crypto_to_database
                    # 使用智能路径检测
                    try:
                        from path_fix import get_database_path
                        db_path, table_name = get_database_path('BTC', 'crypto')
                        # 如果数据库已存在，直接返回路径
                        if os.path.exists(db_path):
                            pass
                        else:
                            # 如果不存在，下载到当前目录
                            crypto_data = download_crypto_from_yahoo("BTC-USD", "比特币", days_back=3650)
                            if crypto_data:
                                db_path = save_crypto_to_database(crypto_data, "BTC", "比特币")
                            else:
                                raise Exception("BTC数据下载失败")
                    except ImportError:
                        # 如果路径修复模块不存在，使用原有逻辑
                        crypto_data = download_crypto_from_yahoo("BTC-USD", "比特币", days_back=3650)
                        if crypto_data:
                            db_path = save_crypto_to_database(crypto_data, "BTC", "比特币")
                        else:
                            raise Exception("BTC数据下载失败")
                elif code == 'ETH':
                    from 下载股票历史数据.crypto_downloader import download_crypto_from_yahoo, save_crypto_to_database
                    # 使用智能路径检测
                    try:
                        from path_fix import get_database_path
                        db_path, table_name = get_database_path('ETH', 'crypto')
                        # 如果数据库已存在，直接返回路径
                        if os.path.exists(db_path):
                            pass
                        else:
                            # 如果不存在，下载到当前目录
                            crypto_data = download_crypto_from_yahoo("ETH-USD", "以太坊", days_back=3650)
                            if crypto_data:
                                db_path = save_crypto_to_database(crypto_data, "ETH", "以太坊")
                            else:
                                raise Exception("ETH数据下载失败")
                    except ImportError:
                        # 如果路径修复模块不存在，使用原有逻辑
                        crypto_data = download_crypto_from_yahoo("ETH-USD", "以太坊", days_back=3650)
                        if crypto_data:
                            db_path = save_crypto_to_database(crypto_data, "ETH", "以太坊")
                        else:
                            raise Exception("ETH数据下载失败")
                else:
                    self.log.emit(f'不支持的加密货币代码: {code}')
                    return
                self.log.emit(f'下载完成: {db_path}')
            else:
                self.log.emit(f'开始下载 {code} 历史数据...')
                db_path = download_daily_to_sqlite(code, code)
                self.log.emit(f'下载完成: {db_path}')
        except Exception as e:
            self.log.emit(f'下载失败: {e}')
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
        self.data_source.addItems(['crypto', 'baostock', 'legacy'])
        self.data_source.currentTextChanged.connect(self.on_data_source_changed)
        
        # 添加数据源说明标签
        self.data_source_label = QtWidgets.QLabel('数据源说明：crypto=加密货币, baostock=宝股票数据, legacy=原有股票数据')
        self.data_source_label.setStyleSheet("color: blue; font-size: 10px;")
        
        # 使用QStackedWidget来管理代码/币种输入控件
        self.code_stack = QtWidgets.QStackedWidget()
        
        # 股票代码输入框
        self.code_input = QtWidgets.QLineEdit()
        self.code_input.setPlaceholderText('输入股票代码，如：sh.600030')
        
        # 加密货币选择下拉框
        self.crypto_combo = QtWidgets.QComboBox()
        self.crypto_combo.addItems(['BTC', 'ETH'])
        self.crypto_combo.currentTextChanged.connect(self.on_crypto_code_changed)
        
        # 将两个控件添加到堆叠控件中
        self.code_stack.addWidget(self.code_input)  # 索引0：股票输入框
        self.code_stack.addWidget(self.crypto_combo)  # 索引1：加密货币下拉框
        
        self.table = QtWidgets.QLineEdit('btc_daily')  # 默认比特币表名
        self.limit_num = QtWidgets.QSpinBox()
        self.limit_num.setRange(100, 200000)
        self.limit_num.setValue(4000)
        self.cash = QtWidgets.QDoubleSpinBox()
        self.cash.setDecimals(2)
        self.cash.setMaximum(1e12)
        self.cash.setValue(10_000_000)
        self.ma_short = QtWidgets.QSpinBox()
        self.ma_short.setRange(1, 1000)
        self.ma_short.setValue(20)
        self.ma_long = QtWidgets.QSpinBox()
        self.ma_long.setRange(1, 5000)
        self.ma_long.setValue(60)
        self.stake = QtWidgets.QSpinBox()
        self.stake.setRange(1, 10_000_000)
        self.stake.setValue(10000)
        self.dbmode = QtWidgets.QComboBox()
        self.dbmode.addItems(['crypto', 'baostock', 'legacy'])
        self.trade_mode = QtWidgets.QComboBox()
        self.trade_mode.addItems(['双向', '只做多', '只做空'])

        r = 0
        self.form_layout.addWidget(QtWidgets.QLabel('数据源'), r, 0)
        self.form_layout.addWidget(self.data_source, r, 1)
        self.form_layout.addWidget(self.data_source_label, r, 2, 1, 4)  # 跨4列显示说明
        r += 1
        self.form_layout.addWidget(QtWidgets.QLabel('代码/币种'), r, 0)
        self.form_layout.addWidget(self.code_stack, r, 1)  # 使用堆叠控件
        self.form_layout.addWidget(QtWidgets.QLabel('表名'), r, 2)
        self.form_layout.addWidget(self.table, r, 3)
        r += 1
        self.form_layout.addWidget(QtWidgets.QLabel('初始资金'), r, 0)
        self.form_layout.addWidget(self.cash, r, 1)
        self.form_layout.addWidget(QtWidgets.QLabel('短均线'), r, 2)
        self.form_layout.addWidget(self.ma_short, r, 3)
        self.form_layout.addWidget(QtWidgets.QLabel('长均线'), r, 4)
        self.form_layout.addWidget(self.ma_long, r, 5)
        r += 1
        self.form_layout.addWidget(QtWidgets.QLabel('K线数量'), r, 0)
        self.form_layout.addWidget(self.limit_num, r, 1)
        self.form_layout.addWidget(QtWidgets.QLabel('每次下单股数'), r, 2)
        self.form_layout.addWidget(self.stake, r, 3)
        self.form_layout.addWidget(QtWidgets.QLabel('交易方向'), r, 4)
        self.form_layout.addWidget(self.trade_mode, r, 5)

        btn_bar = QtWidgets.QHBoxLayout()
        vbox.addLayout(btn_bar)
        self.btn_dl = QtWidgets.QPushButton('下载数据')
        self.btn_bt = QtWidgets.QPushButton('运行回测')
        btn_bar.addWidget(self.btn_dl)
        btn_bar.addWidget(self.btn_bt)
        btn_bar.addStretch(1)

        self.log = QtWidgets.QTextEdit()
        self.log.setReadOnly(True)
        self.log.setMinimumHeight(140)
        vbox.addWidget(self.log)

        self.web = QWebEngineView()
        vbox.addWidget(self.web, 1)

        self.btn_dl.clicked.connect(self.handle_download)
        self.btn_bt.clicked.connect(self.handle_backtest)
        
        # 初始化时设置加密货币模式
        self.on_data_source_changed('crypto')

    def on_data_source_changed(self, source: str):
        """数据源改变时的处理"""
        if source == 'crypto':
            # 加密货币模式：显示下拉选择框
            self.code_stack.setCurrentIndex(1)  # 显示加密货币下拉框
            self.crypto_combo.setCurrentText('BTC')  # 默认选择BTC
            self.table.setText('btc_daily')
            self.table.setEnabled(False)  # 表名根据代码自动设置
            self.dbmode.setCurrentText('crypto')
            
        else:
            # 股票模式：显示输入框
            self.code_stack.setCurrentIndex(0)  # 显示股票代码输入框
            self.table.setEnabled(True)
            if source == 'baostock':
                self.code_input.setText('sh.600030')
                self.table.setText('daily_data')
                self.dbmode.setCurrentText('baostock')
            else:  # legacy
                self.code_input.setText('sh.600030')
                self.table.setText('daily_data')
                self.dbmode.setCurrentText('legacy')
    
    def on_crypto_code_changed(self, code: str):
        """加密货币代码改变时的处理"""
        if code == 'BTC':
            self.table.setText('btc_daily')
        elif code == 'ETH':
            self.table.setText('eth_daily')

    def _start_thread(self, fn, *args):
        self.btn_dl.setEnabled(False)
        self.btn_bt.setEnabled(False)
        th = QtCore.QThread(self)
        wk = Worker()
        wk.moveToThread(th)
        wk.log.connect(self.append_log)
        wk.done.connect(th.quit)
        wk.done.connect(lambda: self.btn_dl.setEnabled(True))
        wk.done.connect(lambda: self.btn_bt.setEnabled(True))
        wk.chart_ready.connect(self.load_chart)
        th.started.connect(lambda: fn(wk, *args))
        th.finished.connect(wk.deleteLater)
        th.start()

    def handle_download(self):
        data_source = self.data_source.currentText()
        
        # 根据数据源获取代码
        if data_source == 'crypto':
            code = self.crypto_combo.currentText()
        else:
            code = self.code_input.text().strip()
            if not code:
                self.append_log('请输入股票代码')
                return
        
        self._start_thread(lambda w: w.run_download(code, data_source))

    def handle_backtest(self):
        mode_map = {'双向': 'both', '只做多': 'long_only', '只做空': 'short_only'}
        
        # 根据数据源获取代码
        data_source = self.data_source.currentText()
        if data_source == 'crypto':
            code = self.crypto_combo.currentText()
        else:
            code = self.code_input.text().strip()
        
        params = dict(
            code=code,
            table_name=self.table.text().strip(),
            limit_num=int(self.limit_num.value()),
            initial_cash=float(self.cash.value()),
            ma_short=int(self.ma_short.value()),
            ma_long=int(self.ma_long.value()),
            db_mode=self.dbmode.currentText(),
            stake_qty=int(self.stake.value()),
            trade_mode=mode_map.get(self.trade_mode.currentText(), 'both'),
        )
        self._start_thread(lambda w: w.run_backtest(params))

    @QtCore.pyqtSlot(str)
    def append_log(self, text: str):
        self.log.append(text)

    @QtCore.pyqtSlot(str)
    def load_chart(self, abspath: str):
        self.web.load(QUrl.fromLocalFile(abspath))


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


