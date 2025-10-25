import datetime
import logging
import json
import os
from pyecharts.charts import *
import MyTT
from sklearn.preprocessing import StandardScaler
import torch.nn as nn
import csv
import torch.nn.init as init
import configparser
import sqlite3
import time
from MyTT import *
from pyecharts.charts import Kline
from pyecharts.charts import Line
from pyecharts.globals import ThemeType
from pyecharts import options as opts
from pyecharts.charts import Bar, EffectScatter
import pandas as pd
import webbrowser
from pyecharts.render import make_snapshot
from snapshot_selenium import snapshot
from data_processing import *
from visualization import *


# 修改qushi函数的返回值处理
def qushi(df, wz1, wz2, price1, price2):  # 画射线趋势线函数
    # 添加数据类型转换和预处理
    wz1 = np.array(wz1, dtype=float)
    wz2 = np.array(wz2, dtype=float)
    price1 = np.array(price1, dtype=float)
    price2 = np.array(price2, dtype=float)

    # 添加详细的数据检查
    # print("\n数据详细检查:")
    # print(f"wz1 范围: 最小值={np.min(wz1)}, 最大值={np.max(wz1)}")
    # print(f"wz2 范围: 最小值={np.min(wz2)}, 最大值={np.max(wz2)}")
    # print(f"price1 范围: 最小值={np.nanmin(price1)}, 最大值={np.nanmax(price1)}")
    # print(f"price2 范围: 最小值={np.nanmin(price2)}, 最大值={np.nanmax(price2)}")

    trend_lines = []
    trend_lines_valid = []
    valid_count = 0

    # 遍历每一行数据
    for i in range(len(df)):
        try:
            index_wz1 = int(i - wz1[i])  # 确保索引是整数
            index_wz2 = int(i - wz2[i])
            #
            # print(f"\n处理点 {i}:")
            # print(f"原始值: wz1={wz1[i]}, wz2={wz2[i]}")
            # print(f"计算索引: index_wz1={index_wz1}, index_wz2={index_wz2}")

            # 检查索引有效性
            if index_wz1 < 0 or index_wz2 < 0 or index_wz1 >= len(df) or index_wz2 >= len(df):
                trend_lines.append(np.nan)
                trend_lines_valid.append(0)
                continue

            # 检查价格有效性
            if np.isnan(price1[i]) or np.isnan(price2[i]):
                trend_lines.append(np.nan)
                trend_lines_valid.append(0)
                continue

            x = np.array([index_wz1, index_wz2], dtype=float)
            y = np.array([price1[i], price2[i]], dtype=float)

            # 检查x值是否相同
            if x[0] == x[1]:
                trend_lines.append(np.nan)
                trend_lines_valid.append(0)
                continue

            m = (y[1] - y[0]) / (x[1] - x[0])  # 计算斜率
            b = y[0] - m * x[0]

            trend_value = m * i + b  # 简化计算，只计算当前点的值
            trend_lines.append(trend_value)

            # 判断趋势线方向
            if m <= 0:
                trend_lines_valid.append(1)
                valid_count += 1
            else:
                trend_lines_valid.append(0)

        except Exception as e:
            print(f"计算出错，位置 {i}:")
            print(f"错误: {str(e)}")
            trend_lines.append(np.nan)
            trend_lines_valid.append(0)

    # 创建有效趋势线序列
    trend_lines = np.array(trend_lines)
    trend_lines_valid = np.array(trend_lines_valid)
    trend_line_effective = np.where(trend_lines_valid == 1, trend_lines, np.nan)

    # print(f"\n处理结果统计:")
    # print(f"有效趋势线数量: {valid_count}")
    # print(f"有效率: {valid_count / len(df) * 100:.2f}%")
    # print(f"非nan值的数量: {np.sum(~np.isnan(trend_line_effective))}")

    return trend_lines, trend_lines_valid, trend_line_effective


def extend_trend_line(trend_line, extend_periods=20, df_index=None):
    """延伸趋势线
    在原有时间序列的基础上填充延伸数据
    """
    print("\n开始延伸趋势线分析...")
    trend_line = np.array(trend_line)
    extended_line = trend_line.copy()
    valid_indices = np.where(~np.isnan(trend_line))[0]

    if len(valid_indices) < 2:
        print("警告：总有效点少于2个，无法延伸")
        return trend_line

    # 找出所有连续的有效数据段
    segments = []
    current_segment = [valid_indices[0]]

    for i in range(1, len(valid_indices)):
        if valid_indices[i] == valid_indices[i - 1] + 1:
            current_segment.append(valid_indices[i])
        else:
            if len(current_segment) >= 2:
                segments.append(current_segment)
            current_segment = [valid_indices[i]]

    if len(current_segment) >= 2:
        segments.append(current_segment)

    # 处理每一段连续数据
    for segment in segments:
        # if df_index is not None:
        #     print(f"\n处理连续段: {df_index[segment[0]]} 到 {df_index[segment[-1]]}")

        # 使用段的最后两个点计算斜率
        last_idx = segment[-1]
        prev_idx = segment[-2]

        # 计算斜率
        slope = (trend_line[last_idx] - trend_line[prev_idx]) / (last_idx - prev_idx)
        last_value = trend_line[last_idx]

        # 在原时间序列上延伸
        extend_count = 0
        current_idx = last_idx + 1

        while extend_count < extend_periods and current_idx < len(trend_line):
            if np.isnan(extended_line[current_idx]):  # 只在原来无效的位置填充延伸数据
                extended_value = last_value + slope * (current_idx - last_idx)
                extended_line[current_idx] = extended_value
                # if df_index is not None:
                #     print(f"延伸点: 时间 {df_index[current_idx]}, 值 {extended_value:.2f}")
                extend_count += 1
            current_idx += 1

    # 打印延伸结果统计
    if df_index is not None:
        original_valid = np.sum(~np.isnan(trend_line))
        extended_valid = np.sum(~np.isnan(extended_line))
        # print(f"\n原始有效点数量: {original_valid}")
        # print(f"延伸后有效点数量: {extended_valid}")
        # print(f"新增点数量: {extended_valid - original_valid}")

    return extended_line


def qushi_buy(df, wz1, wz2, price1, price2):  # 画射线买入趋势线函数
    # 确保输入的长度一致
    if not (len(wz1) == len(wz2) == len(price1) == len(price2) == len(df)):
        raise ValueError("输入数组长度必须与df长度相同")

    trend_lines = []
    trend_lines_valid = []  # 新增有效趋势线标记列表

    # 遍历每一行数据
    for i in range(len(df)):
        index_wz1 = i - wz1[i]
        index_wz2 = i - wz2[i]

        if index_wz1 < 0 or index_wz2 < 0:
            trend_lines.append(np.nan)
            trend_lines_valid.append(0)  # 无效趋势线标记为0
            continue

        x = np.array([index_wz1, index_wz2])
        y = np.array([price1[i], price2[i]])

        m = (y[1] - y[0]) / (x[1] - x[0])  # 计算斜率
        b = y[0] - m * x[0]

        trend_value = m * np.arange(i + 1) + b
        trend_lines.append(trend_value[-1])

        # 判断趋势线方向
        # m > 0 表示向上的趋势（与qushi函数相反）
        trend_lines_valid.append(1 if m > 0 else 0)

    # 创建有效趋势线序列（无效的设为NaN）
    trend_line_effective = np.where(np.array(trend_lines_valid) == 1, trend_lines, np.nan)
    # print(trend_line_effective)
    return np.array(trend_lines), np.array(trend_lines_valid), np.array(trend_line_effective)


def sell_out_qsx_gjd(sqszzh_sell_jiedian, 指导价, jl):
    # 处理卖出信号
    sqszzh_sell_jiedian_wz1 = MY_BARSLAST(sqszzh_sell_jiedian, 1)

    # 寻找满足间隔要求的wz2
    n = 2  # 从2开始，因为1已经用于wz1
    found = False
    max_n =1000

    while n <= max_n:
        bars_last = MY_BARSLAST(sqszzh_sell_jiedian, n)
        # 检查是否存在大于jl的间隔
        if np.any(bars_last > jl):
            found = True
            sqszzh_sell_jiedian_wz2 = bars_last
            # print(f"找到合适的n={n}, 对应的bars_last值为:", bars_last)
            break
        n += 1

    if not found:
        # 如果没找到合适的wz2，使用默认值
        sqszzh_sell_jiedian_wz2 = MY_BARSLAST(sqszzh_sell_jiedian, 2)+jl

    # 获取对应的价格
    sqszzh_sell_jiedian_price1 = MYREF(指导价, sqszzh_sell_jiedian_wz1) * 1.2
    sqszzh_sell_jiedian_price2 = MYREF(指导价, sqszzh_sell_jiedian_wz2) * 1.2

    return sqszzh_sell_jiedian_wz1, sqszzh_sell_jiedian_wz2, sqszzh_sell_jiedian_price1, sqszzh_sell_jiedian_price2


def buy_out_qsx_gjd(sqszzh_buy_jiedian, 指导价, jl):
    # 处理买入信号
    sqszzh_buy_jiedian_wz1 = MY_BARSLAST(sqszzh_buy_jiedian, 1)

    # 寻找满足间隔要求的wz2
    n = 2  # 从2开始，因为1已经用于wz1
    found = False
    max_n = 1000

    while n <= max_n:
        bars_last = MY_BARSLAST(sqszzh_buy_jiedian, n)
        # 检查是否存在大于jl的间隔
        if np.any(bars_last > jl):
            found = True
            sqszzh_buy_jiedian_wz2 = bars_last
            # print(f"找到合适的n=buy_out_qsx_gjd{n}, 对应的bars_last值为:", bars_last)
            break
        n += 1

    if not found:
        # 如果没找到合适的wz2，使用默认值
        sqszzh_buy_jiedian_wz2 = MY_BARSLAST(sqszzh_buy_jiedian, 2)+jl

    # 获取对应的价格
    sqszzh_buy_jiedian_price1 = MYREF(指导价, sqszzh_buy_jiedian_wz1) * 0.8
    sqszzh_buy_jiedian_price2 = MYREF(指导价, sqszzh_buy_jiedian_wz2) * 0.8

    return sqszzh_buy_jiedian_wz1, sqszzh_buy_jiedian_wz2, sqszzh_buy_jiedian_price1, sqszzh_buy_jiedian_price2


def shu9(指导价):
    # 指导价 =主动买多动量
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
    return sqsz_9_gaopao,sqsz_9_dixi

def zlzdmr_qsx(df, ns, bs):
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

    小中zc成交量 = bt成交量
    小主买 = IF(bt收盘价 > REF(bt收盘价, 1 * bs),
                (bt收盘价 - REF(bt收盘价, 1 * bs)) / (bt最高价 - bt最低价) * 小中zc成交量, 0)
    小主卖 = IF(bt收盘价 < REF(bt收盘价, 1 * bs),
                np.abs(bt收盘价 - REF(bt收盘价, 1 * bs)) / (bt最高价 - bt最低价) * 小中zc成交量,
                0)

    sjbs = ns * bs
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

    小_zhudong_cha = (小主动买入HJ - 小主动卖出HJ)  # 粉小英线大中粉小主动差
    jing_high = bt最高价
    jing_low = bt最低价
    jing_close = bt收盘价
    jing_open = bt开盘价
    jing_vol = bt成交量
    jing_bs = ns * bs
    jing_pjj = (jing_close + jing_high + jing_low + jing_open) / 4
    jing_suducha = jing_pjj - REF(jing_pjj, 1 * bs)
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
    pian_bs = ns * bs

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
    fang_bs = ns * bs

    fang_xiaoqian_up = fang_close > REF(fang_close, 1 * bs)
    fang_xiaoqian_down = fang_close < REF(fang_close, 1 * bs)
    fang_xiaoqian_bfw1_tj1 = IF(REF(fang_xiaoqian_down, 1 * bs) != 1, 1, 0)
    fang_xiaoqian_bfw1_tj2 = IF(fang_xiaoqian_down == 1, 1, 0)
    fang_xiaoqian_bfw1_tj3 = IF(fang_xiaoqian_bfw1_tj1 + fang_xiaoqian_bfw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bfw1 = MY_BARSLAST(fang_xiaoqian_bfw1_tj3 == 1, 1 * bs) + 1

    fang_xiaoqian_bgw1_tj1 = IF(REF(fang_xiaoqian_up, 1 * bs) != 1, 1, 0)
    fang_xiaoqian_bgw1_tj2 = IF(fang_xiaoqian_up == 1, 1, 0)
    fang_xiaoqian_bgw1_tj3 = IF(fang_xiaoqian_bgw1_tj1 + fang_xiaoqian_bgw1_tj2 == 2, 1, 0)
    fang_xiaoqian_bgw1 = MY_BARSLAST(fang_xiaoqian_bgw1_tj3 == 1, 1 * bs) + 1
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

    主动买多动量 = (jing_zhubuy_HJ + fang_zhubuy_HJ + pian_zhubuy_HJ + 小主动买入HJ)/10000
    主动卖空动量 = (jing_zhusel_HJ + fang_zhusel_HJ + pian_zhusel_HJ + 小主动卖出HJ) / 10000

    主动买多指导价 = EMA(主动买多动量, 5)
    主动买多动量_dx9,主动买多动量_gp9=shu9(主动买多指导价)
    # 修改转折点判断逻辑
    主动买多动量趋势 = IF(主动买多指导价 > REF(主动买多指导价, 1), 1, -1)  # 1表示上升，-1表示下降

    # A条件：判断是否从上升变为下降的转折点
    主动买多转折点条件1a = IF(REF(主动买多动量趋势, 1) == 1, 1, 0)  # 由上升转为下降
    主动买多转折点条件1b = IF(主动买多动量趋势 == -1, 1, 0)  # 由上升转为下降
    主动买多转折点条件1 = IF(主动买多转折点条件1a + 主动买多转折点条件1b == 2, 1, 0)

    # 综合判断转折点
    主动买多_sqszzh_sell_jiedian = IF(主动买多转折点条件1 == 1, 1, 0)

    # 买入信号部分 - 新增代码
    买入主动买多动量趋势 = IF(主动买多指导价 < REF(主动买多指导价, 1), 1, -1)  # 1表示下降，-1表示上升

    # A条件：判断是否从下降变为上升的转折点
    主动买多_买入转折点条件1a = IF(REF(买入主动买多动量趋势, 1) == 1, 1, 0)  # 之前在下降
    主动买多_买入转折点条件1b = IF(买入主动买多动量趋势 == -1, 1, 0)  # 现在开始上升
    主动买多_买入转折点条件1 = IF(主动买多_买入转折点条件1a + 主动买多_买入转折点条件1b == 2, 1, 0)

    # 综合判断买入转折点
    主动买多_sqszzh_buy_jiedian = IF(主动买多_买入转折点条件1 == 1, 1, 0)

    主动买多_ema动量 = 主动买多指导价
    # print("zlzdmr_qsx计算主动买多后++++++++++++",df)
    主动卖空指导价 = EMA(主动卖空动量, 5)
    主动卖空动量_dx9, 主动卖空动量_gp9 = shu9(主动卖空指导价)
    # 修改转折点判断逻辑
    主动卖空动量趋势 = IF(主动卖空指导价 > REF(主动卖空指导价, 1), 1, -1)  # 1表示上升，-1表示下降

    # A条件：判断是否从上升变为下降的转折点
    主动卖空转折点条件1a = IF(REF(主动卖空动量趋势, 1) == 1, 1, 0)  # 由上升转为下降
    主动卖空转折点条件1b = IF(主动卖空动量趋势 == -1, 1, 0)  # 由上升转为下降
    主动卖空转折点条件1 = IF(主动卖空转折点条件1a + 主动卖空转折点条件1b == 2, 1, 0)

    # 综合判断转折点
    主动卖空_sqszzh_sell_jiedian = IF(主动卖空转折点条件1 == 1, 1, 0)

    # 买入信号部分 - 新增代码
    买入主动卖空动量趋势 = IF(主动卖空指导价 < REF(主动卖空指导价, 1), 1, -1)  # 1表示下降，-1表示上升

    # A条件：判断是否从下降变为上升的转折点
    主动卖空_买入转折点条件1a = IF(REF(买入主动卖空动量趋势, 1) == 1, 1, 0)  # 之前在下降
    主动卖空_买入转折点条件1b = IF(买入主动卖空动量趋势 == -1, 1, 0)  # 现在开始上升
    主动卖空_买入转折点条件1 = IF(主动卖空_买入转折点条件1a + 主动卖空_买入转折点条件1b == 2, 1, 0)

    # 综合判断买入转折点
    主动卖空_sqszzh_buy_jiedian = IF(主动卖空_买入转折点条件1 == 1, 1, 0)

    主动卖空_ema动量 = 主动卖空指导价
    return df, 主动买多动量, 主动买多_ema动量, 主动买多_sqszzh_sell_jiedian, 主动买多_sqszzh_buy_jiedian,主动卖空动量, 主动卖空_ema动量, 主动卖空_sqszzh_sell_jiedian, 主动卖空_sqszzh_buy_jiedian
def check_data_validity(df, wz1, wz2, price1, price2, function_name):
    """数据有效性检查函数"""
    try:
        # 检查数据长度是否一致
        if not (len(df) == len(wz1) == len(wz2) == len(price1) == len(price2)):
            raise ValueError(f"{function_name}: 输入数据长度不一致")

        # 检查wz1和wz2是否都为0
        if np.all(wz1 == 0) or np.all(wz2 == 0):
            raise ValueError(f"{function_name}: 位置数据无效，全为0")

        # 检查price1和price2是否全为nan
        if np.all(np.isnan(price1)) or np.all(np.isnan(price2)):
            raise ValueError(f"{function_name}: 价格数据无效，全为nan")

        # 检查异常值
        price_threshold = 1e9  # 设置一个合理的价格上限，比如10亿
        if np.any(price1[~np.isnan(price1)] > price_threshold) or np.any(price2[~np.isnan(price2)] > price_threshold):
            raise ValueError(f"{function_name}: 价格数据存在异常值")

        return True
    except Exception as e:
        print(f"数据检查错误: {str(e)}")
        return False
def dongliang_ema66(df,n1=2,n2=1):
    """
        计算趋势线和动量指标的主函数

        Args:
            df: DataFrame, 包含OHLCV数据
            ns: int, 周期参数
            bs: int, 倍数参数

        Returns:
            dict: 包含计算出的各项指标
                - ema动量: EMA动量指标
                - trend_lines_out_line: 趋势线
                - buy_trend_lines_out_line: 买入趋势线
                - sqszzh_sell_jiedian: 卖出节点
                - sqszzh_buy_jiedian: 买入节点
        """
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)

    df['最高价_b'] = df['high'].astype(float)
    df['最低价_b'] = df['low'].astype(float)
    df['收盘价_b'] = df['open'].astype(float)
    df['开盘价_b'] = df['close'].astype(float)
    df['成交量_b'] = df['vol'].astype(float)

    # 在函数开始处添加 numpy 打印设置
    np.set_printoptions(threshold=np.inf)  # 设置打印完整数组
    np.set_printoptions(suppress=True)     # 禁用科学计数法
    df, 主动买多动量, ema动量, sqszzh_sell_jiedian, sqszzh_buy_jiedian = zlzdmr_qsx(df, n1, n2)
    EMA_dongliang_66=EMA(ema动量,88)
    df['trend_line_effective']=EMA_dongliang_66
    df['buy_trend_line_effective']=EMA_dongliang_66
    趋势线上下穿空 = IF(ema动量 < EMA_dongliang_66, 1, 0)
    趋势线上下穿多 = IF(ema动量 > EMA_dongliang_66, 1, 0)
    trend_line_effective=df['trend_line_effective']
    buy_trend_line_effective=df['buy_trend_line_effective']
    return  ema动量,trend_line_effective,buy_trend_line_effective,趋势线上下穿空,趋势线上下穿多

def calculate_trend_indicators(df,n1=2,n2=1):
    """
        计算趋势线和动量指标的主函数

        Args:
            df: DataFrame, 包含OHLCV数据
            ns: int, 周期参数
            bs: int, 倍数参数

        Returns:
            dict: 包含计算出的各项指标
                - ema动量: EMA动量指标
                - trend_lines_out_line: 趋势线
                - buy_trend_lines_out_line: 买入趋势线
                - sqszzh_sell_jiedian: 卖出节点
                - sqszzh_buy_jiedian: 买入节点
        """
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['open'] = df['open'].astype(float)
    df['close'] = df['close'].astype(float)
    df['vol'] = df['vol'].astype(float)

    df['最高价_b'] = df['high'].astype(float)
    df['最低价_b'] = df['low'].astype(float)
    df['收盘价_b'] = df['open'].astype(float)
    df['开盘价_b'] = df['close'].astype(float)
    df['成交量_b'] = df['vol'].astype(float)

    # 在函数开始处添加 numpy 打印设置
    np.set_printoptions(threshold=np.inf)  # 设置打印完整数组
    np.set_printoptions(suppress=True)     # 禁用科学计数法
    df, 主动买多动量, 主动买多_ema动量, 主动买多_sqszzh_sell_jiedian, 主动买多_sqszzh_buy_jiedian,主动卖空动量, 主动卖空_ema动量, 主动卖空_sqszzh_sell_jiedian, 主动卖空_sqszzh_buy_jiedian = zlzdmr_qsx(
        df, n1, n2)
    sqszzh_buy_jiedian_wz1_80, sqszzh_buy_jiedian_wz2_80, sqszzh_buy_jiedian_price1_80, sqszzh_buy_jiedian_price2_80 = buy_out_qsx_gjd(
        主动买多_sqszzh_buy_jiedian, 主动买多_ema动量, 30)
    # print("买入位置1(wz1_80):", sqszzh_buy_jiedian_wz1_80)
    # print("买入位置2(wz2_80):", sqszzh_buy_jiedian_wz2_80)
    # print("买入价格1(price1_80):", sqszzh_buy_jiedian_price1_80)
    # print("买入价格2(price2_80):", sqszzh_buy_jiedian_price2_80)
    sqszzh_sell_jiedian_wz1_80, sqszzh_sell_jiedian_wz2_80, sqszzh_sell_jiedian_price1_80, sqszzh_sell_jiedian_price2_80 = sell_out_qsx_gjd(
        主动买多_sqszzh_sell_jiedian, 主动买多_ema动量, 30)

    sqszzh_buy_jiedian_wz1_40, sqszzh_buy_jiedian_wz2_40, sqszzh_buy_jiedian_price1_40, sqszzh_buy_jiedian_price2_40 = buy_out_qsx_gjd(
        主动买多_sqszzh_buy_jiedian, 主动买多_ema动量, 30)
    # print(sqszzh_buy_jiedian_wz1_40, sqszzh_buy_jiedian_wz2_40)
    sqszzh_sell_jiedian_wz1_40, sqszzh_sell_jiedian_wz2_40, sqszzh_sell_jiedian_price1_40, sqszzh_sell_jiedian_price2_40, = sell_out_qsx_gjd(
        主动买多_sqszzh_sell_jiedian, 主动买多_ema动量, 30)
    # 在主程序中的调用方式修改为：
    trend_lines_80, trend_lines_valid_80, trend_line_effective_80 = qushi(df, sqszzh_sell_jiedian_wz1_80,
                                                                          sqszzh_sell_jiedian_wz2_80,
                                                                          sqszzh_sell_jiedian_price1_80,
                                                                          sqszzh_sell_jiedian_price2_80)

    trend_lines_40, trend_lines_valid_40, trend_line_effective_40 = qushi(df, sqszzh_sell_jiedian_wz1_40,
                                                                          sqszzh_sell_jiedian_wz2_40,
                                                                          sqszzh_sell_jiedian_price1_40,
                                                                          sqszzh_sell_jiedian_price2_40)

    buy_trend_lines_80, buy_trend_lines_valid_80, buy_trend_line_effective_80 = qushi_buy(df, sqszzh_buy_jiedian_wz1_80,
                                                                                          sqszzh_buy_jiedian_wz2_80,
                                                                                          sqszzh_buy_jiedian_price1_80,
                                                                                          sqszzh_buy_jiedian_price2_80)

    buy_trend_lines_40, buy_trend_lines_valid_40, buy_trend_line_effective_40 = qushi_buy(df, sqszzh_buy_jiedian_wz1_40,
                                                                                          sqszzh_buy_jiedian_wz2_40,
                                                                                          sqszzh_buy_jiedian_price1_40,
                                                                                          sqszzh_buy_jiedian_price2_40)

    # 计算平均趋势线
    df['trend_line_effective'] = (np.array(trend_line_effective_80) + np.array(trend_line_effective_40)) / 2
    df['buy_trend_line_effective'] = (np.array(buy_trend_line_effective_80) + np.array(buy_trend_line_effective_40)) / 2
    # df['trend_line_effective'] = (np.array(trend_line_effective_80) + np.array(trend_line_effective_80)) / 2
    # df['buy_trend_line_effective'] = (np.array(buy_trend_line_effective_80) + np.array(buy_trend_line_effective_80)) / 2
    # 在延伸趋势线之前添加调试信息
    print("卖出趋势线有效点数量：", np.sum(~np.isnan(df['trend_line_effective'])))
    print("买入趋势线有效点数量：", np.sum(~np.isnan(df['buy_trend_line_effective'])))

    # 延伸两条趋势线
    # 在延伸趋势线之前添加调试信息
    # print("\n卖出趋势线信息：")
    df['trend_line_effective'] = extend_trend_line(df['trend_line_effective'].values, 7, df.index)

    # print("\n买入趋势线信息：")
    df['buy_trend_line_effective'] = extend_trend_line(df['buy_trend_line_effective'].values, 7, df.index)

    # 延伸后再次检查
    # print("延伸后卖出趋势线有效点数量：", np.sum(~np.isnan(df['trend_line_effective'])))
    # print("延伸后买入趋势线有效点数量：", np.sum(~np.isnan(df['buy_trend_line_effective'])))

    # 在延伸趋势线之后，添加MA平滑处理
    # 修改平滑处理函数
    def smooth_trend_line(data, ma_period=4):
        # 计算MA
        ma_data = MA(data, ma_period)
        # 将原始数据和MA数据结合
        # 如果MA数据有效（不是nan），则使用MA数据；否则使用原始数据
        result = np.where(np.isnan(ma_data), data, ma_data)
        return result

    # 应用平滑处理
    df['trend_line_effective'] = smooth_trend_line(df['trend_line_effective'])
    df['buy_trend_line_effective'] = smooth_trend_line(df['buy_trend_line_effective'])
    下穿上涨趋势线 = IF(bt_crossunder(主动买多_ema动量, df['buy_trend_line_effective']), 1, 0)
    下穿下跌趋势线 = IF(bt_crossunder(主动买多_ema动量, df['trend_line_effective']), 1, 0)
    下穿趋势线=IF(下穿上涨趋势线+下穿下跌趋势线>=1,1,0)
    # 下穿趋势线 = 下穿上涨趋势线
    上穿下跌趋势线 = IF(bt_crossover(主动买多_ema动量, df['trend_line_effective']), 1, 0)
    上穿上涨趋势线 = IF(bt_crossover(主动买多_ema动量, df['buy_trend_line_effective']), 1, 0)
    上穿趋势线 = IF(上穿下跌趋势线 + 上穿上涨趋势线 >= 1, 1, 0)
    # 上穿趋势线 = 上穿下跌趋势线
    下穿上涨趋势线wz = MY_BARSLAST(下穿趋势线, 1)
    上穿下跌趋势线wz = MY_BARSLAST(上穿趋势线, 1)

    # 趋势线上下穿空的条件：
    # 修改多空判断逻辑
    trend_line_valid = ~np.isnan(df['trend_line_effective'])
    buy_trend_line_valid = ~np.isnan(df['buy_trend_line_effective'])

    # 1. 原有的位置判断条件
    空_位置条件 = IF(下穿上涨趋势线wz < 上穿下跌趋势线wz, 1, 0)
    # 2. 有效趋势线的位置判断条件
    空_趋势线条件 = IF((trend_line_valid & (主动买多_ema动量 < df['trend_line_effective'])) |
                       (buy_trend_line_valid & (主动买多_ema动量 < df['buy_trend_line_effective'])), 1, 0)
    # 趋势线上下穿空 = IF(空_位置条件 | 空_趋势线条件 , 1, 0)
    趋势线上下穿空 = IF(空_位置条件  , 1, 0)
    # 趋势线上下穿多的条件：
    # 1. 原有的位置判断条件
    多_位置条件 = IF(下穿上涨趋势线wz > 上穿下跌趋势线wz, 1, 0)
    # 2. 有效趋势线的位置判断条件
    多_趋势线条件 = IF((trend_line_valid & (主动买多_ema动量 > df['trend_line_effective'])) |
                       (buy_trend_line_valid & (主动买多_ema动量 > df['buy_trend_line_effective'])), 1, 0)
    # 趋势线上下穿多 = IF(多_位置条件 | 多_趋势线条件 , 1, 0)
    趋势线上下穿多 = IF(多_位置条件 , 1, 0)

    trend_line_effective=df['trend_line_effective']
    buy_trend_line_effective=df['buy_trend_line_effective']
    return  主动买多_ema动量,trend_line_effective,buy_trend_line_effective,趋势线上下穿空,趋势线上下穿多