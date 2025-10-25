import numpy as np
import pandas as pd
import mplfinance as mpf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def supertrend_tv(df: pd.DataFrame, length: int = 10, multiplier: float = 3.0, time_unit: str = 's') -> pd.DataFrame:
    """
    适配标准表结构的超级趋势计算，输出三列：
    - cjqs_d: 多头标记(1/0)
    - cjqs_k: 空头标记(1/0)
    - cjqs_xz: 当前显示的超级趋势线（多=最终下轨，空=最终上轨）

    支持两种输入格式：
    1. 标准格式：列包含['time', 'high', 'low', 'open', 'close', 'vol', 'code']，索引为DatetimeIndex
    2. 原始格式：列包含['time', 'high', 'low', 'open', 'close', 'vol', 'code']，time列为时间戳或字符串

    参数与TradingView一致：length=ATR长度, multiplier=ATR倍数。
    """
    # 复制避免修改原数据
    df = df.copy()

    # 确保必要价格列与代码列存在
    required_price_cols = ['high', 'low', 'open', 'close']
    missing_price = [c for c in required_price_cols if c not in df.columns]
    if missing_price:
        raise ValueError(f"缺少必要价格列: {missing_price}")
    if 'vol' not in df.columns and 'volume' in df.columns:
        df.rename(columns={'volume': 'vol'}, inplace=True)
    if 'vol' not in df.columns:
        raise ValueError("缺少成交量列 'vol'")
    if 'code' not in df.columns:
        df['code'] = 'DEFAULT'

    # 生成排序键，避免与索引名冲突
    # 统一使用临时列 '_ts' 排序，用完即删
    if isinstance(df.index, pd.DatetimeIndex):
        df['_ts'] = (df.index.view('int64') // 10**9).astype('int64')
    else:
        if 'time' in df.columns:
            time_series = df['time']
            if pd.api.types.is_integer_dtype(time_series) or pd.api.types.is_float_dtype(time_series):
                df['_ts'] = pd.to_numeric(time_series, errors='coerce').astype('float').astype('Int64')
            else:
                dt = pd.to_datetime(time_series, errors='coerce')
                df['_ts'] = (dt.view('int64') // 10**9).astype('float').astype('Int64')
        else:
            raise ValueError("缺少 'time' 列，且索引也不是 DatetimeIndex，无法生成时间排序键")

    # 数值化价格与成交量
    for col in ['open', 'high', 'low', 'close', 'vol']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # 分组按(code,_ts)升序
    df.sort_values(['code', '_ts'], inplace=True)

    # 预置输出列
    df['cjqs_d'] = 0
    df['cjqs_k'] = 0
    df['cjqs_xz'] = np.nan

    def _compute_group(g: pd.DataFrame) -> pd.DataFrame:
        high = g['high'].values
        low = g['low'].values
        close = g['close'].values

        # True Range
        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]
        tr = np.maximum.reduce([
            high - low,
            np.abs(high - prev_close),
            np.abs(prev_close - low)
        ])

        # Wilder RMA for ATR (等价于EMA alpha=1/length)
        atr = pd.Series(tr).ewm(alpha=1/length, adjust=False, min_periods=length).mean().values

        hl2 = (high + low) / 2.0
        upper = hl2 + multiplier * atr
        lower = hl2 - multiplier * atr

        # 趋势方向 True=多, False=空
        trend = np.ones(len(g), dtype=bool)

        # 可变副本用于单向性调整
        final_upper = upper.copy()
        final_lower = lower.copy()

        for i in range(1, len(g)):
            prev = i - 1
            if close[i] > final_upper[prev]:
                trend[i] = True
            elif close[i] < final_lower[prev]:
                trend[i] = False
            else:
                trend[i] = trend[prev]
                if trend[i] and final_lower[i] < final_lower[prev]:
                    final_lower[i] = final_lower[prev]
                if (not trend[i]) and final_upper[i] > final_upper[prev]:
                    final_upper[i] = final_upper[prev]

        # 生成输出：多=1/空=1，线=多用final_lower，空用final_upper
        cjqs_d = np.where(trend, 1, 0)
        cjqs_k = np.where(~trend, 1, 0)
        xz = np.where(trend, final_lower, final_upper)

        # 初始化阶段（ATR为NaN）的处理：置为0/NaN
        invalid = np.isnan(atr)
        cjqs_d[invalid] = 0
        cjqs_k[invalid] = 0
        xz[invalid] = np.nan

        g = g.copy()
        g['cjqs_d'] = cjqs_d
        g['cjqs_k'] = cjqs_k
        g['cjqs_xz'] = xz
        return g

    df = df.groupby('code', group_keys=False, sort=False).apply(_compute_group)

    # 清理临时列
    if '_ts' in df.columns:
        df.drop(columns=['_ts'], inplace=True)
    return df


def supertrend_single(df: pd.DataFrame, length: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    单周期超级趋势：在输入df上新增三列并返回同一个DataFrame。
    新增列：cjqs_d, cjqs_k, cjqs_xz
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise ValueError('supertrend_single 需要 df 索引为 DatetimeIndex')
    if 'code' not in df.columns:
        df = df.copy()
        df['code'] = 'DEFAULT'
    st = supertrend_tv(df, length=length, multiplier=multiplier)
    out = df.copy()
    out['cjqs_d'] = st['cjqs_d']
    out['cjqs_k'] = st['cjqs_k']
    out['cjqs_xz'] = st['cjqs_xz']
    return out


def supertrend_dual(df_low: pd.DataFrame,
                    df_high: pd.DataFrame,
                    low_length: int = 10,
                    low_multiplier: float = 3.0,
                    high_length: int = None,
                    high_multiplier: float = None,
                    align_method: str = 'ffill',
                    suffix: str = 'min60') -> pd.DataFrame:
    """
    双周期共振超级趋势：
    - 在低周期df_low基础上，计算低周期ST与高周期ST，并将高周期对齐到低周期索引。
    - 新增列：cjqs_d_{suffix}, cjqs_k_{suffix}, cjqs_xz_{suffix}
    返回：包含新增列的 df_low 副本。
    """
    if not isinstance(df_low.index, pd.DatetimeIndex):
        raise ValueError('df_low 需要 DatetimeIndex')
    if not isinstance(df_high.index, pd.DatetimeIndex):
        raise ValueError('df_high 需要 DatetimeIndex')
    if 'code' not in df_low.columns:
        df_low = df_low.copy()
        df_low['code'] = 'DEFAULT'
    if 'code' not in df_high.columns:
        df_high = df_high.copy()
        df_high['code'] = df_low['code'].iloc[0]

    # 低周期（可按需保留已有列，不强制覆盖）
    st_low = supertrend_tv(df_low, length=low_length, multiplier=low_multiplier)
    # 高周期
    st_high = supertrend_tv(df_high,
                            length=high_length or low_length,
                            multiplier=high_multiplier or low_multiplier)
    # 对齐
    st_high_aligned = st_high.reindex(df_low.index, method=align_method)

    out = df_low.copy()
    out[f'cjqs_d_{suffix}'] = st_high_aligned['cjqs_d'].fillna(0).astype(int)
    out[f'cjqs_k_{suffix}'] = st_high_aligned['cjqs_k'].fillna(0).astype(int)
    out[f'cjqs_xz_{suffix}'] = st_high_aligned['cjqs_xz']
    return out

def super_trend(df, atr_period=34, multiplier=3.0):
    """
    计算超级趋势指标
    
    参数:
    df: DataFrame，包含'high', 'low', 'close'列
    atr_period: ATR周期，默认34
    multiplier: ATR倍数，默认3.0
    
    返回:
    DataFrame，包含'Supertrend', 'Final Lowerband', 'Final Upperband'列
    """
    high = df['high']
    low = df['low']
    close = df['close']
    
    # 首先计算ATR
    price_diffs = [high - low, high - close.shift(), close.shift() - low]
    true_range = pd.concat(price_diffs, axis=1)
    true_range = true_range.abs().max(axis=1)
    atr = true_range.ewm(alpha=1 / atr_period, min_periods=atr_period).mean()
    
    # 计算超级趋势指标
    hl2 = (high + low) / 2
    final_upperband = hl2 + (multiplier * atr)
    final_lowerband = hl2 - (multiplier * atr)

    st = [True] * len(df)  # True代表上行趋势，False代表下行趋势
    
    for i in range(1, len(df.index)):
        curr, prev = i, i - 1

        # 如果当前收盘价上传上轨
        if close[curr] > final_upperband[prev]:
            st[curr] = True
        # 当前收盘价下穿下轨
        elif close[curr] < final_lowerband[prev]:
            st[curr] = False
        # 否则趋势延续
        else:
            st[curr] = st[prev]
            if st[curr] and final_lowerband[curr] < final_lowerband[prev]:
                final_lowerband[curr] = final_lowerband[prev]
            if not st[curr] and final_upperband[curr] > final_upperband[prev]:
                final_upperband[curr] = final_upperband[prev]

        # 根据趋势方向分别移除相应的上下轨
        if st[curr]:
            final_upperband[curr] = np.nan
        else:
            final_lowerband[curr] = np.nan
    
    return pd.DataFrame({
        'Supertrend': st,
        'Final Lowerband': final_lowerband,
        'Final Upperband': final_upperband
    }, index=df.index)


def generate_sample_data():
    """
    生成模拟的OHLCV数据用于测试
    """
    np.random.seed(42)
    dates = pd.date_range(start='2021-01-01', end='2022-05-20', freq='D')
    n_days = len(dates)
    
    # 生成模拟价格数据
    base_price = 30000
    price_changes = np.random.normal(0, 0.02, n_days)
    prices = [base_price]
    
    for change in price_changes[1:]:
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    # 生成OHLC数据
    data = []
    for i, price in enumerate(prices):
        daily_volatility = abs(np.random.normal(0, 0.01))
        high = price * (1 + daily_volatility)
        low = price * (1 - daily_volatility)
        open_price = prices[i-1] if i > 0 else price
        close = price
        volume = np.random.randint(1000000, 5000000)
        
        data.append({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data, index=dates)
    return df


def main():
    """
    主函数 - 演示超级趋势指标
    """
    print("正在生成模拟数据...")
    data = generate_sample_data()
    
    print(f"数据形状: {data.shape}")
    print("数据预览:")
    print(data.head())
    
    # 设置参数
    atr_period = 10
    atr_multiplier = 3.0
    
    print(f"\n正在计算超级趋势指标 (ATR周期: {atr_period}, 倍数: {atr_multiplier})...")
    
    # 计算超级趋势指标
    supertrend = super_trend(data, atr_period, atr_multiplier)
    data_with_supertrend = data.join(supertrend)
    
    print("超级趋势指标计算结果:")
    print(data_with_supertrend.tail())
    
    # 准备绘图数据
    addplots = []
    
    # 根据趋势方向创建正确的超级趋势线
    # 上升趋势时显示下轨（红线），下降趋势时显示上轨（绿线）
    supertrend_line = []
    for i in range(len(data_with_supertrend)):
        if data_with_supertrend['Supertrend'].iloc[i]:  # 上升趋势
            supertrend_line.append(data_with_supertrend['Final Lowerband'].iloc[i])
        else:  # 下降趋势
            supertrend_line.append(data_with_supertrend['Final Upperband'].iloc[i])
    
    # 创建超级趋势线Series
    supertrend_series = pd.Series(supertrend_line, index=data_with_supertrend.index)
    
    # 根据趋势方向设置颜色
    trend_colors = []
    for i in range(len(data_with_supertrend)):
        if data_with_supertrend['Supertrend'].iloc[i]:  # 上升趋势 - 红色
            trend_colors.append('red')
        else:  # 下降趋势 - 绿色
            trend_colors.append('green')
    
    # 分别绘制上升和下降趋势的线段
    # 上升趋势段（红色）
    uptrend_mask = data_with_supertrend['Supertrend'] == True
    if uptrend_mask.any():
        uptrend_data = supertrend_series.where(uptrend_mask)
        addplots.append(mpf.make_addplot(uptrend_data, color='red', width=2))
    
    # 下降趋势段（绿色）
    downtrend_mask = data_with_supertrend['Supertrend'] == False
    if downtrend_mask.any():
        downtrend_data = supertrend_series.where(downtrend_mask)
        addplots.append(mpf.make_addplot(downtrend_data, color='green', width=2))
    
    # 绘制K线图
    print("\n正在绘制图形...")
    mpf.plot(data_with_supertrend, 
             type='candle', 
             style='charles',
             addplot=addplots,
             tight_layout=True,
             figsize=(12, 8),
             title=f'超级趋势指标演示 (ATR周期: {atr_period}, 倍数: {atr_multiplier})')
    
    print("\n超级趋势指标计算完成！")
    print("绿色线表示上轨，红色线表示下轨")
    print("当价格在上轨上方时，趋势为上升；当价格在下轨下方时，趋势为下降")

    # 演示：使用适配表结构的函数，构造与您表一致的列名
    demo_df = data.reset_index().rename(columns={'index':'datetime'})
    demo_df['time'] = demo_df['datetime'].astype('int64') // 10**9
    demo_df['vol'] = demo_df['volume']
    demo_df['code'] = 'DEMO'
    demo_df = demo_df[['time','high','low','open','close','vol','code']]

    print("\n演示计算三列输出(cjqs_d/cjqs_k/cjqs_xz)...")
    demo_out = supertrend_tv(demo_df, length=10, multiplier=3.0, time_unit='s')
    print(demo_out[['time','code','cjqs_d','cjqs_k','cjqs_xz']].tail())


if __name__ == "__main__":
    main()
