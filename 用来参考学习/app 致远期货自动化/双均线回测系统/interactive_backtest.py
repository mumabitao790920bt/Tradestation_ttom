import os
import threading
import queue
import backtrader as bt
from typing import Optional
import pandas as pd

from data_processing import MA, bt_crossover, bt_crossunder, IF, REF
from 回测示例 import load_df_generic, BacktestConfig, SQLiteData, PortfolioObserver
from huatu_mz import huatucs


class InteractiveController:
    def __init__(self):
        self._decisions = queue.Queue()
        self._reply_event = None
        self._reply_value = None
        self.df_ref: Optional[pd.DataFrame] = None

    # called by strategy
    def request_decision(self, decision: dict) -> str:
        self._reply_event = threading.Event()
        self._reply_value = None
        self._decisions.put(decision)
        self._reply_event.wait()  # wait until GUI replies
        choice = self._reply_value or 'follow'
        self._reply_event = None
        self._reply_value = None
        return choice

    # called by GUI
    def get_next_decision_nowait(self) -> Optional[dict]:
        try:
            return self._decisions.get_nowait()
        except queue.Empty:
            return None

    def submit_choice(self, choice: str):
        if self._reply_event is not None:
            self._reply_value = choice
            self._reply_event.set()

    def set_df(self, df: pd.DataFrame):
        self.df_ref = df


class InteractiveStrategy(bt.Strategy):
    params = (
        ('df', None),
        ('trade_mode', 'both'),
        ('controller', None),
        ('stake_qty', 10000),
    )

    def __init__(self):
        self.df = self.p.df
        self.direction = 0
        self.asset_list = []
        self.direction_list = []
        self.controller: InteractiveController = self.p.controller
        self.initial_cash_at_start = float(self.broker.getvalue())

        # stats (same口径 as SimpleStrategy)
        self.wins = 0
        self.total_trades = 0
        self.losses_total = 0.0
        self.win_total = 0.0
        self.win_lirun = 0.0
        self.wins_lv = 0.0
        self.win_losses_bi = 0.0
        self.csv_filename = "portfolio_单.csv"

        # ensure columns
        for col in ['做多', '做空']:
            if col not in self.df.columns:
                raise ValueError(f"DataFrame必须包含{col}列")
            self.df[col] = self.df[col].astype(float)

    def _pause_for_decision(self, action: str, current_datetime: pd.Timestamp):
        decision = {
            'datetime': current_datetime,
            'action': action,
            'direction': self.direction,
            'price': float(self.data.close[0]) if len(self.data) else None,
            'equity': float(self.broker.getvalue()),
        }
        return self.controller.request_decision(decision)

    def next(self):
        # record
        current_datetime = pd.Timestamp(self.datetime.datetime())
        # expose to observers (e.g., PortfolioObserver expects _owner.current_datetime)
        self.current_datetime = current_datetime
        self.asset_list.append(self.broker.getvalue())

        # fetch signals
        try:
            long_sig = float(self.df.loc[current_datetime, '做多'])
            short_sig = float(self.df.loc[current_datetime, '做空'])
        except Exception:
            self.direction_list.append(self.direction)
            return

        # decision flow
        if self.direction == 0:
            if self.p.trade_mode in ['long_only', 'both'] and long_sig == 1:
                choice = self._pause_for_decision('open_long', current_datetime)
                if choice == 'follow':
                    self.buy()
                    self.direction = 1
            elif self.p.trade_mode in ['short_only', 'both'] and short_sig == 1:
                choice = self._pause_for_decision('open_short', current_datetime)
                if choice == 'follow':
                    self.sell()
                    self.direction = -1

        elif self.direction == 1:
            if short_sig == 1:
                # treat as close long (and maybe open short)
                action = 'close_long_then_open_short' if self.p.trade_mode == 'both' else 'close_long'
                choice = self._pause_for_decision(action, current_datetime)
                if choice == 'follow':
                    self.close()
                    if self.p.trade_mode == 'both':
                        self.sell()
                        self.direction = -1
                    else:
                        self.direction = 0

        elif self.direction == -1:
            if long_sig == 1:
                action = 'close_short_then_open_long' if self.p.trade_mode == 'both' else 'close_short'
                choice = self._pause_for_decision(action, current_datetime)
                if choice == 'follow':
                    self.close()
                    if self.p.trade_mode == 'both':
                        self.buy()
                        self.direction = 1
                    else:
                        self.direction = 0

        self.direction_list.append(self.direction)

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        pnl = float(trade.pnlcomm) if trade.pnlcomm is not None else float(trade.pnl)
        self.total_trades += 1
        if pnl > 0:
            self.wins += 1
            self.win_total += pnl
        else:
            self.losses_total += pnl
        self.wins_lv = (self.wins / self.total_trades * 100.0) if self.total_trades > 0 else 0.0
        self.win_losses_bi = (self.win_total / abs(self.losses_total)) if abs(self.losses_total) > 0 else 0.0
        self.win_lirun = self.win_total + self.losses_total
        try:
            import csv
            with open(self.csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([self.wins_lv, self.win_losses_bi, self.win_lirun])
        except Exception:
            pass

    def stop(self):
        end_value = float(self.broker.get_value())
        pnl_abs = end_value - float(self.initial_cash_at_start)
        roi = pnl_abs / float(self.initial_cash_at_start)
        print(f'策略结束 - 初始资金: {self.initial_cash_at_start:.2f}, 期末资产: {end_value:.2f}, 绝对盈亏: {pnl_abs:.2f}, ROI: {roi:.6%}')

    def get_asset_list(self):
        return self.asset_list

    def get_direction(self):
        return self.direction_list


def build_df_for_code(code: str, table_name: str, limit_num: int, ma_short: int, ma_long: int, db_mode: str = 'baostock', db_folder: Optional[str] = None) -> pd.DataFrame:
    if db_mode == 'crypto':
        base_folder = db_folder or os.path.join(os.getcwd(), 'gupiao_baostock')
        # 对于加密货币，使用固定的数据库文件名
        if code == 'BTC':
            db_path = os.path.join(base_folder, 'btc_data.db')
        elif code == 'ETH':
            db_path = os.path.join(base_folder, 'eth_data.db')
        else:
            raise ValueError(f'不支持的加密货币代码: {code}')
    elif db_mode == 'baostock':
        base_folder = db_folder or os.path.join(os.getcwd(), 'gupiao_baostock')
        db_path = os.path.join(base_folder, f'{code}_data.db')
    else:
        base_folder = db_folder or r'D:\\gupiao_sql'
        db_path = os.path.join(base_folder, f'{code}_data.db')

    df = load_df_generic(db_path, table_name, limit_num, code)
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
    return df


def run_backtest_interactive(code: str,
                             table_name: str,
                             limit_num: int,
                             initial_cash: float,
                             ma_short: int,
                             ma_long: int,
                             db_mode: str = 'baostock',
                             stake_qty: int = 10000,
                             trade_mode: str = 'both',
                             controller: Optional[InteractiveController] = None):
    controller = controller or InteractiveController()
    df = build_df_for_code(code, table_name, limit_num, ma_short, ma_long, db_mode=db_mode)
    controller.set_df(df)

    # backtrader env
    bt_config = BacktestConfig()
    cerebro = bt.Cerebro()
    # reset csv
    with open("portfolio_单.csv", 'w', newline='') as _f:
        pass
    cerebro.broker.setcash(initial_cash)
    cerebro.broker.setcommission(commission=bt_config.commission_rate)
    cerebro.addsizer(bt.sizers.FixedSize, stake=int(stake_qty))

    df['做多'] = df['上下穿多'].astype(float)
    df['做空'] = df['上下穿空'].astype(float)
    df.index = pd.to_datetime(df.index)
    data = SQLiteData(dataname=df)
    cerebro.adddata(data)
    cerebro.addstrategy(InteractiveStrategy, df=df, trade_mode=trade_mode, controller=controller, stake_qty=stake_qty)
    cerebro.addobserver(PortfolioObserver)

    results = cerebro.run()
    asset_list = results[0].get_asset_list()
    direction_list = results[0].get_direction()
    df['direction_list'] = direction_list
    多开_output = IF((df['direction_list'] == 1) & (REF(df['direction_list'], 1) != 1), 1, 0)
    空开_output = IF((df['direction_list'] == -1) & (REF(df['direction_list'], 1) != -1), 1, 0)
    空仓_output = IF((df['direction_list'] == 0) & (REF(df['direction_list'], 1) != 0), 1, 0)
    net_profit_list = [value - initial_cash for value in asset_list]
    df['net_profit_list'] = net_profit_list
    df['多开_output'] = 多开_output
    df['空开_output'] = 空开_output
    df['空仓_output'] = 空仓_output

    # metrics
    import os
    if os.path.exists("portfolio_单.csv") and os.path.getsize("portfolio_单.csv") > 0:
        df_portfolio = pd.read_csv("portfolio_单.csv", header=None)
        win_rate = df_portfolio.iloc[-1, 0]
        profit_loss_ratio = df_portfolio.iloc[-1, 1]
    else:
        win_rate = 0
        profit_loss_ratio = 0
    final_value = cerebro.broker.getvalue()
    profit = final_value - initial_cash

    # final chart
    columns_to_include = df.columns.tolist()
    zhibiaomc = f'{table_name}_deepseek{code}预测交易多空hb_回测_交互'
    data_dict = {col: df[col] for col in columns_to_include}
    data_dict['date'] = df.index
    huatucs(data_dict, code, table_name, zhibiaomc)

    chart_path = None
    try:
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
        'controller': controller,
    }


