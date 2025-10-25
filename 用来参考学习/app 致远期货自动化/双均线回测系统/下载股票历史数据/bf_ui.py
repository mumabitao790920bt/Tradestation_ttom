import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import pandas as pd
import datetime
import time
import os
from tkcalendar import DateEntry
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates
from matplotlib.figure import Figure
import threading
import sys
import io
import contextlib
import pymysql

# 导入数据采集器
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from baostock_complete_data_collector_v2 import BaoStockCompleteDataCollectorV2


def check_remote_authorization():
    """检查远程数据库授权"""
    try:
        # 数据库连接配置
        db_config = {
            'host': '115.159.44.226',
            'port': 3306,
            'user': 'xianyu',
            'password': 'zxz2jwwRTYmMkpyT',
            'database': 'xianyu',
            'charset': 'utf8mb4'
        }

        # 连接数据库
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()

        # 查询phone字段为tdx_sjjk_yha的记录
        query = "SELECT COUNT(*) FROM xianyu_account WHERE phone = 'tdx_sjjk_yha'"
        cursor.execute(query)
        result = cursor.fetchone()

        cursor.close()
        conn.close()

        # 如果找到记录，返回True，否则返回False
        return result[0] > 0

    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
        return False


class StockAnalysisGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("股票数据分析系统")
        self.root.geometry("1200x900")  # 增加窗口高度
        self.root.configure(bg='#f0f0f0')

        # 数据文件夹路径
        self.data_folder = r'gupiao_lssj'

        # 初始化数据采集器
        self.data_collector = BaoStockCompleteDataCollectorV2()

        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_label = tk.Label(self.root, text="股票数据分析系统",
                               font=("Arial", 20, "bold"),
                               bg='#f0f0f0', fg='#2c3e50')
        title_label.pack(pady=10)

        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # 左侧面板 - 输入区域
        left_frame = ttk.LabelFrame(main_frame, text="数据输入", padding=10)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # 股票代码输入
        ttk.Label(left_frame, text="股票代码:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.stock_code_var = tk.StringVar()
        self.stock_code_entry = ttk.Entry(left_frame, textvariable=self.stock_code_var, width=20)
        self.stock_code_entry.grid(row=0, column=1, sticky=tk.W, pady=5)
        self.query_button = ttk.Button(left_frame, text="查询", command=self.query_stock_data)
        self.query_button.grid(row=0, column=2, padx=5, pady=5)

        # 状态显示
        self.status_label = ttk.Label(left_frame, text="状态: 未连接", foreground="red")
        self.status_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)

        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(left_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=2)

        # 时间范围选择
        ttk.Label(left_frame, text="开始日期:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.start_date = DateEntry(left_frame, width=15, background='darkblue', foreground='white',
                                    borderwidth=2, date_pattern='yyyy-mm-dd')
        self.start_date.grid(row=3, column=1, sticky=tk.W, pady=5)

        ttk.Label(left_frame, text="结束日期:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.end_date = DateEntry(left_frame, width=15, background='darkblue', foreground='white',
                                  borderwidth=2, date_pattern='yyyy-mm-dd')
        self.end_date.grid(row=4, column=1, sticky=tk.W, pady=5)

        # 分析按钮
        ttk.Button(left_frame, text="分析K线数据", command=self.analyze_kline_data).grid(row=5, column=0, columnspan=3,
                                                                                         pady=10)

        # 周期选择（多选框）
        ttk.Label(left_frame, text="选择周期:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.daily_var = tk.BooleanVar(value=True)
        self.weekly_var = tk.BooleanVar()
        self.monthly_var = tk.BooleanVar()
        self.quarterly_var = tk.BooleanVar()
        self.yearly_var = tk.BooleanVar()
        ttk.Checkbutton(left_frame, text='日线', variable=self.daily_var).grid(row=6, column=1, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_frame, text='周线', variable=self.weekly_var).grid(row=7, column=1, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_frame, text='月线', variable=self.monthly_var).grid(row=8, column=1, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_frame, text='季线', variable=self.quarterly_var).grid(row=9, column=1, sticky=tk.W, pady=2)
        ttk.Checkbutton(left_frame, text='年线', variable=self.yearly_var).grid(row=10, column=1, sticky=tk.W, pady=2)
        ttk.Button(left_frame, text="分析成交量数据", command=self.analyze_volume_data).grid(row=11, column=0,
                                                                                             columnspan=3, pady=10)

        # 计算功能模块
        ttk.Label(left_frame, text="输入:").grid(row=12, column=2, sticky=tk.W, pady=(10, 5))

        # 输入框 a1-a6
        self.a1_var = tk.StringVar()
        self.a2_var = tk.StringVar()
        self.a3_var = tk.StringVar()
        self.a4_var = tk.StringVar()
        self.a5_var = tk.StringVar()
        self.a6_var = tk.StringVar()

        # 输入框布局 - 一行排列，a1与a2间距更大，a2-a6等距
        ttk.Entry(left_frame, textvariable=self.a1_var, width=6).grid(row=13, column=2, padx=(0, 15), pady=2)
        ttk.Entry(left_frame, textvariable=self.a2_var, width=6).grid(row=13, column=3, padx=2, pady=2)
        ttk.Entry(left_frame, textvariable=self.a3_var, width=6).grid(row=13, column=4, padx=2, pady=2)
        ttk.Entry(left_frame, textvariable=self.a4_var, width=6).grid(row=13, column=5, padx=2, pady=2)
        ttk.Entry(left_frame, textvariable=self.a5_var, width=6).grid(row=13, column=6, padx=2, pady=2)
        ttk.Entry(left_frame, textvariable=self.a6_var, width=6).grid(row=13, column=7, padx=2, pady=2)

        # 输出标签
        ttk.Label(left_frame, text="输出:").grid(row=15, column=2, sticky=tk.W, pady=(10, 5))

        # 输出框 b1-b5
        self.b1_var = tk.StringVar()
        self.b2_var = tk.StringVar()
        self.b3_var = tk.StringVar()
        self.b4_var = tk.StringVar()
        self.b5_var = tk.StringVar()

        # 输出框布局 - 与a2-a6对齐
        ttk.Entry(left_frame, textvariable=self.b1_var, width=6, state='readonly').grid(row=16, column=3, padx=2,
                                                                                        pady=2)
        ttk.Entry(left_frame, textvariable=self.b2_var, width=6, state='readonly').grid(row=16, column=4, padx=2,
                                                                                        pady=2)
        ttk.Entry(left_frame, textvariable=self.b3_var, width=6, state='readonly').grid(row=16, column=5, padx=2,
                                                                                        pady=2)
        ttk.Entry(left_frame, textvariable=self.b4_var, width=6, state='readonly').grid(row=16, column=6, padx=2,
                                                                                        pady=2)
        ttk.Entry(left_frame, textvariable=self.b5_var, width=6, state='readonly').grid(row=16, column=7, padx=2,
                                                                                        pady=2)

        # 计算按钮
        ttk.Button(left_frame, text="计算", command=self.calculate_values).grid(row=18, column=0, columnspan=6, pady=10)

        # 导出按钮
        ttk.Button(left_frame, text="导出分析结果", command=self.export_analysis_results).grid(row=19, column=0,
                                                                                               columnspan=6, pady=10)

        # 右侧面板 - 结果显示
        right_frame = ttk.LabelFrame(main_frame, text="分析结果", padding=10)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        # 创建Notebook用于分页显示
        self.notebook = ttk.Notebook(right_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # K线分析页面
        self.kline_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.kline_frame, text="K线分析")

        # 成交量分析页面
        self.volume_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.volume_frame, text="成交量分析")

        # 创建结果显示区域
        self.create_result_widgets()

        # 底部日志显示区域
        self.create_log_widgets()

    def create_result_widgets(self):
        """创建结果显示组件"""
        # K线分析结果
        self.kline_text = tk.Text(self.kline_frame, height=20, width=60)
        kline_scrollbar = ttk.Scrollbar(self.kline_frame, orient=tk.VERTICAL, command=self.kline_text.yview)
        self.kline_text.configure(yscrollcommand=kline_scrollbar.set)
        self.kline_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kline_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 成交量分析结果
        self.volume_text = tk.Text(self.volume_frame, height=20, width=60)
        volume_scrollbar = ttk.Scrollbar(self.volume_frame, orient=tk.VERTICAL, command=self.volume_text.yview)
        self.volume_text.configure(yscrollcommand=volume_scrollbar.set)
        self.volume_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        volume_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def create_log_widgets(self):
        """创建日志显示组件"""
        # 底部日志框架
        log_frame = ttk.LabelFrame(self.root, text="数据采集日志", padding=10)
        log_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        # 日志文本框
        self.log_text = tk.Text(log_frame, height=8, width=100)
        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 清空日志按钮
        clear_log_button = ttk.Button(log_frame, text="清空日志", command=self.clear_log)
        clear_log_button.pack(side=tk.BOTTOM, pady=5)

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def add_log(self, message):
        """添加日志信息"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_message)
        self.log_text.see(tk.END)  # 自动滚动到底部
        self.root.update()

    def update_progress(self, value, message=""):
        """更新进度条"""
        self.progress_var.set(value)
        if message:
            self.add_log(message)
        self.root.update()

    def capture_print_output(self, func, *args, **kwargs):
        """捕获print输出并显示在日志框中"""
        # 创建StringIO对象来捕获输出
        output = io.StringIO()

        # 重定向print输出
        with contextlib.redirect_stdout(output):
            try:
                result = func(*args, **kwargs)
                # 获取捕获的输出
                captured_output = output.getvalue()
                if captured_output:
                    # 将输出添加到日志
                    self.root.after(0, lambda: self.add_log(captured_output.strip()))
                return result
            except Exception as e:
                # 获取捕获的输出
                captured_output = output.getvalue()
                if captured_output:
                    self.root.after(0, lambda: self.add_log(captured_output.strip()))
                raise e
            finally:
                output.close()

    def query_stock_data(self):
        """查询股票数据 - 调用数据采集器"""
        stock_code = self.stock_code_var.get().strip()
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码")
            return

        # 检查数据文件夹是否存在
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        # 检查数据库文件是否存在
        db_path = os.path.join(self.data_folder, f"{stock_code}_complete_data.db")
        data_exists = os.path.exists(db_path)

        # 清空日志
        self.clear_log()

        # 更新状态显示
        self.status_label.config(text="状态: 正在连接BaoStock...", foreground="orange")
        self.query_button.config(state="disabled")
        self.progress_var.set(0)
        self.root.update()

        # 在新线程中执行数据采集
        def collect_data_thread():
            try:
                # 更新进度
                self.root.after(0, lambda: self.update_progress(10, "正在连接BaoStock..."))

                # 登录BaoStock
                if not self.capture_print_output(self.data_collector.login_baostock):
                    self.root.after(0, lambda: self.status_label.config(text="状态: 连接失败", foreground="red"))
                    self.root.after(0, lambda: self.query_button.config(state="normal"))
                    self.root.after(0, lambda: self.update_progress(0, "连接失败"))
                    return

                self.root.after(0, lambda: self.update_progress(20, "连接成功，开始数据采集..."))

                # 采集或更新数据
                self.capture_print_output(self.data_collector.collect_complete_stock_data, stock_code, stock_code)

                # 更新状态
                if data_exists:
                    self.root.after(0, lambda: self.status_label.config(text="状态: 数据更新完成", foreground="green"))
                    self.root.after(0, lambda: self.update_progress(100, "数据更新完成"))
                    self.root.after(0, lambda: messagebox.showinfo("成功", f"股票 {stock_code} 数据更新完成"))
                else:
                    self.root.after(0, lambda: self.status_label.config(text="状态: 数据采集完成", foreground="green"))
                    self.root.after(0, lambda: self.update_progress(100, "数据采集完成"))
                    self.root.after(0, lambda: messagebox.showinfo("成功", f"股票 {stock_code} 数据采集完成"))

            except Exception as e:
                self.root.after(0, lambda: self.status_label.config(text=f"状态: 错误 - {str(e)}", foreground="red"))
                self.root.after(0, lambda: self.update_progress(0, f"错误: {str(e)}"))
                self.root.after(0, lambda: messagebox.showerror("错误", f"数据采集失败: {str(e)}"))
            finally:
                self.root.after(0, lambda: self.query_button.config(state="normal"))

        # 启动数据采集线程
        thread = threading.Thread(target=collect_data_thread)
        thread.daemon = True
        thread.start()

    def get_stock_data(self, stock_code, start_date, end_date, period='daily'):
        """获取股票数据"""
        db_path = os.path.join(self.data_folder, f"{stock_code}_complete_data.db")
        if not os.path.exists(db_path):
            return None

        # 周期映射
        period_mapping = {
            'daily': 'daily_data',
            'weekly': 'weekly_data',
            'monthly': 'monthly_data',
            'quarterly': 'quarterly_data',
            'yearly': 'yearly_data'
        }

        table_name = period_mapping.get(period, 'daily_data')

        try:
            conn = sqlite3.connect(db_path)
            query = f"""
            SELECT * FROM {table_name} 
            WHERE code = ? AND date BETWEEN ? AND ?
            ORDER BY date
            """

            df = pd.read_sql_query(query, conn, params=[stock_code, start_date, end_date])
            conn.close()

            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                return df
            else:
                return None

        except Exception as e:
            print(f"获取数据时出错: {e}")
            return None

    def analyze_kline_data(self):
        """分析K线数据"""
        stock_code = self.stock_code_var.get().strip()
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码")
            return

        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()

        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return

        # 获取数据
        df = self.get_stock_data(stock_code, start_date, end_date, 'daily')
        if df is None or df.empty:
            messagebox.showerror("错误", "未找到指定时间段的数据")
            return

        # 找到最高和最低收盘价
        max_close_idx = df['close'].idxmax()
        min_close_idx = df['close'].idxmin()
        max_close_row = df.loc[max_close_idx]
        min_close_row = df.loc[min_close_idx]

        # 格式化输出
        result_text = f"股票代码: {stock_code}\n"
        result_text += f"分析时间段: {start_date} 至 {end_date}\n"
        result_text += f"K线数量: {len(df)} 条\n\n"

        result_text += "=== 最高收盘价信息 ===\n"
        result_text += f"区间内最高收盘价：{max_close_row['close']:.2f}\n"
        result_text += f"日期: {max_close_row['date'].strftime('%Y-%m-%d')}\n"
        result_text += f"收盘价: {max_close_row['close']:.2f}\n"
        result_text += f"开盘价: {max_close_row['open']:.2f}\n"
        result_text += f"最高价: {max_close_row['high']:.2f}\n"
        result_text += f"最低价: {max_close_row['low']:.2f}\n"
        result_text += f"成交量: {int(max_close_row['volume'])}\n\n"

        result_text += "=== 最低收盘价信息 ===\n"
        result_text += f"区间内最低收盘价：{min_close_row['close']:.2f}\n"
        result_text += f"日期: {min_close_row['date'].strftime('%Y-%m-%d')}\n"
        result_text += f"收盘价: {min_close_row['close']:.2f}\n"
        result_text += f"开盘价: {min_close_row['open']:.2f}\n"
        result_text += f"最高价: {min_close_row['high']:.2f}\n"
        result_text += f"最低价: {min_close_row['low']:.2f}\n"
        result_text += f"成交量: {int(min_close_row['volume'])}\n\n"

        # 计算比例
        ratio = (max_close_row['close'] / min_close_row['close']) * 100
        result_text += "=== 价格比例分析 ===\n"
        result_text += f"最高收盘价与最低收盘价比例: {ratio:.2f}%\n"
        result_text += f"价格区间: {min_close_row['close']:.2f} - {max_close_row['close']:.2f}\n"
        result_text += f"价格差异: {max_close_row['close'] - min_close_row['close']:.2f}\n"

        # 显示结果
        self.kline_text.delete(1.0, tk.END)
        self.kline_text.insert(1.0, result_text)

        # 切换到K线分析页面
        self.notebook.select(0)  # 选择第一个页面（K线分析）

    def get_nearest_quarter(self, date):
        dt = pd.to_datetime(date)
        year = dt.year
        quarter = (dt.month - 1) // 3 + 1
        return f"{year}Q{quarter}"

    def get_circulating_share(self, stock_code, quarter):
        db_path = os.path.join(self.data_folder, f"{stock_code}_complete_data.db")
        if not os.path.exists(db_path):
            return 0
        try:
            conn = sqlite3.connect(db_path)
            query = "SELECT circulating_shares FROM quarterly_data WHERE code=? AND quarter<=? ORDER BY quarter DESC LIMIT 1"
            cur = conn.cursor()
            cur.execute(query, (stock_code, quarter))
            row = cur.fetchone()
            conn.close()
            return row[0] if row and row[0] else 0
        except Exception as e:
            print(f"获取流通股本时出错: {e}")
            return 0

    def analyze_volume_data(self):
        """分析成交量数据（多周期多选）"""
        stock_code = self.stock_code_var.get().strip()
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码")
            return
        start_date = self.start_date.get_date()
        end_date = self.end_date.get_date()
        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return
        # 周期多选
        period_list = []
        if self.daily_var.get(): period_list.append(('日线', 'daily'))
        if self.weekly_var.get(): period_list.append(('周线', 'weekly'))
        if self.monthly_var.get(): period_list.append(('月线', 'monthly'))
        if self.quarterly_var.get(): period_list.append(('季线', 'quarterly'))
        if self.yearly_var.get(): period_list.append(('年线', 'yearly'))
        if not period_list:
            messagebox.showerror("错误", "请至少选择一个周期")
            return
        result_text = f"股票代码: {stock_code}\n分析时间段: {start_date} 至 {end_date}\n"
        for period_name, period in period_list:
            df = self.get_stock_data(stock_code, start_date, end_date, period)
            if df is None or df.empty:
                result_text += f"{period_name}级别周期内无数据\n"
                continue
            total_volume = df['volume'].sum()
            # 获取区间起始日最近的季度流通股本
            start_date_str = str(start_date)
            quarter = self.get_nearest_quarter(start_date_str)
            circulating_share = self.get_circulating_share(stock_code, quarter)
            turnover = (total_volume / circulating_share) * 100 if circulating_share > 0 else 0
            result_text += f"{period_name}级别周期内成交量合计：{int(total_volume)}, 换手率为：{turnover:.2f}%\n"
        self.volume_text.delete(1.0, tk.END)
        self.volume_text.insert(1.0, result_text)

        # 切换到成交量分析页面
        self.notebook.select(1)  # 选择第二个页面（成交量分析）

    def calculate_values(self):
        """计算功能：a1分别乘以a2-a6，结果输出到b1-b5"""
        try:
            # 获取a1的值
            a1_str = self.a1_var.get().strip()
            if not a1_str:
                messagebox.showwarning("警告", "请输入a1的值")
                return

            try:
                a1 = float(a1_str)
            except ValueError:
                messagebox.showerror("错误", "a1必须是数字")
                return

            # 清空所有输出框
            self.b1_var.set("")
            self.b2_var.set("")
            self.b3_var.set("")
            self.b4_var.set("")
            self.b5_var.set("")

            # 获取a2-a6的值并计算
            a_values = [
                (self.a2_var.get().strip(), self.b1_var),
                (self.a3_var.get().strip(), self.b2_var),
                (self.a4_var.get().strip(), self.b3_var),
                (self.a5_var.get().strip(), self.b4_var),
                (self.a6_var.get().strip(), self.b5_var)
            ]

            # 逐个计算
            for a_str, b_var in a_values:
                if a_str:  # 如果输入框不为空
                    try:
                        a_val = float(a_str)
                        result = a1 * a_val
                        b_var.set(f"{result:.2f}")
                    except ValueError:
                        # 如果输入的不是数字，保持输出框为空
                        continue

            self.add_log("计算完成")

        except Exception as e:
            messagebox.showerror("错误", f"计算过程中出错: {str(e)}")

    def export_analysis_results(self):
        """导出分析结果为CSV格式"""
        try:
            from tkinter import filedialog
            import csv
            from datetime import datetime
            import os

            stock_code = self.stock_code_var.get().strip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # 检查是否有分析结果
            kline_text = self.kline_text.get(1.0, tk.END).strip()
            volume_text = self.volume_text.get(1.0, tk.END).strip()

            if not kline_text and not volume_text:
                messagebox.showwarning("警告", "没有可导出的分析结果，请先进行分析")
                return

            # 导出K线分析结果
            if kline_text:
                try:
                    # 让用户选择K线分析结果保存位置
                    kline_filename = filedialog.asksaveasfilename(
                        title="保存K线分析结果",
                        defaultextension=".csv",
                        filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
                    )

                    if kline_filename:
                        # 准备K线分析数据
                        kline_data = []
                        kline_data.append(["=== K线分析结果 ==="])
                        for line in kline_text.split('\n'):
                            if line.strip():
                                kline_data.append([line.strip()])
                        kline_data.append([])
                        kline_data.append([f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                        kline_data.append([f"股票代码: {stock_code}"])

                        # 写入K线分析CSV文件
                        with open(kline_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerows(kline_data)

                        messagebox.showinfo("导出成功", f"K线分析结果已导出到:\n{kline_filename}")
                        self.add_log(f"K线分析结果已导出到: {kline_filename}")

                except Exception as e:
                    messagebox.showerror("导出失败", f"导出K线分析结果时出错: {str(e)}")
                    self.add_log(f"导出K线分析结果失败: {str(e)}")

            # 导出成交量分析结果
            if volume_text:
                try:
                    # 让用户选择成交量分析结果保存位置
                    volume_filename = filedialog.asksaveasfilename(
                        title="保存成交量分析结果",
                        defaultextension=".csv",
                        filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
                    )

                    if volume_filename:
                        # 准备成交量分析数据
                        volume_data = []
                        volume_data.append(["=== 成交量分析结果 ==="])
                        for line in volume_text.split('\n'):
                            if line.strip():
                                volume_data.append([line.strip()])
                        volume_data.append([])
                        volume_data.append([f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"])
                        volume_data.append([f"股票代码: {stock_code}"])

                        # 写入成交量分析CSV文件
                        with open(volume_filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                            writer = csv.writer(csvfile)
                            writer.writerows(volume_data)

                        messagebox.showinfo("导出成功", f"成交量分析结果已导出到:\n{volume_filename}")
                        self.add_log(f"成交量分析结果已导出到: {volume_filename}")

                except Exception as e:
                    messagebox.showerror("导出失败", f"导出成交量分析结果时出错: {str(e)}")
                    self.add_log(f"导出成交量分析结果失败: {str(e)}")

        except Exception as e:
            messagebox.showerror("导出失败", f"导出过程中出错: {str(e)}")
            self.add_log(f"导出失败: {str(e)}")


def main():
    """主函数"""
    # 首先检查远程授权
    print("正在检查远程授权...")
    if not check_remote_authorization():
        print("授权验证失败，程序退出")
        sys.exit(1)

    print("授权验证成功，启动程序...")
    root = tk.Tk()
    app = StockAnalysisGUI(root)

    # 程序结束时登出BaoStock
    def on_closing():
        try:
            app.data_collector.logout_baostock()
        except:
            pass
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()