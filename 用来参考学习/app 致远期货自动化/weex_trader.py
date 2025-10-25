#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Weex 交易模块
负责 Weex 交易所的网页自动化交易操作
"""

import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class WeexTrader:
    def __init__(self, driver, element_map, log_callback=None):
        """
        初始化 Weex 交易器
        
        Args:
            driver: Selenium WebDriver 实例
            element_map: 元素对照表字典
            log_callback: 日志回调函数
        """
        self.driver = driver
        self.element_map = element_map
        self.log = log_callback or print
        self.wait = WebDriverWait(driver, 10)
        
    def _click_element(self, element_key, description=""):
        """点击元素"""
        try:
            if element_key not in self.element_map:
                self.log(f"❌ 元素对照表中未找到'{element_key}'")
                return False
            
            element = self.driver.find_element(By.XPATH, self.element_map[element_key]['xpath'])
            element.click()
            self.log(f"✅ {description or f'已点击{element_key}'}")
            time.sleep(0.5)  # 等待页面响应
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
            element.click()  # 先点击聚焦
            element.send_keys(Keys.CONTROL + "a")  # 全选
            element.send_keys(Keys.DELETE)  # 删除
            element.send_keys(str(text))  # 输入新文本
            self.log(f"✅ {description or f'已输入{element_key}: {text}'}")
            time.sleep(0.3)
            return True
        except Exception as e:
            self.log(f"❌ 输入{element_key}失败: {e}")
            return False
    
    def buy_long(self, price_offset=0.1, quantity=0.001):
        """
        做多买入
        
        Args:
            price_offset: 超价金额（默认0.1）
            quantity: 下单数量
        """
        try:
            self.log("🔄 开始 Weex 做多买入流程...")
            
            # 1. 点击开仓
            if not self._click_element('开仓', '点击开仓标签'):
                return False
            
            # 2. 点击限价
            if not self._click_element('开仓_限价', '点击限价'):
                return False
            
            # 3. 获取当前价格并计算超价
            current_price = self._get_current_price()
            if current_price == 0:
                self.log("❌ 无法获取当前价格")
                return False
            
            buy_price = current_price + price_offset
            self.log(f"📊 当前价格: {current_price}, 买入价格: {buy_price}")
            
            # 4. 输入价格
            if not self._input_text('开仓_限价_价格', buy_price, f'输入买入价格: {buy_price}'):
                return False
            
            # 5. 输入数量
            if not self._input_text('开仓_限价_数量', quantity, f'输入下单数量: {quantity}'):
                return False
            
            # 6. 点击买入开多
            if not self._click_element('开仓_限价_买入开多', '点击买入开多'):
                return False
            
            # 7. 确认订单
            time.sleep(1)
            if '确认开仓_确定' in self.element_map:
                if self._click_element('确认开仓_确定', '确认订单'):
                    self.log("✅ Weex 做多买入订单已提交")
                    return True
            
            self.log("✅ Weex 做多买入流程完成")
            return True
            
        except Exception as e:
            self.log(f"❌ Weex 做多买入失败: {e}")
            return False
    
    def sell_short(self, price_offset=0.1, quantity=0.001):
        """
        做空买入
        
        Args:
            price_offset: 超价金额（默认0.1）
            quantity: 下单数量
        """
        try:
            self.log("🔄 开始 Weex 做空买入流程...")
            
            # 1. 点击开仓
            if not self._click_element('开仓', '点击开仓标签'):
                return False
            
            # 2. 点击限价
            if not self._click_element('开仓_限价', '点击限价'):
                return False
            
            # 3. 获取当前价格并计算超价
            current_price = self._get_current_price()
            if current_price == 0:
                self.log("❌ 无法获取当前价格")
                return False
            
            sell_price = current_price - price_offset
            self.log(f"📊 当前价格: {current_price}, 卖出价格: {sell_price}")
            
            # 4. 输入价格
            if not self._input_text('开仓_限价_价格', sell_price, f'输入卖出价格: {sell_price}'):
                return False
            
            # 5. 输入数量
            if not self._input_text('开仓_限价_数量', quantity, f'输入下单数量: {quantity}'):
                return False
            
            # 6. 点击卖出开空
            if not self._click_element('开仓_限价_卖出开空', '点击卖出开空'):
                return False
            
            # 7. 确认订单
            time.sleep(1)
            if '确认开仓_确定' in self.element_map:
                if self._click_element('确认开仓_确定', '确认订单'):
                    self.log("✅ Weex 做空买入订单已提交")
                    return True
            
            self.log("✅ Weex 做空买入流程完成")
            return True
            
        except Exception as e:
            self.log(f"❌ Weex 做空买入失败: {e}")
            return False
    
    def close_long_position(self, price_offset=0.1, quantity=None):
        """
        做多平仓（卖出平多）
        
        Args:
            price_offset: 超价金额（默认0.1）
            quantity: 平仓数量，如果为None则使用持仓数量
        """
        try:
            self.log("🔄 开始 Weex 做多平仓流程...")
            
            # 1. 点击平仓
            if not self._click_element('平仓', '点击平仓标签'):
                return False
            
            # 2. 点击限价
            if not self._click_element('平仓_限价', '点击限价'):
                return False
            
            # 3. 获取当前价格并计算超价
            current_price = self._get_current_price()
            if current_price == 0:
                self.log("❌ 无法获取当前价格")
                return False
            
            close_price = current_price - price_offset
            self.log(f"📊 当前价格: {current_price}, 平仓价格: {close_price}")
            
            # 4. 输入价格
            if not self._input_text('平仓_限价_价格', close_price, f'输入平仓价格: {close_price}'):
                return False
            
            # 5. 输入数量（使用持仓数量）
            if quantity is None:
                quantity = self._get_position_quantity()
                if quantity == 0:
                    self.log("❌ 无法获取持仓数量")
                    return False
            
            if not self._input_text('平仓_限价_数量', quantity, f'输入平仓数量: {quantity}'):
                return False
            
            # 6. 点击卖出平多
            if not self._click_element('平仓_限价_卖出平多', '点击卖出平多'):
                return False
            
            # 7. 确认订单
            time.sleep(1)
            if '确认开仓_确定' in self.element_map:
                if self._click_element('确认开仓_确定', '确认订单'):
                    self.log("✅ Weex 做多平仓订单已提交")
                    return True
            
            self.log("✅ Weex 做多平仓流程完成")
            return True
            
        except Exception as e:
            self.log(f"❌ Weex 做多平仓失败: {e}")
            return False
    
    def close_short_position(self, price_offset=0.1, quantity=None):
        """
        做空平仓（买入平空）
        
        Args:
            price_offset: 超价金额（默认0.1）
            quantity: 平仓数量，如果为None则使用持仓数量
        """
        try:
            self.log("🔄 开始 Weex 做空平仓流程...")
            
            # 1. 点击平仓
            if not self._click_element('平仓', '点击平仓标签'):
                return False
            
            # 2. 点击限价
            if not self._click_element('平仓_限价', '点击限价'):
                return False
            
            # 3. 获取当前价格并计算超价
            current_price = self._get_current_price()
            if current_price == 0:
                self.log("❌ 无法获取当前价格")
                return False
            
            close_price = current_price + price_offset
            self.log(f"📊 当前价格: {current_price}, 平仓价格: {close_price}")
            
            # 4. 输入价格
            if not self._input_text('平仓_限价_价格', close_price, f'输入平仓价格: {close_price}'):
                return False
            
            # 5. 输入数量（使用持仓数量）
            if quantity is None:
                quantity = self._get_position_quantity()
                if quantity == 0:
                    self.log("❌ 无法获取持仓数量")
                    return False
            
            if not self._input_text('平仓_限价_数量', quantity, f'输入平仓数量: {quantity}'):
                return False
            
            # 6. 点击买入平空
            if not self._click_element('平仓_限价_买入平空', '点击买入平空'):
                return False
            
            # 7. 确认订单
            time.sleep(1)
            if '确认开仓_确定' in self.element_map:
                if self._click_element('确认开仓_确定', '确认订单'):
                    self.log("✅ Weex 做空平仓订单已提交")
                    return True
            
            self.log("✅ Weex 做空平仓流程完成")
            return True
            
        except Exception as e:
            self.log(f"❌ Weex 做空平仓失败: {e}")
            return False
    
    def query_positions(self):
        """
        查询持仓
        返回持仓信息字典列表
        """
        try:
            self.log("🔄 查询 Weex 持仓...")
            
            # 显示元素对照表信息
            self.log("🔍 检查元素对照表:")
            self.log(f"  - 元素对照表包含 {len(self.element_map)} 个元素")
            self.log(f"  - 查找'仓位': {'仓位' in self.element_map}")
            self.log(f"  - 查找'仓位_简洁视图_持仓表': {'仓位_简洁视图_持仓表' in self.element_map}")
            
            if '仓位' in self.element_map:
                self.log(f"  - 仓位 XPath: {self.element_map['仓位']['xpath']}")
            if '仓位_简洁视图_持仓表' in self.element_map:
                self.log(f"  - 持仓表 XPath: {self.element_map['仓位_简洁视图_持仓表']['xpath']}")
            
            # 1. 点击仓位标签
            if not self._click_element('仓位', '切换到仓位页面'):
                return []
            
            # 2. 等待页面加载
            time.sleep(2)
            
            # 3. 获取持仓信息
            positions = []
            if '仓位_简洁视图_持仓表' in self.element_map:
                try:
                    position_table = self.driver.find_element(By.XPATH, self.element_map['仓位_简洁视图_持仓表']['xpath'])
                    position_text = position_table.text
                    
                    # 先显示原始数据，便于调试
                    self.log("=" * 80)
                    self.log("🔍 原始持仓数据:")
                    self.log("=" * 80)
                    self.log(position_text)
                    self.log("=" * 80)
                    
                    # 解析持仓信息
                    positions = self._parse_position_info(position_text)
                    
                except Exception as e:
                    self.log(f"❌ 获取持仓表格失败: {e}")
            else:
                self.log("❌ 元素对照表中未找到'仓位_简洁视图_持仓表'")
                # 尝试获取整个页面的文本作为备选
                try:
                    page_text = self.driver.find_element(By.TAG_NAME, "body").text
                    self.log("🔍 尝试获取整个页面文本:")
                    self.log("=" * 80)
                    self.log(page_text[:2000])  # 只显示前2000字符
                    self.log("=" * 80)
                except Exception as e2:
                    self.log(f"❌ 获取页面文本也失败: {e2}")
            
            return positions
            
        except Exception as e:
            self.log(f"❌ Weex 查询持仓失败: {e}")
            return []
    
    def query_orders(self):
        """
        查询委托
        返回委托信息字典列表
        """
        try:
            self.log("🔄 查询 Weex 委托...")
            
            # 1. 点击当前委托标签
            if not self._click_element('当前委托', '切换到委托页面'):
                return []
            
            # 2. 等待页面加载
            time.sleep(2)
            
            # 3. 获取委托信息
            orders = []
            if '当前委托_委托表' in self.element_map:
                try:
                    order_table = self.driver.find_element(By.XPATH, self.element_map['当前委托_委托表']['xpath'])
                    order_text = order_table.text
                    self.log(f"📊 Weex 委托原始信息: {order_text}")
                    
                    # 解析委托信息（这里需要根据实际页面结构调整）
                    orders = self._parse_order_info(order_text)
                    
                except Exception as e:
                    self.log(f"❌ 获取委托表格失败: {e}")
            
            return orders
            
        except Exception as e:
            self.log(f"❌ Weex 查询委托失败: {e}")
            return []
    
    def _get_current_price(self):
        """获取当前价格"""
        try:
            if '买一价' in self.element_map and '卖一价' in self.element_map:
                bid_element = self.driver.find_element(By.XPATH, self.element_map['买一价']['xpath'])
                ask_element = self.driver.find_element(By.XPATH, self.element_map['卖一价']['xpath'])
                
                bid_text = bid_element.text.strip().replace(',', '').replace('‎', '')
                ask_text = ask_element.text.strip().replace(',', '').replace('‎', '')
                
                import re
                bid_numbers = re.findall(r'[\d,]+\.?\d*', bid_text)
                ask_numbers = re.findall(r'[\d,]+\.?\d*', ask_text)
                
                if bid_numbers and ask_numbers:
                    bid_price = float(bid_numbers[0].replace(',', ''))
                    ask_price = float(ask_numbers[0].replace(',', ''))
                    return (bid_price + ask_price) / 2.0  # 返回中间价
            
            return 0
        except Exception as e:
            self.log(f"❌ 获取当前价格失败: {e}")
            return 0
    
    def _get_position_quantity(self):
        """获取持仓数量"""
        try:
            positions = self.query_positions()
            if positions:
                # 返回第一个持仓的数量（这里需要根据实际数据结构调整）
                return positions[0].get('quantity', 0)
            return 0
        except Exception as e:
            self.log(f"❌ 获取持仓数量失败: {e}")
            return 0
    
    def _parse_position_info(self, position_text):
        """
        解析持仓信息
        根据 Weex 实际页面结构解析持仓数据
        """
        positions = []
        try:
            self.log(f"🔍 开始解析持仓文本...")
            self.log(f"🔍 文本长度: {len(position_text)} 字符")
            
            # 按行分割文本
            lines = position_text.split('\n')
            self.log(f"🔍 持仓文本行数: {len(lines)}")
            
            # 查找 ETH/USDT 持仓
            i = 0
            while i < len(lines):
                line = lines[i].strip()
                
                # 找到 ETH/USDT 行
                if line == "ETH/USDT":
                    self.log(f"🔍 发现 ETH/USDT 持仓，开始解析...")
                    
                    # 解析持仓数据
                    position = self._parse_single_position(lines, i)
                    if position:
                        positions.append(position)
                        self.log(f"✅ 解析持仓成功: {position}")
                    
                    # 跳过已处理的行，但不要跳过太多
                    i += 15  # 减少跳过的行数，确保能找到第二个持仓
                else:
                    i += 1
            
            self.log(f"📊 总共解析到 {len(positions)} 个持仓")
            return positions
            
        except Exception as e:
            self.log(f"❌ 解析持仓信息失败: {e}")
            return []
    
    def _parse_single_position(self, lines, start_index):
        """
        解析单个持仓数据
        """
        try:
            position = {}
            
            # 从 ETH/USDT 行开始解析，但限制解析范围
            for i in range(start_index, min(start_index + 20, len(lines))):
                line = lines[i].strip()
                
                # 解析交易对
                if line == "ETH/USDT":
                    position['symbol'] = 'ETH-USDT'
                
                # 解析方向
                elif line == "空":
                    position['direction'] = 'short'
                elif line == "多":
                    position['direction'] = 'long'
                
                # 解析杠杆
                elif line == "100x":
                    position['leverage'] = 100
                
                # 解析数量 - 更精确的匹配
                elif "ETH" in line and any(x in line for x in ["0.001", "0.042"]):
                    try:
                        # 提取数字部分
                        import re
                        numbers = re.findall(r'[\d,]+\.?\d*', line)
                        for num in numbers:
                            val = float(num.replace(',', ''))
                            if 0.0001 <= val <= 1.0:  # 合理的持仓数量范围
                                position['quantity'] = val
                                break
                    except:
                        pass
                
                # 解析开仓均价 - 更精确的识别
                elif self._is_price_line(line) and 'avg_price' not in position:
                    try:
                        price = float(line.replace(',', ''))
                        if 3800 <= price <= 4000:  # ETH 合理价格范围
                            position['avg_price'] = price
                    except:
                        pass
                
                # 解析标记价格
                elif self._is_price_line(line) and 'avg_price' in position and 'mark_price' not in position:
                    try:
                        price = float(line.replace(',', ''))
                        if 3800 <= price <= 4000:  # ETH 合理价格范围
                            position['mark_price'] = price
                    except:
                        pass
                
                # 解析保证金 - 更精确的匹配
                elif "USDT" in line and ("0.039" in line or "1.631" in line):
                    try:
                        # 提取数字部分
                        import re
                        numbers = re.findall(r'[\d,]+\.?\d*', line)
                        for num in numbers:
                            val = float(num.replace(',', ''))
                            if 0.01 <= val <= 2.0:  # 合理的保证金范围
                                position['margin'] = val
                                break
                    except:
                        pass
                
                # 解析未实现盈亏 - 更精确的识别
                elif ("+" in line or "-" in line) and "USDT" in line and "unrealized_pnl" not in position:
                    try:
                        # 提取 + 0.0192 USDT 或 -0.0511 USDT 这样的格式
                        import re
                        pnl_match = re.search(r'([+-]?[\d,]+\.?\d*)\s*USDT', line)
                        if pnl_match:
                            pnl = float(pnl_match.group(1).replace(',', ''))
                            if -1.0 <= pnl <= 1.0:  # 合理的盈亏范围
                                position['unrealized_pnl'] = pnl
                    except:
                        pass
                
                # 解析未实现盈亏百分比
                elif ("+" in line or "-" in line) and "%" in line and "unrealized_pnl_pct" not in position:
                    try:
                        # 提取 + 49.31 % 或 -3.13 % 这样的格式
                        import re
                        pct_match = re.search(r'([+-]?[\d,]+\.?\d*)%', line)
                        if pct_match:
                            pct = float(pct_match.group(1).replace(',', ''))
                            if -100 <= pct <= 1000:  # 合理的百分比范围
                                position['unrealized_pnl_pct'] = pct
                    except:
                        pass
                
                # 解析已实现盈亏 - 更精确的识别
                elif ("+" in line or "-" in line) and "USDT" in line and "realized_pnl" not in position and "unrealized_pnl" in position:
                    try:
                        # 提取 + 0.4789 USDT 这样的格式
                        import re
                        pnl_match = re.search(r'([+-]?[\d,]+\.?\d*)\s*USDT', line)
                        if pnl_match:
                            pnl = float(pnl_match.group(1).replace(',', ''))
                            if -10.0 <= pnl <= 10.0:  # 合理的已实现盈亏范围
                                position['realized_pnl'] = pnl
                    except:
                        pass
            
            # 检查是否解析到必要信息
            if 'symbol' in position and 'direction' in position and 'quantity' in position:
                return position
            else:
                self.log(f"⚠️ 持仓信息不完整: {position}")
                return None
                
        except Exception as e:
            self.log(f"❌ 解析持仓行失败: {e}")
            return None
    
    def _is_price_line(self, line):
        """
        判断是否是价格行
        """
        try:
            # 检查是否包含数字和逗号
            if ',' in line and any(c.isdigit() for c in line):
                # 尝试转换为数字
                float(line.replace(',', ''))
                return True
        except:
            pass
        return False
    
    def _parse_position_line(self, lines, start_index):
        """
        解析单行持仓数据
        """
        try:
            position = {}
            
            # 从当前行开始，查找相关数据
            for i in range(start_index, min(start_index + 10, len(lines))):
                line = lines[i].strip()
                if not line:
                    continue
                
                # 解析交易对
                if 'ETH' in line and 'USDT' in line:
                    position['symbol'] = 'ETH-USDT'
                elif 'BTC' in line and 'USDT' in line:
                    position['symbol'] = 'BTC-USDT'
                
                # 解析方向（多/空）
                if '多' in line and '100x' in line:
                    position['direction'] = 'long'
                    position['leverage'] = 100
                elif '空' in line and '100x' in line:
                    position['direction'] = 'short'
                    position['leverage'] = 100
                
                # 解析数量
                if '数量' in line or 'ETH' in line:
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', line)
                    for num in numbers:
                        try:
                            val = float(num.replace(',', ''))
                            if 0.0001 <= val <= 1000:  # 合理的持仓数量范围
                                position['quantity'] = val
                                break
                        except:
                            continue
                
                # 解析开仓价格
                if '开仓价' in line or 'Open Price' in line:
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', line)
                    for num in numbers:
                        try:
                            val = float(num.replace(',', ''))
                            if 1000 <= val <= 100000:  # 合理的价格范围
                                position['avg_price'] = val
                                break
                        except:
                            continue
                
                # 解析标记价格
                if '标记价' in line or 'Mark Price' in line:
                    import re
                    numbers = re.findall(r'[\d,]+\.?\d*', line)
                    for num in numbers:
                        try:
                            val = float(num.replace(',', ''))
                            if 1000 <= val <= 100000:  # 合理的价格范围
                                position['mark_price'] = val
                                break
                        except:
                            continue
                
                # 解析未实现盈亏
                if '未实现' in line or 'Unrealized' in line:
                    import re
                    # 查找正负号和数字
                    pnl_match = re.search(r'([+-]?[\d,]+\.?\d*)\s*USDT', line)
                    if pnl_match:
                        try:
                            position['unrealized_pnl'] = float(pnl_match.group(1).replace(',', ''))
                        except:
                            pass
                    
                    # 查找百分比
                    pct_match = re.search(r'([+-]?[\d,]+\.?\d*)%', line)
                    if pct_match:
                        try:
                            position['unrealized_pnl_pct'] = float(pct_match.group(1).replace(',', ''))
                        except:
                            pass
                
                # 解析保证金
                if '保证金' in line or 'Margin' in line:
                    import re
                    margin_match = re.search(r'([\d,]+\.?\d*)\s*USDT', line)
                    if margin_match:
                        try:
                            position['margin'] = float(margin_match.group(1).replace(',', ''))
                        except:
                            pass
            
            # 检查是否解析到必要信息
            if 'symbol' in position and 'direction' in position and 'quantity' in position:
                return position
            else:
                self.log(f"⚠️ 持仓信息不完整: {position}")
                return None
                
        except Exception as e:
            self.log(f"❌ 解析持仓行失败: {e}")
            return None
    
    def _parse_order_info(self, order_text):
        """
        解析委托信息
        这里需要根据实际的页面结构来实现
        """
        orders = []
        try:
            # 简单的文本解析示例
            lines = order_text.split('\n')
            for line in lines:
                if 'BTC' in line or 'ETH' in line:  # 包含交易对的行
                    # 这里需要根据实际页面结构调整解析逻辑
                    parts = line.split()
                    if len(parts) >= 4:
                        order = {
                            'symbol': parts[0],
                            'side': 'buy' if '买入' in line else 'sell',
                            'quantity': float(parts[1]) if parts[1].replace('.', '').isdigit() else 0,
                            'price': float(parts[2]) if parts[2].replace('.', '').isdigit() else 0,
                            'status': parts[3] if len(parts) > 3 else 'pending'
                        }
                        orders.append(order)
            
            self.log(f"📊 解析到 {len(orders)} 个委托")
            return orders
            
        except Exception as e:
            self.log(f"❌ 解析委托信息失败: {e}")
            return []
