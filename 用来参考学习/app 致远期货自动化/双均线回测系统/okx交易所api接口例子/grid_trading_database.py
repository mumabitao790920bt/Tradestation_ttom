#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网格交易数据库记录功能
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import asdict

class GridTradingDatabase:
    """网格交易数据库类"""
    
    def __init__(self, db_path: str = "grid_trading.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 创建策略记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT UNIQUE,
                        instrument TEXT,
                        base_price REAL,
                        grid_width REAL,
                        trade_mode TEXT,
                        trade_value REAL,
                        start_time TEXT,
                        end_time TEXT,
                        status TEXT,
                        total_profit REAL DEFAULT 0.0,
                        total_trades INTEGER DEFAULT 0,
                        profitable_trades INTEGER DEFAULT 0,
                        max_drawdown REAL DEFAULT 0.0
                    )
                ''')
                
                # 创建策略状态表 - 新增
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS strategy_status (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT UNIQUE,
                        instrument TEXT,
                        base_price REAL,
                        grid_width REAL,
                        trade_size REAL,  -- 新增：交易数量字段
                        current_price REAL,
                        current_grid_index INTEGER,
                        current_grid_price REAL,
                        grid_direction TEXT,
                        grid_number INTEGER,
                        down_grids INTEGER,
                        up_grids INTEGER,
                        grid_prices TEXT,  -- JSON格式存储所有网格价格
                        expected_buy_orders TEXT,  -- JSON格式存储预期买单
                        expected_sell_orders TEXT,  -- JSON格式存储预期卖单
                        current_position REAL DEFAULT 0.0,
                        total_profit REAL DEFAULT 0.0,
                        active_orders_count INTEGER DEFAULT 0,
                        last_update_time TEXT,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建网格订单表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grid_orders (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        grid_id TEXT,
                        order_id TEXT,
                        price REAL,
                        side TEXT,
                        size REAL,
                        status TEXT,
                        create_time TEXT,
                        fill_time TEXT,
                        fill_price REAL,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建交易记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        trade_id TEXT,
                        order_id TEXT,
                        side TEXT,
                        price REAL,
                        size REAL,
                        timestamp TEXT,
                        profit REAL DEFAULT 0.0,
                        grid_id TEXT,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建套利记录表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS profit_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        buy_order_id TEXT,
                        sell_order_id TEXT,
                        buy_price REAL,
                        sell_price REAL,
                        size REAL,
                        profit REAL,
                        timestamp TEXT,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建交易配对记录表 - 新增
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trade_pairs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        pair_id TEXT UNIQUE,
                        buy_order_id TEXT,
                        sell_order_id TEXT,
                        buy_price REAL,
                        sell_price REAL,
                        size REAL,
                        buy_time TEXT,
                        sell_time TEXT,
                        profit REAL,
                        status TEXT DEFAULT 'open',  -- 'open' or 'closed'
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建持仓明细表 - 新增
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS position_details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        order_id TEXT,
                        price REAL,
                        size REAL,
                        timestamp TEXT,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                # 创建操作日志表
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS operation_logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        log_id TEXT UNIQUE,
                        strategy_id TEXT,
                        timestamp TEXT,
                        operation_type TEXT,
                        details TEXT,
                        price REAL DEFAULT 0.0,
                        size REAL DEFAULT 0.0,
                        order_id TEXT DEFAULT '',
                        grid_id TEXT DEFAULT '',
                        current_price REAL DEFAULT 0.0,  -- 操作时的实时市场价格
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')

                # 创建网格层级表（用于可视化 20下 + 1上 + 基准价）
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS grid_levels (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        strategy_id TEXT,
                        level_index INTEGER,               -- 从高到低排序的索引
                        direction TEXT,                    -- 'up' | 'down' | 'base'
                        price REAL,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(strategy_id, level_index),
                        FOREIGN KEY (strategy_id) REFERENCES strategies (strategy_id)
                    )
                ''')
                
                conn.commit()
                
                # ========= 兼容已有老库的表结构，按需迁移 =========
                # 1) 为 operation_logs 表添加 current_price 字段（如果不存在）
                try:
                    cursor.execute("PRAGMA table_info(operation_logs)")
                    op_columns = [column[1] for column in cursor.fetchall()]
                    if 'current_price' not in op_columns:
                        cursor.execute('ALTER TABLE operation_logs ADD COLUMN current_price REAL DEFAULT 0.0')
                        conn.commit()
                        print("✅ 已为operation_logs表添加current_price字段")
                except Exception as e:
                    print(f"⚠️ 检查/添加operation_logs.current_price字段时出错: {e}")
                
                # 检查并添加trade_size字段（如果不存在）
                try:
                    cursor.execute("PRAGMA table_info(strategy_status)")
                    columns = [column[1] for column in cursor.fetchall()]
                    if 'trade_size' not in columns:
                        cursor.execute('ALTER TABLE strategy_status ADD COLUMN trade_size REAL')
                        conn.commit()
                        print("✅ 已为strategy_status表添加trade_size字段")
                    # 为策略状态添加最近成交信息字段
                    if 'last_fill_price' not in columns:
                        cursor.execute('ALTER TABLE strategy_status ADD COLUMN last_fill_price REAL DEFAULT 0')
                        conn.commit()
                        print("✅ 已为strategy_status表添加last_fill_price字段")
                    if 'last_fill_side' not in columns:
                        cursor.execute("ALTER TABLE strategy_status ADD COLUMN last_fill_side TEXT DEFAULT ''")
                        conn.commit()
                        print("✅ 已为strategy_status表添加last_fill_side字段")
                    if 'last_fill_ts' not in columns:
                        cursor.execute("ALTER TABLE strategy_status ADD COLUMN last_fill_ts TEXT DEFAULT ''")
                        conn.commit()
                        print("✅ 已为strategy_status表添加last_fill_ts字段")
                except Exception as e:
                    print(f"⚠️ 添加trade_size字段时出错: {e}")
                
        except Exception as e:
            print(f"❌ 初始化数据库失败: {e}")
    
    def create_strategy(self, strategy_id: str, params: Dict) -> bool:
        """创建策略记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO strategies (
                        strategy_id, instrument, base_price, grid_width,
                        trade_mode, trade_value, start_time, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    params['instrument'],
                    params['base_price'],
                    params['grid_width'],
                    params['trade_mode'],
                    params['trade_value'],
                    datetime.now().isoformat(),
                    'running'
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 创建策略记录失败: {e}")
            return False
    
    def update_strategy_status(self, strategy_id: str, status: str, end_time: str = None):
        """更新策略状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if end_time:
                    cursor.execute('''
                        UPDATE strategies 
                        SET status = ?, end_time = ?
                        WHERE strategy_id = ?
                    ''', (status, end_time, strategy_id))
                else:
                    cursor.execute('''
                        UPDATE strategies 
                        SET status = ?
                        WHERE strategy_id = ?
                    ''', (status, strategy_id))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ 更新策略状态失败: {e}")
    
    def add_grid_order(self, strategy_id: str, grid_order: Dict) -> bool:
        """添加网格订单记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO grid_orders (
                        strategy_id, grid_id, order_id, price, side,
                        size, status, create_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    grid_order['grid_id'],
                    grid_order['order_id'],
                    grid_order['price'],
                    grid_order['side'],
                    grid_order['size'],
                    grid_order['status'],
                    grid_order['create_time']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 添加网格订单记录失败: {e}")
            return False
    
    def update_grid_order(self, strategy_id: str, grid_id: str, updates: Dict):
        """更新网格订单记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [strategy_id, grid_id]
                
                cursor.execute(f'''
                    UPDATE grid_orders 
                    SET {set_clause}
                    WHERE strategy_id = ? AND grid_id = ?
                ''', values)
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ 更新网格订单记录失败: {e}")
    
    def add_trade_record(self, strategy_id: str, trade_record: Dict) -> bool:
        """添加交易记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trade_records (
                        strategy_id, trade_id, order_id, side, price,
                        size, timestamp, profit, grid_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    trade_record['trade_id'],
                    trade_record['order_id'],
                    trade_record['side'],
                    trade_record['price'],
                    trade_record['size'],
                    trade_record['timestamp'],
                    trade_record.get('profit', 0.0),
                    trade_record.get('grid_id')
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 添加交易记录失败: {e}")
            return False
    
    def add_profit_record(self, strategy_id: str, profit_record: Dict) -> bool:
        """添加套利记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO profit_records (
                        strategy_id, buy_order_id, sell_order_id, buy_price,
                        sell_price, size, profit, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    profit_record['buy_order_id'],
                    profit_record['sell_order_id'],
                    profit_record['buy_price'],
                    profit_record['sell_price'],
                    profit_record['size'],
                    profit_record['profit'],
                    profit_record['timestamp']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 添加套利记录失败: {e}")
            return False
    
    def get_strategy_statistics(self, strategy_id: str) -> Dict:
        """获取策略统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取策略基本信息
                cursor.execute('''
                    SELECT total_profit, total_trades, profitable_trades, max_drawdown
                    FROM strategies
                    WHERE strategy_id = ?
                ''', (strategy_id,))
                
                result = cursor.fetchone()
                if result:
                    stats = {
                        'total_profit': result[0] or 0.0,
                        'total_trades': result[1] or 0,
                        'profitable_trades': result[2] or 0,
                        'max_drawdown': result[3] or 0.0
                    }
                    
                    # 获取当前网格数量
                    cursor.execute('''
                        SELECT COUNT(*) FROM grid_orders
                        WHERE strategy_id = ? AND status = 'pending'
                    ''', (strategy_id,))
                    
                    current_grids = cursor.fetchone()[0]
                    stats['current_grids'] = current_grids
                    
                    return stats
                
                return {}
                
        except Exception as e:
            print(f"❌ 获取策略统计信息失败: {e}")
            return {}
    
    def get_trade_history(self, strategy_id: str) -> List[Dict]:
        """获取交易历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT trade_id, order_id, side, price, size, 
                           timestamp, profit, grid_id
                    FROM trade_records
                    WHERE strategy_id = ?
                    ORDER BY timestamp DESC
                ''', (strategy_id,))
                
                results = cursor.fetchall()
                trades = []
                
                for row in results:
                    trades.append({
                        'trade_id': row[0],
                        'order_id': row[1],
                        'side': row[2],
                        'price': row[3],
                        'size': row[4],
                        'timestamp': row[5],
                        'profit': row[6],
                        'grid_id': row[7]
                    })
                
                return trades
                
        except Exception as e:
            print(f"❌ 获取交易历史失败: {e}")
            return []
    
    def get_profit_history(self, strategy_id: str) -> List[Dict]:
        """获取套利历史"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT buy_order_id, sell_order_id, buy_price, sell_price,
                           size, profit, timestamp
                    FROM profit_records
                    WHERE strategy_id = ?
                    ORDER BY timestamp DESC
                ''', (strategy_id,))
                
                results = cursor.fetchall()
                profits = []
                
                for row in results:
                    profits.append({
                        'buy_order_id': row[0],
                        'sell_order_id': row[1],
                        'buy_price': row[2],
                        'sell_price': row[3],
                        'size': row[4],
                        'profit': row[5],
                        'timestamp': row[6]
                    })
                
                return profits
                
        except Exception as e:
            print(f"❌ 获取套利历史失败: {e}")
            return []
    
    def update_strategy_stats(self, strategy_id: str, stats: Dict):
        """更新策略统计信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE strategies 
                    SET total_profit = ?, total_trades = ?, 
                        profitable_trades = ?, max_drawdown = ?
                    WHERE strategy_id = ?
                ''', (
                    stats.get('total_profit', 0.0),
                    stats.get('total_trades', 0),
                    stats.get('profitable_trades', 0),
                    stats.get('max_drawdown', 0.0),
                    strategy_id
                ))
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ 更新策略统计信息失败: {e}")

    # 新增策略状态管理方法
    def save_strategy_status(self, strategy_id: str, status_data: Dict) -> bool:
        """保存策略状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查是否已存在
                cursor.execute('SELECT id FROM strategy_status WHERE strategy_id = ?', (strategy_id,))
                exists = cursor.fetchone()
                
                if exists:
                    # 更新现有记录
                    cursor.execute('''
                        UPDATE strategy_status SET
                            instrument = ?, base_price = ?, grid_width = ?, trade_size = ?, current_price = ?,
                            current_grid_index = ?, current_grid_price = ?, grid_direction = ?,
                            grid_number = ?, down_grids = ?, up_grids = ?, grid_prices = ?,
                            expected_buy_orders = ?, expected_sell_orders = ?, current_position = ?,
                            total_profit = ?, active_orders_count = ?, last_update_time = ?,
                            last_fill_price = ?, last_fill_side = ?, last_fill_ts = ?
                        WHERE strategy_id = ?
                    ''', (
                        status_data.get('instrument'),
                        status_data.get('base_price'),
                        status_data.get('grid_width'),
                        status_data.get('trade_size'),
                        status_data.get('current_price'),
                        status_data.get('current_grid_index'),
                        status_data.get('current_grid_price'),
                        status_data.get('grid_direction'),
                        status_data.get('grid_number'),
                        status_data.get('down_grids'),
                        status_data.get('up_grids'),
                        json.dumps(status_data.get('grid_prices', [])),
                        json.dumps(status_data.get('expected_buy_orders', [])),
                        json.dumps(status_data.get('expected_sell_orders', [])),
                        status_data.get('current_position', 0.0),
                        status_data.get('total_profit', 0.0),
                        status_data.get('active_orders_count', 0),
                        datetime.now().isoformat(),
                        status_data.get('last_fill_price', 0.0),
                        status_data.get('last_fill_side', ''),
                        status_data.get('last_fill_ts', ''),
                        strategy_id
                    ))
                else:
                    # 创建新记录
                    cursor.execute('''
                        INSERT INTO strategy_status (
                            strategy_id, instrument, base_price, grid_width, trade_size, current_price,
                            current_grid_index, current_grid_price, grid_direction, grid_number,
                            down_grids, up_grids, grid_prices, expected_buy_orders, expected_sell_orders,
                            current_position, total_profit, active_orders_count, last_update_time,
                            last_fill_price, last_fill_side, last_fill_ts
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        strategy_id,
                        status_data.get('instrument'),
                        status_data.get('base_price'),
                        status_data.get('grid_width'),
                        status_data.get('trade_size'),
                        status_data.get('current_price'),
                        status_data.get('current_grid_index'),
                        status_data.get('current_grid_price'),
                        status_data.get('grid_direction'),
                        status_data.get('grid_number'),
                        status_data.get('down_grids'),
                        status_data.get('up_grids'),
                        json.dumps(status_data.get('grid_prices', [])),
                        json.dumps(status_data.get('expected_buy_orders', [])),
                        json.dumps(status_data.get('expected_sell_orders', [])),
                        status_data.get('current_position', 0.0),
                        status_data.get('total_profit', 0.0),
                        status_data.get('active_orders_count', 0),
                        datetime.now().isoformat(),
                        status_data.get('last_fill_price', 0.0),
                        status_data.get('last_fill_side', ''),
                        status_data.get('last_fill_ts', '')
                    ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 保存策略状态失败: {e}")
            return False

    def get_strategy_status(self, strategy_id: str) -> Optional[Dict]:
        """获取策略状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM strategy_status WHERE strategy_id = ?
                ''', (strategy_id,))
                
                row = cursor.fetchone()
                if row:
                    # 获取列名
                    columns = [description[0] for description in cursor.description]
                    status_data = dict(zip(columns, row))
                    
                    # 解析JSON字段
                    if status_data.get('grid_prices'):
                        status_data['grid_prices'] = json.loads(status_data['grid_prices'])
                    if status_data.get('expected_buy_orders'):
                        status_data['expected_buy_orders'] = json.loads(status_data['expected_buy_orders'])
                    if status_data.get('expected_sell_orders'):
                        status_data['expected_sell_orders'] = json.loads(status_data['expected_sell_orders'])
                    
                    return status_data
                return None
        except Exception as e:
            print(f"❌ 获取策略状态失败: {e}")
            return None

    def delete_strategy_status(self, strategy_id: str) -> bool:
        """删除策略状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM strategy_status WHERE strategy_id = ?', (strategy_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"❌ 删除策略状态失败: {e}")
            return False
    
    def delete_strategy(self, strategy_id: str) -> bool:
        """删除指定策略记录（包括所有相关数据）"""
        try:
            print(f"🗑️ 开始删除策略: {strategy_id}")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查删除前的数据
                cursor.execute('SELECT COUNT(*) FROM strategy_status WHERE strategy_id = ?', (strategy_id,))
                status_count = cursor.fetchone()[0]
                print(f"📊 删除前strategy_status记录数: {status_count}")
                
                cursor.execute('SELECT COUNT(*) FROM strategies WHERE strategy_id = ?', (strategy_id,))
                strategy_count = cursor.fetchone()[0]
                print(f"📊 删除前strategies记录数: {strategy_count}")
                
                # 删除策略状态
                cursor.execute('DELETE FROM strategy_status WHERE strategy_id = ?', (strategy_id,))
                status_deleted = cursor.rowcount
                print(f"🗑️ 删除strategy_status记录: {status_deleted}条")
                
                # 删除网格层级
                cursor.execute('DELETE FROM grid_levels WHERE strategy_id = ?', (strategy_id,))
                levels_deleted = cursor.rowcount
                print(f"🗑️ 删除grid_levels记录: {levels_deleted}条")
                
                # 删除网格订单记录
                cursor.execute('DELETE FROM grid_orders WHERE strategy_id = ?', (strategy_id,))
                orders_deleted = cursor.rowcount
                print(f"🗑️ 删除grid_orders记录: {orders_deleted}条")
                
                # 删除交易记录
                cursor.execute('DELETE FROM trade_records WHERE strategy_id = ?', (strategy_id,))
                trades_deleted = cursor.rowcount
                print(f"🗑️ 删除trade_records记录: {trades_deleted}条")
                
                # 删除套利记录
                cursor.execute('DELETE FROM profit_records WHERE strategy_id = ?', (strategy_id,))
                profits_deleted = cursor.rowcount
                print(f"🗑️ 删除profit_records记录: {profits_deleted}条")
                
                # 删除主策略记录
                cursor.execute('DELETE FROM strategies WHERE strategy_id = ?', (strategy_id,))
                strategy_deleted = cursor.rowcount
                print(f"🗑️ 删除strategies记录: {strategy_deleted}条")
                
                conn.commit()
                print(f"✅ 策略 {strategy_id} 及其所有相关数据已删除")
                return True
        except Exception as e:
            print(f"❌ 删除策略失败: {e}")
            return False
    
    def delete_all_strategies(self) -> bool:
        """删除所有策略记录（包括所有相关数据）"""
        try:
            print("🗑️ 开始删除所有策略")
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查删除前的数据
                cursor.execute('SELECT COUNT(*) FROM strategy_status')
                status_count = cursor.fetchone()[0]
                print(f"📊 删除前strategy_status记录数: {status_count}")
                
                cursor.execute('SELECT COUNT(*) FROM strategies')
                strategy_count = cursor.fetchone()[0]
                print(f"📊 删除前strategies记录数: {strategy_count}")
                
                cursor.execute('SELECT COUNT(*) FROM grid_orders')
                orders_count = cursor.fetchone()[0]
                print(f"📊 删除前grid_orders记录数: {orders_count}")
                
                cursor.execute('SELECT COUNT(*) FROM trade_records')
                trades_count = cursor.fetchone()[0]
                print(f"📊 删除前trade_records记录数: {trades_count}")
                
                cursor.execute('SELECT COUNT(*) FROM profit_records')
                profits_count = cursor.fetchone()[0]
                print(f"📊 删除前profit_records记录数: {profits_count}")
                
                cursor.execute('SELECT COUNT(*) FROM trade_pairs')
                pairs_count = cursor.fetchone()[0]
                print(f"📊 删除前trade_pairs记录数: {pairs_count}")
                
                cursor.execute('SELECT COUNT(*) FROM position_details')
                position_details_count = cursor.fetchone()[0]
                print(f"📊 删除前position_details记录数: {position_details_count}")
                
                # 删除所有策略状态
                cursor.execute('DELETE FROM strategy_status')
                status_deleted = cursor.rowcount
                print(f"🗑️ 删除strategy_status记录: {status_deleted}条")
                
                # 删除所有网格层级
                cursor.execute('DELETE FROM grid_levels')
                levels_deleted = cursor.rowcount
                print(f"🗑️ 删除grid_levels记录: {levels_deleted}条")
                
                # 删除所有网格订单记录
                cursor.execute('DELETE FROM grid_orders')
                orders_deleted = cursor.rowcount
                print(f"🗑️ 删除grid_orders记录: {orders_deleted}条")
                
                # 删除所有交易记录
                cursor.execute('DELETE FROM trade_records')
                trades_deleted = cursor.rowcount
                print(f"🗑️ 删除trade_records记录: {trades_deleted}条")
                
                # 删除所有套利记录
                cursor.execute('DELETE FROM profit_records')
                profits_deleted = cursor.rowcount
                print(f"🗑️ 删除profit_records记录: {profits_deleted}条")
                
                # 删除所有交易配对记录
                cursor.execute('DELETE FROM trade_pairs')
                pairs_deleted = cursor.rowcount
                print(f"🗑️ 删除trade_pairs记录: {pairs_deleted}条")
                
                # 删除所有持仓明细记录
                cursor.execute('DELETE FROM position_details')
                position_details_deleted = cursor.rowcount
                print(f"🗑️ 删除position_details记录: {position_details_deleted}条")
                
                # 删除所有主策略记录
                cursor.execute('DELETE FROM strategies')
                strategy_deleted = cursor.rowcount
                print(f"🗑️ 删除strategies记录: {strategy_deleted}条")
                
                conn.commit()
                print("✅ 所有策略及其相关数据已删除")
                return True
        except Exception as e:
            print(f"❌ 删除所有策略失败: {e}")
            return False
    
    def get_all_strategy_status(self) -> Dict[str, Dict]:
        """获取所有策略状态"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM strategy_status")
                rows = cursor.fetchall()
                
                if not rows:
                    return {}
                
                # 获取列名
                columns = [description[0] for description in cursor.description]
                
                # 构建结果字典
                result = {}
                for row in rows:
                    strategy_data = dict(zip(columns, row))
                    strategy_id = strategy_data['strategy_id']
                    
                    # 解析JSON字段
                    if strategy_data.get('grid_prices'):
                        try:
                            strategy_data['grid_prices'] = json.loads(strategy_data['grid_prices'])
                        except:
                            strategy_data['grid_prices'] = []
                    
                    if strategy_data.get('expected_buy_orders'):
                        try:
                            strategy_data['expected_buy_orders'] = json.loads(strategy_data['expected_buy_orders'])
                        except:
                            strategy_data['expected_buy_orders'] = []
                    
                    if strategy_data.get('expected_sell_orders'):
                        try:
                            strategy_data['expected_sell_orders'] = json.loads(strategy_data['expected_sell_orders'])
                        except:
                            strategy_data['expected_sell_orders'] = []
                    
                    result[strategy_id] = strategy_data
                
                return result
        except Exception as e:
            print(f"❌ 获取所有策略状态失败: {e}")
            return {}
    
    def add_trade_pair(self, strategy_id: str, pair_data: Dict) -> bool:
        """添加交易配对记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO trade_pairs (
                        strategy_id, pair_id, buy_order_id, sell_order_id,
                        buy_price, sell_price, size, buy_time, sell_time, profit, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    pair_data['pair_id'],
                    pair_data['buy_order_id'],
                    pair_data['sell_order_id'],
                    pair_data['buy_price'],
                    pair_data['sell_price'],
                    pair_data['size'],
                    pair_data['buy_time'],
                    pair_data['sell_time'],
                    pair_data['profit'],
                    pair_data['status']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 添加交易配对记录失败: {e}")
            return False
    
    def update_trade_pair(self, strategy_id: str, pair_id: str, updates: Dict) -> bool:
        """更新交易配对记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 构建更新语句
                set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
                values = list(updates.values()) + [strategy_id, pair_id]
                
                cursor.execute(f'''
                    UPDATE trade_pairs 
                    SET {set_clause}
                    WHERE strategy_id = ? AND pair_id = ?
                ''', values)
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 更新交易配对记录失败: {e}")
            return False
    
    def add_position_detail(self, strategy_id: str, position_data: Dict) -> bool:
        """添加持仓明细记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO position_details (
                        strategy_id, order_id, price, size, timestamp
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    strategy_id,
                    position_data['order_id'],
                    position_data['price'],
                    position_data['size'],
                    position_data['timestamp']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 添加持仓明细记录失败: {e}")
            return False
    
    def get_trade_pairs(self, strategy_id: str) -> List[Dict]:
        """获取交易配对记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM trade_pairs WHERE strategy_id = ? ORDER BY buy_time DESC", (strategy_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # 获取列名
                columns = [description[0] for description in cursor.description]
                
                # 构建结果列表
                result = []
                for row in rows:
                    pair_data = dict(zip(columns, row))
                    result.append(pair_data)
                
                return result
        except Exception as e:
            print(f"❌ 获取交易配对记录失败: {e}")
            return []
    
    def get_position_details(self, strategy_id: str) -> List[Dict]:
        """获取持仓明细记录"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM position_details WHERE strategy_id = ? ORDER BY timestamp DESC", (strategy_id,))
                rows = cursor.fetchall()
                
                if not rows:
                    return []
                
                # 获取列名
                columns = [description[0] for description in cursor.description]
                
                # 构建结果列表
                result = []
                for row in rows:
                    detail_data = dict(zip(columns, row))
                    result.append(detail_data)
                
                return result
        except Exception as e:
            print(f"❌ 获取持仓明细记录失败: {e}")
            return []
    
    def get_strategy_summary(self, strategy_id: str) -> Dict:
        """获取策略汇总信息"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 获取交易配对统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_pairs,
                        SUM(CASE WHEN status = 'closed' THEN 1 ELSE 0 END) as closed_pairs,
                        SUM(CASE WHEN status = 'closed' THEN profit ELSE 0 END) as total_profit,
                        AVG(CASE WHEN status = 'closed' THEN profit ELSE NULL END) as avg_profit
                    FROM trade_pairs 
                    WHERE strategy_id = ?
                """, (strategy_id,))
                
                pair_stats = cursor.fetchone()
                
                # 获取持仓明细统计
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_positions,
                        SUM(size) as total_size,
                        SUM(price * size) as total_value
                    FROM position_details 
                    WHERE strategy_id = ?
                """, (strategy_id,))
                
                position_stats = cursor.fetchone()
                
                # 构建汇总信息
                summary = {
                    'total_pairs': pair_stats[0] if pair_stats else 0,
                    'closed_pairs': pair_stats[1] if pair_stats else 0,
                    'total_profit': pair_stats[2] if pair_stats else 0.0,
                    'avg_profit': pair_stats[3] if pair_stats else 0.0,
                    'total_positions': position_stats[0] if position_stats else 0,
                    'total_size': position_stats[1] if position_stats else 0.0,
                    'avg_price': (position_stats[2] / position_stats[1]) if position_stats and position_stats[1] > 0 else 0.0
                }
                
                return summary
                
        except Exception as e:
            print(f"❌ 获取策略汇总信息失败: {e}")
            return {}
    
    def save_operation_log(self, strategy_id: str, operation_log) -> bool:
        """保存操作日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO operation_logs 
                    (log_id, strategy_id, timestamp, operation_type, details, price, size, order_id, grid_id, current_price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    operation_log.log_id,
                    strategy_id,
                    operation_log.timestamp,
                    operation_log.operation_type,
                    operation_log.details,
                    operation_log.price,
                    operation_log.size,
                    operation_log.order_id,
                    operation_log.grid_id,
                    operation_log.current_price if hasattr(operation_log, 'current_price') else 0.0
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ 保存操作日志失败: {e}")
            return False
    
    def get_operation_logs(self, strategy_id: str, limit: int = 100, operation_type: str = None) -> List[Dict]:
        """获取操作日志"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if operation_type:
                    cursor.execute('''
                        SELECT * FROM operation_logs 
                        WHERE strategy_id = ? AND operation_type = ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (strategy_id, operation_type, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM operation_logs 
                        WHERE strategy_id = ?
                        ORDER BY created_at DESC 
                        LIMIT ?
                    ''', (strategy_id, limit))
                
                columns = [description[0] for description in cursor.description]
                logs = []
                
                for row in cursor.fetchall():
                    log_dict = dict(zip(columns, row))
                    logs.append(log_dict)
                
                return logs
                
        except Exception as e:
            print(f"❌ 获取操作日志失败: {e}")
            return []
    
    def delete_operation_logs(self, strategy_id: str) -> bool:
        """删除策略的所有操作日志（重置策略时使用）"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM operation_logs WHERE strategy_id = ?', (strategy_id,))
                deleted_count = cursor.rowcount
                
                conn.commit()
                
                print(f"✅ 已删除策略 {strategy_id} 的 {deleted_count} 条操作日志")
                return True
                
        except Exception as e:
            print(f"❌ 删除操作日志失败: {e}")
            return False
    
    def get_operation_summary(self, strategy_id: str) -> Dict:
        """获取操作摘要统计"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 统计各类操作数量
                cursor.execute('''
                    SELECT operation_type, COUNT(*) as count
                    FROM operation_logs 
                    WHERE strategy_id = ?
                    GROUP BY operation_type
                ''', (strategy_id,))
                
                operation_counts = {}
                for row in cursor.fetchall():
                    operation_counts[row[0]] = row[1]
                
                # 获取总操作数量
                cursor.execute('''
                    SELECT COUNT(*) FROM operation_logs WHERE strategy_id = ?
                ''', (strategy_id,))
                total_operations = cursor.fetchone()[0]
                
                # 获取最早和最新的操作时间
                cursor.execute('''
                    SELECT MIN(created_at), MAX(created_at) 
                    FROM operation_logs WHERE strategy_id = ?
                ''', (strategy_id,))
                time_range = cursor.fetchone()
                
                return {
                    'total_operations': total_operations,
                    'operation_counts': operation_counts,
                    'first_operation': time_range[0] if time_range[0] else None,
                    'last_operation': time_range[1] if time_range[1] else None
                }
                
        except Exception as e:
            print(f"❌ 获取操作摘要失败: {e}")
            return {
                'total_operations': 0,
                'operation_counts': {},
                'first_operation': None,
                'last_operation': None
            }

def main():
    """测试数据库功能"""
    db = GridTradingDatabase()
    print("✅ 数据库初始化完成")

if __name__ == "__main__":
    main() 