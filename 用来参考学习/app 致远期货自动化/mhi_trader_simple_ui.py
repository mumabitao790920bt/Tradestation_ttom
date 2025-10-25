#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易测试程序 - 简洁UI界面
提供简洁的图形化界面来快速测试MHI交易功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
from datetime import datetime
import logging

class SimpleMHITraderUI:
    def __init__(self, root):
        self.root = root
        self.root.title("MHI交易测试 - 简洁版")
        self.root.geometry("800x600")
        self.root.configure(bg='#f5f5f5')
        
        # 交易器实例
        self.trader = None
        self.is_browser_running = False
        
        # 创建界面
        self.create_interface()
        
    def create_interface(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="MHI交易测试程序", 
                               font=('Arial', 14, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # 创建左右两个面板
        self.create_left_panel(main_frame)
        self.create_right_panel(main_frame)
        
    def create_left_panel(self, parent):
        """创建左侧控制面板"""
        left_frame = ttk.Frame(parent)
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 浏览器控制
        browser_frame = ttk.LabelFrame(left_frame, text="浏览器控制", padding="10")
        browser_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(browser_frame, text="启动浏览器", 
                  command=self.start_browser, width=15).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(browser_frame, text="关闭浏览器", 
                  command=self.close_browser, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        self.browser_status_label = ttk.Label(browser_frame, text="未连接", foreground="red")
        self.browser_status_label.grid(row=1, column=0, columnspan=2, pady=5)
        
        # 快速设置
        settings_frame = ttk.LabelFrame(left_frame, text="快速设置", padding="10")
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 模式选择
        ttk.Label(settings_frame, text="交易模式:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mode_var = tk.StringVar(value="模拟")
        mode_combo = ttk.Combobox(settings_frame, textvariable=self.mode_var, 
                                 values=["模拟", "实盘"], state="readonly", width=15)
        mode_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 手数选择
        ttk.Label(settings_frame, text="手数:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.lots_var = tk.StringVar(value="1")
        lots_combo = ttk.Combobox(settings_frame, textvariable=self.lots_var, 
                                 values=["1", "2", "3", "5", "8", "10"], state="readonly", width=15)
        lots_combo.grid(row=1, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 保证金选择
        ttk.Label(settings_frame, text="保证金:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.margin_var = tk.StringVar(value="2700")
        margin_combo = ttk.Combobox(settings_frame, textvariable=self.margin_var, 
                                   values=["2700", "4050", "5850", "8100"], state="readonly", width=15)
        margin_combo.grid(row=2, column=1, sticky=tk.W, pady=2, padx=(5, 0))
        
        # 交易操作
        trade_frame = ttk.LabelFrame(left_frame, text="交易操作", padding="10")
        trade_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 买涨买跌按钮
        ttk.Button(trade_frame, text="买涨", 
                  command=self.buy_long, style="Buy.TButton", width=12).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(trade_frame, text="买跌", 
                  command=self.buy_short, style="Sell.TButton", width=12).grid(row=0, column=1, padx=5, pady=5)
        
        # 平仓按钮
        ttk.Button(trade_frame, text="一键平仓", 
                  command=self.close_all_positions, width=25).grid(row=1, column=0, columnspan=2, pady=5)
        
        # 查询操作
        query_frame = ttk.LabelFrame(left_frame, text="查询操作", padding="10")
        query_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(query_frame, text="查询持仓", 
                  command=self.query_positions, width=12).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(query_frame, text="查询委托", 
                  command=self.query_orders, width=12).grid(row=0, column=1, padx=5, pady=5)
        
        # 测试操作
        test_frame = ttk.LabelFrame(left_frame, text="测试操作", padding="10")
        test_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(test_frame, text="按钮测试", 
                  command=self.run_button_test, width=12).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(test_frame, text="完整测试", 
                  command=self.run_full_test, width=12).grid(row=0, column=1, padx=5, pady=5)
        
        # 配置网格权重
        left_frame.columnconfigure(0, weight=1)
        
    def create_right_panel(self, parent):
        """创建右侧日志面板"""
        right_frame = ttk.Frame(parent)
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志面板
        log_frame = ttk.LabelFrame(right_frame, text="操作日志", padding="10")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 日志文本框
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=50)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 清空日志按钮
        ttk.Button(log_frame, text="清空日志", 
                  command=self.clear_log).grid(row=1, column=0, pady=5)
        
        # 配置网格权重
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        # 在主线程中更新UI
        self.root.after(0, self._update_log, log_entry)
        
    def _update_log(self, log_entry):
        """更新日志显示"""
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)
        
    def start_browser(self):
        """启动浏览器"""
        try:
            if self.is_browser_running:
                messagebox.showinfo("提示", "浏览器已在运行")
                return
            
            # 在新线程中启动浏览器
            threading.Thread(target=self._start_browser_thread, daemon=True).start()
            
        except Exception as e:
            self.log_message(f"启动浏览器失败: {e}")
            messagebox.showerror("错误", f"启动浏览器失败: {e}")
    
    def _start_browser_thread(self):
        """启动浏览器线程"""
        try:
            from mhi_trader_test import MHITrader
            
            self.trader = MHITrader(log_callback=self.log_message)
            
            if self.trader.start_browser():
                self.is_browser_running = True
                self.root.after(0, self._update_browser_status, "已连接", "green")
                self.log_message("✅ 浏览器启动成功")
            else:
                self.root.after(0, self._update_browser_status, "连接失败", "red")
                self.log_message("❌ 浏览器启动失败")
                
        except Exception as e:
            self.log_message(f"启动浏览器异常: {e}")
            self.root.after(0, self._update_browser_status, "连接失败", "red")
    
    def _update_browser_status(self, status, color):
        """更新浏览器状态"""
        self.browser_status_label.config(text=status, foreground=color)
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.trader:
                self.trader.close_browser()
                self.trader = None
                self.is_browser_running = False
                self._update_browser_status("未连接", "red")
                self.log_message("✅ 浏览器已关闭")
            else:
                messagebox.showinfo("提示", "浏览器未运行")
                
        except Exception as e:
            self.log_message(f"关闭浏览器失败: {e}")
            messagebox.showerror("错误", f"关闭浏览器失败: {e}")
    
    def buy_long(self):
        """买涨操作"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动浏览器")
            return
        
        # 获取参数
        lots = int(self.lots_var.get())
        margin = int(self.margin_var.get())
        
        # 在新线程中执行买涨
        threading.Thread(target=self._buy_long_thread, 
                       args=(lots, margin), daemon=True).start()
    
    def _buy_long_thread(self, lots, margin):
        """买涨线程"""
        try:
            self.log_message(f"🔄 开始买涨操作 - 手数:{lots}, 保证金:{margin}")
            
            if self.trader.buy_long(lots, margin):
                self.log_message("✅ 买涨操作完成")
            else:
                self.log_message("❌ 买涨操作失败")
                
        except Exception as e:
            self.log_message(f"买涨操作异常: {e}")
    
    def buy_short(self):
        """买跌操作"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动浏览器")
            return
        
        # 获取参数
        lots = int(self.lots_var.get())
        margin = int(self.margin_var.get())
        
        # 在新线程中执行买跌
        threading.Thread(target=self._buy_short_thread, 
                       args=(lots, margin), daemon=True).start()
    
    def _buy_short_thread(self, lots, margin):
        """买跌线程"""
        try:
            self.log_message(f"🔄 开始买跌操作 - 手数:{lots}, 保证金:{margin}")
            
            if self.trader.buy_short(lots, margin):
                self.log_message("✅ 买跌操作完成")
            else:
                self.log_message("❌ 买跌操作失败")
                
        except Exception as e:
            self.log_message(f"买跌操作异常: {e}")
    
    def close_all_positions(self):
        """一键平仓"""
        if not self.trader:
            messagebox.showwarning("警告", "请先启动浏览器")
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
            messagebox.showwarning("警告", "请先启动浏览器")
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
            messagebox.showwarning("警告", "请先启动浏览器")
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
            messagebox.showwarning("警告", "请先启动浏览器")
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
            messagebox.showwarning("警告", "请先启动浏览器")
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
    
    app = SimpleMHITraderUI(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.trader:
            app.close_browser()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
