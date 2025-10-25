#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易器 - 直接启动Chrome版本
使用用户数据目录直接启动Chrome浏览器
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class MHIDirectTrader:
    def __init__(self):
        self.driver = None
        self.wait = None
        self.element_map = {}
        self.current_mode = "模拟"
        self.load_element_map()
        
    def load_element_map(self):
        """加载元素映射"""
        try:
            with open('mexc_element_map_1757729194.json', 'r', encoding='utf-8') as f:
                self.element_map = json.load(f)
            print(f"✅ 已加载 {len(self.element_map)} 个元素映射")
        except Exception as e:
            print(f"❌ 加载元素映射失败: {e}")
            self.element_map = {}
    
    def start_browser(self):
        """启动浏览器"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 使用你的Chrome配置
            chrome_options.binary_location = r"C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe"
            chrome_options.add_argument(r'--user-data-dir="C:\Users\Administrator\AppData\Local\Google Chrome\ChromeUserData"')
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.wait = WebDriverWait(self.driver, 15)
            
            # 打开MHI交易页面
            self.driver.get("https://fk.crkpk.com/trade/MHI")
            time.sleep(3)
            
            print("✅ 浏览器启动成功，已使用你的Chrome用户数据目录")
            print("✅ 已打开MHI交易页面")
            return True
                
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            return False
    
    def close_browser(self):
        """关闭浏览器"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.wait = None
                print("✅ 浏览器已关闭")
        except Exception as e:
            print(f"❌ 关闭浏览器失败: {e}")
    
    def click_element(self, element_name, description=""):
        """点击元素"""
        try:
            if element_name not in self.element_map:
                print(f"❌ 未找到元素: {element_name}")
                return False
            
            element = self.driver.find_element(By.XPATH, self.element_map[element_name]['xpath'])
            element.click()
            print(f"✅ {description or f'已点击{element_name}'}")
            time.sleep(0.3)
            return True
            
        except Exception as e:
            print(f"❌ 点击{element_name}失败: {e}")
            return False
    
    def switch_mode(self, mode):
        """切换交易模式"""
        try:
            print(f"🔄 切换交易模式: {mode}")
            
            if mode == "模拟":
                if not self.click_element('模拟', '点击模拟模式'):
                    return False
            elif mode == "实盘":
                if not self.click_element('实盘', '点击实盘模式'):
                    return False
                # 实盘模式需要先点击市价
                time.sleep(1)
                if not self.click_element('市价', '点击市价'):
                    print("⚠️ 点击市价失败，但继续执行")
            else:
                print(f"❌ 无效的交易模式: {mode}")
                return False
            
            self.current_mode = mode
            time.sleep(1)
            print(f"✅ 已切换到{mode}模式")
            return True
            
        except Exception as e:
            print(f"❌ 切换模式失败: {e}")
            return False
    
    def set_lot_size(self, lots):
        """设置手数"""
        try:
            print(f"🔄 设置手数: {lots}")
            
            # 根据当前模式选择对应的手数按钮
            if self.current_mode == "模拟":
                lot_buttons = {
                    1: '模拟_数量1',
                    2: '模拟_数量2', 
                    3: '模拟_数量3',
                    5: '模拟_数量5',
                    8: '模拟_数量8',
                    10: '模拟_数量10'
                }
            else:  # 实盘模式
                lot_buttons = {
                    1: '数量1',
                    2: '数量2', 
                    3: '数量3',
                    5: '数量5',
                    8: '数量8',
                    10: '数量10'
                }
            
            if lots not in lot_buttons:
                print(f"❌ 无效的手数: {lots}")
                return False
            
            if not self.click_element(lot_buttons[lots], f'点击{lots}手'):
                return False
            
            time.sleep(0.5)
            print(f"✅ 已设置{lots}手")
            return True
            
        except Exception as e:
            print(f"❌ 设置手数失败: {e}")
            return False
    
    def set_margin(self, margin):
        """设置保证金"""
        try:
            print(f"🔄 设置保证金: {margin}")
            
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
                print(f"❌ 无效的保证金: {margin}")
                return False
            
            if not self.click_element(margin_buttons[margin], f'点击保证金{margin}'):
                return False
            
            time.sleep(0.5)
            print(f"✅ 已设置保证金{margin}")
            return True
            
        except Exception as e:
            print(f"❌ 设置保证金失败: {e}")
            return False
    
    def handle_confirm_dialog(self, description=""):
        """处理确认弹窗"""
        try:
            time.sleep(0.5)
            
            # 通过文本查找确认按钮
            try:
                confirm_buttons = self.driver.find_elements(By.XPATH, "//div[contains(text(), '确认')]")
                for button in confirm_buttons:
                    try:
                        if button.is_displayed() and button.is_enabled():
                            button.click()
                            print(f"✅ {description} - 确认成功")
                            time.sleep(0.5)
                            return True
                    except Exception as e:
                        if "stale element" in str(e).lower():
                            continue
                        else:
                            print(f"⚠️ 点击确认按钮时出错: {e}")
                            continue
            except Exception as e:
                print(f"⚠️ 通过文本查找确认按钮失败: {e}")
            
            # 如果没找到确认按钮，按ESC键关闭弹窗
            try:
                from selenium.webdriver.common.keys import Keys
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.ESCAPE)
                print(f"⚠️ {description} - 未找到确认按钮，已按ESC关闭弹窗")
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️ 按ESC键失败: {e}")
            
            print(f"⚠️ {description} - 未找到确认按钮")
            return False
            
        except Exception as e:
            print(f"❌ 处理确认弹窗失败: {e}")
            return False
    
    def buy_long(self, lots=1, margin=2700):
        """买涨操作"""
        try:
            print(f"🔄 开始买涨操作 - 手数:{lots}, 保证金:{margin}")
            
            # 1. 设置手数
            if not self.set_lot_size(lots):
                return False
            
            # 2. 设置保证金
            if not self.set_margin(margin):
                return False
            
            # 3. 点击买涨按钮
            if self.current_mode == "模拟":
                if not self.click_element('模拟_买涨', '点击买涨'):
                    return False
            else:  # 实盘模式
                if not self.click_element('买涨', '点击买涨'):
                    return False
            
            # 4. 处理确认弹窗
            time.sleep(1)
            self.handle_confirm_dialog('确认买涨订单')
            
            print("✅ 买涨操作完成")
            return True
            
        except Exception as e:
            print(f"❌ 买涨操作失败: {e}")
            return False
    
    def buy_short(self, lots=1, margin=2700):
        """买跌操作"""
        try:
            print(f"🔄 开始买跌操作 - 手数:{lots}, 保证金:{margin}")
            
            # 1. 设置手数
            if not self.set_lot_size(lots):
                return False
            
            # 2. 设置保证金
            if not self.set_margin(margin):
                return False
            
            # 3. 点击买跌按钮
            if self.current_mode == "模拟":
                if not self.click_element('模拟_买跌', '点击买跌'):
                    return False
            else:  # 实盘模式
                if not self.click_element('买跌', '点击买跌'):
                    return False
            
            # 4. 处理确认弹窗
            time.sleep(1)
            self.handle_confirm_dialog('确认买跌订单')
            
            print("✅ 买跌操作完成")
            return True
            
        except Exception as e:
            print(f"❌ 买跌操作失败: {e}")
            return False
    
    def run_test(self):
        """运行测试"""
        print("🚀 开始MHI交易测试")
        
        try:
            # 启动浏览器
            if not self.start_browser():
                return False
            
            # 等待页面加载
            time.sleep(3)
            
            # 测试买涨
            print("\n📈 测试买涨操作")
            self.buy_long(lots=1, margin=2700)
            
            time.sleep(3)
            
            # 测试买跌
            print("\n📉 测试买跌操作")
            self.buy_short(lots=1, margin=2700)
            
            print("\n✅ 测试完成")
            return True
            
        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")
            return False
        finally:
            # 关闭浏览器
            self.close_browser()

def main():
    """主函数"""
    print("=" * 60)
    print("MHI交易器 - 直接启动Chrome版本")
    print("=" * 60)
    
    trader = MHIDirectTrader()
    trader.run_test()

if __name__ == "__main__":
    main()
