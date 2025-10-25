#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易测试程序 - UI界面
提供图形化界面来操作和测试MHI交易功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

class MHITraderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MHI交易测试程序 - UI界面")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 交易器实例
        self.trader = None
        self.is_browser_running = False
        
        # 日志回调
        self.log_callback = self.log_message
        
        # 创建界面
        self.create_interface()
        
        # 设置日志
        self.setup_logging()
        
    def create_interface(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="MHI交易测试程序", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左侧控制面板
        self.create_control_panel(main_frame)
        
        # 右侧日志面板
        self.create_log_panel(main_frame)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 数据连接控制
        browser_frame = ttk.LabelFrame(control_frame, text="数据连接控制", padding="5")
        browser_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(browser_frame, text="启动数据连接",
                  command=self.start_browser).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(browser_frame, text="关闭数据连接",
                  command=self.close_browser).grid(row=0, column=1, padx=5, pady=5)
        
        self.browser_status_label = ttk.Label(browser_frame, text="未连接", foreground="red")
        self.browser_status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 模式控制
        mode_frame = ttk.LabelFrame(control_frame, text="交易模式", padding="5")
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        self.mode_var = tk.StringVar(value="模拟")
        ttk.Radiobutton(mode_frame, text="模拟模式", variable=self.mode_var, 
                       value="模拟").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Radiobutton(mode_frame, text="实盘模式", variable=self.mode_var, 
                       value="实盘").grid(row=1, column=0, sticky=tk.W, pady=2)
        
        # 订单设置
        order_frame = ttk.LabelFrame(control_frame, text="订单设置", padding="5")
        order_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 订单类型
        ttk.Label(order_frame, text="订单类型:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.order_type_var = tk.StringVar(value="市价")
        order_type_combo = ttk.Combobox(order_frame, textvariable=self.order_type_var, 
                                       values=["市价", "限价"], state="readonly", width=10)
        order_type_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 交易模式
        ttk.Label(order_frame, text="交易模式:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.trading_mode_var = tk.StringVar(value="元")
        self.trading_mode_combo = ttk.Combobox(order_frame, textvariable=self.trading_mode_var, 
                                        values=["元", "角"], state="readonly", width=10)
        self.trading_mode_combo.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 绑定模式变化事件，自动调整交易模式选项
        self.mode_var.trace('w', self.on_mode_change)
        
        # 手数设置
        ttk.Label(order_frame, text="手数:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.lots_var = tk.StringVar(value="1")
        lots_combo = ttk.Combobox(order_frame, textvariable=self.lots_var, 
                                 values=["1", "2", "3", "5", "8", "10"], state="readonly", width=10)
        lots_combo.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 保证金设置
        ttk.Label(order_frame, text="保证金:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.margin_var = tk.StringVar(value="一档")
        margin_combo = ttk.Combobox(order_frame, textvariable=self.margin_var, 
                                   values=["一档", "二档", "三档", "四档"], state="readonly", width=10)
        margin_combo.grid(row=3, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 止盈设置
        ttk.Label(order_frame, text="止盈价格:").grid(row=4, column=0, sticky=tk.W, pady=2)
        self.take_profit_var = tk.StringVar()
        take_profit_entry = ttk.Entry(order_frame, textvariable=self.take_profit_var, width=12)
        take_profit_entry.grid(row=4, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 切换模式按钮（移到订单设置下面）
        ttk.Button(order_frame, text="切换模式", 
                  command=self.switch_mode).grid(row=5, column=0, columnspan=2, pady=10)
        
        # 交易操作
        trade_frame = ttk.LabelFrame(control_frame, text="交易操作", padding="5")
        trade_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(trade_frame, text="买涨", 
                  command=self.buy_long, style="Buy.TButton").grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(trade_frame, text="买跌", 
                  command=self.buy_short, style="Sell.TButton").grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(trade_frame, text="一键平仓", 
                  command=self.close_all_positions).grid(row=1, column=0, columnspan=2, pady=5)
        
        # 查询操作（暂时隐藏）
        # query_frame = ttk.LabelFrame(control_frame, text="查询操作", padding="5")
        # query_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # ttk.Button(query_frame, text="查询持仓", 
        #           command=self.query_positions).grid(row=0, column=0, padx=5, pady=5)
        # ttk.Button(query_frame, text="查询委托", 
        #           command=self.query_orders).grid(row=0, column=1, padx=5, pady=5)
        
        # 测试操作（暂时隐藏）
        # test_frame = ttk.LabelFrame(control_frame, text="测试操作", padding="5")
        # test_frame.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # ttk.Button(test_frame, text="按钮测试", 
        #           command=self.run_button_test).grid(row=0, column=0, padx=5, pady=5)
        # ttk.Button(test_frame, text="完整测试", 
        #           command=self.run_full_test).grid(row=0, column=1, padx=5, pady=5)
        
        # 配置网格权重
        control_frame.columnconfigure(0, weight=1)
        
    def create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(parent, text="操作日志", padding="10")
        log_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=30, width=60)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mhi_trader_ui.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, self._update_log, log_entry)
        logging.info(message)
    
    def on_mode_change(self, *args):
        """模式变化时的处理"""
        mode = self.mode_var.get()
        if mode == "模拟":
            # 模拟模式只能选择"元"
            self.trading_mode_combo['values'] = ["元"]
            if self.trading_mode_var.get() != "元":
                self.trading_mode_var.set("元")
        else:
            # 实盘模式可以选择"元"或"角"
            self.trading_mode_combo['values'] = ["元", "角"]
        
    def _update_log(self, log_entry):
        """更新日志显示"""
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def start_browser(self):
        """启动数据连接"""
        try:
            if self.is_browser_running:
                messagebox.showinfo("提示", "数据连接已在运行")
                return
            
            # 在新线程中启动数据连接
            threading.Thread(target=self._start_browser_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"启动数据连接失败: {e}")
            messagebox.showerror("错误", f"启动数据连接失败: {e}")
    
    def _start_browser_thread(self):
        """启动数据连接线程"""
        try:
            from mhi_trader_test import MHITrader
            
            self.trader = MHITrader(log_callback=self.log_callback)
            
            if self.trader.start_browser():
                self.is_browser_running = True
                self.root.after(0, self._update_browser_status, "已连接", "green")
                self.log_message("✅ 数据连接启动成功")
            else:
                self.root.after(0, self._update_browser_status, "连接失败", "red")
                self.log_message("❌ 数据连接启动失败")
                
        except Exception as e:
            self.log_message(f"启动数据连接异常: {e}")
            self.root.after(0, self._update_browser_status, "连接失败", "red")
    
    def _update_browser_status(self, status, color):
        """更新数据连接状态"""
        self.browser_status_label.config(text=status, foreground=color)
    
    def close_browser(self):
        """关闭数据连接"""
        try:
            if self.trader:
                self.trader.close_browser()
                self.trader = None
                self.is_browser_running = False
                self._update_browser_status("未连接", "red")
                self.log_message("✅ 数据连接已关闭")
            else:
                messagebox.showinfo("提示", "数据连接未运行")
                
        except Exception as e:
            self.log_message(f"关闭数据连接失败: {e}")
            messagebox.showerror("错误", f"关闭数据连接失败: {e}")
    
    def switch_mode(self):
        """切换交易模式并一次性设置所有参数"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        mode = self.mode_var.get()
        
        # 实盘模式需要确认
        if mode == "实盘":
            result = messagebox.askyesno("确认", "确定要切换到实盘模式吗？\n这将进行真实交易！")
            if not result:
                self.mode_var.set("模拟")
                return
        
        # 在新线程中切换模式并设置所有参数
        threading.Thread(target=self._switch_mode_and_set_all_thread, args=(mode,), daemon=True).start()
    
    def _switch_mode_and_set_all_thread(self, mode):
        """切换模式并设置所有参数线程"""
        try:
            self.log_message(f"🔄 开始切换模式并设置所有参数: {mode}")
            
            # 1. 切换交易模式
            if not self.trader.switch_mode(mode):
                self.log_message(f"❌ 切换{mode}模式失败")
                self.root.after(0, lambda: self.mode_var.set("模拟"))
                return
            
            # 2. 设置订单类型（只有实盘模式需要设置）
            order_type = "不设置"  # 默认值
            if mode == "实盘":
                order_type = self.order_type_var.get()
                if not self.trader.set_order_type(order_type):
                    self.log_message(f"❌ 设置订单类型{order_type}失败")
                    return
            
            # 3. 设置交易模式（元/角）
            trading_mode = self.trading_mode_var.get()
            # 模拟模式只能选择"元"
            if mode == "模拟" and trading_mode != "元":
                self.log_message("⚠️ 模拟模式只能选择'元'，自动设置为'元'")
                trading_mode = "元"
                self.root.after(0, lambda: self.trading_mode_var.set("元"))
            
            if not self.trader.set_trading_mode(trading_mode):
                self.log_message(f"❌ 设置交易模式{trading_mode}失败")
                return
            
            # 4. 设置手数
            lots = int(self.lots_var.get())
            if not self.trader.set_lot_size(lots):
                self.log_message(f"❌ 设置手数{lots}失败")
                return
            
            # 5. 设置保证金
            margin_text = self.margin_var.get()
            # 将档位转换为对应的保证金值
            margin_map = {
                "一档": 2700,
                "二档": 4050,
                "三档": 5850,
                "四档": 8100
            }
            margin = margin_map.get(margin_text, 2700)
            if not self.trader.set_margin(margin):
                self.log_message(f"❌ 设置保证金{margin_text}({margin})失败")
                return
            
            # 6. 设置止盈价格（如果有输入）
            take_profit = self.take_profit_var.get()
            if take_profit.strip():
                try:
                    take_profit_price = float(take_profit)
                    if not self.trader.set_take_profit(take_profit_price):
                        self.log_message(f"❌ 设置止盈价格{take_profit_price}失败")
                        return
                except ValueError:
                    self.log_message(f"⚠️ 止盈价格格式错误: {take_profit}")
            
            self.log_message(f"✅ 已切换到{mode}模式并完成所有参数设置")
            self.log_message(f"📋 参数设置: 订单类型={order_type}, 交易模式={trading_mode}, 手数={lots}, 保证金={margin}, 止盈={take_profit or '未设置'}")
                
        except Exception as e:
            self.log_message(f"❌ 切换模式并设置参数异常: {e}")
            self.root.after(0, lambda: self.mode_var.set("模拟"))
    
    def buy_long(self):
        """买涨操作"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 在新线程中执行买涨（不再设置参数，直接交易）
        threading.Thread(target=self._buy_long_thread, daemon=True).start()
    
    def _buy_long_thread(self):
        """买涨线程"""
        try:
            self.log_message("🔄 开始买涨操作")
            
            # 直接执行买涨，不再设置参数
            if self.trader.buy_long():
                self.log_message("✅ 买涨操作完成")
            else:
                self.log_message("❌ 买涨操作失败")
                
        except Exception as e:
            self.log_message(f"买涨操作异常: {e}")
    
    def buy_short(self):
        """买跌操作"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 在新线程中执行买跌（不再设置参数，直接交易）
        threading.Thread(target=self._buy_short_thread, daemon=True).start()
    
    def _buy_short_thread(self):
        """买跌线程"""
        try:
            self.log_message("🔄 开始买跌操作")
            
            # 直接执行买跌，不再设置参数
            if self.trader.buy_short():
                self.log_message("✅ 买跌操作完成")
            else:
                self.log_message("❌ 买跌操作失败")
                
        except Exception as e:
            self.log_message(f"买跌操作异常: {e}")
    
    def close_all_positions(self):
        """一键平仓"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 确认操作
        result = messagebox.askyesno("确认", "确定要执行一键平仓吗？")
        if not result:
            return
        
        # 在新线程中执行平仓
        threading.Thread(target=self._close_all_positions_thread, daemon=True).start()
    
    def _close_all_positions_thread(self):
        """一键平仓线程"""
        try:
            self.log_message("🔄 执行一键平仓")
            
            if self.trader.close_all_positions():
                self.log_message("✅ 一键平仓完成")
            else:
                self.log_message("❌ 一键平仓失败")
                
        except Exception as e:
            self.log_message(f"一键平仓异常: {e}")
    
    def query_positions(self):
        """查询持仓"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 在新线程中查询持仓
        threading.Thread(target=self._query_positions_thread, daemon=True).start()
    
    def _query_positions_thread(self):
        """查询持仓线程"""
        try:
            self.log_message("🔄 查询当前持仓")
            
            positions = self.trader.query_positions()
            self.log_message(f"📊 当前持仓: {len(positions)} 个")
            
            for i, pos in enumerate(positions):
                self.log_message(f"  持仓{i+1}: {pos}")
                
        except Exception as e:
            self.log_message(f"查询持仓异常: {e}")
    
    def query_orders(self):
        """查询委托"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 在新线程中查询委托
        threading.Thread(target=self._query_orders_thread, daemon=True).start()
    
    def _query_orders_thread(self):
        """查询委托线程"""
        try:
            self.log_message("🔄 查询当前委托")
            
            orders = self.trader.query_orders()
            self.log_message(f"📋 当前委托: {len(orders)} 个")
            
            for i, order in enumerate(orders):
                self.log_message(f"  委托{i+1}: {order}")
                
        except Exception as e:
            self.log_message(f"查询委托异常: {e}")
    
    def run_button_test(self):
        """运行按钮测试"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 在新线程中运行按钮测试
        threading.Thread(target=self._run_button_test_thread, daemon=True).start()
    
    def _run_button_test_thread(self):
        """按钮测试线程"""
        try:
            self.log_message("🧪 开始按钮功能测试")
            
            from mhi_button_tester import MHIButtonTester
            tester = MHIButtonTester()
            tester.driver = self.trader.driver
            tester.wait = self.trader.wait
            tester.element_map = self.trader.element_map
            
            # 运行各种测试
            tester.test_mode_switches()
            tester.test_order_type_buttons()
            tester.test_trading_mode_buttons()
            tester.test_lot_size_buttons()
            tester.test_margin_buttons()
            tester.test_input_fields()
            tester.test_position_buttons()
            
            self.log_message("✅ 按钮功能测试完成")
            
        except Exception as e:
            self.log_message(f"按钮测试异常: {e}")
    
    def run_full_test(self):
        """运行完整测试"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动数据连接")
            return
        
        # 确认操作
        result = messagebox.askyesno("确认", "确定要运行完整测试吗？\n这将执行完整的交易流程测试。")
        if not result:
            return
        
        # 在新线程中运行完整测试
        threading.Thread(target=self._run_full_test_thread, daemon=True).start()
    
    def _run_full_test_thread(self):
        """完整测试线程"""
        try:
            self.log_message("🚀 开始完整测试场景")
            
            mode = self.mode_var.get()
            if self.trader.run_test_scenario(mode):
                self.log_message("✅ 完整测试场景完成")
            else:
                self.log_message("❌ 完整测试场景失败")
                
        except Exception as e:
            self.log_message(f"完整测试异常: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    
    # 设置样式
    style = ttk.Style()
    style.configure("Buy.TButton", foreground="red")
    style.configure("Sell.TButton", foreground="green")
    
    app = MHITraderUI(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.trader:
            app.close_browser()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
