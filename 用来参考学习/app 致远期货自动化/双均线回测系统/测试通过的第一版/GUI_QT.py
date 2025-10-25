import os
import sys
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtWebEngineWidgets import QWebEngineView

from 回测示例 import run_backtest
from 下载股票历史数据.downloader_bridge import download_daily_to_sqlite


class Worker(QtCore.QObject):
    log = QtCore.pyqtSignal(str)
    done = QtCore.pyqtSignal()
    chart_ready = QtCore.pyqtSignal(str)

    def run_download(self, code: str):
        try:
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

        form = QtWidgets.QGridLayout()
        vbox.addLayout(form)

        self.code = QtWidgets.QLineEdit('sh.600030')
        self.table = QtWidgets.QLineEdit('daily_data')
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
        self.dbmode.addItems(['baostock', 'legacy'])
        self.trade_mode = QtWidgets.QComboBox()
        self.trade_mode.addItems(['双向', '只做多', '只做空'])

        r = 0
        form.addWidget(QtWidgets.QLabel('股票代码'), r, 0)
        form.addWidget(self.code, r, 1)
        form.addWidget(QtWidgets.QLabel('表名'), r, 2)
        form.addWidget(self.table, r, 3)
        form.addWidget(QtWidgets.QLabel('回测条数'), r, 4)
        form.addWidget(self.limit_num, r, 5)
        r += 1
        form.addWidget(QtWidgets.QLabel('初始资金'), r, 0)
        form.addWidget(self.cash, r, 1)
        form.addWidget(QtWidgets.QLabel('短均线'), r, 2)
        form.addWidget(self.ma_short, r, 3)
        form.addWidget(QtWidgets.QLabel('长均线'), r, 4)
        form.addWidget(self.ma_long, r, 5)
        r += 1
        form.addWidget(QtWidgets.QLabel('每次下单股数'), r, 0)
        form.addWidget(self.stake, r, 1)
        form.addWidget(QtWidgets.QLabel('数据源'), r, 2)
        form.addWidget(self.dbmode, r, 3)
        form.addWidget(QtWidgets.QLabel('交易方向'), r, 4)
        form.addWidget(self.trade_mode, r, 5)

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
        code = self.code.text().strip()
        if not code:
            self.append_log('请输入股票代码')
            return
        self._start_thread(lambda w: w.run_download(code))

    def handle_backtest(self):
        mode_map = {'双向': 'both', '只做多': 'long_only', '只做空': 'short_only'}
        params = dict(
            code=self.code.text().strip(),
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


