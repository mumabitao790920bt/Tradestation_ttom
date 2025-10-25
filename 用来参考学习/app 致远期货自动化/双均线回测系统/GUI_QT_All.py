import os
import sys
import faulthandler
from typing import Optional

faulthandler.enable(file=sys.stderr, all_threads=True)

# WebEngine稳定性：尝试禁用沙箱/硬件加速，必要时回退到系统浏览器
os.environ.setdefault('QTWEBENGINE_DISABLE_SANDBOX', '1')
os.environ.setdefault('QTWEBENGINE_CHROMIUM_FLAGS', '--disable-gpu')

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QUrl, QTimer
# 延迟导入 QWebEngineView，避免部分环境在模块导入期崩溃
QWebEngineView = None

from 回测示例 import run_backtest
from interactive_backtest import (
    InteractiveController,
    run_backtest_interactive,
    build_df_for_code,
)
from 下载股票历史数据.downloader_bridge import download_daily_to_sqlite
from huatu_mz import huatucs
import pandas as pd


class DecisionBar(QtWidgets.QFrame):
    decisionChosen = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self.setStyleSheet('QFrame { background: rgba(255,255,255,0.95); border:1px solid #888; }')
        h = QtWidgets.QHBoxLayout(self)
        self.lbl = QtWidgets.QLabel('')
        h.addWidget(self.lbl, 1)
        self.btn_follow = QtWidgets.QPushButton('按策略执行')
        self.btn_skip = QtWidgets.QPushButton('跳过')
        h.addWidget(self.btn_follow)
        h.addWidget(self.btn_skip)
        self.btn_follow.clicked.connect(lambda: self.decisionChosen.emit('follow'))
        self.btn_skip.clicked.connect(lambda: self.decisionChosen.emit('skip'))
        self.hide()

    def show_with(self, decision: dict):
        action_map = {
            'open_long': '开多',
            'open_short': '开空',
            'close_long': '平多',
            'close_short': '平空',
            'close_long_then_open_short': '平多并开空',
            'close_short_then_open_long': '平空并开多',
        }
        dir_map = {1: '多头', -1: '空头', 0: '空仓'}
        action_cn = action_map.get(decision.get('action', ''), str(decision.get('action', '')))
        dir_cn = dir_map.get(decision.get('direction'), str(decision.get('direction')))
        self.lbl.setText(
            f"时间: {decision.get('datetime')}  动作: {action_cn}  方向: {dir_cn}  现价: {decision.get('price')}  权益: {decision.get('equity')}"
        )
        self.show()


class BacktestThreadSimple(QtCore.QThread):
    chart_ready = QtCore.pyqtSignal(str)
    finished_bt = QtCore.pyqtSignal(dict)
    log = QtCore.pyqtSignal(str)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params

    def run(self):
        try:
            result = run_backtest(**self.params)
            chart = result.get('chart_path') if isinstance(result, dict) else None
            # 兼容我们之前的 run_backtest 返回值结构（若不同，这里忽略，直接从目录取最新）
            if not chart or not os.path.exists(chart):
                cand = [f for f in os.listdir('.') if f.startswith('kdj_chart_') and f.endswith('.html')]
                if cand:
                    chart = max(cand, key=lambda p: os.path.getmtime(p))
            if chart:
                self.chart_ready.emit(os.path.abspath(chart))
            # 简要汇总
            self.finished_bt.emit({'ok': True})
        except Exception as e:
            import traceback
            tb = ''.join(traceback.format_exc())
            self.log.emit(f'[普通回测异常] {e}\n{tb}')


class BacktestThreadInteractive(QtCore.QThread):
    chart_ready = QtCore.pyqtSignal(str)
    finished_bt = QtCore.pyqtSignal(dict)
    log = QtCore.pyqtSignal(str)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params
        self.controller = InteractiveController()

    def run(self):
        try:
            # 先构造 df 给 controller 以便 GUI 渲染预览
            df = build_df_for_code(
                code=self.params['code'],
                table_name=self.params['table_name'],
                limit_num=self.params['limit_num'],
                ma_short=self.params['ma_short'],
                ma_long=self.params['ma_long'],
                db_mode=self.params.get('db_mode', 'baostock'),
            )
            self.controller.set_df(df)

            result = run_backtest_interactive(controller=self.controller, **self.params)
            chart = result.get('chart_path')
            if chart and os.path.exists(chart):
                self.chart_ready.emit(os.path.abspath(chart))
            self.finished_bt.emit(result)
        except Exception as e:
            import traceback
            tb = ''.join(traceback.format_exc())
            self.log.emit(f'[交互回测异常] {e}\n{tb}')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('双均线回测（普通/交互）- PyQt All-In-One')
        self.resize(1200, 820)
        self._build_ui()
        self.timer: Optional[QTimer] = None
        self.bt_thread_simple: Optional[BacktestThreadSimple] = None
        self.bt_thread_interactive: Optional[BacktestThreadInteractive] = None

    def _build_ui(self):
        cw = QtWidgets.QWidget(); self.setCentralWidget(cw)
        vbox = QtWidgets.QVBoxLayout(cw)

        form = QtWidgets.QGridLayout(); vbox.addLayout(form)
        self.code = QtWidgets.QLineEdit('sh.600030')
        self.table = QtWidgets.QLineEdit('daily_data')
        self.limit_num = QtWidgets.QSpinBox(); self.limit_num.setRange(100, 200000); self.limit_num.setValue(4000)
        self.cash = QtWidgets.QDoubleSpinBox(); self.cash.setDecimals(2); self.cash.setMaximum(1e12); self.cash.setValue(10_000_000)
        self.ma_short = QtWidgets.QSpinBox(); self.ma_short.setRange(1, 1000); self.ma_short.setValue(20)
        self.ma_long = QtWidgets.QSpinBox(); self.ma_long.setRange(1, 5000); self.ma_long.setValue(60)
        self.stake = QtWidgets.QSpinBox(); self.stake.setRange(1, 10_000_000); self.stake.setValue(10000)
        self.dbmode = QtWidgets.QComboBox(); self.dbmode.addItems(['baostock', 'legacy'])
        self.trade_mode = QtWidgets.QComboBox(); self.trade_mode.addItems(['双向', '只做多', '只做空'])
        self.chk_interactive = QtWidgets.QCheckBox('交互式模式')

        r = 0
        form.addWidget(QtWidgets.QLabel('股票代码'), r, 0); form.addWidget(self.code, r, 1)
        form.addWidget(QtWidgets.QLabel('表名'), r, 2); form.addWidget(self.table, r, 3)
        form.addWidget(QtWidgets.QLabel('回测条数'), r, 4); form.addWidget(self.limit_num, r, 5); r += 1
        form.addWidget(QtWidgets.QLabel('初始资金'), r, 0); form.addWidget(self.cash, r, 1)
        form.addWidget(QtWidgets.QLabel('短均线'), r, 2); form.addWidget(self.ma_short, r, 3)
        form.addWidget(QtWidgets.QLabel('长均线'), r, 4); form.addWidget(self.ma_long, r, 5); r += 1
        form.addWidget(QtWidgets.QLabel('每次下单股数'), r, 0); form.addWidget(self.stake, r, 1)
        form.addWidget(QtWidgets.QLabel('数据源'), r, 2); form.addWidget(self.dbmode, r, 3)
        form.addWidget(QtWidgets.QLabel('交易方向'), r, 4); form.addWidget(self.trade_mode, r, 5); r += 1
        form.addWidget(self.chk_interactive, r, 0)

        btn_bar = QtWidgets.QHBoxLayout(); vbox.addLayout(btn_bar)
        self.btn_download = QtWidgets.QPushButton('下载数据')
        self.btn_run = QtWidgets.QPushButton('运行回测')
        btn_bar.addWidget(self.btn_download)
        btn_bar.addWidget(self.btn_run)
        btn_bar.addStretch(1)
        self.btn_download.clicked.connect(self.on_download)
        self.btn_run.clicked.connect(self.on_run)

        self.log = QtWidgets.QTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(140); vbox.addWidget(self.log)
        # 延迟创建 WebView，避免部分环境初始化崩溃
        self.web_container = QtWidgets.QWidget(); self.web_layout = QtWidgets.QVBoxLayout(self.web_container)
        self.web_layout.setContentsMargins(0,0,0,0)
        self.web = None
        vbox.addWidget(self.web_container, 1)

        # 决策条
        self.decision_bar = DecisionBar(self)
        vbox.addWidget(self.decision_bar)
        self.decision_bar.decisionChosen.connect(self.on_decision_chosen)

    def on_download(self):
        code = self.code.text().strip()
        if not code:
            self.log.append('请输入股票代码')
            return
        try:
            path = download_daily_to_sqlite(code, code)
            self.log.append(f'下载完成: {path}')
        except Exception as e:
            self.log.append(f'下载失败: {e}')

    def on_run(self):
        # 关闭可能存在的旧计时器
        if self.timer:
            self.timer.stop(); self.timer = None
        # 参数收集
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
        if self.chk_interactive.isChecked():
            # 交互回测
            self.bt_thread_interactive = BacktestThreadInteractive(params)
            self.bt_thread_interactive.chart_ready.connect(self.load_chart)
            self.bt_thread_interactive.finished_bt.connect(self.on_finished)
            self.bt_thread_interactive.log.connect(self.append_log)
            self.bt_thread_interactive.start()
            # 主线程轮询决策
            self.timer = QTimer(self); self.timer.setInterval(100); self.timer.timeout.connect(self.poll_decision)
            self.timer.start()
        else:
            # 普通回测
            self.decision_bar.hide()
            self.bt_thread_simple = BacktestThreadSimple(params)
            self.bt_thread_simple.chart_ready.connect(self.load_chart)
            self.bt_thread_simple.finished_bt.connect(self.on_finished)
            self.bt_thread_simple.log.connect(self.append_log)
            self.bt_thread_simple.start()

    @QtCore.pyqtSlot(str)
    def load_chart(self, abspath: str):
        try:
            global QWebEngineView
            if QWebEngineView is None:
                from PyQt5.QtWebEngineWidgets import QWebEngineView as _QWebView
                QWebEngineView = _QWebView
            if self.web is None:
                self.web = QWebEngineView()
                self.web_layout.addWidget(self.web)
            self.web.load(QUrl.fromLocalFile(abspath))
        except Exception as e:
            import webbrowser
            self.append_log(f'[WebView不可用] {e} -> 改用系统浏览器')
            webbrowser.open_new_tab(abspath)

    def poll_decision(self):
        th = self.bt_thread_interactive
        if not th or not th.isRunning():
            if self.timer:
                self.timer.stop(); self.timer=None
            return
        d = th.controller.get_next_decision_nowait()
        if d is None:
            return
        try:
            self.render_preview_chart(d)
        except Exception as e:
            self.append_log(f'[预览失败]{e}')
        self.decision_bar.show_with(d)

    def render_preview_chart(self, decision: dict):
        ctrl = self.bt_thread_interactive.controller if self.bt_thread_interactive else None
        df0 = ctrl.df_ref if ctrl else None
        if df0 is None or df0.empty:
            return
        dt = pd.Timestamp(decision.get('datetime'))
        df = df0[df0.index <= dt].copy()
        for col in ['net_profit_list', '多开_output', '空开_output', '空仓_output']:
            if col not in df.columns:
                df[col] = 0
        data_dict = {col: df[col] for col in df.columns}
        data_dict['date'] = df.index
        code = self.code.text().strip(); table = self.table.text().strip()
        zhibiaomc = f'{table}_预览'
        huatucs(data_dict, code, table, zhibiaomc)
        cand = [f for f in os.listdir('.') if f.startswith('kdj_chart_') and f.endswith('.html')]
        if cand:
            chart = max(cand, key=lambda p: os.path.getmtime(p))
            self.load_chart(os.path.abspath(chart))

    @QtCore.pyqtSlot(str)
    def append_log(self, text: str):
        self.log.append(text)

    @QtCore.pyqtSlot(str)
    def on_decision_chosen(self, choice: str):
        th = self.bt_thread_interactive
        if th and th.isRunning():
            th.controller.submit_choice(choice)
        self.decision_bar.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


