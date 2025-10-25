#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清理本地SQLite原始表 temp_hsi_realtime 的非交易时段数据。

用法示例：
  python clean_local_realtime_non_trading.py --db hsi_realtime_temp.db --recent-days 9999 --yes

参数说明：
  --db            SQLite文件路径，默认: hsi_realtime_temp.db
  --recent-days   仅清理最近N天（含今天），默认: 全量
  --yes           无交互确认，直接执行删除
"""

import argparse
import sqlite3
from datetime import datetime, timedelta


def is_hsi_trading_time(dt: datetime) -> bool:
    """恒指期货交易时间（香港时间/本地时间按UTC+8理解）。"""
    hour = dt.hour
    minute = dt.minute

    if hour == 9 and minute >= 15:
        return True
    if hour in [10, 11]:
        return True
    if hour == 12 and minute == 0:
        return True

    if hour in [13, 14, 15]:
        return True
    if hour == 16 and minute <= 30:
        return True

    if hour == 17 and minute >= 15:
        return True
    if hour in [18, 19, 20, 21, 22, 23]:
        return True
    if hour in [0, 1, 2]:
        return True
    if hour == 3 and minute == 0:
        return True

    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--db', default='hsi_realtime_temp.db')
    parser.add_argument('--recent-days', type=int, default=None)
    parser.add_argument('--yes', action='store_true')
    args = parser.parse_args()

    db_path = args.db
    since_clause = ''
    params = []
    if args.recent_days is not None:
        since_dt = datetime.now() - timedelta(days=args.recent_days)
        since_str = since_dt.strftime('%Y-%m-%d %H:%M:%S')
        since_clause = 'WHERE datetime >= ?'
        params.append(since_str)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # 基本情况
    cur.execute('SELECT COUNT(*) FROM temp_hsi_realtime')
    total = cur.fetchone()[0]
    print(f'本地原始表总记录数: {total}')

    # 取候选集合
    sql_select = f"""
        SELECT datetime FROM temp_hsi_realtime
        {since_clause}
        ORDER BY datetime ASC
    """
    cur.execute(sql_select, params)
    rows = cur.fetchall()
    print(f'候选记录数: {len(rows)} (recent_days={args.recent_days})')

    # 计算需删除集合（非交易时段）
    to_delete = []
    for (dt_str,) in rows:
        try:
            dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')
        except Exception:
            # 无法解析的时间，视为需删除
            to_delete.append(dt_str)
            continue
        if not is_hsi_trading_time(dt):
            to_delete.append(dt_str)

    print(f'非交易时段记录数（将删除）: {len(to_delete)}')

    if not to_delete:
        print('无需要删除的记录。')
        conn.close()
        return

    if not args.yes:
        confirm = input('确认删除以上记录? (y/N): ').strip().lower()
        if confirm != 'y':
            print('取消删除。')
            conn.close()
            return

    # 分批删除
    batch_size = 5000
    deleted = 0
    for i in range(0, len(to_delete), batch_size):
        batch = to_delete[i:i+batch_size]
        placeholders = ','.join(['?'] * len(batch))
        del_sql = f"DELETE FROM temp_hsi_realtime WHERE datetime IN ({placeholders})"
        cur.execute(del_sql, batch)
        deleted += cur.rowcount
        conn.commit()
        print(f'已删除: {deleted}/{len(to_delete)}')

    # 结果
    cur.execute('SELECT COUNT(*) FROM temp_hsi_realtime')
    remain = cur.fetchone()[0]
    print(f'删除完成。剩余记录数: {remain}')

    conn.close()


if __name__ == '__main__':
    main()



