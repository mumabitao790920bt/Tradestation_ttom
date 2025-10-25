#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC交互式元素检测器
功能：用户手动点击页面元素，程序实时捕捉并记录到对照表
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import json
import os
from datetime import datetime
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('mexc_element_detector.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class InteractiveElementDetector:
    def __init__(self, root):
        self.root = root
        self.root.title("交互式元素检测器（MHI页面）")
        self.root.geometry("1000x700")
        self.root.configure(bg='#1e1e1e')
        
        # 检测状态
        self.is_detecting = False
        self.detection_thread = None
        
        # 元素对照表
        self.element_map = {}
        
        # Selenium驱动
        self.driver = None
        self.wait = None

        # Cookies
        self.cookies = []
        self.cookie_header = ""
        # Browser config
        self.chrome_binary = None
        self.user_data_dir = None
        self.profile_directory = None
        self.debugger_address = None
        
        # 创建界面
        self.create_interface()
        
        # 加载已有对照表
        self.load_element_map()
        # 预加载 Cookie（若存在）
        self.load_cookie_config()
        
    def create_interface(self):
        """创建主界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(main_frame, text="交互式元素检测器（MHI页面）", 
                               font=('Arial', 16, 'bold'))
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 左侧控制面板
        self.create_control_panel(main_frame)
        
        # 右侧检测面板
        self.create_detection_panel(main_frame)
        
        # 底部日志面板
        self.create_log_panel(main_frame)
        
    def create_control_panel(self, parent):
        """创建控制面板"""
        control_frame = ttk.LabelFrame(parent, text="控制面板", padding="10")
        control_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # 浏览器控制
        browser_frame = ttk.Frame(control_frame)
        browser_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(browser_frame, text="启动浏览器", 
                  command=self.start_browser).grid(row=0, column=0, padx=5)
        ttk.Button(browser_frame, text="关闭浏览器", 
                  command=self.close_browser).grid(row=0, column=1, padx=5)
        
        # 检测控制
        detection_frame = ttk.Frame(control_frame)
        detection_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)
        
        # 元素名称输入
        ttk.Label(detection_frame, text="元素名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.element_name_var = tk.StringVar()
        element_name_entry = ttk.Entry(detection_frame, textvariable=self.element_name_var, width=20)
        element_name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(5, 0))
        
        # 开始检测按钮
        self.detect_btn = ttk.Button(detection_frame, text="开始检测", 
                                    command=self.toggle_detection)
        self.detect_btn.grid(row=1, column=0, columnspan=2, pady=10)
        
        # 停止检测按钮
        ttk.Button(detection_frame, text="停止检测", 
                  command=self.stop_detection).grid(row=2, column=0, columnspan=2, pady=5)
        
        # 保存对照表按钮
        ttk.Button(detection_frame, text="保存对照表", 
                  command=self.save_element_map).grid(row=3, column=0, columnspan=2, pady=5)
        
        # 清空对照表按钮
        ttk.Button(detection_frame, text="清空对照表", 
                  command=self.clear_element_map).grid(row=4, column=0, columnspan=2, pady=5)
        
        # 预设元素名称
        preset_frame = ttk.LabelFrame(control_frame, text="预设元素名称", padding="5")
        preset_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)
        
        preset_elements = [
            "Open标签", "Close标签", "Limit标签", "Market标签",
            "价格输入框", "数量输入框", "Open Long按钮", "Open Short按钮",
            "Close Long按钮", "Close Short按钮", "持仓标签", "委托标签"
        ]
        
        for i, element in enumerate(preset_elements):
            btn = ttk.Button(preset_frame, text=element, 
                           command=lambda e=element: self.set_element_name(e))
            btn.grid(row=i//2, column=i%2, sticky=(tk.W, tk.E), padx=2, pady=2)
        
        # 配置网格权重
        detection_frame.columnconfigure(1, weight=1)
        preset_frame.columnconfigure(0, weight=1)
        preset_frame.columnconfigure(1, weight=1)
        
    def create_detection_panel(self, parent):
        """创建检测面板"""
        detection_frame = ttk.LabelFrame(parent, text="检测结果", padding="10")
        detection_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 当前检测状态
        status_frame = ttk.Frame(detection_frame)
        status_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(status_frame, text="检测状态:").grid(row=0, column=0, sticky=tk.W)
        self.status_label = ttk.Label(status_frame, text="未开始", foreground="red")
        self.status_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 当前检测元素
        current_frame = ttk.Frame(detection_frame)
        current_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(current_frame, text="当前检测:").grid(row=0, column=0, sticky=tk.W)
        self.current_element_label = ttk.Label(current_frame, text="无", foreground="blue")
        self.current_element_label.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        
        # 检测到的元素信息
        info_frame = ttk.LabelFrame(detection_frame, text="元素信息", padding="5")
        info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        self.element_info_text = scrolledtext.ScrolledText(info_frame, height=15, width=50)
        self.element_info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 对照表显示
        map_frame = ttk.LabelFrame(detection_frame, text="元素对照表", padding="5")
        map_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)
        
        # 创建Treeview显示对照表
        columns = ('元素名称', '标签', 'ID', 'Class', '文本')
        self.map_tree = ttk.Treeview(map_frame, columns=columns, show='headings', height=8)
        
        for col in columns:
            self.map_tree.heading(col, text=col)
            self.map_tree.column(col, width=100)
        
        self.map_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        detection_frame.columnconfigure(0, weight=1)
        detection_frame.rowconfigure(2, weight=1)
        detection_frame.rowconfigure(3, weight=1)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        map_frame.columnconfigure(0, weight=1)
        map_frame.rowconfigure(0, weight=1)
        
    def create_log_panel(self, parent):
        """创建日志面板"""
        log_frame = ttk.LabelFrame(parent, text="检测日志", padding="10")
        log_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, width=100)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(2, weight=1)
        
    def log_message(self, message):
        """添加日志消息"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        logging.info(message)
        
    def start_browser(self):
        """启动浏览器"""
        try:
            if self.driver:
                self.log_message("浏览器已在运行")
                return
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            # 兼容性考虑：移除部分实验配置，避免旧驱动报错
            # chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            # chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            # chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # 场景0：附着到已打开的Chrome（需要先用 --remote-debugging-port 启动）
            TARGET_URL = "https://fk.crkpk.com/trade/MHI"

            if self.debugger_address:
                chrome_options.add_experimental_option("debuggerAddress", self.debugger_address)
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, 15)
                # 优先复用当前已打开的页签；仅当不在目标域时再跳转
                try:
                    current_url = self.driver.current_url or ""
                except Exception:
                    current_url = ""
                if "fk.crkpk.com" not in current_url:
                    self.driver.get(TARGET_URL)
                    time.sleep(2)
                    self.log_message(f"已附着到现有Chrome调试端口 {self.debugger_address} 并打开目标页")
                else:
                    self.log_message(f"已附着到现有Chrome调试端口 {self.debugger_address}，复用当前已登录页面: {current_url}")
                self.status_label.config(text="已连接", foreground="green")
                return
            
            # 复用已登录的用户数据（若提供）
            use_profile = False
            if self.chrome_binary and os.path.exists(self.chrome_binary):
                chrome_options.binary_location = self.chrome_binary
            elif os.path.exists(r"C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"):
                chrome_options.binary_location = r"C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            
            if self.user_data_dir and os.path.exists(self.user_data_dir):
                chrome_options.add_argument(f"--user-data-dir={self.user_data_dir}")
                use_profile = True
            else:
                default_user_data = r"C:\\Users\\Administrator\\AppData\\Local\\Google\\Chrome\\User Data"
                if os.path.exists(default_user_data):
                    chrome_options.add_argument(f"--user-data-dir={default_user_data}")
                    use_profile = True
            
            # 仅当明确提供 profile_directory 时才追加该参数
            if self.profile_directory:
                chrome_options.add_argument(f"--profile-directory={self.profile_directory}")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.wait = WebDriverWait(self.driver, 15)
            
            # 场景1：复用已登录用户数据，直接打开目标页
            if use_profile:
                self.driver.get(TARGET_URL)
                time.sleep(3)
                self.log_message("已使用用户数据目录启动Chrome并打开目标交易页面（不清Cookie、不注入Cookie）")
                self.status_label.config(text="已连接", foreground="green")
                return

            # 场景2：无用户数据目录，使用Cookie注入
            for init_url in [
                "https://fk.crkpk.com",
                "https://crkpk.com",
                "https://weex.com",
                "https://www.weex.com",
            ]:
                try:
                    self.driver.get(init_url)
                    time.sleep(2)
                except Exception:
                    pass

            # 清除现有cookie避免冲突
            try:
                self.driver.delete_all_cookies()
            except Exception:
                pass

            # 注入 Cookie（如果存在）到 fk.crkpk.com / crkpk.com / weex.com / www.weex.com
            injected = 0
            for domain in ['fk.crkpk.com', 'crkpk.com', 'weex.com', 'www.weex.com']:
                try:
                    scheme = 'https'
                    # 在切换域前先跳转一次，确保 add_cookie 域匹配
                    self.driver.get(f"{scheme}://{domain}")
                    time.sleep(0.6)
                except Exception:
                    pass
                for cookie in self.cookies:
                    try:
                        if isinstance(cookie, dict) and 'name' in cookie and 'value' in cookie:
                            name = cookie.get('name', '')
                            value = cookie.get('value', '')
                            cookie_dict = {
                                'name': name,
                                'value': value,
                                'domain': domain,
                                'path': '/',
                                'secure': True,
                                'httpOnly': False,
                            }
                            self.driver.add_cookie(cookie_dict)
                            injected += 1
                    except Exception as e:
                        self.log_message(f"注入Cookie失败({domain}): {e}")

            if injected:
                self.log_message(f"已注入 {injected} 条Cookie到目标域集合")
            else:
                self.log_message("未发现可用Cookie，可能需要先登录并保存")

            self.driver.get(TARGET_URL)
            time.sleep(3)
            self.driver.refresh()
            time.sleep(2)
            
            self.log_message("浏览器启动成功，已打开目标交易页面")
            self.status_label.config(text="已连接", foreground="green")
            
        except Exception as e:
            self.log_message(f"启动浏览器失败: {e}")
            messagebox.showerror("错误", f"启动浏览器失败: {e}")
            
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.log_message("浏览器已关闭")
                self.status_label.config(text="未连接", foreground="red")
        except Exception as e:
            self.log_message(f"关闭浏览器失败: {e}")
    
    def load_cookie_config(self):
        """加载Cookie配置（优先raw header，其次JSON），并尝试读取 weex_browser_config.json"""
        try:
            # 读取浏览器配置（可选）
            try:
                cfg_file = 'weex_browser_config.json'
                if os.path.exists(cfg_file):
                    with open(cfg_file, 'r', encoding='utf-8') as f:
                        cfg = json.load(f) or {}
                    self.chrome_binary = cfg.get('chrome_binary') or None
                    self.user_data_dir = cfg.get('user_data_dir') or None
                    self.profile_directory = cfg.get('profile_directory') or None
                    self.debugger_address = cfg.get('debugger_address') or None
                    self.log_message(f"已加载浏览器配置: binary={self.chrome_binary or ''}, user_data_dir={self.user_data_dir or ''}, profile={self.profile_directory or ''}, debug={self.debugger_address or ''}")
            except Exception as e:
                self.log_message(f"读取浏览器配置失败: {e}")
            
            # 1) 优先读取原始Header文件（用户可直接粘贴浏览器Cookie头）
            header_file = 'weex_cookie_header.txt'
            if os.path.exists(header_file):
                with open(header_file, 'r', encoding='utf-8') as f:
                    self.cookie_header = f.read().strip()
                self.log_message(f"Cookie原始头已加载：{header_file}")
                # 解析为 name=value 列表
                parsed = []
                for part in self.cookie_header.split(';'):
                    if '=' in part:
                        name, value = part.split('=', 1)
                        parsed.append({'name': name.strip(), 'value': value.strip()})
                self.cookies = parsed
                return
            
            # 2) 兼容旧的JSON文件（若存在则使用）
            if os.path.exists('mexc_cookies.json'):
                with open('mexc_cookies.json', 'r', encoding='utf-8') as f:
                    self.cookies = json.load(f)
                self.log_message("Cookie配置已加载：mexc_cookies.json")
            else:
                self.cookies = []
                self.log_message("未找到 weex_cookie_header.txt 或 mexc_cookies.json，将以未登录方式打开页面")
        except Exception as e:
            self.cookies = []
            self.log_message(f"加载Cookie失败: {e}")
            
    def set_element_name(self, name):
        """设置元素名称"""
        self.element_name_var.set(name)
        self.log_message(f"已设置元素名称: {name}")
        
    def toggle_detection(self):
        """切换检测状态"""
        if not self.is_detecting:
            self.start_detection()
        else:
            self.stop_detection()
            
    def start_detection(self):
        """开始检测"""
        if not self.driver:
            messagebox.showwarning("警告", "请先启动浏览器")
            return
            
        element_name = self.element_name_var.get().strip()
        if not element_name:
            messagebox.showwarning("警告", "请输入元素名称")
            return
            
        self.is_detecting = True
        self.detect_btn.config(text="停止检测")
        self.status_label.config(text="检测中", foreground="green")
        self.current_element_label.config(text=element_name)
        
        self.detection_thread = threading.Thread(target=self.detection_worker, daemon=True)
        self.detection_thread.start()
        
        self.log_message(f"开始检测元素: {element_name}")
        self.log_message("请在浏览器中点击要检测的元素...")
        
    def stop_detection(self):
        """停止检测"""
        self.is_detecting = False
        self.detect_btn.config(text="开始检测")
        self.status_label.config(text="已停止", foreground="red")
        self.current_element_label.config(text="无")
        self.log_message("停止检测")
        
    def detection_worker(self):
        """检测工作线程"""
        try:
            # 注入JavaScript来监听点击事件
            js_code = """
            // 移除之前的监听器
            if (window.elementClickHandler) {
                document.removeEventListener('click', window.elementClickHandler, true);
            }
            
            // 创建新的点击监听器
            window.elementClickHandler = function(event) {
                // 不阻止默认行为，让标签正常切换
                // event.preventDefault();
                // event.stopPropagation();
                
                const element = event.target;
                const rect = element.getBoundingClientRect();
                
                // 收集元素信息
                const elementInfo = {
                    tagName: element.tagName,
                    id: element.id || '',
                    className: element.className || '',
                    textContent: element.textContent ? element.textContent.trim().substring(0, 100) : '',
                    innerHTML: element.innerHTML ? element.innerHTML.trim().substring(0, 200) : '',
                    outerHTML: element.outerHTML ? element.outerHTML.trim().substring(0, 300) : '',
                    attributes: {},
                    boundingRect: {
                        top: rect.top,
                        left: rect.left,
                        width: rect.width,
                        height: rect.height
                    },
                    xpath: getXPath(element),
                    cssPath: getCSSPath(element)
                };
                
                // 收集所有属性
                for (let attr of element.attributes) {
                    elementInfo.attributes[attr.name] = attr.value;
                }
                
                // 发送到Python
                window.lastClickedElement = elementInfo;
                console.log('元素已捕获:', elementInfo);
                
                // 高亮元素
                element.style.outline = '3px solid #ff0000';
                element.style.outlineOffset = '2px';
                setTimeout(() => {
                    element.style.outline = '';
                    element.style.outlineOffset = '';
                }, 2000);
            };
            
            // 生成XPath
            function getXPath(element) {
                if (element.id !== '') {
                    return 'id("' + element.id + '")';
                }
                if (element === document.body) {
                    return element.tagName;
                }
                
                var ix = 0;
                var siblings = element.parentNode.childNodes;
                for (var i = 0; i < siblings.length; i++) {
                    var sibling = siblings[i];
                    if (sibling === element) {
                        return getXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                    }
                    if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                        ix++;
                    }
                }
            }
            
            // 生成CSS选择器
            function getCSSPath(element) {
                if (element.id) {
                    return '#' + element.id;
                }
                if (element === document.body) {
                    return 'body';
                }
                
                var path = [];
                while (element && element.nodeType === 1) {
                    var selector = element.nodeName.toLowerCase();
                    if (element.className) {
                        selector += '.' + element.className.split(' ').join('.');
                    }
                    path.unshift(selector);
                    element = element.parentNode;
                }
                return path.join(' > ');
            }
            
            // 添加监听器
            document.addEventListener('click', window.elementClickHandler, true);
            
            return '点击监听器已启动';
            """
            
            # 执行JavaScript
            result = self.driver.execute_script(js_code)
            self.log_message(f"JavaScript注入结果: {result}")
            
            # 循环检测点击
            while self.is_detecting:
                try:
                    # 检查是否有新点击的元素
                    element_info = self.driver.execute_script("return window.lastClickedElement;")
                    
                    if element_info:
                        # 清除已检测的元素
                        self.driver.execute_script("window.lastClickedElement = null;")
                        
                        # 处理检测到的元素
                        self.handle_detected_element(element_info)
                        
                        # 停止检测
                        self.stop_detection()
                        break
                        
                except Exception as e:
                    self.log_message(f"检测循环错误: {e}")
                    
                time.sleep(0.1)  # 100ms检查一次
                
        except Exception as e:
            self.log_message(f"检测工作线程错误: {e}")
            self.stop_detection()
            
    def handle_detected_element(self, element_info):
        """处理检测到的元素"""
        try:
            element_name = self.element_name_var.get().strip()
            
            # 创建元素记录
            element_record = {
                'name': element_name,
                'tag': element_info.get('tagName', ''),
                'id': element_info.get('id', ''),
                'class': element_info.get('className', ''),
                'text': element_info.get('textContent', ''),
                'xpath': element_info.get('xpath', ''),
                'cssPath': element_info.get('cssPath', ''),
                'attributes': element_info.get('attributes', {}),
                'boundingRect': element_info.get('boundingRect', {}),
                'timestamp': datetime.now().isoformat()
            }
            
            # 添加到对照表
            self.element_map[element_name] = element_record
            
            # 更新界面显示
            self.root.after(0, self.update_element_display, element_record)
            
            self.log_message(f"成功检测到元素: {element_name}")
            self.log_message(f"标签: {element_record['tag']}")
            self.log_message(f"ID: {element_record['id']}")
            self.log_message(f"Class: {element_record['class']}")
            self.log_message(f"文本: {element_record['text']}")
            self.log_message(f"XPath: {element_record['xpath']}")
            self.log_message(f"CSS Path: {element_record['cssPath']}")
            
        except Exception as e:
            self.log_message(f"处理检测元素失败: {e}")
            
    def update_element_display(self, element_record):
        """更新元素显示"""
        # 清空信息显示
        self.element_info_text.delete(1.0, tk.END)
        
        # 显示元素信息
        info_text = f"""元素名称: {element_record['name']}
标签: {element_record['tag']}
ID: {element_record['id']}
Class: {element_record['class']}
文本: {element_record['text']}
XPath: {element_record['xpath']}
CSS Path: {element_record['cssPath']}

属性:
"""
        for attr_name, attr_value in element_record['attributes'].items():
            info_text += f"  {attr_name}: {attr_value}\n"
            
        info_text += f"""
位置信息:
  上: {element_record['boundingRect'].get('top', 0)}
  左: {element_record['boundingRect'].get('left', 0)}
  宽: {element_record['boundingRect'].get('width', 0)}
  高: {element_record['boundingRect'].get('height', 0)}
"""
        
        self.element_info_text.insert(tk.END, info_text)
        
        # 更新对照表显示
        self.update_map_display()
        
    def update_map_display(self):
        """更新对照表显示"""
        # 清空现有数据
        for item in self.map_tree.get_children():
            self.map_tree.delete(item)
            
        # 添加对照表数据
        for name, record in self.element_map.items():
            self.map_tree.insert('', 'end', values=(
                record['name'],
                record['tag'],
                record['id'],
                record['class'],
                record['text'][:50] + '...' if len(record['text']) > 50 else record['text']
            ))
            
    def save_element_map(self):
        """保存对照表"""
        try:
            # 使用固定的文件名，覆盖现有文件
            filename = "mexc_element_map_1757729194.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.element_map, f, ensure_ascii=False, indent=2)
            self.log_message(f"对照表已保存到: {filename}")
            self.log_message(f"保存了 {len(self.element_map)} 个元素")
            messagebox.showinfo("成功", f"对照表已保存到: {filename}")
        except Exception as e:
            self.log_message(f"保存对照表失败: {e}")
            messagebox.showerror("错误", f"保存对照表失败: {e}")
            
    def load_element_map(self):
        """加载对照表"""
        try:
            # 直接加载固定文件名
            filename = "mexc_element_map_1757729194.json"
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    self.element_map = json.load(f)
                self.log_message(f"已加载对照表: {filename}")
                self.log_message(f"加载了 {len(self.element_map)} 个元素")
                self.update_map_display()
            else:
                self.log_message(f"未找到对照表文件: {filename}，将创建新的对照表")
        except Exception as e:
            self.log_message(f"加载对照表失败: {e}")
            
    def clear_element_map(self):
        """清空对照表"""
        if messagebox.askyesno("确认", "确定要清空对照表吗？"):
            self.element_map = {}
            self.update_map_display()
            self.element_info_text.delete(1.0, tk.END)
            self.log_message("对照表已清空")

def main():
    """主函数"""
    root = tk.Tk()
    app = InteractiveElementDetector(root)
    
    # 设置窗口关闭事件
    def on_closing():
        if app.is_detecting:
            app.stop_detection()
        if app.driver:
            app.close_browser()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()
