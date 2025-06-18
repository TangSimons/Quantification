from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import os.path
import sys
import pandas as pd
from backtrader.plot import plot


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

    if data_type_name == "Sharpe Ratio":
        print(f"夏普比率: {data.get('sharperatio'):.3f}")
        return

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
class BollingerBandsMeanReversion(bt.Strategy):
    params = (
        ('period', 15),  # 布林带计算周期
        ('devfactor', 1.2),  # 标准差倍数
        ('movav', bt.indicators.SMA),  # 移动平均线类型 (默认 SMA)
    )

    def log(self, txt, dt=None):
        ''' 记录日志 '''
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.boll = bt.indicators.BBands(self.dataclose, period=self.p.period, devfactor=self.p.devfactor,
                                         movav=self.p.movav)
        self.order = None

    def next(self):

        # 如果收盘价高于上轨，发出卖出信号
        if self.dataclose[0] > self.boll.lines.top[0] and self.position:  # 使用 self.position
            self.order = self.close()
            self.log(f'平仓 CREATE, {self.dataclose[0]:.2f}')

        # 如果收盘价低于下轨，发出买入信号
        if self.dataclose[0] < self.boll.lines.bot[0] and not self.position:  # 增加 not self.position
            self.order = self.buy()
            self.log(f'BUY CREATE, {self.dataclose[0]:.2f}')

    # 交易执行后的回调函数
    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # 订单提交/接受，无需操作
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
                    'SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f.' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        else:
            self.log("OPERATION PROFIT, GROSS %.2f, NET %.2f" %
                     (trade.pnl, trade.pnlcomm))


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 加载策略
    cerebro.addstrategy(BollingerBandsMeanReversion)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = '../数据获取/ETHUSDm20240101-20250501-4H.csv'

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
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)

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
