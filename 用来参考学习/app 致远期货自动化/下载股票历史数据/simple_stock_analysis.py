import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import pandas as pd
import datetime
import os
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates

class SimpleStockAnalysis:
    def __init__(self, root):
        self.root = root
        self.root.title("股票数据分析系统")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        # 数据文件夹路径
        self.data_folder = r'gupiao_baostock'
        
        # 创建界面
        self.create_widgets()
        
    def create_widgets(self):
        """创建界面组件"""
        # 主标题
        title_label = tk.Label(self.root, text="股票数据分析系统", 
                              font=("Arial", 16, "bold"), 
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
        ttk.Button(left_frame, text="查询", command=self.query_stock_data).grid(row=0, column=2, padx=5, pady=5)
        
        # 时间范围输入
        ttk.Label(left_frame, text="开始日期 (YYYY-MM-DD):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.start_date_var = tk.StringVar(value="2023-01-01")
        self.start_date_entry = ttk.Entry(left_frame, textvariable=self.start_date_var, width=15)
        self.start_date_entry.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        ttk.Label(left_frame, text="结束日期 (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.end_date_var = tk.StringVar(value="2023-12-31")
        self.end_date_entry = ttk.Entry(left_frame, textvariable=self.end_date_var, width=15)
        self.end_date_entry.grid(row=2, column=1, sticky=tk.W, pady=5)
        
        # 分析按钮
        ttk.Button(left_frame, text="分析K线数据", command=self.analyze_kline_data).grid(row=3, column=0, columnspan=3, pady=10)
        
        # 周期选择
        ttk.Label(left_frame, text="选择周期:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.period_var = tk.StringVar(value="daily")
        periods = [("日线", "daily"), ("周线", "weekly"), ("月线", "monthly"), 
                  ("季线", "quarterly"), ("年线", "yearly")]
        for i, (text, value) in enumerate(periods):
            ttk.Radiobutton(left_frame, text=text, variable=self.period_var, 
                           value=value).grid(row=4+i, column=1, sticky=tk.W, pady=2)
        
        ttk.Button(left_frame, text="分析成交量数据", command=self.analyze_volume_data).grid(row=9, column=0, columnspan=3, pady=10)
        
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
        
        # 图表页面
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="图表显示")
        
        # 创建结果显示区域
        self.create_result_widgets()
        
    def create_result_widgets(self):
        """创建结果显示组件"""
        # K线分析结果
        self.kline_text = tk.Text(self.kline_frame, height=20, width=50)
        kline_scrollbar = ttk.Scrollbar(self.kline_frame, orient=tk.VERTICAL, command=self.kline_text.yview)
        self.kline_text.configure(yscrollcommand=kline_scrollbar.set)
        self.kline_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        kline_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 成交量分析结果
        self.volume_text = tk.Text(self.volume_frame, height=20, width=50)
        volume_scrollbar = ttk.Scrollbar(self.volume_frame, orient=tk.VERTICAL, command=self.volume_text.yview)
        self.volume_text.configure(yscrollcommand=volume_scrollbar.set)
        self.volume_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        volume_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 图表显示区域
        self.chart_canvas = None
        
    def query_stock_data(self):
        """查询股票数据"""
        stock_code = self.stock_code_var.get().strip()
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码")
            return
        
        # 检查数据库文件是否存在
        db_path = os.path.join(self.data_folder, f"{stock_code}_data.db")
        if not os.path.exists(db_path):
            messagebox.showerror("错误", f"未找到股票 {stock_code} 的数据库文件")
            return
        
        messagebox.showinfo("成功", f"股票 {stock_code} 数据加载成功")
        
    def get_stock_data(self, stock_code, start_date, end_date, period='daily'):
        """获取股票数据"""
        db_path = os.path.join(self.data_folder, f"{stock_code}_data.db")
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
            WHERE code = ? AND time BETWEEN ? AND ?
            ORDER BY time
            """
            
            df = pd.read_sql_query(query, conn, params=[stock_code, start_date, end_date])
            conn.close()
            
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
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
        
        try:
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
        except ValueError:
            messagebox.showerror("错误", "日期格式错误，请使用YYYY-MM-DD格式")
            return
        
        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return
        
        # 获取数据
        df = self.get_stock_data(stock_code, start_date, end_date, 'daily')
        if df is None or df.empty:
            messagebox.showerror("错误", "未找到指定时间段的数据")
            return
        
        # 分析数据
        result_text = f"股票代码: {stock_code}\n"
        result_text += f"分析时间段: {start_date} 至 {end_date}\n"
        result_text += f"K线数量: {len(df)} 条\n\n"
        
        # 找到最高和最低收盘价
        max_close_idx = df['close'].idxmax()
        min_close_idx = df['close'].idxmin()
        
        max_close_row = df.loc[max_close_idx]
        min_close_row = df.loc[min_close_idx]
        
        result_text += "=== 最高收盘价信息 ===\n"
        result_text += f"日期: {max_close_row['time'].strftime('%Y-%m-%d')}\n"
        result_text += f"收盘价: {max_close_row['close']:.2f}\n"
        result_text += f"开盘价: {max_close_row['open']:.2f}\n"
        result_text += f"最高价: {max_close_row['high']:.2f}\n"
        result_text += f"最低价: {max_close_row['low']:.2f}\n"
        result_text += f"成交量: {max_close_row['vol']:.0f}\n\n"
        
        result_text += "=== 最低收盘价信息 ===\n"
        result_text += f"日期: {min_close_row['time'].strftime('%Y-%m-%d')}\n"
        result_text += f"收盘价: {min_close_row['close']:.2f}\n"
        result_text += f"开盘价: {min_close_row['open']:.2f}\n"
        result_text += f"最高价: {min_close_row['high']:.2f}\n"
        result_text += f"最低价: {min_close_row['low']:.2f}\n"
        result_text += f"成交量: {min_close_row['vol']:.0f}\n\n"
        
        # 计算比例
        ratio = (max_close_row['close'] / min_close_row['close']) * 100
        result_text += f"=== 价格比例分析 ===\n"
        result_text += f"最高收盘价与最低收盘价比例: {ratio:.2f}%\n"
        result_text += f"价格区间: {min_close_row['close']:.2f} - {max_close_row['close']:.2f}\n"
        result_text += f"价格差异: {max_close_row['close'] - min_close_row['close']:.2f}\n"
        
        # 显示结果
        self.kline_text.delete(1.0, tk.END)
        self.kline_text.insert(1.0, result_text)
        
        # 绘制图表
        self.plot_kline_chart(df, stock_code)
        
    def analyze_volume_data(self):
        """分析成交量数据"""
        stock_code = self.stock_code_var.get().strip()
        if not stock_code:
            messagebox.showerror("错误", "请输入股票代码")
            return
        
        try:
            start_date = self.start_date_var.get()
            end_date = self.end_date_var.get()
            
            # 验证日期格式
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
        except ValueError:
            messagebox.showerror("错误", "日期格式错误，请使用YYYY-MM-DD格式")
            return
        
        if start_date > end_date:
            messagebox.showerror("错误", "开始日期不能晚于结束日期")
            return
        
        period = self.period_var.get()
        
        # 获取数据
        df = self.get_stock_data(stock_code, start_date, end_date, period)
        if df is None or df.empty:
            messagebox.showerror("错误", "未找到指定时间段的数据")
            return
        
        # 分析数据
        result_text = f"股票代码: {stock_code}\n"
        result_text += f"分析时间段: {start_date} 至 {end_date}\n"
        result_text += f"分析周期: {period}\n"
        result_text += f"数据条数: {len(df)} 条\n\n"
        
        # 成交量统计
        result_text += "=== 成交量统计 ===\n"
        result_text += f"总成交量: {df['vol'].sum():.0f}\n"
        result_text += f"平均成交量: {df['vol'].mean():.0f}\n"
        result_text += f"最大成交量: {df['vol'].max():.0f}\n"
        result_text += f"最小成交量: {df['vol'].min():.0f}\n"
        result_text += f"成交量标准差: {df['vol'].std():.0f}\n\n"
        
        # 成交量分布
        result_text += "=== 成交量分布 ===\n"
        volume_quartiles = df['vol'].quantile([0.25, 0.5, 0.75])
        result_text += f"25%分位数: {volume_quartiles[0.25]:.0f}\n"
        result_text += f"中位数: {volume_quartiles[0.5]:.0f}\n"
        result_text += f"75%分位数: {volume_quartiles[0.75]:.0f}\n\n"
        
        # 高成交量日期
        high_volume_threshold = df['vol'].quantile(0.9)
        high_volume_days = df[df['vol'] >= high_volume_threshold]
        result_text += f"=== 高成交量日期 (前10%) ===\n"
        for _, row in high_volume_days.head(10).iterrows():
            result_text += f"{row['time'].strftime('%Y-%m-%d')}: {row['vol']:.0f}\n"
        
        # 显示结果
        self.volume_text.delete(1.0, tk.END)
        self.volume_text.insert(1.0, result_text)
        
        # 绘制成交量图表
        self.plot_volume_chart(df, stock_code, period)
        
    def plot_kline_chart(self, df, stock_code):
        """绘制K线图表"""
        # 清除旧图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        
        # 价格图表
        ax1.plot(df['time'], df['close'], label='收盘价', linewidth=2)
        ax1.plot(df['time'], df['high'], label='最高价', alpha=0.7)
        ax1.plot(df['time'], df['low'], label='最低价', alpha=0.7)
        ax1.set_title(f'{stock_code} 价格走势图')
        ax1.set_ylabel('价格')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 成交量图表
        ax2.bar(df['time'], df['vol'], alpha=0.7, color='blue')
        ax2.set_title('成交量')
        ax2.set_ylabel('成交量')
        ax2.grid(True, alpha=0.3)
        
        # 格式化x轴
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 显示图表
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
    def plot_volume_chart(self, df, stock_code, period):
        """绘制成交量图表"""
        # 清除旧图表
        for widget in self.chart_frame.winfo_children():
            widget.destroy()
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 6))
        
        # 成交量柱状图
        ax1.bar(df['time'], df['vol'], alpha=0.7, color='green')
        ax1.set_title(f'{stock_code} 成交量分析 ({period})')
        ax1.set_ylabel('成交量')
        ax1.grid(True, alpha=0.3)
        
        # 成交量移动平均
        if len(df) > 5:
            ma5 = df['vol'].rolling(window=5).mean()
            ma10 = df['vol'].rolling(window=10).mean()
            ax2.plot(df['time'], ma5, label='5期移动平均', linewidth=2)
            ax2.plot(df['time'], ma10, label='10期移动平均', linewidth=2)
            ax2.set_title('成交量移动平均')
            ax2.set_ylabel('成交量')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # 格式化x轴
        for ax in [ax1, ax2]:
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            ax.xaxis.set_major_locator(mdates.MonthLocator())
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        # 显示图表
        canvas = FigureCanvasTkAgg(fig, self.chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    """主函数"""
    root = tk.Tk()
    app = SimpleStockAnalysis(root)
    root.mainloop()

if __name__ == "__main__":
    main() 