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


class RNNModel(nn.Module):
    def __init__(self, input_size, hidden_size, num_layers, output_size, bidirectional, dropout):
        super(RNNModel, self).__init__()
        self.num_directions = 2 if bidirectional else 1
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.rnn = nn.LSTM(input_size=input_size, hidden_size=hidden_size, num_layers=num_layers,
                           batch_first=True, bidirectional=bidirectional, dropout=dropout)
        self.fc1 = nn.Linear(hidden_size * self.num_directions, 64)
        self.dropout = nn.Dropout(p=0.05)
        self.fc2 = nn.Linear(64, output_size)
        # 添加正则化项
        self.relu = nn.ReLU()
        self.regularization = nn.L1Loss()  # 添加正则化项
        init.xavier_uniform_(self.fc1.weight)  # Add xavier uniform initialization
        init.xavier_uniform_(self.fc2.weight)

    def forward(self, x):
        sequence_length = x.shape[1]
        input_size = x.shape[2]
        h0 = torch.zeros(self.num_layers * self.num_directions, x.size(0), self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers * self.num_directions, x.size(0), self.hidden_size).to(x.device)
        inputs = x
        out, (hn, cn) = self.rnn(inputs, (h0[:, :x.size(0), :], c0[:, :x.size(0), :]))
        out = self.dropout(out)
        out = nn.functional.relu(self.fc1(out[:, -1, :]))
        out = self.fc2(out)
        return out

    def regularization(self, target):
        return torch.norm(target, p=1)  # 计算权重的L1正则化项


def ylzcqs(df):
    指导价 = EMA(df['close'], 4)
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

    上限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) + 0.0 * xATR1
    下限 = MYREF(df['close'], MY_BARSLAST(小角度cqrxz == 1, 1)) - 0.0 * xATR1

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
    junxa = (junx2 + HHV(df['high'], 60)) / 2
    junxb = (junx2 + LLV(df['low'], 60)) / 2

    junx2上穿_tj1 = IF(指导价 > junx2, 1, 0)
    junx2上穿_tj2 = IF(REF(指导价, 1) <= REF(junx2, 1), 1, 0)
    junx2上穿 = IF(junx2上穿_tj1 + junx2上穿_tj2 == 2, 1, 0)

    junx2b上穿_tj1 = IF(指导价 > junx2b, 1, 0)
    junx2b上穿_tj2 = IF(REF(指导价, 1) <= REF(junx2b, 1), 1, 0)
    junx2b上穿 = IF(junx2b上穿_tj1 + junx2b上穿_tj2 == 2, 1, 0)

    junxa上穿_tj1 = IF(指导价 > junxa, 1, 0)
    junxa上穿_tj2 = IF(REF(指导价, 1) <= REF(junxa, 1), 1, 0)
    junxa上穿 = IF(junxa上穿_tj1 + junxa上穿_tj2 == 2, 1, 0)

    junxb上穿_tj1 = IF(指导价 > junxb, 1, 0)
    junxb上穿_tj2 = IF(REF(指导价, 1) <= REF(junxb, 1), 1, 0)
    junxb上穿 = IF(junxb上穿_tj1 + junxb上穿_tj2 == 2, 1, 0)

    上穿汇总 = IF(junx2上穿 + junx2b上穿 + junxa上穿 + junxb上穿 >= 1, 1, 0)
    junx2上穿wz = BARSLAST(junx2上穿)
    junx2b上穿wz = BARSLAST(junx2b上穿)
    junxa上穿wz = BARSLAST(junxa上穿)
    junxb上穿wz = BARSLAST(junxb上穿)
    上穿汇总wz = BARSLAST(上穿汇总)

    junx2下穿_tj1 = IF(指导价 < junx2, 1, 0)
    junx2下穿_tj2 = IF(REF(指导价, 1) >= REF(junx2, 1), 1, 0)
    junx2下穿 = IF(junx2下穿_tj1 + junx2下穿_tj2 == 2, 1, 0)

    junx2b下穿_tj1 = IF(指导价 < junx2b, 1, 0)
    junx2b下穿_tj2 = IF(REF(指导价, 1) >= REF(junx2b, 1), 1, 0)
    junx2b下穿 = IF(junx2b下穿_tj1 + junx2b下穿_tj2 == 2, 1, 0)

    junxa下穿_tj1 = IF(指导价 < junxa, 1, 0)
    junxa下穿_tj2 = IF(REF(指导价, 1) >= REF(junxa, 1), 1, 0)
    junxa下穿 = IF(junxa下穿_tj1 + junxa下穿_tj2 == 2, 1, 0)

    junxb下穿_tj1 = IF(指导价 < junxb, 1, 0)
    junxb下穿_tj2 = IF(REF(指导价, 1) >= REF(junxb, 1), 1, 0)
    junxb下穿 = IF(junxb下穿_tj1 + junxb下穿_tj2 == 2, 1, 0)
    下穿汇总 = IF(junx2下穿 + junx2b下穿 + junxa下穿 + junxb下穿 >= 1, 1, 0)

    junx2下穿wz = BARSLAST(junx2下穿)
    junx2b下穿wz = BARSLAST(junx2b下穿)
    junxa下穿wz = BARSLAST(junxa下穿)
    junxb下穿wz = BARSLAST(junxb下穿)
    下穿汇总wz = BARSLAST(下穿汇总)

    上下穿多 = IF(上穿汇总wz < 下穿汇总wz, 1, 0)
    上下穿空 = IF(下穿汇总wz < 上穿汇总wz, 1, 0)

    横盘最大线 = NthMaxList(1, junx2b, junx2, junxa, junxb)
    横盘最小线 = NthMinList(1, junx2b, junx2, junxa, junxb)
    震荡_tj1 = IF(指导价 <= 横盘最大线, 1, 0)
    震荡_tj2 = IF(指导价 >= 横盘最小线, 1, 0)
    震荡 = IF(震荡_tj1 + 震荡_tj2 == 2, 1, 0)
    震荡扩大 = EXIST(震荡, 7)

    趋势于最大线比值 = ABS(1 - 指导价 / 横盘最大线) * 100
    趋势于最小线比值 = ABS(1 - 指导价 / 横盘最小线) * 100
    趋势多_tj1 = IF(震荡 != 1, 1, 0)
    趋势多_tj2 = IF(上下穿多 == 1, 1, 0)
    趋势多 = IF(趋势多_tj1 + 趋势多_tj2 == 2, 1, 0)
    趋势空_tj1 = IF(震荡 != 1, 1, 0)
    趋势空_tj2 = IF(上下穿空 == 1, 1, 0)
    趋势空 = IF(趋势空_tj1 + 趋势空_tj2 == 2, 1, 0)
    趋势多持续时间_tja = IF(REF(上下穿多, 1) != 1, 1, 0)
    趋势多持续时间_tjb = IF(上下穿多 + 趋势多持续时间_tja == 2, 1, 0)
    趋势多持续时间 = IF(上下穿多 == 1, MY_BARSLAST(趋势多持续时间_tjb == 1, 1), 0)
    趋势空持续时间_tja = IF(REF(上下穿空, 1) != 1, 1, 0)
    趋势空持续时间_tjb = IF(上下穿空 + 趋势空持续时间_tja == 2, 1, 0)
    趋势空持续时间 = IF(上下穿空 == 1, MY_BARSLAST(趋势空持续时间_tjb == 1, 1), 0)

    junxa_pj, barpos = calculate_avg_and_positions(junxa)
    junxa_b24 = junxa - REF(junxa, 24)
    junxa_b24[junxa_b24 == 0] = 1e-8  # 判断并将分母为零的值赋为1e-8
    junxa_a24 = 24 * junxa_pj
    junxa_jiaodu_c24 = 90 - (np.arctan(junxa_a24 / junxa_b24) * 57.29578)
    junxa_jiaodu_cqr24 = IF(junxa_jiaodu_c24 > 90, (180 - junxa_jiaodu_c24) * -1, junxa_jiaodu_c24)

    junxa_b12 = junxa - REF(junxa, 12)
    junxa_b12[junxa_b12 == 0] = 1e-8  # 判断并将分母为零的值赋为1e-8
    junxa_a12 = 12 * junxa_pj
    junxa_jiaodu_c12 = 90 - (np.arctan(junxa_a12 / junxa_b12) * 57.29578)
    junxa_jiaodu_cqr12 = IF(junxa_jiaodu_c12 > 90, (180 - junxa_jiaodu_c12) * -1, junxa_jiaodu_c12)

    return junx2, junx2b, junxa, junxb, 指导价, 上下穿多, 上下穿空, 震荡扩大, 趋势多, 趋势空, 趋势多持续时间, 趋势空持续时间, junxa_jiaodu_cqr24, junxa_jiaodu_cqr12


def caiji_yuce_jiaoyizhibiao(sqldb_path_file, table_name, limit_num, code, ma_short=20, ma_long=60):
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

    # 动态均线参数
    二十下穿六十 = bt_crossunder(MA(df['close'], ma_short), MA(df['close'], ma_long))
    二十上穿六十 = bt_crossover(MA(df['close'], ma_short), MA(df['close'], ma_long))
    上下穿多 = MA(df['close'], ma_short) > MA(df['close'], ma_long)
    上下穿空 = MA(df['close'], ma_short) < MA(df['close'], ma_long)
    ma20 = MA(df['close'], ma_short)
    ma60 = MA(df['close'], ma_long)
    ma5=MA(df['close'],5)
    # 将计算结果添加到df中
    df['上下穿多'] = 上下穿多
    df['上下穿空'] = 上下穿空
    df['ma20']=ma20
    df['ma60']=ma60
    df['卖60'] = 二十下穿六十
    df['买60'] = 二十上穿六十
    df['ma5']=ma5
    print(df)
    print(df.columns)

    return df


def run_backtest(code: str,
                 table_name: str,
                 limit_num: int,
                 initial_cash: float,
                 ma_short: int,
                 ma_long: int,
                 db_mode: str = 'legacy',
                 db_folder: str = None,
                 stake_qty: int = 10000,
                 trade_mode: str = 'both'):
    # 构建数据库路径（使用智能路径检测）
    if db_mode == 'crypto':
        # 导入路径修复模块
        try:
            from path_fix import get_database_path
            db_path, table_name = get_database_path(code, 'crypto')
        except ImportError:
            # 如果路径修复模块不存在，使用原有逻辑
            if code == 'BTC':
                db_path = 'btc_data.db'
                table_name = 'btc_daily'
            elif code == 'ETH':
                db_path = 'eth_data.db'
                table_name = 'eth_daily'
            else:
                raise ValueError(f'不支持的加密货币代码: {code}')
        
        df = load_df_generic(db_path, table_name, limit_num, code)
        # 叠加策略所需均线和信号
        ma20 = MA(df['close'], ma_short)
        ma60 = MA(df['close'], ma_long)
        ma5 = MA(df['close'], 5)
        二十下穿六十 = bt_crossunder(ma20, ma60)
        二十上穿六十 = bt_crossover(ma20, ma60)
        上下穿多 = ma20 > ma60
        上下穿空 = ma20 < ma60
        df['上下穿多'] = 上下穿多
        df['上下穿空'] = 上下穿空
        df['卖60'] = 二十下穿六十
        df['买60'] = 二十上穿六十
        df['ma20'] = ma20
        df['ma60'] = ma60
        df['ma5'] = ma5
    elif db_mode == 'baostock':
        # 使用智能路径检测
        try:
            from path_fix import get_database_path
            db_path, table_name = get_database_path(code, 'baostock')
        except ImportError:
            # 如果路径修复模块不存在，使用原有逻辑
            base_folder = db_folder or os.path.join(os.getcwd(), 'gupiao_baostock')
            db_path = os.path.join(base_folder, f'{code}_data.db')
            table_name = code  # 确保table_name被定义
        df = load_df_generic(db_path, table_name, limit_num, code)
        # 叠加策略所需均线和信号
        ma20 = MA(df['close'], ma_short)
        ma60 = MA(df['close'], ma_long)
        ma5 = MA(df['close'], 5)
        二十下穿六十 = bt_crossunder(ma20, ma60)
        二十上穿六十 = bt_crossover(ma20, ma60)
        上下穿多 = ma20 > ma60
        上下穿空 = ma20 < ma60
        df['上下穿多'] = 上下穿多
        df['上下穿空'] = 上下穿空
        df['卖60'] = 二十下穿六十
        df['买60'] = 二十上穿六十
        df['ma20'] = ma20
        df['ma60'] = ma60
        df['ma5'] = ma5
    else:
        # 使用智能路径检测
        try:
            from path_fix import get_database_path
            db_path, table_name = get_database_path(code, 'legacy')
        except ImportError:
            # 如果路径修复模块不存在，使用原有逻辑
            db_zhumulu_folder = db_folder or r'D:\\gupiao_sql'
            model_folder_mc = code + '_data.db'
            db_path = os.path.join(db_zhumulu_folder, model_folder_mc)
        df = caiji_yuce_jiaoyizhibiao(db_path, table_name, limit_num, code, ma_short=ma_short, ma_long=ma_long)

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

        table_name = "min_data15"
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
        cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='both')

        # 只做空模式
        # cerebro.addstrategy(SimpleStrategy, df=df, trade_mode='short_only')

        # 双向交易模式
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
        self.initial_cash = 10000000.0
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
            # 空仓状态
            if self.direction == 0:
                if self.p.trade_mode in ['long_only', 'both'] and 做多_price == 1:
                    self.buy()
                    self.direction = 1
                    print(f'{self.current_datetime} - 开多仓')
                elif self.p.trade_mode in ['short_only', 'both'] and 做空_price == 1:
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
        print(f'策略结束 - 初始资金: {self.initial_cash_at_start:.2f}, 期末资产: {end_value:.2f}, 绝对盈亏: {pnl_abs:.2f}, ROI: {roi:.6%}')

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
    # 初始化配置
    init_config()
    print('初始化配置完成')
    # 设置日志
    logging.basicConfig(
        filename='trading_log.txt',
        level=logging.INFO,
        format='%(asctime)s - %(message)s'
    )

    # 读取配置
    config = configparser.ConfigParser()
    config.read('xlsys.ini')

    # 从配置文件获取参数
    code = config['xl_main_folder']['code']
    table_name = config['xl_main_folder']['table_name']
    limit_num = int(config['xl_main_folder']['limit_num'])
    db_path = config['xl_main_folder']['db_path']

    # 首次运行
    update_chart()
