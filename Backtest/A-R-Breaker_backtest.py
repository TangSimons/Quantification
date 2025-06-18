from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import os.path
import sys
import pandas as pd
from backtrader.plot import plot
import datetime


# 提取分析器数据
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

    '''if data_type_name == "Sharpe Ratio":
        print(f"夏普比率: {data.get('sharperatio'):.3f}")
        return'''

    if data_type_name == 'annual_returns':
        total = 0
        count = 0
        for year in range(2024, 2024 + len(annual_returns)):
            total += annual_returns[year]
            count += 1
        average_return = total / count
        print(f'平均年度收益率：{average_return * 100:.3f}%')

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
        self.style = 'candle'
        self.barup = 'red'
        # Default color for a bearish bar/candle
        self.bardown = 'green'
# 定义双突破策略类
class RBreakerStrategy(bt.Strategy):
    params = (
        ('stoploss_points', ),
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def __init__(self):
        self.high_l1 = self.datas[0].high
        self.low_l1 = self.datas[0].low
        self.close_l1 = self.datas[0].close
        self.pivot = (self.high_l1[0] + self.low_l1[0] + self.close_l1[0]) / 3
        self.bBreak = self.high_l1[0] + 2 * (self.pivot - self.low_l1[0])
        self.sSetup = self.pivot + (self.high_l1[0] - self.low_l1[0])
        self.sEnter = 2 * self.pivot - self.low_l1[0]
        self.bEnter = 2 * self.pivot - self.high_l1[0]
        self.bSetup = self.pivot - (self.high_l1[0] - self.low_l1[0])
        self.sBreak = self.low_l1[0] - 2 * (self.high_l1[0] - self.pivot)


        self.order = None
        self.open_position_price = None

    def next(self):

        # 获取当前价格
        close_price = self.datas[0].close[0]
        high_price = self.datas[0].high[0]
        low_price = self.datas[0].low[0]

        # 获取现有持仓
        long_position = self.position.size > 0
        short_position = self.position.size < 0
        in_position = long_position or short_position

        # 突破策略:
        if not in_position:  # 空仓条件下
            if close_price > self.bBreak:
                # 在空仓的情况下，如果盘中价格超过突破买入价，则采取趋势策略，即在该点位开仓做多
                self.order = self.buy()
                self.log(f'空仓,盘中价格超过突破买入价: 开仓做多, Price: {close_price:.2f}')
                self.open_position_price = close_price
            elif close_price < self.sBreak:
                # 在空仓的情况下，如果盘中价格跌破突破卖出价，则采取趋势策略，即在该点位开仓做空
                self.order = self.sell()
                self.log(f'空仓,盘中价格跌破突破卖出价: 开仓做空, Price: {close_price:.2f}')
                self.open_position_price = close_price

        # 设置止损条件和反转策略
        elif self.order is None:  # 避免在同一根K线上重复交易
            if long_position and self.open_position_price is not None and (
                    self.open_position_price - close_price >= self.p.stoploss_points):
                self.log(f'多头持仓, 达到止损点, 平仓, Price: {close_price:.2f}')
                self.order = self.close()
            elif short_position and self.open_position_price is not None and (
                    close_price - self.open_position_price >= self.p.stoploss_points):
                self.log(f'空头持仓, 达到止损点, 平仓, Price: {close_price:.2f}')
                self.order = self.close()

            # 反转策略:
            elif long_position:  # 多仓条件下
                if self.datas[0].high[-1] > self.sSetup and close_price < self.sEnter:
                    # 多头持仓,当日内最高价超过观察卖出价后，盘中价格出现回落，且进一步跌破反转卖出价构成的支撑线时，反手做空
                    self.log(f'多头持仓, 最高价超观察卖出价且跌破反转卖出价: 反手做空, Price: {close_price:.2f}')
                    self.order = self.close()
                    self.order = self.sell()
                    self.open_position_price = close_price
            elif short_position:  # 空头持仓
                if self.datas[0].low[-1] < self.bSetup and close_price > self.bEnter:
                    # 空头持仓，当日内最低价低于观察买入价后，盘中价格出现反弹，且进一步超过反转买入价构成的阻力线时，反手做多
                    self.log(f'空头持仓, 最低价低于观察买入价且超过反转买入价: 反手做多, Price: {close_price:.2f}')
                    self.order = self.close()
                    self.order = self.buy()
                    self.open_position_price = close_price

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(f'BUY EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.open_position_price = order.executed.price
            elif order.issell():
                self.log(f'SELL EXECUTED, Price: {order.executed.price:.2f}, Cost: {order.executed.value:.2f}, Comm: {order.executed.comm:.2f}')
                self.open_position_price = order.executed.price

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'Order Canceled/Margin/Rejected')

        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log(f'OPERATION PROFIT, GROSS {trade.pnl:.2f}, NET {trade.pnlcomm:.2f}')

    def stop(self):
        self.log('回测结束, 当前账户价值 %.2f' % self.broker.getvalue())


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 加载策略
    cerebro.addstrategy(RBreakerStrategy)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = 'ETHUSDm20240101-20250501-4H.csv'

    # 添加数据
    df = pd.read_csv(datapath, parse_dates=['time'], index_col='time')
    print(df.index.dtype)
    print(df.index[:5])
    df.index = pd.to_datetime(df.index)
    data = bt.feeds.PandasData(dataname=df)

    cerebro.adddata(data)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')

    # 设置初始资金
    cerebro.broker.setcash(100.0)

    # 设置交易量 1
    cerebro.addsizer(bt.sizers.FixedSize, stake=0.01)

    # 设置手续费0.1%
    cerebro.broker.setcommission(commission=0.001, leverage=400)

    # 运行回测
    results = cerebro.run()
    # 添加策略
    strategy = results[0]

    # 获取分析数据
    drawdown_analysis = strategy.analyzers.drawdown.get_analysis()
    trade_analysis = strategy.analyzers.tradeanalyzer.get_analysis()
    Sharpe_Ratio = strategy.analyzers.sharperatio.get_analysis()
    annual_returns = strategy.analyzers.annualreturn.get_analysis()

    # 打印回测结果
    extract_metrics(drawdown_analysis, "Drawdown Analysis")

    extract_metrics(trade_analysis, "Trade Analysis")

    extract_metrics(Sharpe_Ratio, "Sharpe Ratio")

    extract_metrics(annual_returns, "annual_returns")

    print(annual_returns)
    # 绘制
    myscheme = MyPlotScheme()
    cerebro.plot(volume=None, iplot=True, scheme=myscheme)
