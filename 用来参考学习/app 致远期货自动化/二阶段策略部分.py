# 使用要求 ：数据库为
# 品种文件在d:/期货单目录_rb2505.csv
# 模型源代码在python_py_path = r'C:\神经网络学习2\批量训练_期货_best_282cs_实战包_520参数_预判天干地址买卖点'  # py程序路径
# 模型存储位置在：dst_folder = r'e:\20230707_qihuo_min155_520cs_best_4_tgdz_mmd\qihuo_dl_win_xunlian_model_fnh_min155_0.02_2ceng_cs282_' + code  # 全数据模型存储的上级文件夹
# 数据库地址 db_zhumulu_folder = r'd:\qihuo_sql'
# 数据库名称：model_folder_mc = code + '_data.db'
# from tqsdk import TqApi, TqAuth, TqKq, TqBacktest, TargetPosTask
from huatu_mz import *
import warnings

warnings.filterwarnings('ignore')

import logging
import torch
import torch.nn as nn
from datetime import datetime
import torch.nn.init as init
import time
import datetime
from data_processing import *
import configparser
import backtrader as bt
import csv


# 初始化配置
def init_config():
    config = configparser.ConfigParser()
    config['xl_main_folder'] = {
        'gl_model_folder': r'D:\yolov5\神经网络学习_序列数据训练预测\600030_min_data15_hb\qushi_model\gl_model',
        'zd_model_folder': r'D:\yolov5\神经网络学习_序列数据训练预测\600030_min_data15_hb\qushi_model\zd_model',
        'code': 'sh.600030',
        'limit_num': '4000',
        'table_name': 'min_data15',
        'zig_x': '0.02',
        'db_path': r'D:\gupiao_sql\sh.600030_data.db',
        'python_py_path': r'D:\yolov5\神经网络学习_序列数据训练预测\批量训练_期货_best_282cs_实战包_520参数',
        'dst_folder': r'e:\20230707_qihuo_min60_520cs_best_4\sh600030_model',
        'table_level': '60'
    }

    with open('xlsys.ini', 'w') as f:
        config.write(f)


def calculate_strategy_signals(df, jx1=5, jx2=10, jx3=20, jx4=30, jx5=60, 
                             粘合阈值=0.0015, ma4附近阈值=0.0012):
    """
    计算策略信号的核心函数
    直接返回包含所有策略指标的DataFrame
    
    参数:
    - df: 包含OHLCV数据的DataFrame
    - jx1-jx5: 均线参数
    - 粘合阈值: 五线粘合判断阈值 (默认0.0015)
    - ma4附近阈值: ma4附近上下范围阈值 (默认0.002)
    """
    # 计算均线
    ma1 = MA(df['close'], jx1)
    ma2 = MA(df['close'], jx2)
    ma3 = MA(df['close'], jx3)
    ma4 = MA(df['close'], jx4)
    ma5 = MA(df['close'], jx5)
    
    # 计算五线相关指标
    五线最大 = NthMaxList(1,ma1, ma2, ma3, ma4, ma5)
    五线最小 = NthMinList(1,ma1, ma2, ma3, ma4, ma5)
    五线差 = np.array(五线最大) - np.array(五线最小)
    五线比 = 五线差 / df['close']
    粘合 = IF(五线比 <= 粘合阈值, 1, 0)

    # 计算ma4附近指标
    ma4附近上 = ma4 + ma4 * ma4附近阈值
    ma4附近下 = ma4 - ma4 * ma4附近阈值
    
    # 计算买卖信号
    上穿ma4附近 = IF(bt_crossover(df['close'], ma4附近上), 1, 0)
    下穿ma4附近 = IF(bt_crossunder(df['close'], ma4附近上), 1, 0)
    下穿ma4附近wz = MY_BARSLAST(下穿ma4附近, 1)
    有效跌破_tj1 = IF(EVERY(df['close'] < ma4附近下, 2), 1, 0)
    有效跌破_tj2 = IF(MYEXIST(有效跌破_tj1, 下穿ma4附近wz), 1, 0)
    有效跌破_tj3 = IF(EXIST(有效跌破_tj1, 7), 1, 0)#天之内没有跌破下轨。
    无跌破 = IF(有效跌破_tj3 == 0, 1, 0)
    附近粘合tj = IF(df['close'] < ma4附近上, 1, 0)
    附近粘合 = IF(粘合 + 附近粘合tj == 2, 1, 0)
    买入_tj1 = IF(MYEXIST(附近粘合, 下穿ma4附近wz), 1, 0)
    买入 = IF(买入_tj1 + 上穿ma4附近 + 无跌破 == 3, 1, 0)
    买入wz = MY_BARSLAST(买入,1)
    卖出zb = IF(EVERY(df['close'] < ma4, 2), 1, 0)
    卖出zb2=IF(REF(卖出zb,1)!=1,1,0)
    卖出 =  IF(卖出zb+卖出zb2==2,1,0)
    卖出wz = MY_BARSLAST(卖出,1)
    
    # 计算最终信号
    二十下穿六十 = 卖出
    二十上穿六十 = 买入
    上下穿多 = IF(买入wz < 卖出wz, 1, 0)
    上下穿空 = IF(上下穿多 != 1, 1, 0)
    
    # 将计算结果添加到df中
    df['上下穿多'] = 二十上穿六十
    df['上下穿空'] = 二十下穿六十
    df['m1'] = ma1
    df['m2'] = ma2
    df['m3'] = ma3
    df['m4'] = ma4
    df['m5'] = ma5
    df['卖60'] = 二十下穿六十
    df['买60'] = 二十上穿六十
    df['ma5'] = ma5
    df['五线差']=五线差
    df['五线比']=五线比
    df['粘合']=粘合
    df['ma4附近上']=ma4附近上
    df['ma4附近下']=ma4附近下
    df['买入_tj1']=买入_tj1
    df['上穿ma4附近']=上穿ma4附近
    df['无跌破']=无跌破
    return df


def caiji_yuce_jiaoyizhibiao(sqldb_path_file, table_name, limit_num, code, jx1=5, jx2=10,jx3=20,jx4=40,jx5=60,
                           粘合阈值=0.0015, ma4附近阈值=0.002):
    # 连接数据库
    print('连接数据库', sqldb_path_file)
    conn = sqlite3.connect(sqldb_path_file)
    c = conn.cursor()
    # 修改的地方
    # 查询指定股票代码的数据并按时间远近排序

    table_name = table_name  # 修改的地方
    limit_num = limit_num  # 修改的地方
    dst_folder = os.path.join(os.path.dirname(__file__), 'tgdz_model')  # 一号预测模型目录
    print('模型存放主目录', dst_folder)
    print('模型调用的数据表', table_name)
    query = "SELECT * FROM %s WHERE code='%s' ORDER BY time DESC LIMIT %s" % (
        table_name, code, limit_num)  # 股票代码导入语句，因为代码是字符需要在%s 加引号
    c.execute(query)  # 执行查询
    rows = c.fetchall()  # 使用  fetchall()  获取所有查询结果
    rows.reverse()  # 使用  reverse()  将结果列表翻转
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    df['time'] = pd.to_datetime(df['time'])
    df = df.set_index('time')
    print(df)

    # 使用公共函数计算策略信号
    df = calculate_strategy_signals(df, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)
    print(df)
    print(df.columns)

    return df



def run_backtest_local(code: str,
                      table_name: str,
                      limit_num: int,
                      initial_cash: float,
                      ma_short: int,
                      ma_long: int,
                      db_mode: str = 'legacy',
                      db_folder: str = None,
                      stake_qty: int = 10000,
                      trade_mode: str = 'long_only',
                      jx1: int = 5,
                      jx2: int = 10,
                      jx3: int = 20,
                      jx4: int = 30,
                      jx5: int = 60,
                      粘合阈值: float = 0.0015,
                      ma4附近阈值: float = 0.002):
    # 构建数据库路径（legacy 使用原有库，baostock 使用下载库，crypto 使用加密货币库）
    if db_mode == 'crypto':
        # 加密货币数据库在当前目录
        if code == 'BTC':
            db_path = 'btc_data.db'
            table_name = 'btc_daily'
        elif code == 'ETH':
            db_path = 'eth_data.db'
            table_name = 'eth_daily'
        else:
            raise ValueError(f'不支持的加密货币代码: {code}')

        df = load_df_generic(db_path, table_name, limit_num, code)
        # 使用公共函数计算策略信号
        df = calculate_strategy_signals(df, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)
    elif db_mode == 'baostock':
        base_folder = db_folder or os.path.join(os.getcwd(), 'gupiao_baostock')
        db_path = os.path.join(base_folder, f'{code}_data.db')
        df = load_df_generic(db_path, table_name, limit_num, code)
        # 使用公共函数计算策略信号
        df = calculate_strategy_signals(df, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)
    else:
        db_zhumulu_folder = db_folder or r'D:\\gupiao_sql'
        model_folder_mc = code + '_data.db'
        db_path = os.path.join(db_zhumulu_folder, model_folder_mc)
        df = caiji_yuce_jiaoyizhibiao(db_path, table_name, limit_num, code, ma_short=ma_short, ma_long=ma_long,
                                     jx1=jx1, jx2=jx2, jx3=jx3, jx4=jx4, jx5=jx5, 
                                     粘合阈值=粘合阈值, ma4附近阈值=ma4附近阈值)

    bt_config = BacktestConfig()
    cerebro = bt.Cerebro()
    # 清空上一轮回测统计
    with open("portfolio_单.csv", 'w', newline='') as _f:
        pass
    # 覆盖初始资金
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=bt_config.commission_rate)
    cerebro.addsizer(bt.sizers.FixedSize, stake=int(stake_qty))

    df['做多'] = df['上下穿多'].astype(float)
    df['做空'] = df['上下穿空'].astype(float)
    df.index = pd.to_datetime(df.index)
    data = SQLiteData(dataname=df)
    cerebro.adddata(data)
    # 交易方向：'long_only' / 'short_only' / 'both'
    if trade_mode not in ['long_only', 'short_only', 'both']:
        trade_mode = 'both'
    cerebro.addstrategy(SimpleStrategy, df=df, trade_mode=trade_mode)
    cerebro.addobserver(PortfolioObserver)

    results = cerebro.run()
    asset_list = results[0].get_asset_list()
    direction_list = results[0].get_direction()
    df['direction_list'] = direction_list
    多开_output_zb1 = IF(df['direction_list'] == 1, 1, 0)
    多开_output_zb2 = IF(REF(df['direction_list'], 1) != 1, 1, 0)
    多开_output = IF(多开_output_zb1 + 多开_output_zb2 == 2, 1, 0)
    空开_output_zb1 = IF(df['direction_list'] == -1, 1, 0)
    空开_output_zb2 = IF(REF(df['direction_list'], 1) != -1, 1, 0)
    空开_output = IF(空开_output_zb1 + 空开_output_zb2 == 2, 1, 0)
    空仓_output_zb1 = IF(df['direction_list'] == 0, 1, 0)
    空仓_output_zb2 = IF(REF(df['direction_list'], 1) != 0, 1, 0)
    空仓_output = IF(空仓_output_zb1 + 空仓_output_zb2 == 2, 1, 0)
    net_profit_list = [value - initial_cash for value in asset_list]
    df['net_profit_list'] = net_profit_list
    df['多开_output'] = 多开_output
    df['空开_output'] = 空开_output
    df['空仓_output'] = 空仓_output

    # 胜率/盈亏比采用已平仓口径
    if os.path.exists("portfolio_单.csv") and os.path.getsize("portfolio_单.csv") > 0:
        df_portfolio = pd.read_csv("portfolio_单.csv", header=None)
        win_rate = df_portfolio.iloc[-1, 0]
        profit_loss_ratio = df_portfolio.iloc[-1, 1]
    else:
        win_rate = 0
        profit_loss_ratio = 0

    final_value = cerebro.broker.getvalue()
    profit = final_value - initial_cash

    # 生成图表
    columns_to_include = df.columns.tolist()
    zhibiaomc = f'{table_name}_deepseek{code}预测交易多空hb_回测'
    data_dict = {col: df[col] for col in columns_to_include}
    data_dict['date'] = df.index
    huatucs(data_dict, code, table_name, zhibiaomc)

    # 猜测/搜寻输出的HTML
    chart_path = None
    try:
        # 常见命名以 kdj_chart_ 开头
        cand = [f for f in os.listdir('.') if f.startswith('kdj_chart_') and f.endswith('.html')]
        chart_path = max(cand, key=lambda p: os.path.getmtime(p)) if cand else None
    except Exception:
        chart_path = None

    return {
        'final_value': final_value,
        'profit': profit,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'chart_path': chart_path,
        'df': df
    }


def run_backtest_remote(code: str,
                       table_name: str,
                       limit_num: int,
                       initial_cash: float,
                       ma_short: int,
                       ma_long: int,
                       stake_qty: int = 10000,
                       trade_mode: str = 'long_only',
                       jx1: int = 5,
                       jx2: int = 10,
                       jx3: int = 20,
                       jx4: int = 30,
                       jx5: int = 60,
                       粘合阈值: float = 0.0015,
                       ma4附近阈值: float = 0.002):
    """从远程数据库运行策略回测（用于指定期货）"""
    try:
        import pymysql
        import pandas as pd
        import numpy as np
        
        # 远程数据库配置
        mysql_config = {
            'host': '115.159.44.226',
            'port': 3306,
            'user': 'qihuo',
            'password': 'Hejdf3KdfaTt4h3w',
            'database': 'qihuo',
            'charset': 'utf8mb4',
            'autocommit': True
        }
        
        # 连接远程数据库
        conn = pymysql.connect(**mysql_config)
        cursor = conn.cursor()
        
        # 根据交易周期选择表名（直接使用远程已存在的聚合表）
        if table_name == "min_data3":
            sql_table = "hf_HSI_min3"
        elif table_name == "min_data5":
            sql_table = "hf_HSI_min5"
        elif table_name == "min_data10":
            sql_table = "hf_HSI_min10"
        elif table_name == "min_data15":
            sql_table = "hf_HSI_min15"
        elif table_name == "min_data30":
            sql_table = "hf_HSI_min30"
        elif table_name == "min_data60":
            sql_table = "hf_HSI_min60"
        else:
            sql_table = "hf_HSI_min1"  # 默认1分钟数据
        
        sql = f"""
        SELECT datetime, open, high, low, close, volume
        FROM {sql_table} 
        ORDER BY datetime DESC 
        LIMIT %s
        """
        
        cursor.execute(sql, (limit_num,))
        results = cursor.fetchall()
        conn.close()
        
        # 转换为DataFrame格式
        data = []
        for row in results:
            data.append({
                'datetime': row[0],
                'open': float(row[1]),
                'high': float(row[2]),
                'low': float(row[3]),
                'close': float(row[4]),
                'volume': float(row[5])
            })
        
        if not data:
            return {
                'final_value': initial_cash,
                'profit': 0,
                'win_rate': 0,
                'profit_loss_ratio': 0,
                'chart_path': None,
                'df': None
            }
        
        # 转换为DataFrame
        df = pd.DataFrame(data)
        df['datetime'] = pd.to_datetime(df['datetime'])
        df = df.sort_values('datetime')
        df.set_index('datetime', inplace=True)
        
        # 使用公共函数计算策略信号
        df = calculate_strategy_signals(df, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)
        
        # 执行回测逻辑（简化版）
        bt_config = BacktestConfig()
        cerebro = bt.Cerebro()
        
        # 清空上一轮回测统计
        with open("portfolio_单.csv", 'w', newline='') as _f:
            pass
        
        # 覆盖初始资金
        cerebro.broker.setcash(initial_cash)
        cerebro.broker.setcommission(commission=bt_config.commission_rate)
        cerebro.addsizer(bt.sizers.FixedSize, stake=int(stake_qty))

        df['做多'] = df['上下穿多'].astype(float)
        df['做空'] = df['上下穿空'].astype(float)
        df.index = pd.to_datetime(df.index)
        data = SQLiteData(dataname=df)
        cerebro.adddata(data)
        
        # 交易方向
        if trade_mode not in ['long_only', 'short_only', 'both']:
            trade_mode = 'both'
        cerebro.addstrategy(SimpleStrategy, df=df, trade_mode=trade_mode)
        cerebro.addobserver(PortfolioObserver)

        results = cerebro.run()
        asset_list = results[0].get_asset_list()
        direction_list = results[0].get_direction()
        df['direction_list'] = direction_list
        
        多开_output_zb1 = IF(df['direction_list'] == 1, 1, 0)
        多开_output_zb2 = IF(REF(df['direction_list'], 1) != 1, 1, 0)
        多开_output = IF(多开_output_zb1 + 多开_output_zb2 == 2, 1, 0)
        空开_output_zb1 = IF(df['direction_list'] == -1, 1, 0)
        空开_output_zb2 = IF(REF(df['direction_list'], 1) != -1, 1, 0)
        空开_output = IF(空开_output_zb1 + 空开_output_zb2 == 2, 1, 0)
        空仓_output_zb1 = IF(df['direction_list'] == 0, 1, 0)
        空仓_output_zb2 = IF(REF(df['direction_list'], 1) != 0, 1, 0)
        空仓_output = IF(空仓_output_zb1 + 空仓_output_zb2 == 2, 1, 0)
        net_profit_list = [value - initial_cash for value in asset_list]
        df['net_profit_list'] = net_profit_list
        df['多开_output'] = 多开_output
        df['空开_output'] = 空开_output
        df['空仓_output'] = 空仓_output

        # 胜率/盈亏比采用已平仓口径
        if os.path.exists("portfolio_单.csv") and os.path.getsize("portfolio_单.csv") > 0:
            df_portfolio = pd.read_csv("portfolio_单.csv", header=None)
            win_rate = df_portfolio.iloc[-1, 0]
            profit_loss_ratio = df_portfolio.iloc[-1, 1]
        else:
            win_rate = 0
            profit_loss_ratio = 0

        final_value = cerebro.broker.getvalue()
        profit = final_value - initial_cash

        # 生成图表
        columns_to_include = df.columns.tolist()
        zhibiaomc = f'{table_name}_deepseek{code}预测交易多空hb_回测'
        data_dict = {col: df[col] for col in columns_to_include}
        data_dict['date'] = df.index
        huatucs(data_dict, code, table_name, zhibiaomc)

        # 猜测/搜寻输出的HTML
        chart_path = None
        try:
            # 常见命名以 kdj_chart_ 开头
            cand = [f for f in os.listdir('.') if f.startswith('kdj_chart_') and f.endswith('.html')]
            chart_path = max(cand, key=lambda p: os.path.getmtime(p)) if cand else None
            print(f"找到图表文件: {chart_path}")
        except Exception as e:
            print(f"搜索图表文件失败: {e}")
            chart_path = None

        return {
            'final_value': final_value,
            'profit': profit,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'chart_path': chart_path,
            'df': df
        }
        
    except Exception as e:
        print(f"远程数据库策略运行失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'final_value': initial_cash,
            'profit': 0,
            'win_rate': 0,
            'profit_loss_ratio': 0,
            'chart_path': None,
            'df': None
        }


def run_backtest(code: str,
                 table_name: str,
                 limit_num: int,
                 initial_cash: float,
                 ma_short: int,
                 ma_long: int,
                 db_mode: str = 'legacy',
                 db_folder: str = None,
                 stake_qty: int = 10000,
                 trade_mode: str = 'long_only',
                 jx1: int = 5,
                 jx2: int = 10,
                 jx3: int = 20,
                 jx4: int = 30,
                 jx5: int = 60,
                 粘合阈值: float = 0.0015,
                 ma4附近阈值: float = 0.002):
    """统一的策略运行接口，根据db_mode选择不同的实现"""
    if db_mode == 'remote':
        return run_backtest_remote(code, table_name, limit_num, initial_cash, ma_short, ma_long,
                                 stake_qty, trade_mode, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)
    else:
        return run_backtest_local(code, table_name, limit_num, initial_cash, ma_short, ma_long,
                                db_mode, db_folder, stake_qty, trade_mode, jx1, jx2, jx3, jx4, jx5, 粘合阈值, ma4附近阈值)


def load_df_generic(db_path: str, table_name: str, limit_num: int, code: str) -> pd.DataFrame:
    # 从 sqlite 装载数据，兼容两类结构：
    # - 原有库：列 time, high, low, open, close, vol, code
    # - BaoStock 库：列 date, code, open, high, low, close, volume, ...
    # 返回索引为时间，包含 high, low, open, close, vol, code
    if not os.path.exists(db_path):
        raise FileNotFoundError(f'数据库不存在: {db_path}')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    try:
        c.execute(f"PRAGMA table_info({table_name})")
        cols = [r[1] for r in c.fetchall()]
        if 'time' in cols:
            query = f"SELECT time, high, low, open, close, vol, code FROM {table_name} WHERE code=? ORDER BY time DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(code, limit_num))
            df.rename(columns={'time': 'date'}, inplace=True)
        elif 'date' in cols:
            vol_col = 'volume' if 'volume' in cols else ('vol' if 'vol' in cols else None)
            if vol_col is None:
                raise ValueError('未找到成交量字段(volume/vol)')
            query = f"SELECT date, high, low, open, close, {vol_col} as vol, code FROM {table_name} WHERE code=? ORDER BY date DESC LIMIT ?"
            df = pd.read_sql_query(query, conn, params=(code, limit_num))
        else:
            raise ValueError('未知表结构，缺少 time/date 字段')
        df = df.iloc[::-1].copy()
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df
    finally:
        c.close()
        conn.close()


def update_chart():
    start_time_daima = time.time()
    now_2 = datetime.datetime.now()
    current_time = now_2.strftime("%H:%M")  # 获取当前时间
    print(f'刷新时间：{current_time}')
    current_weekday = now_2.weekday()  # 获取当前星期几（0-6，0代表星期一）
    # print(current_weekday)
    if current_weekday <= 5:  # 0-4代表星期一到星期五

        table_name = "min_data5"
        table_level = "15"  # 用于向前推一些数据不训练
        limit_num = 4000
        code = 'sh.600030'  # 修改
        zig_x = 0.02  # zig参数
        # 设置生成文件目录#修改的地方
        db_zhumulu_folder = r'D:\gupiao_sql'
        model_folder_mc = code + '_data.db'
        db_path = os.path.join(db_zhumulu_folder, model_folder_mc)
        df = caiji_yuce_jiaoyizhibiao(db_path, table_name, limit_num, code)

        print('四合一预测完毕')
        print('开始计算指标')

        bt_config = BacktestConfig()
        cerebro = bt.Cerebro()
        # 清空上一轮回测的逐笔统计文件，避免跨次运行的尾行干扰本次结果
        with open("portfolio_单.csv", 'w', newline='') as _f:
            pass
        cerebro.broker.setcash(bt_config.initial_cash)
        cerebro.broker.setcommission(commission=bt_config.commission_rate)
        cerebro.addsizer(bt.sizers.FixedSize, stake=bt_config.xdsl * bt_config.multiplier)
        # cerebro.addsizer(bt.sizers.PercentSizer, percents=100)
        df['做多'] = df['上下穿多'].astype(float)
        df['做空'] = df['上下穿空'].astype(float)
        # 将索引转换为时间戳格式
        df.index = pd.to_datetime(df.index)
        data = SQLiteData(dataname=df)
        cerebro.adddata(data)
        # 只做多模式
        cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='long_only')

        # 只做空模式
        # cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='short_only')

        # 双向交易模式
        # cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='both')
        # cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='long_only')
        cerebro.addobserver(PortfolioObserver)

        results = cerebro.run()
        asset_list = results[0].get_asset_list()
        direction_list = results[0].get_direction()
        # print(direction_list)
        df['direction_list'] = direction_list
        多开_output_zb1 = IF(df['direction_list'] == 1, 1, 0)
        多开_output_zb2 = IF(REF(df['direction_list'], 1) != 1, 1, 0)
        多开_output = IF(多开_output_zb1 + 多开_output_zb2 == 2, 1, 0)

        空开_output_zb1 = IF(df['direction_list'] == -1, 1, 0)
        空开_output_zb2 = IF(REF(df['direction_list'], 1) != -1, 1, 0)
        # print(空开_output_zb2)
        空开_output = IF(空开_output_zb1 + 空开_output_zb2 == 2, 1, 0)

        空仓_output_zb1 = IF(df['direction_list'] == 0, 1, 0)
        空仓_output_zb2 = IF(REF(df['direction_list'], 1) != 0, 1, 0)
        空仓_output = IF(空仓_output_zb1 + 空仓_output_zb2 == 2, 1, 0)
        # 计算净利润列表
        net_profit_list = [value - bt_config.initial_cash for value in asset_list]
        print(net_profit_list)
        df['net_profit_list'] = net_profit_list
        df['多开_output'] = 多开_output
        df['空开_output'] = 空开_output
        df['空仓_output'] = 空仓_output
        print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())
        print(df)
        # 读取portfolio_xxx.csv文件
        # 注意：文件可能为空（无成交），此时给出默认值
        if os.path.exists("portfolio_单.csv") and os.path.getsize("portfolio_单.csv") > 0:
            df_portfolio = pd.read_csv("portfolio_单.csv", header=None)
            win_rate = df_portfolio.iloc[-1, 0]
            profit_loss_ratio = df_portfolio.iloc[-1, 1]
            # 利润口径切换为“期末总资产-初始资金”，包含未平仓盈亏
            profit = cerebro.broker.getvalue() - bt_config.initial_cash
        else:
            win_rate = 0
            profit_loss_ratio = 0
            profit = cerebro.broker.getvalue() - bt_config.initial_cash
        # print(win_rate, profit_loss_ratio, profit)
        # 输出最终的胜率、盈亏比和利润
        print(f'最终胜率: {win_rate}%, 盈亏比: {profit_loss_ratio}, 利润: {profit}')
        # 检查胜率比较表.csv文件是否存在
        file_path = "胜率比较表.csv"
        if not os.path.exists(file_path):
            # 文件不存在，创建文件并写入表头
            with open(file_path, 'w') as file:
                file.write("contract_name,win_rate,profit_loss_ratio,profit\n")

        # 检查胜率比较表.csv文件中是否存在与contract_name相同的数据
        contract_name = code
        df_compare = pd.read_csv(file_path)
        if contract_name not in df_compare['contract_name'].values:
            # 在表中写入新数据
            with open(file_path, 'a') as file:
                file.write(f"{contract_name},{win_rate},{profit_loss_ratio},{profit}\n")
        # 获取 df 的所有列名
        # print(df.columns)
        columns_to_include = df.columns.tolist()
        # 批量创建 data 字典
        zhibiaomc = f'{table_name}_deepseek{code}预测交易多空hb_回测'
        data = {col: df[col] for col in columns_to_include}
        data['date'] = df.index
        huatucs(data, code, table_name, zhibiaomc)


# 添加回测参数配置
class BacktestConfig:
    def __init__(self):
        self.initial_cash = 10000000000.0
        self.multiplier = 1  # 合约乘数
        self.xdsl = 10  # 每次交易手数
        self.commission_rate = 0.00000  # 手续费率


class SQLiteData(bt.feeds.PandasData):
    params = (
        ('datetime', None),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('openinterest', -1),
        ('tick_size', 10),
    )


class SimpleStrategy(bt.Strategy):
    params = (
        ('df', None),  # DataFrame对象
        ('trade_mode', 'both'),  # 交易模式: 'long_only', 'short_only', 'both'
    )

    def __init__(self):
        self.df = self.params.df
        self.direction = 0  # 持仓方向：0空仓，1多仓，-1空仓
        self.asset_list = []  # 记录资产变化
        self.direction_list = []  # 记录持仓方向
        # 统计变量（基于成交回调结算）
        self.wins = 0
        self.total_trades = 0
        self.losses_total = 0.0
        self.win_total = 0.0
        self.win_lirun = 0.0
        self.wins_lv = 0.0
        self.win_losses_bi = 0.0
        self.csv_filename = "portfolio_单.csv"
        # 记录初始资金用于 ROI/净值口径
        self.initial_cash_at_start = float(self.broker.getvalue())
        print(f"DEBUG - 启动策略，trade_mode={self.p.trade_mode}")

        # 确保信号列存在且格式正确
        required_columns = ['做多', '做空']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"DataFrame必须包含{col}列")
            self.df[col] = self.df[col].astype(float)

    def next(self):
        try:
            # 1. 更新当前时间和资产
            self.current_datetime = pd.Timestamp(self.datetime.datetime())
            self.asset_list.append(self.broker.getvalue())

            # 2. 获取当前K线的信号
            try:
                做多_price = float(self.df.loc[self.current_datetime, '做多'])
                做空_price = float(self.df.loc[self.current_datetime, '做空'])
                print(f"DEBUG - 时间: {self.current_datetime}")
                print(f"DEBUG - 信号: 做多={做多_price}, 做空={做空_price}")
                print(f"DEBUG - 当前方向: {self.direction}")
            except KeyError:
                print(f"警告: 在{self.current_datetime}未找到对应的信号数据")
                return
            except ValueError:
                print(f"警告: 在{self.current_datetime}的信号数据格式错误")
                return

            # 3. 交易逻辑
            print(f"DEBUG - 模式: {self.p.trade_mode}, 做多={做多_price}, 做空={做空_price}, 方向={self.direction}")
            # 空仓状态
            if self.direction == 0:
                if self.p.trade_mode in ['long_only', 'both'] and 做多_price == 1:
                    print("DEBUG - 满足多侧开仓条件 -> buy()")
                    self.buy()
                    self.direction = 1
                    print(f'{self.current_datetime} - 开多仓')
                elif self.p.trade_mode in ['short_only', 'both'] and 做空_price == 1:
                    print("DEBUG - 满足空侧开仓条件 -> sell()")
                    self.sell()
                    self.direction = -1
                    print(f'{self.current_datetime} - 开空仓')

            # 持多仓状态
            elif self.direction == 1:
                if 做空_price == 1:
                    self.close()
                    if self.p.trade_mode == 'both':
                        self.sell()
                        self.direction = -1
                        print(f'{self.current_datetime} - 平多开空')
                    else:
                        self.direction = 0
                        print(f'{self.current_datetime} - 平多')

            # 持空仓状态
            elif self.direction == -1:
                if 做多_price == 1:
                    self.close()
                    if self.p.trade_mode == 'both':
                        self.buy()
                        self.direction = 1
                        print(f'{self.current_datetime} - 平空开多')
                    else:
                        self.direction = 0
                        print(f'{self.current_datetime} - 平空')

            # 4. 记录方向
            self.direction_list.append(self.direction)

        except Exception as e:
            print(f"错误发生在{self.current_datetime}: {str(e)}")
            self.direction_list.append(self.direction)  # 保持上一个方向

    def notify_trade(self, trade):
        # 仅在交易完全关闭时统计
        if not trade.isclosed:
            return
        pnl = float(trade.pnlcomm) if trade.pnlcomm is not None else float(trade.pnl)
        self.total_trades += 1
        if pnl > 0:
            self.wins += 1
            self.win_total += pnl
        else:
            self.losses_total += pnl
        # 计算衍生指标
        self.wins_lv = (self.wins / self.total_trades * 100.0) if self.total_trades > 0 else 0.0
        self.win_losses_bi = (self.win_total / abs(self.losses_total)) if abs(self.losses_total) > 0 else 0.0
        self.win_lirun = self.win_total + self.losses_total
        # 逐笔写入统计行（无表头）
        try:
            with open(self.csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([self.wins_lv, self.win_losses_bi, self.win_lirun])
        except Exception as _:
            pass
        # 打印成交结算
        print(
            f"成交结算 -> 交易次数: {self.total_trades} 盈利次数: {self.wins} 胜率: {self.wins_lv} 盈利总金额{self.win_total} 亏损总金额{self.losses_total} 盈亏比:{self.win_losses_bi} 利润:{self.win_lirun}")

    def stop(self):
        end_value = float(self.broker.get_value())
        pnl_abs = end_value - float(self.initial_cash_at_start)
        roi = pnl_abs / float(self.initial_cash_at_start)
        print(
            f'策略结束 - 初始资金: {self.initial_cash_at_start:.2f}, 期末资产: {end_value:.2f}, 绝对盈亏: {pnl_abs:.2f}, ROI: {roi:.6%}')

    def get_asset_list(self):
        return self.asset_list

    def get_direction(self):
        return self.direction_list


class PortfolioObserver(bt.Observer):
    lines = ('portfolio_value',)

    def __init__(self):
        self.trades = []  # 用于记录交易信息（可选）
        self.prev_direction = '空仓'
        self.prev_pos_price = 0  # 定义prev_pos_price属性
        self.prev_open_portfolio_value = 0  # 记录上一次开仓时的总资产

    def next(self):
        current_datetime = self._owner.current_datetime
        self.lines.portfolio_value[0] = self._owner.broker.getvalue()
        pos = self._owner.getposition(data=self._owner.datas[0])
        direction = '多头' if pos.size > 0 else ('空头' if pos.size < 0 else '空仓')
        if self.prev_direction == '空仓' and direction == '多头':
            self.prev_open_portfolio_value = self._owner.broker.getvalue()

        self.prev_direction = direction

        pos_price = pos.price
        Current_closing_price = self._owner.data.close[0]
        position_value = pos.size * Current_closing_price
        print(
            '%s - 总资产: %.2f, Direction: %s, 持仓数量: %s, 建仓价格: %.2f, 当前收盘价: %.2f, 持仓金额: %.2f' % (
                current_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._owner.broker.getvalue(), direction,
                pos.size, pos_price, Current_closing_price, position_value))
        # 逐bar不再打印统计，也不在此写入CSV，统计完全由策略的 notify_trade 负责

    def notify_trade(self, trade):
        self.trades.append(trade)

    def stop(self):
        # 在收尾时，从策略读取最终统计打印（若有交易）
        owner = self._owner
        try:
            print(
                f" 胜率: {getattr(owner, 'wins_lv', 0)}%, 盈亏比: {getattr(owner, 'win_losses_bi', 0)}, 利润: {getattr(owner, 'win_lirun', 0)}"
            )
        except Exception:
            pass


if __name__ == '__main__':
    # 直接使用远程服务器 5 分钟数据进行策略运行验证
    logging.basicConfig(
        filename='trading_log.txt',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    code = '恒指期货'
    table_name = 'min_data5'  # 对应远程表 hf_HSI_min5
    limit_num = 4000
    initial_cash = 10000000000.0
    ma_short = 20
    ma_long = 60
    stake_qty = 1  # 降低手数，避免因资金或乘数导致下单失败
    trade_mode = 'long_only'  # 可改为 'long_only' 或 'short_only' 做单侧验证

    result = run_backtest(
        code=code,
        table_name=table_name,
        limit_num=limit_num,
        initial_cash=initial_cash,
        ma_short=ma_short,
        ma_long=ma_long,
        db_mode='remote',
        stake_qty=stake_qty,
        trade_mode=trade_mode,
    )

    print(f"策略结束 - 初始资金: {initial_cash:.2f}, 期末资产: {result['final_value']:.2f}, 绝对盈亏: {result['profit']:.2f}")
    if result.get('chart_path'):
        print(f"找到图表文件: {result['chart_path']}")
    else:
        print('未找到图表文件')
