import sqlite3
import pandas as pd
import os
from MyTT import *
import numpy as np
# import talib

# 从原文件移植数据处理相关函数
def create_3min_candles(contract_name, zhumulu_folder):
    # Connect to the SQLite database
    db_path = os.path.join(zhumulu_folder, f'{contract_name}_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if the min_10 table exists, create it if it does not
    c.execute('''CREATE TABLE IF NOT EXISTS min_data3 (
                    time DATETIME,
                    high FLOAT,
                    low FLOAT,
                    open FLOAT,
                    close FLOAT,
                    vol FLOAT,
                    code TEXT,
                    PRIMARY KEY (time, code)
                )''')
    # Define the SQL query to synthesize 20-minute candlestick data
    sql_query = """
    SELECT 
        datetime((strftime('%s', time) / 180) * 180, 'unixepoch') AS time,
        MAX(high) AS high,
        MIN(low) AS low,
        (SELECT open FROM min_data1 m2 WHERE m2.code = m1.code AND m2.time <= m1.time ORDER BY time DESC LIMIT 1) AS open,
        (SELECT close FROM min_data1 m3 WHERE m3.code = m1.code AND m3.time >= m1.time ORDER BY time ASC LIMIT 1) AS close,
        SUM(vol) AS vol,
        code
    FROM min_data1 m1
    GROUP BY datetime((strftime('%s', time) / 180) * 180, 'unixepoch'), code
    """
    # Read data into a DataFrame
    df = pd.read_sql_query(sql_query, conn)
    # Insert data into min_20 table with filtering
    df.to_sql('min_data3', conn, if_exists='replace', index=False)  # Remove method='multi' and chunksize=1000
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
def create_20min_candles(contract_name, zhumulu_folder):
    # Connect to the SQLite database
    db_path = os.path.join(zhumulu_folder, f'{contract_name}_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if the min_10 table exists, create it if it does not
    c.execute('''CREATE TABLE IF NOT EXISTS min_data20 (
                    time DATETIME,
                    high FLOAT,
                    low FLOAT,
                    open FLOAT,
                    close FLOAT,
                    vol FLOAT,
                    code TEXT,
                    PRIMARY KEY (time, code)
                )''')
    # Define the SQL query to synthesize 20-minute candlestick data
    sql_query = """
    SELECT 
        datetime((strftime('%s', time) / 1200) * 1200, 'unixepoch') AS time,
        MAX(high) AS high,
        MIN(low) AS low,
        (SELECT open FROM min_data1 m2 WHERE m2.code = m1.code AND m2.time <= m1.time ORDER BY time DESC LIMIT 1) AS open,
        (SELECT close FROM min_data1 m3 WHERE m3.code = m1.code AND m3.time >= m1.time ORDER BY time ASC LIMIT 1) AS close,
        SUM(vol) AS vol,
        code
    FROM min_data1 m1
    GROUP BY datetime((strftime('%s', time) / 1200) * 1200, 'unixepoch'), code
    """
    # Read data into a DataFrame
    df = pd.read_sql_query(sql_query, conn)
    # Insert data into min_20 table with filtering
    df.to_sql('min_data20', conn, if_exists='replace', index=False)  # Remove method='multi' and chunksize=1000
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
def create_10min_candles(contract_name, zhumulu_folder):
    # Connect to the SQLite database
    db_path = os.path.join(zhumulu_folder, f'{contract_name}_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if the min_10 table exists, create it if it does not
    c.execute('''CREATE TABLE IF NOT EXISTS min_data10 (
                    time DATETIME,
                    high FLOAT,
                    low FLOAT,
                    open FLOAT,
                    close FLOAT,
                    vol FLOAT,
                    code TEXT,
                    PRIMARY KEY (time, code)
                )''')
    # Define the SQL query to synthesize 10-minute candlestick data
    sql_query = """
    SELECT 
        datetime((strftime('%s', time) / 600) * 600, 'unixepoch') AS time,
        MAX(high) AS high,
        MIN(low) AS low,
        (SELECT open FROM min_data1 m2 WHERE m2.code = m1.code AND m2.time <= m1.time ORDER BY time DESC LIMIT 1) AS open,
        (SELECT close FROM min_data1 m3 WHERE m3.code = m1.code AND m3.time >= m1.time ORDER BY time ASC LIMIT 1) AS close,
        SUM(vol) AS vol,
        code
    FROM min_data1 m1
    GROUP BY datetime((strftime('%s', time) / 600) * 600, 'unixepoch'), code
    """
    # Read data into a DataFrame
    df = pd.read_sql_query(sql_query, conn)
    # Insert data into min_10 table with filtering
    df.to_sql('min_data10', conn, if_exists='replace', index=False)  # Remove method='multi' and chunksize=1000
    # Commit the changes and close the connection
    conn.commit()
    conn.close()
def create_5min_candles(contract_name, zhumulu_folder):
    # Connect to the SQLite database
    db_path = os.path.join(zhumulu_folder, f'{contract_name}_data.db')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # Check if the min_5 table exists, create it if it does not
    c.execute('''CREATE TABLE IF NOT EXISTS min_data5 (
                    time DATETIME,
                    high FLOAT,
                    low FLOAT,
                    open FLOAT,
                    close FLOAT,
                    vol FLOAT,
                    code TEXT,
                    PRIMARY KEY (time, code)
                )''')

    # Define the SQL query to synthesize 5-minute candlestick data
    sql_query = """
    SELECT 
        datetime((strftime('%s', time) / 300) * 300, 'unixepoch') AS time,
        MAX(high) AS high,
        MIN(low) AS low,
        (SELECT open FROM min_data1 m2 WHERE m2.code = m1.code AND m2.time <= m1.time ORDER BY time DESC LIMIT 1) AS open,
        (SELECT close FROM min_data1 m3 WHERE m3.code = m1.code AND m3.time >= m1.time ORDER BY time ASC LIMIT 1) AS close,
        SUM(vol) AS vol,
        code
    FROM min_data1 m1
    GROUP BY datetime((strftime('%s', time) / 300) * 300, 'unixepoch'), code
    """

    # Read data into a DataFrame
    df = pd.read_sql_query(sql_query, conn)

    # Insert data into min_5 table with filtering
    df.to_sql('min_data5', conn, if_exists='replace', index=False)  # Remove method='multi' and chunksize=1000

    # Commit the changes and close the connection
    conn.commit()
    conn.close()
def tgdz789(df,sjbs,ns):
    最高价_x = df['high'].astype(float)
    最低价_x = df['low'].astype(float)
    开盘价_x = df['open'].astype(float)
    收盘价_x = df['close'].astype(float)
    成交量_x = df['vol'].astype(float)


    bt成交量 = 成交量_x
    bt最高价 = 最高价_x
    bt最低价 = 最低价_x
    bt开盘价 = 开盘价_x
    bt收盘价 = 收盘价_x
    空标0_a_tj1 = IF(bt最高价 > REF(bt最高价, 2 * sjbs), 1, 0)
    空标0_a_tj2 = IF(bt最高价 > REF(bt最高价, 1 * sjbs), 1, 0)
    空标0_a = IF(空标0_a_tj1 + 空标0_a_tj2 == 2, 1, 0)

    空标0_b = IF(bt最低价 > REF(bt最低价, 1 * sjbs), 1, 0)
    空标0 = IF(空标0_a + 空标0_b == 2, 1, 0)
    空标0wz = MY_BARSLAST(空标0, 1)

    空标5_a_tj1 = IF(bt最低价 < REF(bt最低价, 2 * sjbs), 1, 0)
    空标5_a_tj2 = IF(bt最低价 < REF(bt最低价, 1 * sjbs), 1, 0)
    空标5_a = IF(空标5_a_tj1 + 空标5_a_tj2 == 2, 1, 0)
    空标5_b = IF(bt最高价 < REF(bt最高价, 1 * sjbs), 1, 0)
    空标5 = IF(空标5_a + 空标5_b == 2, 1, 0)

    空标6zb1 = IF(bt收盘价 <= REF(bt收盘价, 1 * sjbs), 1, 0)
    空标6zb2_tj1 = IF(bt最高价 < REF(bt最高价, 1 * sjbs), 1, 0)
    空标6zb2_tj2 = IF(bt最低价 <= REF(bt最低价, 1 * sjbs), 1, 0)
    空标6zb2 = IF(空标6zb2_tj1 + 空标6zb2_tj2 == 2, 1, 0)
    空标6zb = IF(空标6zb1 + 空标6zb2 >= 1, 1, 0)
    空标6_tj1 = IF(REF(空标5, 1 * sjbs) == 1, 1, 0)
    空标6_tj2 = IF(空标6zb == 1, 1, 0)
    空标6 = IF(空标6_tj1 + 空标6_tj2 == 2, 1, 0)
    空标6_wy_tj = IF(REF(空标6, 1 * sjbs) != 1, 1, 0)
    空标6_wy = IF(空标6 + 空标6_wy_tj == 2, 1, 0)

    空标7 = IF(REF(空标6, 1 * sjbs), 1, 0)
    空标7_wy_tj = IF(REF(空标7, 1 * sjbs) != 1, 1, 0)
    空标7_wy = IF(空标7 + 空标7_wy_tj == 2, 1, 0)

    空标8 = IF(REF(空标7, 1 * sjbs), 1, 0)
    空标8_wy_tj = IF(REF(空标8, 1 * sjbs) != 1, 1, 0)
    空标8_wy = IF(空标8 + 空标8_wy_tj == 2, 1, 0)

    空标9 = IF(REF(空标8, 1 * sjbs), 1, 0)
    空标9_wy_tj = IF(REF(空标9, 1 * sjbs) != 1, 1, 0)
    空标9_wy = IF(空标9 + 空标9_wy_tj == 2, 1, 0)

    标0_a_tj1 = IF(bt最低价 < REF(bt最低价, 2 * sjbs), 1, 0)
    标0_a_tj2 = IF(bt最低价 < REF(bt最低价, 1 * sjbs), 1, 0)
    标0_a = IF(标0_a_tj1 + 标0_a_tj2 == 2, 1, 0)

    标0_b = IF(bt最高价 < REF(bt最高价, 1 * sjbs), 1, 0)
    标0 = IF(标0_a + 标0_b == 2, 1, 0)
    标0wz = MY_BARSLAST(标0, 1 * sjbs)

    标5_a_tj1 = IF(bt最高价 > REF(bt最高价, 2 * sjbs), 1, 0)
    标5_a_tj2 = IF(bt最高价 > REF(bt最高价, 1 * sjbs), 1, 0)
    标5_a = IF(标5_a_tj1 + 标5_a_tj2 == 2, 1, 0)
    标5_b = IF(bt最低价 > REF(bt最低价, 1 * sjbs), 1, 0)
    标5 = IF(标5_a + 标5_b == 2, 1, 0)

    标6zb1 = IF(bt收盘价 >= REF(bt收盘价, 1 * sjbs), 1, 0)
    标6zb2_tj1 = IF(bt最高价 > REF(bt最高价, 1 * sjbs), 1, 0)
    标6zb2_tj2 = IF(bt最低价 >= REF(bt最低价, 1 * sjbs), 1, 0)
    标6zb2 = IF(标6zb2_tj1 + 标6zb2_tj2 == 2, 1, 0)
    标6zb = IF(标6zb1 + 标6zb2 >= 1, 1, 0)
    标6_tj1 = IF(REF(标5, 1 * sjbs) == 1, 1, 0)
    标6_tj2 = IF(标6zb == 1, 1, 0)
    标6 = IF(标6_tj1 + 标6_tj2 == 2, 1, 0)
    标6_wy_tj = IF(REF(标6, 1 * sjbs) != 1, 1, 0)
    标6_wy = IF(标6 + 标6_wy_tj == 2, 1, 0)

    标7 = IF(REF(标6, 1 * sjbs), 1, 0)
    标7_wy_tj = IF(REF(标7, 1 * sjbs) != 1, 1, 0)
    标7_wy = IF(标7 + 标7_wy_tj == 2, 1, 0)

    标8 = IF(REF(标7, 1 * sjbs), 1, 0)
    标8_wy_tj = IF(REF(标8, 1 * sjbs) != 1, 1, 0)
    标8_wy = IF(标8 + 标8_wy_tj == 2, 1, 0)

    标9 = IF(REF(标8, 1 * sjbs), 1, 0)
    标9_wy_tj = IF(REF(标9, 1 * sjbs) != 1, 1, 0)
    标9_wy = IF(标9 + 标9_wy_tj == 2, 1, 0)
    df['标6_wy']=标6_wy
    df['标7_wy'] = 标7_wy
    df['标9_wy'] = 标9_wy
    df['空标6_wy'] = 空标6_wy
    df['空标7_wy'] = 空标7_wy
    df['空标9_wy'] = 空标9_wy


    return df,标6_wy,标7_wy,标9_wy,空标6_wy,空标7_wy,空标9_wy
def gaopao_dixi4(df):
    sqsz_9_zdsz = df['close']
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) == 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL != 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) == 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL != 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr

    sqszzh_sell_jiedian = IF(sqsz_9_gaopao == 1, 1, 0)
    sqszzh_buy_jiedian = IF(sqsz_9_dixi == 1, 1, 0)
    return df, sqszzh_sell_jiedian, sqszzh_buy_jiedian
def zdmrmc_cha(df,sjbs,ns):
    # 镜
    最高价_x = df['high'].astype(float)
    最低价_x = df['low'].astype(float)
    开盘价_x = df['open'].astype(float)
    收盘价_x = df['close'].astype(float)
    成交量_x = df['vol'].astype(float)

    # bt成交量 = SUM(成交量_x,sjbs)
    # bt最高价 = HHV(最高价_x,sjbs)
    # bt最低价 = LLV(最低价_x,sjbs)
    # bt开盘价 = REF(开盘价_x,sjbs)
    # bt收盘价 = 收盘价_x

    bt成交量 = 成交量_x
    bt最高价 = 最高价_x
    bt最低价 = 最低价_x
    bt开盘价 = 开盘价_x
    bt收盘价 = 收盘价_x
    空标0_a_tj1=IF(bt最高价>REF(bt最高价,2*sjbs),1,0)
    空标0_a_tj2 = IF(bt最高价 > REF(bt最高价, 1*sjbs),1,0)
    空标0_a = IF(空标0_a_tj1+空标0_a_tj2==2,1,0)

    空标0_b = IF(bt最低价 > REF(bt最低价, 1*sjbs),1,0)
    空标0 = IF(空标0_a+空标0_b==2,1,0)
    空标0wz = MY_BARSLAST(空标0, 1)

    空标5_a_tj1=IF(bt最低价 < REF(bt最低价, 2*sjbs),1,0)
    空标5_a_tj2=IF(bt最低价 < REF(bt最低价, 1*sjbs),1,0)
    空标5_a =IF(空标5_a_tj1+空标5_a_tj2==2,1,0)
    空标5_b = IF(bt最高价 < REF(bt最高价, 1*sjbs),1,0)
    空标5 = IF(空标5_a+空标5_b==2,1,0)


    空标6zb1 = IF(bt收盘价 <= REF(bt收盘价, 1*sjbs),1,0)
    空标6zb2_tj1=IF(bt最高价 < REF(bt最高价, 1*sjbs),1,0)
    空标6zb2_tj2=IF(bt最低价 <= REF(bt最低价, 1*sjbs), 1, 0)
    空标6zb2 =IF(空标6zb2_tj1+空标6zb2_tj2==2,1,0)
    空标6zb = IF(空标6zb1 +空标6zb2>=1,1,0)
    空标6_tj1=IF( REF(空标5, 1*sjbs)==1,1,0)
    空标6_tj2 = IF(空标6zb == 1, 1, 0)
    空标6 =IF(空标6_tj1+空标6_tj2==2,1,0)
    空标6_wy_tj=IF(REF(空标6, 1*sjbs) != 1,1,0)
    空标6_wy = IF(空标6+ 空标6_wy_tj==2,1,0)

    空标7 = IF(REF(空标6, 1*sjbs),1,0)
    空标7_wy_tj=IF(REF(空标7, 1*sjbs) !=1,1,0)
    空标7_wy = IF(空标7+空标7_wy_tj==2,1,0)

    空标8 = IF(REF(空标7, 1*sjbs),1,0)
    空标8_wy_tj=IF(REF(空标8, 1*sjbs)!=1,1,0)
    空标8_wy = IF(空标8+空标8_wy_tj==2,1,0)

    空标9 = IF(REF(空标8, 1*sjbs),1,0)
    空标9_wy_tj=IF(REF(空标9, 1*sjbs)!= 1,1,0)
    空标9_wy = IF(空标9 +空标9_wy_tj==2,1,0)

    标0_a_tj1 = IF(bt最低价 < REF(bt最低价, 2*sjbs), 1, 0)
    标0_a_tj2 = IF(bt最低价 < REF(bt最低价, 1*sjbs), 1, 0)
    标0_a = IF(标0_a_tj1 + 标0_a_tj2 == 2, 1, 0)

    标0_b = IF(bt最高价 < REF(bt最高价, 1*sjbs), 1, 0)
    标0 = IF(标0_a + 标0_b == 2, 1, 0)
    标0wz = MY_BARSLAST(标0, 1*sjbs)

    标5_a_tj1 = IF(bt最高价 > REF(bt最高价, 2*sjbs), 1, 0)
    标5_a_tj2 = IF(bt最高价 > REF(bt最高价, 1*sjbs), 1, 0)
    标5_a = IF(标5_a_tj1 + 标5_a_tj2 == 2, 1, 0)
    标5_b = IF(bt最低价 > REF(bt最低价, 1*sjbs), 1, 0)
    标5 = IF(标5_a + 标5_b == 2, 1, 0)

    标6zb1 = IF(bt收盘价 >= REF(bt收盘价, 1*sjbs), 1, 0)
    标6zb2_tj1 = IF(bt最高价 > REF(bt最高价, 1*sjbs), 1, 0)
    标6zb2_tj2 = IF(bt最低价 >= REF(bt最低价, 1*sjbs), 1, 0)
    标6zb2 = IF(标6zb2_tj1 + 标6zb2_tj2 == 2, 1, 0)
    标6zb = IF(标6zb1 + 标6zb2 >= 1, 1, 0)
    标6_tj1 = IF(REF(标5, 1*sjbs) == 1, 1, 0)
    标6_tj2 = IF(标6zb == 1, 1, 0)
    标6 = IF(标6_tj1 + 标6_tj2 == 2, 1, 0)
    标6_wy_tj = IF(REF(标6, 1*sjbs) != 1, 1, 0)
    标6_wy = IF(标6 + 标6_wy_tj == 2, 1, 0)

    标7 = IF(REF(标6, 1*sjbs), 1, 0)
    标7_wy_tj = IF(REF(标7, 1*sjbs) != 1, 1, 0)
    标7_wy = IF(标7 + 标7_wy_tj == 2, 1, 0)

    标8 = IF(REF(标7, 1*sjbs), 1, 0)
    标8_wy_tj = IF(REF(标8, 1*sjbs) != 1, 1, 0)
    标8_wy = IF(标8 + 标8_wy_tj == 2, 1, 0)

    标9 = IF(REF(标8, 1*sjbs), 1, 0)
    标9_wy_tj = IF(REF(标9, 1*sjbs) != 1, 1, 0)
    标9_wy = IF(标9 + 标9_wy_tj == 2, 1, 0)


    # 片
    pian_high = bt最高价
    pian_low = bt最低价
    pian_close = bt收盘价
    pian_open = bt开盘价
    pian_vol = bt成交量
    pian_bs = sjbs*ns

    # 在 pian_VAR1 的计算中加入1e-8在计算 pian_VAR1 之前对分母进行判断，如果为零则将分母赋值为一个极小值（例如  1e-8 ），避免除数为零的情况。
    pian_VAR1 = pian_vol / ((pian_high - pian_low) * 2 - ABS(pian_close - pian_open))
    pian_zhubuy_zb = IF(pian_close>pian_open,pian_VAR1*(pian_high-pian_low),IF(pian_close<pian_open,pian_VAR1*((pian_high-pian_open)+(pian_close-pian_low)),pian_vol/2))
    # pian_zhubuy_zb = IF(np.isnan(pian_VAR1), 0, IF(pian_close > pian_open, pian_VAR1 * (pian_high - pian_low),
    #                                             IF(pian_close < pian_open,
    #                                                pian_VAR1 * ((pian_high - pian_open) + (pian_close - pian_low)),
    #                                                pian_vol / 2)))
    pian_zhusell_zb=IF(pian_close>pian_open,0-pian_VAR1*((pian_high-pian_close)+(pian_open-pian_low)),IF(pian_close<pian_open,0-pian_VAR1*(pian_high-pian_low),0-pian_vol/2))
    # pian_zhusell_zb = IF(np.isnan(pian_VAR1), 0,
    #                   IF(pian_close > pian_open, 0 - pian_VAR1 * ((pian_high - pian_close) + (pian_open - pian_low)),
    #                      IF(pian_close < pian_open, 0 - pian_VAR1 * (pian_high - pian_low), 0 - pian_vol / 2)))

    卖增条件 = IF(标7_wy + 空标6_wy + 标9_wy>=1,1,0)
    买增条件 =IF( 空标7_wy + 标6_wy + 空标9_wy>=1,1,0)
    pian_zhusell = IF(卖增条件==1, pian_zhusell_zb * 1.5, pian_zhusell_zb)
    pian_zhubuy = IF(买增条件==1, pian_zhubuy_zb * 1.5, pian_zhubuy_zb)

    pian_zhubuy_15 = SUM(ABS(pian_zhubuy), 1* pian_bs)
    pian_zhusell_15 = SUM(ABS(pian_zhusell), 1* pian_bs)
    pian_zhubuy_20 = SUM(ABS(pian_zhubuy), 2 * pian_bs)
    pian_zhusell_20 = SUM(ABS(pian_zhusell), 2 * pian_bs)
    pian_zhubuy_40 = SUM(ABS(pian_zhubuy), 4 * pian_bs)
    pian_zhusell_40 = SUM(ABS(pian_zhusell), 4 * pian_bs)
    pian_zhubuy_80 = SUM(ABS(pian_zhubuy), 8 * pian_bs)
    pian_zhusell_80 = SUM(ABS(pian_zhusell), 8 * pian_bs)
    pian_zhubuy_100 = SUM(ABS(pian_zhubuy), 15 * pian_bs)
    pian_zhusell_100 = SUM(ABS(pian_zhusell), 15 * pian_bs)
    pian_zhubuy_120 = SUM(ABS(pian_zhubuy), 6 * pian_bs)
    pian_zhusell_120 = SUM(ABS(pian_zhusell),  6* pian_bs)
    pian_zhubuy_140 = SUM(ABS(pian_zhubuy), 9 * pian_bs)
    pian_zhusell_140 = SUM(ABS(pian_zhusell), 9 * pian_bs)
    pian_zhubuy_160 = SUM(ABS(pian_zhubuy), 20 * pian_bs)
    pian_zhusell_160 = SUM(ABS(pian_zhusell), 20 * pian_bs)
    pian_zhubuy_180 = SUM(ABS(pian_zhubuy), 10 * pian_bs)
    pian_zhusell_180 = SUM(ABS(pian_zhusell), 10 * pian_bs)

    pian_zhubuy_HJ = (
                             pian_zhubuy_15 + pian_zhubuy_20 + pian_zhubuy_40 + pian_zhubuy_80 + pian_zhubuy_100 + pian_zhubuy_120 + pian_zhubuy_140 + pian_zhubuy_160 + pian_zhubuy_180) / 9
    pian_zhusel_HJ = (
                             pian_zhusell_15 + pian_zhusell_20 + pian_zhusell_40 + pian_zhusell_80 + pian_zhusell_100 + pian_zhusell_120 + pian_zhusell_140 + pian_zhusell_160 + pian_zhusell_180) / 9
    pian_zhudong_cha = (pian_zhubuy_HJ - pian_zhusel_HJ)  # 粉小英线大中粉小主动差

    # 主动买入hh = MA(pian_zhubuy_HJ, 10*sjbs)
    # 主动卖出hh = MA(pian_zhusel_HJ, 10*sjbs)
    主动买入hh =pian_zhubuy_HJ
    主动卖出hh = pian_zhusel_HJ
    差多 = 主动买入hh > 主动卖出hh
    差空 = 主动买入hh < 主动卖出hh
    return df,主动买入hh,主动卖出hh,差多,差空
def MYHHV(s, n):
    hhv_result = []
    for i in range(len(s)):
        if i - n[i] >= 0 and i - n[i] < i + 1:
            max_value = np.max(s[i - n[i]:i + 1])
        else:
            max_value = np.max(s[0:i + 1])
        hhv_result.append(max_value)
    return np.array(hhv_result)


def MYLLV(s, n):
    llv_result = []
    for i in range(len(s)):
        if i - n[i] >= 0 and i - n[i] < i + 1:
            min_value = np.min(s[i - n[i]:i + 1])
        else:
            min_value = np.min(s[0:i + 1])
        llv_result.append(min_value)
    return np.array(llv_result)


def MY_BARSLAST(conditions, n):
    res = []  # 保存每根K线的timesswz2的列表
    for i in range(len(conditions)):
        last_occurrence = np.where(conditions[:i + 1] == 1)[0]
        if len(last_occurrence) < n:  # 不存在1
            res.append(0)  # 将timesswz2赋值为0代表不成立
        else:

            last_occurrence = last_occurrence[-1 * n]  # 获取最后一个1的位置
            ts = len(conditions[last_occurrence:i + 1]) - 1  # 从最后一个1的位置到当前位置的周期数
            res.append(ts)
    return np.array(res)


# 上穿
def bt_crossover(ma1, ma2):
    ma1 = np.array(ma1).astype(float)
    ma2 = np.array(ma2).astype(float)
    result = np.zeros_like(ma1)
    for i in range(1, len(ma1)):
        if ma1[i - 1] < ma2[i - 1] and ma1[i] >= ma2[i]:
            result[i] = 1
    return result


# 下穿
def bt_crossunder(ma1, ma2):
    ma1 = np.array(ma1).astype(float)
    ma2 = np.array(ma2).astype(float)
    result = np.zeros_like(ma1)
    for i in range(1, len(ma1)):
        if ma1[i - 1] > ma2[i - 1] and ma1[i] <= ma2[i]:
            result[i] = 1
    return result





def bt_crossover(ma1, ma2):
    ma1 = np.array(ma1).astype(float)
    ma2 = np.array(ma2).astype(float)
    result = np.zeros_like(ma1)
    for i in range(1, len(ma1)):
        if ma1[i - 1] < ma2[i - 1] and ma1[i] >= ma2[i]:
            result[i] = 1
    return result


def bt_crossunder(ma1, ma2):
    ma1 = np.array(ma1).astype(float)
    ma2 = np.array(ma2).astype(float)
    result = np.zeros_like(ma1)
    for i in range(1, len(ma1)):
        if ma1[i - 1] > ma2[i - 1] and ma1[i] <= ma2[i]:
            result[i] = 1
    return result


def NthMaxList(n, *args):
    if n <= 0:
        return "Invalid value for n. Please provide a positive integer."
    elif n > len(args[0]):
        return f"n is greater than the number of elements in the arrays. Please provide a value less than or equal to {len(args[0])}."
    else:
        second_max_list = []
        for i in range(len(args[0])):
            column_values = [arr[i] for arr in args]
            column_values.sort(reverse=True)
            second_max_list.append(column_values[n - 1])
        return second_max_list


def sz_NthMaxList(n, *args):
    result = []
    for i in range(len(args[0])):
        column_values = [arr[i] for arr in args]
        column_values.sort(reverse=True)
        if n[i] <= 0:
            result.append("Invalid value for n. Please provide a positive integer.")
        elif n[i] > len(column_values):
            result.append(
                f"n is greater than the number of elements in the arrays. Please provide a value less than or equal to {len(column_values)}.")
        else:
            result.append(column_values[n[i] - 1])
    return result


def sz_NthMinList(n, *args):
    result = []
    for i in range(len(args[0])):
        column_values = [arr[i] for arr in args]
        column_values.sort()
        if n[i] <= 0:
            result.append("Invalid value for n. Please provide a positive integer.")
        elif n[i] > len(column_values):
            result.append(
                f"n is greater than the number of elements in the arrays. Please provide a value less than or equal to {len(column_values)}.")
        else:
            result.append(column_values[n[i] - 1])
    return result


def NthMinList(n, *args):
    if n <= 0:
        return "Invalid value for n. Please provide a positive integer."
    elif n > len(args[0]):
        return f"n is greater than the number of elements in the arrays. Please provide a value less than or equal to {len(args[0])}."
    else:
        second_min_list = []
        for i in range(len(args[0])):
            column_values = [arr[i] for arr in args]
            column_values.sort()
            second_min_list.append(column_values[n - 1])
        return second_min_list


# def calculate_kama(close, sqsz_min_wz):
#     kama_array = np.zeros_like(close)
#     for i in range(len(close)):
#         kama_array[i] = talib.KAMA(close[:i + 1], int(sqsz_min_wz[i]))[-1]
#     return kama_array


def dynamic_moving_average(data, c):
    dma = sum([data[i] - c * data[i - 1] for i in range(1, len(data))]) / len(data)
    return dma


def exponential_moving_average(data, alpha):
    ema = [data[0]]
    for i in range(1, len(data)):
        ema.append(alpha * data[i] + (1 - alpha) * ema[-1])
    return ema


def MYAMA(data, n=10, fast=5, slow=30):
    ama = []
    for i in range(len(data)):
        if i < slow:
            ama.append(data[i])
        else:
            dif = abs(data[i] - data[i - n])
            dif_sum = sum([abs(data[j] - data[j - 1]) for j in range(i - n, i)])
            roc = dif / dif_sum
            fastest = 2 / (fast + 1)
            slowest = 2 / (slow + 1)
            sm = roc * (fastest - slowest) + slowest
            c = sm * sm
            dma = dynamic_moving_average(data[i - n + 1:i + 1], c)
            ema = exponential_moving_average([dma], 2)
            ama.append(ema[-1])
    return ama


def MYEMA(S, N):
    if isinstance(S, list):
        S = np.array(S)
    if isinstance(N, list):
        N = np.array(N)
    alpha = 2 / (N + 1)
    res = []
    for i in range(len(S)):
        span = N[i]
        ema = pd.Series(S[:i + 1]).ewm(span=span, adjust=False).mean().values[-1]
        res.append(ema)
    return np.array(res)

# 将zhen_buy13_REF_wz8_HIGH_osc写入ini文件


def MYEXIST(zhen_buy13_limachengli, zhen_buy9_wz8):
    zhen_buy13_chengli_tj3 = []
    for i in range(len(zhen_buy9_wz8)):
        flag = False
        for j in range(i - zhen_buy9_wz8[i], i):
            if j >= 0 and zhen_buy13_limachengli[j] == 1:
                flag = True
                break
        zhen_buy13_chengli_tj3.append(1 if flag else 0)
    return np.array(zhen_buy13_chengli_tj3)


def MY_SUM(S, N):
    if isinstance(S, list):
        S = np.array(S)
    if isinstance(N, list):
        N = np.array(N)
    res = []
    for i in range(len(S)):
        sum_range = 0
        for j in range(i - N[i] + 1, i + 1):
            if j >= 0:
                sum_range += S[j]
        res.append(sum_range)
    return np.array(res)


def MY_BARSLAST(conditions, n):
    res = []  # 保存每根K线的timesswz2的列表
    for i in range(len(conditions)):
        last_occurrence = np.where(conditions[:i + 1] == 1)[0]
        if len(last_occurrence) < n:  # 不存在1
            res.append(0)  # 将timesswz2赋值为0代表不成立
        else:

            last_occurrence = last_occurrence[-1 * n]  # 获取最后一个1的位置
            ts = len(conditions[last_occurrence:i + 1]) - 1  # 从最后一个1的位置到当前位置的周期数
            res.append(ts)
    return np.array(res)


def MYREF(zhen_HIGH_osc, zhen_buy9_wz8):
    zhen_buy13_REF = []
    for i in range(len(zhen_HIGH_osc)):
        if i < zhen_buy9_wz8[i]:
            zhen_buy13_REF.append(np.nan)
        else:
            zhen_buy13_REF.append(zhen_HIGH_osc[i - zhen_buy9_wz8[i]])
    return np.array(zhen_buy13_REF)


def MY_LLVBARS(low_series, n):
    # 创建一个列表来存储结果
    result = []
    # 遍历每个周期
    for i in range(len(low_series)):
        # 计算当前周期的起始点
        start = max(0, i - n + 1)
        # print(start)
        # 获取n个周期内的最低值
        lowest_low = low_series[start:i + 1].min()
        # print(lowest_low)
        # 找到最低值的索引
        lowest_index = low_series[start:i + 1][low_series[start:i + 1] == lowest_low].index[0]

        # 计算当前周期到最低值的周期差
        bars = i - low_series.index.get_loc(lowest_index)
        # print(bars)
        result.append(bars)
        # print(result)
    return result


def MY_HHVBARS(high_series, n):
    # 创建一个列表来存储结果
    result = []
    # 遍历每个周期
    for i in range(len(high_series)):
        # 计算当前周期的起始点
        start = max(0, i - n + 1)
        # 获取n个周期内的最大值
        highest_high = high_series[start:i + 1].max()

        # 找到最大值的索引
        highest_index = high_series[start:i + 1][high_series[start:i + 1] == highest_high].index[0]

        # 计算当前周期到最大值的周期差
        bars = i - high_series.index.get_loc(highest_index)

        result.append(bars)

    return result


def calculate_avg_and_positions(fen_zhubuy_HJ):
    # 寻找有效数据的位置
    valid_data_idx = np.where(~np.isnan(fen_zhubuy_HJ))[0]
    # 取出有效数据
    valid_data = fen_zhubuy_HJ[valid_data_idx]
    # 计算有效数据的累计和
    sum_values = np.cumsum(np.abs(valid_data))
    # 生成有效数据的位置序列
    barpos = valid_data_idx + 1
    # 计算有效数据的移动平均值
    fen_zhudongbuy_pj = sum_values / barpos
    # 用1补齐无效数据
    fen_zhudongbuy_pj = np.concatenate(
        (np.array([1] * (fen_zhubuy_HJ.shape[0] - len(fen_zhudongbuy_pj))), fen_zhudongbuy_pj))
    barpos = np.arange(1, len(fen_zhudongbuy_pj) + 1)
    # 返回每个位置的移动平均值和每个元素的位置
    np.set_printoptions(precision=4, suppress=True)
    return fen_zhudongbuy_pj, barpos


def MYCOUNT(tiaojian, numpyint):
    sc_count = []
    for i in range(len(tiaojian)):
        count = 0
        for j in range(i - numpyint[i], i):
            if j >= 0 and tiaojian[j] == 1:
                count += 1
        sc_count.append(count)
    return np.array(sc_count)
def xuanze_jisuan(db_path, table_name, code, limit_num):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']
    # print(df)
    # 神奇数字算法
    # 价买13
    指导价 = EMA(df['close'], 4)
    sqsz_1_zdsz = 指导价
    sqsz_1_jiange_1 = 1
    sqsz_1_t1 = IF(sqsz_1_zdsz < REF(sqsz_1_zdsz, sqsz_1_jiange_1), 1, 0)
    sqsz_1_t2 = IF(REF(sqsz_1_zdsz, 1) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 1), 1, 0)
    sqsz_1_t3 = IF(REF(sqsz_1_zdsz, 2) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 2), 1, 0)
    sqsz_1_t4 = IF(REF(sqsz_1_zdsz, 3) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 3), 1, 0)
    sqsz_1_t5 = IF(REF(sqsz_1_zdsz, 4) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 4), 1, 0)
    sqsz_1_t6 = IF(REF(sqsz_1_zdsz, 5) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 5), 1, 0)
    sqsz_1_t7 = IF(REF(sqsz_1_zdsz, 6) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 6), 1, 0)
    sqsz_1_CL = IF(sqsz_1_t1 + sqsz_1_t2 + sqsz_1_t3 + sqsz_1_t4 + sqsz_1_t5 + sqsz_1_t6 + sqsz_1_t7 == 7, 1, 0)
    sqsz_1_CLqr_tj1 = IF(REF(sqsz_1_CL, 1) != 1, 1, 0)
    sqsz_1_CLqr_tj2 = IF(sqsz_1_CL == 1, 1, 0)
    sqsz_1_CLqr = IF(sqsz_1_CLqr_tj1 + sqsz_1_CLqr_tj2 == 2, 1, 0)

    sqsz_1_fan_t1 = IF(sqsz_1_zdsz > REF(sqsz_1_zdsz, sqsz_1_jiange_1), 1, 0)
    sqsz_1_fan_t2 = IF(REF(sqsz_1_zdsz, 1) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 1), 1, 0)
    sqsz_1_fan_t3 = IF(REF(sqsz_1_zdsz, 2) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 2), 1, 0)
    sqsz_1_fan_t4 = IF(REF(sqsz_1_zdsz, 3) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 3), 1, 0)
    sqsz_1_fan_t5 = IF(REF(sqsz_1_zdsz, 4) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 4), 1, 0)
    sqsz_1_fan_t6 = IF(REF(sqsz_1_zdsz, 5) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 5), 1, 0)
    sqsz_1_fan_t7 = IF(REF(sqsz_1_zdsz, 6) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 6), 1, 0)
    sqsz_1_fan_CL = IF(
        sqsz_1_fan_t1 + sqsz_1_fan_t2 + sqsz_1_fan_t3 + sqsz_1_fan_t4 + sqsz_1_fan_t5 + sqsz_1_fan_t6 + sqsz_1_fan_t7 == 7,
        1, 0)
    sqsz_1_fan_CLqr_tj1 = IF(REF(sqsz_1_fan_CL, 1) != 1, 1, 0)
    sqsz_1_fan_CLqr_tj2 = IF(sqsz_1_fan_CL == 1, 1, 0)
    sqsz_1_fan_CLqr = IF(sqsz_1_fan_CLqr_tj1 + sqsz_1_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_1_gaopao = sqsz_1_fan_CLqr
    sqsz_1_dixi = sqsz_1_CLqr

    sqsz_4_zdsz = 指导价
    sqsz_4_jiange_1 = 4
    sqsz_4_t1 = IF(sqsz_4_zdsz < REF(sqsz_4_zdsz, sqsz_4_jiange_1), 1, 0)
    sqsz_4_t2 = IF(REF(sqsz_4_zdsz, 1) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 1), 1, 0)
    sqsz_4_t3 = IF(REF(sqsz_4_zdsz, 2) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 2), 1, 0)
    sqsz_4_t4 = IF(REF(sqsz_4_zdsz, 3) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 3), 1, 0)
    sqsz_4_t5 = IF(REF(sqsz_4_zdsz, 4) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 4), 1, 0)
    sqsz_4_t6 = IF(REF(sqsz_4_zdsz, 5) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 5), 1, 0)
    sqsz_4_t7 = IF(REF(sqsz_4_zdsz, 6) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 6), 1, 0)
    sqsz_4_CL = IF(sqsz_4_t1 + sqsz_4_t2 + sqsz_4_t3 + sqsz_4_t4 + sqsz_4_t5 + sqsz_4_t6 + sqsz_4_t7 == 7, 1, 0)
    sqsz_4_CLqr_tj1 = IF(REF(sqsz_4_CL, 1) != 1, 1, 0)
    sqsz_4_CLqr_tj2 = IF(sqsz_4_CL == 1, 1, 0)
    sqsz_4_CLqr = IF(sqsz_4_CLqr_tj1 + sqsz_4_CLqr_tj2 == 2, 1, 0)

    sqsz_4_fan_t1 = IF(sqsz_4_zdsz > REF(sqsz_4_zdsz, sqsz_4_jiange_1), 1, 0)
    sqsz_4_fan_t2 = IF(REF(sqsz_4_zdsz, 1) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 1), 1, 0)
    sqsz_4_fan_t3 = IF(REF(sqsz_4_zdsz, 2) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 2), 1, 0)
    sqsz_4_fan_t4 = IF(REF(sqsz_4_zdsz, 3) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 3), 1, 0)
    sqsz_4_fan_t5 = IF(REF(sqsz_4_zdsz, 4) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 4), 1, 0)
    sqsz_4_fan_t6 = IF(REF(sqsz_4_zdsz, 5) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 5), 1, 0)
    sqsz_4_fan_t7 = IF(REF(sqsz_4_zdsz, 6) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 6), 1, 0)
    sqsz_4_fan_CL = IF(
        sqsz_4_fan_t1 + sqsz_4_fan_t2 + sqsz_4_fan_t3 + sqsz_4_fan_t4 + sqsz_4_fan_t5 + sqsz_4_fan_t6 + sqsz_4_fan_t7 == 7,
        1, 0)
    sqsz_4_fan_CLqr_tj1 = IF(REF(sqsz_4_fan_CL, 1) != 1, 1, 0)
    sqsz_4_fan_CLqr_tj2 = IF(sqsz_4_fan_CL == 1, 1, 0)
    sqsz_4_fan_CLqr = IF(sqsz_4_fan_CLqr_tj1 + sqsz_4_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_4_gaopao = sqsz_4_fan_CLqr
    sqsz_4_dixi = sqsz_4_CLqr

    sqsz_2_zdsz = 指导价
    sqsz_2_jiange_1 = 2
    sqsz_2_t1 = IF(sqsz_2_zdsz < REF(sqsz_2_zdsz, sqsz_2_jiange_1), 1, 0)
    sqsz_2_t2 = IF(REF(sqsz_2_zdsz, 1) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 1), 1, 0)
    sqsz_2_t3 = IF(REF(sqsz_2_zdsz, 2) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 2), 1, 0)
    sqsz_2_t4 = IF(REF(sqsz_2_zdsz, 3) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 3), 1, 0)
    sqsz_2_t5 = IF(REF(sqsz_2_zdsz, 4) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 4), 1, 0)
    sqsz_2_t6 = IF(REF(sqsz_2_zdsz, 5) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 5), 1, 0)
    sqsz_2_t7 = IF(REF(sqsz_2_zdsz, 6) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 6), 1, 0)
    sqsz_2_CL = IF(sqsz_2_t1 + sqsz_2_t2 + sqsz_2_t3 + sqsz_2_t4 + sqsz_2_t5 + sqsz_2_t6 + sqsz_2_t7 == 7, 1, 0)
    sqsz_2_CLqr_tj1 = IF(REF(sqsz_2_CL, 1) != 1, 1, 0)
    sqsz_2_CLqr_tj2 = IF(sqsz_2_CL == 1, 1, 0)
    sqsz_2_CLqr = IF(sqsz_2_CLqr_tj1 + sqsz_2_CLqr_tj2 == 2, 1, 0)

    sqsz_2_fan_t1 = IF(sqsz_2_zdsz > REF(sqsz_2_zdsz, sqsz_2_jiange_1), 1, 0)
    sqsz_2_fan_t2 = IF(REF(sqsz_2_zdsz, 1) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 1), 1, 0)
    sqsz_2_fan_t3 = IF(REF(sqsz_2_zdsz, 2) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 2), 1, 0)
    sqsz_2_fan_t4 = IF(REF(sqsz_2_zdsz, 3) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 3), 1, 0)
    sqsz_2_fan_t5 = IF(REF(sqsz_2_zdsz, 4) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 4), 1, 0)
    sqsz_2_fan_t6 = IF(REF(sqsz_2_zdsz, 5) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 5), 1, 0)
    sqsz_2_fan_t7 = IF(REF(sqsz_2_zdsz, 6) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 6), 1, 0)
    sqsz_2_fan_CL = IF(
        sqsz_2_fan_t1 + sqsz_2_fan_t2 + sqsz_2_fan_t3 + sqsz_2_fan_t4 + sqsz_2_fan_t5 + sqsz_2_fan_t6 + sqsz_2_fan_t7 == 7,
        1, 0)
    sqsz_2_fan_CLqr_tj1 = IF(REF(sqsz_2_fan_CL, 1) != 1, 1, 0)
    sqsz_2_fan_CLqr_tj2 = IF(sqsz_2_fan_CL == 1, 1, 0)
    sqsz_2_fan_CLqr = IF(sqsz_2_fan_CLqr_tj1 + sqsz_2_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_2_gaopao = sqsz_2_fan_CLqr
    sqsz_2_dixi = sqsz_2_CLqr

    sqsz_8_zdsz = 指导价
    sqsz_8_jiange_1 = 8
    sqsz_8_t1 = IF(sqsz_8_zdsz < REF(sqsz_8_zdsz, sqsz_8_jiange_1), 1, 0)
    sqsz_8_t2 = IF(REF(sqsz_8_zdsz, 1) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 1), 1, 0)
    sqsz_8_t3 = IF(REF(sqsz_8_zdsz, 2) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 2), 1, 0)
    sqsz_8_t4 = IF(REF(sqsz_8_zdsz, 3) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 3), 1, 0)
    sqsz_8_t5 = IF(REF(sqsz_8_zdsz, 4) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 4), 1, 0)
    sqsz_8_t6 = IF(REF(sqsz_8_zdsz, 5) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 5), 1, 0)
    sqsz_8_t7 = IF(REF(sqsz_8_zdsz, 6) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 6), 1, 0)
    sqsz_8_CL = IF(sqsz_8_t1 + sqsz_8_t2 + sqsz_8_t3 + sqsz_8_t4 + sqsz_8_t5 + sqsz_8_t6 + sqsz_8_t7 == 7, 1, 0)
    sqsz_8_CLqr_tj1 = IF(REF(sqsz_8_CL, 1) != 1, 1, 0)
    sqsz_8_CLqr_tj2 = IF(sqsz_8_CL == 1, 1, 0)
    sqsz_8_CLqr = IF(sqsz_8_CLqr_tj1 + sqsz_8_CLqr_tj2 == 2, 1, 0)

    sqsz_8_fan_t1 = IF(sqsz_8_zdsz > REF(sqsz_8_zdsz, sqsz_8_jiange_1), 1, 0)
    sqsz_8_fan_t2 = IF(REF(sqsz_8_zdsz, 1) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 1), 1, 0)
    sqsz_8_fan_t3 = IF(REF(sqsz_8_zdsz, 2) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 2), 1, 0)
    sqsz_8_fan_t4 = IF(REF(sqsz_8_zdsz, 3) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 3), 1, 0)
    sqsz_8_fan_t5 = IF(REF(sqsz_8_zdsz, 4) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 4), 1, 0)
    sqsz_8_fan_t6 = IF(REF(sqsz_8_zdsz, 5) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 5), 1, 0)
    sqsz_8_fan_t7 = IF(REF(sqsz_8_zdsz, 6) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 6), 1, 0)
    sqsz_8_fan_CL = IF(
        sqsz_8_fan_t1 + sqsz_8_fan_t2 + sqsz_8_fan_t3 + sqsz_8_fan_t4 + sqsz_8_fan_t5 + sqsz_8_fan_t6 + sqsz_8_fan_t7 == 7,
        1, 0)
    sqsz_8_fan_CLqr_tj1 = IF(REF(sqsz_8_fan_CL, 1) != 1, 1, 0)
    sqsz_8_fan_CLqr_tj2 = IF(sqsz_8_fan_CL == 1, 1, 0)
    sqsz_8_fan_CLqr = IF(sqsz_8_fan_CLqr_tj1 + sqsz_8_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_8_gaopao = sqsz_8_fan_CLqr
    sqsz_8_dixi = sqsz_8_CLqr

    sqsz_5_zdsz = 指导价
    sqsz_5_jiange_1 = 5
    sqsz_5_t1 = IF(sqsz_5_zdsz < REF(sqsz_5_zdsz, sqsz_5_jiange_1), 1, 0)
    sqsz_5_t2 = IF(REF(sqsz_5_zdsz, 1) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 1), 1, 0)
    sqsz_5_t3 = IF(REF(sqsz_5_zdsz, 2) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 2), 1, 0)
    sqsz_5_t4 = IF(REF(sqsz_5_zdsz, 3) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 3), 1, 0)
    sqsz_5_t5 = IF(REF(sqsz_5_zdsz, 4) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 4), 1, 0)
    sqsz_5_t6 = IF(REF(sqsz_5_zdsz, 5) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 5), 1, 0)
    sqsz_5_t7 = IF(REF(sqsz_5_zdsz, 6) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 6), 1, 0)
    sqsz_5_CL = IF(sqsz_5_t1 + sqsz_5_t2 + sqsz_5_t3 + sqsz_5_t4 + sqsz_5_t5 + sqsz_5_t6 + sqsz_5_t7 == 7, 1, 0)
    sqsz_5_CLqr_tj1 = IF(REF(sqsz_5_CL, 1) != 1, 1, 0)
    sqsz_5_CLqr_tj2 = IF(sqsz_5_CL == 1, 1, 0)
    sqsz_5_CLqr = IF(sqsz_5_CLqr_tj1 + sqsz_5_CLqr_tj2 == 2, 1, 0)

    sqsz_5_fan_t1 = IF(sqsz_5_zdsz > REF(sqsz_5_zdsz, sqsz_5_jiange_1), 1, 0)
    sqsz_5_fan_t2 = IF(REF(sqsz_5_zdsz, 1) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 1), 1, 0)
    sqsz_5_fan_t3 = IF(REF(sqsz_5_zdsz, 2) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 2), 1, 0)
    sqsz_5_fan_t4 = IF(REF(sqsz_5_zdsz, 3) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 3), 1, 0)
    sqsz_5_fan_t5 = IF(REF(sqsz_5_zdsz, 4) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 4), 1, 0)
    sqsz_5_fan_t6 = IF(REF(sqsz_5_zdsz, 5) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 5), 1, 0)
    sqsz_5_fan_t7 = IF(REF(sqsz_5_zdsz, 6) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 6), 1, 0)
    sqsz_5_fan_CL = IF(
        sqsz_5_fan_t1 + sqsz_5_fan_t2 + sqsz_5_fan_t3 + sqsz_5_fan_t4 + sqsz_5_fan_t5 + sqsz_5_fan_t6 + sqsz_5_fan_t7 == 7,
        1, 0)
    sqsz_5_fan_CLqr_tj1 = IF(REF(sqsz_5_fan_CL, 1) != 1, 1, 0)
    sqsz_5_fan_CLqr_tj2 = IF(sqsz_5_fan_CL == 1, 1, 0)
    sqsz_5_fan_CLqr = IF(sqsz_5_fan_CLqr_tj1 + sqsz_5_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_5_gaopao = sqsz_5_fan_CLqr
    sqsz_5_dixi = sqsz_5_CLqr

    sqsz_7_zdsz = 指导价
    sqsz_7_jiange_1 = 7
    sqsz_7_t1 = IF(sqsz_7_zdsz < REF(sqsz_7_zdsz, sqsz_7_jiange_1), 1, 0)
    sqsz_7_t2 = IF(REF(sqsz_7_zdsz, 1) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 1), 1, 0)
    sqsz_7_t3 = IF(REF(sqsz_7_zdsz, 2) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 2), 1, 0)
    sqsz_7_t4 = IF(REF(sqsz_7_zdsz, 3) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 3), 1, 0)
    sqsz_7_t5 = IF(REF(sqsz_7_zdsz, 4) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 4), 1, 0)
    sqsz_7_t6 = IF(REF(sqsz_7_zdsz, 5) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 5), 1, 0)
    sqsz_7_t7 = IF(REF(sqsz_7_zdsz, 6) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 6), 1, 0)
    sqsz_7_CL = IF(sqsz_7_t1 + sqsz_7_t2 + sqsz_7_t3 + sqsz_7_t4 + sqsz_7_t5 + sqsz_7_t6 + sqsz_7_t7 == 7, 1, 0)
    sqsz_7_CLqr_tj1 = IF(REF(sqsz_7_CL, 1) != 1, 1, 0)
    sqsz_7_CLqr_tj2 = IF(sqsz_7_CL == 1, 1, 0)
    sqsz_7_CLqr = IF(sqsz_7_CLqr_tj1 + sqsz_7_CLqr_tj2 == 2, 1, 0)

    sqsz_7_fan_t1 = IF(sqsz_7_zdsz > REF(sqsz_7_zdsz, sqsz_7_jiange_1), 1, 0)
    sqsz_7_fan_t2 = IF(REF(sqsz_7_zdsz, 1) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 1), 1, 0)
    sqsz_7_fan_t3 = IF(REF(sqsz_7_zdsz, 2) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 2), 1, 0)
    sqsz_7_fan_t4 = IF(REF(sqsz_7_zdsz, 3) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 3), 1, 0)
    sqsz_7_fan_t5 = IF(REF(sqsz_7_zdsz, 4) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 4), 1, 0)
    sqsz_7_fan_t6 = IF(REF(sqsz_7_zdsz, 5) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 5), 1, 0)
    sqsz_7_fan_t7 = IF(REF(sqsz_7_zdsz, 6) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 6), 1, 0)
    sqsz_7_fan_CL = IF(
        sqsz_7_fan_t1 + sqsz_7_fan_t2 + sqsz_7_fan_t3 + sqsz_7_fan_t4 + sqsz_7_fan_t5 + sqsz_7_fan_t6 + sqsz_7_fan_t7 == 7,
        1, 0)
    sqsz_7_fan_CLqr_tj1 = IF(REF(sqsz_7_fan_CL, 1) != 1, 1, 0)
    sqsz_7_fan_CLqr_tj2 = IF(sqsz_7_fan_CL == 1, 1, 0)
    sqsz_7_fan_CLqr = IF(sqsz_7_fan_CLqr_tj1 + sqsz_7_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_7_gaopao = sqsz_7_fan_CLqr
    sqsz_7_dixi = sqsz_7_CLqr

    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) != 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL == 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) != 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL == 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr

    sqszzh_sell_jiedian = IF(
        sqsz_1_gaopao + sqsz_4_gaopao + sqsz_2_gaopao + sqsz_8_gaopao + sqsz_5_gaopao + sqsz_7_gaopao + sqsz_9_gaopao >= 1,
        1, 0)
    sqszzh_buy_jiedian = IF(
        sqsz_1_dixi + sqsz_4_dixi + sqsz_2_dixi + sqsz_8_dixi + sqsz_5_dixi + sqsz_7_dixi + sqsz_9_dixi >= 1, 1, 0)
    # sqszzh_sell_jiedian=IF(sqsz_1_gaopao+sqsz_4_gaopao+sqsz_2_gaopao+sqsz_8_gaopao+sqsz_5_gaopao+sqsz_7_gaopao>=1,1,0)
    # sqszzh_buy_jiedian=IF(sqsz_1_dixi+sqsz_4_dixi+sqsz_2_dixi+sqsz_8_dixi+sqsz_5_dixi+sqsz_7_dixi>=1,1,0)
    # sqszzh_gjd_jiedian=IF(sqszzh_sell_jiedian+sqszzh_buy_jiedian+算涨A铆钉节点+算涨B铆钉节点>=1,1,0)
    # sqszzh_sell_jiedian=IF(sqsz_4_gaopao+sqsz_8_gaopao+sqsz_9_gaopao>=1,1,0)
    # sqszzh_buy_jiedian=IF(sqsz_4_dixi+sqsz_8_dixi+sqsz_9_dixi>=1,1,0)
    sqszzh_gjd_jiedian = IF(sqszzh_sell_jiedian + sqszzh_buy_jiedian >= 1, 1, 0)
    BarsLast_sqszzh_buy_jiedian_wz = MY_BARSLAST(sqszzh_buy_jiedian == 1, 1)  # 上一次低吸wz
    BarsLast_sqszzh_sell_jiedian_wz = MY_BARSLAST(sqszzh_sell_jiedian == 1, 1)  # 上一次高抛wz
    BarsLast_ssqszzh_gjd_jiedian_wz = MY_BARSLAST(sqszzh_gjd_jiedian == 1, 1)  # 上一次关键点wz
    x最高价 = HHV(df['high'], 4)
    x最低价 = LLV(df['low'], 4)
    x收盘价 = df['close']
    x开盘价 = REF(df['close'], 4)
    xm = 26
    xTR1 = MAX(MAX((x最高价 - x最低价), ABS(REF(x收盘价, 4) - x最高价)), ABS(REF(x收盘价, 4) - x最低价))
    xATR1 = EMA(xTR1, xm)

    下关键线 = MYREF(MA(LLV(df['high'], 30), 30), BarsLast_ssqszzh_gjd_jiedian_wz)
    下盈 = (HHV(下关键线, 30))

    上关键线 = MYREF(MA(HHV(df['low'], 30), 30), BarsLast_ssqszzh_gjd_jiedian_wz)
    上盈 = (LLV(上关键线, 30))

    # 价格的波段率
    bs = 1
    bdl_a = ((HHV(最高价_x, 39 * bs) - LLV(最低价_x, 39 * bs)) / 39 * bs) * 10000
    bdl_b = (HHV(最高价_x, 24 * bs) - LLV(最低价_x, 24 * bs)) / 24 * bs * 10000
    bdl_c = (HHV(最高价_x, 71 * bs) - LLV(最低价_x, 71 * bs)) / 71 * bs * 10000
    bdl_d = (HHV(最高价_x, 44 * bs) - LLV(最低价_x, 44 * bs)) / 44 * bs * 10000
    bdl_e = (HHV(最高价_x, 66 * bs) - LLV(最低价_x, 66 * bs)) / 66 * bs * 10000
    bdl_f = (HHV(最高价_x, 99 * bs) - LLV(最低价_x, 99 * bs)) / 99 * bs * 10000
    bdl_bz = bdl_a * 1000 / bdl_b * 1000 / bdl_c * 1000 / bdl_d * 1000 / bdl_e * 1000 / bdl_f * 1000
    # 最大最小值归一化
    bdl_bz = (bdl_bz - np.nanmin(bdl_bz)) / (np.nanmax(bdl_bz) - np.nanmin(bdl_bz))
    # 零均值单位方差归一化
    # mean_filled_bdl_bz = np.nan_to_num(bdl_bz, nan=np.nanmean(bdl_bz))
    # normalized_bdl_bz = (mean_filled_bdl_bz - np.mean(mean_filled_bdl_bz)) / np.std(mean_filled_bdl_bz)*1000000
    # print(bdl_bz)
    bdl_bz_ema = EMA(bdl_bz, 60)
    bdl_二十最高 = HHV(bdl_bz, 10)
    bdl_二十最高pj = SUM(bdl_二十最高, 100) / 100
    bdl_波动率_pj, barpos = calculate_avg_and_positions(bdl_二十最高pj)
    bdl_波动率_b2 = bdl_二十最高pj - REF(bdl_二十最高pj, 25)
    bdl_波动率_b2[bdl_波动率_b2 == 0] = 1e-8  # 判断并将分母为零的值赋为1e-8
    bdl_波动率_a2 = 25 * bdl_波动率_pj
    bdl_波动率_jiaodu_c2 = 90 - (np.arctan(bdl_波动率_a2 / bdl_波动率_b2) * 57.29578)
    bdl_波动率_jiaodu_cqr2 = IF(bdl_波动率_jiaodu_c2 > 90, (180 - bdl_波动率_jiaodu_c2) * -1, bdl_波动率_jiaodu_c2)
    小角度cqr = EMA(bdl_波动率_jiaodu_cqr2, 20)
    小角度cqr小于0节点tj1 = IF(小角度cqr < 0, 1, 0)
    小角度cqr小于0节点tj2 = IF(REF(小角度cqr, 1) >= 0, 1, 0)
    小角度cqr小于0节点 = IF(小角度cqr小于0节点tj1 + 小角度cqr小于0节点tj2 == 2, 1, 0)
    小角度cqrxz_tj1 = IF(EVERY(小角度cqr < 0, 4), 1, 0)
    小角度cqrxz_tj2 = IF(EXIST(小角度cqr小于0节点 == 1, 4), 1, 0)
    小角度cqrxz = IF(小角度cqrxz_tj1 + 小角度cqrxz_tj2 == 2, 1, 0)

    上限 = MYREF(收盘价_x, MY_BARSLAST(小角度cqrxz == 1, 1)) + 1 * xATR1
    下限 = MYREF(收盘价_x, MY_BARSLAST(小角度cqrxz == 1, 1)) - 1 * xATR1

    # 最高价_x=df['high']
    # 最低价_x=df['low']
    # 开盘价_x=df['open']
    # 收盘价_x=df['close']
    # 成交量_x=df['vol']
    a_tj1 = IF(df['high'] < x最高价, 1, 0)
    a_tj2 = IF(df['low'] > x最低价, 1, 0)
    a_tj3 = IF(NthMaxList(1, df['open'], df['close']) < NthMaxList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a_tj4 = IF(NthMinList(1, df['open'], df['close']) > NthMinList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a = IF(a_tj1 + a_tj2 + a_tj3 + a_tj4 == 4, 1, 0)
    a_wz = MY_BARSLAST(a, 1)
    yali = NthMaxList(1, MYREF(df['high'], a_wz), MYREF(df['high'], a_wz + 1), MYREF(df['high'], a_wz + 2),
                      MYREF(df['high'], a_wz + 3))
    zicheng = NthMinList(1, MYREF(df['low'], a_wz), MYREF(df['low'], a_wz + 1), MYREF(df['low'], a_wz + 2),
                         MYREF(df['low'], a_wz + 3))
    junx2 = EMA((上限 + 上盈 + EMA(zicheng, 30) + EMA(zicheng, 40) + EMA(zicheng, 50) + EMA(zicheng, 60)) / 6, 66)
    junx2b = EMA((下限 + 下盈 + EMA(zicheng, 20)) / 3, 66)
    junxa = (junx2 + HHV(df['high'], 66)) / 2
    junxb = (junx2 + LLV(df['low'], 66)) / 2

    # 动量 主动买入形成趋势分时
    # 镜

    jing_sss = 4
    jing_zqbs = 1
    jing_high = df['high']
    jing_low = df['low']
    jing_close = df['close']
    jing_open = df['open']
    jing_vol = df['vol']
    jing_oop = 1
    jing_bs = 1

    jing_pjj = (jing_close + jing_high + jing_low + jing_open) / 4
    jing_suducha = jing_pjj - REF(jing_pjj, 1)
    # IF(S,A,B)
    jing_zhubuy = IF(jing_suducha > 0, jing_suducha, 0) * jing_vol
    jing_zhusell = IF(jing_suducha < 0, jing_suducha, 0) * jing_vol

    jing_zhubuy_15 = SUM(ABS(jing_zhubuy), 1 * jing_oop * jing_bs)
    jing_zhusell_15 = SUM(ABS(jing_zhusell), 1 * jing_oop * jing_bs)
    jing_zhubuy_20 = SUM(ABS(jing_zhubuy), 2 * jing_oop * jing_bs)
    jing_zhusell_20 = SUM(ABS(jing_zhusell), 2 * jing_oop * jing_bs)
    jing_zhubuy_40 = SUM(ABS(jing_zhubuy), 3 * jing_oop * jing_bs)
    jing_zhusell_40 = SUM(ABS(jing_zhusell), 3 * jing_oop * jing_bs)
    jing_zhubuy_80 = SUM(ABS(jing_zhubuy), 6 * jing_oop * jing_bs)
    jing_zhusell_80 = SUM(ABS(jing_zhusell), 6 * jing_oop * jing_bs)
    jing_zhubuy_100 = SUM(ABS(jing_zhubuy), 4 * jing_oop * jing_bs)
    jing_zhusell_100 = SUM(ABS(jing_zhusell), 4 * jing_oop * jing_bs)
    jing_zhubuy_120 = SUM(ABS(jing_zhubuy), 8 * jing_oop * jing_bs)
    jing_zhusell_120 = SUM(ABS(jing_zhusell), 8 * jing_oop * jing_bs)
    jing_zhubuy_140 = SUM(ABS(jing_zhubuy), 10 * jing_oop * jing_bs)
    jing_zhusell_140 = SUM(ABS(jing_zhusell), 10 * jing_oop * jing_bs)
    jing_zhubuy_160 = SUM(ABS(jing_zhubuy), 12 * jing_oop * jing_bs)
    jing_zhusell_160 = SUM(ABS(jing_zhusell), 12 * jing_oop * jing_bs)
    jing_zhubuy_180 = SUM(ABS(jing_zhubuy), 15 * jing_oop * jing_bs)
    jing_zhusell_180 = SUM(ABS(jing_zhusell), 15 * jing_oop * jing_bs)

    jing_zhubuy_HJ = (
                             jing_zhubuy_15 + jing_zhubuy_20 + jing_zhubuy_40 + jing_zhubuy_80 + jing_zhubuy_100 + jing_zhubuy_120 + jing_zhubuy_140 + jing_zhubuy_160 + jing_zhubuy_180) / 9
    jing_zhusel_HJ = (
                             jing_zhusell_15 + jing_zhusell_20 + jing_zhusell_40 + jing_zhusell_80 + jing_zhusell_100 + jing_zhusell_120 + jing_zhusell_140 + jing_zhusell_160 + jing_zhusell_180) / 9
    jing_zhudong_cha = (jing_zhubuy_HJ - jing_zhusel_HJ)  # 粉小英线大中粉小主动差
    jing_zhudong_cha_pjzdc = EMA(jing_zhudong_cha, jing_sss)  # 粉小英线大中粉小主动差

    # 片
    pian_sss = 4
    pian_zqbs = 1
    pian_high = df['high']
    pian_low = df['low']
    pian_close = df['close']
    pian_open = df['open']
    pian_vol = df['vol']
    pian_oop = 1
    pian_bs = 1

    # 在 pian_VAR1 的计算中加入1e-8在计算 pian_VAR1 之前对分母进行判断，如果为零则将分母赋值为一个极小值（例如  1e-8 ），避免除数为零的情况。
    pian_VAR1 = pian_vol / ((pian_high - pian_low) * 2 - ABS(pian_close - pian_open) + 1e-8)
    # pian_buy_zb = IF(pian_close>pian_open,pian_VAR1*(pian_high-pian_low),IF(pian_close<pian_open,pian_VAR1*((pian_high-pian_open)+(pian_close-pian_low)),pian_vol/2))
    pian_zhubuy = IF(np.isnan(pian_VAR1), 0, IF(pian_close > pian_open, pian_VAR1 * (pian_high - pian_low),
                                                IF(pian_close < pian_open,
                                                   pian_VAR1 * ((pian_high - pian_open) + (pian_close - pian_low)),
                                                   pian_vol / 2)))
    # pian_sell_zb=IF(pian_close>pian_open,0-pian_VAR1*((pian_high-pian_close)+(pian_open-pian_low)),IF(pian_close<pian_open,0-pian_VAR1*(pian_high-pian_low),0-pian_vol/2))
    pian_zhusell = IF(np.isnan(pian_VAR1), 0,
                      IF(pian_close > pian_open, 0 - pian_VAR1 * ((pian_high - pian_close) + (pian_open - pian_low)),
                         IF(pian_close < pian_open, 0 - pian_VAR1 * (pian_high - pian_low), 0 - pian_vol / 2)))

    pian_zhubuy_15 = SUM(ABS(pian_zhubuy), 1 * pian_bs)
    pian_zhusell_15 = SUM(ABS(pian_zhusell), 1 * pian_bs)
    pian_zhubuy_20 = SUM(ABS(pian_zhubuy), 2 * pian_bs)
    pian_zhusell_20 = SUM(ABS(pian_zhusell), 2 * pian_bs)
    pian_zhubuy_40 = SUM(ABS(pian_zhubuy), 3 * pian_bs)
    pian_zhusell_40 = SUM(ABS(pian_zhusell), 3 * pian_bs)
    pian_zhubuy_80 = SUM(ABS(pian_zhubuy), 6 * pian_bs)
    pian_zhusell_80 = SUM(ABS(pian_zhusell), 6 * pian_bs)
    pian_zhubuy_100 = SUM(ABS(pian_zhubuy), 4 * pian_bs)
    pian_zhusell_100 = SUM(ABS(pian_zhusell), 4 * pian_bs)
    pian_zhubuy_120 = SUM(ABS(pian_zhubuy), 8 * pian_bs)
    pian_zhusell_120 = SUM(ABS(pian_zhusell), 8 * pian_bs)
    pian_zhubuy_140 = SUM(ABS(pian_zhubuy), 10 * pian_bs)
    pian_zhusell_140 = SUM(ABS(pian_zhusell), 10 * pian_bs)
    pian_zhubuy_160 = SUM(ABS(pian_zhubuy), 12 * pian_bs)
    pian_zhusell_160 = SUM(ABS(pian_zhusell), 12 * pian_bs)
    pian_zhubuy_180 = SUM(ABS(pian_zhubuy), 15 * pian_bs)
    pian_zhusell_180 = SUM(ABS(pian_zhusell), 15 * pian_bs)

    pian_zhubuy_HJ = (
                             pian_zhubuy_15 + pian_zhubuy_20 + pian_zhubuy_40 + pian_zhubuy_80 + pian_zhubuy_100 + pian_zhubuy_120 + pian_zhubuy_140 + pian_zhubuy_160 + pian_zhubuy_180) / 9
    pian_zhusel_HJ = (
                             pian_zhusell_15 + pian_zhusell_20 + pian_zhusell_40 + pian_zhusell_80 + pian_zhusell_100 + pian_zhusell_120 + pian_zhusell_140 + pian_zhusell_160 + pian_zhusell_180) / 9
    pian_zhudong_cha = (pian_zhubuy_HJ - pian_zhusel_HJ)  # 粉小英线大中粉小主动差
    pian_zhudong_cha_pjzdc = EMA(pian_zhudong_cha, pian_sss)  # 粉小英线大中粉小主动差

    # 防
    fang_sss = 4
    fang_zqbs = 1
    fang_high = df['high']
    fang_low = df['low']
    fang_close = df['close']
    fang_open = df['open']
    fang_vol = df['vol'] / 2
    fang_oop = 1
    fang_bs = 1

    fang_xiaoqian_up = fang_close > REF(fang_close, 1)
    fang_xiaoqian_down = fang_close < REF(fang_close, 1)
    fang_xiaoqian_bfw1_tj1 = IF(REF(fang_xiaoqian_down, 1) != 1, 1, 0)
    fang_xiaoqian_bfw1_tj2 = IF(fang_xiaoqian_down == 1, 1, 0)
    fang_xiaoqian_bfw1_tj3 = IF(fang_xiaoqian_bfw1_tj1 + fang_xiaoqian_bfw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bfw1 = MY_BARSLAST(fang_xiaoqian_bfw1_tj3 == 1, 1) + 1

    fang_xiaoqian_bgw1_tj1 = IF(REF(fang_xiaoqian_up, 1) != 1, 1, 0)
    fang_xiaoqian_bgw1_tj2 = IF(fang_xiaoqian_up == 1, 1, 0)
    fang_xiaoqian_bgw1_tj3 = IF(fang_xiaoqian_bgw1_tj1 + fang_xiaoqian_bgw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bgw1 = MY_BARSLAST(fang_xiaoqian_bgw1_tj3 == 1, 1) + 1
    fang_xiaoqian_up_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bgw1)
    fang_xiaoqian_down_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bfw1)

    fang_xiaoqian_xxx = IF(fang_xiaoqian_up == 1, fang_xiaoqian_up_jiliang, fang_xiaoqian_down_jiliang)
    fang_xiaoqian_gongji = IF(fang_xiaoqian_down, fang_xiaoqian_xxx, 0)
    fang_xiaoqian_xuqiu = IF(fang_xiaoqian_up, fang_xiaoqian_xxx, 0)
    fang_zhubuy = fang_xiaoqian_xuqiu
    fang_zhusell = fang_xiaoqian_gongji

    fang_zhubuy_15 = SUM(ABS(fang_zhubuy), 1 * fang_oop * fang_bs)
    fang_zhusell_15 = SUM(ABS(fang_zhusell), 1 * fang_oop * fang_bs)
    fang_zhubuy_20 = SUM(ABS(fang_zhubuy), 2 * fang_oop * fang_bs)
    fang_zhusell_20 = SUM(ABS(fang_zhusell), 2 * fang_oop * fang_bs)
    fang_zhubuy_40 = SUM(ABS(fang_zhubuy), 3 * fang_oop * fang_bs)
    fang_zhusell_40 = SUM(ABS(fang_zhusell), 3 * fang_oop * fang_bs)
    fang_zhubuy_80 = SUM(ABS(fang_zhubuy), 6 * fang_oop * fang_bs)
    fang_zhusell_80 = SUM(ABS(fang_zhusell), 6 * fang_oop * fang_bs)
    fang_zhubuy_100 = SUM(ABS(fang_zhubuy), 4 * fang_oop * fang_bs)
    fang_zhusell_100 = SUM(ABS(fang_zhusell), 4 * fang_oop * fang_bs)
    fang_zhubuy_120 = SUM(ABS(fang_zhubuy), 8 * fang_oop * fang_bs)
    fang_zhusell_120 = SUM(ABS(fang_zhusell), 8 * fang_oop * fang_bs)
    fang_zhubuy_140 = SUM(ABS(fang_zhubuy), 10 * fang_oop * fang_bs)
    fang_zhusell_140 = SUM(ABS(fang_zhusell), 10 * fang_oop * fang_bs)
    fang_zhubuy_160 = SUM(ABS(fang_zhubuy), 12 * fang_oop * fang_bs)
    fang_zhusell_160 = SUM(ABS(fang_zhusell), 12 * fang_oop * fang_bs)
    fang_zhubuy_180 = SUM(ABS(fang_zhubuy), 15 * fang_oop * fang_bs)
    fang_zhusell_180 = SUM(ABS(fang_zhusell), 15 * fang_oop * fang_bs)
    fang_zhubuy_HJ = (
                             fang_zhubuy_15 + fang_zhubuy_20 + fang_zhubuy_40 + fang_zhubuy_80 + fang_zhubuy_100 + fang_zhubuy_120 + fang_zhubuy_140 + fang_zhubuy_160 + fang_zhubuy_180) / 9
    fang_zhusel_HJ = (
                             fang_zhusell_15 + fang_zhusell_20 + fang_zhusell_40 + fang_zhusell_80 + fang_zhusell_100 + fang_zhusell_120 + fang_zhusell_140 + fang_zhusell_160 + fang_zhusell_180) / 9
    fang_zhudong_cha = (fang_zhubuy_HJ - fang_zhusel_HJ)  # 粉小英线大中粉小主动差
    fang_zhudong_cha_pjzdc = EMA(fang_zhudong_cha, fang_sss)  # 粉小英线大中粉小主动差

    小合小pjzdc1x = (fang_zhubuy_HJ + pian_zhubuy_HJ + jing_zhubuy_HJ) / 3
    小合小pjzdc1 = (SUM(小合小pjzdc1x, 2) / 2 + SUM(小合小pjzdc1x, 4) / 4 + SUM(小合小pjzdc1x, 7) / 7) / 3

    小合小主动买入HJ = (fang_zhubuy_HJ + pian_zhubuy_HJ + jing_zhubuy_HJ) / 3
    小合小主动卖出HJ = (fang_zhusel_HJ + pian_zhusel_HJ + jing_zhusel_HJ) / 3
    QSsjbs = 14
    Ema_shi_zhubuy_HJ = MA(MA(MA(小合小主动买入HJ, 21 * QSsjbs), 13 * QSsjbs), 7 * QSsjbs)
    Ema_shi_zhubuy_HJx = MA(MA(MA(小合小主动买入HJ, 5 * QSsjbs), 5 * QSsjbs), 5 * QSsjbs)
    Ema_shi_zhusell_HJ = MA(MA(MA(小合小主动卖出HJ, 21 * QSsjbs), 13 * QSsjbs), 7 * QSsjbs)
    Ema_shi_zhusell_HJx = MA(MA(MA(小合小主动卖出HJ, 5 * QSsjbs), 5 * QSsjbs), 5 * QSsjbs)
    shi_zhudong_cha = (小合小主动买入HJ - 小合小主动卖出HJ)  # 粉小英线大中粉小主动差
    # print('shi_zhudong_bz:', [format(x, '.8f') for x in shi_zhudong_bz])
    shi_duotou_qiangshi1_tj1 = IF(小合小主动买入HJ > Ema_shi_zhubuy_HJx, 1, 0)
    shi_duotou_qiangshi1_tj2 = IF(小合小主动买入HJ > Ema_shi_zhubuy_HJ, 1, 0)
    shi_duotou_qiangshi1 = IF(shi_duotou_qiangshi1_tj1 + shi_duotou_qiangshi1_tj2 >= 1, 1, 0)
    shi_duotou_qiangshi_tj1 = IF(小合小主动买入HJ > 小合小主动卖出HJ, 1, 0)
    shi_duotou_qiangshi = IF(shi_duotou_qiangshi1 + shi_duotou_qiangshi_tj1 == 2, 1, 0)

    shi_kongtou_qiangshi1_tj1 = IF(小合小主动卖出HJ > Ema_shi_zhusell_HJx, 1, 0)
    shi_kongtou_qiangshi1_tj2 = IF(小合小主动卖出HJ > Ema_shi_zhusell_HJ, 1, 0)
    shi_kongtou_qiangshi1 = IF(shi_kongtou_qiangshi1_tj1 + shi_kongtou_qiangshi1_tj2 >= 1, 1, 0)
    shi_kongtou_qiangshi_tj1 = IF(小合小主动卖出HJ > 小合小主动买入HJ, 1, 0)
    shi_kongtou_qiangshi = IF(shi_kongtou_qiangshi1 + shi_kongtou_qiangshi_tj1 == 2, 1, 0)

    小合平均小主动差1 = MA(小合小pjzdc1, 3 * QSsjbs)
    小合平均小主动差2 = MA(小合小pjzdc1, 5 * QSsjbs)

    shi_buchong_best_duo1_tj1 = IF(小合平均小主动差1 > REF(小合平均小主动差1, 1), 1, 0)
    shi_buchong_best_duo1_tj2 = IF(小合平均小主动差1 > REF(小合平均小主动差1, 2), 1, 0)
    shi_buchong_best_duo1_tj3 = IF(小合平均小主动差2 > REF(小合平均小主动差2, 1), 1, 0)
    shi_buchong_best_duo1_tj4 = IF(小合平均小主动差2 > REF(小合平均小主动差2, 2), 1, 0)
    shi_buchong_best_duo1 = IF(
        shi_buchong_best_duo1_tj1 + shi_buchong_best_duo1_tj2 + shi_buchong_best_duo1_tj3 + shi_buchong_best_duo1_tj4 >= 1,
        1, 0)
    # 强势多
    shi_buchong_best_duo = IF(shi_buchong_best_duo1 + shi_duotou_qiangshi == 2, 1, 0)

    shi_buchong_best_kong1_tj1 = IF(小合平均小主动差1 < REF(小合平均小主动差1, 1), 1, 0)
    shi_buchong_best_kong1_tj2 = IF(小合平均小主动差1 < REF(小合平均小主动差1, 2), 1, 0)
    shi_buchong_best_kong1_tj3 = IF(小合平均小主动差2 < REF(小合平均小主动差2, 1), 1, 0)
    shi_buchong_best_kong1_tj4 = IF(小合平均小主动差2 < REF(小合平均小主动差2, 2), 1, 0)
    shi_buchong_best_kong1 = IF(
        shi_buchong_best_kong1_tj1 + shi_buchong_best_kong1_tj2 + shi_buchong_best_kong1_tj3 + shi_buchong_best_kong1_tj4 >= 1,
        1, 0)
    # 强势空
    shi_buchong_best_kong = IF(shi_buchong_best_kong1 + shi_kongtou_qiangshi == 2, 1, 0)

    选择tj1_A = IF(指导价 > junxa, 1, 0)
    选择tj1_B = IF(REF(指导价, 1) < REF(junxa, 1), 1, 0)
    选择tj1_AB = IF(选择tj1_A + 选择tj1_B == 2, 1, 0)
    选择tj1 = IF(EXIST(选择tj1_AB, 4), 1, 0)
    选择tj2 = IF(EXIST(shi_buchong_best_duo, 4), 1, 0)
    xuanze = IF(选择tj1 + 选择tj2 == 2, 1, 0)

    下行选择tj1_A = IF(指导价 < junxa, 1, 0)
    下行选择tj1_B = IF(REF(指导价, 1) > REF(junxa, 1), 1, 0)
    下行选择tj1_AB = IF(下行选择tj1_A + 下行选择tj1_B == 2, 1, 0)
    下行选择tj1 = IF(EXIST(下行选择tj1_AB, 1), 1, 0)
    xx_xuanze = IF(下行选择tj1 == 1, 1, 0)
    return xuanze, xx_xuanze


def gaopao_dix_gjd_all(指导价):
    sqsz_1_zdsz = 指导价
    sqsz_1_jiange_1 = 1
    sqsz_1_t1 = IF(sqsz_1_zdsz < REF(sqsz_1_zdsz, sqsz_1_jiange_1), 1, 0)
    sqsz_1_t2 = IF(REF(sqsz_1_zdsz, 1) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 1), 1, 0)
    sqsz_1_t3 = IF(REF(sqsz_1_zdsz, 2) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 2), 1, 0)
    sqsz_1_t4 = IF(REF(sqsz_1_zdsz, 3) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 3), 1, 0)
    sqsz_1_t5 = IF(REF(sqsz_1_zdsz, 4) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 4), 1, 0)
    sqsz_1_t6 = IF(REF(sqsz_1_zdsz, 5) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 5), 1, 0)
    sqsz_1_t7 = IF(REF(sqsz_1_zdsz, 6) < REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 6), 1, 0)
    sqsz_1_CL = IF(sqsz_1_t1 + sqsz_1_t2 + sqsz_1_t3 + sqsz_1_t4 + sqsz_1_t5 + sqsz_1_t6 + sqsz_1_t7 == 7, 1, 0)
    sqsz_1_CLqr_tj1 = IF(REF(sqsz_1_CL, 1) != 1, 1, 0)
    sqsz_1_CLqr_tj2 = IF(sqsz_1_CL == 1, 1, 0)
    sqsz_1_CLqr = IF(sqsz_1_CLqr_tj1 + sqsz_1_CLqr_tj2 == 2, 1, 0)

    sqsz_1_fan_t1 = IF(sqsz_1_zdsz > REF(sqsz_1_zdsz, sqsz_1_jiange_1), 1, 0)
    sqsz_1_fan_t2 = IF(REF(sqsz_1_zdsz, 1) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 1), 1, 0)
    sqsz_1_fan_t3 = IF(REF(sqsz_1_zdsz, 2) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 2), 1, 0)
    sqsz_1_fan_t4 = IF(REF(sqsz_1_zdsz, 3) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 3), 1, 0)
    sqsz_1_fan_t5 = IF(REF(sqsz_1_zdsz, 4) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 4), 1, 0)
    sqsz_1_fan_t6 = IF(REF(sqsz_1_zdsz, 5) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 5), 1, 0)
    sqsz_1_fan_t7 = IF(REF(sqsz_1_zdsz, 6) > REF(sqsz_1_zdsz, sqsz_1_jiange_1 + 6), 1, 0)
    sqsz_1_fan_CL = IF(
        sqsz_1_fan_t1 + sqsz_1_fan_t2 + sqsz_1_fan_t3 + sqsz_1_fan_t4 + sqsz_1_fan_t5 + sqsz_1_fan_t6 + sqsz_1_fan_t7 == 7,
        1, 0)
    sqsz_1_fan_CLqr_tj1 = IF(REF(sqsz_1_fan_CL, 1) != 1, 1, 0)
    sqsz_1_fan_CLqr_tj2 = IF(sqsz_1_fan_CL == 1, 1, 0)
    sqsz_1_fan_CLqr = IF(sqsz_1_fan_CLqr_tj1 + sqsz_1_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_1_gaopao = sqsz_1_fan_CLqr
    sqsz_1_dixi = sqsz_1_CLqr

    sqsz_4_zdsz = 指导价
    sqsz_4_jiange_1 = 4
    sqsz_4_t1 = IF(sqsz_4_zdsz < REF(sqsz_4_zdsz, sqsz_4_jiange_1), 1, 0)
    sqsz_4_t2 = IF(REF(sqsz_4_zdsz, 1) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 1), 1, 0)
    sqsz_4_t3 = IF(REF(sqsz_4_zdsz, 2) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 2), 1, 0)
    sqsz_4_t4 = IF(REF(sqsz_4_zdsz, 3) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 3), 1, 0)
    sqsz_4_t5 = IF(REF(sqsz_4_zdsz, 4) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 4), 1, 0)
    sqsz_4_t6 = IF(REF(sqsz_4_zdsz, 5) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 5), 1, 0)
    sqsz_4_t7 = IF(REF(sqsz_4_zdsz, 6) < REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 6), 1, 0)
    sqsz_4_CL = IF(sqsz_4_t1 + sqsz_4_t2 + sqsz_4_t3 + sqsz_4_t4 + sqsz_4_t5 + sqsz_4_t6 + sqsz_4_t7 == 7, 1, 0)
    sqsz_4_CLqr_tj1 = IF(REF(sqsz_4_CL, 1) != 1, 1, 0)
    sqsz_4_CLqr_tj2 = IF(sqsz_4_CL == 1, 1, 0)
    sqsz_4_CLqr = IF(sqsz_4_CLqr_tj1 + sqsz_4_CLqr_tj2 == 2, 1, 0)

    sqsz_4_fan_t1 = IF(sqsz_4_zdsz > REF(sqsz_4_zdsz, sqsz_4_jiange_1), 1, 0)
    sqsz_4_fan_t2 = IF(REF(sqsz_4_zdsz, 1) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 1), 1, 0)
    sqsz_4_fan_t3 = IF(REF(sqsz_4_zdsz, 2) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 2), 1, 0)
    sqsz_4_fan_t4 = IF(REF(sqsz_4_zdsz, 3) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 3), 1, 0)
    sqsz_4_fan_t5 = IF(REF(sqsz_4_zdsz, 4) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 4), 1, 0)
    sqsz_4_fan_t6 = IF(REF(sqsz_4_zdsz, 5) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 5), 1, 0)
    sqsz_4_fan_t7 = IF(REF(sqsz_4_zdsz, 6) > REF(sqsz_4_zdsz, sqsz_4_jiange_1 + 6), 1, 0)
    sqsz_4_fan_CL = IF(
        sqsz_4_fan_t1 + sqsz_4_fan_t2 + sqsz_4_fan_t3 + sqsz_4_fan_t4 + sqsz_4_fan_t5 + sqsz_4_fan_t6 + sqsz_4_fan_t7 == 7,
        1, 0)
    sqsz_4_fan_CLqr_tj1 = IF(REF(sqsz_4_fan_CL, 1) != 1, 1, 0)
    sqsz_4_fan_CLqr_tj2 = IF(sqsz_4_fan_CL == 1, 1, 0)
    sqsz_4_fan_CLqr = IF(sqsz_4_fan_CLqr_tj1 + sqsz_4_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_4_gaopao = sqsz_4_fan_CLqr
    sqsz_4_dixi = sqsz_4_CLqr

    sqsz_2_zdsz = 指导价
    sqsz_2_jiange_1 = 2
    sqsz_2_t1 = IF(sqsz_2_zdsz < REF(sqsz_2_zdsz, sqsz_2_jiange_1), 1, 0)
    sqsz_2_t2 = IF(REF(sqsz_2_zdsz, 1) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 1), 1, 0)
    sqsz_2_t3 = IF(REF(sqsz_2_zdsz, 2) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 2), 1, 0)
    sqsz_2_t4 = IF(REF(sqsz_2_zdsz, 3) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 3), 1, 0)
    sqsz_2_t5 = IF(REF(sqsz_2_zdsz, 4) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 4), 1, 0)
    sqsz_2_t6 = IF(REF(sqsz_2_zdsz, 5) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 5), 1, 0)
    sqsz_2_t7 = IF(REF(sqsz_2_zdsz, 6) < REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 6), 1, 0)
    sqsz_2_CL = IF(sqsz_2_t1 + sqsz_2_t2 + sqsz_2_t3 + sqsz_2_t4 + sqsz_2_t5 + sqsz_2_t6 + sqsz_2_t7 == 7, 1, 0)
    sqsz_2_CLqr_tj1 = IF(REF(sqsz_2_CL, 1) != 1, 1, 0)
    sqsz_2_CLqr_tj2 = IF(sqsz_2_CL == 1, 1, 0)
    sqsz_2_CLqr = IF(sqsz_2_CLqr_tj1 + sqsz_2_CLqr_tj2 == 2, 1, 0)

    sqsz_2_fan_t1 = IF(sqsz_2_zdsz > REF(sqsz_2_zdsz, sqsz_2_jiange_1), 1, 0)
    sqsz_2_fan_t2 = IF(REF(sqsz_2_zdsz, 1) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 1), 1, 0)
    sqsz_2_fan_t3 = IF(REF(sqsz_2_zdsz, 2) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 2), 1, 0)
    sqsz_2_fan_t4 = IF(REF(sqsz_2_zdsz, 3) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 3), 1, 0)
    sqsz_2_fan_t5 = IF(REF(sqsz_2_zdsz, 4) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 4), 1, 0)
    sqsz_2_fan_t6 = IF(REF(sqsz_2_zdsz, 5) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 5), 1, 0)
    sqsz_2_fan_t7 = IF(REF(sqsz_2_zdsz, 6) > REF(sqsz_2_zdsz, sqsz_2_jiange_1 + 6), 1, 0)
    sqsz_2_fan_CL = IF(
        sqsz_2_fan_t1 + sqsz_2_fan_t2 + sqsz_2_fan_t3 + sqsz_2_fan_t4 + sqsz_2_fan_t5 + sqsz_2_fan_t6 + sqsz_2_fan_t7 == 7,
        1, 0)
    sqsz_2_fan_CLqr_tj1 = IF(REF(sqsz_2_fan_CL, 1) != 1, 1, 0)
    sqsz_2_fan_CLqr_tj2 = IF(sqsz_2_fan_CL == 1, 1, 0)
    sqsz_2_fan_CLqr = IF(sqsz_2_fan_CLqr_tj1 + sqsz_2_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_2_gaopao = sqsz_2_fan_CLqr
    sqsz_2_dixi = sqsz_2_CLqr

    sqsz_8_zdsz = 指导价
    sqsz_8_jiange_1 = 8
    sqsz_8_t1 = IF(sqsz_8_zdsz < REF(sqsz_8_zdsz, sqsz_8_jiange_1), 1, 0)
    sqsz_8_t2 = IF(REF(sqsz_8_zdsz, 1) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 1), 1, 0)
    sqsz_8_t3 = IF(REF(sqsz_8_zdsz, 2) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 2), 1, 0)
    sqsz_8_t4 = IF(REF(sqsz_8_zdsz, 3) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 3), 1, 0)
    sqsz_8_t5 = IF(REF(sqsz_8_zdsz, 4) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 4), 1, 0)
    sqsz_8_t6 = IF(REF(sqsz_8_zdsz, 5) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 5), 1, 0)
    sqsz_8_t7 = IF(REF(sqsz_8_zdsz, 6) < REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 6), 1, 0)
    sqsz_8_CL = IF(sqsz_8_t1 + sqsz_8_t2 + sqsz_8_t3 + sqsz_8_t4 + sqsz_8_t5 + sqsz_8_t6 + sqsz_8_t7 == 7, 1, 0)
    sqsz_8_CLqr_tj1 = IF(REF(sqsz_8_CL, 1) != 1, 1, 0)
    sqsz_8_CLqr_tj2 = IF(sqsz_8_CL == 1, 1, 0)
    sqsz_8_CLqr = IF(sqsz_8_CLqr_tj1 + sqsz_8_CLqr_tj2 == 2, 1, 0)

    sqsz_8_fan_t1 = IF(sqsz_8_zdsz > REF(sqsz_8_zdsz, sqsz_8_jiange_1), 1, 0)
    sqsz_8_fan_t2 = IF(REF(sqsz_8_zdsz, 1) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 1), 1, 0)
    sqsz_8_fan_t3 = IF(REF(sqsz_8_zdsz, 2) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 2), 1, 0)
    sqsz_8_fan_t4 = IF(REF(sqsz_8_zdsz, 3) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 3), 1, 0)
    sqsz_8_fan_t5 = IF(REF(sqsz_8_zdsz, 4) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 4), 1, 0)
    sqsz_8_fan_t6 = IF(REF(sqsz_8_zdsz, 5) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 5), 1, 0)
    sqsz_8_fan_t7 = IF(REF(sqsz_8_zdsz, 6) > REF(sqsz_8_zdsz, sqsz_8_jiange_1 + 6), 1, 0)
    sqsz_8_fan_CL = IF(
        sqsz_8_fan_t1 + sqsz_8_fan_t2 + sqsz_8_fan_t3 + sqsz_8_fan_t4 + sqsz_8_fan_t5 + sqsz_8_fan_t6 + sqsz_8_fan_t7 == 7,
        1, 0)
    sqsz_8_fan_CLqr_tj1 = IF(REF(sqsz_8_fan_CL, 1) != 1, 1, 0)
    sqsz_8_fan_CLqr_tj2 = IF(sqsz_8_fan_CL == 1, 1, 0)
    sqsz_8_fan_CLqr = IF(sqsz_8_fan_CLqr_tj1 + sqsz_8_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_8_gaopao = sqsz_8_fan_CLqr
    sqsz_8_dixi = sqsz_8_CLqr

    sqsz_5_zdsz = 指导价
    sqsz_5_jiange_1 = 5
    sqsz_5_t1 = IF(sqsz_5_zdsz < REF(sqsz_5_zdsz, sqsz_5_jiange_1), 1, 0)
    sqsz_5_t2 = IF(REF(sqsz_5_zdsz, 1) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 1), 1, 0)
    sqsz_5_t3 = IF(REF(sqsz_5_zdsz, 2) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 2), 1, 0)
    sqsz_5_t4 = IF(REF(sqsz_5_zdsz, 3) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 3), 1, 0)
    sqsz_5_t5 = IF(REF(sqsz_5_zdsz, 4) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 4), 1, 0)
    sqsz_5_t6 = IF(REF(sqsz_5_zdsz, 5) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 5), 1, 0)
    sqsz_5_t7 = IF(REF(sqsz_5_zdsz, 6) < REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 6), 1, 0)
    sqsz_5_CL = IF(sqsz_5_t1 + sqsz_5_t2 + sqsz_5_t3 + sqsz_5_t4 + sqsz_5_t5 + sqsz_5_t6 + sqsz_5_t7 == 7, 1, 0)
    sqsz_5_CLqr_tj1 = IF(REF(sqsz_5_CL, 1) != 1, 1, 0)
    sqsz_5_CLqr_tj2 = IF(sqsz_5_CL == 1, 1, 0)
    sqsz_5_CLqr = IF(sqsz_5_CLqr_tj1 + sqsz_5_CLqr_tj2 == 2, 1, 0)

    sqsz_5_fan_t1 = IF(sqsz_5_zdsz > REF(sqsz_5_zdsz, sqsz_5_jiange_1), 1, 0)
    sqsz_5_fan_t2 = IF(REF(sqsz_5_zdsz, 1) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 1), 1, 0)
    sqsz_5_fan_t3 = IF(REF(sqsz_5_zdsz, 2) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 2), 1, 0)
    sqsz_5_fan_t4 = IF(REF(sqsz_5_zdsz, 3) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 3), 1, 0)
    sqsz_5_fan_t5 = IF(REF(sqsz_5_zdsz, 4) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 4), 1, 0)
    sqsz_5_fan_t6 = IF(REF(sqsz_5_zdsz, 5) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 5), 1, 0)
    sqsz_5_fan_t7 = IF(REF(sqsz_5_zdsz, 6) > REF(sqsz_5_zdsz, sqsz_5_jiange_1 + 6), 1, 0)
    sqsz_5_fan_CL = IF(
        sqsz_5_fan_t1 + sqsz_5_fan_t2 + sqsz_5_fan_t3 + sqsz_5_fan_t4 + sqsz_5_fan_t5 + sqsz_5_fan_t6 + sqsz_5_fan_t7 == 7,
        1, 0)
    sqsz_5_fan_CLqr_tj1 = IF(REF(sqsz_5_fan_CL, 1) != 1, 1, 0)
    sqsz_5_fan_CLqr_tj2 = IF(sqsz_5_fan_CL == 1, 1, 0)
    sqsz_5_fan_CLqr = IF(sqsz_5_fan_CLqr_tj1 + sqsz_5_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_5_gaopao = sqsz_5_fan_CLqr
    sqsz_5_dixi = sqsz_5_CLqr

    sqsz_7_zdsz = 指导价
    sqsz_7_jiange_1 = 7
    sqsz_7_t1 = IF(sqsz_7_zdsz < REF(sqsz_7_zdsz, sqsz_7_jiange_1), 1, 0)
    sqsz_7_t2 = IF(REF(sqsz_7_zdsz, 1) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 1), 1, 0)
    sqsz_7_t3 = IF(REF(sqsz_7_zdsz, 2) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 2), 1, 0)
    sqsz_7_t4 = IF(REF(sqsz_7_zdsz, 3) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 3), 1, 0)
    sqsz_7_t5 = IF(REF(sqsz_7_zdsz, 4) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 4), 1, 0)
    sqsz_7_t6 = IF(REF(sqsz_7_zdsz, 5) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 5), 1, 0)
    sqsz_7_t7 = IF(REF(sqsz_7_zdsz, 6) < REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 6), 1, 0)
    sqsz_7_CL = IF(sqsz_7_t1 + sqsz_7_t2 + sqsz_7_t3 + sqsz_7_t4 + sqsz_7_t5 + sqsz_7_t6 + sqsz_7_t7 == 7, 1, 0)
    sqsz_7_CLqr_tj1 = IF(REF(sqsz_7_CL, 1) != 1, 1, 0)
    sqsz_7_CLqr_tj2 = IF(sqsz_7_CL == 1, 1, 0)
    sqsz_7_CLqr = IF(sqsz_7_CLqr_tj1 + sqsz_7_CLqr_tj2 == 2, 1, 0)

    sqsz_7_fan_t1 = IF(sqsz_7_zdsz > REF(sqsz_7_zdsz, sqsz_7_jiange_1), 1, 0)
    sqsz_7_fan_t2 = IF(REF(sqsz_7_zdsz, 1) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 1), 1, 0)
    sqsz_7_fan_t3 = IF(REF(sqsz_7_zdsz, 2) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 2), 1, 0)
    sqsz_7_fan_t4 = IF(REF(sqsz_7_zdsz, 3) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 3), 1, 0)
    sqsz_7_fan_t5 = IF(REF(sqsz_7_zdsz, 4) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 4), 1, 0)
    sqsz_7_fan_t6 = IF(REF(sqsz_7_zdsz, 5) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 5), 1, 0)
    sqsz_7_fan_t7 = IF(REF(sqsz_7_zdsz, 6) > REF(sqsz_7_zdsz, sqsz_7_jiange_1 + 6), 1, 0)
    sqsz_7_fan_CL = IF(
        sqsz_7_fan_t1 + sqsz_7_fan_t2 + sqsz_7_fan_t3 + sqsz_7_fan_t4 + sqsz_7_fan_t5 + sqsz_7_fan_t6 + sqsz_7_fan_t7 == 7,
        1, 0)
    sqsz_7_fan_CLqr_tj1 = IF(REF(sqsz_7_fan_CL, 1) != 1, 1, 0)
    sqsz_7_fan_CLqr_tj2 = IF(sqsz_7_fan_CL == 1, 1, 0)
    sqsz_7_fan_CLqr = IF(sqsz_7_fan_CLqr_tj1 + sqsz_7_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_7_gaopao = sqsz_7_fan_CLqr
    sqsz_7_dixi = sqsz_7_CLqr

    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) != 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL == 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) != 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL == 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr

    sqszzh_sell_jiedian = IF(
        sqsz_1_gaopao + sqsz_4_gaopao + sqsz_2_gaopao + sqsz_8_gaopao + sqsz_5_gaopao + sqsz_7_gaopao + sqsz_9_gaopao >= 1,
        1, 0)
    sqszzh_buy_jiedian = IF(
        sqsz_1_dixi + sqsz_4_dixi + sqsz_2_dixi + sqsz_8_dixi + sqsz_5_dixi + sqsz_7_dixi + sqsz_9_dixi >= 1, 1, 0)

    sqszzh_gjd_jiedian = IF(sqszzh_sell_jiedian + sqszzh_buy_jiedian >= 1, 1, 0)
    return sqszzh_sell_jiedian, sqszzh_buy_jiedian


def gaopao_dix_4(指导价):
    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) == 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL != 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) == 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL != 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr
    sqszzh_sell_jiedian = IF(sqsz_9_gaopao == 1, 1, 0)
    sqszzh_buy_jiedian = IF(sqsz_9_dixi == 1, 1, 0)
    return sqszzh_sell_jiedian, sqszzh_buy_jiedian


def dingdifenxing(df):
    指导价 = df['close']
    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) == 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL != 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) == 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL != 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr
    sqszzh_sell_jiedian = IF(sqsz_9_gaopao == 1, 1, 0)
    sqszzh_buy_jiedian = IF(sqsz_9_dixi == 1, 1, 0)
    ##顶底分型
    sr最高价 = df['high']
    sr最低价 = df['low']
    sr开盘价 = df['open']
    sr收盘价 = df['close']
    V00_tj1 = IF(sr最高价 < REF(sr最高价, 1), 1, 0)
    V00_tj2 = IF(sr最低价 < REF(sr最低价, 1), 1, 0)
    V00 = IF(V00_tj1 + V00_tj2 == 2, 1, 0)
    V01_tj1 = IF(sr最高价 < REF(sr最高价, 1), 1, 0)
    V01_tj2 = IF(sr最低价 > REF(sr最低价, 1), 1, 0)
    V01 = IF(V01_tj1 + V01_tj2 == 2, 1, 0)
    V02_tj1 = IF(sr最高价 > REF(sr最高价, 1), 1, 0)
    V02_tj2 = IF(sr最低价 < REF(sr最低价, 1), 1, 0)
    V02 = IF(V02_tj1 + V02_tj2 == 2, 1, 0)
    V03_tj1 = IF(sr最高价 > REF(sr最高价, 1), 1, 0)
    V03_tj2 = IF(sr最低价 > REF(sr最低价, 1), 1, 0)
    V03 = IF(V03_tj1 + V03_tj2 == 2, 1, 0)

    V04_tj1 = IF(REF(sr最高价, 2) < sr最高价, 1, 0)
    V04_tj2 = IF(REF(sr最低价, 2) < sr最低价, 1, 0)
    V04_tj3 = IF(REF(sr最高价, 2) > REF(sr最高价, 1), 1, 0)
    V04_tj4 = IF(REF(sr最低价, 2) < REF(sr最低价, 1), 1, 0)
    V04 = IF(V04_tj1 + V04_tj2 + V04_tj3 + V04_tj4 == 4, 1, 0)

    v1_tj1 = IF(COUNT(V00, 6) >= 3, 1, 0)
    v1_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v1_tj2 = IF(COUNT(v1_tj2_zb, 5) == 0, 1, 0)
    v1_tj3_zb_jg = MyTT.LLVBARS(df['low'], 6)
    v1_tj3 = IF(v1_tj3_zb_jg == 1, 1, 0)
    v1_tj4 = IF(MyTT.HHVBARS(sr最高价, 6) >= 5, 1, 0)
    v1 = IF(v1_tj1 + v1_tj2 + v1_tj3 + v1_tj4 + V03 == 5, 1, 0)

    v2_tj1 = IF(COUNT(V00, 7) >= 3, 1, 0)
    v2_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v2_tj2 = IF(COUNT(v2_tj2_zb, 6) == 1, 1, 0)
    v2_tj3 = IF(MyTT.LLVBARS(sr最低价, 7) == 2, 1, 0)
    v2_tj4 = IF(MyTT.HHVBARS(sr最高价, 7) >= 6, 1, 0)
    v2 = IF(v2_tj1 + v2_tj2 + v2_tj3 + v2_tj4 + V04 == 5, 1, 0)

    v3_tj1 = IF(COUNT(V00, 7) >= 3, 1, 0)
    v3_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v3_tj2 = IF(COUNT(v3_tj2_zb, 6) == 1, 1, 0)
    v3_tj3 = IF(MyTT.LLVBARS(sr最低价, 7) == 1, 1, 0)
    v3_tj4 = IF(MyTT.HHVBARS(sr最高价, 7) >= 6, 1, 0)
    v3 = IF(v3_tj1 + v3_tj2 + v3_tj3 + v3_tj4 + V03 == 5, 1, 0)

    v4_tj1 = IF(COUNT(V00, 8) >= 3, 1, 0)
    v4_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v4_tj2 = IF(COUNT(v4_tj2_zb, 7) <= 2, 1, 0)
    v4_tj3 = IF(MyTT.LLVBARS(sr最低价, 8) == 2, 1, 0)
    v4_tj4 = IF(MyTT.HHVBARS(sr最高价, 8) >= 7, 1, 0)
    v4 = IF(v4_tj1 + v4_tj2 + v4_tj3 + v4_tj4 + V04 == 5, 1, 0)

    v5_tj1 = IF(COUNT(V00, 8) >= 3, 1, 0)
    v5_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v5_tj2 = IF(COUNT(v5_tj2_zb, 7) <= 2, 1, 0)
    v5_tj3 = IF(MyTT.LLVBARS(sr最低价, 8) == 1, 1, 0)
    v5_tj4 = IF(MyTT.HHVBARS(sr最高价, 8) >= 7, 1, 0)
    v5 = IF(v5_tj1 + v5_tj2 + v5_tj3 + v5_tj4 + V03 == 5, 1, 0)

    v6_tj1 = IF(COUNT(V00, 9) >= 3, 1, 0)
    v6_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v6_tj2 = IF(COUNT(v6_tj2_zb, 8) <= 3, 1, 0)
    v6_tj3 = IF(MyTT.LLVBARS(sr最低价, 9) == 2, 1, 0)
    v6_tj4 = IF(MyTT.HHVBARS(sr最高价, 9) >= 8, 1, 0)
    v6 = IF(v6_tj1 + v6_tj2 + v6_tj3 + v6_tj4 + V04 == 5, 1, 0)

    v7_tj1 = IF(COUNT(V00, 9) >= 3, 1, 0)
    v7_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v7_tj2 = IF(COUNT(v7_tj2_zb, 8) <= 3, 1, 0)
    v7_tj3 = IF(MyTT.LLVBARS(sr最低价, 9) == 1, 1, 0)
    v7_tj4 = IF(MyTT.HHVBARS(sr最高价, 9) >= 8, 1, 0)
    v7 = IF(v7_tj1 + v7_tj2 + v7_tj3 + v7_tj4 + V03 == 5, 1, 0)

    v8_tj1 = IF(COUNT(V00, 10) >= 3, 1, 0)
    v8_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v8_tj2 = IF(COUNT(v8_tj2_zb, 9) <= 4, 1, 0)
    v8_tj3 = IF(MyTT.LLVBARS(sr最低价, 10) == 2, 1, 0)
    v8_tj4 = IF(MyTT.HHVBARS(sr最高价, 10) >= 9, 1, 0)
    v8 = IF(v8_tj1 + v8_tj2 + v8_tj3 + v8_tj4 + V04 == 5, 1, 0)

    v9_tj1 = IF(COUNT(V00, 10) >= 3, 1, 0)
    v9_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v9_tj2 = IF(COUNT(v9_tj2_zb, 9) <= 4, 1, 0)
    v9_tj3 = IF(MyTT.LLVBARS(sr最低价, 10) == 1, 1, 0)
    v9_tj4 = IF(MyTT.HHVBARS(sr最高价, 10) >= 9, 1, 0)
    v9 = IF(v9_tj1 + v9_tj2 + v9_tj3 + v9_tj4 + V03 == 5, 1, 0)

    v10_tj1 = IF(COUNT(V00, 11) >= 3, 1, 0)
    v10_tj2_zb = IF(V01 + V02 >= 1, 1, 0)
    v10_tj2 = IF(COUNT(v10_tj2_zb, 10) <= 5, 1, 0)
    v10_tj3 = IF(MyTT.LLVBARS(sr最低价, 11) == 2, 1, 0)
    v10_tj4 = IF(MyTT.HHVBARS(sr最高价, 11) >= 10, 1, 0)
    v10 = IF(v10_tj1 + v10_tj2 + v10_tj3 + v10_tj4 + V04 == 5, 1, 0)

    XG = IF(v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8 + v9 + v10 >= 1, 1, 0)
    HV00_tj1 = IF(sr最高价 > REF(sr最高价, 1), 1, 0)
    HV00_tj2 = IF(sr最低价 > REF(sr最低价, 1), 1, 0)
    HV00 = IF(HV00_tj1 + HV00_tj2 == 2, 1, 0)

    HV01_tj1 = IF(sr最高价 < REF(sr最高价, 1), 1, 0)
    HV01_tj2 = IF(sr最低价 > REF(sr最低价, 1), 1, 0)
    HV01 = IF(HV01_tj1 + HV01_tj2 == 2, 1, 0)

    HV02_tj1 = IF(sr最高价 > REF(sr最高价, 1), 1, 0)
    HV02_tj2 = IF(sr最低价 < REF(sr最低价, 1), 1, 0)
    HV02 = IF(HV02_tj1 + HV02_tj2 == 2, 1, 0)

    HV03_tj1 = IF(sr最高价 < REF(sr最高价, 1), 1, 0)
    HV03_tj2 = IF(sr最低价 < REF(sr最低价, 1), 1, 0)
    HV03 = IF(HV03_tj1 + HV03_tj2 == 2, 1, 0)

    HV04_tj1 = IF(REF(sr最高价, 2) > sr最高价, 1, 0)
    HV04_tj2 = IF(REF(sr最低价, 2) > sr最低价, 1, 0)
    HV04_tj3 = IF(REF(sr最高价, 2) > REF(sr最高价, 1), 1, 0)
    HV04_tj4 = IF(REF(sr最低价, 2) < REF(sr最低价, 1), 1, 0)
    HV04 = IF(HV04_tj1 + HV04_tj2 + HV04_tj3 + HV04_tj4 == 4, 1, 0)

    HV1_tj1 = IF(COUNT(HV00, 6) >= 3, 1, 0)
    HV1_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV1_tj2 = IF(COUNT(HV1_tj2_zb, 5) == 0, 1, 0)
    HV1_tj3 = IF(MyTT.HHVBARS(sr最高价, 6) == 1, 1, 0)
    HV1_tj4 = IF(MyTT.LLVBARS(sr最低价, 6) >= 5, 1, 0)
    HV1 = IF(HV1_tj1 + HV1_tj2 + HV1_tj3 + HV1_tj4 + HV03 == 5, 1, 0)

    HV2_tj1 = IF(COUNT(HV00, 7) >= 3, 1, 0)
    HV2_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV2_tj2 = IF(COUNT(HV2_tj2_zb, 6) == 1, 1, 0)
    HV2_tj3 = IF(MyTT.HHVBARS(sr最高价, 7) == 2, 1, 0)
    HV2_tj4 = IF(MyTT.LLVBARS(sr最低价, 7) >= 6, 1, 0)
    HV2 = IF(HV2_tj1 + HV2_tj2 + HV2_tj3 + HV2_tj4 + HV04 == 5, 1, 0)

    HV3_tj1 = IF(COUNT(HV00, 7) >= 3, 1, 0)
    HV3_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV3_tj2 = IF(COUNT(HV3_tj2_zb, 6) == 1, 1, 0)
    HV3_tj3 = IF(MyTT.HHVBARS(sr最高价, 7) == 1, 1, 0)
    HV3_tj4 = IF(MyTT.LLVBARS(sr最低价, 7) >= 6, 1, 0)
    HV3 = IF(HV3_tj1 + HV3_tj2 + HV3_tj3 + HV3_tj4 + HV03 == 5, 1, 0)

    HV4_tj1 = IF(COUNT(HV00, 8) >= 3, 1, 0)
    HV4_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV4_tj2 = IF(COUNT(HV4_tj2_zb, 7) <= 2, 1, 0)
    HV4_tj3 = IF(MyTT.HHVBARS(sr最高价, 8) == 2, 1, 0)
    HV4_tj4 = IF(MyTT.LLVBARS(sr最低价, 8) >= 7, 1, 0)
    HV4 = IF(HV4_tj1 + HV4_tj2 + HV4_tj3 + HV4_tj4 + HV04 == 5, 1, 0)

    HV5_tj1 = IF(COUNT(HV00, 8) >= 3, 1, 0)
    HV5_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV5_tj2 = IF(COUNT(HV5_tj2_zb, 7) <= 2, 1, 0)
    HV5_tj3 = IF(MyTT.HHVBARS(sr最高价, 8) == 1, 1, 0)
    HV5_tj4 = IF(MyTT.LLVBARS(sr最低价, 8) >= 7, 1, 0)
    HV5 = IF(HV5_tj1 + HV5_tj2 + HV5_tj3 + HV5_tj4 + HV03 == 5, 1, 0)

    HV6_tj1 = IF(COUNT(HV00, 9) >= 3, 1, 0)
    HV6_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV6_tj2 = IF(COUNT(HV6_tj2_zb, 8) <= 3, 1, 0)
    HV6_tj3 = IF(MyTT.HHVBARS(sr最高价, 9) == 2, 1, 0)
    HV6_tj4 = IF(MyTT.LLVBARS(sr最低价, 9) >= 8, 1, 0)
    HV6 = IF(HV6_tj1 + HV6_tj2 + HV6_tj3 + HV6_tj4 + HV04 == 5, 1, 0)

    HV7_tj1 = IF(COUNT(HV00, 9) >= 3, 1, 0)
    HV7_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV7_tj2 = IF(COUNT(HV7_tj2_zb, 8) <= 3, 1, 0)
    HV7_tj3 = IF(MyTT.HHVBARS(sr最高价, 9) == 1, 1, 0)
    HV7_tj4 = IF(MyTT.LLVBARS(sr最低价, 9) >= 8, 1, 0)
    HV7 = IF(HV7_tj1 + HV7_tj2 + HV7_tj3 + HV7_tj4 + HV03 == 5, 1, 0)

    HV8_tj1 = IF(COUNT(HV00, 10) >= 3, 1, 0)
    HV8_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV8_tj2 = IF(COUNT(HV8_tj2_zb, 9) <= 4, 1, 0)
    HV8_tj3 = IF(MyTT.HHVBARS(sr最高价, 10) == 2, 1, 0)
    HV8_tj4 = IF(MyTT.LLVBARS(sr最低价, 10) >= 9, 1, 0)
    HV8 = IF(HV8_tj1 + HV8_tj2 + HV8_tj3 + HV8_tj4 + HV04 == 5, 1, 0)

    HV9_tj1 = IF(COUNT(HV00, 10) >= 3, 1, 0)
    HV9_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV9_tj2 = IF(COUNT(HV9_tj2_zb, 9) <= 4, 1, 0)
    HV9_tj3 = IF(MyTT.HHVBARS(sr最高价, 10) == 1, 1, 0)
    HV9_tj4 = IF(MyTT.LLVBARS(sr最低价, 10) >= 9, 1, 0)
    HV9 = IF(HV9_tj1 + HV9_tj2 + HV9_tj3 + HV9_tj4 + HV03 == 5, 1, 0)

    HV10_tj1 = IF(COUNT(HV00, 11) >= 3, 1, 0)
    HV10_tj2_zb = IF(HV01 + HV02 >= 1, 1, 0)
    HV10_tj2 = IF(COUNT(HV10_tj2_zb, 10) <= 5, 1, 0)
    HV10_tj3 = IF(MyTT.HHVBARS(sr最高价, 11) == 2, 1, 0)
    HV10_tj4 = IF(MyTT.LLVBARS(sr最低价, 11) >= 10, 1, 0)
    HV10 = IF(HV10_tj1 + HV10_tj2 + HV10_tj3 + HV10_tj4 + HV04 == 5, 1, 0)

    HXG = IF(HV1 + HV2 + HV3 + HV4 + HV5 + HV6 + HV7 + HV8 + HV9 + HV10 >= 1, 1, 0)

    底分型 = IF(XG + sqszzh_buy_jiedian >= 1, 1, 0)

    顶分型 = IF(HXG + sqszzh_sell_jiedian >= 1, 1, 0)

    前一个底分型wz = MY_BARSLAST(底分型, 1)
    底分型前1 = MYREF(sr最高价, 前一个底分型wz + 1)
    底分型前2 = MYREF(sr最高价, 前一个底分型wz + 2)
    底分型前0 = MYREF(sr最高价, 前一个底分型wz)
    max底分型前 = NthMaxList(1, 底分型前1, 底分型前2, 底分型前0)
    顶分型qr1_zb1 = IF(LLV(sr最低价, 3) > max底分型前, 1, 0)
    顶分型qr1 = IF(顶分型 + 顶分型qr1_zb1 == 2, 1, 0)

    前一个顶分型wz = MY_BARSLAST(顶分型, 1)
    顶分型前1 = MYREF(sr最低价, 前一个顶分型wz + 1)
    顶分型前2 = MYREF(sr最低价, 前一个顶分型wz + 2)
    顶分型前0 = MYREF(sr最低价, 前一个顶分型wz)
    min顶分型前 = NthMaxList(1, 顶分型前1, 顶分型前2, 顶分型前0)
    底分型qr1_zb1 = IF(HHV(sr最高价, 3) < min顶分型前, 1, 0)
    底分型qr1 = IF(底分型 + 底分型qr1_zb1 == 2, 1, 0)

    maxclose = NthMaxList(1, (sr收盘价 + sr最高价) / 2, (REF(sr收盘价, 1) + REF(sr最高价, 1)) / 2)
    minclose = NthMinList(1, (sr收盘价 + sr最低价) / 2, (REF(sr收盘价, 1) + REF(sr最低价, 1)) / 2)

    dfxwz = MY_BARSLAST(底分型, 1)
    ref_dfx_q2_high = MYREF(maxclose, dfxwz + 2)
    ref_dfx_q1_high = MYREF(maxclose, dfxwz + 1)
    max_ref_dfx_high = NthMaxList(1, ref_dfx_q2_high, ref_dfx_q1_high)
    底分型qr_低滤tj1 = IF(底分型 != 1, 1, 0)
    底分型qr_低滤tj2 = IF(EXIST(底分型, 4), 1, 0)
    底分型qr_低滤tj3 = IF(sr收盘价 > max_ref_dfx_high, 1, 0)
    底分型qr_低滤tja = IF(底分型qr_低滤tj1 + 底分型qr_低滤tj2 + 底分型qr_低滤tj3 == 3, 1, 0)
    底分型qr_低滤_zb1 = IF(底分型qr_低滤tja == 1, 1, 0)
    底分型qr_低滤_zb2 = IF(REF(底分型qr_低滤tja, 1) != 1, 1, 0)
    底分型qr_低滤_zb3 = IF(REF(底分型qr_低滤tja, 2) != 1, 1, 0)
    底分型qr_低滤_zb4 = IF(REF(底分型qr_低滤tja, 3) != 1, 1, 0)
    底分型qr_低滤 = IF(底分型qr_低滤_zb1 + 底分型qr_低滤_zb2 + 底分型qr_低滤_zb3 + 底分型qr_低滤_zb4 == 4, 1, 0)

    topfxwz = MY_BARSLAST(顶分型, 1)
    顶分型前2最低 = MYREF(maxclose, topfxwz + 2)
    顶分型前1最低 = MYREF(maxclose, topfxwz + 1)
    顶分型前最低 = NthMinList(1, 顶分型前2最低, 顶分型前1最低)
    顶分型qr_低滤tja1 = IF(顶分型 != 1, 1, 0)
    顶分型qr_低滤tja2 = IF(EXIST(顶分型, 4), 1, 0)
    顶分型qr_低滤tja3 = IF(sr收盘价 < 顶分型前最低, 1, 0)
    顶分型qr_低滤tja = IF(顶分型qr_低滤tja1 + 顶分型qr_低滤tja2 + 顶分型qr_低滤tja3 == 3, 1, 0)
    顶分型qr_低滤_zb1 = IF(顶分型qr_低滤tja == 1, 1, 0)
    顶分型qr_低滤_zb2 = IF(REF(顶分型qr_低滤tja, 1) != 1, 1, 0)
    顶分型qr_低滤_zb3 = IF(REF(顶分型qr_低滤tja, 2) != 1, 1, 0)
    顶分型qr_低滤_zb4 = IF(REF(顶分型qr_低滤tja, 3) != 1, 1, 0)
    顶分型qr_低滤 = IF(顶分型qr_低滤_zb1 + 顶分型qr_低滤_zb2 + 顶分型qr_低滤_zb3 + 顶分型qr_低滤_zb4 == 4, 1, 0)
    xm = 10
    x最高价 = df['high']
    x最低价 = df['low']
    x收盘价 = df['close']
    x最低价 = df['low']
    xTR1 = MAX(MAX((x最高价 - x最低价), ABS(REF(x收盘价, 4) - x最高价)), ABS(REF(x收盘价, 4) - x最低价))
    xATR1 = EMA(xTR1, xm)
    空趋势 = IF(EXIST(REF(sr收盘价, 1) < (max底分型前 - xATR1 * 0.618), 7), 1, 0)

    多趋势 = IF(EXIST(REF(sr收盘价, 1) > (min顶分型前 + xATR1 * 0.618), 7), 1, 0)

    多点1 = IF(EVERY(REF(sr收盘价, 1) > REF(max底分型前, 1), 3), 1, 0)
    多点2 = IF(EXIST(底分型qr_低滤, 4), 1, 0)
    多点 = IF(多点1 + 多点2 == 2, 1, 0)

    空点1 = IF(REF(sr收盘价, 1) < REF(min顶分型前, 1), 1, 0)
    空点2 = IF(EXIST(顶分型qr_低滤, 4), 1, 0)
    空点 = IF(空点1 + 空点2 == 2, 1, 0)

    return 底分型qr_低滤, 顶分型qr_低滤, 底分型, 顶分型, 空趋势, 多趋势, 多点, 空点


def ylzcqs(df):
    指导价 = EMA(df['close'], 6)
    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) != 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL == 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) != 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL == 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr

    sqszzh_sell_jiedian = IF(sqsz_9_gaopao == 1, 1, 0)
    sqszzh_buy_jiedian = IF(sqsz_9_dixi == 1, 1, 0)

    sqszzh_gjd_jiedian = IF(sqszzh_sell_jiedian + sqszzh_buy_jiedian >= 1, 1, 0)

    BarsLast_ssqszzh_gjd_jiedian_wz = MY_BARSLAST(sqszzh_gjd_jiedian == 1, 1)  # 上一次关键点wz
    x最高价 = HHV(df['high'], 4)
    x最低价 = LLV(df['low'], 4)
    x收盘价 = df['close']
    x开盘价 = REF(df['close'], 4)
    xm = 26
    xTR1 = MAX(MAX((x最高价 - x最低价), ABS(REF(x收盘价, 4) - x最高价)), ABS(REF(x收盘价, 4) - x最低价))
    xATR1 = EMA(xTR1, xm)

    下关键线 = MYREF(MA(LLV(df['high'], 20), 20), BarsLast_ssqszzh_gjd_jiedian_wz)
    下盈 = (HHV(下关键线, 20))

    上关键线 = MYREF(MA(HHV(df['low'], 20), 20), BarsLast_ssqszzh_gjd_jiedian_wz)
    上盈 = (LLV(上关键线, 20))
    # print('下关键线',下关键线)
    # 价格的波段率
    bs = 1
    bdl_a = ((HHV(df['high'], 39 * bs) - LLV(df['low'], 39 * bs)) / 39 * bs) * 10000
    bdl_b = (HHV(df['high'], 24 * bs) - LLV(df['low'], 24 * bs)) / 24 * bs * 10000
    bdl_c = (HHV(df['high'], 71 * bs) - LLV(df['low'], 71 * bs)) / 71 * bs * 10000
    bdl_d = (HHV(df['high'], 44 * bs) - LLV(df['low'], 44 * bs)) / 44 * bs * 10000
    bdl_e = (HHV(df['high'], 66 * bs) - LLV(df['low'], 66 * bs)) / 66 * bs * 10000
    bdl_f = (HHV(df['high'], 99 * bs) - LLV(df['low'], 99 * bs)) / 99 * bs * 10000
    bdl_bz = bdl_a * 1000 / bdl_b * 1000 / bdl_c * 1000 / bdl_d * 1000 / bdl_e * 1000 / bdl_f * 1000
    # 最大最小值归一化
    bdl_bz = (bdl_bz - np.nanmin(bdl_bz)) / (np.nanmax(bdl_bz) - np.nanmin(bdl_bz))
    bdl_bz_ema = EMA(bdl_bz, 60)

    bdl_波动率_pj, barpos = calculate_avg_and_positions(bdl_bz_ema)
    bdl_波动率_b2 = bdl_bz_ema - REF(bdl_bz_ema, 20)
    bdl_波动率_b2[bdl_波动率_b2 == 0] = 1e-8  # 判断并将分母为零的值赋为1e-8
    bdl_波动率_a2 = 20 * bdl_波动率_pj
    bdl_波动率_jiaodu_c2 = 90 - (np.arctan(bdl_波动率_a2 / bdl_波动率_b2) * 57.29578)
    bdl_波动率_jiaodu_cqr2 = IF(bdl_波动率_jiaodu_c2 > 90, (180 - bdl_波动率_jiaodu_c2) * -1, bdl_波动率_jiaodu_c2)
    小角度cqr = EMA(bdl_波动率_jiaodu_cqr2, 20)

    小角度cqr小于0节点tj1 = IF(小角度cqr < 0, 1, 0)
    小角度cqr小于0节点tj2 = IF(REF(小角度cqr, 1) >= 0, 1, 0)
    小角度cqr小于0节点 = IF(小角度cqr小于0节点tj1 + 小角度cqr小于0节点tj2 == 2, 1, 0)
    小角度cqrxz_tj1 = IF(EVERY(小角度cqr < 0, 4), 1, 0)
    小角度cqrxz_tj2 = IF(EXIST(小角度cqr小于0节点 == 1, 4), 1, 0)
    小角度cqrxz = IF(小角度cqrxz_tj1 + 小角度cqrxz_tj2 == 2, 1, 0)

    上限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) + 1 * xATR1
    下限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) - 1 * xATR1

    a_tj1 = IF(df['high'] < x最高价, 1, 0)
    a_tj2 = IF(df['low'] > x最低价, 1, 0)
    a_tj3 = IF(NthMaxList(1, df['open'], df['close']) < NthMaxList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a_tj4 = IF(NthMinList(1, df['open'], df['close']) > NthMinList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a = IF(a_tj1 + a_tj2 + a_tj3 + a_tj4 == 4, 1, 0)
    a_wz = MY_BARSLAST(a, 1)
    yali = NthMaxList(1, MYREF(df['high'], a_wz), MYREF(df['high'], a_wz + 1), MYREF(df['high'], a_wz + 2),
                      MYREF(df['high'], a_wz + 3))
    zicheng = NthMinList(1, MYREF(df['low'], a_wz), MYREF(df['low'], a_wz + 1), MYREF(df['low'], a_wz + 2),
                         MYREF(df['low'], a_wz + 3))
    junx2 = EMA((上限 + 上盈 + EMA(yali, 60)) / 3, 60)
    junx2b = EMA((下限 + 下盈 + EMA(zicheng, 60)) / 3, 60)
    # junxa = ((junx2 + HHV(df['high'], 60)) / 2+EMA(df['close'],60))/2
    junxa = (junx2 + HHV(df['high'], 60)) / 2
    junxb = (junx2 + LLV(df['low'], 60)) / 2
    return junx2, junx2b, junxa, junxb, 指导价
def kdj(df,kdj_bs):
    # 生成KDJ指标
    kdjn = 9 * kdj_bs
    kdjp1 = 3 * kdj_bs
    kdjp2 = 3 * kdj_bs
    RSV = (df['close'] - LLV(df['low'], kdjn)) / (HHV(df['high'], kdjn) - LLV(df['low'], kdjn)) * 100
    K = SMA(RSV, kdjp1, 1)
    D = SMA(K, kdjp2, 1)
    J = 3 * K - 2 * D
    return K,D,J
def bt_RSI(df,N):
    LC = REF(df['close'], 1)
    bt_RSI =SMA(MAX(df['close']-LC,0),N,1)/SMA(ABS(df['close']-LC),N,1)*100
    return bt_RSI


def kdj_ddbl(db_path, table_name, code, limit_num, ns):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']
    # print(df)

    # 神奇数字算法
    # 价买13
    # 算压力支撑趋势
    junx2, junx2b, junxa, junxb, 指导价 = ylzcqs(df)

    # kdj背离
    kdj_ns = ns
    kdjn = 9 * kdj_ns
    kdjp1 = 3 * kdj_ns
    kdjp2 = 3 * kdj_ns
    RSV = (df['close'] - LLV(df['low'], kdjn)) / (HHV(df['high'], kdjn) - LLV(df['low'], kdjn)) * 100
    K = SMA(RSV, kdjp1, 1)
    D = SMA(K, kdjp2, 1)
    J = 3 * K - 2 * D
    df['K'] = K
    df['D'] = D
    df['J'] = J
    指导价_zb = df['K']
    卖点, 买点 = gaopao_dix_gjd_all(指导价_zb)
    # print(卖点,买点)

    关键点吸tj1 = IF(买点 != 1, 1, 0)
    关键点吸tj2 = IF(REF(买点, 1) == 1, 1, 0)
    关键点吸 = IF(关键点吸tj1 + 关键点吸tj2 == 2, 1, 0)
    关键点抛tj1 = IF(卖点 != 1, 1, 0)
    关键点抛tj2 = IF(REF(卖点, 1) == 1, 1, 0)
    关键点抛 = IF(关键点抛tj1 + 关键点抛tj2 == 2, 1, 0)

    上一次高抛wz = BARSLAST(关键点抛)
    上一次点吸wz = BARSLAST(关键点吸)

    有效低吸tj1 = IF(关键点吸 == 1, 1, 0)
    有效低吸tj2 = IF(REF(上一次点吸wz, 1) > 上一次高抛wz, 1, 0)
    有效低吸 = IF(有效低吸tj1 + 有效低吸tj2 == 2, 1, 0)
    # print(有效低吸)
    有效高抛tj1 = IF(关键点抛 == 1, 1, 0)
    有效高抛tj2 = IF(REF(上一次高抛wz, 1) > 上一次点吸wz, 1, 0)
    有效高抛 = IF(有效高抛tj1 + 有效高抛tj2 == 2, 1, 0)
    # print(有效高抛)
    上一次有效高抛wz = BARSLAST(有效高抛)
    上一次有效低吸wz = BARSLAST(有效低吸)
    有效计算距离 = NthMaxList(1, 上一次有效高抛wz, 上一次有效低吸wz)

    平滑k = df['K']

    k拐下A_tj1 = IF(平滑k < REF(平滑k, 1), 1, 0)
    k拐下A_tj2 = IF(REF(平滑k, 1) >= REF(平滑k, 2), 1, 0)
    k拐下A = IF(k拐下A_tj1 + k拐下A_tj2 == 2, 1, 0)
    k拐下AA = IF(EXIST(k拐下A, 4), 1, 0)
    k拐下B = IF(关键点抛 == 1, 1, 0)
    k拐下BB = IF(EXIST(k拐下B, 4), 1, 0)
    k拐下 = IF(k拐下AA + k拐下BB == 2, 1, 0)

    k拐上A_tj1 = IF(平滑k > REF(平滑k, 1), 1, 0)
    k拐上A_tj2 = IF(REF(平滑k, 1) <= REF(平滑k, 2), 1, 0)
    k拐上A = IF(k拐上A_tj1 + k拐上A_tj2 == 2, 1, 0)
    k拐上AA = IF(EXIST(k拐上A, 4), 1, 0)
    k拐上B = IF(关键点吸 == 1, 1, 0)
    k拐上BB = IF(EXIST(k拐上B, 4), 1, 0)
    k拐上 = IF(k拐上AA + k拐上BB == 2, 1, 0)

    平滑k_x = EMA(K, 7)

    k拐下_x_A_tj1 = IF(平滑k_x < REF(平滑k_x, 1), 1, 0)
    k拐下_x_A_tj2 = IF(REF(平滑k_x, 1) >= REF(平滑k_x, 2), 1, 0)
    k拐下_x_A = IF(k拐下_x_A_tj1 + k拐下_x_A_tj2 == 2, 1, 0)
    k拐下_x_AA = IF(EXIST(k拐下_x_A, 4), 1, 0)

    k拐下_x = k拐下_x_AA

    k拐上_x_A_tj1 = IF(平滑k_x > REF(平滑k_x, 1), 1, 0)
    k拐上_x_A_tj2 = IF(REF(平滑k_x, 1) <= REF(平滑k_x, 2), 1, 0)
    k拐上_x_A = IF(k拐上_x_A_tj1 + k拐上_x_A_tj2 == 2, 1, 0)
    k拐上_x_AA = IF(EXIST(k拐上_x_A, 4), 1, 0)
    k拐上_x = k拐上_x_AA

    近高_x = HHV(K, 21)
    远高_x = HHV(K, 60)
    近最高_x = IF(k拐下_x, 近高_x, 0)
    远最高_x = IF(k拐下_x, 远高_x, 0)
    顶背离zb_x = 近最高_x < 远最高_x
    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 == 2, 1, 0)

    持续高位发生_x = EXIST(COUNT(df['close'] > junxa, 40) > 30, 40)

    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x_tj3 = IF(持续高位发生_x, 1, 0)
    顶背离_x_tj4 = IF(EXIST(df['close'] > junxa, 5), 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 + 顶背离_x_tj3 + 顶背离_x_tj4 == 4, 1, 0)

    远高抛计算wz = IF(上一次有效高抛wz < 上一次有效低吸wz, MY_BARSLAST(有效高抛, 2), 上一次有效高抛wz)
    近最高 = IF(k拐下 == 1, MYHHV(K, 上一次有效低吸wz), 0)
    远最高 = IF(k拐下, MYHHV(K, 远高抛计算wz), 0)
    顶背离zb = 近最高 < 远最高 * 0.95
    持续高位发生 = EXIST(COUNT(df['close'] > junx2b, 40) > 30, 40)
    顶背离zb2_tj1 = IF(顶背离zb, 1, 0)
    顶背离zb2_tj2 = IF(REF(顶背离zb, 1) != 1, 1, 0)
    顶背离zb2_tj3 = IF(持续高位发生, 1, 0)
    顶背离zb2_tj4 = IF(EXIST(df['close'] > junx2, 5), 1, 0)

    顶背离zb2 = IF(顶背离zb2_tj1 + 顶背离zb2_tj2 + 顶背离zb2_tj3 + 顶背离zb2_tj4 == 4, 1, 0)

    顶背离 = IF(顶背离zb2 + 顶背离_x >= 1, 1, 0)  # 输出

    远低吸计算wz = IF(上一次有效低吸wz < 上一次有效高抛wz, MY_BARSLAST(有效低吸, 2), 上一次有效低吸wz)
    近最低 = IF(k拐上 == 1, MYLLV(K, 上一次有效高抛wz), 0)
    远最低 = IF(k拐上 == 1, MYLLV(K, 远低吸计算wz), 0)
    底背离zb = 近最低 > 远最低 * 1.05
    持续低位发生 = EXIST(COUNT(df['close'] < junx2b, 40) > 30, 40)

    底背离zb2_tj1 = IF(底背离zb, 1, 0)
    底背离zb2_tj2 = IF(REF(底背离zb, 1) != 1, 1, 0)
    底背离zb2_tj3 = IF(持续低位发生, 1, 0)
    底背离zb2_tj4 = IF(EXIST(df['close'] < junx2b, 5), 1, 0)
    底背离zb2 = IF(底背离zb2_tj1 + 底背离zb2_tj2 + 底背离zb2_tj3 + 底背离zb2_tj4 == 4, 1, 0)
    底背离 = IF(底背离zb2 == 1, 1, 0)
    # print(底背离)
    df['顶背离'] = 顶背离
    df['底背离'] = 底背离

    return 指导价, junx2, junx2b, junxa, junxb, 最高价_x, 最低价_x, 开盘价_x, 收盘价_x, 成交量_x, 顶背离, 底背离, df.index, df


def macd_ddbl(db_path, table_name, code, limit_num, ns):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']
    # print(df)
    # 算压力支撑趋势

    # 算压力支撑趋势
    junx2, junx2b, junxa, junxb, 指导价 = ylzcqs(df)
    # 主动买入
    # macd
    # 镜

    S = 12 * ns
    P = 26 * ns
    M = 9 * ns
    DIFF = EMA(df['close'], S) - EMA(df['close'], P)
    DEA = EMA(DIFF, M)
    MACD = 2 * (DIFF - DEA)

    MACD_zb = EMA(HHV(DIFF, 4), 4)
    # MACD_zb = DIFF
    指导价_zb = MACD_zb
    卖点, 买点 = gaopao_dix_gjd_all(指导价_zb)
    # print(卖点,买点)

    关键点吸tj1 = IF(买点 != 1, 1, 0)
    关键点吸tj2 = IF(REF(买点, 1) == 1, 1, 0)
    关键点吸 = IF(关键点吸tj1 + 关键点吸tj2 == 2, 1, 0)
    关键点抛tj1 = IF(卖点 != 1, 1, 0)
    关键点抛tj2 = IF(REF(卖点, 1) == 1, 1, 0)
    关键点抛 = IF(关键点抛tj1 + 关键点抛tj2 == 2, 1, 0)

    上一次高抛wz = BARSLAST(关键点抛)
    上一次点吸wz = BARSLAST(关键点吸)

    有效低吸tj1 = IF(关键点吸 == 1, 1, 0)
    有效低吸tj2 = IF(REF(上一次点吸wz, 1) > 上一次高抛wz, 1, 0)
    有效低吸 = IF(有效低吸tj1 + 有效低吸tj2 == 2, 1, 0)
    # print(有效低吸)
    有效高抛tj1 = IF(关键点抛 == 1, 1, 0)
    有效高抛tj2 = IF(REF(上一次高抛wz, 1) > 上一次点吸wz, 1, 0)
    有效高抛 = IF(有效高抛tj1 + 有效高抛tj2 == 2, 1, 0)
    # print(有效高抛)
    上一次有效高抛wz = BARSLAST(有效高抛)
    上一次有效低吸wz = BARSLAST(有效低吸)
    有效计算距离 = NthMaxList(1, 上一次有效高抛wz, 上一次有效低吸wz)

    平滑k = 指导价_zb

    k拐下A_tj1 = IF(平滑k < REF(平滑k, 1), 1, 0)
    k拐下A_tj2 = IF(REF(平滑k, 1) >= REF(平滑k, 2), 1, 0)
    k拐下A = IF(k拐下A_tj1 + k拐下A_tj2 == 2, 1, 0)
    k拐下AA = IF(EXIST(k拐下A, 4), 1, 0)
    k拐下B = IF(关键点抛 == 1, 1, 0)
    k拐下BB = IF(EXIST(k拐下B, 4), 1, 0)
    k拐下 = IF(k拐下AA + k拐下BB == 2, 1, 0)

    k拐上A_tj1 = IF(平滑k > REF(平滑k, 1), 1, 0)
    k拐上A_tj2 = IF(REF(平滑k, 1) <= REF(平滑k, 2), 1, 0)
    k拐上A = IF(k拐上A_tj1 + k拐上A_tj2 == 2, 1, 0)
    k拐上AA = IF(EXIST(k拐上A, 4), 1, 0)
    k拐上B = IF(关键点吸 == 1, 1, 0)
    k拐上BB = IF(EXIST(k拐上B, 4), 1, 0)
    k拐上 = IF(k拐上AA + k拐上BB == 2, 1, 0)

    平滑k_x = EMA(指导价_zb, 7)

    k拐下_x_A_tj1 = IF(平滑k_x < REF(平滑k_x, 1), 1, 0)
    k拐下_x_A_tj2 = IF(REF(平滑k_x, 1) >= REF(平滑k_x, 2), 1, 0)
    k拐下_x_A = IF(k拐下_x_A_tj1 + k拐下_x_A_tj2 == 2, 1, 0)
    k拐下_x_AA = IF(EXIST(k拐下_x_A, 4), 1, 0)

    k拐下_x = k拐下_x_AA

    k拐上_x_A_tj1 = IF(平滑k_x > REF(平滑k_x, 1), 1, 0)
    k拐上_x_A_tj2 = IF(REF(平滑k_x, 1) <= REF(平滑k_x, 2), 1, 0)
    k拐上_x_A = IF(k拐上_x_A_tj1 + k拐上_x_A_tj2 == 2, 1, 0)
    k拐上_x_AA = IF(EXIST(k拐上_x_A, 4), 1, 0)
    k拐上_x = k拐上_x_AA

    近高_x = HHV(指导价_zb, 21)
    远高_x = HHV(指导价_zb, 60)
    近最高_x = IF(k拐下_x, 近高_x, 0)
    远最高_x = IF(k拐下_x, 远高_x, 0)
    顶背离zb_x = 近最高_x < 远最高_x
    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 == 2, 1, 0)

    持续高位发生_x = EXIST(COUNT(df['close'] > junxa, 40) > 30, 40)

    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x_tj3 = IF(持续高位发生_x, 1, 0)
    顶背离_x_tj4 = IF(EXIST(df['close'] > junxa, 5), 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 + 顶背离_x_tj3 + 顶背离_x_tj4 == 4, 1, 0)

    远高抛计算wz = IF(上一次有效高抛wz < 上一次有效低吸wz, MY_BARSLAST(有效高抛, 2), 上一次有效高抛wz)
    近最高 = IF(k拐下 == 1, MYHHV(指导价_zb, 上一次有效低吸wz), 0)
    远最高 = IF(k拐下, MYHHV(指导价_zb, 远高抛计算wz), 0)
    顶背离zb = 近最高 < 远最高 * 0.95
    持续高位发生 = EXIST(COUNT(df['close'] > junx2b, 40) > 30, 40)
    顶背离zb2_tj1 = IF(顶背离zb, 1, 0)
    顶背离zb2_tj2 = IF(REF(顶背离zb, 1) != 1, 1, 0)
    顶背离zb2_tj3 = IF(持续高位发生, 1, 0)
    顶背离zb2_tj4 = IF(EXIST(df['close'] > junx2, 5), 1, 0)

    顶背离zb2 = IF(顶背离zb2_tj1 + 顶背离zb2_tj2 + 顶背离zb2_tj3 + 顶背离zb2_tj4 == 4, 1, 0)

    顶背离 = IF(顶背离zb2 + 顶背离_x >= 1, 1, 0)  # 输出

    远低吸计算wz = IF(上一次有效低吸wz < 上一次有效高抛wz, MY_BARSLAST(有效低吸, 2), 上一次有效低吸wz)
    近最低 = IF(k拐上 == 1, MYLLV(指导价_zb, 上一次有效高抛wz), 0)
    远最低 = IF(k拐上 == 1, MYLLV(指导价_zb, 远低吸计算wz), 0)
    底背离zb = 近最低 > 远最低 * 1.05
    持续低位发生 = EXIST(COUNT(df['close'] < junx2b, 40) > 30, 40)

    底背离zb2_tj1 = IF(底背离zb, 1, 0)
    底背离zb2_tj2 = IF(REF(底背离zb, 1) != 1, 1, 0)
    底背离zb2_tj3 = IF(持续低位发生, 1, 0)
    底背离zb2_tj4 = IF(EXIST(df['close'] < junx2b, 5), 1, 0)
    底背离zb2 = IF(底背离zb2_tj1 + 底背离zb2_tj2 + 底背离zb2_tj3 + 底背离zb2_tj4 == 4, 1, 0)
    底背离 = IF(底背离zb2 == 1, 1, 0)
    # print(底背离)
    df['顶背离'] = 顶背离
    df['底背离'] = 底背离
    # values_to_write = [顶背离, 底背离, K, 近高_x, 远高_x]
    # for i, (value1, value2, value3, value4, value5) in enumerate(zip(*values_to_write)):  # 要输出的数据变量。
    #     ini_file_time = df.index[i]
    #     write_ini_file_x(value1, value2, value3, value4, value5, i, ini_file_time.strftime('%Y%m%d%H%M%S'))

    return 顶背离, 底背离, df.index


def zdmr_ddbl(db_path, table_name, code, limit_num, ns):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']
    # print(df)
    # 算压力支撑趋势
    junx2, junx2b, junxa, junxb, 指导价 = ylzcqs(df)

    # 主动买入
    # 动量 主动买入形成趋势分时
    # 镜

    jing_sss = 4
    jing_zqbs = 1
    jing_high = df['high']
    jing_low = df['low']
    jing_close = df['close']
    jing_open = df['open']
    jing_vol = df['vol']
    jing_oop = 1
    jing_bs = 1 * ns

    jing_pjj = (jing_close + jing_high + jing_low + jing_open) / 4
    jing_suducha = jing_pjj - REF(jing_pjj, 1)
    # IF(S,A,B)
    jing_zhubuy = IF(jing_suducha > 0, jing_suducha, 0) * jing_vol
    jing_zhusell = IF(jing_suducha < 0, jing_suducha, 0) * jing_vol

    jing_zhubuy_15 = SUM(ABS(jing_zhubuy), 1 * jing_oop * jing_bs)
    jing_zhusell_15 = SUM(ABS(jing_zhusell), 1 * jing_oop * jing_bs)
    jing_zhubuy_20 = SUM(ABS(jing_zhubuy), 2 * jing_oop * jing_bs)
    jing_zhusell_20 = SUM(ABS(jing_zhusell), 2 * jing_oop * jing_bs)
    jing_zhubuy_40 = SUM(ABS(jing_zhubuy), 3 * jing_oop * jing_bs)
    jing_zhusell_40 = SUM(ABS(jing_zhusell), 3 * jing_oop * jing_bs)
    jing_zhubuy_80 = SUM(ABS(jing_zhubuy), 6 * jing_oop * jing_bs)
    jing_zhusell_80 = SUM(ABS(jing_zhusell), 6 * jing_oop * jing_bs)
    jing_zhubuy_100 = SUM(ABS(jing_zhubuy), 4 * jing_oop * jing_bs)
    jing_zhusell_100 = SUM(ABS(jing_zhusell), 4 * jing_oop * jing_bs)
    jing_zhubuy_120 = SUM(ABS(jing_zhubuy), 8 * jing_oop * jing_bs)
    jing_zhusell_120 = SUM(ABS(jing_zhusell), 8 * jing_oop * jing_bs)
    jing_zhubuy_140 = SUM(ABS(jing_zhubuy), 10 * jing_oop * jing_bs)
    jing_zhusell_140 = SUM(ABS(jing_zhusell), 10 * jing_oop * jing_bs)
    jing_zhubuy_160 = SUM(ABS(jing_zhubuy), 12 * jing_oop * jing_bs)
    jing_zhusell_160 = SUM(ABS(jing_zhusell), 12 * jing_oop * jing_bs)
    jing_zhubuy_180 = SUM(ABS(jing_zhubuy), 15 * jing_oop * jing_bs)
    jing_zhusell_180 = SUM(ABS(jing_zhusell), 15 * jing_oop * jing_bs)

    jing_zhubuy_HJ = (
                             jing_zhubuy_15 + jing_zhubuy_20 + jing_zhubuy_40 + jing_zhubuy_80 + jing_zhubuy_100 + jing_zhubuy_120 + jing_zhubuy_140 + jing_zhubuy_160 + jing_zhubuy_180) / 9
    jing_zhusel_HJ = (
                             jing_zhusell_15 + jing_zhusell_20 + jing_zhusell_40 + jing_zhusell_80 + jing_zhusell_100 + jing_zhusell_120 + jing_zhusell_140 + jing_zhusell_160 + jing_zhusell_180) / 9
    jing_zhudong_cha = (jing_zhubuy_HJ - jing_zhusel_HJ)  # 粉小英线大中粉小主动差
    jing_zhudong_cha_pjzdc = EMA(jing_zhudong_cha, jing_sss)  # 粉小英线大中粉小主动差

    # 片
    pian_sss = 4
    pian_zqbs = 1
    pian_high = df['high']
    pian_low = df['low']
    pian_close = df['close']
    pian_open = df['open']
    pian_vol = df['vol']
    pian_oop = 1
    pian_bs = 1 * ns

    # 在 pian_VAR1 的计算中加入1e-8在计算 pian_VAR1 之前对分母进行判断，如果为零则将分母赋值为一个极小值（例如  1e-8 ），避免除数为零的情况。
    pian_VAR1 = pian_vol / ((pian_high - pian_low) * 2 - ABS(pian_close - pian_open) + 1e-8)
    # pian_buy_zb = IF(pian_close>pian_open,pian_VAR1*(pian_high-pian_low),IF(pian_close<pian_open,pian_VAR1*((pian_high-pian_open)+(pian_close-pian_low)),pian_vol/2))
    pian_zhubuy = IF(np.isnan(pian_VAR1), 0, IF(pian_close > pian_open, pian_VAR1 * (pian_high - pian_low),
                                                IF(pian_close < pian_open,
                                                   pian_VAR1 * ((pian_high - pian_open) + (pian_close - pian_low)),
                                                   pian_vol / 2)))
    # pian_sell_zb=IF(pian_close>pian_open,0-pian_VAR1*((pian_high-pian_close)+(pian_open-pian_low)),IF(pian_close<pian_open,0-pian_VAR1*(pian_high-pian_low),0-pian_vol/2))
    pian_zhusell = IF(np.isnan(pian_VAR1), 0,
                      IF(pian_close > pian_open, 0 - pian_VAR1 * ((pian_high - pian_close) + (pian_open - pian_low)),
                         IF(pian_close < pian_open, 0 - pian_VAR1 * (pian_high - pian_low), 0 - pian_vol / 2)))

    pian_zhubuy_15 = SUM(ABS(pian_zhubuy), 1 * pian_oop * pian_bs)
    pian_zhusell_15 = SUM(ABS(pian_zhusell), 1 * pian_oop * pian_bs)
    pian_zhubuy_20 = SUM(ABS(pian_zhubuy), 2 * pian_oop * pian_bs)
    pian_zhusell_20 = SUM(ABS(pian_zhusell), 2 * pian_oop * pian_bs)
    pian_zhubuy_40 = SUM(ABS(pian_zhubuy), 3 * pian_oop * pian_bs)
    pian_zhusell_40 = SUM(ABS(pian_zhusell), 3 * pian_oop * pian_bs)
    pian_zhubuy_80 = SUM(ABS(pian_zhubuy), 6 * pian_oop * pian_bs)
    pian_zhusell_80 = SUM(ABS(pian_zhusell), 6 * pian_oop * pian_bs)
    pian_zhubuy_100 = SUM(ABS(pian_zhubuy), 4 * pian_oop * pian_bs)
    pian_zhusell_100 = SUM(ABS(pian_zhusell), 4 * pian_oop * pian_bs)
    pian_zhubuy_120 = SUM(ABS(pian_zhubuy), 8 * pian_oop * pian_bs)
    pian_zhusell_120 = SUM(ABS(pian_zhusell), 8 * pian_oop * pian_bs)
    pian_zhubuy_140 = SUM(ABS(pian_zhubuy), 10 * pian_oop * pian_bs)
    pian_zhusell_140 = SUM(ABS(pian_zhusell), 10 * pian_oop * pian_bs)
    pian_zhubuy_160 = SUM(ABS(pian_zhubuy), 12 * pian_oop * pian_bs)
    pian_zhusell_160 = SUM(ABS(pian_zhusell), 12 * pian_oop * pian_bs)
    pian_zhubuy_180 = SUM(ABS(pian_zhubuy), 15 * pian_oop * pian_bs)
    pian_zhusell_180 = SUM(ABS(pian_zhusell), 15 * pian_oop * pian_bs)

    pian_zhubuy_HJ = (
                             pian_zhubuy_15 + pian_zhubuy_20 + pian_zhubuy_40 + pian_zhubuy_80 + pian_zhubuy_100 + pian_zhubuy_120 + pian_zhubuy_140 + pian_zhubuy_160 + pian_zhubuy_180) / 9
    pian_zhusel_HJ = (
                             pian_zhusell_15 + pian_zhusell_20 + pian_zhusell_40 + pian_zhusell_80 + pian_zhusell_100 + pian_zhusell_120 + pian_zhusell_140 + pian_zhusell_160 + pian_zhusell_180) / 9
    pian_zhudong_cha = (pian_zhubuy_HJ - pian_zhusel_HJ)  # 粉小英线大中粉小主动差
    pian_zhudong_cha_pjzdc = EMA(pian_zhudong_cha, pian_sss)  # 粉小英线大中粉小主动差

    # 防
    fang_sss = 4
    fang_zqbs = 1
    fang_high = df['high']
    fang_low = df['low']
    fang_close = df['close']
    fang_open = df['open']
    fang_vol = df['vol'] / 2
    fang_oop = 1
    fang_bs = 1 * ns

    fang_xiaoqian_up = fang_close > REF(fang_close, 1)
    fang_xiaoqian_down = fang_close < REF(fang_close, 1)
    fang_xiaoqian_bfw1_tj1 = IF(REF(fang_xiaoqian_down, 1) != 1, 1, 0)
    fang_xiaoqian_bfw1_tj2 = IF(fang_xiaoqian_down == 1, 1, 0)
    fang_xiaoqian_bfw1_tj3 = IF(fang_xiaoqian_bfw1_tj1 + fang_xiaoqian_bfw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bfw1 = MY_BARSLAST(fang_xiaoqian_bfw1_tj3 == 1, 1) + 1

    fang_xiaoqian_bgw1_tj1 = IF(REF(fang_xiaoqian_up, 1) != 1, 1, 0)
    fang_xiaoqian_bgw1_tj2 = IF(fang_xiaoqian_up == 1, 1, 0)
    fang_xiaoqian_bgw1_tj3 = IF(fang_xiaoqian_bgw1_tj1 + fang_xiaoqian_bgw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bgw1 = MY_BARSLAST(fang_xiaoqian_bgw1_tj3 == 1, 1) + 1
    fang_xiaoqian_up_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bgw1)
    fang_xiaoqian_down_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bfw1)

    fang_xiaoqian_xxx = IF(fang_xiaoqian_up == 1, fang_xiaoqian_up_jiliang, fang_xiaoqian_down_jiliang)
    fang_xiaoqian_gongji = IF(fang_xiaoqian_down, fang_xiaoqian_xxx, 0)
    fang_xiaoqian_xuqiu = IF(fang_xiaoqian_up, fang_xiaoqian_xxx, 0)
    fang_zhubuy = fang_xiaoqian_xuqiu
    fang_zhusell = fang_xiaoqian_gongji

    fang_zhubuy_15 = SUM(ABS(fang_zhubuy), 1 * fang_oop * fang_bs)
    fang_zhusell_15 = SUM(ABS(fang_zhusell), 1 * fang_oop * fang_bs)
    fang_zhubuy_20 = SUM(ABS(fang_zhubuy), 2 * fang_oop * fang_bs)
    fang_zhusell_20 = SUM(ABS(fang_zhusell), 2 * fang_oop * fang_bs)
    fang_zhubuy_40 = SUM(ABS(fang_zhubuy), 3 * fang_oop * fang_bs)
    fang_zhusell_40 = SUM(ABS(fang_zhusell), 3 * fang_oop * fang_bs)
    fang_zhubuy_80 = SUM(ABS(fang_zhubuy), 6 * fang_oop * fang_bs)
    fang_zhusell_80 = SUM(ABS(fang_zhusell), 6 * fang_oop * fang_bs)
    fang_zhubuy_100 = SUM(ABS(fang_zhubuy), 4 * fang_oop * fang_bs)
    fang_zhusell_100 = SUM(ABS(fang_zhusell), 4 * fang_oop * fang_bs)
    fang_zhubuy_120 = SUM(ABS(fang_zhubuy), 8 * fang_oop * fang_bs)
    fang_zhusell_120 = SUM(ABS(fang_zhusell), 8 * fang_oop * fang_bs)
    fang_zhubuy_140 = SUM(ABS(fang_zhubuy), 10 * fang_oop * fang_bs)
    fang_zhusell_140 = SUM(ABS(fang_zhusell), 10 * fang_oop * fang_bs)
    fang_zhubuy_160 = SUM(ABS(fang_zhubuy), 12 * fang_oop * fang_bs)
    fang_zhusell_160 = SUM(ABS(fang_zhusell), 12 * fang_oop * fang_bs)
    fang_zhubuy_180 = SUM(ABS(fang_zhubuy), 15 * fang_oop * fang_bs)
    fang_zhusell_180 = SUM(ABS(fang_zhusell), 15 * fang_oop * fang_bs)
    fang_zhubuy_HJ = (
                             fang_zhubuy_15 + fang_zhubuy_20 + fang_zhubuy_40 + fang_zhubuy_80 + fang_zhubuy_100 + fang_zhubuy_120 + fang_zhubuy_140 + fang_zhubuy_160 + fang_zhubuy_180) / 9
    fang_zhusel_HJ = (
                             fang_zhusell_15 + fang_zhusell_20 + fang_zhusell_40 + fang_zhusell_80 + fang_zhusell_100 + fang_zhusell_120 + fang_zhusell_140 + fang_zhusell_160 + fang_zhusell_180) / 9
    fang_zhudong_cha = (fang_zhubuy_HJ - fang_zhusel_HJ)  # 粉小英线大中粉小主动差
    fang_zhudong_cha_pjzdc = EMA(fang_zhudong_cha, fang_sss)  # 粉小英线大中粉小主动差

    小合小pjzdc1x = (fang_zhubuy_HJ + pian_zhubuy_HJ + jing_zhubuy_HJ) / 3
    小合小pjzdc1 = (SUM(小合小pjzdc1x, 2) / 2 + SUM(小合小pjzdc1x, 4) / 4 + SUM(小合小pjzdc1x, 7) / 7) / 3

    小合小主动买入HJ = (fang_zhubuy_HJ + pian_zhubuy_HJ + jing_zhubuy_HJ) / 3
    小合小主动卖出HJ = (fang_zhusel_HJ + pian_zhusel_HJ + jing_zhusel_HJ) / 3
    QSsjbs = 14
    Ema_shi_zhubuy_HJ = MA(MA(MA(小合小主动买入HJ, 21 * QSsjbs), 13 * QSsjbs), 7 * QSsjbs)
    Ema_shi_zhubuy_HJx = MA(MA(MA(小合小主动买入HJ, 5 * QSsjbs), 5 * QSsjbs), 5 * QSsjbs)
    Ema_shi_zhusell_HJ = MA(MA(MA(小合小主动卖出HJ, 21 * QSsjbs), 13 * QSsjbs), 7 * QSsjbs)
    Ema_shi_zhusell_HJx = MA(MA(MA(小合小主动卖出HJ, 5 * QSsjbs), 5 * QSsjbs), 5 * QSsjbs)
    shi_zhudong_cha = (小合小主动买入HJ - 小合小主动卖出HJ)  # 粉小英线大中粉小主动差
    # print('shi_zhudong_bz:', [format(x, '.8f') for x in shi_zhudong_bz])
    shi_duotou_qiangshi1_tj1 = IF(小合小主动买入HJ > Ema_shi_zhubuy_HJx, 1, 0)
    shi_duotou_qiangshi1_tj2 = IF(小合小主动买入HJ > Ema_shi_zhubuy_HJ, 1, 0)
    shi_duotou_qiangshi1 = IF(shi_duotou_qiangshi1_tj1 + shi_duotou_qiangshi1_tj2 >= 1, 1, 0)
    shi_duotou_qiangshi_tj1 = IF(小合小主动买入HJ > 小合小主动卖出HJ, 1, 0)
    shi_duotou_qiangshi = IF(shi_duotou_qiangshi1 + shi_duotou_qiangshi_tj1 == 2, 1, 0)

    shi_kongtou_qiangshi1_tj1 = IF(小合小主动卖出HJ > Ema_shi_zhusell_HJx, 1, 0)
    shi_kongtou_qiangshi1_tj2 = IF(小合小主动卖出HJ > Ema_shi_zhusell_HJ, 1, 0)
    shi_kongtou_qiangshi1 = IF(shi_kongtou_qiangshi1_tj1 + shi_kongtou_qiangshi1_tj2 >= 1, 1, 0)
    shi_kongtou_qiangshi_tj1 = IF(小合小主动卖出HJ > 小合小主动买入HJ, 1, 0)
    shi_kongtou_qiangshi = IF(shi_kongtou_qiangshi1 + shi_kongtou_qiangshi_tj1 == 2, 1, 0)

    小合平均小主动差1 = MA(小合小pjzdc1, 3 * QSsjbs)
    小合平均小主动差2 = MA(小合小pjzdc1, 5 * QSsjbs)

    shi_buchong_best_duo1_tj1 = IF(小合平均小主动差1 > REF(小合平均小主动差1, 1), 1, 0)
    shi_buchong_best_duo1_tj2 = IF(小合平均小主动差1 > REF(小合平均小主动差1, 2), 1, 0)
    shi_buchong_best_duo1_tj3 = IF(小合平均小主动差2 > REF(小合平均小主动差2, 1), 1, 0)
    shi_buchong_best_duo1_tj4 = IF(小合平均小主动差2 > REF(小合平均小主动差2, 2), 1, 0)
    shi_buchong_best_duo1 = IF(
        shi_buchong_best_duo1_tj1 + shi_buchong_best_duo1_tj2 + shi_buchong_best_duo1_tj3 + shi_buchong_best_duo1_tj4 >= 1,
        1, 0)
    # 强势多
    shi_buchong_best_duo = IF(shi_buchong_best_duo1 + shi_duotou_qiangshi == 2, 1, 0)

    shi_buchong_best_kong1_tj1 = IF(小合平均小主动差1 < REF(小合平均小主动差1, 1), 1, 0)
    shi_buchong_best_kong1_tj2 = IF(小合平均小主动差1 < REF(小合平均小主动差1, 2), 1, 0)
    shi_buchong_best_kong1_tj3 = IF(小合平均小主动差2 < REF(小合平均小主动差2, 1), 1, 0)
    shi_buchong_best_kong1_tj4 = IF(小合平均小主动差2 < REF(小合平均小主动差2, 2), 1, 0)
    shi_buchong_best_kong1 = IF(
        shi_buchong_best_kong1_tj1 + shi_buchong_best_kong1_tj2 + shi_buchong_best_kong1_tj3 + shi_buchong_best_kong1_tj4 >= 1,
        1, 0)
    # 强势空
    shi_buchong_best_kong = IF(shi_buchong_best_kong1 + shi_kongtou_qiangshi == 2, 1, 0)

    指导价_zb = 小合小pjzdc1
    卖点, 买点 = gaopao_dix_gjd_all(指导价_zb)
    # print(卖点,买点)

    关键点吸tj1 = IF(买点 != 1, 1, 0)
    关键点吸tj2 = IF(REF(买点, 1) == 1, 1, 0)
    关键点吸 = IF(关键点吸tj1 + 关键点吸tj2 == 2, 1, 0)
    关键点抛tj1 = IF(卖点 != 1, 1, 0)
    关键点抛tj2 = IF(REF(卖点, 1) == 1, 1, 0)
    关键点抛 = IF(关键点抛tj1 + 关键点抛tj2 == 2, 1, 0)

    上一次高抛wz = BARSLAST(关键点抛)
    上一次点吸wz = BARSLAST(关键点吸)

    有效低吸tj1 = IF(关键点吸 == 1, 1, 0)
    有效低吸tj2 = IF(REF(上一次点吸wz, 1) > 上一次高抛wz, 1, 0)
    有效低吸 = IF(有效低吸tj1 + 有效低吸tj2 == 2, 1, 0)
    # print(有效低吸)
    有效高抛tj1 = IF(关键点抛 == 1, 1, 0)
    有效高抛tj2 = IF(REF(上一次高抛wz, 1) > 上一次点吸wz, 1, 0)
    有效高抛 = IF(有效高抛tj1 + 有效高抛tj2 == 2, 1, 0)
    # print(有效高抛)
    上一次有效高抛wz = BARSLAST(有效高抛)
    上一次有效低吸wz = BARSLAST(有效低吸)
    有效计算距离 = NthMaxList(1, 上一次有效高抛wz, 上一次有效低吸wz)

    平滑k = 指导价_zb

    k拐下A_tj1 = IF(平滑k < REF(平滑k, 1), 1, 0)
    k拐下A_tj2 = IF(REF(平滑k, 1) >= REF(平滑k, 2), 1, 0)
    k拐下A = IF(k拐下A_tj1 + k拐下A_tj2 == 2, 1, 0)
    k拐下AA = IF(EXIST(k拐下A, 4), 1, 0)
    k拐下B = IF(关键点抛 == 1, 1, 0)
    k拐下BB = IF(EXIST(k拐下B, 4), 1, 0)
    k拐下 = IF(k拐下AA + k拐下BB == 2, 1, 0)

    k拐上A_tj1 = IF(平滑k > REF(平滑k, 1), 1, 0)
    k拐上A_tj2 = IF(REF(平滑k, 1) <= REF(平滑k, 2), 1, 0)
    k拐上A = IF(k拐上A_tj1 + k拐上A_tj2 == 2, 1, 0)
    k拐上AA = IF(EXIST(k拐上A, 4), 1, 0)
    k拐上B = IF(关键点吸 == 1, 1, 0)
    k拐上BB = IF(EXIST(k拐上B, 4), 1, 0)
    k拐上 = IF(k拐上AA + k拐上BB == 2, 1, 0)

    平滑k_x = EMA(指导价_zb, 7)

    k拐下_x_A_tj1 = IF(平滑k_x < REF(平滑k_x, 1), 1, 0)
    k拐下_x_A_tj2 = IF(REF(平滑k_x, 1) >= REF(平滑k_x, 2), 1, 0)
    k拐下_x_A = IF(k拐下_x_A_tj1 + k拐下_x_A_tj2 == 2, 1, 0)
    k拐下_x_AA = IF(EXIST(k拐下_x_A, 4), 1, 0)

    k拐下_x = k拐下_x_AA

    k拐上_x_A_tj1 = IF(平滑k_x > REF(平滑k_x, 1), 1, 0)
    k拐上_x_A_tj2 = IF(REF(平滑k_x, 1) <= REF(平滑k_x, 2), 1, 0)
    k拐上_x_A = IF(k拐上_x_A_tj1 + k拐上_x_A_tj2 == 2, 1, 0)
    k拐上_x_AA = IF(EXIST(k拐上_x_A, 4), 1, 0)
    k拐上_x = k拐上_x_AA

    近高_x = HHV(指导价_zb, 21)
    远高_x = HHV(指导价_zb, 60)
    近最高_x = IF(k拐下_x, 近高_x, 0)
    远最高_x = IF(k拐下_x, 远高_x, 0)
    顶背离zb_x = 近最高_x < 远最高_x
    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 == 2, 1, 0)

    持续高位发生_x = EXIST(COUNT(df['close'] > junxa, 40) > 30, 40)

    顶背离_x_tj1 = IF(顶背离zb_x, 1, 0)
    顶背离_x_tj2 = IF(REF(顶背离zb_x, 1) != 1, 1, 0)
    顶背离_x_tj3 = IF(持续高位发生_x, 1, 0)
    顶背离_x_tj4 = IF(EXIST(df['close'] > junxa, 5), 1, 0)
    顶背离_x = IF(顶背离_x_tj1 + 顶背离_x_tj2 + 顶背离_x_tj3 + 顶背离_x_tj4 == 4, 1, 0)

    远高抛计算wz = IF(上一次有效高抛wz < 上一次有效低吸wz, MY_BARSLAST(有效高抛, 2), 上一次有效高抛wz)
    近最高 = IF(k拐下 == 1, MYHHV(指导价_zb, 上一次有效低吸wz), 0)
    远最高 = IF(k拐下, MYHHV(指导价_zb, 远高抛计算wz), 0)
    顶背离zb = 近最高 < 远最高 * 0.95
    持续高位发生 = EXIST(COUNT(df['close'] > junx2b, 40) > 30, 40)
    顶背离zb2_tj1 = IF(顶背离zb, 1, 0)
    顶背离zb2_tj2 = IF(REF(顶背离zb, 1) != 1, 1, 0)
    顶背离zb2_tj3 = IF(持续高位发生, 1, 0)
    顶背离zb2_tj4 = IF(EXIST(df['close'] > junx2, 5), 1, 0)

    顶背离zb2 = IF(顶背离zb2_tj1 + 顶背离zb2_tj2 + 顶背离zb2_tj3 + 顶背离zb2_tj4 == 4, 1, 0)

    顶背离 = IF(顶背离zb2 + 顶背离_x >= 1, 1, 0)  # 输出

    远低吸计算wz = IF(上一次有效低吸wz < 上一次有效高抛wz, MY_BARSLAST(有效低吸, 2), 上一次有效低吸wz)
    近最低 = IF(k拐上 == 1, MYLLV(指导价_zb, 上一次有效高抛wz), 0)
    远最低 = IF(k拐上 == 1, MYLLV(指导价_zb, 远低吸计算wz), 0)
    底背离zb = 近最低 > 远最低 * 1.05
    持续低位发生 = EXIST(COUNT(df['close'] < junx2b, 40) > 30, 40)

    底背离zb2_tj1 = IF(底背离zb, 1, 0)
    底背离zb2_tj2 = IF(REF(底背离zb, 1) != 1, 1, 0)
    底背离zb2_tj3 = IF(持续低位发生, 1, 0)
    底背离zb2_tj4 = IF(EXIST(df['close'] < junx2b, 5), 1, 0)
    底背离zb2 = IF(底背离zb2_tj1 + 底背离zb2_tj2 + 底背离zb2_tj3 + 底背离zb2_tj4 == 4, 1, 0)
    底背离 = IF(底背离zb2 == 1, 1, 0)
    # print(底背离)
    df['顶背离'] = 顶背离
    df['底背离'] = 底背离
    # values_to_write = [顶背离, 底背离, K, 近高_x, 远高_x]
    # for i, (value1, value2, value3, value4, value5) in enumerate(zip(*values_to_write)):  # 要输出的数据变量。
    #     ini_file_time = df.index[i]
    #     write_ini_file_x(value1, value2, value3, value4, value5, i, ini_file_time.strftime('%Y%m%d%H%M%S'))

    return 顶背离, 底背离, df.index


def zdmr_ddbl_zlmr(db_path, table_name, code, limit_num, ns):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']
    # print(df)
    # 算压力支撑趋势

    # 主动买入
    # 动量 主动买入形成趋势分时
    # 镜
    bt成交量 = EMA(df['vol'], 10)
    bt最高价 = EMA((df['high'] + df['close']) / 2, 10)
    bt最低价 = EMA((df['low'] + df['close']) / 2, 10)
    bt开盘价 = EMA((df['open'] + df['close']) / 2, 10)
    bt收盘价 = EMA((df['close'] + df['close']) / 2, 10)

    小中zc成交量 = bt成交量
    小主买 = IF(bt收盘价 > REF(bt收盘价, 1), (bt收盘价 - REF(bt收盘价, 1)) / (bt最高价 - bt最低价) * 小中zc成交量, 0)
    小主卖 = IF(bt收盘价 < REF(bt收盘价, 1), np.abs(bt收盘价 - REF(bt收盘价, 1)) / (bt最高价 - bt最低价) * 小中zc成交量,
                0)

    sjbs = ns
    小主动买入15 = SUM(ABS(小主买), 3 * sjbs)
    小主动卖出15 = SUM(ABS(小主卖), 3 * sjbs)
    小主动买入20 = SUM(ABS(小主买), 5 * sjbs)
    小主动卖出20 = SUM(ABS(小主卖), 5 * sjbs)
    小主动买入40 = SUM(ABS(小主买), 10 * sjbs)
    小主动卖出40 = SUM(ABS(小主卖), 10 * sjbs)
    小主动买入80 = SUM(ABS(小主买), 13 * sjbs)
    小主动卖出80 = SUM(ABS(小主卖), 13 * sjbs)
    小主动买入150 = SUM(ABS(小主买), 20 * sjbs)
    小主动卖出150 = SUM(ABS(小主卖), 20 * sjbs)
    小主动买入60 = SUM(ABS(小主买), 25 * sjbs)
    小主动卖出60 = SUM(ABS(小主卖), 25 * sjbs)
    小主动买入33 = SUM(ABS(小主买), 33 * sjbs)
    小主动卖出33 = SUM(ABS(小主卖), 33 * sjbs)
    小主动买入120 = SUM(ABS(小主买), 21 * sjbs)
    小主动卖出120 = SUM(ABS(小主卖), 21 * sjbs)
    小主动买入100 = SUM(ABS(小主买), 8 * sjbs)
    小主动卖出100 = SUM(ABS(小主卖), 8 * sjbs)

    小主动买入HJ = (
                               小主动买入15 + 小主动买入20 + 小主动买入40 + 小主动买入80 + 小主动买入60 + 小主动买入33 + 小主动买入100 + 小主动买入120 + 小主动买入150) / 9
    # print(小主动买入HJ)
    小主动卖出HJ = (
                               小主动卖出15 + 小主动卖出20 + 小主动卖出40 + 小主动卖出80 + 小主动卖出60 + 小主动卖出33 + 小主动卖出100 + 小主动卖出120 + 小主动卖出150) / 9
    jing_high = bt最高价
    jing_low = bt最低价
    jing_close = bt收盘价
    jing_open = bt开盘价
    jing_vol = bt成交量
    jing_bs = 1 * ns
    jing_pjj = (jing_close + jing_high + jing_low + jing_open) / 4
    jing_suducha = jing_pjj - REF(jing_pjj, 1)
    # IF(S,A,B)
    jing_zhubuy = IF(jing_suducha > 0, jing_suducha, 0) * jing_vol
    jing_zhusell = IF(jing_suducha < 0, jing_suducha, 0) * jing_vol

    jing_zhubuy_15 = SUM(ABS(jing_zhubuy), 1 * jing_bs)
    jing_zhusell_15 = SUM(ABS(jing_zhusell), 1 * jing_bs)
    jing_zhubuy_20 = SUM(ABS(jing_zhubuy), 2 * jing_bs)
    jing_zhusell_20 = SUM(ABS(jing_zhusell), 2 * jing_bs)
    jing_zhubuy_40 = SUM(ABS(jing_zhubuy), 4 * jing_bs)
    jing_zhusell_40 = SUM(ABS(jing_zhusell), 4 * jing_bs)
    jing_zhubuy_80 = SUM(ABS(jing_zhubuy), 8 * jing_bs)
    jing_zhusell_80 = SUM(ABS(jing_zhusell), 8 * jing_bs)
    jing_zhubuy_100 = SUM(ABS(jing_zhubuy), 15 * jing_bs)
    jing_zhusell_100 = SUM(ABS(jing_zhusell), 15 * jing_bs)
    jing_zhubuy_120 = SUM(ABS(jing_zhubuy), 6 * jing_bs)
    jing_zhusell_120 = SUM(ABS(jing_zhusell), 6 * jing_bs)
    jing_zhubuy_140 = SUM(ABS(jing_zhubuy), 3 * jing_bs)
    jing_zhusell_140 = SUM(ABS(jing_zhusell), 3 * jing_bs)
    jing_zhubuy_160 = SUM(ABS(jing_zhubuy), 12 * jing_bs)
    jing_zhusell_160 = SUM(ABS(jing_zhusell), 12 * jing_bs)
    jing_zhubuy_180 = SUM(ABS(jing_zhubuy), 10 * jing_bs)
    jing_zhusell_180 = SUM(ABS(jing_zhusell), 10 * jing_bs)

    jing_zhubuy_HJ = (
                             jing_zhubuy_15 + jing_zhubuy_20 + jing_zhubuy_40 + jing_zhubuy_80 + jing_zhubuy_100 + jing_zhubuy_120 + jing_zhubuy_140 + jing_zhubuy_160 + jing_zhubuy_180) / 9
    jing_zhusel_HJ = (
                             jing_zhusell_15 + jing_zhusell_20 + jing_zhusell_40 + jing_zhusell_80 + jing_zhusell_100 + jing_zhusell_120 + jing_zhusell_140 + jing_zhusell_160 + jing_zhusell_180) / 9
    jing_zhudong_cha = (jing_zhubuy_HJ - jing_zhusel_HJ)  # 粉小英线大中粉小主动差

    # 片
    pian_high = bt最高价
    pian_low = bt最低价
    pian_close = bt收盘价
    pian_open = bt开盘价
    pian_vol = bt成交量
    pian_bs = 1 * ns

    # 在 pian_VAR1 的计算中加入1e-8在计算 pian_VAR1 之前对分母进行判断，如果为零则将分母赋值为一个极小值（例如  1e-8 ），避免除数为零的情况。
    pian_VAR1 = pian_vol / ((pian_high - pian_low) * 2 - ABS(pian_close - pian_open) + 1e-8)
    # pian_buy_zb = IF(pian_close>pian_open,pian_VAR1*(pian_high-pian_low),IF(pian_close<pian_open,pian_VAR1*((pian_high-pian_open)+(pian_close-pian_low)),pian_vol/2))
    pian_zhubuy = IF(np.isnan(pian_VAR1), 0, IF(pian_close > pian_open, pian_VAR1 * (pian_high - pian_low),
                                                IF(pian_close < pian_open,
                                                   pian_VAR1 * ((pian_high - pian_open) + (pian_close - pian_low)),
                                                   pian_vol / 2)))
    # pian_sell_zb=IF(pian_close>pian_open,0-pian_VAR1*((pian_high-pian_close)+(pian_open-pian_low)),IF(pian_close<pian_open,0-pian_VAR1*(pian_high-pian_low),0-pian_vol/2))
    pian_zhusell = IF(np.isnan(pian_VAR1), 0,
                      IF(pian_close > pian_open, 0 - pian_VAR1 * ((pian_high - pian_close) + (pian_open - pian_low)),
                         IF(pian_close < pian_open, 0 - pian_VAR1 * (pian_high - pian_low), 0 - pian_vol / 2)))

    pian_zhubuy_15 = SUM(ABS(pian_zhubuy), 1 * pian_bs)
    pian_zhusell_15 = SUM(ABS(pian_zhusell), 1 * pian_bs)
    pian_zhubuy_20 = SUM(ABS(pian_zhubuy), 2 * pian_bs)
    pian_zhusell_20 = SUM(ABS(pian_zhusell), 2 * pian_bs)
    pian_zhubuy_40 = SUM(ABS(pian_zhubuy), 4 * pian_bs)
    pian_zhusell_40 = SUM(ABS(pian_zhusell), 4 * pian_bs)
    pian_zhubuy_80 = SUM(ABS(pian_zhubuy), 8 * pian_bs)
    pian_zhusell_80 = SUM(ABS(pian_zhusell), 8 * pian_bs)
    pian_zhubuy_100 = SUM(ABS(pian_zhubuy), 15 * pian_bs)
    pian_zhusell_100 = SUM(ABS(pian_zhusell), 15 * pian_bs)
    pian_zhubuy_120 = SUM(ABS(pian_zhubuy), 6 * pian_bs)
    pian_zhusell_120 = SUM(ABS(pian_zhusell), 6 * pian_bs)
    pian_zhubuy_140 = SUM(ABS(pian_zhubuy), 9 * pian_bs)
    pian_zhusell_140 = SUM(ABS(pian_zhusell), 9 * pian_bs)
    pian_zhubuy_160 = SUM(ABS(pian_zhubuy), 20 * pian_bs)
    pian_zhusell_160 = SUM(ABS(pian_zhusell), 20 * pian_bs)
    pian_zhubuy_180 = SUM(ABS(pian_zhubuy), 10 * pian_bs)
    pian_zhusell_180 = SUM(ABS(pian_zhusell), 10 * pian_bs)

    pian_zhubuy_HJ = (
                             pian_zhubuy_15 + pian_zhubuy_20 + pian_zhubuy_40 + pian_zhubuy_80 + pian_zhubuy_100 + pian_zhubuy_120 + pian_zhubuy_140 + pian_zhubuy_160 + pian_zhubuy_180) / 9
    pian_zhusel_HJ = (
                             pian_zhusell_15 + pian_zhusell_20 + pian_zhusell_40 + pian_zhusell_80 + pian_zhusell_100 + pian_zhusell_120 + pian_zhusell_140 + pian_zhusell_160 + pian_zhusell_180) / 9
    pian_zhudong_cha = (pian_zhubuy_HJ - pian_zhusel_HJ)  # 粉小英线大中粉小主动差

    # 防

    fang_high = bt最高价
    fang_low = bt最低价
    fang_close = bt收盘价
    fang_open = bt开盘价
    fang_vol = bt成交量 / 2
    fang_bs = 1 * ns

    fang_xiaoqian_up = fang_close > REF(fang_close, 1)
    fang_xiaoqian_down = fang_close < REF(fang_close, 1)
    fang_xiaoqian_bfw1_tj1 = IF(REF(fang_xiaoqian_down, 1) != 1, 1, 0)
    fang_xiaoqian_bfw1_tj2 = IF(fang_xiaoqian_down == 1, 1, 0)
    fang_xiaoqian_bfw1_tj3 = IF(fang_xiaoqian_bfw1_tj1 + fang_xiaoqian_bfw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bfw1 = MY_BARSLAST(fang_xiaoqian_bfw1_tj3 == 1, 1) + 1

    fang_xiaoqian_bgw1_tj1 = IF(REF(fang_xiaoqian_up, 1) != 1, 1, 0)
    fang_xiaoqian_bgw1_tj2 = IF(fang_xiaoqian_up == 1, 1, 0)
    fang_xiaoqian_bgw1_tj3 = IF(fang_xiaoqian_bgw1_tj1 + fang_xiaoqian_bgw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bgw1 = MY_BARSLAST(fang_xiaoqian_bgw1_tj3 == 1, 1) + 1
    fang_xiaoqian_up_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bgw1)
    fang_xiaoqian_down_jiliang = MY_SUM(fang_vol, fang_xiaoqian_bfw1)

    fang_xiaoqian_xxx = IF(fang_xiaoqian_up == 1, fang_xiaoqian_up_jiliang, fang_xiaoqian_down_jiliang)
    fang_xiaoqian_gongji = IF(fang_xiaoqian_down, fang_xiaoqian_xxx, 0)
    fang_xiaoqian_xuqiu = IF(fang_xiaoqian_up, fang_xiaoqian_xxx, 0)
    fang_zhubuy = fang_xiaoqian_xuqiu
    fang_zhusell = fang_xiaoqian_gongji

    fang_zhubuy_15 = SUM(ABS(fang_zhubuy), 1 * fang_bs)
    fang_zhusell_15 = SUM(ABS(fang_zhusell), 1 * fang_bs)
    fang_zhubuy_20 = SUM(ABS(fang_zhubuy), 2 * fang_bs)
    fang_zhusell_20 = SUM(ABS(fang_zhusell), 2 * fang_bs)
    fang_zhubuy_40 = SUM(ABS(fang_zhubuy), 4 * fang_bs)
    fang_zhusell_40 = SUM(ABS(fang_zhusell), 4 * fang_bs)
    fang_zhubuy_80 = SUM(ABS(fang_zhubuy), 8 * fang_bs)
    fang_zhusell_80 = SUM(ABS(fang_zhusell), 8 * fang_bs)
    fang_zhubuy_100 = SUM(ABS(fang_zhubuy), 15 * fang_bs)
    fang_zhusell_100 = SUM(ABS(fang_zhusell), 15 * fang_bs)
    fang_zhubuy_120 = SUM(ABS(fang_zhubuy), 6 * fang_bs)
    fang_zhusell_120 = SUM(ABS(fang_zhusell), 6 * fang_bs)
    fang_zhubuy_140 = SUM(ABS(fang_zhubuy), 3 * fang_bs)
    fang_zhusell_140 = SUM(ABS(fang_zhusell), 3 * fang_bs)
    fang_zhubuy_160 = SUM(ABS(fang_zhubuy), 12 * fang_bs)
    fang_zhusell_160 = SUM(ABS(fang_zhusell), 12 * fang_bs)
    fang_zhubuy_180 = SUM(ABS(fang_zhubuy), 10 * fang_bs)
    fang_zhusell_180 = SUM(ABS(fang_zhusell), 10 * fang_bs)
    fang_zhubuy_HJ = (
                             fang_zhubuy_15 + fang_zhubuy_20 + fang_zhubuy_40 + fang_zhubuy_80 + fang_zhubuy_100 + fang_zhubuy_120 + fang_zhubuy_140 + fang_zhubuy_160 + fang_zhubuy_180) / 9
    fang_zhusel_HJ = (
                             fang_zhusell_15 + fang_zhusell_20 + fang_zhusell_40 + fang_zhusell_80 + fang_zhusell_100 + fang_zhusell_120 + fang_zhusell_140 + fang_zhusell_160 + fang_zhusell_180) / 9
    fang_zhudong_cha = (fang_zhubuy_HJ - fang_zhusel_HJ)  # 粉小英线大中粉小主动差
    小合小pjzdc1x = (MA(小主动买入HJ, 15) + MA(fang_zhubuy_HJ, 15) + MA(pian_zhubuy_HJ, 15) + MA(jing_zhubuy_HJ,
                                                                                                 15)) / 4

    小合小pjzdc1 = (SUM(小合小pjzdc1x, 2) / 2 + SUM(小合小pjzdc1x, 4) / 4 + SUM(小合小pjzdc1x, 7) / 7) / 3
    趋势小合小pjzdc1 = EMA(小合小pjzdc1, 100)
    主动买多 = 小合小pjzdc1 > 趋势小合小pjzdc1
    return 主动买多, df.index


def dzq_ylzcqs(db_path, table_name, code, limit_num, ns):
    conn = sqlite3.connect(db_path)  # 修改
    c = conn.cursor()
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
    table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    df.fillna(method='ffill', inplace=True)  # ！为了处理数据帧中可能存在的  0  值，您可以在函数的第一行加入以下代码
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)
    最高价_x = df['high']
    最低价_x = df['low']
    开盘价_x = df['open']
    收盘价_x = df['close']
    成交量_x = df['vol']

    指导价 = df['close']
    sqsz_9_zdsz = 指导价
    sqsz_9_jiange_1 = 4
    sqsz_9_t1 = IF(sqsz_9_zdsz < REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_t2 = IF(REF(sqsz_9_zdsz, 1) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_t3 = IF(REF(sqsz_9_zdsz, 2) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_t4 = IF(REF(sqsz_9_zdsz, 3) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_t5 = IF(REF(sqsz_9_zdsz, 4) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_t6 = IF(REF(sqsz_9_zdsz, 5) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_t7 = IF(REF(sqsz_9_zdsz, 6) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_t8 = IF(REF(sqsz_9_zdsz, 7) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_t9 = IF(REF(sqsz_9_zdsz, 8) < REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_CL = IF(
        sqsz_9_t1 + sqsz_9_t2 + sqsz_9_t3 + sqsz_9_t4 + sqsz_9_t5 + sqsz_9_t6 + sqsz_9_t7 + sqsz_9_t8 + sqsz_9_t9 == 9,
        1, 0)
    sqsz_9_CLqr_tj1 = IF(REF(sqsz_9_CL, 1) != 1, 1, 0)
    sqsz_9_CLqr_tj2 = IF(sqsz_9_CL == 1, 1, 0)
    sqsz_9_CLqr = IF(sqsz_9_CLqr_tj1 + sqsz_9_CLqr_tj2 == 2, 1, 0)

    sqsz_9_fan_t1 = IF(sqsz_9_zdsz > REF(sqsz_9_zdsz, sqsz_9_jiange_1), 1, 0)
    sqsz_9_fan_t2 = IF(REF(sqsz_9_zdsz, 1) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 1), 1, 0)
    sqsz_9_fan_t3 = IF(REF(sqsz_9_zdsz, 2) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 2), 1, 0)
    sqsz_9_fan_t4 = IF(REF(sqsz_9_zdsz, 3) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 3), 1, 0)
    sqsz_9_fan_t5 = IF(REF(sqsz_9_zdsz, 4) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 4), 1, 0)
    sqsz_9_fan_t6 = IF(REF(sqsz_9_zdsz, 5) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 5), 1, 0)
    sqsz_9_fan_t7 = IF(REF(sqsz_9_zdsz, 6) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 6), 1, 0)
    sqsz_9_fan_t8 = IF(REF(sqsz_9_zdsz, 7) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 7), 1, 0)
    sqsz_9_fan_t9 = IF(REF(sqsz_9_zdsz, 8) > REF(sqsz_9_zdsz, sqsz_9_jiange_1 + 8), 1, 0)
    sqsz_9_fan_CL = IF(
        sqsz_9_fan_t1 + sqsz_9_fan_t2 + sqsz_9_fan_t3 + sqsz_9_fan_t4 + sqsz_9_fan_t5 + sqsz_9_fan_t6 + sqsz_9_fan_t7 + sqsz_9_fan_t8 + sqsz_9_fan_t9 == 9,
        1, 0)
    sqsz_9_fan_CLqr_tj1 = IF(REF(sqsz_9_fan_CL, 1) != 1, 1, 0)
    sqsz_9_fan_CLqr_tj2 = IF(sqsz_9_fan_CL == 1, 1, 0)
    sqsz_9_fan_CLqr = IF(sqsz_9_fan_CLqr_tj1 + sqsz_9_fan_CLqr_tj2 == 2, 1, 0)
    sqsz_9_gaopao = sqsz_9_fan_CLqr
    sqsz_9_dixi = sqsz_9_CLqr

    sqszzh_sell_jiedian = IF(sqsz_9_gaopao == 1, 1, 0)
    sqszzh_buy_jiedian = IF(sqsz_9_dixi == 1, 1, 0)

    sqszzh_gjd_jiedian = IF(sqszzh_sell_jiedian + sqszzh_buy_jiedian >= 1, 1, 0)

    BarsLast_ssqszzh_gjd_jiedian_wz = MY_BARSLAST(sqszzh_gjd_jiedian == 1, 1)  # 上一次关键点wz
    x最高价 = HHV(df['high'], 4)
    x最低价 = LLV(df['low'], 4)
    x收盘价 = df['close']
    x开盘价 = REF(df['close'], 4)
    xm = 26
    xTR1 = MAX(MAX((x最高价 - x最低价), ABS(REF(x收盘价, 4) - x最高价)), ABS(REF(x收盘价, 4) - x最低价))
    xATR1 = EMA(xTR1, xm)

    下关键线 = MYREF(MA(LLV(df['high'], 20), 20), BarsLast_ssqszzh_gjd_jiedian_wz)
    下盈 = (HHV(下关键线, 20))

    上关键线 = MYREF(MA(HHV(df['low'], 20), 20), BarsLast_ssqszzh_gjd_jiedian_wz)
    上盈 = (LLV(上关键线, 20))
    # print('下关键线',下关键线)
    # 价格的波段率
    bs = 1
    bdl_a = ((HHV(df['high'], 39 * bs) - LLV(df['low'], 39 * bs)) / 39 * bs) * 10000
    bdl_b = (HHV(df['high'], 24 * bs) - LLV(df['low'], 24 * bs)) / 24 * bs * 10000
    bdl_c = (HHV(df['high'], 71 * bs) - LLV(df['low'], 71 * bs)) / 71 * bs * 10000
    bdl_d = (HHV(df['high'], 44 * bs) - LLV(df['low'], 44 * bs)) / 44 * bs * 10000
    bdl_e = (HHV(df['high'], 66 * bs) - LLV(df['low'], 66 * bs)) / 66 * bs * 10000
    bdl_f = (HHV(df['high'], 99 * bs) - LLV(df['low'], 99 * bs)) / 99 * bs * 10000
    bdl_bz = bdl_a * 1000 / bdl_b * 1000 / bdl_c * 1000 / bdl_d * 1000 / bdl_e * 1000 / bdl_f * 1000
    # 最大最小值归一化
    bdl_bz = (bdl_bz - np.nanmin(bdl_bz)) / (np.nanmax(bdl_bz) - np.nanmin(bdl_bz))
    bdl_bz_ema = EMA(bdl_bz, 60)

    bdl_波动率_pj, barpos = calculate_avg_and_positions(bdl_bz_ema)
    bdl_波动率_b2 = bdl_bz_ema - REF(bdl_bz_ema, 20)
    bdl_波动率_b2[bdl_波动率_b2 == 0] = 1e-8  # 判断并将分母为零的值赋为1e-8
    bdl_波动率_a2 = 20 * bdl_波动率_pj
    bdl_波动率_jiaodu_c2 = 90 - (np.arctan(bdl_波动率_a2 / bdl_波动率_b2) * 57.29578)
    bdl_波动率_jiaodu_cqr2 = IF(bdl_波动率_jiaodu_c2 > 90, (180 - bdl_波动率_jiaodu_c2) * -1, bdl_波动率_jiaodu_c2)
    小角度cqr = EMA(bdl_波动率_jiaodu_cqr2, 20)

    小角度cqr小于0节点tj1 = IF(小角度cqr < 0, 1, 0)
    小角度cqr小于0节点tj2 = IF(REF(小角度cqr, 1) >= 0, 1, 0)
    小角度cqr小于0节点 = IF(小角度cqr小于0节点tj1 + 小角度cqr小于0节点tj2 == 2, 1, 0)
    小角度cqrxz_tj1 = IF(EVERY(小角度cqr < 0, 4), 1, 0)
    小角度cqrxz_tj2 = IF(EXIST(小角度cqr小于0节点 == 1, 4), 1, 0)
    小角度cqrxz = IF(小角度cqrxz_tj1 + 小角度cqrxz_tj2 == 2, 1, 0)

    上限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) + 1 * xATR1
    下限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) - 1 * xATR1

    a_tj1 = IF(df['high'] < x最高价, 1, 0)
    a_tj2 = IF(df['low'] > x最低价, 1, 0)
    a_tj3 = IF(NthMaxList(1, df['open'], df['close']) < NthMaxList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a_tj4 = IF(NthMinList(1, df['open'], df['close']) > NthMinList(1, REF(df['open'], 1), REF(df['close'], 1)), 1, 0)
    a = IF(a_tj1 + a_tj2 + a_tj3 + a_tj4 == 4, 1, 0)
    a_wz = MY_BARSLAST(a, 1)
    yali = NthMaxList(1, MYREF(df['high'], a_wz), MYREF(df['high'], a_wz + 1), MYREF(df['high'], a_wz + 2),
                      MYREF(df['high'], a_wz + 3))
    zicheng = NthMinList(1, MYREF(df['low'], a_wz), MYREF(df['low'], a_wz + 1), MYREF(df['low'], a_wz + 2),
                         MYREF(df['low'], a_wz + 3))
    junx2 = EMA((上限 + 上盈 + EMA(yali, 60)) / 3, 160)
    junx2b = EMA((下限 + 下盈 + EMA(zicheng, 60)) / 3, 160)
    junxa = EMA((junx2 + HHV(df['high'], 60)), 160) / 2
    junxb = EMA((junx2 + LLV(df['low'], 60)), 160) / 2

    df['junx2'] = junx2
    df['junx2b'] = junx2b
    df['junxa'] = junxa
    df['junxb'] = junxb
    指导价, junx2, junx2b, junxa, junxb, 最高价_x, 最低价_x, 开盘价_x, 收盘价_x, 成交量_x, kdj_顶背离, kdj_底背离, time, df_zhu = kdj_ddbl(
        db_path, table_name, code, limit_num, ns=4)
    macd_顶背离, macd_底背离, macd_time = macd_ddbl(db_path, table_name, code, limit_num, ns=4)
    zdmr_顶背离, zdmr_底背离, zdmr_time = zdmr_ddbl(db_path, table_name, code, limit_num, ns=6)
    顶背离 = IF(kdj_顶背离 + macd_顶背离 + zdmr_顶背离 >= 1, 1, 0)
    底背离 = IF(kdj_底背离 + macd_底背离 + zdmr_底背离 >= 1, 1, 0)
    df['顶背离'] = 顶背离
    df['底背离'] = 底背离
    return df.index, df


def dzq_ddbl(db_path, table_name, code, limit_num, ns):
    指导价, junx2, junx2b, junxa, junxb, 最高价_x, 最低价_x, 开盘价_x, 收盘价_x, 成交量_x, kdj_顶背离, kdj_底背离, time, df_zhu = kdj_ddbl(
        db_path, table_name, code, limit_num, ns=4)
    macd_顶背离, macd_底背离, macd_time = macd_ddbl(db_path, table_name, code, limit_num, ns=4)
    zdmr_顶背离, zdmr_底背离, zdmr_time = zdmr_ddbl(db_path, table_name, code, limit_num, ns=6)
    顶背离 = IF(kdj_顶背离 + macd_顶背离 + zdmr_顶背离 >= 1, 1, 0)
    底背离 = IF(kdj_底背离 + macd_底背离 + zdmr_底背离 >= 1, 1, 0)
    df_zhu['顶背离'] = 顶背离
    df_zhu['底背离'] = 底背离
    return df_zhu.index, df_zhu


