import os
import threading
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText

import pandas as pd

from 回测示例 import run_backtest
from 下载股票历史数据.downloader_bridge import download_daily_to_sqlite


class BacktestGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('双均线回测系统 - 参数配置与可视化')
        self.geometry('1000x720')

        self._build_widgets()

    def _build_widgets(self):
        frm = ttk.Frame(self)
        frm.pack(fill='x', padx=10, pady=10)

        # 参数区
        self.code_var = tk.StringVar(value='sh.600030')
        self.table_var = tk.StringVar(value='daily_data')
        self.limit_var = tk.IntVar(value=4000)
        self.cash_var = tk.DoubleVar(value=10_000_000)
        self.ma_short_var = tk.IntVar(value=20)
        self.ma_long_var = tk.IntVar(value=60)
        self.dbmode_var = tk.StringVar(value='baostock')
        self.stake_var = tk.IntVar(value=10000)

        row = 0
        ttk.Label(frm, text='股票代码:').grid(row=row, column=0, sticky='e')
        ttk.Entry(frm, textvariable=self.code_var, width=16).grid(row=row, column=1, sticky='w', padx=6)
        ttk.Label(frm, text='表名:').grid(row=row, column=2, sticky='e')
        ttk.Entry(frm, textvariable=self.table_var, width=16).grid(row=row, column=3, sticky='w', padx=6)
        ttk.Label(frm, text='回测条数:').grid(row=row, column=4, sticky='e')
        ttk.Entry(frm, textvariable=self.limit_var, width=10).grid(row=row, column=5, sticky='w', padx=6)
        row += 1

        ttk.Label(frm, text='初始资金:').grid(row=row, column=0, sticky='e')
        ttk.Entry(frm, textvariable=self.cash_var, width=16).grid(row=row, column=1, sticky='w', padx=6)
        ttk.Label(frm, text='短均线:').grid(row=row, column=2, sticky='e')
        ttk.Entry(frm, textvariable=self.ma_short_var, width=10).grid(row=row, column=3, sticky='w', padx=6)
        ttk.Label(frm, text='长均线:').grid(row=row, column=4, sticky='e')
        ttk.Entry(frm, textvariable=self.ma_long_var, width=10).grid(row=row, column=5, sticky='w', padx=6)
        row += 1

        ttk.Label(frm, text='数据源:').grid(row=row, column=0, sticky='e')
        ttk.Combobox(frm, textvariable=self.dbmode_var, values=['baostock', 'legacy'], width=14, state='readonly').grid(row=row, column=1, sticky='w', padx=6)
        ttk.Label(frm, text='每次下单股数:').grid(row=row, column=2, sticky='e')
        ttk.Entry(frm, textvariable=self.stake_var, width=12).grid(row=row, column=3, sticky='w', padx=6)

        # 操作按钮
        btn_frm = ttk.Frame(self)
        btn_frm.pack(fill='x', padx=10)
        ttk.Button(btn_frm, text='下载数据', command=self.on_download).pack(side='left')
        ttk.Button(btn_frm, text='运行回测', command=self.on_backtest).pack(side='left', padx=8)
        ttk.Button(btn_frm, text='打开图表', command=self.on_open_chart).pack(side='left')

        # 日志
        self.log = ScrolledText(self, height=10)
        self.log.pack(fill='both', expand=False, padx=10, pady=10)

        # 网页显示：优先使用 pywebview（独立进程窗口）；否则退化到系统浏览器
        self.chart_path = None
        self.webview_available = False
        try:
            import webview  # pywebview
            self.webview_available = True
        except Exception:
            ph = ttk.Label(self, text='未检测到 pywebview，将使用系统浏览器打开（可 pip install pywebview 启用内嵌）。')
            ph.pack(fill='x', padx=10, pady=6)

    def append_log(self, text: str):
        self.log.insert('end', text + '\n')
        self.log.see('end')
        self.update_idletasks()

    def on_download(self):
        code = self.code_var.get().strip()
        if not code:
            messagebox.showwarning('提示', '请输入股票代码')
            return
        def task():
            try:
                self.append_log(f'开始下载 {code} 历史数据...')
                db_path = download_daily_to_sqlite(code, code)
                self.append_log(f'下载完成: {db_path}')
            except Exception as e:
                messagebox.showerror('下载失败', str(e))
        threading.Thread(target=task, daemon=True).start()

    def on_backtest(self):
        code = self.code_var.get().strip()
        table = self.table_var.get().strip()
        limit_num = self.limit_var.get()
        initial_cash = self.cash_var.get()
        ma_s = self.ma_short_var.get()
        ma_l = self.ma_long_var.get()
        dbmode = self.dbmode_var.get()
        stake_qty = self.stake_var.get()

        def task():
            try:
                self.append_log('开始回测...')
                result = run_backtest(
                    code=code,
                    table_name=table,
                    limit_num=limit_num,
                    initial_cash=initial_cash,
                    ma_short=ma_s,
                    ma_long=ma_l,
                    db_mode=dbmode,
                    stake_qty=stake_qty
                )
                self.chart_path = result.get('chart_path')
                self.append_log(f"回测完成 期末资产: {result['final_value']:.2f}  盈亏: {result['profit']:.2f}  胜率: {result['win_rate']}%  盈亏比: {result['profit_loss_ratio']}")
                if self.chart_path:
                    self.append_log(f'图表: {self.chart_path}')
                    # 内嵌展示或打开浏览器
                    self._display_chart(self.chart_path)
            except Exception as e:
                messagebox.showerror('回测失败', str(e))
        threading.Thread(target=task, daemon=True).start()

    def on_open_chart(self):
        if not self.chart_path or not os.path.exists(self.chart_path):
            messagebox.showinfo('提示', '尚未生成图表或路径不存在')
            return
        self._display_chart(self.chart_path)

    def _display_chart(self, path: str):
        abspath = os.path.abspath(path)
        if self.webview_available:
            try:
                # 在独立进程中启动 pywebview，避免“必须在主线程运行”的限制
                import sys, subprocess, shlex
                py = sys.executable
                code = (
                    "import webview, sys; p=sys.argv[1]; "
                    "webview.create_window('回测图表', p); webview.start()"
                )
                subprocess.Popen([py, '-c', code, abspath])
                return
            except Exception:
                pass
        webbrowser.open_new_tab(abspath)


if __name__ == '__main__':
    app = BacktestGUI()
    app.mainloop()


