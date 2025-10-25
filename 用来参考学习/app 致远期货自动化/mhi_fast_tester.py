#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI快速交易测试脚本
优化后的快速交易测试
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class MHIFastTester:
    def __init__(self):
        self.driver = None
        self.element_map = {}
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
            # 加载浏览器配置
            with open('weex_browser_config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            chrome_options = Options()
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            
            # 使用调试端口附着
            if config.get('debugger_address'):
                chrome_options.add_experimental_option("debuggerAddress", config['debugger_address'])
                self.driver = webdriver.Chrome(options=chrome_options)
                
                # 检查当前页面
                try:
                    current_url = self.driver.current_url or ""
                    if "fk.crkpk.com" not in current_url:
                        self.driver.get("https://fk.crkpk.com/trade/MHI")
                        time.sleep(1)
                        print("已跳转到MHI交易页面")
                    else:
                        print(f"复用当前页面: {current_url}")
                except:
                    self.driver.get("https://fk.crkpk.com/trade/MHI")
                    time.sleep(1)
                
                print("✅ 浏览器启动成功")
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
            time.sleep(0.3)  # 减少等待时间
            return True
            
        except Exception as e:
            print(f"❌ 点击{element_name}失败: {e}")
            return False
    
    def handle_confirm_dialog(self, description=""):
        """快速处理确认弹窗"""
        try:
            # 等待弹窗出现
            time.sleep(0.5)
            
            # 只使用文本查找方法（最可靠）
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
                        # 忽略stale element错误，继续查找下一个
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
    
    def fast_buy_long(self):
        """快速买涨测试"""
        print("\n🚀 快速买涨测试")
        start_time = time.time()
        
        try:
            # 1. 确保在模拟模式
            if not self.click_element('模拟', '切换到模拟模式'):
                return False
            
            # 2. 设置基本参数
            if not self.click_element('模拟_元', '设置元模式'):
                return False
            
            if not self.click_element('模拟_数量1', '设置1手'):
                return False
            
            if not self.click_element('模拟_保证金1', '设置保证金2700'):
                return False
            
            # 3. 点击买涨
            if not self.click_element('模拟_买涨', '点击买涨'):
                return False
            
            # 4. 处理确认弹窗
            self.handle_confirm_dialog('确认买涨订单')
            
            end_time = time.time()
            print(f"✅ 买涨测试完成，耗时: {end_time - start_time:.2f}秒")
            return True
            
        except Exception as e:
            print(f"❌ 买涨测试失败: {e}")
            return False
    
    def fast_buy_short(self):
        """快速买跌测试"""
        print("\n🚀 快速买跌测试")
        start_time = time.time()
        
        try:
            # 1. 确保在模拟模式
            if not self.click_element('模拟', '切换到模拟模式'):
                return False
            
            # 2. 设置基本参数
            if not self.click_element('模拟_元', '设置元模式'):
                return False
            
            if not self.click_element('模拟_数量1', '设置1手'):
                return False
            
            if not self.click_element('模拟_保证金1', '设置保证金2700'):
                return False
            
            # 3. 点击买跌
            if not self.click_element('模拟_买跌', '点击买跌'):
                return False
            
            # 4. 处理确认弹窗
            self.handle_confirm_dialog('确认买跌订单')
            
            end_time = time.time()
            print(f"✅ 买跌测试完成，耗时: {end_time - start_time:.2f}秒")
            return True
            
        except Exception as e:
            print(f"❌ 买跌测试失败: {e}")
            return False
    
    def run_fast_test(self):
        """运行快速测试"""
        print("🚀 开始MHI快速交易测试")
        
        try:
            # 启动浏览器
            if not self.start_browser():
                return False
            
            # 等待页面加载
            time.sleep(2)
            
            # 测试买涨
            self.fast_buy_long()
            
            time.sleep(2)
            
            # 测试买跌
            self.fast_buy_short()
            
            print("\n✅ 快速测试完成")
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
    print("MHI快速交易测试程序")
    print("=" * 60)
    
    tester = MHIFastTester()
    tester.run_fast_test()

if __name__ == "__main__":
    main()


