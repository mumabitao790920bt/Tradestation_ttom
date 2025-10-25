#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易测试程序
基于致远金融MHI页面的自动化交易测试
支持模拟和实盘两种模式
"""

import time
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class MHITrader:
    def __init__(self, element_map_file="mexc_element_map_1757729194.json", log_callback=None):
        """
        初始化MHI交易器
        
        Args:
            element_map_file: 元素映射JSON文件
            log_callback: 日志回调函数
        """
        self.log = log_callback or print
        self.driver = None
        self.wait = None
        self.element_map = {}
        self.current_mode = "模拟"  # 默认模拟模式
        
        # 加载元素映射
        self.load_element_map(element_map_file)
        
        # 配置日志
        self.setup_logging()
        
    def setup_logging(self):
        """设置日志"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('mhi_trader.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        
    def load_element_map(self, filename):
        """加载元素映射"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                self.element_map = json.load(f)
            self.log(f"✅ 已加载元素映射: {len(self.element_map)} 个元素")
        except Exception as e:
            self.log(f"❌ 加载元素映射失败: {e}")
            self.element_map = {}
    
    def start_browser(self):
        """启动浏览器"""
        try:
            # 加载浏览器配置
            config = self.load_browser_config()
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 优先使用用户数据目录方式（复用已登录的浏览器）
            if config.get('user_data_dir') and config.get('chrome_binary'):
                chrome_options.binary_location = config['chrome_binary']
                chrome_options.add_argument(f"--user-data-dir={config['user_data_dir']}")
                
                if config.get('profile_directory'):
                    chrome_options.add_argument(f"--profile-directory={config['profile_directory']}")
                
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, 15)
                
                # 打开MHI交易页面
                self.driver.get("https://fk.crkpk.com/trade/MHI")
                time.sleep(3)
                
                self.log("✅ 浏览器启动成功，已使用用户数据目录（复用已登录状态）")
                return True
            
            # 备用方案：使用调试端口附着
            elif config.get('debugger_address'):
                chrome_options.add_experimental_option("debuggerAddress", config['debugger_address'])
                self.driver = webdriver.Chrome(options=chrome_options)
                self.wait = WebDriverWait(self.driver, 15)
                
                # 检查当前页面
                try:
                    current_url = self.driver.current_url or ""
                    if "fk.crkpk.com" not in current_url:
                        self.driver.get("https://fk.crkpk.com/trade/MHI")
                        time.sleep(2)
                        self.log("已跳转到MHI交易页面")
                    else:
                        self.log(f"复用当前页面: {current_url}")
                except:
                    self.driver.get("https://fk.crkpk.com/trade/MHI")
                    time.sleep(2)
                
                self.log("✅ 浏览器启动成功，已连接到调试端口")
                return True
            
            else:
                self.log("❌ 未找到有效的浏览器配置")
                return False
                
        except Exception as e:
            self.log(f"❌ 启动浏览器失败: {e}")
            return False
    
    def load_browser_config(self):
        """加载浏览器配置"""
        try:
            with open('weex_browser_config.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                self.log("✅ 浏览器已关闭")
        except Exception as e:
            self.log(f"❌ 关闭浏览器失败: {e}")
    
    def _click_element(self, element_key, description=""):
        """点击元素"""
        try:
            if element_key not in self.element_map:
                self.log(f"❌ 元素对照表中未找到'{element_key}'")
                return False
            
            element = self.driver.find_element(By.XPATH, self.element_map[element_key]['xpath'])
            element.click()
            self.log(f"✅ {description or f'已点击{element_key}'}")
            time.sleep(0.5)
            return True
        except Exception as e:
            self.log(f"❌ 点击{element_key}失败: {e}")
            return False
    
    def _input_text(self, element_key, text, description=""):
        """在输入框中输入文本"""
        try:
            if element_key not in self.element_map:
                self.log(f"❌ 元素对照表中未找到'{element_key}'")
                return False
            
            element = self.driver.find_element(By.XPATH, self.element_map[element_key]['xpath'])
            element.click()
            element.send_keys(Keys.CONTROL + "a")
            element.send_keys(Keys.DELETE)
            element.send_keys(str(text))
            self.log(f"✅ {description or f'已输入{element_key}: {text}'}")
            time.sleep(0.3)
            return True
        except Exception as e:
            self.log(f"❌ 输入{element_key}失败: {e}")
            return False
    
    def switch_mode(self, mode):
        """
        切换交易模式
        
        Args:
            mode: "模拟" 或 "实盘"
        """
        try:
            self.log(f"🔄 切换交易模式: {mode}")
            
            if mode == "模拟":
                if not self._click_element('模拟', '点击模拟模式'):
                    return False
            elif mode == "实盘":
                if not self._click_element('实盘', '点击实盘模式'):
                    return False
                # 实盘模式需要先点击市价
                time.sleep(0.1)  # 减少等待时间
                if not self._click_element('市价', '点击市价'):
                    self.log("⚠️ 点击市价失败，但继续执行")
            else:
                self.log(f"❌ 无效的交易模式: {mode}")
                return False
            
            self.current_mode = mode
            time.sleep(0.2)  # 减少等待时间
            self.log(f"✅ 已切换到{mode}模式")
            return True
            
        except Exception as e:
            self.log(f"❌ 切换模式失败: {e}")
            return False
    
    def set_order_type(self, order_type):
        """
        设置订单类型
        
        Args:
            order_type: "市价" 或 "限价"
        """
        try:
            self.log(f"🔄 设置订单类型: {order_type}")
            
            if order_type == "市价":
                if not self._click_element('市价', '点击市价'):
                    return False
            elif order_type == "限价":
                if not self._click_element('限价', '点击限价'):
                    return False
            else:
                self.log(f"❌ 无效的订单类型: {order_type}")
                return False
            
            time.sleep(0.1)  # 减少等待时间
            self.log(f"✅ 已设置{order_type}订单")
            return True
            
        except Exception as e:
            self.log(f"❌ 设置订单类型失败: {e}")
            return False
    
    def set_trading_mode(self, mode):
        """
        设置交易模式（元/角）
        
        Args:
            mode: "元" 或 "角"
        """
        try:
            self.log(f"🔄 设置交易模式: {mode}")
            
            # 根据当前模式选择对应的交易模式按钮
            if self.current_mode == "模拟":
                if mode == "元":
                    if not self._click_element('模拟_元', '点击元模式'):
                        return False
                elif mode == "角":
                    if not self._click_element('模拟_角', '点击角模式'):
                        return False
                else:
                    self.log(f"❌ 无效的交易模式: {mode}")
                    return False
            else:  # 实盘模式
                if mode == "元":
                    if not self._click_element('元', '点击元模式'):
                        return False
                elif mode == "角":
                    if not self._click_element('角', '点击角模式'):
                        return False
                else:
                    self.log(f"❌ 无效的交易模式: {mode}")
                    return False
            
            time.sleep(0.1)  # 减少等待时间
            self.log(f"✅ 已设置{mode}模式")
            return True
            
        except Exception as e:
            self.log(f"❌ 设置交易模式失败: {e}")
            return False
    
    def set_lot_size(self, lots):
        """
        设置手数
        
        Args:
            lots: 手数 (1, 2, 3, 5, 8, 10)
        """
        try:
            self.log(f"🔄 设置手数: {lots}")
            
            # 根据当前模式选择对应的手数按钮
            if self.current_mode == "模拟":
                lot_buttons = {
                    1: '模拟_数量1',
                    2: '模拟_数量2', 
                    3: '模拟_数量3',
                    5: '模拟_数量4',  # 5手对应数量4
                    8: '模拟_数量5',  # 8手对应数量5
                    10: '模拟_数量6'  # 10手对应数量6
                }
            else:  # 实盘模式
                lot_buttons = {
                    1: '数量1',
                    2: '数量2', 
                    3: '数量3',
                    5: '数量4',  # 5手对应数量4
                    8: '数量5',  # 8手对应数量5
                    10: '数量6'  # 10手对应数量6
                }
            
            if lots not in lot_buttons:
                self.log(f"❌ 无效的手数: {lots}")
                return False
            
            if not self._click_element(lot_buttons[lots], f'点击{lots}手'):
                return False
            
            time.sleep(0.1)  # 减少等待时间
            self.log(f"✅ 已设置{lots}手")
            return True
            
        except Exception as e:
            self.log(f"❌ 设置手数失败: {e}")
            return False
    
    def set_margin(self, margin):
        """
        设置保证金
        
        Args:
            margin: 保证金金额 (2700, 4050, 5850, 8100)
        """
        try:
            # 将保证金金额转换为档位显示
            margin_display = {
                2700: "一档",
                4050: "二档", 
                5850: "三档",
                8100: "四档"
            }
            margin_text = margin_display.get(margin, f"{margin}")
            
            self.log(f"🔄 设置保证金: {margin_text}({margin})")
            
            # 根据当前模式选择对应的保证金按钮
            if self.current_mode == "模拟":
                margin_buttons = {
                    2700: '模拟_保证金1',
                    4050: '模拟_保证金2',
                    5850: '模拟_保证金3', 
                    8100: '模拟_保证金4'
                }
            else:  # 实盘模式
                margin_buttons = {
                    2700: '保证金1',
                    4050: '保证金2',
                    5850: '保证金3', 
                    8100: '保证金4'
                }
            
            if margin not in margin_buttons:
                self.log(f"❌ 无效的保证金: {margin}")
                return False
            
            if not self._click_element(margin_buttons[margin], f'点击保证金{margin_text}'):
                return False
            
            time.sleep(0.1)  # 减少等待时间
            self.log(f"✅ 已设置保证金{margin_text}")
            return True
            
        except Exception as e:
            self.log(f"❌ 设置保证金失败: {e}")
            return False
    
    def _handle_confirm_dialog(self, confirm_element_key, description=""):
        """
        处理确认弹窗
        
        Args:
            confirm_element_key: 确认按钮的元素键
            description: 描述信息
        """
        try:
            # 等待弹窗出现
            time.sleep(0.1)  # 减少等待时间
            
            # 只使用文本查找方法（最可靠）
            try:
                confirm_buttons = self.driver.find_elements(By.XPATH, "//div[contains(text(), '确认')]")
                for button in confirm_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                                # 点击按钮
                                button.click()
                                self.log(f"✅ {description} - 通过文本查找成功")
                                time.sleep(0.1)  # 减少等待时间
                                return True
                    except Exception as e:
                        # 忽略stale element错误，继续查找下一个
                        if "stale element" in str(e).lower():
                            continue
                        else:
                            self.log(f"⚠️ 点击确认按钮时出错: {e}")
                            continue
            except Exception as e:
                self.log(f"⚠️ 通过文本查找确认按钮失败: {e}")
            
                # 如果没找到确认按钮，按ESC键关闭弹窗
                try:
                    from selenium.webdriver.common.keys import Keys
                    self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                    self.log(f"⚠️ {description} - 未找到确认按钮，已按ESC关闭弹窗")
                    time.sleep(0.2)  # 减少等待时间
                except Exception as e:
                    self.log(f"⚠️ 按ESC键失败: {e}")
            
            self.log(f"⚠️ {description} - 未找到确认按钮")
            return False
            
        except Exception as e:
            self.log(f"❌ 处理确认弹窗失败: {e}")
            return False
    
    def set_take_profit(self, price):
        """
        设置止盈价格
        
        Args:
            price: 止盈价格
        """
        try:
            self.log(f"🔄 设置止盈价格: {price}")
            
            if not self._input_text('止盈输入框', price, f'输入止盈价格: {price}'):
                return False
            
            time.sleep(0.5)
            self.log(f"✅ 已设置止盈价格{price}")
            return True
            
        except Exception as e:
            self.log(f"❌ 设置止盈价格失败: {e}")
            return False
    
    def buy_long(self, lots=None, margin=None, take_profit=None):
        """
        买涨（做多）
        
        Args:
            lots: 手数（可选，如果不提供则使用默认值1）
            margin: 保证金（可选，如果不提供则使用默认值2700）
            take_profit: 止盈价格（可选）
        """
        try:
            # 如果没有提供参数，使用默认值
            if lots is None:
                lots = 1
            if margin is None:
                margin = 2700
                
            self.log(f"🔄 开始买涨操作 - 手数:{lots}, 保证金:{margin}")
            
            # 1. 设置手数
            if not self.set_lot_size(lots):
                return False
            
            # 2. 设置保证金
            if not self.set_margin(margin):
                return False
            
            # 3. 设置止盈（如果提供）
            if take_profit:
                if not self.set_take_profit(take_profit):
                    return False
            
            # 4. 点击买涨按钮
            if self.current_mode == "模拟":
                if not self._click_element('模拟_买涨', '点击买涨'):
                    return False
            else:  # 实盘模式
                if not self._click_element('买涨', '点击买涨'):
                    return False
            
            # 5. 等待确认弹窗
            time.sleep(0.2)  # 减少等待时间
            
            # 6. 确认订单（如果有确认弹窗）
            if self.current_mode == "模拟":
                if self._handle_confirm_dialog('模拟_买涨_确认', '确认买涨订单'):
                    self.log("✅ 买涨订单已提交")
                    return True
            else:  # 实盘模式
                if self._handle_confirm_dialog('确认', '确认买涨订单'):
                    self.log("✅ 买涨订单已提交")
                    return True
            
            self.log("✅ 买涨操作完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 买涨操作失败: {e}")
            return False
    
    def buy_short(self, lots=None, margin=None, take_profit=None):
        """
        买跌（做空）
        
        Args:
            lots: 手数（可选，如果不提供则使用默认值1）
            margin: 保证金（可选，如果不提供则使用默认值2700）
            take_profit: 止盈价格（可选）
        """
        try:
            # 如果没有提供参数，使用默认值
            if lots is None:
                lots = 1
            if margin is None:
                margin = 2700
                
            self.log(f"🔄 开始买跌操作 - 手数:{lots}, 保证金:{margin}")
            
            # 1. 设置手数
            if not self.set_lot_size(lots):
                return False
            
            # 2. 设置保证金
            if not self.set_margin(margin):
                return False
            
            # 3. 设置止盈（如果提供）
            if take_profit:
                if not self.set_take_profit(take_profit):
                    return False
            
            # 4. 点击买跌按钮
            if self.current_mode == "模拟":
                if not self._click_element('模拟_买跌', '点击买跌'):
                    return False
            else:  # 实盘模式
                if not self._click_element('买跌', '点击买跌'):
                    return False
            
            # 5. 等待确认弹窗
            time.sleep(0.2)  # 减少等待时间
            
            # 6. 确认订单（如果有确认弹窗）
            if self.current_mode == "模拟":
                if self._handle_confirm_dialog('模拟_买跌_确认', '确认买跌订单'):
                    self.log("✅ 买跌订单已提交")
                    return True
            else:  # 实盘模式
                if self._handle_confirm_dialog('买跌_确认', '确认买跌订单'):
                    self.log("✅ 买跌订单已提交")
                    return True
            
            self.log("✅ 买跌操作完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 买跌操作失败: {e}")
            return False
    
    def close_all_positions(self):
        """
        一键平仓
        """
        try:
            self.log("🔄 执行一键平仓")
            
            if self.current_mode == "模拟":
                if not self._click_element('模拟_一键平仓', '点击一键平仓'):
                    return False
            else:  # 实盘模式
                if not self._click_element('一键平仓', '点击一键平仓'):
                    return False
            
            # 等待确认弹窗
            time.sleep(2)
            
            # 确认平仓（如果有确认弹窗）
            if '确认平仓' in self.element_map:
                if self._click_element('确认平仓', '确认一键平仓'):
                    self.log("✅ 一键平仓已执行")
                    return True
            
            self.log("✅ 一键平仓完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 一键平仓失败: {e}")
            return False
    
    def query_positions(self):
        """
        查询当前持仓
        """
        try:
            self.log("🔄 查询当前持仓")
            
            # 查找持仓列表元素
            if '持仓列表' not in self.element_map:
                self.log("❌ 未找到持仓列表元素映射")
                return []
            
            # 等待持仓列表加载
            time.sleep(1)
            
            # 方法1：查找div.list容器（持仓列表）
            try:
                # 查找持仓列表容器
                position_lists = self.driver.find_elements(By.CSS_SELECTOR, "div.list")
                
                for position_list in position_lists:
                    try:
                        # 查找持仓项
                        position_items = position_list.find_elements(By.CSS_SELECTOR, "div.list")
                        
                        for item in position_items:
                            try:
                                # 提取持仓信息
                                divs = item.find_elements(By.CSS_SELECTOR, "div")
                                
                                if len(divs) >= 12:  # 确保有足够的字段
                                    symbol = divs[1].text.strip()  # 小恒指(MHI2510)
                                    mode = divs[2].text.strip()    # 元
                                    lots = divs[3].text.strip()    # 1
                                    margin = divs[4].text.strip()  # 270
                                    open_price = divs[5].text.strip()  # 25776
                                    take_profit = divs[6].text.strip()  # 1350
                                    stop_loss = divs[7].text.strip()    # -270
                                    pnl = divs[8].text.strip()          # -54.00
                                    overnight_days = divs[9].text.strip()  # --
                                    open_time = divs[10].text.strip()    # 10-22 23:43:16
                                    order_id = divs[11].text.strip()     # 订单号
                                    
                                    positions.append({
                                        'symbol': symbol,
                                        'mode': mode,
                                        'lots': lots,
                                        'margin': margin,
                                        'open_price': open_price,
                                        'take_profit': take_profit,
                                        'stop_loss': stop_loss,
                                        'pnl': pnl,
                                        'overnight_days': overnight_days,
                                        'open_time': open_time,
                                        'order_id': order_id
                                    })
                            except Exception as e:
                                self.log(f"⚠️ 解析持仓项失败: {e}")
                                continue
                
                if positions:
                    self.log(f"📊 通过div.list查询到持仓: {len(positions)} 个")
                    return positions
                
            except Exception as e:
                self.log(f"⚠️ div.list查询失败: {e}")
            
            # 方法2：尝试使用CSS选择器查找持仓表格
            try:
                # 查找持仓表格
                position_table = self.driver.find_element(By.CSS_SELECTOR, "div.position_list table, div.position_list tbody, .position_table")
                
                # 查找表格行
                rows = position_table.find_elements(By.CSS_SELECTOR, "tr")
                
                for row in rows[1:]:  # 跳过表头
                    try:
                        cells = row.find_elements(By.CSS_SELECTOR, "td")
                        if len(cells) >= 8:  # 确保有足够的列
                            symbol = cells[0].text.strip()
                            mode = cells[1].text.strip()
                            lots = cells[2].text.strip()
                            margin = cells[3].text.strip()
                            open_price = cells[4].text.strip()
                            take_profit = cells[5].text.strip()
                            stop_loss = cells[6].text.strip()
                            pnl = cells[7].text.strip()
                            
                            positions.append({
                                'symbol': symbol,
                                'mode': mode,
                                'lots': lots,
                                'margin': margin,
                                'open_price': open_price,
                                'take_profit': take_profit,
                                'stop_loss': stop_loss,
                                'pnl': pnl
                            })
                    except Exception as e:
                        self.log(f"⚠️ 解析持仓行失败: {e}")
                        continue
                
                if positions:
                    self.log(f"📊 通过表格查询到持仓: {len(positions)} 个")
                    return positions
                
            except Exception as e:
                self.log(f"⚠️ 表格查询失败: {e}")
            
            # 方法3：尝试使用XPath查找持仓列表
            try:
                position_list = self.driver.find_element(By.XPATH, self.element_map['持仓列表']['xpath'])
                
                # 查找持仓项
                position_items = position_list.find_elements(By.CSS_SELECTOR, "div.position_item, tr")
                
                for item in position_items:
                    try:
                        # 尝试提取持仓信息
                        text_content = item.text.strip()
                        if text_content and "恒指" in text_content:
                            # 简单解析持仓信息
                            parts = text_content.split()
                            if len(parts) >= 3:
                                positions.append({
                                    'symbol': parts[0] if parts else "未知",
                                    'content': text_content
                                })
                    except Exception as e:
                        self.log(f"⚠️ 解析持仓项失败: {e}")
                        continue
                
                if positions:
                    self.log(f"📊 通过列表查询到持仓: {len(positions)} 个")
                    return positions
                
            except Exception as e:
                self.log(f"⚠️ 列表查询失败: {e}")
            
            # 方法4：查找包含"恒指"或"MHI"的元素
            try:
                # 查找包含持仓信息的元素
                position_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '恒指') or contains(text(), 'MHI')]")
                
                for element in position_elements:
                    try:
                        text_content = element.text.strip()
                        if text_content and ("恒指" in text_content or "MHI" in text_content):
                            positions.append({
                                'symbol': '恒指(MHI)',
                                'content': text_content
                            })
                    except Exception as e:
                        continue
                
                if positions:
                    self.log(f"📊 通过文本搜索查询到持仓: {len(positions)} 个")
                    return positions
                
            except Exception as e:
                self.log(f"⚠️ 文本搜索失败: {e}")
            
            self.log(f"📊 当前持仓: {len(positions)} 个")
            return positions
            
        except Exception as e:
            self.log(f"❌ 查询持仓失败: {e}")
            return []
    
    def query_orders(self):
        """
        查询当前委托
        """
        try:
            self.log("🔄 查询当前委托")
            
            # 点击委托标签
            if not self._click_element('当前委托', '切换到委托页面'):
                return []
            
            time.sleep(2)
            
            # 获取委托信息
            orders = []
            if '委托表格' in self.element_map:
                try:
                    order_table = self.driver.find_element(By.XPATH, self.element_map['委托表格']['xpath'])
                    order_text = order_table.text
                    self.log(f"📊 委托信息: {order_text}")
                    
                    # 解析委托信息（这里需要根据实际页面结构调整）
                    orders = self._parse_order_info(order_text)
                    
                except Exception as e:
                    self.log(f"❌ 获取委托表格失败: {e}")
            
            return orders
            
        except Exception as e:
            self.log(f"❌ 查询委托失败: {e}")
            return []
    
    def _parse_position_info(self, position_text):
        """解析持仓信息"""
        # 这里需要根据实际页面结构实现
        positions = []
        try:
            lines = position_text.split('\n')
            for line in lines:
                if 'MHI' in line or '小恒指' in line:
                    # 解析持仓数据
                    pass
        except:
            pass
        return positions
    
    def _parse_order_info(self, order_text):
        """解析委托信息"""
        # 这里需要根据实际页面结构实现
        orders = []
        try:
            lines = order_text.split('\n')
            for line in lines:
                if 'MHI' in line or '小恒指' in line:
                    # 解析委托数据
                    pass
        except:
            pass
        return orders
    
    def run_test_scenario(self, mode="模拟"):
        """
        运行测试场景
        
        Args:
            mode: "模拟" 或 "实盘"
        """
        try:
            self.log(f"🚀 开始运行{mode}模式测试场景")
            
            # 1. 切换模式
            if not self.switch_mode(mode):
                return False
            
            # 2. 设置订单类型为市价
            if not self.set_order_type("市价"):
                return False
            
            # 3. 设置交易模式为元
            if not self.set_trading_mode("元"):
                return False
            
            # 4. 测试买涨
            self.log("📈 测试买涨操作")
            if not self.buy_long(lots=1, margin=2700, take_profit=26500):
                self.log("⚠️ 买涨测试失败")
            
            time.sleep(3)
            
            # 5. 测试买跌
            self.log("📉 测试买跌操作")
            if not self.buy_short(lots=1, margin=2700, take_profit=26000):
                self.log("⚠️ 买跌测试失败")
            
            time.sleep(3)
            
            # 6. 查询持仓
            self.log("📊 查询持仓")
            positions = self.query_positions()
            self.log(f"当前持仓: {len(positions)} 个")
            
            # 7. 查询委托
            self.log("📋 查询委托")
            orders = self.query_orders()
            self.log(f"当前委托: {len(orders)} 个")
            
            # 8. 一键平仓（如果有持仓）
            if positions:
                self.log("🔄 执行一键平仓")
                self.close_all_positions()
            
            self.log(f"✅ {mode}模式测试场景完成")
            return True
            
        except Exception as e:
            self.log(f"❌ 测试场景失败: {e}")
            return False

def main():
    """主函数"""
    print("=" * 60)
    print("MHI交易测试程序")
    print("=" * 60)
    
    trader = MHITrader()
    
    try:
        # 启动浏览器
        if not trader.start_browser():
            print("❌ 启动浏览器失败")
            return
        
        # 等待页面加载
        time.sleep(3)
        
        # 运行模拟模式测试
        print("\n🧪 开始模拟模式测试")
        trader.run_test_scenario("模拟")
        
        time.sleep(5)
        
        # 运行实盘模式测试（谨慎！）
        print("\n⚠️ 开始实盘模式测试（请确认已切换到实盘模式）")
        response = input("确认继续实盘测试？(y/N): ")
        if response.lower() == 'y':
            trader.run_test_scenario("实盘")
        else:
            print("跳过实盘测试")
        
        print("\n✅ 测试完成")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
    finally:
        # 关闭浏览器
        trader.close_browser()

if __name__ == "__main__":
    main()
