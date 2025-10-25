import sqlite3

# 检查股票数据库结构
print('=== 股票数据库结构 ===')
conn = sqlite3.connect('gupiao_baostock/sh.600030_data.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('数据库中的表:', tables)

if tables:
    table_name = tables[0][0]
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = cursor.fetchall()
    print(f'表 {table_name} 结构:')
    for col in columns:
        print(f'  {col[1]} ({col[2]})')
    
    # 检查数据样本
    cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
    sample_data = cursor.fetchall()
    print(f'数据样本:')
    for row in sample_data:
        print(f'  {row}')

conn.close()

print()

# 检查加密货币数据库结构
print('=== 比特币数据库结构 ===')
conn = sqlite3.connect('btc_data.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(btc_daily)')
columns = cursor.fetchall()
print('比特币表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 检查数据样本
cursor.execute('SELECT * FROM btc_daily LIMIT 3')
sample_data = cursor.fetchall()
print('数据样本:')
for row in sample_data:
    print(f'  {row}')

conn.close()

print()

print('=== 以太坊数据库结构 ===')
conn = sqlite3.connect('eth_data.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(eth_daily)')
columns = cursor.fetchall()
print('以太坊表结构:')
for col in columns:
    print(f'  {col[1]} ({col[2]})')

# 检查数据样本
cursor.execute('SELECT * FROM eth_daily LIMIT 3')
sample_data = cursor.fetchall()
print('数据样本:')
for row in sample_data:
    print(f'  {row}')

conn.close()
