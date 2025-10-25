#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
K10 主界面 - 界面层
只负责UI界面的创建和显示，具体功能由modules实现
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
from datetime import datetime
import threading
import time
from data_transfer import get_data_transfer
import pymysql

# 导入modules（使用英文模块名，避免中文导入问题）
try:
    from jd_alliance import JDAllianceService
    from multi_platform_search import MultiPlatformSearchService
except ImportError as e:
    print(f"导入modules失败: {e}")
    # 创建模拟服务
    class MockService:
        def __init__(self):
            pass
        def open_jd_alliance(self, port_var):
            messagebox.showinfo("提示", "京东联盟选品modules未找到")
        def open_multi_search(self):
            messagebox.showinfo("提示", "多平台一键搜索modules未找到")
    
    JDAllianceService = MockService
    MultiPlatformSearchService = MockService

# 导入其他必要的模块
try:
    from jd_service import jd_service
except ImportError:
    class MockJDService:
        def __init__(self):
            self.current_port = None
        def allocate_port(self, port_type="random"):
            return 8080
        def get_jd_alliance_url(self, port=None):
            return "https://union.jd.com/"
        def log_access(self, port, url, action="access"):
            print(f"访问日志: {action} - 端口: {port}, URL: {url}")
    
    jd_service = MockJDService()

def check_remote_authorization():
    """检查远程授权"""
    try:
        db_config = {
            'host': '115.159.44.226',
            'port': 3306,
            'user': 'xianyu',
            'password': 'zxz2jwwRTYmMkpyT',
            'database': 'xianyu',
            'charset': 'utf8mb4'
        }
        conn = pymysql.connect(**db_config)
        cursor = conn.cursor()
        query = "SELECT COUNT(*) FROM xianyu_account WHERE phone = 'tdx_sjjk_yha'"
        cursor.execute(query)
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        return result[0] > 0
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")
        return False

class JingdongTool:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("K10")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f8ff')
        
        # 初始化功能服务
        self.jd_alliance_service = JDAllianceService()
        self.multi_search_service = MultiPlatformSearchService()
        
        # 设置窗口图标和样式
        self.setup_styles()
        
        # 创建主界面
        self.create_main_interface()
        
    def setup_styles(self):
        """设置界面样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 自定义样式
        style.configure('Purple.TFrame', background='#8B5A9B')
        style.configure('Blue.TButton', background='#4A90E2', foreground='white')
        style.configure('Green.TButton', background='#4CAF50', foreground='white')
        style.configure('Grey.TButton', background='#9E9E9E', foreground='white')
        
    def create_main_interface(self):
        """创建主界面"""
        # 顶部栏
        self.create_top_bar()
        
        # 主容器
        main_container = tk.Frame(self.root, bg='#f0f8ff')
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 左侧导航栏
        self.create_left_sidebar(main_container)
        
        # 右侧主内容区
        self.create_right_content(main_container)
        
    def create_top_bar(self):
        """创建顶部栏"""
        top_bar = tk.Frame(self.root, bg='#4A90E2', height=50)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # 左侧标题
        title_label = tk.Label(top_bar, text="K10", font=('Arial', 16, 'bold'), 
                             bg='#4A90E2', fg='white')
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # 右侧用户信息
        user_info = tk.Label(top_bar, 
                           text="尊敬的内部用户 111 您的通用剩余点数为:「66666666 K10点 仅供参考,云端用量为准」",
                           font=('Arial', 10), bg='#4A90E2', fg='white')
        user_info.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # 充值按钮
        recharge_btn = tk.Button(top_bar, text="[充值]", font=('Arial', 10),
                               bg='#FF6B6B', fg='white', relief=tk.FLAT)
        recharge_btn.pack(side=tk.RIGHT, padx=10, pady=10)
        
    def create_left_sidebar(self, parent):
        """创建左侧导航栏"""
        sidebar = tk.Frame(parent, bg='#2C3E50', width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)
        
        # K10标题
        k10_title = tk.Label(sidebar, text="K10", font=('Arial', 18, 'bold'),
                           bg='#2C3E50', fg='white')
        k10_title.pack(pady=20)
        
        # 导航菜单
        nav_items = [
            ("首页", "🏠"),
            ("京东项目", "🔑", True),  # 当前选中
            ("淘宝项目", "🔑"),
            ("视频号项目", "🔒"),
            ("抖音项目", "🔒"),
            ("快手项目", "🔒")
        ]
        
        for item in nav_items:
            if len(item) == 3:  # 带选中状态
                text, icon, selected = item
                bg_color = '#3498DB' if selected else '#2C3E50'
                fg_color = 'white'
            else:
                text, icon = item
                bg_color = '#2C3E50'
                fg_color = '#BDC3C7'
            
            nav_btn = tk.Button(sidebar, text=f"{icon} {text}", 
                              font=('Arial', 12), bg=bg_color, fg=fg_color,
                              relief=tk.FLAT, anchor=tk.W, width=20)
            nav_btn.pack(pady=5, padx=10, fill=tk.X)
        
        # 常用工具标题
        tools_title = tk.Label(sidebar, text="常用工具", font=('Arial', 12, 'bold'),
                              bg='#2C3E50', fg='#BDC3C7')
        tools_title.pack(pady=(30, 10), padx=10, anchor=tk.W)
        
        # 常用工具按钮
        self.create_tools_section(sidebar)
        
        # 用户信息
        user_frame = tk.Frame(sidebar, bg='#2C3E50')
        user_frame.pack(pady=20, padx=10, fill=tk.X)
        
        user_icon = tk.Label(user_frame, text="🐱", font=('Arial', 20),
                           bg='#2C3E50', fg='white')
        user_icon.pack()
        
        user_label = tk.Label(user_frame, text="用户: 111 内部用户", 
                            font=('Arial', 10), bg='#2C3E50', fg='#BDC3C7')
        user_label.pack()
        
        # 版本号
        version_label = tk.Label(sidebar, text="Ver 2.1.1", 
                               font=('Arial', 10), bg='#2C3E50', fg='#BDC3C7')
        version_label.pack(side=tk.BOTTOM, pady=20)
        
    def create_right_content(self, parent):
        """创建右侧主内容区"""
        content_frame = tk.Frame(parent, bg='white')
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 紫色横幅区域
        self.create_purple_banner(content_frame)
        
        # 配置和操作区域
        self.create_config_section(content_frame)
        
        # 发布设置区域
        self.create_publish_settings(content_frame)
        
        # 数据表格区域
        self.create_data_table(content_frame)
        
    def create_purple_banner(self, parent):
        """创建紫色横幅区域"""
        banner_frame = tk.Frame(parent, bg='#8B5A9B', height=200)
        banner_frame.pack(fill=tk.X, pady=(0, 20))
        banner_frame.pack_propagate(False)
        
        # 横幅内容
        banner_content = tk.Frame(banner_frame, bg='#8B5A9B')
        banner_content.pack(expand=True, fill=tk.BOTH, padx=30, pady=20)
        
        # 左侧文字内容
        text_frame = tk.Frame(banner_content, bg='#8B5A9B')
        text_frame.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        
        main_title = tk.Label(text_frame, text="京东 - 逛频道", 
                            font=('Arial', 24, 'bold'), bg='#8B5A9B', fg='white')
        main_title.pack(anchor=tk.W, pady=(0, 10))
        
        subtitle = tk.Label(text_frame, text="多模态拟人工自动发布(4.0AI版)", 
                          font=('Arial', 16), bg='#8B5A9B', fg='white')
        subtitle.pack(anchor=tk.W, pady=(0, 20))
        
        desc_texts = [
            "(稳定输出才是变现的不二法门,安全无痛的发布方式)",
            "(多个京东账号,软件允许多开,请使用不同端口,每个窗口单独计费)",
            "(单个视频成功发布消耗 8 K10点,失败不扣点。)"
        ]
        
        for desc in desc_texts:
            desc_label = tk.Label(text_frame, text=desc, font=('Arial', 12),
                                bg='#8B5A9B', fg='white')
            desc_label.pack(anchor=tk.W, pady=2)
        
        # 右侧按钮
        button_frame = tk.Frame(banner_content, bg='#8B5A9B')
        button_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        
        jd_btn = tk.Button(button_frame, text="前往京东联盟选品>", 
                          font=('Arial', 12), bg='#4A90E2', fg='white',
                          relief=tk.FLAT, padx=20, pady=10,
                          command=self.open_jd_alliance)
        jd_btn.pack(pady=10)
        
        tutorial_btn = tk.Button(button_frame, text="项目教学>>", 
                               font=('Arial', 12), bg='#8B5A9B', fg='white',
                               relief=tk.FLAT, padx=20, pady=10)
        tutorial_btn.pack(pady=10)
        
    def create_config_section(self, parent):
        """创建配置和操作区域"""
        config_frame = tk.Frame(parent, bg='white')
        config_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 京东端口设置
        port_frame = tk.Frame(config_frame, bg='white')
        port_frame.pack(fill=tk.X, pady=10)
        
        port_label = tk.Label(port_frame, text="(固定端口可记录登录信息,避免每次登录都要手机验证)当前京东端口为:", 
                            font=('Arial', 10), bg='white')
        port_label.pack(side=tk.LEFT, padx=(0, 10))
        
        self.port_var = tk.StringVar(value="随机端口")
        port_combo = ttk.Combobox(port_frame, textvariable=self.port_var, 
                                 values=["随机端口", "8080", "8081", "8082"], width=15)
        port_combo.pack(side=tk.LEFT, padx=(0, 10))
        
        remark_label = tk.Label(port_frame, text="备注", font=('Arial', 10), bg='white')
        remark_label.pack(side=tk.LEFT, padx=(20, 5))
        
        remark_entry = tk.Entry(port_frame, width=20)
        remark_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        confirm_btn = tk.Button(port_frame, text="确定", font=('Arial', 10),
                               bg='#4A90E2', fg='white', relief=tk.FLAT,
                               command=self.confirm_port)
        confirm_btn.pack(side=tk.LEFT)
        
        # 添加端口状态显示
        self.port_status_label = tk.Label(port_frame, text="", font=('Arial', 9), 
                                        bg='white', fg='#666')
        self.port_status_label.pack(side=tk.LEFT, padx=(10, 0))
        
        # 右侧操作按钮
        action_frame = tk.Frame(config_frame, bg='white')
        action_frame.pack(fill=tk.X, pady=10)
        
        # 第一行按钮
        row1_frame = tk.Frame(action_frame, bg='white')
        row1_frame.pack(fill=tk.X, pady=5)
        
        login_btn = tk.Button(row1_frame, text="登录[京东创作者平台]", 
                            font=('Arial', 10), bg='#9E9E9E', fg='white',
                            relief=tk.FLAT, padx=15, pady=5)
        login_btn.pack(side=tk.RIGHT, padx=5)
        
        folder_btn = tk.Button(row1_frame, text="选择[视频文件夹]", 
                             font=('Arial', 10), bg='#4A90E2', fg='white',
                             relief=tk.FLAT, padx=15, pady=5)
        folder_btn.pack(side=tk.RIGHT, padx=5)
        
        # 第二行按钮和开关
        row2_frame = tk.Frame(action_frame, bg='white')
        row2_frame.pack(fill=tk.X, pady=5)
        
        random_switch = tk.Checkbutton(row2_frame, text="[导入视频时随机打乱]", 
                                     font=('Arial', 10), bg='white', selectcolor='#4A90E2')
        random_switch.select()  # 默认选中
        random_switch.pack(side=tk.RIGHT, padx=5)
        
        start_btn = tk.Button(row2_frame, text="开始自动发布", 
                            font=('Arial', 12, 'bold'), bg='#4CAF50', fg='white',
                            relief=tk.FLAT, padx=20, pady=8)
        start_btn.pack(side=tk.RIGHT, padx=5)
        
        # 第三行开关
        row3_frame = tk.Frame(action_frame, bg='white')
        row3_frame.pack(fill=tk.X, pady=5)
        
        sync_switch = tk.Checkbutton(row3_frame, text="[同步修改失败作品]", 
                                   font=('Arial', 10), bg='white', selectcolor='#9E9E9E')
        sync_switch.pack(side=tk.RIGHT, padx=5)
        
    def create_publish_settings(self, parent):
        """创建发布设置区域"""
        settings_frame = tk.Frame(parent, bg='white')
        settings_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 发布间隔
        interval_frame = tk.Frame(settings_frame, bg='white')
        interval_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        interval_label = tk.Label(interval_frame, text="发布间隔", font=('Arial', 10), bg='white')
        interval_label.pack(side=tk.LEFT)
        
        interval_entry = tk.Entry(interval_frame, width=5, textvariable=tk.StringVar(value="5"))
        interval_entry.pack(side=tk.LEFT, padx=(5, 5))
        
        interval_unit = tk.Label(interval_frame, text="s (秒)", font=('Arial', 10), bg='white')
        interval_unit.pack(side=tk.LEFT)
        
        # 其他开关设置
        switches = [
            ("[同时挂载全部商品SKU]", True, '#4A90E2'),
            ("[不选择标签]", False, '#9E9E9E'),
            ("[开启自动滑块验证]", True, '#4A90E2'),
            ("[第一帧为封面]", True, '#4A90E2')
        ]
        
        for text, default, color in switches:
            switch = tk.Checkbutton(settings_frame, text=text, font=('Arial', 10),
                                  bg='white', selectcolor=color)
            if default:
                switch.select()
            switch.pack(side=tk.LEFT, padx=10)
        
    def create_data_table(self, parent):
        """创建数据表格区域"""
        table_frame = tk.Frame(parent, bg='white')
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # 表格标题
        table_title = tk.Label(table_frame, text="内容管理", font=('Arial', 14, 'bold'), bg='white')
        table_title.pack(anchor=tk.W, pady=(0, 10))
        
        # 创建表格
        columns = ('序号', '视频标题', '发布日期', '状态', '封面地址', '操作')
        
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=15)
        
        # 设置列标题
        column_headers = [
            ('序号', '📄'),
            ('视频标题', '🎥'),
            ('发布日期', '📅'),
            ('状态', '🔄'),
            ('封面地址', '🖼️'),
            ('操作', '🔧')
        ]
        
        for col, header in zip(columns, column_headers):
            tree.heading(col, text=f"{header[1]} {header[0]}")
            tree.column(col, width=200, anchor=tk.CENTER)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        # 放置表格和滚动条
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def create_tools_section(self, parent):
        """创建常用工具区域"""
        tools_frame = tk.Frame(parent, bg='#2C3E50')
        tools_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 工具按钮列表（显示中文，内部调用英文路径）
        tools = [
            ("抖音搜索", "🎵", self.open_douyin_downloader),
            ("快手搜索", "⚡", self.open_kuaishou_downloader),
            ("视频合成", "🎬", self.open_video_synthesis),
            ("京东视频自动上传", "⬆️", self.open_jd_auto_uploader)
        ]
        
        for text, icon, command in tools:
            tool_btn = tk.Button(tools_frame, text=f"{icon} {text}", 
                               font=('Arial', 10), bg='#34495E', fg='white',
                               relief=tk.FLAT, anchor=tk.W, width=25,
                               command=command)
            tool_btn.pack(pady=2, fill=tk.X)
            
            # 添加鼠标悬停效果
            tool_btn.bind('<Enter>', lambda e, btn=tool_btn: btn.config(bg='#3498DB'))
            tool_btn.bind('<Leave>', lambda e, btn=tool_btn: btn.config(bg='#34495E'))
        
    def open_douyin_downloader(self):
        """打开douyin_search工具"""
        try:
            # 直接导入并启动抖音搜索模块，而不是使用子进程
            from modules.douyin_search.multi_platform_search import MultiPlatformSearchService
            
            # 创建并启动抖音搜索服务
            douyin_service = MultiPlatformSearchService()
            douyin_service.open_multi_search()
            
            print("✅ 抖音搜索工具已启动")
            
        except Exception as e:
            print(f"❌ 启动抖音搜索工具失败: {e}")
            messagebox.showerror("错误", f"启动抖音搜索工具失败: {str(e)}")
    
    def open_kuaishou_downloader(self):
        """打开kuaishou_search工具"""
        try:
            import subprocess
            import os
            
            # 快手下载模块路径
            kuaishou_module_path = os.path.join(os.path.dirname(__file__), "multi_platform_search_kuaishou.py")
            
            if os.path.exists(kuaishou_module_path):
                # 设置下载路径到数据传递
                download_folder = os.path.join(os.path.dirname(__file__), "downloads")
                os.makedirs(download_folder, exist_ok=True)
                
                data_transfer = get_data_transfer()
                data_transfer.set_synthesis_input_folder(download_folder)
                data_transfer.set_module_status("kuaishou_downloader", "running")
                
                # 在新进程中启动快手下载工具
                subprocess.Popen([sys.executable, kuaishou_module_path], 
                               cwd=os.path.dirname(kuaishou_module_path))
            else:
                messagebox.showerror("错误", f"快手下载模块文件不存在:\n{kuaishou_module_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动快手下载工具失败:\n{str(e)}")
    
    def open_video_synthesis(self):
        """打开video_synthesis工具"""
        try:
            import subprocess
            import os
            
            # 视频合成模块路径
            synthesis_module_path = os.path.join(os.path.dirname(__file__), "modules", "video_synthesis", "gui_splitter.py")
            
            if os.path.exists(synthesis_module_path):
                # 设置数据传递
                data_transfer = get_data_transfer()
                data_transfer.set_module_status("video_synthesis", "running")
                
                # 在新进程中启动视频合成工具
                subprocess.Popen([sys.executable, synthesis_module_path], 
                               cwd=os.path.dirname(synthesis_module_path))
            else:
                messagebox.showerror("错误", f"视频合成模块文件不存在:\n{synthesis_module_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动视频合成工具失败:\n{str(e)}")

    def open_jd_auto_uploader(self):
        """打开京东视频自动上传工具"""
        try:
            import subprocess
            import os
            
            uploader_script_path = os.path.join(os.path.dirname(__file__), "jd_auto_uploader", "auto_click_upload_and_browse_ultimate_stealth_v3_enhanced.py")
            uploader_cwd = os.path.dirname(uploader_script_path)
            
            if os.path.exists(uploader_script_path):
                print(f"🚀 正在启动京东视频自动上传工具: {uploader_script_path}")
                subprocess.Popen([sys.executable, uploader_script_path], cwd=uploader_cwd)
                messagebox.showinfo("启动成功", "京东视频自动上传工具已在后台启动。")
            else:
                messagebox.showerror("错误", f"京东视频自动上传脚本文件不存在:\n{uploader_script_path}")
        except Exception as e:
            messagebox.showerror("错误", f"启动京东视频自动上传工具失败:\n{str(e)}")

    def open_video_downloader(self):
        """打开短视频下载工具"""
        messagebox.showinfo("工具", "全网短视频无水印下载工具\n\n功能：支持抖音、快手、B站等平台\n视频无水印下载")
        
    def open_video_editor(self):
        """打开视频剪辑助手"""
        messagebox.showinfo("工具", "视频剪辑助手\n\n功能：视频剪辑、合并、特效添加\n支持多种视频格式")
        
    def open_ocr_tool(self):
        """打开OCR字幕识别工具"""
        messagebox.showinfo("工具", "OCR字幕精准识别\n\n功能：自动识别视频中的文字\n支持多语言字幕提取")
        
    def open_video_positioning(self):
        """打开长视频画面定位工具"""
        messagebox.showinfo("工具", "长视频画面定位\n\n功能：快速定位视频中的特定画面\n支持时间轴标记")
        
    def open_multi_search(self):
        """打开多平台搜索工具"""
        self.multi_search_service.open_multi_search()
        
    def open_cloud_script(self):
        """打开云端自动化脚本工具"""
        messagebox.showinfo("工具", "云端自动化脚本\n\n功能：云端运行自动化脚本\n支持定时任务和批量操作")
        
    def open_jd_assistant(self):
        """打开京东选品助手"""
        messagebox.showinfo("工具", "京东选品助手\n\n功能：智能商品推荐\n热销商品分析\n选品策略建议")
        
    def open_jd_alliance(self):
        """打开京东联盟选品页面"""
        self.jd_alliance_service.open_jd_alliance(self.port_var)
        
    def confirm_port(self):
        """确认端口设置"""
        try:
            selected_port = self.port_var.get()
            
            if selected_port == "随机端口":
                # 使用京东服务分配随机端口
                port = jd_service.allocate_port("random")
                if port:
                    self.port_var.set(str(port))
                    selected_port = str(port)
                    messagebox.showinfo("端口设置", f"已分配随机端口: {port}")
                else:
                    messagebox.showerror("错误", "无法分配随机端口")
                    return
            else:
                # 使用京东服务分配固定端口
                port = jd_service.allocate_port(selected_port)
                if not port:
                    messagebox.showerror("错误", f"端口 {selected_port} 已被占用，请选择其他端口")
                    return
                selected_port = str(port)
            
            # 更新端口状态显示
            self.update_port_status(selected_port)
            
            # 保存端口配置
            self.save_port_config(selected_port)
            
            messagebox.showinfo("成功", f"端口设置已确认: {selected_port}")
            
        except Exception as e:
            messagebox.showerror("错误", f"端口设置失败:\n{str(e)}")
    
    def update_port_status(self, port):
        """更新端口状态显示"""
        try:
            # 使用京东服务获取端口状态
            port_status = jd_service.get_port_status(port)
            if port_status:
                status_text = f"✅ 端口 {port} 可用"
                if port_status.get("login_status"):
                    status_text += " (已登录)"
                self.port_status_label.config(text=status_text, fg='#4CAF50')
            else:
                # 检查端口是否可用
                if self.is_port_available(int(port)):
                    self.port_status_label.config(text=f"✅ 端口 {port} 可用", fg='#4CAF50')
                else:
                    self.port_status_label.config(text=f"❌ 端口 {port} 占用", fg='#F44336')
        except Exception as e:
            self.port_status_label.config(text=f"❓ 端口 {port} 状态未知", fg='#FF9800')
    
    def save_port_config(self, port):
        """保存端口配置"""
        try:
            # 保存到实例变量
            self.current_port = port
            
            # 使用京东服务更新端口状态
            if hasattr(jd_service, 'update_login_status'):
                jd_service.update_login_status(port, False)  # 初始状态为未登录
            
            print(f"端口配置已保存: {port}")
        except Exception as e:
            print(f"保存端口配置失败: {e}")
    
    def is_port_available(self, port):
        """检查端口是否可用"""
        try:
            import socket
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return True
        except OSError:
            return False
        
    def run(self):
        """运行应用程序"""
        self.root.mainloop()

if __name__ == "__main__":
    # 检查远程授权
    if not check_remote_authorization():
        print("授权验证失败，程序退出")
        sys.exit(1)
    
    print("授权验证成功，启动程序...")
    app = JingdongTool()
    app.run()
