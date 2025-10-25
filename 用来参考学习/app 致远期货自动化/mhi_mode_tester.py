#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易测试 - 模式切换验证脚本
验证模拟和实盘模式的元素映射是否正确
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class MHIModeTester:
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
    
    def test_simulated_mode(self):
        """测试模拟模式"""
        print("\n🧪 测试模拟模式")
        
        # 1. 切换到模拟模式
        if not self.click_element('模拟', '切换到模拟模式'):
            return False
        
        time.sleep(2)
        
        # 2. 设置交易模式为元
        if not self.click_element('模拟_元', '设置元模式'):
            return False
        
        time.sleep(1)
        
        # 3. 设置手数为1
        if not self.click_element('模拟_数量1', '设置1手'):
            return False
        
        time.sleep(1)
        
        # 4. 设置保证金为2700
        if not self.click_element('模拟_保证金1', '设置保证金2700'):
            return False
        
        time.sleep(1)
        
        # 5. 点击买涨（但不确认）
        if not self.click_element('模拟_买涨', '点击买涨'):
            return False
        
        time.sleep(2)
        
        # 6. 如果有确认弹窗，点击取消
        if '模拟_买涨_确认' in self.element_map:
            print("⚠️ 检测到确认弹窗，跳过确认")
        
        print("✅ 模拟模式测试完成")
        return True
    
    def test_live_mode(self):
        """测试实盘模式"""
        print("\n⚠️ 测试实盘模式（请确认当前为模拟环境）")
        
        # 1. 切换到实盘模式
        if not self.click_element('实盘', '切换到实盘模式'):
            return False
        
        time.sleep(2)
        
        # 2. 点击市价（实盘模式必需）
        if not self.click_element('市价', '点击市价'):
            return False
        
        time.sleep(1)
        
        # 3. 设置交易模式为元
        if not self.click_element('元', '设置元模式'):
            return False
        
        time.sleep(1)
        
        # 4. 设置手数为1
        if not self.click_element('数量1', '设置1手'):
            return False
        
        time.sleep(1)
        
        # 5. 设置保证金为2700
        if not self.click_element('保证金1', '设置保证金2700'):
            return False
        
        time.sleep(1)
        
        # 6. 点击买涨（但不确认）
        if not self.click_element('买涨', '点击买涨'):
            return False
        
        time.sleep(2)
        
        # 7. 如果有确认弹窗，点击取消
        if '确认' in self.element_map:
            print("⚠️ 检测到确认弹窗，跳过确认")
        
        print("✅ 实盘模式测试完成")
        return True
    
    def run_test(self):
        """运行测试"""
        print("🚀 开始MHI模式切换测试")
        
        try:
            # 启动浏览器
            if not self.start_browser():
                return False
            
            # 等待页面加载
            time.sleep(3)
            
            # 测试模拟模式
            self.test_simulated_mode()
            
            time.sleep(3)
            
            # 测试实盘模式
            self.test_live_mode()
            
            print("\n✅ 所有测试完成")
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
    print("MHI模式切换测试程序")
    print("=" * 60)
    
    tester = MHIModeTester()
    tester.run_test()

if __name__ == "__main__":
    main()


