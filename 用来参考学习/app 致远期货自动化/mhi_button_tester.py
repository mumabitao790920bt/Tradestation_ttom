#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI交易按钮测试脚本
专门用于测试致远金融MHI页面的各个按钮功能
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options

class MHIButtonTester:
    def __init__(self):
        self.driver = None
        self.wait = None
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
                self.wait = WebDriverWait(self.driver, 15)
                
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
                self.wait = None
                print("✅ 浏览器已关闭")
        except Exception as e:
            print(f"❌ 关闭浏览器失败: {e}")
    
    def test_button(self, element_name, description=""):
        """测试单个按钮"""
        try:
            if element_name not in self.element_map:
                print(f"❌ 未找到元素: {element_name}")
                return False
            
            element = self.driver.find_element(By.XPATH, self.element_map[element_name]['xpath'])
            
            # 检查元素是否可见和可点击
            if not element.is_displayed():
                print(f"⚠️ 元素不可见: {element_name}")
                return False
            
            if not element.is_enabled():
                print(f"⚠️ 元素不可点击: {element_name}")
                return False
            
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
            print(f"❌ 测试{element_name}失败: {e}")
            return False
    
    def test_mode_switches(self):
        """测试模式切换按钮"""
        print("\n🔄 测试模式切换按钮")
        
        # 测试模拟模式
        if self.test_button('模拟模式', '点击模拟模式'):
            time.sleep(1)
        
        # 测试实盘模式
        if self.test_button('实盘模式', '点击实盘模式'):
            time.sleep(1)
        
        # 切换回模拟模式
        if self.test_button('模拟模式', '切换回模拟模式'):
            time.sleep(1)
    
    def test_order_type_buttons(self):
        """测试订单类型按钮"""
        print("\n📋 测试订单类型按钮")
        
        # 测试市价
        if self.test_button('市价订单', '点击市价'):
            time.sleep(1)
        
        # 测试限价
        if self.test_button('限价订单', '点击限价'):
            time.sleep(1)
    
    def test_trading_mode_buttons(self):
        """测试交易模式按钮"""
        print("\n💰 测试交易模式按钮")
        
        # 测试元模式
        if self.test_button('元模式', '点击元模式'):
            time.sleep(1)
        
        # 测试角模式
        if self.test_button('角模式', '点击角模式'):
            time.sleep(1)
        
        # 切换回元模式
        if self.test_button('元模式', '切换回元模式'):
            time.sleep(1)
    
    def test_lot_size_buttons(self):
        """测试手数按钮"""
        print("\n📊 测试手数按钮")
        
        lot_buttons = ['1手', '2手', '3手', '5手', '8手', '10手']
        
        for lot in lot_buttons:
            if lot in self.element_map:
                if self.test_button(lot, f'点击{lot}'):
                    time.sleep(0.5)
            else:
                print(f"⚠️ 未找到手数按钮: {lot}")
    
    def test_margin_buttons(self):
        """测试保证金按钮"""
        print("\n💎 测试保证金按钮")
        
        margin_buttons = ['保证金2700', '保证金4050', '保证金5850', '保证金8100']
        
        for margin in margin_buttons:
            if margin in self.element_map:
                if self.test_button(margin, f'点击{margin}'):
                    time.sleep(0.5)
            else:
                print(f"⚠️ 未找到保证金按钮: {margin}")
    
    def test_trade_buttons(self):
        """测试交易按钮"""
        print("\n🎯 测试交易按钮")
        
        # 测试买涨按钮
        if self.test_button('买涨按钮', '点击买涨'):
            time.sleep(2)
            # 检查是否有确认弹窗
            if '确认订单' in self.element_map:
                if self.test_button('确认订单', '确认买涨订单'):
                    time.sleep(1)
                elif '取消订单' in self.element_map:
                    if self.test_button('取消订单', '取消买涨订单'):
                        time.sleep(1)
        
        # 测试买跌按钮
        if self.test_button('买跌按钮', '点击买跌'):
            time.sleep(2)
            # 检查是否有确认弹窗
            if '确认订单' in self.element_map:
                if self.test_button('确认订单', '确认买跌订单'):
                    time.sleep(1)
                elif '取消订单' in self.element_map:
                    if self.test_button('取消订单', '取消买跌订单'):
                        time.sleep(1)
    
    def test_position_buttons(self):
        """测试持仓相关按钮"""
        print("\n📈 测试持仓相关按钮")
        
        # 测试当前持仓标签
        if self.test_button('当前持仓', '点击当前持仓'):
            time.sleep(2)
        
        # 测试当前委托标签
        if self.test_button('当前委托', '点击当前委托'):
            time.sleep(2)
        
        # 测试交易记录标签
        if self.test_button('交易记录', '点击交易记录'):
            time.sleep(2)
        
        # 测试一键平仓按钮
        if self.test_button('一键平仓', '点击一键平仓'):
            time.sleep(2)
            # 检查是否有确认弹窗
            if '确认平仓' in self.element_map:
                if self.test_button('确认平仓', '确认一键平仓'):
                    time.sleep(1)
                elif '取消平仓' in self.element_map:
                    if self.test_button('取消平仓', '取消一键平仓'):
                        time.sleep(1)
    
    def test_input_fields(self):
        """测试输入框"""
        print("\n📝 测试输入框")
        
        # 测试止盈输入框
        if '止盈输入框' in self.element_map:
            try:
                element = self.driver.find_element(By.XPATH, self.element_map['止盈输入框']['xpath'])
                element.click()
                element.send_keys(Keys.CONTROL + "a")
                element.send_keys("26500")
                print("✅ 已输入止盈价格: 26500")
                time.sleep(1)
            except Exception as e:
                print(f"❌ 测试止盈输入框失败: {e}")
        else:
            print("⚠️ 未找到止盈输入框")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始运行所有按钮测试")
        
        try:
            # 1. 测试模式切换
            self.test_mode_switches()
            
            # 2. 测试订单类型
            self.test_order_type_buttons()
            
            # 3. 测试交易模式
            self.test_trading_mode_buttons()
            
            # 4. 测试手数按钮
            self.test_lot_size_buttons()
            
            # 5. 测试保证金按钮
            self.test_margin_buttons()
            
            # 6. 测试输入框
            self.test_input_fields()
            
            # 7. 测试持仓相关按钮
            self.test_position_buttons()
            
            # 8. 测试交易按钮（最后测试，避免实际下单）
            print("\n⚠️ 即将测试交易按钮，请确认当前为模拟模式")
            response = input("确认继续测试交易按钮？(y/N): ")
            if response.lower() == 'y':
                self.test_trade_buttons()
            else:
                print("跳过交易按钮测试")
            
            print("\n✅ 所有测试完成")
            
        except Exception as e:
            print(f"❌ 测试过程中出现异常: {e}")
    
    def run_specific_test(self, test_name):
        """运行特定测试"""
        tests = {
            'mode': self.test_mode_switches,
            'order': self.test_order_type_buttons,
            'trading': self.test_trading_mode_buttons,
            'lots': self.test_lot_size_buttons,
            'margin': self.test_margin_buttons,
            'input': self.test_input_fields,
            'position': self.test_position_buttons,
            'trade': self.test_trade_buttons
        }
        
        if test_name in tests:
            print(f"🎯 运行特定测试: {test_name}")
            tests[test_name]()
        else:
            print(f"❌ 未知的测试名称: {test_name}")
            print(f"可用测试: {', '.join(tests.keys())}")

def main():
    """主函数"""
    print("=" * 60)
    print("MHI交易按钮测试程序")
    print("=" * 60)
    
    tester = MHIButtonTester()
    
    try:
        # 启动浏览器
        if not tester.start_browser():
            print("❌ 启动浏览器失败")
            return
        
        # 等待页面加载
        time.sleep(3)
        
        # 显示可用测试
        print("\n可用测试:")
        print("1. 全部测试 (all)")
        print("2. 模式切换 (mode)")
        print("3. 订单类型 (order)")
        print("4. 交易模式 (trading)")
        print("5. 手数按钮 (lots)")
        print("6. 保证金按钮 (margin)")
        print("7. 输入框 (input)")
        print("8. 持仓相关 (position)")
        print("9. 交易按钮 (trade)")
        
        # 获取用户选择
        choice = input("\n请选择测试类型 (默认: all): ").strip().lower()
        
        if choice == 'all' or choice == '':
            tester.run_all_tests()
        else:
            tester.run_specific_test(choice)
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
    finally:
        # 关闭浏览器
        tester.close_browser()

if __name__ == "__main__":
    main()
