#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MHI持仓查询调试工具
用于调试持仓查询功能
"""

import time
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

class MHIPositionDebugger:
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
    
    def debug_position_elements(self):
        """调试持仓元素"""
        try:
            print("🔍 开始调试持仓元素...")
            
            # 1. 查找所有包含"恒指"的元素
            print("\n1. 查找包含'恒指'的元素:")
            hang_seng_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), '恒指')]")
            for i, element in enumerate(hang_seng_elements):
                try:
                    print(f"  元素{i+1}: {element.tag_name} - {element.text[:50]}...")
                    print(f"    XPath: {self._get_xpath(element)}")
                except:
                    pass
            
            # 2. 查找所有包含"MHI"的元素
            print("\n2. 查找包含'MHI'的元素:")
            mhi_elements = self.driver.find_elements(By.XPATH, "//*[contains(text(), 'MHI')]")
            for i, element in enumerate(mhi_elements):
                try:
                    print(f"  元素{i+1}: {element.tag_name} - {element.text[:50]}...")
                    print(f"    XPath: {self._get_xpath(element)}")
                except:
                    pass
            
            # 3. 查找表格元素
            print("\n3. 查找表格元素:")
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            for i, table in enumerate(tables):
                try:
                    print(f"  表格{i+1}: {table.get_attribute('class')}")
                    rows = table.find_elements(By.TAG_NAME, "tr")
                    print(f"    行数: {len(rows)}")
                    if rows:
                        first_row = rows[0]
                        cells = first_row.find_elements(By.TAG_NAME, "td")
                        print(f"    第一行列数: {len(cells)}")
                        if cells:
                            print(f"    第一行内容: {first_row.text[:100]}...")
                except:
                    pass
            
            # 4. 查找div.position_list
            print("\n4. 查找div.position_list:")
            position_lists = self.driver.find_elements(By.CSS_SELECTOR, "div.position_list")
            for i, pl in enumerate(position_lists):
                try:
                    print(f"  持仓列表{i+1}: {pl.text[:100]}...")
                    print(f"    XPath: {self._get_xpath(pl)}")
                except:
                    pass
            
            # 5. 查找所有tr元素
            print("\n5. 查找所有tr元素:")
            trs = self.driver.find_elements(By.TAG_NAME, "tr")
            for i, tr in enumerate(trs):
                try:
                    text = tr.text.strip()
                    if text and ("恒指" in text or "MHI" in text or "25730" in text):
                        print(f"  TR{i+1}: {text[:100]}...")
                        print(f"    XPath: {self._get_xpath(tr)}")
                except:
                    pass
            
            return True
            
        except Exception as e:
            print(f"❌ 调试失败: {e}")
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
    print("MHI持仓查询调试工具")
    print("=" * 60)
    
    debugger = MHIPositionDebugger()
    
    try:
        # 启动浏览器
        if not debugger.start_browser():
            return False
        
        # 等待页面加载
        time.sleep(3)
        
        # 调试持仓元素
        debugger.debug_position_elements()
        
        print("\n✅ 调试完成")
        return True
        
    except Exception as e:
        print(f"❌ 调试过程中出现异常: {e}")
        return False
    finally:
        # 关闭浏览器
        debugger.close_browser()

if __name__ == "__main__":
    main()
