#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI元素映射验证脚本
验证采集的元素映射是否正确
"""

import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options

class MHIElementValidator:
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
    
    def validate_element(self, element_name, description=""):
        """验证单个元素"""
        try:
            if element_name not in self.element_map:
                print(f"❌ 未找到元素: {element_name}")
                return False
            
            element_info = self.element_map[element_name]
            xpath = element_info.get('xpath', '')
            
            if not xpath:
                print(f"❌ 元素 {element_name} 没有XPath")
                return False
            
            # 尝试查找元素
            element = self.driver.find_element(By.XPATH, xpath)
            
            # 检查元素是否可见
            if not element.is_displayed():
                print(f"⚠️ 元素不可见: {element_name}")
                return False
            
            # 检查元素是否可点击
            if not element.is_enabled():
                print(f"⚠️ 元素不可点击: {element_name}")
                return False
            
            # 高亮元素
            self.driver.execute_script("arguments[0].style.border='3px solid red'", element)
            time.sleep(1)
            
            # 获取元素文本
            text = element.text.strip()
            
            print(f"✅ {description or element_name}: 找到元素，文本='{text}'")
            
            # 移除高亮
            self.driver.execute_script("arguments[0].style.border=''", element)
            time.sleep(0.5)
            
            return True
            
        except Exception as e:
            print(f"❌ 验证元素 {element_name} 失败: {e}")
            return False
    
    def validate_mode_switches(self):
        """验证模式切换元素"""
        print("\n🔄 验证模式切换元素")
        
        # 验证模拟模式
        self.validate_element('模拟', '模拟模式按钮')
        
        # 验证实盘模式
        self.validate_element('实盘', '实盘模式按钮')
    
    def validate_trading_elements(self):
        """验证交易相关元素"""
        print("\n💰 验证交易相关元素")
        
        # 验证订单类型
        self.validate_element('市价', '市价订单')
        
        # 验证交易模式
        self.validate_element('模拟_元', '元模式')
        
        # 验证手数按钮
        for i in range(1, 11):
            element_name = f'模拟_数量{i}'
            if element_name in self.element_map:
                self.validate_element(element_name, f'{i}手按钮')
    
    def validate_trade_buttons(self):
        """验证交易按钮"""
        print("\n🎯 验证交易按钮")
        
        # 验证买涨按钮
        self.validate_element('模拟_买涨', '买涨按钮')
        
        # 验证买跌按钮
        self.validate_element('模拟_买跌', '买跌按钮')
        
        # 验证一键平仓按钮
        self.validate_element('模拟_一键平仓', '一键平仓按钮')
    
    def validate_confirm_buttons(self):
        """验证确认按钮"""
        print("\n✅ 验证确认按钮")
        
        # 验证买涨确认按钮
        if '模拟_买涨_确认' in self.element_map:
            self.validate_element('模拟_买涨_确认', '买涨确认按钮')
        
        # 验证买跌确认按钮
        if '模拟_买跌_确认' in self.element_map:
            self.validate_element('模拟_买跌_确认', '买跌确认按钮')
    
    def run_validation(self):
        """运行完整验证"""
        print("🚀 开始元素映射验证")
        
        try:
            # 启动浏览器
            if not self.start_browser():
                return False
            
            # 等待页面加载
            time.sleep(3)
            
            # 验证各种元素
            self.validate_mode_switches()
            self.validate_trading_elements()
            self.validate_trade_buttons()
            self.validate_confirm_buttons()
            
            print("\n✅ 元素映射验证完成")
            return True
            
        except Exception as e:
            print(f"❌ 验证过程中出现异常: {e}")
            return False
        finally:
            # 关闭浏览器
            self.close_browser()

def main():
    """主函数"""
    print("=" * 60)
    print("MHI元素映射验证程序")
    print("=" * 60)
    
    validator = MHIElementValidator()
    validator.run_validation()

if __name__ == "__main__":
    main()
