#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易测试程序启动器
提供选择不同UI版本的启动界面
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import sys
import os

class MHIStarter:
    def __init__(self, root):
        self.root = root
        self.root.title("MHI交易测试程序启动器")
        self.root.geometry("500x400")
        self.root.configure(bg='#f0f0f0')
        
        # 创建界面
        self.create_interface()
        
    def create_interface(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="MHI交易测试程序", 
                               font=('Arial', 18, 'bold'))
        title_label.grid(row=0, column=0, pady=(0, 30))
        
        # 副标题
        subtitle_label = ttk.Label(main_frame, text="请选择要启动的UI版本", 
                                  font=('Arial', 12))
        subtitle_label.grid(row=1, column=0, pady=(0, 30))
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, pady=20)
        
        # 简洁版UI按钮
        simple_btn = ttk.Button(button_frame, text="简洁版UI", 
                               command=self.launch_simple_ui, width=20)
        simple_btn.grid(row=0, column=0, pady=10, padx=10)
        
        # 完整版UI按钮
        full_btn = ttk.Button(button_frame, text="完整版UI", 
                             command=self.launch_full_ui, width=20)
        full_btn.grid(row=1, column=0, pady=10, padx=10)
        
        # 命令行版本按钮
        cmd_btn = ttk.Button(button_frame, text="命令行版本", 
                            command=self.launch_cmd_version, width=20)
        cmd_btn.grid(row=2, column=0, pady=10, padx=10)
        
        # 按钮测试器按钮
        tester_btn = ttk.Button(button_frame, text="按钮测试器", 
                               command=self.launch_button_tester, width=20)
        tester_btn.grid(row=3, column=0, pady=10, padx=10)
        
        # 元素检测器按钮
        detector_btn = ttk.Button(button_frame, text="元素检测器", 
                                 command=self.launch_element_detector, width=20)
        detector_btn.grid(row=4, column=0, pady=10, padx=10)
        
        # 说明文本
        info_frame = ttk.LabelFrame(main_frame, text="说明", padding="10")
        info_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=20)
        
        info_text = """
简洁版UI: 提供基本的交易操作界面，适合快速测试
完整版UI: 提供完整的交易功能界面，包含详细设置
命令行版本: 纯命令行操作，适合自动化脚本
按钮测试器: 专门用于测试页面按钮功能
元素检测器: 用于采集页面元素信息
        """
        
        info_label = ttk.Label(info_frame, text=info_text.strip(), 
                              justify=tk.LEFT, font=('Arial', 9))
        info_label.grid(row=0, column=0, sticky=tk.W)
        
        # 配置网格权重
        main_frame.rowconfigure(3, weight=1)
        
    def launch_simple_ui(self):
        """启动简洁版UI"""
        try:
            if os.path.exists('mhi_trader_simple_ui.py'):
                subprocess.Popen([sys.executable, 'mhi_trader_simple_ui.py'])
                self.root.destroy()
            else:
                messagebox.showerror("错误", "找不到简洁版UI文件: mhi_trader_simple_ui.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动简洁版UI失败: {e}")
    
    def launch_full_ui(self):
        """启动完整版UI"""
        try:
            if os.path.exists('mhi_trader_ui.py'):
                subprocess.Popen([sys.executable, 'mhi_trader_ui.py'])
                self.root.destroy()
            else:
                messagebox.showerror("错误", "找不到完整版UI文件: mhi_trader_ui.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动完整版UI失败: {e}")
    
    def launch_cmd_version(self):
        """启动命令行版本"""
        try:
            if os.path.exists('mhi_trader_test.py'):
                subprocess.Popen([sys.executable, 'mhi_trader_test.py'])
                self.root.destroy()
            else:
                messagebox.showerror("错误", "找不到命令行版本文件: mhi_trader_test.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动命令行版本失败: {e}")
    
    def launch_button_tester(self):
        """启动按钮测试器"""
        try:
            if os.path.exists('mhi_button_tester.py'):
                subprocess.Popen([sys.executable, 'mhi_button_tester.py'])
                self.root.destroy()
            else:
                messagebox.showerror("错误", "找不到按钮测试器文件: mhi_button_tester.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动按钮测试器失败: {e}")
    
    def launch_element_detector(self):
        """启动元素检测器"""
        try:
            if os.path.exists('通过点击获取网页元素.py'):
                subprocess.Popen([sys.executable, '通过点击获取网页元素.py'])
                self.root.destroy()
            else:
                messagebox.showerror("错误", "找不到元素检测器文件: 通过点击获取网页元素.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动元素检测器失败: {e}")

def main():
    """主函数"""
    root = tk.Tk()
    app = MHIStarter(root)
    root.mainloop()

if __name__ == "__main__":
    main()
