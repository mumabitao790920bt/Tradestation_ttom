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
# 导入超级趋势函数
from demo_supertrend import supertrend_tv
import pandas as pd
import numpy as np
import sqlite3
import os


def calculate_strategy_signals(df, jx1=5, jx2=10, jx3=20, jx4=30, jx5=60, 
                             粘合阈值=0.0015, ma4附近阈值=0.0012,
                             supertrend_length=10, supertrend_multiplier=3.0,
                            supertrend_length_60=10, supertrend_multiplier_60=3.0,
                             df_high: pd.DataFrame = None,
                             high_length: int = None,
                             high_multiplier: float = None,
                             take_profit_factor: float = 2.0,no_TakeProfit=0):
    """
    计算策略信号的核心函数 - 使用超级趋势指标
    直接返回包含所有策略指标的DataFrame
    
    参数:
    - df: 包含OHLCV数据的DataFrame
    - jx1-jx5: 均线参数（保留用于其他指标）
    - 粘合阈值: 五线粘合判断阈值 (默认0.0015)
    - ma4附近阈值: ma4附近上下范围阈值 (默认0.002)
    - supertrend_length: 超级趋势ATR长度 (默认10)
    - supertrend_multiplier: 超级趋势ATR倍数 (默认3.0)
    """
    # 计算均线（保留用于其他指标）
    print(df)
    print(df_high)
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
    # 使用超级趋势计算买卖信号

    
    # 直接调用超级趋势函数（单周期）
    supertrend_result = supertrend_tv(df, length=supertrend_length, multiplier=supertrend_multiplier, time_unit='s')
    
    # 处理60分钟数据（如果提供）

    supertrend_result_df_60 = supertrend_tv(df_high, length=supertrend_length_60, multiplier=supertrend_multiplier_60, time_unit='s')
    # print("60分钟超级趋势结果:")
    # print(f"DataFrame形状: {supertrend_result_df_60.shape}")
    # print(f"列名: {supertrend_result_df_60.columns.tolist()}")
    # print(f"数据类型:")
    # print(supertrend_result_df_60.dtypes)
    # print("所有数据:")
    # 设置pandas显示选项，不省略列
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)  # 显示所有行
    # print(df)
    # 恢复默认设置
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')
    pd.reset_option('display.max_rows')

    # 将超级趋势信号映射到原有变量名（15分钟）
    上下穿多 = supertrend_result['cjqs_d'].values  # 多头信号
    上下穿空 = supertrend_result['cjqs_k'].values  # 空头信号
    # 同步保存在df上，便于后续共振与出场判定
    df['cjqs_d'] = supertrend_result['cjqs_d'].values
    df['cjqs_k'] = supertrend_result['cjqs_k'].values
    df['cjqs_xz'] = supertrend_result['cjqs_xz'].values
    # 初始化60分钟数据列
    df['cjqs_d_60'] = 0
    df['cjqs_k_60'] = 0
    df['cjqs_xz_60'] = np.nan


    df_60_reindexed = supertrend_result_df_60.reindex(df.index, method='ffill')
    # 将新的DataFrame与15分钟的DataFrame对齐
    df['cjqs_d_60'] = df_60_reindexed['cjqs_d']
    df['cjqs_k_60'] = df_60_reindexed['cjqs_k']
    df['cjqs_xz_60'] = df_60_reindexed['cjqs_xz']

    
    # 双周期共振：入场信号
    df['long_entry'] = ((df['cjqs_d'] == 1) & (df['cjqs_d_60'] == 1)).astype(int)
    df['short_entry'] = ((df['cjqs_k'] == 1) & (df['cjqs_k_60'] == 1)).astype(int)
    df['卖60']=df['short_entry']
    df['买60'] = df['long_entry']
    买节点1=IF(REF(df['买60'],1)!=1,1,0)
    买节点=IF(买节点1+df['买60']==2,1,0)
    卖节点1=IF(REF(df['卖60'],1)!=1,1,0)
    卖节点=IF(卖节点1+df['卖60']==2,1,0)
    # 止损/止盈（以信号bar收盘价近似入场价）
    多持仓价格=MYREF(df['close'],MY_BARSLAST(买节点==1,1))
    多开仓时60cx=MYREF(df['cjqs_xz_60'],MY_BARSLAST(买节点==1,1))
    df['long_sl'] =多开仓时60cx#多持仓情况下的止损线
    df['long_tp'] = 多持仓价格+ (多持仓价格 - 多开仓时60cx) * take_profit_factor #多持仓情况下的止盈线 ，多持仓情况当价格突破则止盈

    多平1=IF(df['close']<=df['long_sl'],1,0)
    多平2 = IF(df['close'] >= df['long_tp'], 1, 0)
    非多止盈区=IF(多平2!=1,1,0)
    多开1=IF(REF(df['long_entry'],1)!=1,1,0)
    # 多开=IF(df['long_entry']+非多止盈区==2,1,0)
    多开 = IF(多开1 + df['long_entry'] == 2, 1, 0)
    # 15分钟反向强平
    df['long_exit_15'] = (df['cjqs_k'] == 1).astype(int)
    多平_a=IF(多平1+多平2+df['long_exit_15']>=1,1,0)
    多平_b=IF(df['long_exit_15']==1,1,0)
    多平=IF(no_TakeProfit==0,多平_a,多平_b)

    空持仓价格=MYREF(df['close'],MY_BARSLAST(卖节点==1,1))
    空开仓时60cx=MYREF(df['cjqs_xz_60'],MY_BARSLAST(卖节点==1,1))
    df['short_sl'] = 空开仓时60cx#空持仓情况下的止损线
    df['short_tp'] = 空持仓价格 - (空开仓时60cx-空持仓价格) * take_profit_factor#空持仓情况下的止盈线 ，空持仓情况当价格向下突破这条线则止盈

    空平1=IF(df['close']>=df['short_sl'],1,0)#止损平仓
    空平2 = IF(df['close'] <= df['short_tp'], 1, 0)#止盈平仓
    非空止盈区=IF(空平2!=1,1,0)

    空开1=IF(REF(df['short_entry'],1)!=1,1,0)
    空开 =IF(空开1+df['short_entry']== 2, 1, 0)
    # 空开 = IF(df['short_entry']+ 非空止盈区== 2, 1, 0)
    df['short_exit_15'] = (df['cjqs_d'] == 1).astype(int)
    空平_a=IF(空平1+空平2+df['short_exit_15']>=1,1,0)
    空平_b = IF(df['short_exit_15'] == 1, 1, 0)
    空平=IF(no_TakeProfit==0,空平_a,空平_b)
    # 将四个交易信号添加到DataFrame
    df['多开'] = 多开
    df['多平'] = 多平
    df['空开'] = 空开
    df['空平'] = 空平
    df['买节点'] = 买节点
    df['卖节点'] = 卖节点

    # 回测用映射
    df['上下穿多'] = 上下穿多
    df['上下穿空'] = 上下穿空
    df['m1'] = supertrend_result['cjqs_xz'].values
    df['m2'] = ma2
    df['m3'] = ma3
    df['m4'] = ma4
    df['m5'] = ma5
    df['五线差'] = 五线差
    df['五线比'] = 五线比
    df['粘合'] = 粘合
    df['ma4附近上'] = ma4附近上
    df['ma4附近下'] = ma4附近下
    df['买入_tj1']=买入_tj1
    df['上穿ma4附近']=上穿ma4附近
    df['无跌破']=无跌破
    # 添加超级趋势相关列
    df['supertrend_line'] = supertrend_result['cjqs_xz'].values
    df['supertrend_direction'] = supertrend_result['cjqs_d'].values - supertrend_result['cjqs_k'].values  # 1=多, -1=空, 0=无
    # 将共振信号作为做多/做空供回测
    df['做多'] = df['long_entry'].astype(float)
    df['做空'] = df['short_entry'].astype(float)
    # print('导入计算的df')
    # print(f"DataFrame形状: {df.shape}")
    # print(f"列名: {df.columns.tolist()}")
    # print(f"数据类型:")
    # print(df.dtypes)
    # print("所有数据:")
    # 设置pandas显示选项，不省略列
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)  # 显示所有行
    # print(df)
    # 恢复默认设置
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')
    pd.reset_option('display.max_rows')
    return df


def load_rb_data(db_path=r'D:\qihuo_sql\KQ.m@SHFE.rb_data.db', table_name='min_data15', limit_num=7000,
                 supertrend_length=10, supertrend_multiplier=3.0, code='BTCUSDT'):
    """
    专门加载数据的函数，支持按合约代码过滤
    """
    print(f'连接数据库: {db_path}')
    print(f'加载合约: {code}')
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 查询数据，按合约代码过滤
    query = f"SELECT time, high, low, open, close, vol, code FROM {table_name} WHERE code=? ORDER BY time DESC LIMIT {limit_num}"
    c.execute(query, (code,))
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        raise ValueError(f"未找到数据，请检查表 {table_name} 是否存在数据")
    
    # 转换为DataFrame
    df = pd.DataFrame(rows, columns=['time', 'high', 'low', 'open', 'close', 'vol', 'code'])
    # 兼容字符串时间与整数时间戳
    s_time = df['time']
    try:
        # 若是全数字，可按秒解析
        if pd.api.types.is_integer_dtype(s_time) or pd.api.types.is_float_dtype(s_time):
            df['time'] = pd.to_datetime(df['time'], unit='s', errors='coerce')
        else:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
    except Exception:
        df['time'] = pd.to_datetime(df['time'], errors='coerce')
    df = df.set_index('time')
    df = df.sort_index()  # 按时间升序排列
    
    # 数值化价格和成交量数据
    for col in ['open', 'high', 'low', 'close', 'vol']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    
    print(f"加载数据形状: {df.shape}")
    print("数据预览:")
    print(df.head())


    return df


def run_backtest_local(df, trade_mode, initial_cash=1000000.0, stake_qty=1, code='KQ.m@SHFE.rb', table_name='min_data15', db_path=''):
    # print('导入计算的df')
    # print(f"DataFrame形状: {df.shape}")
    # print(f"列名: {df.columns.tolist()}")
    # print(f"数据类型:")
    # print(df.dtypes)
    # print("所有数据:")
    # 设置pandas显示选项，不省略列
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.max_rows', None)  # 显示所有行
    # print(df)
    # 恢复默认设置
    pd.reset_option('display.max_columns')
    pd.reset_option('display.width')
    pd.reset_option('display.max_colwidth')
    pd.reset_option('display.max_rows')

    bt_config = BacktestConfig()
    cerebro = bt.Cerebro()
    # 清空上一轮回测统计
    with open("portfolio_单.csv", 'w', newline='') as _f:
        pass
    # 覆盖初始资金
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=bt_config.commission_rate)
    cerebro.addsizer(bt.sizers.FixedSize, stake=int(stake_qty))


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

    ##开始计算持仓数量
    df['chicang_qk'] = direction_list

    result_df = pd.DataFrame(
        {"Col1": df['close'], "Col2": df.index.strftime('%Y-%m-%d %H:%M:%S'), "Col3": df['code'],
         "Output": df['close'],
         "Predicted": df['chicang_qk']})
    # 增加功能 - 检查数据库是否有 sishi_chicangqk_predicted 表，如果没有创建
    if not db_path:
        db_path = 'binance_futures_data.db'  # 默认使用币安期货数据库
    print(f'链接数据库:{db_path}')
    conn = sqlite3.connect(db_path)
    # 创建 sishi_chicangqk_predicted 表
    conn.execute('''CREATE TABLE IF NOT EXISTS sishi_chicangqk_predicted
                                                                       (Col1 TEXT, Col2 TEXT, Col3 TEXT, Output REAL, Predicted REAL)''')
    conn.commit()
    # 获取最新的n条数据
    n = 500  # 读取最后5条数据
    latest_data = result_df.tail(n)
    # print(result_df)
    # 依次检查 sishi_chicangqk_predicted 表 col2 字段中是否有相同时间的数据
    cursor = conn.cursor()
    for _, row in latest_data.iterrows():
        cursor.execute("SELECT * FROM sishi_chicangqk_predicted WHERE Col2=?", (row['Col2'],))
        data_exists = cursor.fetchone()
        # 如果没有相同时间的数据，则写入
        if not data_exists:
            row_df = row.to_frame().T
            row_df.to_sql('sishi_chicangqk_predicted', conn, if_exists='append', index=False)
            # print(f'数据 {row} 已写入 sishi_chicangqk_predicted 表。')
        # else:
        #     print(f'数据 {row} 已存在，未写入 sishi_chicangqk_predicted 表。')

    gl_zdqr_result = df['chicang_qk'].iloc[-1]  # 读取最新的持仓数据
    print(f'当前策略持仓数量: {gl_zdqr_result}')
    
    # 关闭数据库连接
    conn.close()

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
        'df': df,
        'current_position': gl_zdqr_result  # 添加当前持仓信息
    }




# 对外单次运行函数：由GUI调用。加载数据→计算信号→可选回测→返回结果
def run_strategy_once(
        db_path: str,
        table_low: str,
        table_high: str,
        code: str,
        limit_num: int,
        take_profit_factor: float,
        supertrend_length: int,
        supertrend_multiplier: float,
        supertrend_length_60: int,
        supertrend_multiplier_60: float,
        trade_mode: str = 'both',
        do_backtest: bool = False,
        initial_cash: float = 1000000.0,
        stake_qty: int = 1,
        no_TakeProfit: int = 0,
    ):
    # 载入小周期
    df_low = load_rb_data(db_path=db_path, table_name=table_low, limit_num=limit_num,
                          supertrend_length=supertrend_length, supertrend_multiplier=supertrend_multiplier,
                          code=code)
    df_low['real_open']=df_low['open']
    df_low['real_high']=df_low['high']
    df_low['real_low']=df_low['low']
    df_low['real_close']=df_low['close']

    df_low['ha_close']=(df_low['open']+df_low['high']+df_low['low']+df_low['close'])/4
    df_low['ha_open']=(REF(df_low['open'],1)+REF(df_low['ha_close'],1))/2
    df_low['ha_high']=NthMaxList(1, df_low['high'], df_low['ha_open'], df_low['ha_close'])
    df_low['ha_low']=NthMinList(1, df_low['low'], df_low['ha_open'], df_low['ha_close'])

    df_low['open']=df_low['ha_open']
    df_low['high']=df_low['ha_high']
    df_low['low']=df_low['ha_low']
    df_low['close']=df_low['ha_close']
    # 载入大周期
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(f"SELECT time, high, low, open, close, vol, code FROM {table_high} WHERE code=? ORDER BY time ASC", (code,))
    rows_high = cur.fetchall()
    conn.close()
    df_high = pd.DataFrame(rows_high, columns=['time','high','low','open','close','vol','code'])
    df_high['time'] = pd.to_datetime(df_high['time'], errors='coerce')
    df_high = df_high.dropna(subset=['time']).set_index('time').sort_index()
    for _c in ['open','high','low','close','vol']:
        df_high[_c] = pd.to_numeric(df_high[_c], errors='coerce')
    df_high['real_open']=df_high['open']
    df_high['real_high']=df_high['high']
    df_high['real_low']=df_high['low']
    df_high['real_close']=df_high['close']

    df_high['ha_close']=(df_high['open']+df_high['high']+df_high['low']+df_high['close'])/4
    df_high['ha_open']=(REF(df_high['open'],1)+REF(df_high['ha_close'],1))/2
    df_high['ha_high']=NthMaxList(1, df_high['high'], df_high['ha_open'], df_high['ha_close'])
    df_high['ha_low']=NthMinList(1, df_high['low'], df_high['ha_open'], df_high['ha_close'])

    df_high['open']=df_high['ha_open']
    df_high['high']=df_high['ha_high']
    df_high['low']=df_high['ha_low']
    df_high['close']=df_high['ha_close']
    # 计算信号
    df_signals = calculate_strategy_signals(
        df_low,
        jx1=5, jx2=10, jx3=20, jx4=30, jx5=60,
        粘合阈值=0.0015, ma4附近阈值=0.0012,
        supertrend_length=supertrend_length, supertrend_multiplier=supertrend_multiplier,
        supertrend_length_60=supertrend_length_60, supertrend_multiplier_60=supertrend_multiplier_60,
        df_high=df_high,
        high_length=supertrend_length_60, high_multiplier=supertrend_multiplier_60,
        take_profit_factor=take_profit_factor,
        no_TakeProfit=no_TakeProfit
    )

    # 提取当前止损参考价（60分钟超级趋势线）与当前收盘价
    try:
        stop_ref_price = float(df_signals['cjqs_xz_60'].iloc[-1]) if 'cjqs_xz_60' in df_signals.columns else None
    except Exception:
        stop_ref_price = None
    try:
        latest_close_price = float(df_signals['close'].iloc[-1]) if 'close' in df_signals.columns else None
    except Exception:
        latest_close_price = None

    if stop_ref_price is not None:
        print(f"当前应持仓对应的 df['cjqs_xz_60']: {stop_ref_price}")
    if latest_close_price is not None:
        print(f"当前收盘价: {latest_close_price}")

    result = {
        'df': df_signals,
        'stats': {
            'long_signals': float(df_signals['long_entry'].sum()) if 'long_entry' in df_signals.columns else 0.0,
            'short_signals': float(df_signals['short_entry'].sum()) if 'short_entry' in df_signals.columns else 0.0,
        },
        'current_position': 0,  # 默认持仓为0
        'stop_ref_price': stop_ref_price,
        'latest_close_price': latest_close_price,
    }

    if do_backtest:
        bt_result = run_backtest_local(
            df=df_signals,
            trade_mode=trade_mode,
            initial_cash=initial_cash,
            stake_qty=stake_qty,
            code=code,
            table_name=table_low,
            db_path=db_path  # 传递数据库路径
        )
        result.update(bt_result)
        # 回测结果中也带出止损参考价，便于GUI传递给交易模块
        result['stop_ref_price'] = stop_ref_price
        result['latest_close_price'] = latest_close_price

    return result

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
        required_columns = ['多开', '多平', '空开', '空平']
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"DataFrame必须包含{col}列")
            self.df[col] = self.df[col].astype(float)

    def next(self):
        try:
            # 1. 更新当前时间和资产
            self.current_datetime = pd.Timestamp(self.datetime.datetime())
            self.asset_list.append(self.broker.getvalue())

            # 2. 获取当前K线的四个交易信号
            try:
                多开 = float(self.df.loc[self.current_datetime, '多开'])
                多平 = float(self.df.loc[self.current_datetime, '多平'])
                空开 = float(self.df.loc[self.current_datetime, '空开'])
                空平 = float(self.df.loc[self.current_datetime, '空平'])
                
                print(f"DEBUG - 时间: {self.current_datetime}")
                print(f"DEBUG - 信号: 多开={多开}, 多平={多平}, 空开={空开}, 空平={空平}")
                print(f"DEBUG - 当前方向: {self.direction}")
            except KeyError:
                print(f"警告: 在{self.current_datetime}未找到对应的信号数据")
                return
            except ValueError:
                print(f"警告: 在{self.current_datetime}的信号数据格式错误")
                return

            # 3. 交易逻辑
            print(f"DEBUG - 模式: {self.p.trade_mode}, 方向={self.direction}")
            
            # 空仓状态 (direction = 0)
            if self.direction == 0:
                # 做多买入
                if self.p.trade_mode in ['long_only', 'both'] and 多开 == 1:
                    print("DEBUG - 满足多开条件 -> buy()")
                    self.buy()
                    self.direction = 1
                    print(f'{self.current_datetime} - 开多仓')
                # 做空买入
                elif self.p.trade_mode in ['short_only', 'both'] and 空开 == 1:
                    print("DEBUG - 满足空开条件 -> sell()")
                    self.sell()
                    self.direction = -1
                    print(f'{self.current_datetime} - 开空仓')

            # 持多仓状态 (direction = 1)
            elif self.direction == 1:
                # 做多平仓
                if 多平 == 1:
                    print("DEBUG - 满足多平条件 -> close()")
                    self.close()
                    self.direction = 0
                    print(f'{self.current_datetime} - 平多仓')
                # 做空买入（先平多再开空）
                elif self.p.trade_mode == 'both' and 空开 == 1:
                    print("DEBUG - 满足空开条件（持多仓）-> close() + sell()")
                    self.close()
                    self.sell()
                    self.direction = -1
                    print(f'{self.current_datetime} - 平多开空')

            # 持空仓状态 (direction = -1)
            elif self.direction == -1:
                # 做空平仓
                if 空平 == 1:
                    print("DEBUG - 满足空平条件 -> close()")
                    self.close()
                    self.direction = 0
                    print(f'{self.current_datetime} - 平空仓')
                # 做多买入（先平空再开多）
                elif self.p.trade_mode == 'both' and 多开 == 1:
                    print("DEBUG - 满足多开条件（持空仓）-> close() + buy()")
                    self.close()
                    self.buy()
                    self.direction = 1
                    print(f'{self.current_datetime} - 平空开多')

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
        # print(
        #     f"成交结算 -> 交易次数: {self.total_trades} 盈利次数: {self.wins} 胜率: {self.wins_lv} 盈利总金额{self.win_total} 亏损总金额{self.losses_total} 盈亏比:{self.win_losses_bi} 利润:{self.win_lirun}")

    def stop(self):
        end_value = float(self.broker.get_value())
        pnl_abs = end_value - float(self.initial_cash_at_start)
        roi = pnl_abs / float(self.initial_cash_at_start)
        # print(
        #     f'策略结束 - 初始资金: {self.initial_cash_at_start:.2f}, 期末资产: {end_value:.2f}, 绝对盈亏: {pnl_abs:.2f}, ROI: {roi:.6%}')

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
        # print(
        #     '%s - 总资产: %.2f, Direction: %s, 持仓数量: %s, 建仓价格: %.2f, 当前收盘价: %.2f, 持仓金额: %.2f' % (
        #         current_datetime.strftime('%Y-%m-%d %H:%M:%S'), self._owner.broker.getvalue(), direction,
        #         pos.size, pos_price, Current_closing_price, position_value))
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
    # 切换为本地螺纹钢数据库（min_data15）作为主周期入口
    logging.basicConfig(
        filename='trading_log.txt',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    # 本地参数
    code = 'KQ.m@SHFE.rb'
    table_name = 'min_data15'
    limit_num = 7000
    db_path_local = r'D:\qihuo_sql\KQ.m@SHFE.rb_data.db'

    # 载入主周期数据
    df15 = load_rb_data(db_path=db_path_local, table_name=table_name, limit_num=limit_num,
                        supertrend_length=10, supertrend_multiplier=3.0)
    df15['real_open']=df15['open']
    df15['real_high']=df15['high']
    df15['real_low']=df15['low']
    df15['real_close']=df15['close']

    df15['ha_close']=(df15['open']+df15['high']+df15['low']+df15['close'])/4
    df15['ha_open']=(REF(df15['open'],1)+REF(df15['ha_close'],1))/2
    df15['ha_high']=NthMaxList(1, df15['high'], df15['ha_open'], df15['ha_close'])
    df15['ha_low']=NthMinList(1, df15['low'], df15['ha_open'], df15['ha_close'])

    df15['open']=df15['ha_open']
    df15['high']=df15['ha_high']
    df15['low']=df15['ha_low']
    df15['close']=df15['ha_close']

#     1.
#     收盘价（HA - Close）
#     当前周期的实际开盘价、最高价、最低价、收盘价的平均值：
#     HA - Close = (实际开盘价 + 实际最高价 + 实际最低价 + 实际收盘价) / 4
    # 2.
    # 开盘价（HA - Open）
    # 前一周期HA - 开盘价与HA - 收盘价的平均值（引入滞后性，平滑趋势）：
    # HA - Open = (前一周期HA - Open + 前一周期HA - Close) / 2
    # 3.
    # 最高价（HA - High）
    # 当前实际最高价、HA - 开盘价、HA - 收盘价三者中的最大值：
    # HA - High = max(实际最高价, HA - Open, HA - Close)
    # 4.
    # 最低价（HA - Low）
    # 当前实际最低价、HA - 开盘价、HA - 收盘价三者中的最小值：
    # HA - Low = min(实际最低价, HA - Open, HA - Close)
    # 载入60分钟数据（作为高周期），供 calculate_strategy_signals 可选对齐使用

    conn = sqlite3.connect(db_path_local)
    cur = conn.cursor()
    cur.execute("SELECT time, high, low, open, close, vol, code FROM min_data60 WHERE code=? ORDER BY time ASC", (code,))
    rows60 = cur.fetchall()
    conn.close()
    df60 = pd.DataFrame(rows60, columns=['time','high','low','open','close','vol','code'])
    df60['time'] = pd.to_datetime(df60['time'], errors='coerce')
    df60 = df60.dropna(subset=['time']).set_index('time').sort_index()
    for _c in ['open','high','low','close','vol']:
        df60[_c] = pd.to_numeric(df60[_c], errors='coerce')
    df60['real_open']=df60['open']
    df60['real_high']=df60['high']
    df60['real_low']=df60['low']
    df60['real_close']=df60['close']

    df60['ha_close']=(df60['open']+df60['high']+df60['low']+df60['close'])/4
    df60['ha_open']=(REF(df60['open'],1)+REF(df60['ha_close'],1))/2
    df60['ha_high']=NthMaxList(1, df60['high'], df60['ha_open'], df60['ha_close'])
    df60['ha_low']=NthMinList(1, df60['low'], df60['ha_open'], df60['ha_close'])

    df60['open']=df60['ha_open']
    df60['high']=df60['ha_high']
    df60['low']=df60['ha_low']
    df60['close']=df60['ha_close']
    # 调用双周期共振策略
    print('本地15分钟与60分钟数据加载完成:')
    print('df15 shape:', df15.shape)
    print('df60 shape:', df60.shape)
    
    # 计算双周期共振策略信号
    df_with_signals = calculate_strategy_signals(
        df15, 
        jx1=5, jx2=10, jx3=20, jx4=30, jx5=60,
        粘合阈值=0.0015, ma4附近阈值=0.0012,
        supertrend_length=10, supertrend_multiplier=3.0,
        supertrend_length_60=10, supertrend_multiplier_60=3.0,
        df_high=df60,  # 传入60分钟数据
        high_length=10, high_multiplier=3.0,
        take_profit_factor=4.0
    )
    
    print('双周期共振策略信号计算完成')
    print('信号统计:')
    print(f'做多信号数量: {df_with_signals["做多"].sum()}')
    print(f'做空信号数量: {df_with_signals["做空"].sum()}')
    print(f'多头入场信号: {df_with_signals["long_entry"].sum()}')
    print(f'空头入场信号: {df_with_signals["short_entry"].sum()}')
    
    # 运行回测
    result = run_backtest_local(
        df=df_with_signals,
        trade_mode='both',
        initial_cash=1000000.0,
        stake_qty=1,
        code=code,
        table_name=table_name
    )
    
    # print(f"策略结束 - 初始资金: 1000000.0, 期末资产: {result['final_value']:.2f}, 绝对盈亏: {result['profit']:.2f}")
    if result.get('chart_path'):
        print(f"找到图表文件: {result['chart_path']}")
    else:
        print('未找到图表文件')


