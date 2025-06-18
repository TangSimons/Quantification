from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import numpy as np
import pandas as pd
import os
import sys
from backtrader.plot import plot


def extract_metrics(data, data_type_name=""):
    """
    根据你的数据结构，提取关键指标并打印
    """
    print(f"==== {data_type_name} ====")

    if data_type_name == "Drawdown Analysis":
        print(f"最大回撤: {data.get('max', {}).get('drawdown'):.3f}%")
        print(f"最大回撤金额: {data.get('max', {}).get('moneydown'):.3f}")
        print(f"最大回撤周期: {data.get('max', {}).get('len')}")
        return  # Exit early since drawdown analysis is different

    if data_type_name == "Sharpe Ratio" and data.get('sharperatio'):
        print(f"夏普比率: {data.get('sharperatio'):.3f}")
        return

    if not isinstance(data, dict):
        print(f"数据类型错误：{type(data)}，应为字典。")
        return

    total_trades = data.get('total', {}).get('total', None)
    if total_trades is None:
        total_trades = data.get('total', None)  # Check if 'total' is directly available
        if total_trades is None:
            print("没有交易总数信息")
            return

    print(f"总交易次数：{total_trades}")

    # 盈亏情况
    pnl = data.get('pnl', {})
    total_profit = pnl.get('net', {}).get('total', 0)
    avg_profit = pnl.get('net', {}).get('average', 0)

    print(f"净利润总和：{total_profit:.3f}")
    print(f"平均每笔净利润：{avg_profit:.3f}")

    # 盈利交易数
    won = data.get('won', {})
    total_won = won.get('total', 0)
    # 亏损交易数
    lost = data.get('lost', {})
    total_lost = lost.get('total', 0)
    # 计算胜率
    win_rate = (total_won / total_trades) * 100 if total_trades else 0
    print(f"盈利交易次数：{total_won}")
    print(f"亏损交易次数：{total_lost}")
    print(f"胜率：{win_rate:.2f}%")

    # 盈利交易详情
    pnl_won = won.get('pnl', {})
    total_won_pnl = pnl_won.get('total', 0)
    max_won_pnl = pnl_won.get('max', 0)
    avg_won_pnl = pnl_won.get('average', 0)
    print(f"盈利总额：{total_won_pnl:.3f}")
    print(f"最大盈利：{max_won_pnl:.3f}")
    print(f"平均盈利：{avg_won_pnl:.3f}")

    # 亏损交易详情
    pnl_lost = lost.get('pnl', {})
    total_lost_pnl = pnl_lost.get('total', 0)
    max_lost_pnl = pnl_lost.get('max', 0)
    avg_lost_pnl = pnl_lost.get('average', 0)
    print(f"亏损总额：{total_lost_pnl:.3f}")
    print(f"最大亏损：{max_lost_pnl:.3f}")
    print(f"平均亏损：{avg_lost_pnl:.3f}")

    # 连续赢和输
    streak = data.get('streak', {})
    won_streak = streak.get('won', {})
    lost_streak = streak.get('lost', {})
    print(f"最长盈利连续 streak：{won_streak.get('longest')}")
    print(f"最长亏损连续 streak：{lost_streak.get('longest')}")

    print("\n==== 持仓信息 ====")
    len_stats = data.get('len', {})
    total_len = len_stats.get('total', 0)
    avg_len = len_stats.get('average', 0)
    max_len = len_stats.get('max', 0)
    min_len = len_stats.get('min', 0)

    print(f"总持仓次数：{total_len}")
    print(f"平均持仓时间：{avg_len}")
    print(f"最大持仓时间：{max_len}")
    print(f"最小持仓时间：{min_len}")

    # 持仓分类
    long_pos = len_stats.get('long', {})
    short_pos = len_stats.get('short', {})
    if long_pos and short_pos:
        print(f"多头持仓总数：{long_pos.get('total')}")
        print(f"空头持仓总数：{short_pos.get('total')}")


class MyPlotScheme(plot.PlotScheme):
    def __init__(self):
        super(MyPlotScheme, self).__init__()
        self.fmt_x_ticks = '%Y-%m-%d %H:%M:%S'  # Set the tick format
        self.fmt_x_data = '%Y-%m-%d %H:%M:%S'  # Set the data/hover format
        self.rowsmajor = 1
        self.rowsminor = 1


class GridStrategy(bt.Strategy):
    params = (
        ('grid_size', 40),  # 网格大小
        ('grid_levels', 15),  # 网格层数
        ('initial_level', 0),  # 初始网格层级
        ('take_profit_pct', 0.04),  # 止盈1%
        ('stop_loss_pct', 0.03),  # 止损2%
        ('max_positions', 4)  # 最大持仓5
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def initialize_grid(self, current_price):
        """初始化网格"""
        self.base_price = current_price
        self.grid_prices = [self.base_price + i * self.p.grid_size for i in
                            range(-self.p.grid_levels, self.p.grid_levels + 1)]
        self.log(f"初始化网格，基准价: {self.base_price}, 网格价格: {self.grid_prices}")

    def get_level(self, price):
        """确定价格所在的网格层级索引"""
        if self.base_price is None:
            return None
        levels = np.array(self.grid_prices)
        level_index = np.searchsorted(levels, price)
        return level_index

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.order = None
        self.entry_price = []  # 记录所有持仓[entry_price, size]
        self.grid_prices = []  # 网格价格列表
        self.current_level = 13  # 最初层级
        self.rsi = bt.indicators.RSI(self.datas[0])
        self.atr = bt.indicators.ATR(self.datas[0])
        self.initialize_grid(2300)

    def next(self):
        current_price = self.dataclose[0]
        new_level = self.get_level(current_price)

        # 判断是否有持仓
        position = self.broker.getposition(data=self.datas[0]).size >= 0.1

        # atr过滤
        atr = self.atr[0] < 5
        if position:
            for position_size in list(self.entry_price):  # 使用list复制避免修改问题
                entry_price, size = position_size
                profit_pct = (current_price - entry_price) / entry_price
                # 止损逻辑
                if profit_pct <= -self.p.stop_loss_pct:
                    self.log(f"触发止损  {current_price:.2f}")
                    self.order = self.sell(size=0.1)
                    self.entry_price.remove(position_size)

                # 止盈逻辑
                elif profit_pct >= self.p.take_profit_pct:
                    self.log(f"触发止盈  {current_price:.2f}")
                    self.order = self.sell(size=0.1)
                    self.entry_price.remove(position_size)

        if new_level is not None and new_level != self.current_level:
            # 层级变动计算
            level_diff = new_level - self.current_level
            # 价格上涨，有持仓，rsi，atr条件满足
            if level_diff > 0 and position and self.rsi[0] > 65 and atr:
                self.log(f"平仓订单, 价格:{self.dataclose[0]}")
                self.order = self.sell(size=0.1)

                # 价格下跌，rsi，atr条件满足
            elif level_diff < 0 and self.rsi[0] < 35 and atr and self.broker.getposition(data=self.datas[0]).size < self.p.max_positions:
                self.log(f"层级 {new_level}, 买0.1手")
                self.order = self.buy()
                self.entry_price.append([self.dataclose[0], 0.1])

        # 修正网格层级
        self.current_level = new_level

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Size: {order.executed.size}')

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected - Ref: {order.ref}')
            self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log(f"OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}")


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 数据加载路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = '../数据获取/ETHUSDm20250301-20250523-3m.csv'

    # 加载数据
    df = pd.read_csv(datapath, parse_dates=['time'], index_col='time')
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 添加网格策略
    cerebro.addstrategy(GridStrategy)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')
    # 设置初始资金
    cerebro.broker.setcash(100.0)

    # 设置交易量
    cerebro.addsizer(bt.sizers.FixedSize, stake=0.1)

    # 设置手续费
    cerebro.broker.setcommission(commission=0.0007, leverage=400.0)

    # 运行回测
    results = cerebro.run()
    strategy = results[0]
    # 获取分析数据
    drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
    trade_analysis = strategy.analyzers.tradeanalyzer.get_analysis()
    Sharpe_Ratio = strategy.analyzers.sharperatio.get_analysis()
    annual_returns = strategy.analyzers.annualreturn.get_analysis()

    # 打印回测结果
    print(annual_returns)
    print(Sharpe_Ratio)
    extract_metrics(drawdown_analysis, "Drawdown Analysis")

    extract_metrics(trade_analysis, "Trade Analysis")

    #extract_metrics(Sharpe_Ratio, "Sharpe Ratio")

    print('未平仓量：', cerebro.broker.getposition(data=cerebro.datas[0]))
    #绘制
    myscheme = MyPlotScheme()
    cerebro.plot(volume=None, iplot=True, scheme=myscheme)
