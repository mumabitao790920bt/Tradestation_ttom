#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI确认弹窗测试脚本
专门测试确认弹窗的处理
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options

class MHIConfirmDialogTester:
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
                        time.sleep(2)
                        print("已跳转到MHI交易页面")
                    else:
                        print(f"复用当前页面: {current_url}")
                except:
                    self.driver.get("https://fk.crkpk.com/trade/MHI")
                    time.sleep(2)
                
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
            
            # 高亮元素
            self.driver.execute_script("arguments[0].style.border='3px solid red'", element)
            time.sleep(1)
            
            # 点击元素
            element.click()
            print(f"✅ {description or f'已点击{element_name}'}")
            
            # 移除高亮
            self.driver.execute_script("arguments[0].style.border=''", element)
            time.sleep(0.5)
            return True
            
        except Exception as e:
            print(f"❌ 点击{element_name}失败: {e}")
            return False
    
    def test_confirm_dialog_methods(self):
        """测试确认弹窗的各种查找方法"""
        print("\n🧪 测试确认弹窗查找方法")
        
        # 等待弹窗出现
        time.sleep(2)
        
        # 方法1: 检查预定义元素是否存在
        print("\n方法1: 检查预定义元素")
        if '模拟_买涨_确认' in self.element_map:
            print(f"✅ 找到预定义元素: 模拟_买涨_确认")
            print(f"   XPath: {self.element_map['模拟_买涨_确认']['xpath']}")
            print(f"   CSS: {self.element_map['模拟_买涨_确认']['cssPath']}")
        else:
            print("❌ 未找到预定义元素: 模拟_买涨_确认")
        
        # 方法2: 通过文本查找确认按钮
        print("\n方法2: 通过文本查找确认按钮")
        try:
            confirm_buttons = self.driver.find_elements(By.XPATH, "//div[contains(text(), '确认')]")
            print(f"找到 {len(confirm_buttons)} 个包含'确认'文本的元素")
            
            for i, button in enumerate(confirm_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        print(f"  按钮{i+1}: 文本='{button.text}', 可见={button.is_displayed()}, 可点击={button.is_enabled()}")
                        # 高亮按钮
                        self.driver.execute_script("arguments[0].style.border='3px solid blue'", button)
                        time.sleep(1)
                        # 移除高亮
                        self.driver.execute_script("arguments[0].style.border=''", button)
                except Exception as e:
                    print(f"  按钮{i+1}: 检查失败 - {e}")
        except Exception as e:
            print(f"❌ 通过文本查找失败: {e}")
        
        # 方法3: 通过CSS选择器查找
        print("\n方法3: 通过CSS选择器查找")
        try:
            confirm_buttons = self.driver.find_elements(By.CSS_SELECTOR, ".ant-modal .btn_box div")
            print(f"找到 {len(confirm_buttons)} 个CSS选择器匹配的元素")
            
            for i, button in enumerate(confirm_buttons):
                try:
                    if button.is_displayed() and button.is_enabled():
                        print(f"  按钮{i+1}: 文本='{button.text}', 可见={button.is_displayed()}, 可点击={button.is_enabled()}")
                        # 高亮按钮
                        self.driver.execute_script("arguments[0].style.border='3px solid green'", button)
                        time.sleep(1)
                        # 移除高亮
                        self.driver.execute_script("arguments[0].style.border=''", button)
                except Exception as e:
                    print(f"  按钮{i+1}: 检查失败 - {e}")
        except Exception as e:
            print(f"❌ 通过CSS选择器查找失败: {e}")
        
        # 方法4: 查找所有模态框
        print("\n方法4: 查找所有模态框")
        try:
            modals = self.driver.find_elements(By.CSS_SELECTOR, ".ant-modal")
            print(f"找到 {len(modals)} 个模态框")
            
            for i, modal in enumerate(modals):
                try:
                    if modal.is_displayed():
                        print(f"  模态框{i+1}: 可见={modal.is_displayed()}")
                        # 查找模态框内的按钮
                        buttons = modal.find_elements(By.CSS_SELECTOR, "div")
                        print(f"    包含 {len(buttons)} 个div元素")
                        
                        for j, button in enumerate(buttons):
                            try:
                                if button.is_displayed() and button.is_enabled() and button.text.strip():
                                    print(f"      按钮{j+1}: 文本='{button.text.strip()}'")
                            except:
                                pass
                except Exception as e:
                    print(f"  模态框{i+1}: 检查失败 - {e}")
        except Exception as e:
            print(f"❌ 查找模态框失败: {e}")
    
    def test_buy_long_with_confirm(self):
        """测试买涨并处理确认弹窗"""
        print("\n🎯 测试买涨操作并处理确认弹窗")
        
        try:
            # 1. 确保在模拟模式
            if not self.click_element('模拟', '切换到模拟模式'):
                return False
            
            time.sleep(2)
            
            # 2. 设置基本参数
            if not self.click_element('模拟_元', '设置元模式'):
                return False
            
            time.sleep(1)
            
            if not self.click_element('模拟_数量1', '设置1手'):
                return False
            
            time.sleep(1)
            
            if not self.click_element('模拟_保证金1', '设置保证金2700'):
                return False
            
            time.sleep(1)
            
            # 3. 点击买涨
            if not self.click_element('模拟_买涨', '点击买涨'):
                return False
            
            time.sleep(2)
            
            # 4. 测试确认弹窗处理
            self.test_confirm_dialog_methods()
            
            # 5. 尝试点击确认按钮
            print("\n尝试点击确认按钮")
            try:
                confirm_buttons = self.driver.find_elements(By.XPATH, "//div[contains(text(), '确认')]")
                for button in confirm_buttons:
                    if button.is_displayed() and button.is_enabled():
                        print("找到确认按钮，尝试点击")
                        button.click()
                        print("✅ 确认按钮点击成功")
                        time.sleep(2)
                        break
                else:
                    print("⚠️ 未找到可点击的确认按钮")
            except Exception as e:
                print(f"❌ 点击确认按钮失败: {e}")
            
            return True
            
        except Exception as e:
            print(f"❌ 测试买涨操作失败: {e}")
            return False
    
    def run_test(self):
        """运行测试"""
        print("🚀 开始MHI确认弹窗测试")
        
        try:
            # 启动浏览器
            if not self.start_browser():
                return False
            
            # 等待页面加载
            time.sleep(3)
            
            # 测试买涨操作
            self.test_buy_long_with_confirm()
            
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
    print("MHI确认弹窗测试程序")
    print("=" * 60)
    
    tester = MHIConfirmDialogTester()
    tester.run_test()

if __name__ == "__main__":
    main()


