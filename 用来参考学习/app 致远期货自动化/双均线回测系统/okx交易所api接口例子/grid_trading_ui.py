#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格交易策略UI界面
支持做多网格交易策略
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
from datetime import datetime
import json
import queue
import sys
import sqlite3
from io import StringIO

from okx_client_v2 import OKXClientV2 as OKXClient
from grid_trading_strategy import DynamicGridTradingStrategy
from config import Config

class RealTimeLogger:
    """实时日志记录器，用于捕获后台打印信息"""
    
    def __init__(self, max_lines=100):
        self.max_lines = max_lines
        self.log_queue = queue.Queue()
        self.log_lines = []
        self.callback = None
        
        # 重定向stdout和stderr
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        self.stdout_capture = StringIO()
        self.stderr_capture = StringIO()
        
        # 设置重定向
        sys.stdout = self.stdout_capture
        sys.stderr = self.stderr_capture
        
        # 启动监控线程
        self.monitor_thread = threading.Thread(target=self._monitor_output, daemon=True)
        self.monitor_thread.start()
    
    def set_callback(self, callback):
        """设置日志回调函数"""
        self.callback = callback
    
    def _monitor_output(self):
        """监控输出流"""
        while True:
            try:
                # 检查stdout
                stdout_content = self.stdout_capture.getvalue()
                if stdout_content:
                    self.stdout_capture.truncate(0)
                    self.stdout_capture.seek(0)
                    for line in stdout_content.split('\n'):
                        if line.strip():
                            self._add_log_line(f"[STDOUT] {line}")
                
                # 检查stderr
                stderr_content = self.stderr_capture.getvalue()
                if stderr_content:
                    self.stderr_capture.truncate(0)
                    self.stderr_capture.seek(0)
                    for line in stderr_content.split('\n'):
                        if line.strip():
                            self._add_log_line(f"[STDERR] {line}")
                
                time.sleep(0.1)  # 每100ms检查一次
                
            except Exception as e:
                # 如果出错，恢复原始输出
                sys.stdout = self.original_stdout
                sys.stderr = self.original_stderr
                print(f"日志监控异常: {e}")
                break
    
    def _add_log_line(self, line):
        """添加日志行"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {line}"
        
        self.log_lines.append(log_entry)
        
        # 保持最大行数限制
        if len(self.log_lines) > self.max_lines:
            self.log_lines.pop(0)
        
        # 通知UI更新
        if self.callback:
            self.callback(log_entry)
    
    def get_all_logs(self):
        """获取所有日志"""
        return self.log_lines.copy()
    
    def clear_logs(self):
        """清除日志"""
        self.log_lines.clear()
    
    def restore_output(self):
        """恢复原始输出"""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr

class GridTradingUI:
    """网格交易策略UI类"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("网格交易策略 - 做多策略")
        self.root.geometry("1400x1000")  # 增加窗口大小以容纳实时日志窗口
        
        # 初始化客户端
        self.client = OKXClient()
        
        # 初始化数据库管理器
        try:
            from grid_trading_database import GridTradingDatabase
            self.db_manager = GridTradingDatabase()
        except Exception as e:
            print(f"数据库初始化失败: {e}")
            self.db_manager = None
        
        # 策略相关
        self.grid_strategy = None
        self.update_thread = None
        
        # 初始化合约列表
        self.all_instruments = []
        
        # 初始化UI
        self.setup_ui()
        
        # 初始化状态变量（即使不显示UI也需要）
        self.status_var = tk.StringVar(value="策略未启动")
        self.current_price_var = tk.StringVar(value="当前价格: $0.00000000")
        self.base_price_status_var = tk.StringVar(value="基准价格: $0.00000000")
        self.grid_position_var = tk.StringVar(value="当前网格: 未确定")
        self.next_order_var = tk.StringVar(value="下一个挂单: 无")
        self.position_var = tk.StringVar(value="持仓: 0张")
        self.profit_var = tk.StringVar(value="总盈利: 0.0000 USDT")
        self.active_orders_var = tk.StringVar(value="活跃订单: 0个")
        self.grid_count_var = tk.StringVar(value="网格数量: 0")
        
        # 加载合约列表
        self.load_instruments()
        
        # 初始化实时日志记录器（在UI设置完成后）
        try:
            self.real_time_logger = RealTimeLogger(max_lines=100)
            self.real_time_logger.set_callback(self._on_real_time_log)
        except Exception as e:
            print(f"实时日志记录器初始化失败: {e}")
            self.real_time_logger = None
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

        # 全局异常钩子：记录异常（不退出进程）；容错计数达到阈值再自动重启
        try:
            # 连续失败计数与时间窗
            self._strategy_failure_count = 0
            self._last_failure_ts = 0
            self._failure_threshold = 10  # 连续10次异常才触发重启
            self._failure_window_seconds = 60  # 超过60秒无异常则计数清零

            def _sys_ex_hook(exc_type, exc_value, exc_traceback):
                try:
                    self._handle_strategy_exception('sys', exc_type, exc_value)
                except Exception:
                    pass
            import sys as _sys
            _sys.excepthook = _sys_ex_hook

            import threading as _threading
            def _thread_hook(args):
                try:
                    # 只有策略线程异常才计数
                    if hasattr(self, 'strategy_thread') and args.thread is getattr(self, 'strategy_thread', None):
                        self._handle_strategy_exception('thread', args.exc_type, args.exc_value)
                except Exception:
                    pass
            _threading.excepthook = _thread_hook
        except Exception:
            pass
    
    def _on_closing(self):
        """阻止右上角直接关闭。引导使用“关闭程序”按钮。"""
        try:
            messagebox.showinfo("提示", "请使用控制区的【关闭程序】按钮退出。程序将继续运行。")
        except Exception:
            pass
        return

    def close_program(self):
        """真正的关闭程序入口：先停策略，再退出UI。"""
        try:
            if not messagebox.askyesno("确认退出", "确定要停止策略并关闭程序吗？"):
                return
            # 恢复原始输出
            if hasattr(self, 'real_time_logger') and self.real_time_logger:
                try:
                    self.real_time_logger.restore_output()
                except Exception:
                    pass
            # 停止策略
            if hasattr(self, 'grid_strategy') and self.grid_strategy:
                try:
                    self.grid_strategy.stop()
                except Exception:
                    pass
            self.root.destroy()
        except Exception as e:
            print(f"关闭程序失败: {e}")
    
    def _on_real_time_log(self, log_entry):
        """实时日志回调函数"""
        try:
            # 在主线程中更新UI
            self.root.after(0, self._update_real_time_log, log_entry)
        except Exception as e:
            print(f"更新实时日志失败: {e}")
    
    def _update_real_time_log(self, log_entry):
        """更新实时日志显示"""
        try:
            if hasattr(self, 'real_time_log_text') and self.real_time_log_text:
                self.real_time_log_text.insert(tk.END, log_entry + "\n")
                self.real_time_log_text.see(tk.END)
                
                # 保持最大行数限制
                lines = self.real_time_log_text.get("1.0", tk.END).split('\n')
                if len(lines) > 100:
                    # 删除多余的行
                    excess_lines = len(lines) - 100
                    self.real_time_log_text.delete("1.0", f"{excess_lines + 1}.0")
        except Exception as e:
            print(f"更新实时日志显示失败: {e}")
    
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.columnconfigure(2, weight=1)  # 为右侧日志区域添加权重
        
        # 标题
        title_label = ttk.Label(main_frame, text="网格交易策略 - 做多策略", font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 左侧内容区域
        left_frame = ttk.Frame(main_frame)
        left_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 参数设置区域
        self.setup_parameters_frame(left_frame)
        
        # 策略控制区域
        self.setup_control_frame(left_frame)
        
        # 持仓显示区域
        self.setup_positions_frame(left_frame)
        
        # 日志显示区域
        self.setup_log_frame(left_frame)
        
        # 右侧实时日志显示区域
        self.setup_real_time_log_frame(main_frame)
    
    def setup_parameters_frame(self, parent):
        """设置参数输入区域"""
        param_frame = ttk.LabelFrame(parent, text="策略参数设置", padding="10")
        param_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 合约搜索区域
        search_frame = ttk.Frame(param_frame)
        search_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 5))
        
        # 搜索输入框
        ttk.Label(search_frame, text="搜索合约:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=15)
        self.search_entry.grid(row=0, column=1, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 搜索按钮
        search_button = ttk.Button(search_frame, text="搜索", command=self.search_instruments, width=6)
        search_button.grid(row=0, column=2, padx=(5, 0), pady=5)
        
        # 清除搜索按钮
        clear_button = ttk.Button(search_frame, text="清除", command=self.clear_search, width=6)
        clear_button.grid(row=0, column=3, padx=(5, 0), pady=5)
        
        # 品种选择
        ttk.Label(param_frame, text="交易品种:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.instrument_var = tk.StringVar()
        self.instrument_combo = ttk.Combobox(param_frame, textvariable=self.instrument_var, width=30)
        self.instrument_combo.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        
        # 刷新按钮
        refresh_button = ttk.Button(param_frame, text="刷新", command=self.refresh_instrument_info, width=8)
        refresh_button.grid(row=1, column=2, padx=(5, 0), pady=5)
        
        # 绑定选择事件
        self.instrument_combo.bind('<<ComboboxSelected>>', self.on_instrument_selected)
        
        # 合约信息显示
        self.contract_info_var = tk.StringVar(value="请选择合约")
        contract_info_label = ttk.Label(param_frame, textvariable=self.contract_info_var, 
                                      font=("Arial", 9), foreground="blue")
        contract_info_label.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        # 基准价格
        ttk.Label(param_frame, text="基准价格:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.base_price_var = tk.StringVar()
        self.base_price_entry = ttk.Entry(param_frame, textvariable=self.base_price_var, width=20)
        self.base_price_entry.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 网格宽度
        ttk.Label(param_frame, text="网格宽度:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.grid_width_var = tk.StringVar()
        self.grid_width_entry = ttk.Entry(param_frame, textvariable=self.grid_width_var, width=20)
        self.grid_width_entry.grid(row=4, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 交易方式
        ttk.Label(param_frame, text="交易方式:").grid(row=5, column=0, sticky=tk.W, pady=5)
        self.trade_mode_var = tk.StringVar(value="quantity")
        trade_mode_frame = ttk.Frame(param_frame)
        trade_mode_frame.grid(row=5, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Radiobutton(trade_mode_frame, text="同等数量", variable=self.trade_mode_var, 
                       value="quantity").pack(side=tk.LEFT)
        ttk.Radiobutton(trade_mode_frame, text="同等金额", variable=self.trade_mode_var, 
                       value="amount").pack(side=tk.LEFT, padx=(10, 0))
        
        # 交易数量/金额
        ttk.Label(param_frame, text="交易数量/金额:").grid(row=6, column=0, sticky=tk.W, pady=5)
        self.trade_value_var = tk.StringVar()
        self.trade_value_entry = ttk.Entry(param_frame, textvariable=self.trade_value_var, width=20)
        self.trade_value_entry.grid(row=6, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 建立底仓按钮
        self.build_position_button = ttk.Button(param_frame, text="建立底仓", 
                                               command=self.build_base_position, width=10)
        self.build_position_button.grid(row=6, column=2, padx=(5, 0), pady=5)
        
        # 向下网格数量
        ttk.Label(param_frame, text="向下网格数量:").grid(row=7, column=0, sticky=tk.W, pady=5)
        self.down_grids_var = tk.StringVar(value="20")
        self.down_grids_entry = ttk.Entry(param_frame, textvariable=self.down_grids_var, width=20)
        self.down_grids_entry.grid(row=7, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 向上网格数量
        ttk.Label(param_frame, text="向上网格数量:").grid(row=8, column=0, sticky=tk.W, pady=5)
        self.up_grids_var = tk.StringVar(value="1")
        self.up_grids_entry = ttk.Entry(param_frame, textvariable=self.up_grids_var, width=20)
        self.up_grids_entry.grid(row=8, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # 配置列权重
        param_frame.columnconfigure(1, weight=1)
        search_frame.columnconfigure(1, weight=1)
    
    def setup_control_frame(self, parent):
        """设置控制按钮区域"""
        control_frame = ttk.LabelFrame(parent, text="策略控制", padding="10")
        control_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 启动策略按钮
        self.start_button = ttk.Button(control_frame, text="启动策略", 
                                      command=self.start_strategy)
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # 暂停策略按钮
        self.pause_button = ttk.Button(control_frame, text="暂停策略", 
                                      command=self.pause_strategy, state="disabled")
        self.pause_button.grid(row=0, column=1, padx=(0, 10))
        
        # 重置策略按钮
        self.reset_button = ttk.Button(control_frame, text="重置策略", 
                                      command=self.reset_strategy)
        self.reset_button.grid(row=0, column=2, padx=(0, 10))
        
        # 查看统计按钮
        self.stats_button = ttk.Button(control_frame, text="查看统计", 
                                      command=self.show_statistics)
        self.stats_button.grid(row=0, column=3, padx=(0, 10))
        
        # 查看挂单按钮
        self.orders_button = ttk.Button(control_frame, text="查看挂单", 
                                      command=self.show_grid_orders)
        self.orders_button.grid(row=0, column=4, padx=(0, 10))
        
        # 查询持仓按钮
        self.positions_button = ttk.Button(control_frame, text="查询持仓", 
                                         command=self.refresh_positions_display)
        self.positions_button.grid(row=0, column=5)

        # 关闭程序按钮（唯一允许真正退出的入口）
        self.exit_button = ttk.Button(control_frame, text="关闭程序", command=self.close_program)
        self.exit_button.grid(row=0, column=6, padx=(10, 0))
        
        # 策略健康状态显示
        self.health_status_var = tk.StringVar(value="策略状态: 未启动")
        health_status_label = ttk.Label(control_frame, textvariable=self.health_status_var, 
                                      font=("Arial", 9), foreground="blue")
        health_status_label.grid(row=0, column=6, padx=(10, 0))
        
        # 强制恢复策略按钮
        self.force_resume_button = ttk.Button(control_frame, text="强制恢复", 
                                            command=self.force_resume_strategy, state="disabled")
        self.force_resume_button.grid(row=0, column=7, padx=(5, 0))

        # 新增：手动确认中心价按钮（当需要人工选择 DB/交易所 最近成交价时）
        self.confirm_center_price_button = ttk.Button(control_frame, text="确认中心价", 
                                                      command=self.confirm_center_price_dialog, state="disabled")
        self.confirm_center_price_button.grid(row=0, column=8, padx=(5, 0))
    
    def setup_status_frame(self, parent):
        """设置状态显示区域"""
        status_frame = ttk.LabelFrame(parent, text="策略状态", padding="10")
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 策略运行状态
        self.status_var = tk.StringVar(value="策略未启动")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, font=("Arial", 10, "bold"))
        status_label.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 当前价格
        self.current_price_var = tk.StringVar(value="当前价格: $0.00000000")
        current_price_label = ttk.Label(status_frame, textvariable=self.current_price_var)
        current_price_label.grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 基准价格
        self.base_price_status_var = tk.StringVar(value="基准价格: $0.00000000")
        base_price_label = ttk.Label(status_frame, textvariable=self.base_price_status_var)
        base_price_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        # 当前网格位置
        self.grid_position_var = tk.StringVar(value="当前网格: 未确定")
        grid_position_label = ttk.Label(status_frame, textvariable=self.grid_position_var)
        grid_position_label.grid(row=2, column=0, sticky=tk.W, pady=2)
        
        # 下一个挂单价格
        self.next_order_var = tk.StringVar(value="下一个挂单: 无")
        next_order_label = ttk.Label(status_frame, textvariable=self.next_order_var)
        next_order_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        # 持仓信息
        self.position_var = tk.StringVar(value="持仓: 0张")
        position_label = ttk.Label(status_frame, textvariable=self.position_var)
        position_label.grid(row=3, column=0, sticky=tk.W, pady=2)
        
        # 总盈利
        self.profit_var = tk.StringVar(value="总盈利: 0.0000 USDT")
        profit_label = ttk.Label(status_frame, textvariable=self.profit_var)
        profit_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # 活跃订单数
        self.active_orders_var = tk.StringVar(value="活跃订单: 0个")
        active_orders_label = ttk.Label(status_frame, textvariable=self.active_orders_var)
        active_orders_label.grid(row=4, column=0, sticky=tk.W, pady=2)
        
        # 网格数量
        self.grid_count_var = tk.StringVar(value="网格数量: 0")
        grid_count_label = ttk.Label(status_frame, textvariable=self.grid_count_var)
        grid_count_label.grid(row=4, column=1, sticky=tk.W, pady=2)
    
    def setup_log_frame(self, parent):
        """设置日志显示区域"""
        log_frame = ttk.LabelFrame(parent, text="运行日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=10, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置权重
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(4, weight=1)  # 调整行权重
    
    def setup_real_time_log_frame(self, parent):
        """设置右侧实时日志显示区域"""
        real_time_log_frame = ttk.LabelFrame(parent, text="实时后台日志", padding="10")
        real_time_log_frame.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        # 实时日志文本框 - 做成从上到下的长条
        self.real_time_log_text = scrolledtext.ScrolledText(real_time_log_frame, 
                                                           font=("Consolas", 9), 
                                                           bg="black", fg="white",
                                                           width=60)  # 设置固定宽度
        self.real_time_log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 控制按钮框架
        control_frame = ttk.Frame(real_time_log_frame)
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 清除日志按钮
        clear_button = ttk.Button(control_frame, text="清除日志", command=self.clear_real_time_logs)
        clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 保存日志按钮
        save_button = ttk.Button(control_frame, text="保存日志", command=self.save_real_time_logs)
        save_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 日志状态标签
        self.log_status_var = tk.StringVar(value="实时日志监控已启动")
        status_label = ttk.Label(control_frame, textvariable=self.log_status_var, font=("Arial", 9))
        status_label.pack(side=tk.RIGHT)
        
        # 配置权重 - 让日志区域占满整个右侧
        real_time_log_frame.columnconfigure(0, weight=1)
        real_time_log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)  # 让右侧日志区域占满整个高度
    
    def setup_positions_frame(self, parent):
        """设置持仓显示区域"""
        positions_frame = ttk.LabelFrame(parent, text="当前持仓", padding="10")
        positions_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 持仓表格
        columns = ("合约", "持仓方向", "持仓数量", "开仓均价", "最新价格", "未实现盈亏", "保证金")
        self.positions_tree = ttk.Treeview(positions_frame, columns=columns, show="headings", height=4)
        
        # 设置列标题和宽度
        column_widths = {
            "合约": 120,
            "持仓方向": 80,
            "持仓数量": 100,
            "开仓均价": 120,
            "最新价格": 120,
            "未实现盈亏": 120,
            "保证金": 100
        }
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=column_widths[col])
        
        # 添加滚动条
        positions_scrollbar = ttk.Scrollbar(positions_frame, orient=tk.VERTICAL, command=self.positions_tree.yview)
        self.positions_tree.configure(yscrollcommand=positions_scrollbar.set)
        
        # 布局
        self.positions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        positions_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 配置权重
        positions_frame.columnconfigure(0, weight=1)
        positions_frame.rowconfigure(0, weight=1)
    
    def load_instruments(self):
        """加载可交易合约列表"""
        try:
            self.log("正在加载可交易合约列表...")
            instruments = self.client.get_instruments("SWAP")
            
            if instruments:
                instrument_list = [inst['instId'] for inst in instruments]
                self.instrument_combo['values'] = instrument_list
                if instrument_list:
                    self.instrument_combo.set(instrument_list[0])
                self.all_instruments = instruments # 缓存所有合约
                self.log(f"加载完成，共 {len(instrument_list)} 个合约")
            else:
                self.log("❌ 无法获取合约列表")
                
        except Exception as e:
            self.log(f"❌ 加载合约列表失败: {e}")
    
    def log(self, message):
        """添加日志信息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"[{timestamp}] {message}\n"
        
        # 检查是否有日志文本框
        if hasattr(self, 'log_text') and self.log_text:
            self.log_text.insert(tk.END, log_message)
            self.log_text.see(tk.END)
            self.root.update_idletasks()
        else:
            # 如果没有日志文本框，直接打印到控制台
            print(log_message.strip())
    
    def validate_parameters(self):
        """验证策略参数"""
        try:
            # 检查品种
            if not self.instrument_var.get():
                messagebox.showerror("错误", "请选择交易品种")
                return False
            
            # 检查基准价格
            base_price = float(self.base_price_var.get())
            if base_price <= 0:
                messagebox.showerror("错误", "基准价格必须大于0")
                return False
            
            # 检查网格宽度
            grid_width = float(self.grid_width_var.get())
            if grid_width <= 0:
                messagebox.showerror("错误", "网格宽度必须大于0")
                return False
            
            # 检查交易数量/金额
            trade_value = float(self.trade_value_var.get())
            if trade_value <= 0:
                messagebox.showerror("错误", "交易数量/金额必须大于0")
                return False
            
            return True
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数值")
            return False
    
    def check_position(self):
        """检查是否有持仓 - 只检查long方向的持仓"""
        try:
            positions = self.client.get_positions()
            if positions:
                for position in positions:
                    if (position.get('instId') == self.instrument_var.get() and 
                        position.get('posSide') == 'long' and  # 只检查long方向
                        float(position.get('pos', '0')) > 0):
                        return True
            
            return False
            
        except Exception as e:
            self.log(f"❌ 检查持仓失败: {e}")
            return False
    
    def start_strategy(self):
        """启动策略"""
        try:
            # 检查是否已有策略实例且处于暂停状态
            if hasattr(self, 'grid_strategy') and self.grid_strategy and not self.grid_strategy.is_running:
                # 重新启动现有策略
                self.log("🔄 重新启动现有策略")
                
                # 启动策略线程 - 先调用start()初始化，然后调用run()进入循环
                self.strategy_thread = threading.Thread(target=self._run_strategy_with_start)
                self.strategy_thread.daemon = True
                self.strategy_thread.start()
                
                # 启动UI更新线程
                self.update_thread = threading.Thread(target=self.update_status)
                self.update_thread.daemon = True
                self.update_thread.start()
                
                self.log("🚀 策略重新启动成功")
                
                self.start_button.config(state='disabled')
                self.pause_button.config(state='normal')
                return
            
            # 检查数据库中是否有现有策略
            existing_strategy = None
            if self.db_manager:
                try:
                    # 获取所有策略状态
                    all_strategies = self.db_manager.get_all_strategy_status()
                    if all_strategies:
                        # 找到第一个做多策略
                        for strategy_id, strategy_data in all_strategies.items():
                            if strategy_data.get('strategy_type', 'long') == 'long':  # 做多策略
                                existing_strategy = {
                                    'strategy_id': strategy_id,
                                    'data': strategy_data
                                }
                                break
                    
                    if existing_strategy:
                        # 发现现有策略，询问用户是否继续使用
                        strategy_data = existing_strategy['data']
                        existing_instrument = strategy_data.get('instrument', 'N/A')
                        
                        strategy_info = f"""发现现有策略：

• 策略ID: {existing_strategy['strategy_id']}
• 交易对: {existing_instrument}
• 基准价格: ${strategy_data.get('base_price', 0):.2f}
• 网格宽度: ${strategy_data.get('grid_width', 0):.2f}
• 交易数量: {strategy_data.get('trade_size', 0)}张

是否继续使用此策略？
• 点击【确定】继续使用此策略
• 点击【取消】退出启动"""

                        # 弹出确认对话框
                        if not messagebox.askokcancel("发现现有策略", strategy_info):
                            self.log("❌ 用户取消启动策略")
                            return
                            
                        self.log(f"📋 用户确认使用现有策略: {existing_strategy['strategy_id']}")
                        self.log(f"📊 策略信息:")
                        self.log(f"  合约: {existing_instrument}")
                        self.log(f"  基准价格: ${strategy_data.get('base_price', 0):.8f}")
                        self.log(f"  网格宽度: ${strategy_data.get('grid_width', 0):.8f}")
                        self.log(f"  交易数量: {strategy_data.get('trade_size', 0)}张")
                        self.log(f"  当前持仓: {strategy_data.get('current_position', 0)}张")
                        self.log(f"  总盈利: ${strategy_data.get('total_profit', 0):.4f} USDT")
                        
                        messagebox.showinfo("启动现有策略", strategy_info)
                        
                        # 使用现有策略的参数
                        instrument = existing_instrument
                        base_price = strategy_data.get('base_price', 0)
                        grid_width = strategy_data.get('grid_width', 0)
                        trade_size = strategy_data.get('trade_size', 0)
                        down_grids = strategy_data.get('down_grids', 20)
                        up_grids = strategy_data.get('up_grids', 1)
                        strategy_id = existing_strategy['strategy_id']
                        
                        # 更新UI显示现有策略的参数
                        self.base_price_var.set(f"{base_price:.8f}")
                        self.grid_width_var.set(f"{grid_width:.8f}")
                        self.trade_value_var.set(f"{trade_size}")
                        self.down_grids_var.set(f"{down_grids}")
                        self.up_grids_var.set(f"{up_grids}")
                        
                        # 记录恢复的交易数量
                        self.log(f"📋 恢复交易数量: {trade_size}张")
                        
                    else:
                        # 没有现有策略，提示新建
                        self.log("📋 数据表中没有现有策略，提示新建")
                        
                        # 检查UI参数是否填写完整
                        instrument = self.instrument_var.get()
                        base_price_str = self.base_price_var.get()
                        grid_width_str = self.grid_width_var.get()
                        trade_size_str = self.trade_value_var.get()
                        
                        # 检查参数完整性
                        missing_params = []
                        if not instrument:
                            missing_params.append("交易品种")
                        if not base_price_str:
                            missing_params.append("基准价格")
                        if not grid_width_str:
                            missing_params.append("网格宽度")
                        if not trade_size_str:
                            missing_params.append("交易数量")
                        
                        if missing_params:
                            # 参数不完整，提示用户填写
                            missing_text = "、".join(missing_params)
                            messagebox.showwarning("参数不完整", f"请先填写以下参数：\n{missing_text}")
                            return
                        
                        # 验证参数有效性
                        try:
                            base_price = float(base_price_str)
                            grid_width = float(grid_width_str)
                            trade_size = float(trade_size_str)
                            down_grids = int(self.down_grids_var.get())
                            up_grids = int(self.up_grids_var.get())
                            
                            if base_price <= 0 or grid_width <= 0 or trade_size <= 0:
                                messagebox.showerror("参数错误", "基准价格、网格宽度、交易数量必须大于0")
                                return
                                
                        except ValueError:
                            messagebox.showerror("参数错误", "请确保所有参数都是有效的数值")
                            return
                        
                        # 参数完整且有效，创建新策略
                        self.log("✅ 参数检查通过，创建新策略")
                        strategy_id = f"grid_strategy_{instrument}"
                            
                except Exception as e:
                    self.log(f"❌ 检查策略状态失败: {e}")
                    messagebox.showerror("错误", f"检查策略状态失败: {e}")
                    return
            else:
                # 没有数据库管理器
                messagebox.showerror("错误", "数据库管理器未初始化")
                return
            
            # 创建策略实例
            self.grid_strategy = DynamicGridTradingStrategy(
                client=self.client,
                instrument=instrument,
                base_price=base_price,
                grid_width=grid_width,
                trade_size=trade_size,
                down_grids=down_grids,
                up_grids=up_grids,
                db_manager=self.db_manager,
                strategy_id=strategy_id
            )
            
            # 设置策略的UI日志回调函数
            self.grid_strategy.ui_log_callback = self.log
            
            # 启动策略线程 - 先调用start()初始化，然后调用run()进入循环
            self.strategy_thread = threading.Thread(target=self._run_strategy_with_start)
            self.strategy_thread.daemon = True
            self.strategy_thread.start()
            
            # 启动UI更新线程
            self.update_thread = threading.Thread(target=self.update_status)
            self.update_thread.daemon = True
            self.update_thread.start()
            
            self.log(f"🚀 策略启动成功: {strategy_id}")
            
            # 立即更新状态显示
            self.status_var.set("策略运行中")
            
            self.start_button.config(state='disabled')
            self.pause_button.config(state='normal')
            
        except Exception as e:
            self.log(f"❌ 启动策略失败: {e}")
            messagebox.showerror("错误", f"启动策略失败: {e}")
    
    def pause_strategy(self):
        """暂停策略"""
        if self.grid_strategy:
            self.grid_strategy.stop()
            # 不删除策略对象，保持状态以便重新启动
        
        self.strategy_running = False
        self.start_button.config(state="normal")
        self.pause_button.config(state="disabled")
        self.status_var.set("策略已暂停")
        self.log("⏸️ 网格交易策略已暂停")
        
        # 重置状态显示
        self.current_price_var.set("当前价格: $0.00000000")
        self.base_price_status_var.set("基准价格: $0.00000000")
        self.grid_position_var.set("当前网格: 未确定")
        self.next_order_var.set("下一个挂单: 无")
        self.position_var.set("持仓: 0张")
        self.profit_var.set("总盈利: 0.0000 USDT")
        self.active_orders_var.set("活跃订单: 0个")
        self.grid_count_var.set("网格数量: 0")
    
    def reset_strategy(self):
        """重置策略 - 删除所有策略状态和委托"""
        try:
            # 确认重置
            result = messagebox.askyesno("确认重置", 
                "确定要重置所有策略吗？\n\n这将删除：\n• 所有策略状态\n• 所有委托记录\n• 所有交易记录\n• 所有交易配对记录\n• 所有持仓明细记录\n\n此操作不可恢复！")
            
            if not result:
                return
            
            self.log("🔄 开始重置所有策略")
            
            # 1. 如果有正在运行的策略，先停止并取消所有委托
            if hasattr(self, 'grid_strategy') and self.grid_strategy:
                self.log("🛑 停止正在运行的策略并取消所有委托")
                self.grid_strategy.stop()  # 这会取消所有委托
                self.grid_strategy = None  # 删除策略对象
            
            # 2. 删除数据库中所有策略记录和相关日志
            if self.db_manager:
                self.log("🗑️ 准备删除数据库中所有策略记录和操作日志")
                
                # 删除策略记录
                success = self.db_manager.delete_all_strategies()
                if success:
                    self.log("✅ 数据库中所有策略记录已删除")
                else:
                    self.log("⚠️ 数据库策略记录删除失败")
                
                # 删除操作日志
                try:
                    with sqlite3.connect(self.db_manager.db_path) as conn:
                        cursor = conn.cursor()
                        cursor.execute('DELETE FROM operation_logs')
                        deleted_count = cursor.rowcount
                        conn.commit()
                        self.log(f"✅ 已删除 {deleted_count} 条操作日志")
                except Exception as e:
                    self.log(f"⚠️ 删除操作日志失败: {e}")
            else:
                self.log("⚠️ 数据库管理器未初始化")
            
            # 3. 重置UI状态
            self.strategy_running = False
            self.start_button.config(state="normal")
            self.pause_button.config(state="disabled")
            self.status_var.set("策略未启动")
            
            self.log("✅ 所有策略重置完成")
            messagebox.showinfo("成功", "所有策略已完全重置\n\n已清除：\n• 所有策略状态\n• 所有委托记录\n• 所有交易记录\n• 所有交易配对记录\n• 所有持仓明细记录\n\n所有委托已取消，数据库已清空")
                
        except Exception as e:
            self.log(f"❌ 重置策略失败: {e}")
            messagebox.showerror("错误", f"重置策略失败: {e}")
    
    def show_trade_records(self):
        """显示交易记录"""
        if not self.db_manager:
            messagebox.showinfo("提示", "数据库管理器未初始化")
            return
        
        # 获取当前策略ID
        instrument = self.instrument_var.get()
        if not instrument:
            messagebox.showinfo("提示", "请先选择交易对")
            return
        
        strategy_id = f"grid_strategy_{instrument}"
        
        # 创建交易记录显示窗口
        trades_window = tk.Toplevel(self.root)
        trades_window.title("交易记录详情")
        trades_window.geometry("1200x800")
        
        # 创建主框架
        main_frame = ttk.Frame(trades_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="交易记录详情", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # 交易配对选项卡
        pairs_frame = ttk.Frame(notebook)
        notebook.add(pairs_frame, text="交易配对")
        
        # 创建交易配对表格
        pairs_columns = ("配对ID", "买入价格", "卖出价格", "数量", "买入时间", "卖出时间", "盈利")
        pairs_tree = ttk.Treeview(pairs_frame, columns=pairs_columns, show="headings", height=15)
        
        # 设置列标题
        for col in pairs_columns:
            pairs_tree.heading(col, text=col)
            pairs_tree.column(col, width=150)
        
        # 添加滚动条
        pairs_scrollbar = ttk.Scrollbar(pairs_frame, orient=tk.VERTICAL, command=pairs_tree.yview)
        pairs_tree.configure(yscrollcommand=pairs_scrollbar.set)
        
        # 布局
        pairs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        pairs_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 持仓明细选项卡
        position_frame = ttk.Frame(notebook)
        notebook.add(position_frame, text="持仓明细")
        
        # 创建持仓明细表格
        position_columns = ("订单ID", "价格", "数量", "时间")
        position_tree = ttk.Treeview(position_frame, columns=position_columns, show="headings", height=15)
        
        # 设置列标题
        for col in position_columns:
            position_tree.heading(col, text=col)
            position_tree.column(col, width=200)
        
        # 添加滚动条
        position_scrollbar = ttk.Scrollbar(position_frame, orient=tk.VERTICAL, command=position_tree.yview)
        position_tree.configure(yscrollcommand=position_scrollbar.set)
        
        # 布局
        position_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        position_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 策略汇总选项卡
        summary_frame = ttk.Frame(notebook)
        notebook.add(summary_frame, text="策略汇总")
        
        # 获取数据
        try:
            # 获取交易配对数据
            trade_pairs = self.db_manager.get_trade_pairs(strategy_id)
            for pair in trade_pairs:
                # 安全地格式化数值，处理None值
                buy_price = pair.get('buy_price', 0) or 0
                sell_price = pair.get('sell_price', 0) or 0
                size = pair.get('size', 0) or 0
                profit = pair.get('profit', 0) or 0
                
                pairs_tree.insert("", tk.END, values=(
                    pair.get('pair_id', ''),
                    f"${buy_price:.8f}",
                    f"${sell_price:.8f}",
                    f"{size}张",
                    pair.get('buy_time', ''),
                    pair.get('sell_time', ''),
                    f"${profit:.4f}"
                ))
            
            # 获取持仓明细数据
            position_details = self.db_manager.get_position_details(strategy_id)
            for detail in position_details:
                # 安全地格式化数值，处理None值
                price = detail.get('price', 0) or 0
                size = detail.get('size', 0) or 0
                
                position_tree.insert("", tk.END, values=(
                    detail.get('order_id', ''),
                    f"${price:.8f}",
                    f"{size}张",
                    detail.get('timestamp', '')
                ))
            
            # 获取策略汇总信息
            summary = self.db_manager.get_strategy_summary(strategy_id)
            
            # 显示汇总信息
            # 安全地获取汇总数据，处理None值
            total_pairs = summary.get('total_pairs', 0) or 0
            closed_pairs = summary.get('closed_pairs', 0) or 0
            total_profit = summary.get('total_profit', 0) or 0
            avg_profit = summary.get('avg_profit', 0) or 0
            total_positions = summary.get('total_positions', 0) or 0
            total_size = summary.get('total_size', 0) or 0
            avg_price = summary.get('avg_price', 0) or 0
            
            summary_text = f"""
策略汇总信息:
总交易配对: {total_pairs}个
已完成配对: {closed_pairs}个
总盈利: ${total_profit:.4f} USDT
平均盈利: ${avg_profit:.4f} USDT
持仓明细记录: {total_positions}条
总持仓数量: {total_size:.2f}张
平均持仓价格: ${avg_price:.8f}
            """
            
            summary_label = ttk.Label(summary_frame, text=summary_text, font=("Arial", 12))
            summary_label.pack(pady=20)
            
        except Exception as e:
            self.log(f"❌ 获取交易记录失败: {e}")
            messagebox.showerror("错误", f"获取交易记录失败: {e}")
        
        # 添加刷新按钮
        refresh_button = ttk.Button(main_frame, text="刷新数据", 
                                  command=lambda: self.refresh_trade_records(pairs_tree, position_tree))
        refresh_button.pack(pady=10)
    
    def refresh_trade_records(self, pairs_tree, position_tree):
        """刷新交易记录"""
        # 清空现有数据
        for item in pairs_tree.get_children():
            pairs_tree.delete(item)
        for item in position_tree.get_children():
            position_tree.delete(item)
        
        # 重新获取数据
        instrument = self.instrument_var.get()
        strategy_id = f"grid_strategy_{instrument}"
        
        try:
            # 重新获取交易配对数据
            trade_pairs = self.db_manager.get_trade_pairs(strategy_id)
            for pair in trade_pairs:
                # 安全地格式化数值，处理None值
                buy_price = pair.get('buy_price', 0) or 0
                sell_price = pair.get('sell_price', 0) or 0
                size = pair.get('size', 0) or 0
                profit = pair.get('profit', 0) or 0
                
                pairs_tree.insert("", tk.END, values=(
                    pair.get('pair_id', ''),
                    f"${buy_price:.8f}",
                    f"${sell_price:.8f}",
                    f"{size}张",
                    pair.get('buy_time', ''),
                    pair.get('sell_time', ''),
                    f"${profit:.4f}"
                ))
            
            # 重新获取持仓明细数据
            position_details = self.db_manager.get_position_details(strategy_id)
            for detail in position_details:
                # 安全地格式化数值，处理None值
                price = detail.get('price', 0) or 0
                size = detail.get('size', 0) or 0
                
                position_tree.insert("", tk.END, values=(
                    detail.get('order_id', ''),
                    f"${price:.8f}",
                    f"{size}张",
                    detail.get('timestamp', '')
                ))
                
        except Exception as e:
            self.log(f"❌ 刷新交易记录失败: {e}")
    
    def show_statistics(self):
        """显示统计信息"""
        if not self.grid_strategy:
            messagebox.showinfo("统计信息", "策略未启动")
            return
        
        stats = self.grid_strategy.get_statistics()
        
        stats_text = f"""
交易统计:
总交易次数: {stats['total_trades']}
买入交易: {stats['buy_trades']}
卖出交易: {stats['sell_trades']}
已完成配对: {stats['closed_pairs']}
当前网格数量: {stats['current_grids']}
最大回撤: {stats['max_drawdown']:.4f} USDT
        """
        
        messagebox.showinfo("统计信息", stats_text)
    
    def show_grid_orders(self):
        """显示当前网格挂单信息"""
        if not self.grid_strategy:
            messagebox.showinfo("挂单信息", "策略未启动")
            return
        
        # 创建挂单显示窗口
        orders_window = tk.Toplevel(self.root)
        orders_window.title("网格挂单详情")
        orders_window.geometry("800x600")
        
        # 创建主框架
        main_frame = ttk.Frame(orders_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="网格挂单详情", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # 创建表格
        columns = ("网格ID", "价格", "方向", "数量", "状态", "订单ID", "创建时间")
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=20)
        
        # 设置列标题
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 布局
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 获取网格订单信息
        if self.grid_strategy and self.grid_strategy.grids:
            for grid_id, grid_order in self.grid_strategy.grids.items():
                tree.insert("", tk.END, values=(
                    grid_order.grid_id,
                    f"${grid_order.price:.8f}",
                    grid_order.side,
                    f"{grid_order.size} 张",
                    grid_order.status,
                    grid_order.order_id,
                    grid_order.create_time
                ))
        
        # 添加刷新按钮
        refresh_button = ttk.Button(main_frame, text="刷新", 
                                  command=lambda: self.refresh_orders_window(tree))
        refresh_button.pack(pady=10)
        
        # 添加统计信息
        if self.grid_strategy:
            stats = self.grid_strategy.get_statistics()
            
            # 获取交易所的订单数量
            try:
                exchange_orders = self.grid_strategy.client.get_order_list()
                exchange_order_count = len(exchange_orders) if exchange_orders else 0
            except:
                exchange_order_count = "无法获取"
            
            stats_text = f"""
挂单统计:
策略管理网格: {len(self.grid_strategy.grids)}个
交易所订单: {exchange_order_count}个
活跃网格: {stats['current_grids']}个
已成交: {len([g for g in self.grid_strategy.grids.values() if g.status == 'filled'])}个
已取消: {len([g for g in self.grid_strategy.grids.values() if g.status == 'cancelled'])}个
待处理: {len([g for g in self.grid_strategy.grids.values() if g.status == 'pending'])}个
            """
            stats_label = ttk.Label(main_frame, text=stats_text, font=("Arial", 10))
            stats_label.pack(pady=10)
    
    def refresh_orders_window(self, tree):
        """刷新挂单窗口"""
        # 清空现有数据
        for item in tree.get_children():
            tree.delete(item)
        
        # 重新填充数据
        if self.grid_strategy and self.grid_strategy.grids:
            for grid_id, grid_order in self.grid_strategy.grids.items():
                tree.insert("", tk.END, values=(
                    grid_order.grid_id,
                    f"${grid_order.price:.8f}",
                    grid_order.side,
                    f"{grid_order.size} 张",
                    grid_order.status,
                    grid_order.order_id,
                    grid_order.create_time
                ))
    
    def _run_strategy_with_start(self):
        """启动策略并运行主循环"""
        try:
            # 先调用start()进行初始化
            self.grid_strategy.start()
            # 然后调用run()进入主循环
            self.grid_strategy.run()
        except Exception as e:
            self._handle_strategy_exception('runner', type(e), e)

    def _schedule_strategy_restart(self, delay_seconds: int = 5):
        """在后台计划自动重启策略（避免异常导致停止）。"""
        try:
            if not hasattr(self, 'grid_strategy') or not self.grid_strategy:
                return
            self.log(f"⏳ {delay_seconds}秒后自动重启策略...")
            def _restart():
                try:
                    if self.grid_strategy:
                        # 确保标志位复位
                        self.grid_strategy.is_running = False
                        # 启动新线程
                        self.strategy_thread = threading.Thread(target=self._run_strategy_with_start, daemon=True)
                        self.strategy_thread.start()
                        self.log("🚀 已自动重启策略")
                except Exception as e:
                    self.log(f"自动重启失败: {e}")
            threading.Timer(delay_seconds, _restart).start()
        except Exception:
            pass

    def _handle_strategy_exception(self, source: str, exc_type, exc_value):
        """容错计数后再决定是否自动重启。"""
        try:
            now = time.time()
            # 超过窗口，清零
            if now - getattr(self, '_last_failure_ts', 0) > getattr(self, '_failure_window_seconds', 60):
                self._strategy_failure_count = 0
            self._last_failure_ts = now

            self._strategy_failure_count += 1
            self.log(f"[异常]({source}) {getattr(exc_type,'__name__',str(exc_type))}: {exc_value} | 计数={self._strategy_failure_count}/{self._failure_threshold}")

            if self._strategy_failure_count >= self._failure_threshold:
                self._strategy_failure_count = 0
                self.log("🔁 达到异常阈值，准备重启策略")
                self._schedule_strategy_restart()
        except Exception:
            pass
    
    def run_strategy(self):
        """运行策略的主循环"""
        if self.grid_strategy:
            self.grid_strategy.start()
            self.grid_strategy.run()
    
    def update_status(self):
        """更新状态信息"""
        while hasattr(self, 'grid_strategy') and self.grid_strategy and self.grid_strategy.is_running:
            try:
                # 获取策略状态
                status = self.grid_strategy.get_strategy_status()
                
                # 更新策略运行状态
                self.status_var.set("策略运行中")
                
                # 更新当前价格
                current_price = status['current_price']
                if current_price > 0:
                    self.current_price_var.set(f"当前价格: ${current_price:.8f}")
                
                # 更新基准价格
                self.base_price_status_var.set(f"基准价格: ${status['base_price']:.8f}")
                
                # 更新网格位置信息
                grid_direction = status['grid_direction']
                grid_number = status['grid_number']
                self.grid_position_var.set(f"当前网格: {grid_direction}第{grid_number}个")
                
                # 更新下一个挂单价格
                next_buy = status['next_buy_price']
                next_sell = status['next_sell_price']
                if next_buy:
                    self.next_order_var.set(f"下一个买单: ${next_buy:.8f}")
                elif next_sell:
                    self.next_order_var.set(f"下一个卖单: ${next_sell:.8f}")
                else:
                    self.next_order_var.set("下一个挂单: 无")
                
                # 更新持仓信息
                position = status['current_position']
                self.position_var.set(f"持仓: {position}张")
                
                # 更新盈利信息
                profit = status['total_profit']
                self.profit_var.set(f"总盈利: {profit:.4f} USDT")
                
                # 更新活跃订单数
                active_orders = status['active_orders']
                self.active_orders_var.set(f"活跃订单: {active_orders}个")
                
                # 更新网格数量
                total_grids = len(self.grid_strategy.grid_prices)
                self.grid_count_var.set(f"网格数量: {total_grids}")
                
                # 更新健康状态
                self.update_health_status()
                
            except Exception as e:
                self.log(f"更新状态失败: {e}")
            
            time.sleep(1)  # 每秒更新一次
    
    def update_position_info(self):
        """更新持仓信息 - 只显示long方向的持仓"""
        try:
            positions = self.client.get_positions()
            if positions:
                for position in positions:
                    if (position.get('instId') == self.strategy_params['instrument'] and 
                        position.get('posSide') == 'long'):  # 只显示long方向
                        pos_size = float(position.get('pos', '0'))
                        self.position_var.set(f"持仓: {pos_size:.2f} 张")
                        return
            
            self.position_var.set("持仓: 0 张")
            
        except Exception as e:
            self.log(f"❌ 更新持仓信息失败: {e}")
    
    def on_instrument_selected(self, event):
        """当合约选择改变时，更新合约信息显示"""
        selected_instrument = self.instrument_var.get()
        if selected_instrument:
            try:
                # 获取合约详细信息
                instrument_info = self.get_instrument_info(selected_instrument)
                current_price = self.get_current_price(selected_instrument)
                
                if instrument_info and current_price:
                    # 计算合约面值和成本
                    ct_val = float(instrument_info.get('ctVal', 1))
                    contract_value = current_price * ct_val
                    
                    info_text = f"当前价格: ${current_price:.8f} | 合约面值: {ct_val} | 1张价值: ${contract_value:.4f}"
                    self.contract_info_var.set(info_text)
                    
                    # 自动填充基准价格
                    self.base_price_var.set(f"{current_price:.8f}")
                    
                    # 根据价格计算建议的网格宽度
                    suggested_width = current_price * 0.01  # 1%的价格作为建议网格宽度
                    self.grid_width_var.set(f"{suggested_width:.8f}")
                    
                    self.log(f"已选择合约: {selected_instrument}")
                    self.log(f"当前价格: ${current_price:.8f}")
                    self.log(f"建议网格宽度: ${suggested_width:.8f}")
                    
                elif current_price:
                    info_text = f"当前价格: ${current_price:.8f}"
                    self.contract_info_var.set(info_text)
                    self.base_price_var.set(f"{current_price:.8f}")
                    
                else:
                    self.contract_info_var.set(f"合约: {selected_instrument} (无法获取价格)")
                    
            except Exception as e:
                self.log(f"❌ 获取合约信息失败: {e}")
                self.contract_info_var.set(f"合约: {selected_instrument} (错误)")
        else:
            self.contract_info_var.set("请选择合约")
    
    def search_instruments(self):
        """根据搜索文本筛选合约"""
        search_text = self.search_var.get().strip()
        if search_text:
            try:
                # 从缓存的合约列表中筛选
                filtered_instruments = []
                for inst in self.all_instruments:
                    if search_text.upper() in inst['instId'].upper():
                        filtered_instruments.append(inst['instId'])
                
                if filtered_instruments:
                    self.instrument_combo['values'] = filtered_instruments
                    self.instrument_combo.set(filtered_instruments[0])
                    self.log(f"找到 {len(filtered_instruments)} 个包含 '{search_text}' 的合约")
                    
                    # 自动更新选中合约的信息
                    self.on_instrument_selected(None)
                else:
                    self.instrument_combo['values'] = []
                    self.instrument_combo.set("")
                    self.contract_info_var.set(f"未找到包含 '{search_text}' 的合约")
                    self.log(f"未找到包含 '{search_text}' 的合约")
                    
            except Exception as e:
                self.log(f"❌ 搜索合约失败: {e}")
        else:
            # 如果搜索框为空，恢复所有合约
            self.load_instruments()
    
    def clear_search(self):
        """清除搜索文本并恢复默认合约列表"""
        self.search_var.set("")
        self.load_instruments()  # 重新加载所有合约
        self.log("已清除搜索，恢复默认合约列表")
    
    def get_instrument_info(self, instrument_id):
        """获取合约详细信息"""
        try:
            instruments = self.client.get_instruments("SWAP")
            if instruments:
                for instrument in instruments:
                    if instrument['instId'] == instrument_id:
                        return instrument
            return None
        except Exception as e:
            self.log(f"❌ 获取合约信息异常: {e}")
            return None
    
    def get_current_price(self, instrument_id):
        """获取合约当前价格"""
        try:
            tickers = self.client.get_tickers("SWAP")
            if tickers:
                for ticker in tickers:
                    if ticker['instId'] == instrument_id:
                        return float(ticker['last'])
            return None
        except Exception as e:
            self.log(f"❌ 获取当前价格异常: {e}")
            return None
    
    def build_base_position(self):
        """建立底仓"""
        try:
            # 检查是否选择了合约
            instrument = self.instrument_var.get()
            if not instrument:
                messagebox.showwarning("提示", "请先选择交易品种")
                return
            
            # 检查交易数量/金额是否填写
            trade_value_str = self.trade_value_var.get().strip()
            if not trade_value_str:
                messagebox.showwarning("提示", "请先在交易数量/金额输入框中输入数值")
                return
            
            # 验证交易数量/金额是否为有效数值
            try:
                trade_value = float(trade_value_str)
                if trade_value <= 0:
                    messagebox.showerror("错误", "交易数量/金额必须大于0")
                    return
            except ValueError:
                messagebox.showerror("错误", "请输入有效的交易数量/金额")
                return
            
            # 获取当前价格
            current_price = self.get_current_price(instrument)
            if not current_price:
                messagebox.showerror("错误", "无法获取当前价格")
                return
            
            # 确认建立底仓
            trade_mode = self.trade_mode_var.get()
            if trade_mode == "quantity":
                confirm_message = f"确定要建立底仓吗？\n\n合约: {instrument}\n买入数量: {trade_value}张\n当前价格: ${current_price:.8f}\n预估金额: ${trade_value * current_price:.4f} USDT"
            else:
                confirm_message = f"确定要建立底仓吗？\n\n合约: {instrument}\n买入金额: {trade_value} USDT\n当前价格: ${current_price:.8f}\n预估数量: {trade_value / current_price:.4f}张"
            
            result = messagebox.askyesno("确认建立底仓", confirm_message)
            if not result:
                return
            
            # 执行买入操作
            self.log(f"🔄 开始建立底仓...")
            self.log(f"合约: {instrument}")
            self.log(f"交易模式: {'同等数量' if trade_mode == 'quantity' else '同等金额'}")
            self.log(f"交易值: {trade_value}")
            self.log(f"当前价格: ${current_price:.8f}")
            
            # 根据交易模式确定下单参数
            if trade_mode == "quantity":
                # 同等数量模式：直接使用输入的数量
                size = trade_value
                amount = None
            else:
                # 同等金额模式：根据金额计算数量
                size = trade_value / current_price
                amount = trade_value
            
            # 执行市价买入
            try:
                order_result = self.client.place_order(
                    inst_id=instrument,
                    td_mode="cross",
                    side="buy",
                    pos_side="long",  # 做多策略，持仓方向为long
                    ord_type="market",
                    sz=str(size),
                    px=None  # 市价单不需要价格
                )
                
                if order_result and order_result.get('ordId'):
                    order_id = order_result['ordId']
                    self.log(f"✅ 底仓建立成功！")
                    self.log(f"订单ID: {order_id}")
                    self.log(f"买入数量: {size:.4f}张")
                    if amount:
                        self.log(f"买入金额: ${amount:.4f} USDT")
                    
                    messagebox.showinfo("成功", f"底仓建立成功！\n订单ID: {order_id}\n买入数量: {size:.4f}张")
                    
                    # 刷新持仓显示
                    self.refresh_positions_display()
                else:
                    error_msg = order_result.get('msg', '未知错误') if order_result else '下单失败'
                    self.log(f"❌ 建立底仓失败: {error_msg}")
                    messagebox.showerror("错误", f"建立底仓失败: {error_msg}")
                    
            except Exception as e:
                self.log(f"❌ 建立底仓异常: {e}")
                messagebox.showerror("错误", f"建立底仓异常: {e}")
                
        except Exception as e:
            self.log(f"❌ 建立底仓失败: {e}")
            messagebox.showerror("错误", f"建立底仓失败: {e}")
    
    def refresh_instrument_info(self):
        """手动刷新合约信息"""
        selected_instrument = self.instrument_var.get()
        if selected_instrument:
            try:
                instrument_info = self.get_instrument_info(selected_instrument)
                current_price = self.get_current_price(selected_instrument)
                
                if instrument_info and current_price:
                    ct_val = float(instrument_info.get('ctVal', 1))
                    contract_value = current_price * ct_val
                    
                    info_text = f"当前价格: ${current_price:.8f} | 合约面值: {ct_val} | 1张价值: ${contract_value:.4f}"
                    self.contract_info_var.set(info_text)
                    
                    self.base_price_var.set(f"{current_price:.8f}")
                    
                    suggested_width = current_price * 0.01
                    self.grid_width_var.set(f"{suggested_width:.8f}")
                    
                    self.log(f"已刷新合约: {selected_instrument}")
                    self.log(f"当前价格: ${current_price:.8f}")
                    self.log(f"建议网格宽度: ${suggested_width:.8f}")
                else:
                    self.contract_info_var.set(f"合约: {selected_instrument} (无法获取信息)")
            except Exception as e:
                self.log(f"❌ 刷新合约信息失败: {e}")
        else:
            messagebox.showwarning("提示", "请先选择一个合约")
    
    def refresh_positions_display(self):
        """刷新持仓显示"""
        try:
            # 清空现有数据
            for item in self.positions_tree.get_children():
                self.positions_tree.delete(item)
            
            # 获取持仓信息
            self.log("正在查询持仓信息...")
            positions = self.client.get_positions()
            
            if positions is None:
                self.log("❌ 获取持仓信息失败")
                return
            
            self.log(f"获取到 {len(positions)} 条持仓记录")
            
            # 过滤出有持仓的记录，只显示long方向的持仓
            active_positions = [pos for pos in positions if 
                              float(pos.get('pos', '0')) != 0 and 
                              pos.get('posSide') == 'long']  # 只显示long方向
            
            if not active_positions:
                self.log("✅ 当前没有long方向持仓")
                return
            
            self.log(f"✅ 当前有 {len(active_positions)} 个long方向持仓")
            
            for position in active_positions:
                inst_id = position.get('instId', '')
                pos_side = position.get('posSide', '')
                
                # 安全地转换数值，处理空字符串
                pos_size_str = position.get('pos', '0')
                avg_px_str = position.get('avgPx', '0')
                mark_px_str = position.get('markPx', '0')
                upl_str = position.get('upl', '0')
                margin_str = position.get('margin', '0')
                
                pos_size = float(pos_size_str) if pos_size_str and pos_size_str.strip() else 0.0
                avg_px = float(avg_px_str) if avg_px_str and avg_px_str.strip() else 0.0
                mark_px = float(mark_px_str) if mark_px_str and mark_px_str.strip() else 0.0
                upl = float(upl_str) if upl_str and upl_str.strip() else 0.0
                margin = float(margin_str) if margin_str and margin_str.strip() else 0.0
                
                # 格式化显示
                pos_side_display = "做多" if pos_side == "long" else "做空" if pos_side == "short" else pos_side
                pos_size_display = f"{pos_size:.4f}张"
                avg_px_display = f"${avg_px:.8f}" if avg_px > 0 else "N/A"
                mark_px_display = f"${mark_px:.8f}" if mark_px > 0 else "N/A"
                upl_display = f"${upl:.4f}" if upl != 0 else "$0.0000"
                margin_display = f"${margin:.4f}" if margin > 0 else "$0.0000"
                
                # 插入到表格
                self.positions_tree.insert("", tk.END, values=(
                    inst_id,
                    pos_side_display,
                    pos_size_display,
                    avg_px_display,
                    mark_px_display,
                    upl_display,
                    margin_display
                ))
                
                self.log(f"持仓: {inst_id} {pos_side_display} {pos_size_display} 均价:{avg_px_display} 盈亏:{upl_display}")
                
        except Exception as e:
            self.log(f"❌ 刷新持仓显示失败: {e}")
            import traceback
            traceback.print_exc()
    
    def clear_real_time_logs(self):
        """清除实时日志"""
        try:
            self.real_time_log_text.delete("1.0", tk.END)
            if hasattr(self, 'real_time_logger'):
                self.real_time_logger.clear_logs()
            self.log_status_var.set("日志已清除")
            self.log(f"🧹 实时日志已清除")
        except Exception as e:
            self.log(f"❌ 清除日志失败: {e}")
    
    def save_real_time_logs(self):
        """保存实时日志到文件"""
        try:
            from tkinter import filedialog
            import os
            
            # 获取当前时间作为文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"grid_trading_logs_{timestamp}.txt"
            
            # 打开文件保存对话框
            filename = filedialog.asksaveasfilename(
                title="保存日志文件",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
                initialname=default_filename
            )
            
            if filename:
                # 获取所有日志内容
                log_content = self.real_time_log_text.get("1.0", tk.END)
                
                # 写入文件
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(f"网格交易策略日志 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n")
                    f.write(log_content)
                
                self.log_status_var.set(f"日志已保存: {os.path.basename(filename)}")
                self.log(f"💾 实时日志已保存到: {filename}")
                
        except Exception as e:
            self.log(f"❌ 保存日志失败: {e}")
    
    def open_console_log_window(self):
        """打开独立控制台日志窗口"""
        try:
            # 导入控制台日志窗口模块
            from console_logger import create_console_log_window
            
            # 创建独立日志窗口
            self.console_log_window = create_console_log_window()
            
            # 在新线程中运行日志窗口
            log_window_thread = threading.Thread(target=self.console_log_window.run, daemon=True)
            log_window_thread.start()
            
            self.log("🖥️ 独立日志窗口已启动")
            
        except ImportError:
            messagebox.showerror("错误", "无法导入控制台日志模块，请确保console_logger.py文件存在")
        except Exception as e:
            self.log(f"❌ 启动独立日志窗口失败: {e}")
            messagebox.showerror("错误", f"启动独立日志窗口失败: {e}")
    
    def run(self):
        """运行UI"""
        self.root.mainloop()
    
    def force_resume_strategy(self):
        """强制恢复策略运行"""
        if self.grid_strategy:
            if self.grid_strategy.force_resume_strategy():
                self.log("🔄 策略已强制恢复运行")
                self.health_status_var.set("策略状态: 已恢复")
                self.force_resume_button.config(state="disabled")
            else:
                self.log("ℹ️ 策略当前没有暂停")
        else:
            self.log("❌ 策略未启动")

    def confirm_center_price_dialog(self):
        """弹窗：当数据库最后成交价与交易所最近成交价差异大时，供人工确认选择中心价"""
        try:
            if not self.grid_strategy or not self.db_manager:
                messagebox.showwarning("提示", "策略未启动或数据库不可用")
                return

            strategy_id = self.grid_strategy.strategy_id
            status = self.db_manager.get_strategy_status(strategy_id) or {}
            db_last = float(status.get('last_fill_price') or 0)

            # 实时获取交易所最近成交（两次验证由策略端已实现；此处仅展示一次）
            fills = self.grid_strategy.client.get_recent_fills(self.grid_strategy.instrument, limit=1) or []
            ex_last = 0.0
            if fills:
                f = fills[0]
                ex_last = float(f.get('fillPx') or f.get('px') or 0)

            prompt = f"数据库最后成交价: ${db_last:.2f}\n交易所最近成交价: ${ex_last:.2f}\n\n请选择用于计算挂单的中心价。"
            choice = messagebox.askyesno("确认中心价", prompt + "\n\n是=使用交易所价，否=使用数据库价")

            chosen = ex_last if choice else db_last
            if chosen <= 0:
                messagebox.showerror("错误", "中心价无效")
                return

            # 写入到策略的最近成交价并保存状态
            self.grid_strategy.last_fill_price = chosen
            self.grid_strategy.last_fill_side = 'buy'  # 无法确认方向，这里仅占位
            self.grid_strategy._save_strategy_status()

            self.log(f"✅ 已确认中心价: ${chosen:.2f}")
            messagebox.showinfo("成功", f"已确认中心价: ${chosen:.2f}")
        except Exception as e:
            self.log(f"❌ 中心价确认失败: {e}")
    
    def update_health_status(self):
        """更新策略健康状态显示"""
        if self.grid_strategy:
            try:
                health = self.grid_strategy.get_strategy_health()
                
                # 更新状态显示
                self.health_status_var.set(f"策略状态: {health['status_description']}")
                
                # 根据状态设置按钮状态
                if health['critical_data_failed']:
                    self.force_resume_button.config(state="normal")
                    # 设置状态颜色
                    if health['consecutive_failures'] >= health['max_consecutive_failures']:
                        self.health_status_var.set(f"策略状态: 暂停中 (连续失败{health['consecutive_failures']}次)")
                    else:
                        self.health_status_var.set(f"策略状态: 暂停中 (等待重试)")
                else:
                    self.force_resume_button.config(state="disabled")
                    self.health_status_var.set("策略状态: 运行正常")
                    
            except Exception as e:
                self.log(f"❌ 更新健康状态失败: {e}")
                self.health_status_var.set("策略状态: 状态未知")
        else:
            self.health_status_var.set("策略状态: 未启动")
            self.force_resume_button.config(state="disabled")

def main():
    """主函数"""
    app = GridTradingUI()
    app.run()

if __name__ == "__main__":
    main() 