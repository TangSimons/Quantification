import pandas as pd
import numpy as np
import MetaTrader5 as mt5
from Send_Order_API import create_order, stop_order
from datetime import datetime, time

import time as atime


# 判断是否初始化MT5平台成功
def if_initialize_mt5():
    if not mt5.initialize():
        print('MT5 初始化失败', mt5.last_error())
        quit()
    else:
        print('MT5 初始化成功')


# 判断是否交易时间段
def if_trade_time():
    now = datetime.now().time()
    open_time = time(0, 1)
    close_time = time(23, 59)
    if close_time <= now <= open_time:
        print('当前非交易时间段...')
        atime.sleep(120)


# 获取数据
def get_data(symbol, level, n_bar=100):
    data = mt5.copy_rates_from(symbol, level, datetime.now(), n_bar)
    data = pd.DataFrame(data)
    data['time'] = pd.to_datetime(data['time'])
    data.set_index('time', inplace=True)

    return data


# 获取当前持仓信息
def get_positions(symbol):
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return positions


# 网格策略类
class GridStrategy:
    def __init__(self, symbol, grid_size, grid_levels, lot_size):
        self.symbol = symbol
        self.grid_size = grid_size  # 网格大小(点)
        self.grid_levels = grid_levels  # 网格层数
        self.lot_size = lot_size  # 每单交易量
        self.base_price = None  # 基准价格
        self.grid_prices = []  # 网格价格列表
        self.current_level = 6  # 当前网格层级
        self.positions = {}  # 存储持仓信息 {order_id: (price, level)}
        self.buy_count = 0
        self.sell_count = 0
        self.total_count = 0

    def initialize_grid(self, current_price):
        """初始化网格"""
        self.base_price = current_price
        self.grid_prices = [self.base_price + i * self.grid_size for i in
                            range(-self.grid_levels, self.grid_levels + 1)]
        print(f"初始化网格，基准价: {self.base_price}, 网格价格: {self.grid_prices}")

    def check_grid(self, current_price):
        """检查价格变动并执行交易"""
        if self.base_price is None:
            self.initialize_grid(current_price)  # 以当前价格为基准，生成网格价格列表

        # 确定当前价格所在的网格层级
        new_level = np.searchsorted(self.grid_prices, current_price)

        if new_level != self.current_level:
            level_diff = new_level - self.current_level
            print('-----------------------------------------------------')
            print(datetime.now())
            print(f"价格变动到 {current_price}, 从层级 {self.current_level} 到 {new_level}")

            if level_diff > 0:  # 价格上涨level_diff层
                for _ in range(level_diff):  # 卖出执行level_diff次
                    if self.positions:  # 如果有持仓才卖出
                        oldest_order_id = next(iter(self.positions))  # 取出最早的买入订单号
                        price, level = self.positions.pop(oldest_order_id)  # 删除该订单，并获取买入价格，和所在层级
                        result, order_price = stop_order(self.symbol, oldest_order_id)
                        if result.retcode == mt5.TRADE_RETCODE_DONE:
                            self.sell_count += 1
                            self.total_count += 1
                            print(f"成功卖出 {self.lot_size} 手，价格: {order_price}")
                            print(f"卖出次数：{self.sell_count}")
                            print(f"交易次数：{self.total_count}")
                            print('-----------------------------------------------------')
            else:  # 价格下跌，买入
                for _ in range(-level_diff):  # 因为层级为负，level_diff为负值
                    result, order_id, order_price = create_order(self.symbol)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        self.positions[order_id] = (order_price, self.current_level)
                        self.buy_count += 1
                        self.total_count += 1
                        print(f"成功买入 {self.lot_size} 手，价格: {order_price}")
                        print(f"买入次数：{self.buy_count}")
                        print(f"交易次数：{self.total_count}")
                        print('-----------------------------------------------------')

            self.current_level = new_level


# 主策略函数
def strategy():
    symbol = 'ETHUSDm'
    data_level = mt5.TIMEFRAME_M1

    # 初始化MT5连接
    if_initialize_mt5()

    # 检查交易时间
    if_trade_time()

    # 网格策略参数
    grid_size = 5  # 100点网格
    grid_levels = 20  # 5层网格
    lot_size = 1.0  # 每单1手

    # 创建网格策略实例
    grid_strategy = GridStrategy(symbol, grid_size, grid_levels, lot_size)

    # 主循环
    while True:
        # 获取最新价格数据
        print('开始循环')
        data = get_data(symbol, data_level, 10)
        current_price = data['close'].iloc[-1]

        # 检查网格
        grid_strategy.check_grid(current_price)

        # 等待一段时间再检查
        atime.sleep(59)  # 每分钟检查一次


if __name__ == "__main__":
    strategy()
