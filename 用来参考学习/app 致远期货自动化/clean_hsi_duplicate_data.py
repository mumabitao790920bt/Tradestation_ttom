#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
恒指期货数据清洗脚本
功能：清理恒指期货表中OHLC完全相同的重复K线数据（横线K线）
"""

import os
import pymysql
import pandas as pd
from datetime import datetime, timedelta
import sys

# 远程数据库配置
MYSQL_CONFIG = {
    'host': '115.159.44.226',
    'port': 3306,
    'user': 'qihuo',
    'password': 'Hejdf3KdfaTt4h3w',
    'database': 'qihuo',
    'charset': 'utf8mb4',
    'autocommit': False
}

def is_duplicate_kline(row):
    """判断K线是否为横线（OHLC完全相同）"""
    try:
        open_price = float(row['open'])
        high_price = float(row['high'])
        low_price = float(row['low'])
        close_price = float(row['close'])
        
        # 如果OHLC完全相同，则为横线K线
        return (open_price == high_price == low_price == close_price)
    except (ValueError, TypeError):
        return False

def clean_table_duplicate_data(table_name, recent_days=1, batch_size=5000, recent_rows=None):
    """清洗单个表的重复数据
    - recent_days: 仅按天数窗口清理（与recent_rows二选一）
    - recent_rows: 若给定，则改为仅读取最近N行(ORDER BY datetime DESC LIMIT N)
    """
    mode_desc = f"最近{recent_days}天" if not recent_rows else f"最近{recent_rows}行"
    print(f"\n开始清洗表: {table_name}  | {mode_desc} | 批大小={batch_size}")
    
    try:
        # 连接数据库
        conn = pymysql.connect(**MYSQL_CONFIG)
        # 先用缓冲游标做COUNT，避免与流式结果冲突
        count_cur = conn.cursor()
        
        # 查询表是否存在（使用独立缓冲游标）
        tb_cur = conn.cursor()
        tb_cur.execute(f"SHOW TABLES LIKE '{table_name}'")
        if not tb_cur.fetchone():
            print(f"表 {table_name} 不存在，跳过")
            return 0
        tb_cur.close()
        
        # 统计数据量
        if recent_rows:
            # 在recent_rows模式下，不再做COUNT+ORDER BY全表排序，直接拉取LIMIT行再计算总数
            print(f"跳过COUNT，直接读取最近{recent_rows}行...")
        else:
            print(f"准备统计最近{recent_days}天数据量...")
            count_cur.execute(
                f"SELECT COUNT(*) FROM {table_name} WHERE datetime >= NOW() - INTERVAL %s DAY",
                (recent_days,)
            )
        if not recent_rows:
            total_count = count_cur.fetchone()[0]
            print(f"表 {table_name} {mode_desc} 数据量: {total_count}")
        count_cur.close()
        
        # 查询最近N天的有序数据
        print("开始查询数据（按时间升序）...")
        if recent_rows:
            # 简单路径：直接取最近N行后再升序
            simple_cur = conn.cursor()
            simple_cur.execute(
                f"SELECT datetime, open, high, low, close, volume FROM {table_name} ORDER BY datetime DESC LIMIT %s",
                (recent_rows,)
            )
            rows_desc = simple_cur.fetchall()
            simple_cur.close()
            # 转为升序
            rows = list(reversed(rows_desc))
            total_count = len(rows)
        else:
            # 使用流式游标读取天数窗口
            stream_cur = conn.cursor(pymysql.cursors.SSCursor)
            stream_cur.execute(
                f"""
                SELECT datetime, open, high, low, close, volume 
                FROM {table_name} 
                WHERE datetime >= NOW() - INTERVAL %s DAY
                ORDER BY datetime
                """,
                (recent_days,)
            )
            rows = []
            fetch_batch = 10000
            fetched_total = 0
            while True:
                batch = stream_cur.fetchmany(fetch_batch)
                if not batch:
                    break
                rows.extend(batch)
                fetched_total += len(batch)
                print(f"已读取 {fetched_total}/{total_count} 条...")
            stream_cur.close()
        columns = ['datetime', 'open', 'high', 'low', 'close', 'volume']
        df = pd.DataFrame(rows, columns=columns)
        if df.empty:
            print(f"{mode_desc} 无数据，跳过 {table_name}")
            conn.close()
            return 0
        
        print(f"查询到 {len(df)} 条数据（{mode_desc}）")
        
        # 找出横线K线（OHLC完全相同），并只删除“与前一条OHLC完全一致”的后续重复，保留每段首条
        duplicate_mask = df.apply(is_duplicate_kline, axis=1)
        df_dup = df[duplicate_mask].copy()
        prev_key = None
        prev_dt = None
        to_delete_datetimes = []
        dup_examples = []  # 保存将被删除的真实重复样本
        for _, row in df_dup.iterrows():
            cur_key = (row['open'], row['high'], row['low'], row['close'])
            cur_dt = row['datetime']
            if prev_key is not None and cur_key == prev_key:
                to_delete_datetimes.append(cur_dt)
                if len(dup_examples) < 10:
                    dup_examples.append({
                        'datetime': cur_dt,
                        'prev_datetime': prev_dt,
                        'open': row['open'],
                        'high': row['high'],
                        'low': row['low'],
                        'close': row['close']
                    })
            prev_key = cur_key
            prev_dt = cur_dt

        duplicate_count = len(to_delete_datetimes)
        print(f"发现 {duplicate_count} 条可删除的连续横线K线（保留每段首条）")
        
        if duplicate_count == 0:
            print(f"表 {table_name} 无重复数据，无需清洗")
            return 0
        
        # 显示将被删除的真实连续重复样例（不是候选）
        print(f"\n将被删除的连续重复样例（前5条）:")
        for ex in dup_examples[:5]:
            print(f"  {ex['datetime']} (前一条: {ex['prev_datetime']}): O={ex['open']}, H={ex['high']}, L={ex['low']}, C={ex['close']}")
        
        # 确认是否删除
        auto_confirm = os.environ.get('AUTO_CONFIRM', '') == '1'
        if not auto_confirm:
            confirm = input(f"\n确认删除表 {table_name} 中的 {duplicate_count} 条重复数据？(y/N): ")
            if confirm.lower() != 'y':
                print("取消删除操作")
                return 0
        else:
            print("AUTO_CONFIRM=1 已设置，自动确认删除。")
        
        # 删除重复数据
        # 分批删除，避免长事务与SQL过长
        deleted_count = 0
        del_cur = conn.cursor()
        for i in range(0, len(to_delete_datetimes), batch_size):
            batch_datetimes = to_delete_datetimes[i:i+batch_size]
            datetime_strs = ",".join(["%s"] * len(batch_datetimes))
            delete_sql = f"DELETE FROM {table_name} WHERE datetime IN ({datetime_strs})"
            del_cur.execute(delete_sql, batch_datetimes)
            deleted_count += del_cur.rowcount
            conn.commit()
            print(f"已删除 {deleted_count}/{duplicate_count} 条...")
        del_cur.close()
        
        print(f"成功删除 {deleted_count} 条重复数据")
        
        # 验证删除结果
        verify_cur = conn.cursor()
        verify_cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        remaining_count = verify_cur.fetchone()[0]
        verify_cur.close()
        print(f"删除后剩余数据量: {remaining_count}")
        
        conn.close()
        return deleted_count
        
    except Exception as e:
        print(f"清洗表 {table_name} 时出错: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return 0

def main():
    """主函数"""
    print("=" * 60)
    print("恒指期货数据清洗脚本")
    print("=" * 60)
    print(f"开始时间: {datetime.now()}")
    
    # 恒指期货相关表名
    hsi_tables = [
        'hf_HSI_min1',   # 1分钟数据
        'hf_HSI_min3',   # 3分钟数据
        'hf_HSI_min5',   # 5分钟数据
        'hf_HSI_min10',  # 10分钟数据
        'hf_HSI_min15',  # 15分钟数据
        'hf_HSI_min30',  # 30分钟数据
    ]
    
    total_deleted = 0
    
    for table_name in hsi_tables:
        # 快速测试：仅读取最近100行，验证读取与识别逻辑是否正常
        deleted_count = clean_table_duplicate_data(table_name, recent_rows=4000)
        total_deleted += deleted_count
    
    print("\n" + "=" * 60)
    print("清洗完成!")
    print(f"总共删除重复数据: {total_deleted} 条")
    print(f"结束时间: {datetime.now()}")
    print("=" * 60)

if __name__ == "__main__":
    main()

