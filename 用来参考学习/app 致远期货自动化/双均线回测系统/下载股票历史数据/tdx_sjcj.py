import sqlite3
import datetime
import time
import pandas as pd
from pytdx.hq import TdxHq_API
import os
import csv
import socket
import concurrent.futures


class KLineData:
    def __init__(self, time: datetime.datetime, high, low, open, close, vol, code):
        self.time = time.strftime("%Y-%m-%d %H:%M:%S")  # 修改这里，格式化时间，并补充秒
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


def store_kline_data(conn, code, level, data_list):
    fields = ['time', 'high', 'low', 'open', 'close', 'vol', 'code']
    # 获取表名
    table_name = get_table_name(level)
    # 开启事务
    conn.execute("BEGIN TRANSACTION")
    try:
        # 批量插入数据
        conn.executemany(f"INSERT OR IGNORE INTO {table_name} ({','.join(fields)}) VALUES (?, ?, ?, ?, ?, ?, ?)",
                         data_list)
        # 提交事务
        conn.commit()
    except Exception as e:
        # 回滚事务
        conn.rollback()
        print(e)


def load_kline_data(conn, code, level):
    # 获取表名
    table_name = get_table_name(level)
    # 从表中读取所有数据并转为DataFrame格式
    df = pd.read_sql(f"SELECT * FROM {table_name} WHERE code='{code}'", conn)
    # print(df)
    # 将DataFrame中的时间数据转换为datetime格式
    df['time'] = pd.to_datetime(df['time'])
    # 将数据按照时间升序排序并返回
    df = df.sort_values(by='time', ascending=True)
    return df


max_retries = 3  # 最大重试次数
retry_delay = 5  # 重试延迟时间（秒）


def download_data_with_retry():
    print('开始测试连接')
    retries = 0
    connected = False

    while not connected and retries < max_retries:
        try:
            with api.connect('121.36.81.195', 7709):
                print('连接行情数据正常，开始下载')
                connected = True
        except socket.timeout:
            retries += 1
            print(f"连接超时，尝试重新连接，重试次数：{retries}/{max_retries}")
            time.sleep(retry_delay)

    if not connected:
        print("无法连接到服务器，请检查网络连接或稍后重试。")


api = TdxHq_API(multithread=True)
zhumulu_folder = r'd:\gupiao_sql'
if not os.path.exists(zhumulu_folder):
    os.makedirs(zhumulu_folder)

api = TdxHq_API()
while True:
    try:
        with open(r'd:\实操票.csv', 'r', encoding='gbk') as f:
            reader = csv.reader(f)
            next(reader)  # 跳过标题行
            print(reader)

            fields = ['time', 'high', 'low', 'open', 'close', 'vol', 'code']
            for row in reader:
                data = row[0]
                codec = data

                code = data[3:]
                if data[:3] == 'sh.':
                    shichang = 1
                elif data[:3] == 'sz.':
                    shichang = 0
                else:
                    shichang = None

                print('data:', data)
                print('codec:', codec)
                print('shichang:', shichang)
                print('code:', code)
                model_folder_mc = codec + '_data.db'
                db_path = os.path.join(zhumulu_folder, model_folder_mc)
                print(db_path)
                conn = sqlite3.connect(db_path)

                # 调用连接函数
                download_data_with_retry()
                with api.connect('121.36.81.195', 7709):
                    try:
                        print('连接行情数据正常，开始下载')
                        with conn:
                            print('连接数据库正常，开始写入')

                            # 获取日线数据
                            level = 9
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print('日线——kline_data', kline_data)
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print('日线——kline_data',kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'],
                                                 kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append(
                                    [data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)


                            # 获取60分钟数据
                            level = 3
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print('kline_data',kline_data)
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print(kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'], kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append([data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)

                            #获取1分钟数据
                            level = 7
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            # print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 800))
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 800))
                                print(kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'], kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append([data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)

                            #获取30分钟数据
                            level = 2
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            # print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 800))
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 800))
                                print(kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'], kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append([data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)

                            # 获取15分钟数据
                            level = 1
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            # print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print(kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'], kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append([data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)

                            # 获取5分钟数据
                            level = 0
                            kline_data_loaded = load_kline_data(conn, codec, level)
                            # print('读取本地数据库kline_data_loaded---', kline_data_loaded)
                            if kline_data_loaded.empty:
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                            else:
                                last_time = kline_data_loaded['time'].iloc[-1]
                                start_time = last_time + datetime.timedelta(minutes=level)
                                start_time_int = int(time.mktime(start_time.timetuple()))
                                # print('需要的开始时间---', start_time)
                                # print('code---', codec)
                                # print('shichang---', shichang)
                                kline_data = api.to_df(api.get_security_bars(level, shichang, code, 0, 100))
                                print(kline_data)
                                # kline_data = api.to_df(api.get_security_bars(level, shichang, code, start_time_int, 100))
                            kline_data = kline_data[:-1]  # 剔除最新的一条数据
                            # print(kline_data)
                            # print(kline_data.columns)

                            kline_list = []
                            for i in range(len(kline_data)):
                                time_str = kline_data.iloc[i]['datetime']
                                time_obj = datetime.datetime.strptime(time_str, "%Y-%m-%d %H:%M")
                                data = KLineData(time_obj, kline_data.iloc[i]['high'], kline_data.iloc[i]['low'],
                                                 kline_data.iloc[i]['open'], kline_data.iloc[i]['close'], kline_data.iloc[i]['vol'],
                                                 codec)
                                kline_list.append([data.time, data.high, data.low, data.open, data.close, data.vol, data.code])

                            existing_data = kline_data_loaded[['time', 'code']].values.tolist()
                            new_data = [item for item in kline_list if [item[0], item[6]] not in existing_data]
                            if new_data:
                                store_kline_data(conn, codec, level, new_data)

                            kline_data_loaded = load_kline_data(conn, codec, level)
                    except concurrent.futures.TimeoutError:
                        print("等待更新超时，继续等待")
                        continue
                    except Exception as e:
                        print(f"发生异常：{e}")
                        continue
                        # 休眠 1 秒钟，避免持续占用 CPU 时间
    except concurrent.futures.TimeoutError:
        print("等待更新超时，继续等待")
        continue
    except Exception as e:
        print(f"发生异常：{e}")
    continue

