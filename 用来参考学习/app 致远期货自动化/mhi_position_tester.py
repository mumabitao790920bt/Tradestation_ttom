#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI持仓查询测试工具
专门用于测试和调试持仓查询功能
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class MHIPositionTester:
    def __init__(self):
        self.driver = None
        self.wait = None
        
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
            
            print("✅ 浏览器启动成功")
            return True
                
        except Exception as e:
            print(f"❌ 启动浏览器失败: {e}")
            return False
    
    def test_position_query(self):
        """测试持仓查询"""
        try:
            print("🔍 开始测试持仓查询...")
            
            # 1. 查找所有div.list元素
            print("\n1. 查找所有div.list元素:")
            list_elements = self.driver.find_elements(By.CSS_SELECTOR, "div.list")
            print(f"   找到 {len(list_elements)} 个div.list元素")
            
            for i, element in enumerate(list_elements):
                try:
                    divs = element.find_elements(By.CSS_SELECTOR, "div")
                    print(f"   元素{i+1}: 包含 {len(divs)} 个div子元素")
                    
                    if len(divs) >= 12:
                        print(f"     商品名称: {divs[1].text.strip()}")
                        print(f"     模式: {divs[2].text.strip()}")
                        print(f"     手数: {divs[3].text.strip()}")
                        print(f"     保证金: {divs[4].text.strip()}")
                        print(f"     开仓价: {divs[5].text.strip()}")
                        print(f"     止盈: {divs[6].text.strip()}")
                        print(f"     止损: {divs[7].text.strip()}")
                        print(f"     盈亏: {divs[8].text.strip()}")
                        print(f"     过夜天数: {divs[9].text.strip()}")
                        print(f"     开仓时间: {divs[10].text.strip()}")
                        print(f"     订单号: {divs[11].text.strip()}")
                except Exception as e:
                    print(f"   元素{i+1}解析失败: {e}")
            
            # 2. 查找包含"小恒指"的元素
            print("\n2. 查找包含'小恒指'的元素:")
            hang_seng_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '小恒指')]")
            print(f"   找到 {len(hang_seng_elements)} 个包含'小恒指'的元素")
            
            for i, element in enumerate(hang_seng_elements):
                try:
                    print(f"   元素{i+1}: {element.tag_name} - {element.text.strip()}")
                    print(f"     XPath: {self._get_xpath(element)}")
                except:
                    pass
            
            # 3. 查找包含"25776"的元素（开仓价）
            print("\n3. 查找包含'25776'的元素:")
            price_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '25776')]")
            print(f"   找到 {len(price_elements)} 个包含'25776'的元素")
            
            for i, element in enumerate(price_elements):
                try:
                    print(f"   元素{i+1}: {element.tag_name} - {element.text.strip()}")
                    print(f"     XPath: {self._get_xpath(element)}")
                except:
                    pass
            
            # 4. 查找包含"-54.00"的元素（盈亏）
            print("\n4. 查找包含'-54.00'的元素:")
            pnl_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '-54.00')]")
            print(f"   找到 {len(pnl_elements)} 个包含'-54.00'的元素")
            
            for i, element in enumerate(pnl_elements):
                try:
                    print(f"   元素{i+1}: {element.tag_name} - {element.text.strip()}")
                    print(f"     XPath: {self._get_xpath(element)}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"❌ 测试失败: {e}")
            return False
    
    def _get_xpath(self, element):
        """获取元素的XPath"""
        try:
            return self.driver.execute_script("""
                function getElementXPath(element) {
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
                            return getElementXPath(element.parentNode) + '/' + element.tagName + '[' + (ix + 1) + ']';
                        }
                        if (sibling.nodeType === 1 && sibling.tagName === element.tagName) {
                            ix++;
                        }
                    }
                }
                return getElementXPath(arguments[0]);
            """, element)
        except:
            return "无法获取XPath"
    
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

def main():
    """主函数"""
    print("=" * 60)
    print("MHI持仓查询测试工具")
    print("=" * 60)
    
    tester = MHIPositionTester()
    
    try:
        # 启动浏览器
        if not tester.start_browser():
            return False
        
        # 等待页面加载
        time.sleep(3)
        
        # 测试持仓查询
        tester.test_position_query()
        
        print("\n✅ 测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试过程中出现异常: {e}")
        return False
    finally:
        # 关闭浏览器
        tester.close_browser()

if __name__ == "__main__":
    main()
