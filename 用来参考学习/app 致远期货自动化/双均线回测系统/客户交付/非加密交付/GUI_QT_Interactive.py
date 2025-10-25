import os
import sys
import faulthandler
faulthandler.enable(file=sys.stderr, all_threads=True)
from typing import Optional
import pandas as pd
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QUrl, QTimer
from PyQt5.QtWebEngineWidgets import QWebEngineView

from interactive_backtest import (
    InteractiveController,
    run_backtest_interactive,
    build_df_for_code,
)
from huatu_mz import huatucs


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


class BacktestThread(QtCore.QThread):
    log = QtCore.pyqtSignal(str)
    chart_ready = QtCore.pyqtSignal(str)
    finished_bt = QtCore.pyqtSignal(dict)

    def __init__(self, params: dict):
        super().__init__()
        self.params = params
        self.controller = InteractiveController()

    def run(self):
        try:
            # 先构造 df 给 controller 以便 GUI 绘图
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
            self.log.emit(f'[回测线程异常] {e}\n{tb}')


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('双均线交互式回测 (PyQt)')
        self.resize(1200, 820)
        self._build_ui()
        self.bt_thread: Optional[BacktestThread] = None
        self.timer: Optional[QTimer] = None

    def _build_ui(self):
        cw = QtWidgets.QWidget()
        self.setCentralWidget(cw)
        vbox = QtWidgets.QVBoxLayout(cw)

        form = QtWidgets.QGridLayout()
        vbox.addLayout(form)

        # 股票代码输入框，支持直接输入或选择预设的加密货币
        self.code = QtWidgets.QComboBox()
        self.code.setEditable(True)  # 允许编辑
        self.code.addItems(['BTC', 'ETH', 'sh.600030'])  # 默认选项：BTC、ETH、示例股票
        self.code.setCurrentText('BTC')  # 默认选择BTC
        self.code.currentTextChanged.connect(self.on_code_changed)  # 连接代码改变事件
        
        self.table = QtWidgets.QLineEdit('btc_daily')  # 默认比特币表名
        self.limit_num = QtWidgets.QSpinBox(); self.limit_num.setRange(100, 200000); self.limit_num.setValue(4000)
        self.cash = QtWidgets.QDoubleSpinBox(); self.cash.setDecimals(2); self.cash.setMaximum(1e12); self.cash.setValue(10_000_000)
        self.ma_short = QtWidgets.QSpinBox(); self.ma_short.setRange(1, 1000); self.ma_short.setValue(20)
        self.ma_long = QtWidgets.QSpinBox(); self.ma_long.setRange(1, 5000); self.ma_long.setValue(60)
        self.stake = QtWidgets.QSpinBox(); self.stake.setRange(1, 10_000_000); self.stake.setValue(10000)
        self.dbmode = QtWidgets.QComboBox(); self.dbmode.addItems(['crypto', 'baostock', 'legacy'])  # 添加crypto选项
        self.trade_mode = QtWidgets.QComboBox(); self.trade_mode.addItems(['双向', '只做多', '只做空'])

        r = 0
        form.addWidget(QtWidgets.QLabel('股票代码'), r, 0); form.addWidget(self.code, r, 1)
        form.addWidget(QtWidgets.QLabel('表名'), r, 2); form.addWidget(self.table, r, 3)
        form.addWidget(QtWidgets.QLabel('回测条数'), r, 4); form.addWidget(self.limit_num, r, 5); r += 1
        form.addWidget(QtWidgets.QLabel('初始资金'), r, 0); form.addWidget(self.cash, r, 1)
        form.addWidget(QtWidgets.QLabel('短均线'), r, 2); form.addWidget(self.ma_short, r, 3)
        form.addWidget(QtWidgets.QLabel('长均线'), r, 4); form.addWidget(self.ma_long, r, 5); r += 1
        form.addWidget(QtWidgets.QLabel('每次下单股数'), r, 0); form.addWidget(self.stake, r, 1)
        form.addWidget(QtWidgets.QLabel('数据源'), r, 2); form.addWidget(self.dbmode, r, 3)
        form.addWidget(QtWidgets.QLabel('交易方向'), r, 4); form.addWidget(self.trade_mode, r, 5)

        btn_bar = QtWidgets.QHBoxLayout(); vbox.addLayout(btn_bar)
        self.btn_bt = QtWidgets.QPushButton('运行交互式回测'); btn_bar.addWidget(self.btn_bt); btn_bar.addStretch(1)
        self.btn_bt.clicked.connect(self.on_backtest)

        self.log = QtWidgets.QTextEdit(); self.log.setReadOnly(True); self.log.setMinimumHeight(140); vbox.addWidget(self.log)
        self.web = QWebEngineView(); vbox.addWidget(self.web, 1)
        # 内嵌决策条（叠加在图表上方）
        self.decision_bar = DecisionBar(self)
        bar_container = QtWidgets.QWidget(self)
        bar_layout = QtWidgets.QVBoxLayout(bar_container); bar_layout.setContentsMargins(0,0,0,0)
        bar_layout.addWidget(self.decision_bar)
        vbox.addWidget(bar_container)
        self.decision_bar.decisionChosen.connect(self.on_decision_chosen)

    def on_code_changed(self, code: str):
        """当代码改变时，自动设置表名和数据源"""
        if code in ['BTC', 'ETH']:
            # 加密货币模式
            if code == 'BTC':
                self.table.setText('btc_daily')
            else:  # ETH
                self.table.setText('eth_daily')
            self.dbmode.setCurrentText('crypto')
        else:
            # 股票模式
            self.table.setText('daily_data')
            self.dbmode.setCurrentText('baostock')

    def on_backtest(self):
        mode_map = {'双向': 'both', '只做多': 'long_only', '只做空': 'short_only'}
        params = dict(
            code=self.code.currentText().strip(),  # 使用currentText()获取QComboBox的值
            table_name=self.table.text().strip(),
            limit_num=int(self.limit_num.value()),
            initial_cash=float(self.cash.value()),
            ma_short=int(self.ma_short.value()),
            ma_long=int(self.ma_long.value()),
            db_mode=self.dbmode.currentText(),
            stake_qty=int(self.stake.value()),
            trade_mode=mode_map.get(self.trade_mode.currentText(), 'both'),
        )
        self.bt_thread = BacktestThread(params)
        self.bt_thread.chart_ready.connect(self.load_chart)
        self.bt_thread.finished_bt.connect(self.on_finished)
        self.bt_thread.log.connect(self.append_log)
        self.bt_thread.start()
        # 在主线程轮询决策队列
        self.timer = QTimer(self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.poll_decision)
        self.timer.start()

    @QtCore.pyqtSlot(str)
    def load_chart(self, abspath: str):
        self.web.load(QUrl.fromLocalFile(abspath))

    def poll_decision(self):
        if not self.bt_thread or not self.bt_thread.isRunning():
            if self.timer:
                self.timer.stop()
            return
        d = self.bt_thread.controller.get_next_decision_nowait()
        if d is None:
            return
        # 生成预览图，定位到当前决策时间
        try:
            self.render_preview_chart(d)
        except Exception as e:
            self.log.append(f"[预览渲染失败] {e}")
        self.decision_bar.show_with(d)

    @QtCore.pyqtSlot(dict)
    def on_finished(self, result: dict):
        self.log.append(f"完成 期末资产:{result['final_value']:.2f} 盈亏:{result['profit']:.2f} 胜率:{result['win_rate']}% 盈亏比:{result['profit_loss_ratio']}")
        if self.timer:
            self.timer.stop()

    @QtCore.pyqtSlot(str)
    def append_log(self, text: str):
        self.log.append(text)

    def render_preview_chart(self, decision: dict):
        ctrl = self.bt_thread.controller
        df0 = ctrl.df_ref
        if df0 is None or df0.empty:
            return
        dt = pd.Timestamp(decision.get('datetime'))
        df = df0[df0.index <= dt].copy()
        # 填充 huatucs 需要但可能缺失的列
        for col in ['net_profit_list', '多开_output', '空开_output', '空仓_output']:
            if col not in df.columns:
                df[col] = 0
        data_dict = {col: df[col] for col in df.columns}
        data_dict['date'] = df.index
        code = self.code.currentText().strip()  # 使用currentText()获取QComboBox的值
        table = self.table.text().strip()
        zhibiaomc = f"{table}_预览"
        huatucs(data_dict, code, table, zhibiaomc)
        # 加载最新的预览文件
        cand = [f for f in os.listdir('.') if f.startswith('kdj_chart_') and f.endswith('.html')]
        if cand:
            # 选择最新
            chart = max(cand, key=lambda p: os.path.getmtime(p))
            self.web.load(QUrl.fromLocalFile(os.path.abspath(chart)))

    @QtCore.pyqtSlot(str)
    def on_decision_chosen(self, choice: str):
        if self.bt_thread and self.bt_thread.isRunning():
            self.bt_thread.controller.submit_choice(choice)
        self.decision_bar.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow(); w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()


