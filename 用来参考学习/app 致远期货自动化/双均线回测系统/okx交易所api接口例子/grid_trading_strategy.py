#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格交易策略核心逻辑
"""

import time
import threading
import queue
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime
import logging
import platform
import queue

@dataclass
class GridOrder:
    """网格订单数据类"""
    grid_id: str
    price: float
    side: str  # 'buy' or 'sell'
    size: float
    status: str  # 'pending', 'filled', 'cancelled'
    order_id: Optional[str] = None
    create_time: str = ""
    
@dataclass
class TradeRecord:
    """交易记录数据类"""
    trade_id: str
    order_id: str
    side: str
    price: float
    size: float
    fee: float
    timestamp: str

@dataclass
class OperationLog:
    """操作日志数据类"""
    log_id: str
    timestamp: str
    operation_type: str  # 'create_position', 'place_order', 'cancel_order', 'order_filled'
    details: dict
    price: float = 0.0  # 操作价格（挂单价格、成交价格等）
    size: float = 0.0   # 操作数量
    order_id: str = ""  # 订单ID
    grid_id: str = ""   # 网格ID
    current_price: float = 0.0  # 操作时的实时市场价格

class DynamicGridTradingStrategy:
    """动态网格交易策略"""
    
    def __init__(self, client, instrument, base_price, grid_width, trade_size, 
                 down_grids=20, up_grids=1, db_manager=None, strategy_id=None):
        """初始化动态网格交易策略"""
        self.client = client
        self.instrument = instrument
        self.base_price = base_price
        self.grid_width = grid_width
        self.trade_size = trade_size
        self.down_grids = down_grids
        self.up_grids = up_grids
        self.db_manager = db_manager
        
        # 使用固定的策略ID，而不是时间戳
        if strategy_id:
            self.strategy_id = strategy_id
        else:
            # 使用固定的策略ID格式
            self.strategy_id = f"grid_strategy_{instrument}"
        
        # 初始化网格相关变量
        self.grid_prices = []
        self.grids = {}  # 存储网格订单的字典
        self.current_price = 0.0
        self.current_position = 0.0
        self.total_profit = 0.0
        self.active_orders_count = 0
        self.expected_buy_orders = []
        self.expected_sell_orders = []
        self.trade_records = []  # 交易记录列表
        self.operation_logs = []  # 操作日志列表
        self.max_drawdown = 0.0  # 最大回撤
        
        # 最近一次成交信息（用于“以成交价为中心 ± 一个网格”重挂单）
        self.last_fill_price = None  # 最近一次成交价
        self.last_fill_side = None   # 'buy' 或 'sell'
        
        # 策略运行状态
        self.is_running = False
        
        # 全局互斥：所有改动订单/持仓的操作串行化
        self._order_mutation_lock = threading.Lock()
        # 底仓抖动保护时间戳（到该时间前不再重复建底仓）
        self._base_build_protect_until = 0.0
        # 持仓上限控制（单位份数），默认20份
        self.position_upper_units = 20
        self._last_upper_enforce_ts = 0.0
        self.upper_enforce_cooldown_seconds = 3.0
        
        # 防御性初始化：确保运行时访问的属性存在
        self._building_position = False
        self.verification_cache = {
            'positions': [],
            'price': [],
            'orders': []
        }
        self.verification_timestamps = {
            'positions': 0,
            'price': 0,
            'orders': 0
        }
        
        # 数据验证相关属性
        self.data_verification_attempts = 2
        self.verification_interval = 1.5
        self.min_verification_agreement = 2
        self.max_verification_discrepancy = 0.001
        
        # 价格缓存相关属性
        self.price_cache_ttl = 15
        self.price_verification_cooldown = 10
        self.last_price_verification_ts = 0
        self.cached_price = None
        self.price_cache_timestamp = 0
        self.positions_cache_timestamp = 0
        self.cached_positions = None
        self.cache_validity = 30
        
        # 错误处理和重试相关属性
        self.consecutive_failures = 0
        self.max_consecutive_failures = 5
        self.critical_data_failed = False
        self.max_retries = 3
        self.retry_delay = 5
        self.network_timeout = 10
        self.pause_until = 0
        
        # 交易相关的关键属性
        self.tick_size = None  # 价格步长，启动时从交易所获取
        self.lot_size = None   # 数量步长，启动时从交易所获取
        
        # 订单管理相关属性
        self._rebuilding_orders = False
        self.last_two_order_enforce_ts = 0.0
        self.two_order_enforce_interval = 5.0
        
        # 底仓建立相关属性
        self.last_base_build_ts = 0.0
        self.base_build_cooldown_seconds = 30.0
        self._consecutive_zero_positions = 0
        
        # 成交追踪相关属性
        self.last_seen_fill_id = None
        self.center_price_committed = None
        
        # 线程和队列相关属性
        self.strategy_thread = None
        self._db_write_queue = queue.Queue() if 'queue' in globals() else None
        self._db_writer_thread = None
        self.ui_log_callback = None

    def _enforce_upper_limit_if_needed(self):
        """当双挂就绪后执行的持仓上限控制：
        条件：当前持仓>0 且 持仓> upper_units*trade_size 且 交易所侧存在一买一卖挂单。
        动作：市价卖出一份 trade_size，将持仓压回上限。
        """
        try:
            # 仅在有持仓情况下检查
            if self.current_position <= 0:
                return
            # 上限份数
            target_units = max(1, int(getattr(self, 'position_upper_units', 20)))
            max_position = target_units * float(self.trade_size)
            if self.current_position <= max_position:
                return

            # 确认双挂都存在（以交易所 open orders 为准）
            orders = self.client.get_order_list() or []
            my_open = [o for o in orders if o.get('instId') == self.instrument and (o.get('state') in ('live','partially_filled'))]
            has_buy = any(o.get('side') == 'buy' for o in my_open)
            has_sell = any(o.get('side') == 'sell' for o in my_open)
            if not (has_buy and has_sell):
                return

            # 节流
            now_ts = time.time()
            if now_ts - getattr(self, '_last_upper_enforce_ts', 0) <= self.upper_enforce_cooldown_seconds:
                return

            reduce_size = min(float(self.trade_size), self.current_position - max_position)
            if reduce_size <= 0:
                return

            self.log(f"⚖️ 触发上限控制: 当前{self.current_position:.8f}张 > 上限{max_position:.8f}张，市价卖出 {reduce_size:.8f} 张")
            with self._order_mutation_lock:
                self.client.place_order(
                    inst_id=self.instrument,
                    td_mode='cross',
                    side='sell',
                    pos_side='long',
                    ord_type='market',
                    sz=str(reduce_size)
                )
            self._last_upper_enforce_ts = now_ts
        except Exception as e:
            self.log(f"⚠️ 上限控制执行失败: {e}")
        
        # 全局互斥：所有改变订单/持仓的动作只允许单线程执行
        self._order_mutation_lock = threading.Lock()
        
        # 底仓抖动保护（防止短时间内重复建底仓）
        self._base_build_protect_until = 0.0
        
        # 初始化网格价格
        self._initialize_grid_prices()
        
        # 尝试加载现有策略状态
        self._load_strategy_status()
        
        self.log(f"🚀 初始化动态网格策略: {self.strategy_id}")
        self.log(f"  基准价格: ${self.base_price:.8f}")
        self.log(f"  网格宽度: ${self.grid_width:.8f}")
        self.log(f"  交易数量: {self.trade_size}张")
        self.log(f"  向下网格: {self.down_grids}个")
        self.log(f"  向上网格: {self.up_grids}个")
        
        # 错误处理和重试机制相关属性
        self.max_retries = 3  # 最大重试次数
        self.retry_delay = 5  # 重试延迟（秒）
        self.network_timeout = 10  # 网络超时时间（秒）
        self.critical_data_failed = False  # 关键数据获取失败标志
        self.pause_until = 0  # 暂停直到的时间戳
        self.consecutive_failures = 0  # 连续失败次数
        self.max_consecutive_failures = 5  # 最大连续失败次数
        
        # 关键数据缓存
        self.cached_positions = None
        self.cached_price = None
        # 将价格与持仓的缓存时间戳分离，避免相互影响
        self.positions_cache_timestamp = 0
        self.price_cache_timestamp = 0
        self.cache_validity = 30  # 持仓缓存有效期（秒）
        # 价格验证与缓存策略（可调）
        self.price_cache_ttl = 15                # 验证价格缓存有效期（秒）
        self.price_verification_cooldown = 10    # 两次价格验证之间的最小冷却时间（秒）
        self.last_price_verification_ts = 0      # 上次价格验证时间
        
        # 底仓建立防重复标志
        self._building_position = False
        
        # 交易所步进（启动时查询并缓存）
        self.tick_size = None
        self.lot_size = None

        # 数据验证机制相关属性
        self.data_verification_attempts = 2  # 数据验证次数（从3次改为2次，提升执行速度）
        self.verification_interval = 1.5  # 验证间隔（秒，从2秒改为1.5秒）
        self.min_verification_agreement = 2  # 最少需要多少次相同结果
        self.max_verification_discrepancy = 0.001  # 最大允许的数值差异
        
        # 数据验证缓存
        self.verification_cache = {
            'positions': [],
            'price': [],
            'orders': []
        }
        self.verification_timestamps = {
            'positions': 0,
            'price': 0,
            'orders': 0
        }

        # 二单约束节流
        self.last_two_order_enforce_ts = 0.0
        self.two_order_enforce_interval = 5.0  # 秒

        # 记录已应用到委托的中心价（用于事件驱动，只在新成交时重建）
        self.center_price_committed = None
        self.last_seen_fill_id = None
        # 内部流程锁：避免并发重建/下单
        self._rebuilding_orders = False
        # ==== 关键节点日志最小集 ====
        self._log_minimal = True
        self.last_rebuild_ts = 0.0
        self.rebuild_grace_seconds = 5.0
        self.last_base_build_ts = 0.0
        self.base_build_cooldown_seconds = 30.0
        self._consecutive_zero_positions = 0
    
        # 顺序写库队列（保证表内记录顺序与业务顺序一致）
        self._db_write_queue: "queue.Queue" = queue.Queue()
        self._db_writer_thread = threading.Thread(target=self._db_writer_loop, daemon=True)
        self._db_writer_thread.start()

    def _initialize_grid_prices(self):
        """初始化网格价格列表"""
        self.grid_prices = []
        
        # 向上网格价格（卖出网格）- 从高到低
        for i in range(self.up_grids, 0, -1):
            price = self.base_price + (i * self.grid_width)
            self.grid_prices.append(price)
        
        # 基准价格（不用于挂单，只作为参考）
        # self.grid_prices.append(self.base_price)  # 注释掉，避免在基准价格挂卖单
        
        # 向下网格价格（买入网格）- 从高到低
        for i in range(1, self.down_grids + 1):
            price = self.base_price - (i * self.grid_width)
            self.grid_prices.append(price)
        
        # 按价格排序（从高到低）
        self.grid_prices.sort(reverse=True)
        
        self.log(f"初始化网格价格完成，共 {len(self.grid_prices)} 个网格")
        self.log(f"基准价格: ${self.base_price:.8f} (不用于挂单)")
        for i, price in enumerate(self.grid_prices):
            self.log(f"网格 {i}: ${price:.8f}")

        # 保存网格层级到数据库（可视化用）
        if self.db_manager and hasattr(self.db_manager, 'save_grid_levels'):
            try:
                levels = []
                # 上方一级
                levels.append({'level_index': len(self.grid_prices), 'direction': 'up', 'price': self.base_price + self.grid_width})
                # 基准
                levels.append({'level_index': len(self.grid_prices) - 1, 'direction': 'base', 'price': self.base_price})
                # 向下若干
                # grid_prices 已是从高到低排序（含上1格和20个下格）
                # 我们给每个价格一个从高到低的索引
                for idx, p in enumerate(self.grid_prices):
                    dirc = 'up' if p > self.base_price else ('down' if p < self.base_price else 'base')
                    levels.append({'level_index': len(self.grid_prices) - idx - 2, 'direction': dirc, 'price': p})
                self.db_manager.save_grid_levels(self.strategy_id, levels)
                self.log("🗂️ 网格层级已写入数据库(grid_levels)")
            except Exception as e:
                self.log(f"⚠️ 保存网格层级失败: {e}")
    
    def _load_strategy_status(self):
        """加载现有策略状态"""
        if not self.db_manager:
            return
        
        try:
            status_data = self.db_manager.get_strategy_status(self.strategy_id)
            if status_data:
                self.log(f"📋 加载现有策略状态: {self.strategy_id}")
                
                # 恢复交易数量
                if status_data.get('trade_size'):
                    self.trade_size = status_data['trade_size']
                    self.log(f"恢复交易数量: {self.trade_size}张")
                
                # 恢复网格价格
                if status_data.get('grid_prices'):
                    self.grid_prices = status_data['grid_prices']
                    self.log(f"恢复网格价格列表，共 {len(self.grid_prices)} 个网格")
                
                # 恢复预期委托
                if status_data.get('expected_buy_orders'):
                    self.expected_buy_orders = status_data['expected_buy_orders']
                if status_data.get('expected_sell_orders'):
                    self.expected_sell_orders = status_data['expected_sell_orders']
                
                # 恢复网格订单字典 - 这是关键！
                if status_data.get('grids'):
                    try:
                        self.grids = {}
                        grids_data = status_data['grids']
                        for grid_id, grid_data in grids_data.items():
                            grid_order = GridOrder(
                                grid_id=grid_data.get('grid_id', ''),
                                price=grid_data.get('price', 0),
                                side=grid_data.get('side', ''),
                                size=grid_data.get('size', 0),
                                status=grid_data.get('status', 'pending'),
                                order_id=grid_data.get('order_id', ''),
                                create_time=grid_data.get('create_time', '')
                            )
                            self.grids[grid_id] = grid_order
                        self.log(f"📋 恢复网格订单: {len(self.grids)}个")
                    except Exception as e:
                        self.log(f"❌ 恢复网格订单失败: {e}")
                        self.grids = {}  # 确保是空字典
                else:
                    self.log("📋 没有历史网格订单数据，使用空字典")
                    self.grids = {}
                
                # 从交易所获取实时的long方向持仓
                current_position = 0
                positions = self.client.get_positions()
                if positions:
                    for position in positions:
                        if (position.get('instId') == self.instrument and 
                            position.get('posSide') == 'long'):  # 只统计long方向
                            current_position = float(position.get('pos', '0'))
                            break
                
                self.current_position = current_position
                # 重置盈利，避免加载错误的历史数据
                self.total_profit = 0.0
                self.log("🔄 重置盈利计算，从0开始")
                
                # 从数据库加载历史交易记录
                if self.db_manager:
                    try:
                        trade_records = self.db_manager.get_trade_history(self.strategy_id)
                        for trade in trade_records:
                            trade_record = TradeRecord(
                                trade_id=trade.get('trade_id', ''),
                                order_id=trade.get('order_id', ''),
                                side=trade.get('side', ''),
                                price=trade.get('price', 0),
                                size=trade.get('size', 0),
                                fee=trade.get('fee', 0),
                                timestamp=trade.get('timestamp', '')
                            )
                            self.trade_records.append(trade_record)
                        self.log(f"📋 加载历史交易记录: {len(trade_records)} 条")
                    except Exception as e:
                        self.log(f"❌ 加载历史交易记录失败: {e}")
                
                # 恢复最近一次成交信息（用于以成交价为中心挂单）
                try:
                    self.last_fill_price = float(status_data.get('last_fill_price', 0) or 0)
                except Exception:
                    self.last_fill_price = 0.0
                self.last_fill_side = status_data.get('last_fill_side', '') or ''
                if self.last_fill_price > 0:
                    self.log(f"🔄 恢复最近成交: {self.last_fill_side or '未知'} @ ${self.last_fill_price:.8f}")
                else:
                    self.log("ℹ️ 未找到最近成交记录，将在建立底仓后确定中心价")
                
                self.log(f"策略状态已恢复: 持仓 {self.current_position}张, 盈利 {self.total_profit:.4f} USDT")
                return True
            else:
                self.log("📋 未找到现有策略状态，将创建新策略")
                return False
        except Exception as e:
            self.log(f"❌ 加载策略状态失败: {e}")
            return False
    
    def _save_strategy_status(self):
        """保存策略状态"""
        if not self.db_manager:
            return
        
        try:
            current_price = self.get_current_price()
            current_grid_index = self.find_current_grid_index(current_price)
            current_grid_price = self.grid_prices[current_grid_index] if current_grid_index < len(self.grid_prices) else 0
            
            # 获取当前持仓 - 只统计long方向的持仓
            current_position = 0
            positions = self.client.get_positions()
            if positions:
                for position in positions:
                    if (position.get('instId') == self.instrument and 
                        position.get('posSide') == 'long'):  # 只统计long方向
                        current_position = float(position.get('pos', '0'))
                        break
            
            # 获取当前委托
            current_orders = self.client.get_order_list()
            # 只统计属于当前策略的订单
            strategy_orders = []
            if current_orders:
                for order in current_orders:
                    if order.get('instId') == self.instrument:
                        # 检查是否属于策略管理的订单
                        order_id = order.get('ordId')
                        is_strategy_order = False
                        for grid_order in self.grids.values():
                            if grid_order.order_id == order_id:
                                is_strategy_order = True
                                break
                        if is_strategy_order:
                            strategy_orders.append(order)
            
            active_orders_count = len(strategy_orders)
            
            # 确定网格方向
            if current_grid_index == 0:
                grid_direction = "上"
                grid_number = 1
            elif current_grid_index == len(self.grid_prices) - 1:
                grid_direction = "下"
                grid_number = len(self.grid_prices)
            else:
                grid_direction = "下" if current_grid_index > len(self.grid_prices) // 2 else "上"
                grid_number = current_grid_index + 1
            
            # 计算每个网格应该的持仓数量
            grid_positions = {}
            for i, price in enumerate(self.grid_prices):
                if i < current_grid_index:
                    # 向上网格，应该没有持仓
                    grid_positions[f"grid_{i}"] = 0
                else:
                    # 向下网格，应该有持仓
                    grid_positions[f"grid_{i}"] = self.trade_size
            
            # 确定下一个挂单价格
            next_buy_price = None
            next_sell_price = None
            
            if current_grid_index < len(self.grid_prices) - 1:
                next_buy_price = self.grid_prices[current_grid_index + 1]
            
            if current_grid_index > 0:
                next_sell_price = self.grid_prices[current_grid_index - 1]
            
            # 保存网格订单数据
            grids_data = {}
            for grid_id, grid_order in self.grids.items():
                grids_data[grid_id] = {
                    'grid_id': grid_order.grid_id,
                    'price': grid_order.price,
                    'side': grid_order.side,
                    'size': grid_order.size,
                    'status': grid_order.status,
                    'order_id': grid_order.order_id,
                    'create_time': grid_order.create_time
                }
            
            status_data = {
                'instrument': self.instrument,
                'base_price': self.base_price,
                'grid_width': self.grid_width,
                'trade_size': self.trade_size,  # 新增：保存交易数量
                'current_price': current_price,
                'current_grid_index': current_grid_index,
                'current_grid_price': current_grid_price,
                'grid_direction': grid_direction,
                'grid_number': grid_number,
                'down_grids': self.down_grids,
                'up_grids': self.up_grids,
                'grid_prices': self.grid_prices,
                'expected_buy_orders': self.expected_buy_orders,
                'expected_sell_orders': self.expected_sell_orders,
                'grids': grids_data,  # 新增：保存网格订单数据
                'current_position': current_position,
                'total_profit': self.total_profit,
                'active_orders_count': active_orders_count,
                'grid_positions': grid_positions,  # 每个网格应该的持仓数量
                'next_buy_price': next_buy_price,  # 下一个买单价格
                'next_sell_price': next_sell_price,  # 下一个卖单价格
                'strategy_state': 'running' if self.is_running else 'stopped',
                'last_action': 'order_placed',  # 最后执行的动作
                'next_action': 'wait_for_fill',  # 下一步行动计划
                'last_update_time': datetime.now().isoformat(),
                'last_fill_price': self.last_fill_price or 0.0,
                'last_fill_side': self.last_fill_side or '',
                'last_fill_ts': datetime.now().isoformat()
            }
            
            self.db_manager.save_strategy_status(self.strategy_id, status_data)
            self.log(f"💾 策略状态已保存: 持仓{current_position}张, 活跃委托{active_orders_count}个")
            
        except Exception as e:
            self.log(f"❌ 保存策略状态失败: {e}")
    
    def _generate_expected_orders(self):
        """生成预期委托列表 - 只创建当前需要的委托"""
        self.expected_buy_orders = []
        self.expected_sell_orders = []
        
        # 优先基于最近一次成交价生成：在成交价上下各一个网格
        if self.last_fill_price and self.grid_width > 0:
            buy_price = self.last_fill_price - self.grid_width
            sell_price = self.last_fill_price + self.grid_width
            self.expected_buy_orders.append({
                'grid_id': f"grid_down_center",
                'price': buy_price,
                'size': self.trade_size,
                'side': 'buy'
            })
            self.expected_sell_orders.append({
                'grid_id': f"grid_up_center",
                'price': sell_price,
                'size': self.trade_size,
                'side': 'sell'
            })
            self.log(f"🎯 基于成交价生成预期委托: 买@${buy_price:.2f}, 卖@${sell_price:.2f}")
            self.log(f"生成预期委托: {len(self.expected_buy_orders)}个买单, {len(self.expected_sell_orders)}个卖单")
            return

        # 🔥 回退方案：使用更宽松的价格获取方式，避免因严格验证导致无法生成订单
        current_price = self.get_current_price()
        
        # 如果严格验证失败，尝试使用缓存价格或直接获取
        if current_price <= 0:
            self.log("⚠️ 严格价格验证失败，尝试使用缓存价格...")
            
            # 尝试使用缓存的价格
            cached_price_data = self.verification_cache.get('price')
            if cached_price_data and cached_price_data.get('price', 0) > 0:
                current_price = cached_price_data['price']
                self.log(f"✅ 使用缓存价格: ${current_price:.8f}")
            else:
                # 如果缓存也没有，尝试直接获取价格（不使用严格验证）
                try:
                    raw_data = self.client.get_ticker(inst_id=self.instrument)
                    if raw_data and 'data' in raw_data and raw_data['data']:
                        ticker_data = raw_data['data'][0]
                        if ticker_data and ticker_data.get('last'):
                            current_price = float(ticker_data['last'])
                            self.log(f"✅ 直接获取价格成功: ${current_price:.8f}")
                        else:
                            self.log("❌ 无法获取有效价格数据")
                            return
                    else:
                        self.log("❌ 无法获取价格数据")
                        return
                except Exception as e:
                    self.log(f"❌ 直接获取价格失败: {e}")
            return
        
        # 🔥 修复：基于当前价格直接计算最近的买卖单价格，而不依赖网格索引
        
        # 找到当前价格上方最近的网格（卖单）
        sell_price = None
        sell_grid_id = None
        for i, grid_price in enumerate(self.grid_prices):
            if grid_price > current_price:
                sell_price = grid_price
                sell_grid_id = f"grid_up_{i + 1}"
                break
        
        # 找到当前价格下方最近的网格（买单）
        buy_price = None
        buy_grid_id = None
        for i, grid_price in enumerate(self.grid_prices):
            if grid_price < current_price:
                buy_price = grid_price
                buy_grid_id = f"grid_down_{i + 1}"
                break
        
        # 创建卖单（如果找到了上方网格）
        if sell_price and sell_grid_id:
            self.expected_sell_orders.append({
                'grid_id': sell_grid_id,
                'price': sell_price,
                'size': self.trade_size,
                'side': 'sell'
            })
            self.log(f"📈 生成卖单: ${sell_price:.2f} (当前价格上方最近网格)")
        
        # 创建买单（如果找到了下方网格）
        if buy_price and buy_grid_id:
            self.expected_buy_orders.append({
                'grid_id': buy_grid_id,
                'price': buy_price,
                'size': self.trade_size,
                'side': 'buy'
            })
            self.log(f"📉 生成买单: ${buy_price:.2f} (当前价格下方最近网格)")
        
        self.log(f"生成预期委托: {len(self.expected_buy_orders)}个买单, {len(self.expected_sell_orders)}个卖单")
    
    def _sync_orders_with_exchange(self, ask_confirmation=True):
        """同步委托与交易所"""
        try:
            # 事件驱动：没有中心价或没有持仓时，不做网格同步
            if not self.last_fill_price or self.current_position <= 0:
                return
            # 获取当前所有委托
            current_orders = self.client.get_order_list()
            current_buy_orders = []
            current_sell_orders = []
            
            # 检查API调用是否成功
            if current_orders is None:
                self.log("⚠️ 无法获取当前委托，跳过同步")
                return
            
            # 分类当前委托
            for order in current_orders:
                if order.get('instId') == self.instrument:  # 只处理当前合约的订单
                    if order.get('side') == 'buy':
                        current_buy_orders.append(order)
                    elif order.get('side') == 'sell':
                        current_sell_orders.append(order)
            
            self.log(f"当前委托: {len(current_buy_orders)}个买单, {len(current_sell_orders)}个卖单")
            
            # 串行：先买后卖，且在同一轮中禁止再次触发重建
            self._sync_buy_orders(current_buy_orders, ask_confirmation)
            self._sync_sell_orders(current_sell_orders, ask_confirmation)
            
            # 仅补单，不做清理未匹配的委托（避免频繁撤挂）
            
            # 保存状态
            self._save_strategy_status()
            
        except Exception as e:
            self.log(f"❌ 同步委托失败: {e}")
            # 即使同步失败，也继续执行，不要卡住程序

    def ensure_two_orders_by_last_fill(self):
        """严格二单约束：
        - 若本合约挂单已存在一买一卖 → 不动作
        - 若没有任何挂单 → 按中心价（最近成交价优先，其次当前价，再次基准价）各挂一买一卖
        - 若仅有一个挂单（不论买或卖，或两张同向/数量异常）→ 先撤本合约所有挂单，再按中心价各挂一买一卖
        """
        try:
            # 串行化：若正在重建，直接跳过
            if self._rebuilding_orders:
                self.log("⏳ 正在重建双单，跳过本次约束")
                return False
            self._rebuilding_orders = True

            if self.current_position <= 0:
                return False

            # 刷新中心价（优先最近成交）
            try:
                self.log("🔎 正在获取最近成交用于确定中心价...")
                fills = self.client.get_recent_fills(self.instrument, limit=1) or []
                if fills:
                    fill = fills[0]
                    fill_id = fill.get('billId') or fill.get('tradeId') or fill.get('ordId')
                    price = float(fill.get('fillPx') or fill.get('px') or 0)
                    side = fill.get('side') or ''
                    if price > 0 and fill_id != self.last_seen_fill_id:
                        self.last_fill_price = price
                        self.last_fill_side = side
                        self.last_seen_fill_id = fill_id
                        side_cn = '买入' if side == 'buy' else '卖出' if side == 'sell' else side
                        self.log(f"🧾 最近成交: {side_cn} @ ${price:.2f} (fillId={fill_id}) → 用作中心价")
                else:
                    self.log("ℹ️ 未获取到最近成交记录，准备使用回退中心价")
            except Exception as e:
                self.log(f"⚠️ 获取最近成交失败: {e}")

            center_price = self.last_fill_price
            if not center_price or center_price <= 0:
                # 回退到当前价
                try:
                    center_price = self.get_current_price() or 0
                    if center_price > 0:
                        self.log(f"📌 使用当前价作为中心价: ${center_price:.2f}")
                except Exception:
                    center_price = 0
            if not center_price or center_price <= 0:
                # 再次回退到基准价
                center_price = self.base_price
                if center_price and center_price > 0:
                    self.log(f"📌 使用基准价作为中心价: ${center_price:.2f}")

            if not center_price or center_price <= 0:
                self.log("⚠️ 无法确定中心价，跳过二单约束")
                return False

            # 计算目标价并对齐步进
            buy_target = center_price - self.grid_width
            sell_target = center_price + self.grid_width
            if self.tick_size:
                buy_target = round(round(buy_target / self.tick_size) * self.tick_size, 8)
                sell_target = round(round(sell_target / self.tick_size) * self.tick_size, 8)

            # 检查当前委托
            current_orders = self.client.get_order_list() or []
            my_orders = [o for o in current_orders if o.get('instId') == self.instrument]
            buy_orders = [o for o in my_orders if o.get('side') == 'buy']
            sell_orders = [o for o in my_orders if o.get('side') == 'sell']

            # 情况A：已是一买一卖 → 不动作
            if len(buy_orders) >= 1 and len(sell_orders) >= 1:
                self.log("✅ 已存在一买一卖挂单，保持不变")
                self.last_two_order_enforce_ts = time.time()
                return True

            # 情况B：没有任何挂单 → 直接补齐一买一卖
            if len(my_orders) == 0:
                self._place_order('buy', buy_target, self.trade_size, 'grid_down_center')
                self._place_order('sell', sell_target, self.trade_size, 'grid_up_center')
                self.log(f"🧩 无挂单，按中心价补齐双单: 买@${buy_target:.2f} / 卖@${sell_target:.2f}")
                self.last_two_order_enforce_ts = time.time()
                return True

            # 情况C：只有一个挂单或不规范（两张同向等）→ 先撤后建
            for o in my_orders:
                try:
                    self.client.cancel_order(inst_id=self.instrument, ord_id=o.get('ordId'))
                    # 记录撤单到数据库
                    try:
                        side_name = '买' if (o.get('side') == 'buy') else '卖'
                        px_val = float(o.get('px') or 0)
                        self.log_operation(
                            operation_type=f"撤销{side_name}单",
                            details=f"撤销{side_name}单 {o.get('sz','?')}张 @${px_val:.2f} [ordId={o.get('ordId','')}]",
                            price=px_val,
                            size=float(o.get('sz') or 0),
                            order_id=o.get('ordId',''),
                            grid_id=''
                        )
                    except Exception as _:
                        pass
                except Exception as ce:
                    self.log(f"⚠️ 撤销旧单失败: {ce}")

            self._place_order('buy', buy_target, self.trade_size, 'grid_down_center')
            self._place_order('sell', sell_target, self.trade_size, 'grid_up_center')
            self.log(f"🔁 仅单或不规范，已重建双单: 买@${buy_target:.2f} / 卖@${sell_target:.2f}")
            self.last_two_order_enforce_ts = time.time()
            return True
        except Exception as e:
            self.log(f"❌ ensure_two_orders_by_last_fill 失败: {e}")
            return False
        finally:
            self._rebuilding_orders = False
    
    def _sync_buy_orders(self, current_buy_orders, ask_confirmation):
        """同步买单"""
        # 只补缺的买单；不做清理
        
        for expected_order in self.expected_buy_orders:
            expected_price = expected_order['price']
            expected_size = expected_order['size']
            expected_grid_id = expected_order['grid_id']
            
            # 查找匹配的当前委托
            matching_order = None
            for current_order in current_buy_orders:
                current_price = float(current_order.get('px', 0))
                current_size = float(current_order.get('sz', 0))
                
                # 使用步进容差匹配
                price_ok = True
                size_ok = True
                if self.tick_size:
                    price_ok = abs(current_price - expected_price) <= self.tick_size / 2
                if self.lot_size:
                    size_ok = abs(current_size - expected_size) <= self.lot_size / 2
                if price_ok and size_ok:
                    matching_order = current_order
                    # 记录到网格中（如果还没有记录）
                    if expected_grid_id not in self.grids:
                        self.grids[expected_grid_id] = GridOrder(
                            grid_id=expected_grid_id,
                            price=current_price,
                            side='buy',
                            size=current_size,
                            status='pending',
                            order_id=current_order.get('ordId'),
                            create_time=datetime.now().strftime("%H:%M:%S")
                        )
                    break
            
            if not matching_order:
                # 没有匹配的委托，需要创建
                if ask_confirmation:
                    self.log(f"自动确认创建买单: 价格${expected_price:.8f}, 数量{expected_size}张")
                else:
                    self.log(f"创建买单: 价格${expected_price:.8f}, 数量{expected_size}张")
                
                self._place_order('buy', expected_price, expected_size, expected_grid_id)
    
    def _sync_sell_orders(self, current_sell_orders, ask_confirmation):
        """同步卖单"""
        # 先检查是否有持仓
        if not self._check_position_before_sell():
            self.log("⚠️ 没有持仓，跳过卖单创建")
            return
        
        # 上限控制在 ensure_two_orders_strict 完成后统一执行，不在此处处理
            
        # 只补缺的卖单；不做清理
        
        for expected_order in self.expected_sell_orders:
            expected_price = expected_order['price']
            expected_size = expected_order['size']
            expected_grid_id = expected_order['grid_id']
            
            # 查找匹配的当前委托
            matching_order = None
            for current_order in current_sell_orders:
                    
                current_price = float(current_order.get('px', 0))
                current_size = float(current_order.get('sz', 0))
                
                # 使用步进容差匹配
                price_ok = True
                size_ok = True
                if self.tick_size:
                    price_ok = abs(current_price - expected_price) <= self.tick_size / 2
                if self.lot_size:
                    size_ok = abs(current_size - expected_size) <= self.lot_size / 2
                if price_ok and size_ok:
                    matching_order = current_order
                    
                    # 记录到网格中（如果还没有记录）
                    if expected_grid_id not in self.grids:
                        self.grids[expected_grid_id] = GridOrder(
                            grid_id=expected_grid_id,
                            price=current_price,
                            side='sell',
                            size=current_size,
                            status='pending',
                            order_id=current_order.get('ordId'),
                            create_time=datetime.now().strftime("%H:%M:%S")
                        )
                    break
            
            if not matching_order:
                # 没有匹配的委托，需要创建
                if ask_confirmation:
                    self.log(f"自动确认创建卖单: 价格${expected_price:.8f}, 数量{expected_size}张")
                else:
                    self.log(f"创建卖单: 价格${expected_price:.8f}, 数量{expected_size}张")
                
                self._place_order('sell', expected_price, expected_size, expected_grid_id)
        
        # 不做清理未匹配委托，避免频繁撤挂
    
    def _place_order(self, side, price, size, grid_id):
        """下订单"""
        try:
            # 对于做多网格策略，所有订单都使用long持仓方向
            # buy + long = 开多单，sell + long = 平多单
            pos_side = 'long'

            # 步进对齐
            if self.lot_size:
                size = max(self.lot_size, (int(size / self.lot_size)) * self.lot_size)
            if self.tick_size and price is not None:
                # 取最近tick
                price = round(round(price / self.tick_size) * self.tick_size, 8)
            if size <= 0:
                self.log("❌ 下单数量<=0，取消下单")
                return None
            
            order_result = self.client.place_order(
                inst_id=self.instrument,
                td_mode='cross',
                side=side,
                pos_side=pos_side,
                ord_type='limit',
                px=str(price),
                sz=str(size)
            )
            
            if order_result and order_result.get('ordId'):
                order_id = order_result['ordId']
                self.log(f"✅ 订单创建成功: {side} {size}张 @ ${price:.8f}, 订单ID: {order_id}")
                
                # 记录挂单操作
                side_name = "买" if side == "buy" else "卖"
                self.log_operation(
                    operation_type=f"挂{side_name}单",
                    details=f"挂{side_name}单 {size}张 @${price:.2f} [{grid_id}]",
                    price=price,
                    size=size,
                    order_id=order_id,
                    grid_id=grid_id
                )
                
                # 记录网格订单
                grid_order = GridOrder(
                    grid_id=grid_id,
                    price=price,
                    side=side,
                    size=size,
                    status='pending',
                    order_id=order_id,
                    create_time=datetime.now().isoformat()
                )
                self.grids[grid_id] = grid_order
                
                # 显示当前委托列表
                self._display_current_orders()
                
                # 保存策略状态
                self._save_strategy_status()

                # 二单约束改为由启动/恢复和周期性检查触发，避免下单后立即撤自己造成循环
                
                return order_id
            else:
                self.log(f"❌ 订单创建失败: {order_result}")
                return None
                
        except Exception as e:
            self.log(f"❌ 下订单异常: {e}")
            return None
    
    def _display_current_orders(self):
        """显示当前委托列表"""
        try:
            current_orders = self.client.get_order_list()
            
            if current_orders:
                self.log("当前委托列表:")
                self.log("-" * 60)
                
                for i, order in enumerate(current_orders, 1):
                    self.log(f"委托 {i}:")
                    self.log(f"  交易对: {order.get('instId', '')}")
                    self.log(f"  订单ID: {order.get('ordId', '')}")
                    self.log(f"  委托方向: {order.get('side', '')}")
                    self.log(f"  持仓方向: {order.get('posSide', '')}")
                    self.log(f"  委托类型: {order.get('ordType', '')}")
                    self.log(f"  委托数量: {order.get('sz', '')} 张")
                    self.log(f"  委托价格: {order.get('px', '')}")
                    self.log(f"  委托状态: {order.get('state', '')}")
                    self.log(f"  已成交数量: {order.get('accFillSz', '0')} 张")
                    self.log(f"  委托时间: {order.get('cTime', '')}")
                    self.log("")
            else:
                self.log("当前没有活跃委托")
                
        except Exception as e:
            self.log(f"❌ 显示委托列表失败: {e}")
    
    def _check_position_before_sell(self):
        """检查是否有持仓，有持仓才能挂卖单"""
        try:
            positions = self.client.get_positions()
            if positions:
                for position in positions:
                    if (position.get('instId') == self.instrument and 
                        position.get('posSide') == 'long' and  # 只检查long方向
                        float(position.get('pos', '0')) > 0):
                        self.log(f"✅ 检查持仓: {float(position.get('pos', '0'))}张")
                        return True
            
            self.log("❌ 没有持仓，不能挂卖单")
            return False
            
        except Exception as e:
            self.log(f"❌ 检查持仓失败: {e}")
            return False

    def _is_order_open(self, order) -> bool:
        """判断订单是否为挂单状态（交易所可见未完全成交）。"""
        try:
            state = (order or {}).get('state', '')
            return state in ('live', 'partially_filled')
        except Exception:
            return False

    def _place_order_confirmed(self, side: str, price: float, size: float, grid_id: str):
        """下单并确认在交易所处于挂单(open)状态后再记录。"""
        try:
            # 对齐步进
            if self.lot_size:
                size = max(self.lot_size, (int(size / self.lot_size)) * self.lot_size)
            if self.tick_size and price is not None:
                price = round(round(price / self.tick_size) * self.tick_size, 8)
            if size <= 0:
                self.log("❌ 下单数量<=0，取消下单")
                return None

            # 生成幂等 clOrdId（价格取整到tick，避免不同精度导致重复）
            cl_id_core = f"{self.strategy_id}-{grid_id}-{side}-{round(price or 0, 6)}-{round(size, 6)}"
            cl_id = (cl_id_core.replace(' ', '').replace(':', '').replace('/', '')[:32])

            # 若同 clOrdId 已存在并为open/partially_filled，则直接返回
            try:
                existed = self.client.get_order(inst_id=self.instrument, cl_ord_id=cl_id)
                if existed and existed.get('state') in ('live', 'partially_filled'):
                    ord_id = existed.get('ordId')
                    self.log(f"♻️ 复用已存在订单: {side} {size}张 @ ${price:.8f}, clOrdId={cl_id}, ordId={ord_id}")
                    # 同步入本地grids
                    grid_order = GridOrder(
                        grid_id=grid_id,
                        price=price,
                        side=side,
                        size=size,
                        status='pending',
                        order_id=ord_id,
                        create_time=datetime.now().isoformat()
                    )
                    self.grids[grid_id] = grid_order
                    return ord_id
            except Exception:
                pass

            result = self.client.place_order(
                inst_id=self.instrument,
                td_mode='cross',
                side=side,
                pos_side='long',
                ord_type='limit',
                px=str(price),
                sz=str(size),
                cl_ord_id=cl_id
            )
            if not result or not result.get('ordId'):
                self.log(f"❌ 订单创建失败: {result}")
                return None

            ord_id = result['ordId']

            # 确认订单在交易所为 open 状态
            confirmed = False
            for _ in range(5):
                try:
                    info = self.client.get_order(inst_id=self.instrument, ord_id=ord_id)
                    if info and self._is_order_open(info):
                        confirmed = True
                        break
                except Exception:
                    pass
                time.sleep(0.5)

            if not confirmed:
                self.log(f"⚠️ 订单未确认为open状态，将稍后由对账器纠偏: {ord_id}")
            else:
                self.log(f"✅ 订单创建成功: {side} {size}张 @ ${price:.8f}, 订单ID: {ord_id}")

            # 无论是否确认，都记录到 grids 以便后续对账与撤单
            grid_order = GridOrder(
                grid_id=grid_id,
                price=price,
                side=side,
                size=size,
                status='pending',
                order_id=ord_id,
                create_time=datetime.now().isoformat()
            )
            self.grids[grid_id] = grid_order

            # 记录挂单操作
            side_name = '买' if side == 'buy' else '卖'
            self.log_operation(
                operation_type=f"挂{side_name}单",
                details=f"挂{side_name}单 {size}张 @${price:.2f} [{grid_id}]",
                price=price,
                size=size,
                order_id=ord_id,
                grid_id=grid_id
            )

            self._display_current_orders()
            self._save_strategy_status()

            return ord_id
        except Exception as e:
            self.log(f"❌ 下单并确认异常: {e}")
            return None

    # ===== 关键节点日志封装 =====
    def _fmt_kv(self, **kv) -> str:
        try:
            parts = []
            for k, v in kv.items():
                if isinstance(v, float):
                    parts.append(f"{k}={v:.2f}")
                else:
                    parts.append(f"{k}={v}")
            return " ".join(parts)
        except Exception:
            return ""

    def _log_step(self, tag: str, msg: str = "", **kv):
        if not getattr(self, '_log_minimal', False):
            return
        line = f"[{tag}] {msg}".strip()
        kvs = self._fmt_kv(**kv)
        if kvs:
            line = f"{line} {kvs}"
        self.log(line)

    def _log_orders(self, orders):
        if not getattr(self, '_log_minimal', False):
            return
        try:
            my = [o for o in (orders or []) if o.get('instId') == self.instrument]
            buys = [o for o in my if o.get('side') == 'buy']
            sells = [o for o in my if o.get('side') == 'sell']
            self._log_step("ORDERS", "open snapshot",
                           total=len(my), buy=len(buys), sell=len(sells))
            if buys:
                b = buys[0]
                self._log_step("ORDERS", "BUY",
                               ordId=b.get('ordId'), px=float(b.get('px') or 0), state=b.get('state'))
            if sells:
                s = sells[0]
                self._log_step("ORDERS", "SELL",
                               ordId=s.get('ordId'), px=float(s.get('px') or 0), state=s.get('state'))
        except Exception:
            pass

    def ensure_two_orders_strict(self):
        """严格串行的一买一卖保障流程：
        1) 查询交易所 open orders
        2) 若已是一买一卖 → 返回
        3) 否则：取消全部 → 依据中心价±网格宽度 顺序挂买(确认)→挂卖(确认)
        """
        try:
            if self._rebuilding_orders:
                return False
            if self.current_position <= 0:
                return False

            self._rebuilding_orders = True

            # 1) 读取交易所 open orders
            orders = self.client.get_order_list() or []
            self._log_orders(orders)
            my_orders = [o for o in orders if o.get('instId') == self.instrument and self._is_order_open(o)]
            buy_orders = [o for o in my_orders if o.get('side') == 'buy']
            sell_orders = [o for o in my_orders if o.get('side') == 'sell']

            # 同步检查：本地 grids 侧是否也是一买一卖
            grid_buys = [g for g in self.grids.values() if g.side == 'buy']
            grid_sells = [g for g in self.grids.values() if g.side == 'sell']

            exchange_two_ok = (len(buy_orders) >= 1 and len(sell_orders) >= 1)
            grids_two_ok = (len(grid_buys) >= 1 and len(grid_sells) >= 1)

            if exchange_two_ok and grids_two_ok:
                self._log_step("STATE", "two-orders-ok")
                return True

            # 2) 取消全部 open orders 并等待清空
            reason = "not_two_orders"
            if exchange_two_ok and not grids_two_ok:
                reason = "grids_mismatch"
            self._log_step("REBUILD", "start", reason=reason,
                           buy=len(buy_orders), sell=len(sell_orders),
                           grid_buy=len(grid_buys), grid_sell=len(grid_sells))
            for o in my_orders:
                try:
                    self.client.cancel_order(inst_id=self.instrument, ord_id=o.get('ordId'))
                    try:
                        side_name = '买' if (o.get('side') == 'buy') else '卖'
                        px_val = float(o.get('px') or 0)
                        self.log_operation(
                            operation_type=f"撤销{side_name}单",
                            details=f"撤销{side_name}单 {o.get('sz','?')}张 @${px_val:.2f} [ordId={o.get('ordId','')}]",
                            price=px_val,
                            size=float(o.get('sz') or 0),
                            order_id=o.get('ordId',''),
                            grid_id=''
                        )
                        self._log_step("CANCEL", side_name, ordId=o.get('ordId'), px=px_val)
                    except Exception:
                        pass
                except Exception as ce:
                    self.log(f"⚠️ 撤销旧单失败: {ce}")

            # 等待交易所侧清空
            start_wait = time.time()
            while True:
                remain = [o for o in (self.client.get_order_list() or []) if o.get('instId') == self.instrument and self._is_order_open(o)]
                if not remain:
                    break
                if time.time() - start_wait > 15:
                    self.log("⚠️ 撤单等待超时，仍存在活跃委托，继续后续流程但将强制重建双单")
                    break
                time.sleep(0.3)

            # 等待交易所侧清空
            start_wait = time.time()
            while True:
                remain = [o for o in (self.client.get_order_list() or []) if o.get('instId') == self.instrument and self._is_order_open(o)]
                if not remain:
                    break
                if time.time() - start_wait > 15:
                    self.log("⚠️ 撤单等待超时，仍存在活跃委托，继续后续流程但将强制重建双单")
                    break
                time.sleep(0.3)

            # 3) 计算中心价
            center_price = self.last_fill_price
            if not center_price or center_price <= 0:
                try:
                    center_price = self.get_current_price() or 0
                except Exception:
                    center_price = 0
            if not center_price or center_price <= 0:
                center_price = self.base_price
            if not center_price or center_price <= 0:
                self.log("⚠️ 无法确定中心价，跳过重建")
                return False

            buy_target = center_price - self.grid_width
            sell_target = center_price + self.grid_width
            if self.tick_size:
                buy_target = round(round(buy_target / self.tick_size) * self.tick_size, 8)
                sell_target = round(round(sell_target / self.tick_size) * self.tick_size, 8)

            # 4) 顺序下单并确认（若交易所已有其中一边但本地缺失，也强制重建）
            self._log_step("PLACE", "buy", px=buy_target, size=self.trade_size, center=center_price, width=self.grid_width)
            with self._order_mutation_lock:
                self._place_order_confirmed('buy', buy_target, self.trade_size, 'grid_down_center')
                self._log_step("PLACE", "sell", px=sell_target, size=self.trade_size, center=center_price, width=self.grid_width)
                self._place_order_confirmed('sell', sell_target, self.trade_size, 'grid_up_center')

            self._log_step("STATE", "two-orders-ensured")
            self._save_strategy_status()
            return True
        except Exception as e:
            self.log(f"❌ ensure_two_orders_strict 失败: {e}")
            return False
        finally:
            self._rebuilding_orders = False

    def _base_build_protected(self) -> bool:
        return time.time() < self._base_build_protect_until
    
    def get_current_price(self):
        """获取当前价格 - 使用严格的数据验证"""
        try:
            # 使用严格的数据验证获取价格
            success, price_data, error_message = self._get_verified_price()
            
            if success:
                price = price_data.get('price', 0)
                if price > 0:
                    # 每30秒输出一次价格信息
                    if int(time.time()) % 30 == 0:
                        self.log(f"💰 当前价格: ${price:.2f}")
                    return price
                else:
                    self.log(f"⚠️ 验证后的价格无效: {price}")
                return 0
            else:
                self.log(f"❌ 价格验证失败: {error_message}")
                return 0
                
        except Exception as e:
            self.log(f"获取当前价格失败: {e}")
            return 0
    
    def find_current_grid_index(self, current_price):
        """找到当前价格所在的网格索引"""
        # 🔥 修复：找到距离当前价格最近的网格索引
        
        if not self.grid_prices:
            return 0
        
        # 找到距离当前价格最近的网格
        min_distance = float('inf')
        closest_index = 0
        for i, grid_price in enumerate(self.grid_prices):
            distance = abs(current_price - grid_price)
            if distance < min_distance:
                min_distance = distance
                closest_index = i
        
        # 如果当前价格正好在两个网格之间，需要特殊处理
        # 确保我们返回的是当前价格"所处的区间"的正确索引
        if closest_index < len(self.grid_prices) - 1:
            current_grid_price = self.grid_prices[closest_index]
            next_grid_price = self.grid_prices[closest_index + 1]
            
            # 如果当前价格在两个网格之间，选择合适的索引
            if current_price > current_grid_price:
                # 价格高于当前网格，应该在当前网格和上一个网格之间
                # 但我们需要确保订单生成逻辑正确
                pass  # 使用closest_index
            elif current_price < next_grid_price:
                # 价格低于下一个网格，在当前区间内
                pass  # 使用closest_index
        
        self.log(f"🔍 价格定位: 当前价格${current_price:.2f}, 最近网格索引{closest_index}, 网格价格${self.grid_prices[closest_index]:.2f}")
        return closest_index
    
    def should_place_buy_order(self, current_price):
        """判断是否应该挂买单"""
        current_grid = self.find_current_grid_index(current_price)
        
        # 检查当前价格附近的网格，如果价格接近且没有该网格的买单
        for i in range(current_grid, len(self.grid_prices)):
            grid_price = self.grid_prices[i]
            grid_id = f"grid_down_{i+1}"
            
            # 重要：买单必须挂在低于当前价格的位置，避免立即成交
            price_diff = current_price - grid_price
            
            # 确保网格价格低于当前价格，且有足够价差（至少网格宽度的10%）
            min_diff = self.grid_width * 0.10
            
            # 额外检查：确保不会在基准价格附近立即买入
            # 如果当前价格接近基准价格，需要更大的价差
            if abs(current_price - self.base_price) < self.grid_width:
                min_diff = self.grid_width * 0.20  # 在基准价格附近需要更大的价差
            
            if (price_diff > min_diff and 
                grid_id not in self.grids):
                self.log(f"🔍 检测到需要挂买单: 当前价格${current_price:.2f}, 网格价格${grid_price:.2f}, 价差${price_diff:.2f}")
                return True, grid_id, grid_price
        
        return False, None, None
    
    def should_place_sell_order(self, current_price):
        """判断是否应该挂卖单"""
        if self.current_position <= 0:
            return False, None, None
        
        current_grid = self.find_current_grid_index(current_price)
        
        # 查找可以卖出的网格
        for i in range(current_grid):
            grid_price = self.grid_prices[i]
            grid_id = f"grid_up_{i+1}"
            
            # 重要：卖单必须挂在高于当前价格的位置，避免立即成交
            price_diff = grid_price - current_price
            
            # 确保网格价格高于当前价格，且有足够价差（至少网格宽度的10%）
            min_diff = self.grid_width * 0.10
            
            # 额外检查：确保不会在基准价格附近立即卖出
            # 如果当前价格接近基准价格，需要更大的价差
            if abs(current_price - self.base_price) < self.grid_width:
                min_diff = self.grid_width * 0.20  # 在基准价格附近需要更大的价差
            
            if (price_diff > min_diff and 
                grid_id not in self.grids):
                self.log(f"🔍 检测到需要挂卖单: 当前价格${current_price:.2f}, 网格价格${grid_price:.2f}, 价差${price_diff:.2f}")
                return True, grid_id, grid_price
        
        return False, None, None
    
    def place_grid_order(self, grid_id, side, price):
        """挂网格订单"""
        try:
            # 对于做多网格策略，所有订单都使用long持仓方向
            # buy + long = 开多单，sell + long = 平多单
            pos_side = "long"
            
            self.log(f"🔄 尝试挂单: {grid_id} {side} {self.trade_size}张 @ ${price:.8f}")
            
            result = self.client.place_order(
                inst_id=self.instrument,
                td_mode="isolated",
                side=side,
                pos_side=pos_side,
                ord_type="limit",
                sz=str(self.trade_size),
                px=str(price)
            )
            
            # 详细检查挂单结果
            self.log(f"📋 挂单响应: {result}")
            
            # 修复判断逻辑：检查sCode是否为'0'
            if result.get('code') == '0' or (result.get('data') and result['data'][0].get('sCode') == '0'):
                order_id = result['data'][0]['ordId']
                
                # 验证订单是否真的创建成功
                if order_id:
                    # 验证订单是否按预期价格挂单
                    if self.verify_order_placement(order_id, price):
                        grid_order = GridOrder(
                            grid_id=grid_id,
                            price=price,
                            side=side,
                            size=self.trade_size,
                            status='pending',
                            order_id=order_id,
                            create_time=datetime.now().strftime("%H:%M:%S")
                        )
                        self.grids[grid_id] = grid_order
                        
                        self.log(f"✅ 网格订单创建成功: {grid_id} {side} {self.trade_size}张 @ ${price:.8f}")
                        self.log(f"📝 订单ID: {order_id}")
                        return True
                    else:
                        self.log(f"❌ 订单验证失败，不添加到网格: {grid_id}")
                        return False
                else:
                    self.log(f"❌ 订单ID为空，挂单失败: {grid_id}")
                    return False
            else:
                self.log(f"❌ 网格订单创建失败: {grid_id} - {result}")
                return False
                
        except Exception as e:
            self.log(f"❌ 挂单异常: {e}")
            return False
    
    def verify_order_placement(self, order_id, expected_price):
        """验证订单是否真的按预期价格挂单成功"""
        try:
            result = self.client.get_order_details(
                inst_id=self.instrument,
                ord_id=order_id
            )
            
            if result.get('code') == '0' and result['data']:
                order_info = result['data'][0]
                actual_price = float(order_info.get('px', '0'))
                order_state = order_info.get('state', '')
                
                self.log(f"🔍 验证订单: ID={order_id}, 预期价格=${expected_price:.8f}, 实际价格=${actual_price:.8f}, 状态={order_state}")
                
                # 检查价格是否匹配
                if abs(actual_price - expected_price) < 0.01:  # 允许0.01的误差
                    self.log(f"✅ 订单价格验证成功")
                    return True
                else:
                    self.log(f"❌ 订单价格不匹配: 预期${expected_price:.8f}, 实际${actual_price:.8f}")
                    return False
            else:
                self.log(f"❌ 无法获取订单详情: {result}")
                return False
                
        except Exception as e:
            self.log(f"❌ 验证订单时发生错误: {e}")
            return False
    
    def check_order_status(self):
        """检查订单状态"""
        try:
            # 首先检查是否需要立即买入建立底仓
            self._check_and_build_position_if_needed()
            
            for grid_id, grid_order in list(self.grids.items()):
                if grid_order.order_id:
                    try:
                        # 使用get_order方法而不是get_order_details
                        order_info = self.client.get_order(
                            inst_id=self.instrument,
                            ord_id=grid_order.order_id
                        )
                        
                        if order_info:
                            state = order_info.get('state', '')
                            fill_sz = float(order_info.get('accFillSz', '0'))
                            
                            if state == 'filled' and fill_sz > 0:
                                self.log(f"订单成交: {grid_id} - {grid_order.side} {fill_sz}张 @ ${grid_order.price:.8f}")
                                self.handle_order_filled(grid_order)
                            elif state == 'canceled':
                                self.log(f"订单取消: {grid_id}")
                                del self.grids[grid_id]
                        else:
                            # 如果获取订单信息失败，记录但不中断程序
                            self.log(f"⚠️ 无法获取订单信息: {grid_order.order_id}")
                            
                    except Exception as e:
                        # 单个订单检查失败，记录但不中断整个循环
                        self.log(f"⚠️ 检查订单 {grid_order.order_id} 状态失败: {e}")
                        continue
                            
        except Exception as e:
            self.log(f"检查订单状态失败: {e}")
            # 即使检查失败，也继续执行，不要卡住程序
    
    def _check_and_build_position_if_needed(self):
        """检查并建立底仓 - 使用严格的数据验证"""
        try:
            # 防重复检查
            if self._building_position:
                self.log("🔄 正在建立底仓中，跳过重复检查")
                return
            
            self.log("🔍 开始严格验证持仓数据...")
            
            # 使用严格的数据验证获取持仓信息
            success, position_data, error_message = self._get_verified_positions()
            
            if not success:
                self.log(f"❌ 持仓数据验证失败: {error_message}")
                self.log("⚠️ 跳过底仓检查，等待下次验证")
                return
            
            # 提取验证后的持仓数量
            current_position = position_data.get('position_size', 0)
            
            # 更新内部持仓状态
            self.current_position = current_position
            
            self.log(f"✅ 持仓数据验证成功: {current_position}张")
            
            # 如果没有持仓，检查是否需要建立底仓（两次确认+冷却期）
            if current_position == 0:
                self.log("🚨 检测到无持仓，开始验证订单状态...")
                self._consecutive_zero_positions = getattr(self, '_consecutive_zero_positions', 0) + 1
                
                # 验证订单数据
                orders_success, orders_data, orders_error = self._get_verified_orders()
                
                if not orders_success:
                    self.log(f"❌ 订单数据验证失败: {orders_error}")
                    self.log("⚠️ 跳过底仓建立，等待下次验证")
                    return
                
                buy_orders_count = orders_data.get('buy_orders', 0)
                sell_orders_count = orders_data.get('sell_orders', 0)
                
                self.log(f"✅ 订单数据验证成功: 买单{buy_orders_count}个, 卖单{sell_orders_count}个")
                
                # 需要连续两次无持仓才触发
                if self._consecutive_zero_positions < 2:
                    self.log("⏳ 无持仓首次出现，等待下一次确认")
                    return
                
                # 冷却期限制，避免短时间内重复建底仓
                now_ts = time.time()
                last_ts = getattr(self, 'last_base_build_ts', 0.0)
                cooldown = getattr(self, 'base_build_cooldown_seconds', 30.0)
                if now_ts - last_ts < cooldown:
                    self.log("⏳ 建底仓冷却中，跳过")
                    return
                
                # 开始统一建底仓流程
                self.log("🚨 无持仓：执行统一建底仓流程（全撤→市价买→双挂）")
                self._building_position = True
                try:
                    self.cancel_all_orders()
                    success = self._execute_market_buy_for_base_position()
                    if success:
                        self.ensure_two_orders_by_last_fill()
                        self.last_base_build_ts = now_ts
                finally:
                    self._building_position = False
            else:
                self._consecutive_zero_positions = 0
                        
        except Exception as e:
            # 确保异常时也清除防重复标志
            self._building_position = False
            self.log(f"❌ 检查建立底仓失败: {e}")
            # 即使检查失败，也继续执行，不要卡住程序
    
    def _cancel_existing_buy_orders(self):
        """取消现有的买入委托"""
        try:
            self.log("🗑️ 开始取消现有买入委托...")
            
            # 获取当前订单列表
            success, orders_data, error_message = self._get_verified_orders()
            
            if not success:
                self.log(f"❌ 获取订单数据失败: {error_message}")
                return
            
            # 获取所有订单详情
            current_orders = self.client.get_order_list()
            if not current_orders:
                self.log("ℹ️ 没有找到需要取消的订单")
                return
            
            cancelled_count = 0
            for order in current_orders:
                if (order.get('instId') == self.instrument and 
                    order.get('side') == 'buy' and
                    order.get('state') in ['live', 'pending']):
                    
                    order_id = order.get('ordId')
                    try:
                        self.client.cancel_order(
                            inst_id=self.instrument,
                            ord_id=order_id
                        )
                        self.log(f"✅ 取消买入委托: {order_id}")
                        cancelled_count += 1
                    except Exception as e:
                        self.log(f"❌ 取消买入委托失败: {order_id} - {e}")
            
            # 从网格记录中移除买入订单
            buy_orders_to_remove = []
            for grid_id, grid_order in self.grids.items():
                if grid_order.side == 'buy':
                    buy_orders_to_remove.append(grid_id)
            
            for grid_id in buy_orders_to_remove:
                del self.grids[grid_id]
                self.log(f"🗑️ 从网格记录中移除: {grid_id}")
            
            self.log(f"✅ 取消买入委托完成，共取消{cancelled_count}个订单")
            
        except Exception as e:
            self.log(f"❌ 取消现有买入委托失败: {e}")
    
    def _execute_market_buy_for_base_position(self):
        """执行市价买入建立底仓 - 使用严格的数据验证"""
        try:
            # 内部互斥，确保建底仓流程串行
            if not getattr(self, '_building_position', False):
                self._building_position = True
                release_lock_after = True
            else:
                release_lock_after = False
            self.log("🔍 开始验证当前价格...")
            
            # 使用严格的数据验证获取价格
            success, price_data, error_message = self._get_verified_price()
            
            if not success:
                self.log(f"❌ 价格数据验证失败: {error_message}")
                return False
            
            current_price = price_data.get('price', 0)
            
            if current_price <= 0:
                self.log("❌ 验证后的价格无效")
                return False
            
            self.log(f"✅ 价格验证成功: ${current_price:.8f}")
            self.log(f"🔄 以市价买入建立底仓: {self.trade_size}张 @ ${current_price:.8f}")
                
            # 执行市价买入
            order_result = self.client.place_order(
                    inst_id=self.instrument,
                    td_mode="cross",
                    side="buy",
                    pos_side="long",
                    ord_type="market",
                    sz=str(self.trade_size),
                    px=None
                )
                
            if not order_result or not order_result.get('ordId'):
                self.log(f"❌ 市价买入失败: {order_result}")
                return False
            
            order_id = order_result['ordId']
            self.log(f"✅ 市价买入成功，订单ID: {order_id}")
                    
            # 记录建立底仓操作
            self.log_operation(
                operation_type="建立底仓",
                details=f"市价买入建立底仓 {self.trade_size}张 @${current_price:.2f}",
                price=current_price,
                size=self.trade_size,
                order_id=order_id
            )
            
            # 等待订单成交
            self.log("⏳ 等待订单成交...")
            time.sleep(3)  # 等待3秒确保订单处理完成
            
            # 验证订单成交状态（确保已成交）
            self.log("🔍 验证订单成交状态...")
            order_verified = False
            
            for verification_attempt in range(3):  # 放宽到3次
                try:
                    order_info = self.client.get_order(
                        inst_id=self.instrument,
                        ord_id=order_id
                    )
                    
                    if order_info and order_info.get('state') == 'filled':
                        fill_sz = float(order_info.get('accFillSz', '0'))
                        if fill_sz >= self.trade_size * 0.99:  # 允许1%的误差
                            self.log(f"✅ 订单成交验证成功: {fill_sz}张")
                            order_verified = True
                            break
                        else:
                            self.log(f"⚠️ 订单部分成交: {fill_sz}张，期望: {self.trade_size}张")
                    else:
                        self.log(f"⚠️ 订单状态: {order_info.get('state') if order_info else 'unknown'}")
                    
                    if verification_attempt < 2:  # 不是最后一次尝试
                        time.sleep(2)
                        
                except Exception as e:
                    self.log(f"⚠️ 验证订单状态失败: {e}")
                    if verification_attempt < 1:
                        time.sleep(2)
            
            if order_verified:
                self.log(f"✅ 底仓建立成功: {self.trade_size}张")
                
                # 再次验证持仓数据
                self.log("🔍 验证持仓更新...")
                time.sleep(2)  # 等待持仓更新
                
                position_success, position_data, position_error = self._get_verified_positions()
                
                # 读取精确成交价（优先 avgPx / fillPx，其次 fallback 为下单前验证价）
                filled_price = current_price
                try:
                    final_order_info = self.client.get_order(inst_id=self.instrument, ord_id=order_id)
                    if final_order_info:
                        filled_price = float(final_order_info.get('avgPx') or final_order_info.get('fillPx') or filled_price)
                except Exception as e:
                    self.log(f"⚠️ 读取成交价失败，使用验证价: {e}")

                # 记录最近一次成交为中心价
                self.last_fill_price = filled_price
                self.last_fill_side = 'buy'
                self.log(f"🎯 设定中心成交价: ${filled_price:.2f}（买入） → 将挂 买@${filled_price - self.grid_width:.2f} / 卖@${filled_price + self.grid_width:.2f}")

                if position_success:
                    new_position = position_data.get('position_size', 0)
                    self.log(f"✅ 持仓验证成功: {new_position}张")
                    
                    # 更新内部持仓状态
                    self.current_position = new_position
                    
                    # 记录交易
                    self._record_buy_trade(order_id, filled_price, self.trade_size)
                    
                    # 🔥 关键修复：底仓建立成功后，立即生成和同步网格订单
                    self.log("🚀 底仓建立完成，开始生成网格订单...")
                    
                    # 重新生成预期委托（只在新成交时）
                    self._generate_expected_orders()
                    self.center_price_committed = self.last_fill_price
                    
                    # 同步委托到交易所
                    self._sync_orders_with_exchange(ask_confirmation=False)
                    
                    # 显示当前状态
                    self._display_current_status()
                    
                    self.log("✅ 网格订单生成完成，策略正常运行")
                    
                    return True
                else:
                    self.log(f"⚠️ 持仓验证失败: {position_error}")
                    # 即使持仓验证失败，如果订单已成交，也认为成功
                    self.current_position = self.trade_size
                    self._record_buy_trade(order_id, filled_price, self.trade_size)
                    
                    # 🔥 关键修复：即使持仓验证失败，也要生成网格订单
                    self.log("🚀 底仓建立完成（持仓验证失败），开始生成网格订单...")
                    
                    # 重新生成预期委托（只在新成交时）
                    self._generate_expected_orders()
                    self.center_price_committed = self.last_fill_price
                    
                    # 同步委托到交易所
                    self._sync_orders_with_exchange(ask_confirmation=False)
                    
                    # 显示当前状态
                    self._display_current_status()
                    
                    self.log("✅ 网格订单生成完成，策略正常运行")
                    
                    return True
            else:
                self.log(f"❌ 订单成交验证失败")
                return False
                
        except Exception as e:
            self.log(f"❌ 执行市价买入异常: {e}")
            return False
        finally:
            if 'release_lock_after' in locals() and release_lock_after:
                self._building_position = False
    
    def _reset_and_restart_with_new_base_price(self, new_base_price):
        """以新的基准价格重置并重启策略"""
        try:
            self.log(f"🔄 以新基准价格 ${new_base_price:.8f} 重置策略")
            
            # 保存当前网格宽度
            current_grid_width = self.grid_width
            
            # 停止当前策略
            self.stop()
            
            # 清空所有状态
            self.grids.clear()
            self.trade_records.clear()
            self.total_profit = 0.0
            
            # 更新基准价格
            self.base_price = new_base_price
            
            # 重新初始化网格价格
            self._initialize_grid_prices()
            
            # 从交易所获取实时的long方向持仓
            current_position = 0
            positions = self.client.get_positions()
            if positions:
                for position in positions:
                    if (position.get('instId') == self.instrument and 
                        position.get('posSide') == 'long'):  # 只统计long方向
                        current_position = float(position.get('pos', '0'))
                        break
            
            self.current_position = current_position
            self.log(f"重置后持仓数量: {self.current_position}张")
            
            # 重新启动策略
            self.start()
            
            # 启动策略运行线程
            self.strategy_thread = threading.Thread(target=self.run)
            self.strategy_thread.daemon = True
            self.strategy_thread.start()
            
            self.log(f"✅ 策略已重置并重启，新基准价格: ${new_base_price:.8f}")
            
        except Exception as e:
            self.log(f"❌ 重置策略失败: {e}")
    
    def handle_order_filled(self, grid_order):
        """处理订单成交"""
        grid_order.status = 'filled'
        
        if grid_order.side == 'buy':
            self.handle_buy_filled(grid_order)
        else:
            self.handle_sell_filled(grid_order)
        
        # 从活跃网格中移除
        if grid_order.grid_id in self.grids:
            del self.grids[grid_order.grid_id]
    
    def handle_buy_filled(self, grid_order):
        """处理买单成交"""
        # 先更新本地，再以交易所权威持仓覆盖，避免累加误差
        self.current_position += grid_order.size
        self.last_fill_price = grid_order.price
        self.last_fill_side = 'buy'

        # 以严格验证的持仓为准刷新 self.current_position
        try:
            pos_success, pos_data, _ = self._get_verified_positions()
            if pos_success:
                self.current_position = float(pos_data.get('position_size', self.current_position) or self.current_position)
        except Exception:
            pass

        self.log(f"✅ 买单成交: {grid_order.size}张 @ ${grid_order.price:.8f}")
        self.log(f"当前持仓: {self.current_position}张")
        
        # 记录买单成交操作
        self.log_operation(
            operation_type="买单成交",
            details=f"买单成交 {grid_order.size}张 @${grid_order.price:.2f} [持仓:{self.current_position:.2f}张]",
            price=grid_order.price,
            size=grid_order.size,
            order_id=grid_order.order_id,
            grid_id=grid_order.grid_id
        )
        
        # 记录交易
        trade_record = TradeRecord(
            trade_id=f"trade_{int(time.time())}",
            order_id=grid_order.order_id,
            side='buy',
            price=grid_order.price,
            size=grid_order.size,
            fee=0.0,  # 实际手续费需要从成交记录获取
            timestamp=datetime.now().strftime("%H:%M:%S")
        )
        self.trade_records.append(trade_record)
        
        # 保存交易记录到数据库
        if self.db_manager:
            try:
                trade_data = {
                    'trade_id': trade_record.trade_id,
                    'order_id': trade_record.order_id,
                    'side': trade_record.side,
                    'price': trade_record.price,
                    'size': trade_record.size,
                    'fee': trade_record.fee,
                    'timestamp': trade_record.timestamp
                }
                self.db_manager.add_trade_record(self.strategy_id, trade_data)
                self.log(f"📝 保存买入交易记录: {trade_record.size}张 @ ${trade_record.price:.8f}")
            except Exception as e:
                self.log(f"❌ 保存交易记录失败: {e}")
        
        # 新增：记录持仓明细
        if self.db_manager:
            try:
                position_data = {
                    'order_id': grid_order.order_id,
                    'price': grid_order.price,
                    'size': grid_order.size,
                    'timestamp': datetime.now().isoformat()
                }
                self.db_manager.add_position_detail(self.strategy_id, position_data)
                self.log(f"📝 记录持仓明细: {grid_order.size}张 @ ${grid_order.price:.8f}")
            except Exception as e:
                self.log(f"❌ 记录持仓明细失败: {e}")
        
        # 触发严格二单约束（节流：至少间隔 self.two_order_enforce_interval 秒）
        try:
            now_ts = time.time()
            if now_ts - self.last_two_order_enforce_ts >= self.two_order_enforce_interval:
                self.ensure_two_orders_by_last_fill()
        except Exception as e:
            self.log(f"⚠️ 买单成交后二单约束失败: {e}")
    
    def _regenerate_orders_after_buy_filled(self, filled_grid_order):
        """买单成交后重新生成委托"""
        try:
            # 找到成交价格对应的网格索引
            filled_price = filled_grid_order.price
            filled_grid_index = -1
            
            for i, price in enumerate(self.grid_prices):
                if abs(price - filled_price) < 0.0001:
                    filled_grid_index = i
                    break
            
            if filled_grid_index == -1:
                self.log(f"❌ 无法找到成交价格对应的网格: ${filled_price:.8f}")
                return
            
            self.log(f"🔄 买单成交后重新生成委托，成交网格索引: {filled_grid_index}")
            
            # 1. 撤销所有现有的卖单（记录撤单日志）
            self.log("🗑️ 撤销所有现有的卖单")
            sell_orders_to_cancel = []
            for grid_id, grid_order in list(self.grids.items()):
                if grid_order.side == 'sell':
                    sell_orders_to_cancel.append(grid_order)
            
            for sell_order in sell_orders_to_cancel:
                if sell_order.order_id:
                    try:
                        self.client.cancel_order(
                            inst_id=self.instrument,
                            ord_id=sell_order.order_id
                        )
                        self.log(f"✅ 撤销卖单: {sell_order.order_id}")
                        try:
                            self.log_operation(
                                operation_type="撤销卖单",
                                details=f"撤销卖单 {sell_order.size}张 @${sell_order.price:.2f} [{sell_order.grid_id}]",
                                price=sell_order.price,
                                size=sell_order.size,
                                order_id=sell_order.order_id,
                                grid_id=sell_order.grid_id
                            )
                        except Exception:
                            pass
                    except Exception as e:
                        self.log(f"❌ 撤销卖单失败: {e}")
                
                # 从网格记录中移除
                if sell_order.grid_id in self.grids:
                    del self.grids[sell_order.grid_id]
            
            # 2. 挂下一个买单（向下一个网格）
            next_buy_grid_index = filled_grid_index + 1
            if next_buy_grid_index < len(self.grid_prices):
                next_buy_price = self.grid_prices[next_buy_grid_index]
                next_buy_grid_id = f"grid_down_{next_buy_grid_index + 1}"
                
                if next_buy_grid_id not in self.grids:
                    self.log(f"📈 挂下一个买单: 网格{next_buy_grid_index + 1}, 价格${next_buy_price:.8f}")
                    self._place_order('buy', next_buy_price, self.trade_size, next_buy_grid_id)
                else:
                    self.log(f"⚠️ 下一个买单已存在: {next_buy_grid_id}")
            
            # 3. 挂上一个卖单（向上一个网格）
            prev_sell_grid_index = filled_grid_index - 1
            if prev_sell_grid_index >= 0:
                prev_sell_price = self.grid_prices[prev_sell_grid_index]
                prev_sell_grid_id = f"grid_up_{prev_sell_grid_index + 1}"
                
                if prev_sell_grid_id not in self.grids:
                    self.log(f"📉 挂上一个卖单: 网格{prev_sell_grid_index + 1}, 价格${prev_sell_price:.8f}")
                    self._place_order('sell', prev_sell_price, self.trade_size, prev_sell_grid_id)
                else:
                    self.log(f"⚠️ 上一个卖单已存在: {prev_sell_grid_id}")
            
            self.log(f"✅ 委托重新生成完成，当前活跃委托: {len(self.grids)}个")
            
        except Exception as e:
            self.log(f"❌ 重新生成委托失败: {e}")
    
    def handle_sell_filled(self, grid_order):
        """处理卖单成交"""
        # 先更新本地，再以交易所权威持仓覆盖
        self.current_position -= grid_order.size
        self.last_fill_price = grid_order.price
        self.last_fill_side = 'sell'

        try:
            pos_success, pos_data, _ = self._get_verified_positions()
            if pos_success:
                self.current_position = float(pos_data.get('position_size', self.current_position) or self.current_position)
        except Exception:
            pass

        # 如果卖出后空仓，则立即重建底仓
        if self.current_position <= 0:
            self.log("🪙 卖出后空仓，执行统一建底仓流程（全撤→市价买→双挂）")
            # 严格串行化：全撤→买入→双挂
            self.cancel_all_orders()
            if self._execute_market_buy_for_base_position():
                self.ensure_two_orders_by_last_fill()
        
        # 重新计算盈利：网格交易的盈利应该是买卖价差
        # 从数据库中获取对应的买入记录来计算盈利
        profit = 0.0
        if self.db_manager:
            try:
                # 从数据库获取买入记录
                trade_records = self.db_manager.get_trade_history(self.strategy_id)
                buy_trades = [t for t in trade_records if t.get('side') == 'buy' and t.get('size') == grid_order.size]
                
                if buy_trades:
                    # 使用最新的对应买入记录
                    buy_trade = buy_trades[-1]
                    buy_price = buy_trade.get('price', 0)
                    profit = (grid_order.price - buy_price) * grid_order.size
                    self.log(f"📊 盈利计算: 卖出${grid_order.price:.8f} - 买入${buy_price:.8f} = ${profit:.4f}")
                else:
                    self.log("⚠️ 未找到对应的买入记录，无法计算盈利")
            except Exception as e:
                self.log(f"❌ 获取交易记录失败: {e}")
        else:
            # 如果没有数据库管理器，使用内存中的记录
            buy_trades = [t for t in self.trade_records if t.side == 'buy' and t.size == grid_order.size]
            if buy_trades:
                buy_trade = buy_trades[-1]
                profit = (grid_order.price - buy_trade.price) * grid_order.size
                self.log(f"📊 盈利计算: 卖出${grid_order.price:.8f} - 买入${buy_trade.price:.8f} = ${profit:.4f}")
            else:
                self.log("⚠️ 未找到对应的买入记录，无法计算盈利")
        
        self.total_profit += profit
        
        self.log(f"✅ 卖单成交: {grid_order.size}张 @ ${grid_order.price:.8f}")
        self.log(f"本次盈利: {profit:.4f} USDT")
        self.log(f"当前持仓: {self.current_position}张")
        self.log(f"总盈利: {self.total_profit:.4f} USDT")
        
        # 记录卖单成交操作
        self.log_operation(
            operation_type="卖单成交",
            details=f"卖单成交 {grid_order.size}张 @${grid_order.price:.2f} [盈利:{profit:.2f}U 持仓:{self.current_position}张]",
            price=grid_order.price,
            size=grid_order.size,
            order_id=grid_order.order_id,
            grid_id=grid_order.grid_id
        )
        
        # 记录交易
        trade_record = TradeRecord(
            trade_id=f"trade_{int(time.time())}",
            order_id=grid_order.order_id,
            side='sell',
            price=grid_order.price,
            size=grid_order.size,
            fee=0.0,
            timestamp=datetime.now().strftime("%H:%M:%S")
        )
        self.trade_records.append(trade_record)
        
        # 保存交易记录到数据库
        if self.db_manager:
            try:
                trade_data = {
                    'trade_id': trade_record.trade_id,
                    'order_id': trade_record.order_id,
                    'side': trade_record.side,
                    'price': trade_record.price,
                    'size': trade_record.size,
                    'fee': trade_record.fee,
                    'timestamp': trade_record.timestamp
                }
                self.db_manager.add_trade_record(self.strategy_id, trade_data)
                self.log(f"📝 保存卖出交易记录: {trade_record.size}张 @ ${trade_record.price:.8f}")
            except Exception as e:
                self.log(f"❌ 保存交易记录失败: {e}")
        
        # 新增：记录交易配对
        if self.db_manager:
            try:
                # 查找对应的买单记录
                buy_trades = [t for t in self.trade_records if t.side == 'buy' and t.size == grid_order.size]
                if buy_trades:
                    # 使用最新的买单作为配对
                    buy_trade = buy_trades[-1]
                    
                    pair_data = {
                        'pair_id': f"pair_{int(time.time())}",
                        'buy_order_id': buy_trade.order_id,
                        'sell_order_id': grid_order.order_id,
                        'buy_price': buy_trade.price,
                        'sell_price': grid_order.price,
                        'size': grid_order.size,
                        'buy_time': buy_trade.timestamp,
                        'sell_time': datetime.now().strftime("%H:%M:%S"),
                        'profit': profit,
                        'status': 'closed'
                    }
                    
                    self.db_manager.add_trade_pair(self.strategy_id, pair_data)
                    self.log(f"📝 记录交易配对: 买入${buy_trade.price:.8f} -> 卖出${grid_order.price:.8f}, 盈利${profit:.4f}")
                else:
                    self.log("⚠️ 未找到对应的买单记录")
                    
            except Exception as e:
                self.log(f"❌ 记录交易配对失败: {e}")
        
        # 触发严格二单约束（节流）
        try:
            now_ts = time.time()
            if now_ts - self.last_two_order_enforce_ts >= self.two_order_enforce_interval:
                self.ensure_two_orders_by_last_fill()
        except Exception as e:
            self.log(f"⚠️ 卖单成交后二单约束失败: {e}")
    
    def _regenerate_orders_after_sell_filled(self, filled_grid_order):
        """卖单成交后重新生成委托"""
        try:
            # 找到成交价格对应的网格索引
            filled_price = filled_grid_order.price
            filled_grid_index = -1
            
            for i, price in enumerate(self.grid_prices):
                if abs(price - filled_price) < 0.0001:
                    filled_grid_index = i
                    break
            
            if filled_grid_index == -1:
                self.log(f"❌ 无法找到成交价格对应的网格: ${filled_price:.8f}")
                return
            
            self.log(f"🔄 卖单成交后重新生成委托，成交网格索引: {filled_grid_index}")
            
            # 1. 撤销所有现有的买单（记录撤单日志）
            self.log("🗑️ 撤销所有现有的买单")
            buy_orders_to_cancel = []
            for grid_id, grid_order in list(self.grids.items()):
                if grid_order.side == 'buy':
                    buy_orders_to_cancel.append(grid_order)
            
            for buy_order in buy_orders_to_cancel:
                if buy_order.order_id:
                    try:
                        self.client.cancel_order(
                            inst_id=self.instrument,
                            ord_id=buy_order.order_id
                        )
                        self.log(f"✅ 撤销买单: {buy_order.order_id}")
                        try:
                            self.log_operation(
                                operation_type="撤销买单",
                                details=f"撤销买单 {buy_order.size}张 @${buy_order.price:.2f} [{buy_order.grid_id}]",
                                price=buy_order.price,
                                size=buy_order.size,
                                order_id=buy_order.order_id,
                                grid_id=buy_order.grid_id
                            )
                        except Exception:
                            pass
                    except Exception as e:
                        self.log(f"❌ 撤销买单失败: {e}")
                
                # 从网格记录中移除
                if buy_order.grid_id in self.grids:
                    del self.grids[buy_order.grid_id]
            
            # 2. 挂下一个卖单（向上一个网格）
            next_sell_grid_index = filled_grid_index - 1
            if next_sell_grid_index >= 0:
                next_sell_price = self.grid_prices[next_sell_grid_index]
                next_sell_grid_id = f"grid_up_{next_sell_grid_index + 1}"
                
                if next_sell_grid_id not in self.grids:
                    self.log(f"📉 挂下一个卖单: 网格{next_sell_grid_index + 1}, 价格${next_sell_price:.8f}")
                    self._place_order('sell', next_sell_price, self.trade_size, next_sell_grid_id)
                else:
                    self.log(f"⚠️ 下一个卖单已存在: {next_sell_grid_id}")
            
            # 3. 挂上一个买单（向下一个网格）
            prev_buy_grid_index = filled_grid_index + 1
            if prev_buy_grid_index < len(self.grid_prices):
                prev_buy_price = self.grid_prices[prev_buy_grid_index]
                prev_buy_grid_id = f"grid_down_{prev_buy_grid_index + 1}"
                
                if prev_buy_grid_id not in self.grids:
                    self.log(f"📈 挂上一个买单: 网格{prev_buy_grid_index + 1}, 价格${prev_buy_price:.8f}")
                    self._place_order('buy', prev_buy_price, self.trade_size, prev_buy_grid_id)
                else:
                    self.log(f"⚠️ 上一个买单已存在: {prev_buy_grid_id}")
            
            self.log(f"✅ 委托重新生成完成，当前活跃委托: {len(self.grids)}个")
            
        except Exception as e:
            self.log(f"❌ 重新生成委托失败: {e}")
    
    def get_average_buy_price(self):
        """获取平均买入价格"""
        buy_trades = [t for t in self.trade_records if t.side == 'buy']
        if not buy_trades:
            return 0
        
        total_value = sum(t.price * t.size for t in buy_trades)
        total_size = sum(t.size for t in buy_trades)
        return total_value / total_size if total_size > 0 else 0
    
    def calculate_real_profit(self):
        """实时计算真实盈利"""
        try:
            # 从数据库中获取已完成的交易配对来计算盈利
            if self.db_manager:
                trade_pairs = self.db_manager.get_trade_pairs(self.strategy_id)
                total_profit = 0.0
                
                for pair in trade_pairs:
                    if pair.get('status') == 'closed':
                        profit = pair.get('profit', 0) or 0
                        total_profit += profit
                
                return total_profit
            else:
                # 如果没有数据库管理器，使用内存中的交易记录
                return self.total_profit
                
        except Exception as e:
            self.log(f"❌ 计算盈利失败: {e}")
            return 0.0
    
    def get_strategy_status(self):
        """获取策略状态信息 - 使用严格的数据验证"""
        try:
            # 使用严格的数据验证获取价格
            price_success, price_data, price_error = self._get_verified_price()
            current_price = price_data.get('price', 0) if price_success else 0
            
            # 使用严格的数据验证获取持仓
            position_success, position_data, position_error = self._get_verified_positions()
            current_position = position_data.get('position_size', 0) if position_success else 0
            
            # 找到当前价格所在的网格
            current_grid_index = self.find_current_grid_index(current_price)
            current_grid_price = self.grid_prices[current_grid_index] if current_grid_index >= 0 else 0
            
            # 确定网格方向
            if current_grid_index == 0:
                grid_direction = "上"
                grid_number = 1
            elif current_grid_index < len(self.grid_prices) // 2:
                grid_direction = "上"
                grid_number = len(self.grid_prices) // 2 - current_grid_index
            else:
                grid_direction = "下"
                grid_number = current_grid_index - len(self.grid_prices) // 2 + 1
            
            # 计算下一个卖出价格
            next_sell_price = None
            for i in range(current_grid_index - 1, -1, -1):
                grid_price = self.grid_prices[i]
                grid_id = f"grid_up_{len(self.grid_prices) - i}"
                if grid_id not in self.grids:
                    next_sell_price = grid_price
                    break
            
            # 计算下一个买入价格（无论是否有持仓）
            next_buy_price = None
            for i in range(current_grid_index + 1, len(self.grid_prices)):
                grid_price = self.grid_prices[i]
                grid_id = f"grid_down_{i+1}"
                if grid_id not in self.grids:
                    next_buy_price = grid_price
                    break
            
            return {
                'current_price': current_price,
                'base_price': self.base_price,
                'current_grid_index': current_grid_index,
                'current_grid_price': current_grid_price,
                'grid_direction': grid_direction,
                'grid_number': grid_number,
                'next_buy_price': next_buy_price,
                'next_sell_price': next_sell_price,
                'current_position': current_position,  # 使用验证后的持仓
                'total_profit': self.calculate_real_profit(),  # 实时计算盈利
                'active_orders': len(self.grids),
                'upper_limit_units': getattr(self, 'position_upper_units', 20),
                'data_verification_status': {
                    'price_verified': price_success,
                    'position_verified': position_success
                }
            }
        except Exception as e:
            self.log(f"获取策略状态失败: {e}")
            # 返回默认状态
            return {
                'current_price': 0,
                'base_price': self.base_price,
                'current_grid_index': -1,
                'current_grid_price': 0,
                'grid_direction': "未知",
                'grid_number': 0,
                'next_buy_price': None,
                'next_sell_price': None,
                'current_position': 0,
                'total_profit': 0,
                'active_orders': len(self.grids),
                'data_verification_status': {
                    'price_verified': False,
                    'position_verified': False
                }
            }
    
    def run(self):
        """运行策略主循环"""
        self.is_running = True
        self.log("🚀 动态网格策略启动")
        
        while self.is_running:
            try:
                # 检查是否应该暂停策略
                if self._should_pause_strategy():
                    current_time = time.time()
                    remaining_pause = max(0, self.pause_until - current_time)
                    if int(time.time()) % 5 == 0:  # 每5秒输出一次暂停状态
                        self.log(f"⏸️ 策略暂停中，剩余暂停时间: {remaining_pause:.1f}秒")
                    
                    # 在暂停期间检查网络状态
                    if int(time.time()) % 10 == 0:  # 每10秒检查一次网络
                        if self._check_network_health():
                            self.log("✅ 网络已恢复，提前结束暂停")
                            self.critical_data_failed = False
                            self.consecutive_failures = 0
                    
                    time.sleep(1)
                    continue
                
                # 每10秒输出一次循环状态
                if int(time.time()) % 10 == 0:
                    self.log(f"🔄 策略循环运行中... 时间: {datetime.now().strftime('%H:%M:%S')}")
                
                # 安全获取当前价格
                current_price = self._safe_get_current_price()
                
                # 每5秒输出一次状态信息
                if int(time.time()) % 5 == 0:
                    if current_price and current_price > 0:
                        self.log(f"📊 策略状态: 当前价格${current_price:.2f}, 活跃订单{len(self.grids)}个, 持仓{self.current_position}张")
                    else:
                        self.log(f"📊 策略状态: 价格获取失败, 活跃订单{len(self.grids)}个, 持仓{self.current_position}张")
                
                # 严格串行总控：先保证双挂再做其他
                try:
                    if self.current_position > 0:
                        self.ensure_two_orders_strict()
                        # 严格双挂就绪后，再检查并执行上限控制
                        self._enforce_upper_limit_if_needed()
                except Exception as e:
                    self.log(f"⚠️ 严格双挂保障失败: {e}")

                # 再检查订单状态（成交、撤单等跟进）
                self.check_order_status()

                # 周期性严格二单约束（节流）：避免出现只剩一边或无单的状态
                try:
                    if self.current_position > 0 and self.last_fill_price:
                        now_ts = time.time()
                        if now_ts - self.last_two_order_enforce_ts >= self.two_order_enforce_interval:
                            self.ensure_two_orders_by_last_fill()
                except Exception as e:
                    self.log(f"⚠️ 周期性二单约束失败: {e}")
                
                # 检查是否需要建立底仓（每30秒检查一次，而不是10秒）
                if int(time.time()) % 30 == 0:
                    self._check_and_build_position_if_needed()
                
                # 只有在获取到有效价格时才处理四种情况
                if current_price and current_price > 0 and self.last_fill_price:
                    # 处理四种情况
                    self._handle_four_scenarios(current_price)
                else:
                    # 如果价格获取失败，输出调试信息
                    if int(time.time()) % 10 == 0:
                        self.log(f"⚠️ 价格获取失败，跳过策略处理")
                
                # 保存策略状态
                self._save_strategy_status()
                
                # 每30秒输出一次心跳信息，确认程序在运行
                if int(time.time()) % 30 == 0:
                    self.log(f"💓 策略运行中... 时间: {datetime.now().strftime('%H:%M:%S')}")
                
                # 每60秒输出一次数据验证摘要
                if int(time.time()) % 60 == 0:
                    self.log_verification_summary()
                
                # 每120秒输出一次价格验证详情
                if int(time.time()) % 120 == 0:
                    self.log_price_verification_details()
                
                # 每300秒（5分钟）输出一次操作摘要
                if int(time.time()) % 300 == 0:
                    self.print_operation_summary()
                
                time.sleep(1)  # 每1秒检查一次
                
            except Exception as e:
                self.log(f"策略运行异常: {e}")
                # 异常情况下也暂停一段时间
                self.pause_until = time.time() + 10
                self.critical_data_failed = True
                time.sleep(5)
        
        self.log("⏹️ 动态网格策略停止")
    
    def _handle_four_scenarios(self, current_price):
        """处理四种情况"""
        try:
            current_grid_index = self.find_current_grid_index(current_price)
            
            # 情况1：价格下跌，挂单成交 - 在下一格挂新单
            # 检查是否有买单成交，如果有则在下一格挂新买单
            self._handle_scenario_1(current_price, current_grid_index)
            
            # 情况2：价格上涨到基准线 - 平仓并重置网格
            self._handle_scenario_2(current_price)
            
            # 情况3：价格上涨到上方网格 - 平仓并重置网格
            if current_grid_index == 0:  # 到达最高网格
                self._handle_scenario_3(current_price)
            
            # 情况4：突破20格底线 - 继续挂单，保证持仓20个
            if current_grid_index >= len(self.grid_prices) - 1:  # 到达最低网格
                self._handle_scenario_4(current_price)
            
        except Exception as e:
            self.log(f"处理四种情况异常: {e}")
    
    def _handle_scenario_1(self, current_price, current_grid_index):
        """情况1：价格下跌，挂单成交 - 在下一格挂新单"""
        # 检查是否有买单成交
        for grid_id, grid_order in list(self.grids.items()):
            if (grid_order.side == 'buy' and 
                grid_order.status == 'filled' and
                grid_order.price < current_price):
                
                self.log(f"情况1: 买单成交，价格${grid_order.price:.8f}")
                
                # 在下一格挂新买单
                next_grid_index = current_grid_index + 1
                if next_grid_index < len(self.grid_prices):
                    next_price = self.grid_prices[next_grid_index]
                    next_grid_id = f"grid_down_{next_grid_index + 1}"
                    
                    # 检查是否已有该网格的订单
                    if next_grid_id not in self.grids:
                        self.log(f"在下一格挂新买单: 价格${next_price:.8f}")
                        self._place_order('buy', next_price, self.trade_size, next_grid_id)
                
                # 移除已成交的订单记录
                del self.grids[grid_id]
    
    def _handle_scenario_2(self, current_price):
        """情况2：停用重置逻辑（与严格二单约束冲突）只记录状态。"""
        try:
            self.log(f"情况2(已停用重置): 当前价 ${current_price:.8f}, 仅记录，不执行平仓/全撤/重置")
        except Exception as e:
            self.log(f"检查情况2时发生错误: {e}")
    
    def _handle_scenario_3(self, current_price):
        """情况3：停用重置逻辑（与严格二单约束冲突）只记录状态。"""
        self.log(f"情况3(已停用重置): 当前价 ${current_price:.8f}, 仅记录，不执行平仓/全撤/重置")
    
    def _handle_scenario_4(self, current_price):
        """情况4：突破20格底线 - 继续挂单，保证持仓20个"""
        self.log(f"情况4: 突破20格底线 ${current_price:.8f}")
        
        # 计算需要保持的持仓数量
        target_position = 20 * self.trade_size
        
        if self.current_position < target_position:
            # 需要增加持仓
            additional_position = target_position - self.current_position
            self.log(f"需要增加持仓: {additional_position}张")
            
            # 在更低的价格挂买单
            # 这里需要实现具体的挂单逻辑
        
        # 取消最高价的买单（止损）
        for grid_id, grid_order in list(self.grids.items()):
            if grid_order.side == 'buy' and grid_order.price == max(self.grid_prices):
                self.log(f"取消最高价买单: ${grid_order.price:.8f}")
                if grid_order.order_id:
                    self.client.cancel_order(inst_id=self.instrument, ord_id=grid_order.order_id)
                del self.grids[grid_id]
    
    def _reset_grid_strategy(self, new_base_price):
        """重置网格策略"""
        self.log(f"重置网格策略，新基准价格: ${new_base_price:.8f}")
        
        # 取消所有现有订单
        self.cancel_all_orders()
        
        # 更新基准价格
        self.base_price = new_base_price
        
        # 重新初始化网格价格
        self._initialize_grid_prices()
        
        # 重新生成预期委托
        self._generate_expected_orders()
        
        # 同步委托
        self._sync_orders_with_exchange(ask_confirmation=True)
    
    def start(self):
        """启动策略"""
        try:
            self.log("🚀 启动动态网格策略")

            # 查询合约步进
            try:
                instruments = self.client.get_instruments("SWAP")
                for ins in instruments or []:
                    if ins.get('instId') == self.instrument:
                        # OKX 返回字符串步进
                        self.tick_size = float(ins.get('tickSz', '0.01'))
                        self.lot_size = float(ins.get('lotSz', '0.001'))
                        break
                self.log(f"🧩 步进: tickSz={self.tick_size}, lotSz={self.lot_size}")
            except Exception as e:
                self.log(f"⚠️ 获取合约步进失败: {e}")
            
            # 检查是否有持仓，如果没有则自动建立底仓
            self._check_and_build_position_if_needed()
            
            # 同步交易所订单（仅观测不做清理；随后由严格二单约束统一处理）
            self._sync_orders_with_exchange(ask_confirmation=False)
            
            # 生成期望的订单（不立即下发，由严格二单约束统一确保一买一卖）
            self._generate_expected_orders()
            
            # 显示当前状态
            self._display_current_status()
            
            # 启动时强制应用严格二单约束
            try:
                if self.current_position > 0:
                    self.ensure_two_orders_by_last_fill()
            except Exception as e:
                self.log(f"⚠️ 启动二单约束失败: {e}")

            # 显示操作历史摘要
            self.print_operation_summary()
            
            self.log("✅ 动态网格策略启动完成")
            
        except Exception as e:
            self.log(f"❌ 启动策略失败: {e}")
            raise
    
    def _print_grid_prices(self):
        """打印网格价格表"""
        self.log("📊 网格价格表:")
        self.log("=" * 50)
        
        # 找到基准价格的位置
        base_price_index = -1
        for i, price in enumerate(self.grid_prices):
            if abs(price - self.base_price) < 0.0001:  # 浮点数比较
                base_price_index = i
                break
        
        for i, price in enumerate(self.grid_prices):
            if i == 0:
                self.log(f"上1格: ${price:.8f}")
            elif i == base_price_index:
                self.log(f"基准价格: ${price:.8f}")
            elif i < base_price_index:
                # 这是向上网格（卖出网格）
                up_grid_num = base_price_index - i
                self.log(f"上{up_grid_num + 1}格: ${price:.8f}")
            else:
                # 这是向下网格（买入网格）
                down_grid_num = i - base_price_index
                self.log(f"下{down_grid_num}格: ${price:.8f}")
        
        self.log("=" * 50)
    
    def _display_current_status(self):
        """显示当前状态"""
        try:
            # 安全获取当前持仓 - 只统计long方向的持仓
            positions = self._safe_get_positions()
            current_position = 0
            if positions:
                for position in positions:
                    if (position.get('instId') == self.instrument and 
                        position.get('posSide') == 'long'):  # 只统计long方向
                        current_position = float(position.get('pos', '0'))
                        break
            
            # 获取当前委托
            current_orders = self.client.get_order_list()
            
            self.log("📋 当前状态:")
            self.log(f"  持仓: {current_position}张")
            
            if current_orders:
                self.log(f"  活跃委托: {len(current_orders)}个")
                self.log("  委托详情:")
                for order in current_orders:
                    side = order.get('side', 'unknown')
                    price = order.get('px', '0')
                    size = order.get('sz', '0')
                    status = order.get('state', 'unknown')
                    self.log(f"    {side.upper()} {size}张 @ ${price} [{status}]")
            else:
                self.log("  活跃委托: 无法获取")
            
            self.log("=" * 50)
            
        except Exception as e:
            self.log(f"❌ 显示状态失败: {e}")
            # 即使显示状态失败，也继续执行，不要卡住程序
    
    def stop(self):
        """停止策略"""
        self.is_running = False
        self.cancel_all_orders()
    
    def cancel_all_orders(self):
        """取消所有订单"""
        try:
            # 第一步：取消策略内部记录的所有订单
            for grid_id, grid_order in list(self.grids.items()):
                if grid_order.order_id:
                    try:
                        self.client.cancel_order(
                            inst_id=self.instrument,
                            ord_id=grid_order.order_id
                        )
                        self.log(f"取消策略订单: {grid_id}")
                        
                        # 记录取消订单操作
                        side_name = "买" if grid_order.side == "buy" else "卖"
                        self.log_operation(
                            operation_type=f"撤销{side_name}单",
                            details=f"撤销{side_name}单 {grid_order.size}张 @${grid_order.price:.2f} [{grid_id}]",
                            price=grid_order.price,
                            size=grid_order.size,
                            order_id=grid_order.order_id,
                            grid_id=grid_id
                        )
                    except Exception as e:
                        self.log(f"取消策略订单失败: {e}")
            
            # 第二步：获取并取消交易所的所有未成交订单
            current_orders = self.client.get_order_list()
            if current_orders:
                for order in current_orders:
                    if order.get('instId') == self.instrument:
                        order_id = order.get('ordId')
                        order_state = order.get('state', '')
                        
                        # 只取消未成交的订单
                        if order_state in ['live', 'pending']:
                            try:
                                self.client.cancel_order(
                                    inst_id=self.instrument,
                                    ord_id=order_id
                                )
                                self.log(f"取消交易所订单: {order_id}")
                            except Exception as e:
                                self.log(f"取消交易所订单失败: {e}")
            
            # 第三步：清空策略内部的网格订单记录
            self.grids.clear()
            self.log("✅ 所有订单已取消，策略内部记录已清空")
            
        except Exception as e:
            self.log(f"❌ 取消所有订单失败: {e}")
    
    def get_statistics(self):
        """获取统计信息 - 从数据库获取真实数据"""
        try:
            if self.db_manager:
                # 从数据库获取交易记录
                trade_records = self.db_manager.get_trade_history(self.strategy_id)
                total_trades = len(trade_records)
                
                # 统计买卖交易次数
                buy_trades = len([t for t in trade_records if t.get('side') == 'buy'])
                sell_trades = len([t for t in trade_records if t.get('side') == 'sell'])
                
                # 从数据库获取交易配对统计
                trade_pairs = self.db_manager.get_trade_pairs(self.strategy_id)
                closed_pairs = len([p for p in trade_pairs if p.get('status') == 'closed'])
                
                # 计算总盈利
                total_profit = 0.0
                for pair in trade_pairs:
                    if pair.get('status') == 'closed':
                        profit = pair.get('profit', 0)
                        if profit is not None:
                            total_profit += profit
                
                # 计算最大回撤（简化版本）
                max_drawdown = 0.0
                if trade_pairs:
                    profits = []
                    for p in trade_pairs:
                        if p.get('status') == 'closed':
                            profit = p.get('profit', 0)
                            if profit is not None:
                                profits.append(profit)
                    
                    if profits:
                        cumulative_profits = []
                        cumulative = 0
                        for profit in profits:
                            cumulative += profit
                            cumulative_profits.append(cumulative)
                        
                        if cumulative_profits:
                            peak = max(cumulative_profits)
                            max_drawdown = min(cumulative_profits) - peak
                
                return {
                    'total_trades': total_trades,
                    'buy_trades': buy_trades,
                    'sell_trades': sell_trades,
                    'closed_pairs': closed_pairs,
                    'total_profit': total_profit,
                    'current_grids': len(self.grids),
                    'max_drawdown': max_drawdown,
                    'avg_profit_per_trade': total_profit / closed_pairs if closed_pairs > 0 else 0
                }
            else:
                # 如果没有数据库管理器，使用内存数据
                return {
                    'total_trades': len(self.trade_records),
                    'buy_trades': len([t for t in self.trade_records if t.side == 'buy']),
                    'sell_trades': len([t for t in self.trade_records if t.side == 'sell']),
                    'closed_pairs': len([t for t in self.trade_records if t.side == 'sell']),
                    'total_profit': self.total_profit,
                    'current_grids': len(self.grids),
                    'max_drawdown': self.max_drawdown,
                    'avg_profit_per_trade': 0
                }
                
        except Exception as e:
            self.log(f"❌ 获取统计信息失败: {e}")
            return {
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'closed_pairs': 0,
                'total_profit': 0,
                'current_grids': len(self.grids),
                'max_drawdown': 0,
                'avg_profit_per_trade': 0
            }
    
    def log(self, message):
        """记录日志"""
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_message = f"{timestamp} {message}"
        print(log_message)
        # 同步写入文件日志（每日轮转）
        try:
            self._append_file_log(log_message)
        except Exception:
            pass
        
        # 如果有UI回调函数，也输出到UI
        if hasattr(self, 'ui_log_callback') and self.ui_log_callback:
            try:
                self.ui_log_callback(log_message)
            except Exception as e:
                print(f"输出日志到UI失败: {e}") 

    def _append_file_log(self, line: str):
        """将日志追加到本地文件 logs/grid_strategy_<inst>_YYYYMMDD.log"""
        import os
        try:
            base_dir = os.path.join(os.getcwd(), 'logs')
            if not os.path.exists(base_dir):
                os.makedirs(base_dir, exist_ok=True)
            day = datetime.now().strftime('%Y%m%d')
            fname = f"grid_strategy_{self.instrument}_{day}.log"
            fpath = os.path.join(base_dir, fname)
            with open(fpath, 'a', encoding='utf-8') as f:
                f.write(line + "\n")
        except Exception:
            pass
    
    def log_operation(self, operation_type, details, price=0.0, size=0.0, order_id="", grid_id=""):
        """记录操作日志"""
        try:
            log_id = f"op_{int(time.time() * 1000)}"  # 使用毫秒时间戳作为ID
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # 获取当前市场价格
            current_market_price = 0.0
            try:
                success, price_data, _ = self._get_verified_price()
                if success:
                    current_market_price = price_data.get('price', 0)
                else:
                    # 如果验证价格失败，尝试直接获取
                    raw_data = self.client.get_ticker(inst_id=self.instrument)
                    if raw_data and 'data' in raw_data and raw_data['data']:
                        ticker_data = raw_data['data'][0]
                        if ticker_data and ticker_data.get('last'):
                            current_market_price = float(ticker_data['last'])
            except Exception as e:
                self.log(f"⚠️ 获取当前市场价格失败: {e}")
            
            operation_log = OperationLog(
                log_id=log_id,
                timestamp=timestamp,
                operation_type=operation_type,
                details=details,
                price=price,
                size=size,
                order_id=order_id,
                grid_id=grid_id,
                current_price=current_market_price
            )
            
            self.operation_logs.append(operation_log)
            
            # 输出到控制台日志（先输出，再入队写库，保持业务顺序）
            self.log(f"📝 操作记录: {operation_type} - {details}")
            
            # 保存到数据库（如果有的话）
            if self.db_manager:
                self._save_operation_log_to_db(operation_log)
            
            # 限制内存中的日志数量，只保留最近1000条
            if len(self.operation_logs) > 1000:
                self.operation_logs = self.operation_logs[-1000:]
                
        except Exception as e:
            self.log(f"❌ 记录操作日志失败: {e}")
    
    def _save_operation_log_to_db(self, operation_log):
        """保存操作日志到数据库（放入队列，保证顺序写入）"""
        try:
            if not self.db_manager:
                return
            self._db_write_queue.put(('op_log', operation_log))
        except Exception as e:
            self.log(f"❌ 入队操作日志失败: {e}")

    def _db_writer_loop(self):
        """顺序写库线程：按入队顺序写入数据库，保证表内顺序与业务顺序一致"""
        while True:
            try:
                item = self._db_write_queue.get()
                if not item:
                    continue
                kind, payload = item
                if kind == 'op_log':
                    try:
                        success = self.db_manager.save_operation_log(self.strategy_id, payload)
                        # 这里不再打印噪声日志，仅在失败时提示
                        if not success:
                            self.log("⚠️ 操作日志保存失败")
                    except Exception as e:
                        self.log(f"❌ 写库异常: {e}")
            except Exception:
                time.sleep(0.1)
    
    def get_operation_logs(self, limit=100, operation_type=None):
        """获取操作日志（优先从数据库获取）"""
        try:
            # 优先从数据库获取日志
            if self.db_manager:
                db_logs = self.db_manager.get_operation_logs(self.strategy_id, limit, operation_type)
                if db_logs:
                    # 将数据库记录转换为OperationLog对象
                    logs = []
                    for log_dict in db_logs:
                        log = OperationLog(
                            log_id=log_dict['log_id'],
                            timestamp=log_dict['timestamp'],
                            operation_type=log_dict['operation_type'],
                            details=log_dict['details'],
                            price=log_dict['price'],
                            size=log_dict['size'],
                            order_id=log_dict['order_id'],
                            grid_id=log_dict['grid_id']
                        )
                        logs.append(log)
                    return logs
            
            # 如果数据库不可用，使用内存中的日志
            logs = self.operation_logs.copy()
            
            # 按操作类型过滤
            if operation_type:
                logs = [log for log in logs if log.operation_type == operation_type]
            
            # 按时间倒序排列，最新的在前
            logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # 限制返回数量
            if limit:
                logs = logs[:limit]
            
            return logs
            
        except Exception as e:
            self.log(f"❌ 获取操作日志失败: {e}")
            return []
    
    def print_operation_summary(self):
        """打印操作摘要（优先使用数据库统计）"""
        try:
            self.log("📊 操作历史摘要:")
            self.log("=" * 60)
            
            # 优先从数据库获取统计信息
            if self.db_manager:
                summary = self.db_manager.get_operation_summary(self.strategy_id)
                operation_counts = summary.get('operation_counts', {})
                total_operations = summary.get('total_operations', 0)
                
                self.log(f"  总操作数量: {total_operations}")
                for op_type, count in operation_counts.items():
                    self.log(f"  {op_type}: {count}次")
                
                if summary.get('first_operation'):
                    self.log(f"  首次操作: {summary['first_operation']}")
                if summary.get('last_operation'):
                    self.log(f"  最近操作: {summary['last_operation']}")
            else:
                # 使用内存统计
                operation_counts = {}
                for log in self.operation_logs:
                    op_type = log.operation_type
                    operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
                
                for op_type, count in operation_counts.items():
                    self.log(f"  {op_type}: {count}次")
            
            self.log("=" * 60)
            
            # 显示最近10条操作
            recent_logs = self.get_operation_logs(limit=10)
            if recent_logs:
                self.log("📋 最近10条操作:")
                for i, log in enumerate(recent_logs, 1):
                    price_info = f" @${log.price:.2f}" if log.price > 0 else ""
                    size_info = f" {log.size}张" if log.size > 0 else ""
                    order_info = f" [{log.order_id[:8]}...]" if log.order_id else ""
                    
                    self.log(f"  {i:2d}. {log.timestamp} {log.operation_type}{price_info}{size_info}{order_info}")
            
            self.log("=" * 60)
            
        except Exception as e:
            self.log(f"❌ 打印操作摘要失败: {e}") 
    
    def _is_cache_valid(self, cache_type):
        """检查缓存是否有效"""
        current_time = time.time()
        if cache_type == 'positions':
            return (
                self.cached_positions is not None and
                current_time - self.positions_cache_timestamp < self.cache_validity
            )
        elif cache_type == 'price':
            return (
                self.cached_price is not None and
                current_time - self.price_cache_timestamp < self.cache_validity
            )
        return False
    
    def _should_pause_strategy(self):
        """检查是否应该暂停策略"""
        if self.critical_data_failed:
            current_time = time.time()
            if current_time < self.pause_until:
                return True
            else:
                # 暂停时间结束，重置标志
                self.critical_data_failed = False
                self.consecutive_failures = 0
                return False
        return False
    
    def _handle_critical_data_failure(self, data_type, error):
        """处理关键数据获取失败"""
        self.consecutive_failures += 1
        self.log(f"❌ 关键数据获取失败 ({data_type}): {error}")
        self.log(f"连续失败次数: {self.consecutive_failures}")
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            # 连续失败次数过多，暂停策略
            pause_duration = min(self.retry_delay * self.consecutive_failures, 60)  # 最多暂停60秒
            self.pause_until = time.time() + pause_duration
            self.critical_data_failed = True
            self.log(f"🚫 连续失败次数过多，策略暂停 {pause_duration} 秒")
        else:
            # 短暂暂停后重试
            self.pause_until = time.time() + self.retry_delay
            self.critical_data_failed = True
            self.log(f"⏸️ 策略暂停 {self.retry_delay} 秒后重试")
    
    def _retry_with_timeout(self, func, *args, **kwargs):
        """带超时和重试的函数调用"""
        for attempt in range(self.max_retries):
            try:
                # Windows系统使用线程超时，Unix系统使用信号超时
                if platform.system() == "Windows":
                    # Windows系统使用线程超时
                    import threading
                    
                    result_queue = queue.Queue()
                    exception_queue = queue.Queue()
                    
                    def worker():
                        try:
                            result = func(*args, **kwargs)
                            result_queue.put(result)
                        except Exception as e:
                            exception_queue.put(e)
                    
                    # 启动工作线程
                    worker_thread = threading.Thread(target=worker, daemon=True)
                    worker_thread.start()
                    
                    # 等待结果或超时
                    try:
                        result = result_queue.get(timeout=self.network_timeout)
                        # 成功获取数据，重置失败计数
                        self.consecutive_failures = 0
                        return result
                    except queue.Empty:
                        # 超时
                        raise TimeoutError(f"操作超时 ({self.network_timeout}秒)")
                    except Exception as e:
                        # 其他异常
                        if not exception_queue.empty():
                            raise exception_queue.get()
                        raise e
                else:
                    # Unix系统使用信号超时
                    import signal
                    
                    def timeout_handler(signum, frame):
                        raise TimeoutError(f"操作超时 ({self.network_timeout}秒)")
                    
                    # 设置信号处理器
                    signal.signal(signal.SIGALRM, timeout_handler)
                    signal.alarm(self.network_timeout)
                    
                    try:
                        result = func(*args, **kwargs)
                        # 清除超时
                        signal.alarm(0)
                        
                        # 成功获取数据，重置失败计数
                        self.consecutive_failures = 0
                        return result
                        
                    except TimeoutError:
                        signal.alarm(0)
                        raise
                    
            except Exception as e:
                if attempt < self.max_retries - 1:
                    self.log(f"⚠️ 第 {attempt + 1} 次尝试失败: {e}")
                    time.sleep(self.retry_delay)
                else:
                    self.log(f"❌ 所有重试都失败了: {e}")
                    raise
        
        return None
    
    def _safe_get_positions(self):
        """安全获取持仓信息，带重试和缓存"""
        try:
            # 检查缓存是否有效
            if self._is_cache_valid('positions'):
                self.log("📋 使用缓存的持仓信息")
                return self.cached_positions
            
            # 尝试获取最新持仓信息
            positions = self._retry_with_timeout(self.client.get_positions)
            
            if positions is not None:
                # 更新缓存
                self.cached_positions = positions
                self.positions_cache_timestamp = time.time()
                self.log("✅ 持仓信息获取成功")
                return positions
            else:
                raise Exception("持仓信息获取失败")
                
        except Exception as e:
            self._handle_critical_data_failure('positions', e)
            # 如果有有效缓存，使用缓存数据
            if self._is_cache_valid('positions'):
                self.log("⚠️ 使用过期缓存数据")
                return self.cached_positions
            return None
    
    def _safe_get_current_price(self):
        """安全获取当前价格，带重试和缓存"""
        try:
            # 检查缓存是否有效
            if self._is_cache_valid('price'):
                self.log("💰 使用缓存的价格信息")
                return self.cached_price
            
            # 冷却期内避免重复验证
            now_ts = time.time()
            if now_ts - self.last_price_verification_ts < self.price_verification_cooldown and self.cached_price:
                self.log("⏱️ 价格验证冷却中，返回最近价格")
                return self.cached_price

            # 尝试获取最新价格（带严格验证）
            price = self._retry_with_timeout(self.get_current_price)
            
            if price is not None and price > 0:
                # 更新缓存
                self.cached_price = price
                self.price_cache_timestamp = time.time()
                self.last_price_verification_ts = self.price_cache_timestamp
                self.log("✅ 价格信息获取成功")
                return price
            else:
                raise Exception("价格信息获取失败")
                
        except Exception as e:
            self._handle_critical_data_failure('price', e)
            # 如果有有效缓存，使用缓存数据
            if self._is_cache_valid('price'):
                self.log("⚠️ 使用过期缓存数据")
                return self.cached_price
            return None
    
    def _check_network_health(self):
        """检查网络连接健康状态"""
        try:
            # 尝试获取一个简单的API响应来检查网络状态
            test_result = self._retry_with_timeout(
                lambda: self.client.get_tickers("SWAP"),
                max_retries=1,  # 网络检查只重试1次
                retry_delay=1
            )
            
            if test_result is not None:
                self.log("✅ 网络连接正常")
                return True
            else:
                self.log("❌ 网络连接异常")
                return False
                
        except Exception as e:
            self.log(f"❌ 网络健康检查失败: {e}")
            return False
    
    def _wait_for_network_recovery(self):
        """等待网络恢复"""
        self.log("🌐 等待网络恢复...")
        recovery_attempts = 0
        max_recovery_attempts = 12  # 最多等待1分钟
        
        while recovery_attempts < max_recovery_attempts:
            if self._check_network_health():
                self.log("✅ 网络已恢复，继续执行策略")
                return True
            
            recovery_attempts += 1
            wait_time = min(5 * recovery_attempts, 30)  # 递增等待时间，最多30秒
            self.log(f"⏳ 网络仍未恢复，{wait_time}秒后重试... (尝试 {recovery_attempts}/{max_recovery_attempts})")
            time.sleep(wait_time)
        
        self.log("❌ 网络恢复超时，策略继续运行但可能不稳定")
        return False
    
    def get_strategy_health(self):
        """获取策略健康状态"""
        health_status = {
            'is_running': self.is_running,
            'critical_data_failed': self.critical_data_failed,
            'consecutive_failures': self.consecutive_failures,
            'max_consecutive_failures': self.max_consecutive_failures,
            'network_healthy': True,
            'cache_status': {
                'positions_cache_valid': self._is_cache_valid('positions'),
                'price_cache_valid': self._is_cache_valid('price'),
                'cache_age': time.time() - self.cache_timestamp if self.cache_timestamp > 0 else 0
            }
        }
        
        # 检查网络健康状态
        try:
            health_status['network_healthy'] = self._check_network_health()
        except:
            health_status['network_healthy'] = False
        
        # 添加状态描述
        if health_status['critical_data_failed']:
            if health_status['consecutive_failures'] >= health_status['max_consecutive_failures']:
                health_status['status_description'] = f"策略暂停中 - 连续失败{health_status['consecutive_failures']}次"
            else:
                health_status['status_description'] = f"策略暂停中 - 等待重试"
        elif not health_status['network_healthy']:
            health_status['status_description'] = "网络连接异常"
        else:
            health_status['status_description'] = "策略运行正常"
        
        return health_status
    
    def force_resume_strategy(self):
        """强制恢复策略运行"""
        if self.critical_data_failed:
            self.log("🔄 强制恢复策略运行")
            self.critical_data_failed = False
            self.consecutive_failures = 0
            self.pause_until = 0
            return True
        else:
            self.log("ℹ️ 策略当前没有暂停")
            return False
    
    def _verify_data_consistency(self, data_type, data_extractor_func, *args, **kwargs):
        """
        严格的数据一致性验证
        
        Args:
            data_type: 数据类型 ('positions', 'price', 'orders')
            data_extractor_func: 数据提取函数
            *args, **kwargs: 传递给数据提取函数的参数
            
        Returns:
            tuple: (is_valid, verified_data, error_message)
        """
        try:
            self.log(f"🔍 开始验证 {data_type} 数据一致性...")
            
            verification_results = []
            error_messages = []
            
            # 执行多次验证
            for attempt in range(self.data_verification_attempts):
                try:
                    self.log(f"  验证尝试 {attempt + 1}/{self.data_verification_attempts}")
                    
                    # 调用数据提取函数
                    result = data_extractor_func(*args, **kwargs)
                    
                    if result is None:
                        error_msg = f"第{attempt + 1}次验证返回None"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    # 根据数据类型进行验证
                    if data_type == 'positions':
                        verified_data = self._extract_position_data(result)
                    elif data_type == 'price':
                        verified_data = self._extract_price_data(result)
                    elif data_type == 'orders':
                        verified_data = self._extract_order_data(result)
                    else:
                        error_msg = f"未知的数据类型: {data_type}"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    if verified_data is not None:
                        verification_results.append(verified_data)
                        self.log(f"    ✅ 第{attempt + 1}次验证成功")
                    else:
                        error_msg = f"第{attempt + 1}次验证数据提取失败"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                    
                    # 如果不是最后一次验证，等待间隔
                    if attempt < self.data_verification_attempts - 1:
                        time.sleep(self.verification_interval)
                        
                except Exception as e:
                    error_msg = f"第{attempt + 1}次验证异常: {str(e)}"
                    error_messages.append(error_msg)
                    self.log(f"    ❌ {error_msg}")
                    if attempt < self.data_verification_attempts - 1:
                        time.sleep(self.verification_interval)
            
            # 分析验证结果
            if len(verification_results) == 0:
                error_msg = f"所有验证尝试都失败: {'; '.join(error_messages)}"
                self.log(f"❌ {error_msg}")
                return False, None, error_msg
            
            if len(verification_results) < self.min_verification_agreement:
                error_msg = f"验证成功次数不足: {len(verification_results)}/{self.min_verification_agreement}"
                self.log(f"❌ {error_msg}")
                return False, None, error_msg
            
            # 检查数据一致性
            is_consistent, consensus_data = self._check_data_consistency(verification_results, data_type)
            
            if not is_consistent:
                error_msg = f"数据不一致，验证结果: {verification_results}"
                self.log(f"❌ {error_msg}")
                return False, None, error_msg
            
            # 更新验证缓存
            self.verification_cache[data_type] = verification_results
            self.verification_timestamps[data_type] = time.time()
            
            self.log(f"✅ {data_type} 数据验证成功，一致结果: {consensus_data}")
            return True, consensus_data, None
            
        except Exception as e:
            error_msg = f"数据验证过程异常: {str(e)}"
            self.log(f"❌ {error_msg}")
            return False, None, error_msg
    
    def _extract_position_data(self, positions_result):
        """提取持仓数据"""
        try:
            if not positions_result:
                # 如果没有持仓数据，返回0持仓
                return {
                    'position_size': 0.0,
                    'instrument': self.instrument,
                    'position_side': 'long'
                }
            
            # 查找当前合约的long方向持仓
            current_position = 0.0
            for position in positions_result:
                if (position.get('instId') == self.instrument and 
                    position.get('posSide') == 'long'):
                    pos_size = position.get('pos', '0')
                    if pos_size and pos_size.strip():
                        try:
                            current_position = float(pos_size)
                        except (ValueError, TypeError):
                            current_position = 0.0
                        break
            
            # 即使没有找到持仓，也返回有效的数据结构
            return {
                'position_size': current_position,
                'instrument': self.instrument,
                'position_side': 'long'
            }
            
        except Exception as e:
            self.log(f"❌ 提取持仓数据失败: {e}")
            # 发生异常时，返回默认的0持仓数据
            return {
                'position_size': 0.0,
                'instrument': self.instrument,
                'position_side': 'long'
            }
    
    def _extract_price_data(self, price_result):
        """提取价格数据"""
        try:
            if not price_result:
                self.log("⚠️ 价格数据为空")
                return None
            
            # 查找当前合约的价格
            for ticker in price_result:
                if ticker.get('instId') == self.instrument:
                    price = ticker.get('last', '0')
                    if price and price.strip():
                        try:
                            return {
                                'price': float(price),
                                'instrument': self.instrument
                            }
                        except (ValueError, TypeError) as e:
                            self.log(f"⚠️ 价格数据转换失败: {price}, 错误: {e}")
                            continue
            
            self.log(f"⚠️ 未找到合约 {self.instrument} 的价格数据")
            return None
            
        except Exception as e:
            self.log(f"❌ 提取价格数据失败: {e}")
            return None
    
    def _extract_order_data(self, orders_result):
        """提取订单数据"""
        try:
            if not orders_result:
                return {
                    'total_orders': 0,
                    'buy_orders': 0,
                    'sell_orders': 0,
                    'instrument': self.instrument
                }
            
            total_orders = 0
            buy_orders = 0
            sell_orders = 0
            
            for order in orders_result:
                if order.get('instId') == self.instrument:
                    total_orders += 1
                    if order.get('side') == 'buy':
                        buy_orders += 1
                    elif order.get('side') == 'sell':
                        sell_orders += 1
            
            return {
                'total_orders': total_orders,
                'buy_orders': buy_orders,
                'sell_orders': sell_orders,
                'instrument': self.instrument
            }
            
        except Exception as e:
            self.log(f"❌ 提取订单数据失败: {e}")
            # 发生异常时，返回默认的空订单数据
            return {
                'total_orders': 0,
                'buy_orders': 0,
                'sell_orders': 0,
                'instrument': self.instrument
            }
    
    def _check_data_consistency(self, verification_results, data_type):
        """
        检查数据一致性
        
        Args:
            verification_results: 验证结果列表
            data_type: 数据类型
            
        Returns:
            tuple: (is_consistent, consensus_data)
        """
        try:
            if len(verification_results) == 0:
                return False, None
            
            # 对于数值类型数据，检查是否在允许的误差范围内
            if data_type in ['positions', 'price']:
                # 提取数值进行比较
                values = []
                for result in verification_results:
                    if data_type == 'positions':
                        values.append(result.get('position_size', 0))
                    elif data_type == 'price':
                        values.append(result.get('price', 0))
                
                # 检查数值一致性
                if len(set(values)) == 1:
                    # 所有值都相同
                    return True, verification_results[0]
                else:
                    # 检查是否在允许的误差范围内
                    min_val = min(values)
                    max_val = max(values)
                    if abs(max_val - min_val) <= self.max_verification_discrepancy:
                        # 在误差范围内，使用平均值
                        if data_type == 'positions':
                            avg_position = sum(values) / len(values)
                            consensus_data = verification_results[0].copy()
                            consensus_data['position_size'] = avg_position
                        elif data_type == 'price':
                            avg_price = sum(values) / len(values)
                            consensus_data = verification_results[0].copy()
                            consensus_data['price'] = avg_price
                        return True, consensus_data
                    else:
                        # 超出误差范围
                        self.log(f"❌ 数据不一致，差异过大: {values}")
                        return False, None
            
            # 对于订单数据，检查结构一致性
            elif data_type == 'orders':
                # 检查所有结果的结构是否一致
                first_result = verification_results[0]
                for result in verification_results[1:]:
                    if (result.get('total_orders') != first_result.get('total_orders') or
                        result.get('buy_orders') != first_result.get('buy_orders') or
                        result.get('sell_orders') != first_result.get('sell_orders')):
                        self.log(f"❌ 订单数据不一致: {verification_results}")
                        return False, None
                
                return True, first_result
            
            return False, None
            
        except Exception as e:
            self.log(f"❌ 检查数据一致性失败: {e}")
            return False, None
    
    def _get_verified_positions(self):
        """
        获取经过验证的持仓数据
        
        Returns:
            tuple: (success, position_data, error_message)
        """
        return self._verify_data_consistency('positions', self.client.get_positions)
    
    def _get_verified_price(self):
        """
        获取经过验证的价格数据
        
        Returns:
            tuple: (success, price_data, error_message)
        """
        try:
            # 检查价格验证缓存（使用更长TTL以降低验证频率）
            current_time = time.time()
            if (current_time - self.verification_timestamps.get('price', 0) < self.price_cache_ttl and
                self.verification_cache.get('price')):
                cached_data = self.verification_cache['price']
                self.log("📋 使用缓存的价格数据（验证缓存）")
                return True, cached_data, None
            
            # 执行专门的价格数据验证
            success, verified_data, error_message = self._verify_price_data()
            
            if success:
                # 更新缓存
                self.verification_cache['price'] = verified_data
                self.verification_timestamps['price'] = current_time
                
            # 记录本次验证时间用于冷却控制
            self.last_price_verification_ts = current_time
            return success, verified_data, error_message
            
        except Exception as e:
            error_msg = f"获取验证价格失败: {e}"
            self.log(f"❌ {error_msg}")
            return False, None, error_msg
    
    def _get_verified_orders(self):
        """
        获取经过验证的订单数据
        
        Returns:
            tuple: (success, order_data, error_message)
        """
        return self._verify_data_consistency('orders', self.client.get_order_list)
    
    def get_data_verification_status(self):
        """
        获取数据验证状态
        
        Returns:
            dict: 数据验证状态信息
        """
        try:
            current_time = time.time()
            
            status = {
                'verification_config': {
                    'attempts': self.data_verification_attempts,
                    'interval': self.verification_interval,
                    'min_agreement': self.min_verification_agreement,
                    'max_discrepancy': self.max_verification_discrepancy
                },
                'cache_status': {},
                'last_verification_results': {}
            }
            
            # 检查各类型数据的缓存状态
            for data_type in ['positions', 'price', 'orders']:
                cache_age = current_time - self.verification_timestamps.get(data_type, 0)
                cache_valid = cache_age < 60  # 1分钟内的缓存认为有效
                
                status['cache_status'][data_type] = {
                    'cache_age_seconds': cache_age,
                    'cache_valid': cache_valid,
                    'cached_results_count': len(self.verification_cache.get(data_type, []))
                }
                
                # 获取最近的验证结果
                cached_results = self.verification_cache.get(data_type, [])
                if cached_results:
                    status['last_verification_results'][data_type] = {
                        'last_result': cached_results[-1],
                        'all_results': cached_results
                    }
            
            return status
            
        except Exception as e:
            self.log(f"❌ 获取数据验证状态失败: {e}")
            return {
                'error': str(e),
                'verification_config': {},
                'cache_status': {},
                'last_verification_results': {}
            }
    
    def force_data_verification(self, data_type):
        """
        强制重新验证指定类型的数据
        
        Args:
            data_type: 数据类型 ('positions', 'price', 'orders')
            
        Returns:
            tuple: (success, data, error_message)
        """
        try:
            self.log(f"🔄 强制重新验证 {data_type} 数据...")
            
            # 清除缓存
            self.verification_cache[data_type] = []
            self.verification_timestamps[data_type] = 0
            
            # 执行验证
            if data_type == 'positions':
                return self._get_verified_positions()
            elif data_type == 'price':
                return self._get_verified_price()
            elif data_type == 'orders':
                return self._get_verified_orders()
            else:
                return False, None, f"未知的数据类型: {data_type}"
                
        except Exception as e:
            error_msg = f"强制验证 {data_type} 失败: {str(e)}"
            self.log(f"❌ {error_msg}")
            return False, None, error_msg
    
    def log_verification_summary(self):
        """输出数据验证摘要"""
        try:
            self.log("📊 数据验证摘要:")
            
            # 获取验证状态
            status = self.get_data_verification_status()
            
            # 输出配置信息
            config = status.get('verification_config', {})
            self.log(f"  配置: 验证次数={config.get('attempts', 3)}, "
                    f"间隔={config.get('interval', 2)}秒, "
                    f"最少同意={config.get('min_agreement', 2)}次")
            
            # 输出缓存状态
            cache_status = status.get('cache_status', {})
            for data_type, cache_info in cache_status.items():
                age = cache_info.get('cache_age_seconds', 0)
                valid = cache_info.get('cache_valid', False)
                count = cache_info.get('cached_results_count', 0)
                
                status_icon = "✅" if valid else "❌"
                self.log(f"  {data_type}: {status_icon} 缓存年龄={age:.1f}秒, "
                        f"结果数量={count}")
            
            # 输出最近的价格验证结果
            price_results = status.get('last_verification_results', {}).get('price', {})
            if price_results:
                last_result = price_results.get('last_result', {})
                if last_result:
                    price = last_result.get('price', 0)
                    price_range = last_result.get('price_range', 0)
                    verification_count = last_result.get('verification_count', 0)
                    self.log(f"  最新价格: ${price:.8f} (验证{verification_count}次, "
                            f"变化范围: {price_range:.8f})")
            
        except Exception as e:
            self.log(f"❌ 输出验证摘要失败: {e}")
    
    def log_price_verification_details(self):
        """输出价格验证的详细信息"""
        try:
            self.log("💰 价格验证详细信息:")
            
            # 获取验证状态
            status = self.get_data_verification_status()
            
            # 输出价格验证结果
            price_results = status.get('last_verification_results', {}).get('price', {})
            if price_results:
                all_results = price_results.get('all_results', [])
                if all_results:
                    self.log(f"  验证历史记录数: {len(all_results)}")
                    
                    # 显示最近3次的价格验证结果
                    recent_results = all_results[-3:] if len(all_results) >= 3 else all_results
                    for i, result in enumerate(recent_results):
                        price = result.get('price', 0)
                        timestamp = result.get('timestamp', 0)
                        price_range = result.get('price_range', 0)
                        verification_count = result.get('verification_count', 0)
                        
                        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S') if timestamp > 0 else "未知"
                        self.log(f"    {i+1}. ${price:.8f} @ {time_str} "
                                f"(验证{verification_count}次, 范围: {price_range:.8f})")
                else:
                    self.log("  暂无价格验证历史记录")
            else:
                self.log("  暂无价格验证数据")
                
        except Exception as e:
            self.log(f"❌ 输出价格验证详情失败: {e}")
    
    def _verify_price_data(self):
        """
        验证价格数据 - 考虑价格实时变化的特性
        
        Returns:
            tuple: (is_valid, price_data, error_message)
        """
        try:
            self.log("🔍 开始验证价格数据...")
            
            price_results = []
            error_messages = []
            
            # 为减少频率：若在冷却窗口内且已有有效验证缓存，则直接复用
            if (time.time() - self.last_price_verification_ts < self.price_verification_cooldown and
                self.verification_cache.get('price')):
                self.log("⏱️ 价格验证冷却中，复用最近验证结果")
                return True, self.verification_cache['price'], None

            # 快速连续获取价格数据（间隔0.5秒），仅在未命中冷却时执行
            for attempt in range(self.data_verification_attempts):
                try:
                    self.log(f"  价格验证尝试 {attempt + 1}/{self.data_verification_attempts}")
                    
                    # 获取原始价格数据
                    raw_data = self.client.get_ticker(inst_id=self.instrument)
                    
                    if not raw_data:
                        error_msg = f"价格数据获取失败: 返回None"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    if 'data' not in raw_data or not raw_data['data']:
                        error_msg = f"价格数据格式错误: {raw_data}"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    ticker_data = raw_data['data'][0]
                    if not ticker_data:
                        error_msg = f"价格数据为空: {raw_data}"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    # 提取关键价格信息
                    try:
                        price_info = {
                            'last': float(ticker_data.get('last', '0') or '0'),
                            'bidPx': float(ticker_data.get('bidPx', '0') or '0'),
                            'askPx': float(ticker_data.get('askPx', '0') or '0'),
                            'high24h': float(ticker_data.get('high24h', '0') or '0'),
                            'low24h': float(ticker_data.get('low24h', '0') or '0'),
                            'timestamp': time.time()
                        }
                    except (ValueError, TypeError) as e:
                        error_msg = f"价格数据转换失败: {ticker_data}, 错误: {e}"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                        continue
                    
                    # 验证价格数据的合理性
                    if self._validate_price_reasonableness(price_info):
                        price_results.append(price_info)
                        self.log(f"    ✅ 价格数据有效: ${price_info['last']:.8f}")
                    else:
                        error_msg = f"价格数据不合理: {price_info}"
                        error_messages.append(error_msg)
                        self.log(f"    ❌ {error_msg}")
                    
                    # 短暂等待后继续下一次验证
                    if attempt < self.data_verification_attempts - 1:
                        time.sleep(0.5)
                        
                except Exception as e:
                    error_msg = f"价格验证异常: {e}"
                    error_messages.append(error_msg)
                    self.log(f"    ❌ {error_msg}")
                    time.sleep(0.5)
            
            # 分析价格数据
            if len(price_results) >= self.min_verification_agreement:
                # 计算价格变化范围
                prices = [p['last'] for p in price_results]
                price_range = max(prices) - min(prices)
                avg_price = sum(prices) / len(prices)
                
                # 检查价格变化是否在合理范围内（允许0.1%的变化）
                max_allowed_change = avg_price * 0.001  # 0.1%
                
                if price_range <= max_allowed_change:
                    # 价格变化在合理范围内，使用最新价格
                    latest_price_info = price_results[-1]
                    
                    verified_data = {
                        'price': latest_price_info['last'],
                        'bid_price': latest_price_info['bidPx'],
                        'ask_price': latest_price_info['askPx'],
                        'price_range': price_range,
                        'avg_price': avg_price,
                        'verification_count': len(price_results),
                        'timestamp': latest_price_info['timestamp']
                    }
                    
                    self.log(f"✅ 价格验证成功: ${verified_data['price']:.8f} (变化范围: {price_range:.8f})")
                    return True, verified_data, None
                else:
                    error_msg = f"价格变化过大: 范围={price_range:.8f}, 平均={avg_price:.8f}, 允许={max_allowed_change:.8f}"
                    self.log(f"❌ {error_msg}")
                    return False, None, error_msg
            else:
                error_msg = f"价格验证失败: 成功次数={len(price_results)}, 需要={self.min_verification_agreement}"
                self.log(f"❌ {error_msg}")
                return False, None, error_msg
                
        except Exception as e:
            error_msg = f"价格验证过程异常: {e}"
            self.log(f"❌ {error_msg}")
            return False, None, error_msg
    
    def _validate_price_reasonableness(self, price_info):
        """
        验证价格数据的合理性
        
        Args:
            price_info: 价格信息字典
            
        Returns:
            bool: 价格是否合理
        """
        try:
            last_price = price_info['last']
            bid_price = price_info['bidPx']
            ask_price = price_info['askPx']
            high_24h = price_info['high24h']
            low_24h = price_info['low24h']
            
            # 基本合理性检查
            if last_price <= 0 or bid_price <= 0 or ask_price <= 0:
                return False
            
            # 买卖价差检查（价差不应超过1%）
            if ask_price > 0 and bid_price > 0:
                spread = (ask_price - bid_price) / bid_price
                if spread > 0.01:  # 1%
                    return False
            
            # 价格应在24小时高低点范围内（允许0.5%的误差）
            if high_24h > 0 and low_24h > 0:
                if last_price < low_24h * 0.995 or last_price > high_24h * 1.005:
                    return False
            
            # 最新价格应在买卖价之间或接近
            if bid_price > 0 and ask_price > 0:
                if last_price < bid_price * 0.99 or last_price > ask_price * 1.01:
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"价格合理性检查异常: {e}")
            return False

 