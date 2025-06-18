from __future__ import (absolute_import, division, print_function, unicode_literals)

import os.path
import sys
import pandas as pd
from backtrader.plot import plot
import backtrader as bt

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

    if data_type_name == "Sharpe Ratio" and data.get('sharperatio') is not None :
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


class DualThrustStrategy(bt.Strategy):
    params = (
        ('period', 1),  # N 值，用于计算 maxH, minC, maxC, minL，通常为 1，range = max(maxH - minC, maxC - minL)
        ('k1', 0.9),  # K1 参数       upper = open+k1*range
        ('k2', 0.3),  # K2 参数       lower = open-k2*range
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.datahigh = self.datas[0].high
        self.datalow = self.datas[0].low
        self.order = None
        self.range_val = None
        self.upper_bound = None
        self.lower_bound = None

    def next(self):
        # self.log('Close, %.2f' % self.dataclose[0])

        # 仅在有足够历史数据时计算
        if len(self) <= self.p.period:
            return

        # 计算 HH, LC, HC, LL
        hh = self.datahigh.get(size=self.p.period)
        lc = self.dataclose.get(size=self.p.period)
        hc = self.dataclose.get(size=self.p.period)
        ll = self.datalow.get(size=self.p.period)

        hh_val = max(hh[:-1]) if len(hh) > 1 else hh[0]
        lc_val = min(lc[:-1]) if len(lc) > 1 else lc[0]
        hc_val = max(hc[:-1]) if len(hc) > 1 else hc[0]
        ll_val = min(ll[:-1]) if len(ll) > 1 else ll[0]

        # 计算 Range
        self.range_val = max((hh_val - lc_val), (hc_val - ll_val))

        # 计算上下界
        self.upper_bound = self.dataopen[0] + self.p.k1 * self.range_val
        self.lower_bound = self.dataopen[0] - self.p.k2 * self.range_val

        # 生成交易信号
        if not self.position:  # 没有仓位
            if self.dataclose[0] > self.upper_bound:
                self.log(f'BUY CREATE, 上破上限 {self.upper_bound:.2f}, 当前价格 {self.dataclose[0]:.2f}')
                self.order = self.buy()
            elif self.dataclose[0] < self.lower_bound:
                self.log(f'SELL CREATE, 下破下限 {self.lower_bound:.2f}, 当前价格 {self.dataclose[0]:.2f}')
                self.order = self.sell()
        else:
            if self.position.size > 0 and self.dataclose[0] < self.lower_bound:
                self.log(f'SELL CREATE, 平多开空, 下破下限 {self.lower_bound:.2f}, 当前价格 {self.dataclose[0]:.2f}')
                self.close()
                self.order = self.sell()
            elif self.position.size < 0 and self.dataclose[0] > self.upper_bound:
                self.log(f'BUY CREATE, 平空开多, 上破上限 {self.upper_bound:.2f}, 当前价格 {self.dataclose[0]:.2f}')
                self.close()
                self.order = self.buy()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))
            else:  # Sell
                self.log(
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 加载策略
    cerebro.addstrategy(DualThrustStrategy)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = 'ETHUSDm20240101-20250501-4H.csv'

    # 添加数据
    df = pd.read_csv(datapath, parse_dates=['time'], index_col='time')
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')

    # 设置初始资金
    cerebro.broker.setcash(1000.0)

    # 设置交易量 1
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)

    # 设置手续费0.1%
    cerebro.broker.setcommission(commission=0.001, leverage=100)

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

    print(f'年化收益:{annual_returns}')
    print(Sharpe_Ratio)
    # 绘制
    myscheme = MyPlotScheme()
    cerebro.plot(volume=None, scheme=myscheme)
