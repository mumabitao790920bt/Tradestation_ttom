import os
from 下载股票历史数据.baostock_data_collector_final import BaoStockDataCollectorFinal


def download_daily_to_sqlite(code: str, name: str = "") -> str:
    """下载单个股票的历史数据（日/周/月）到 gupiao_baostock/{code}_data.db 并返回路径
    依赖 baostock_data_collector_final 中的实现
    """
    collector = BaoStockDataCollectorFinal()
    if not collector.login_baostock():
        raise RuntimeError('BaoStock 登录失败')
    try:
        stock_info = {'code': code, 'name': name or code}
        collector.collect_single_stock_data(stock_info)
    finally:
        collector.logout_baostock()
    db_path = os.path.join('gupiao_baostock', f'{code}_data.db')
    return db_path


