import baostock as bs
import pandas as pd
import sqlite3
import datetime
import time
import pandas as pd
import os
import csv

class KLineData:
    def __init__(self, time, high, low, open, close, vol, code):
        time_obj = datetime.datetime.fromtimestamp(time)
        self.time = time_obj
        self.high = high
        self.low = low
        self.open = open
        self.close = close
        self.vol = vol
        self.code = code

def get_table_name(level):
    table_names = ['min_data5', 'min_data15', 'min_data30', 'min_data60', 'daily_data', 'weekly_data', 'monthly_data',
                   'min_data1', 'min_data1', 'daily_data', 'quarterly_data', 'yearly_data']
    return table_names[level]



def load_kline_data(code, level):
    table_name = get_table_name(level)
    df = pd.read_sql(f"SELECT * FROM {table_name} WHERE code='{code}'", conn)
    df['time'] = pd.to_datetime(df['time'])
    df = df.sort_values(by='time', ascending=True)
    return df

def import_data(code, level):
    frequency_mapping = {
        0: "5",
        1: "15",
        2: "30",
        3: "60",
        4: "d",
        5: "w",
        6: "m"
    }

    if level not in frequency_mapping:
        raise ValueError("Invalid level value. Level should be between 0 and 6.")

    frequency = frequency_mapping[level]
    rs = bs.query_history_k_data_plus(code,
                                      "date,time,code,open,high,low,close,volume,amount,adjustflag",
                                      start_date='2024-6-19', end_date='2025-2-6',
                                      frequency=frequency,
                                      adjustflag="3")
    print(f'query_history_k_data_plus respond error_code:{rs.error_code}—{code}—对应周期{level}')
    print(f'query_history_k_data_plus respond  error_msg:{rs.error_msg}—{code}—对应周期{level}')

    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())

    batch_data = []
    for data in data_list:
        time_val=datetime.datetime.strptime(data[1][:14], '%Y%m%d%H%M%S')
        # print(f'{time_val}代码{code}')
        code_S = code
        batch_data.append([time_val, data[4], data[5], data[3], data[6], data[7], code_S])
    # print(batch_data)

    table_name = get_table_name(level)
    insert_query = f"INSERT OR IGNORE INTO {table_name} ({table_fields}) values (?, ?, ?, ?, ?, ?, ?)"
    cursor = conn.cursor()
    try:
        cursor.executemany(insert_query, batch_data)
    except Exception as e:
        print(e)
    cursor.close()
    conn.commit()
csv_ml=r'd:\行业龙头.csv'
with open(csv_ml, 'r', encoding='gbk') as f:
    reader = csv.reader(f)
    next(reader)  # 跳过标题行
    for row in reader:
        data = row[0]
        code = row[0]
        if data[:3] == 'sh.':
            shichang = 1
        elif data[:3] == 'sz.':
            shichang = 0
        else:
            shichang = None

        print('data:', data)
        print('code:', code)
        print('shichang:', shichang)

        lg = bs.login()
        print('login respond error_code:' + lg.error_code)
        print('login respond  error_msg:' + lg.error_msg)

        zhumulu_folder =  r'gupiao_tdx'
        # zhumulu_folder =  r'd:\gupiao_sql'
        model_folder_mc = code + '_data.db'
        db_path = os.path.join(zhumulu_folder, model_folder_mc)


        conn = sqlite3.connect(db_path)

        fields = ['time', 'high', 'low', 'open', 'close', 'vol', 'code']
        for level in range(12):
            table_name = get_table_name(level)
            table_fields = ",".join(fields)
            cursor = conn.cursor()
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name} (time DATETIME, high FLOAT, low FLOAT, open FLOAT, close FLOAT, vol FLOAT, code TEXT, PRIMARY KEY (time, code))")
            cursor.close()
        cj_zq = 0
        import_data(data, cj_zq)
        cj_zq = 1
        import_data(data, cj_zq)
        cj_zq = 2
        import_data(data, cj_zq)
        cj_zq = 3
        import_data(data, cj_zq)
        # cj_zq = 4
        # import_data(data, cj_zq)

        day_k_rs = bs.query_history_k_data_plus(data,
                                          "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST",
                                          start_date='2024-6-19', end_date='2025-2-6',
                                          frequency="d", adjustflag="3")
        print('日k数据_query_history_k_data_plus respond error_code:' + day_k_rs.error_code)
        print('日k数据_query_history_k_data_plus respond  error_msg:' + day_k_rs.error_msg)
        #
        # #### 打印结果集 ####
        day_k_data_list = []
        while (day_k_rs.error_code == '0') & day_k_rs.next():
            # 获取一条记录，将记录合并在一起
            day_k_data_list.append(day_k_rs.get_row_data())
        result = pd.DataFrame(day_k_data_list, columns=day_k_rs.fields)
        # print(result)

        # Connect to the SQLite3 database
        day_k_conn = sqlite3.connect(db_path)
        day_k_cursor = day_k_conn.cursor()
        # Create the table if it doesn't exist
        table_name = 'daily_data'
        day_k_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS {table_name} (time DATETIME, high FLOAT, low FLOAT, open FLOAT, close FLOAT, vol FLOAT, code TEXT, PRIMARY KEY (time, code))")

        # Iterate through the data and insert into the database
        for row in day_k_data_list:
            try:
                time_day_k = datetime.datetime.strptime(row[0], '%Y-%m-%d').strftime('%Y-%m-%d %H:%M:%S')
                print(time_day_k)
                high = float(row[3])
                low = float(row[4])
                open = float(row[2])
                close = float(row[5])
                vol = float(row[7])
                code = row[1][3:]  # Remove the first three characters from the code

                # Check for duplicate entries
                day_k_cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE time = ? AND code = ?", (time_day_k, code))
                count = day_k_cursor.fetchone()[0]
                if count > 0:
                    continue  # Skip if entry already exists

                # Insert the data into the table
                day_k_cursor.execute(f"INSERT INTO {table_name} VALUES (?, ?, ?, ?, ?, ?, ?)",
                                     (time_day_k, high, low, open, close, vol, code))
            except ValueError as e:
                print(f"ValueError: {e}")
                continue
        # Commit the changes and close the cursor
        day_k_conn.commit()
        day_k_cursor.close()

        bs.logout()