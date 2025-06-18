from __future__ import (absolute_import, division, print_function, unicode_literals)

import backtrader as bt
import os.path
import sys
import pandas as pd
from backtrader.plot import plot


# 提取分析器数据
def extract_metrics(data, data_type_name=""):
    print(f"==== {data_type_name} ====")

    if data_type_name == "Drawdown Analysis":
        print(f"最大回撤: {data.get('max', {}).get('drawdown'):.3f}%")
        print(f"最大回撤金额: {data.get('max', {}).get('moneydown'):.3f}")
        print(f"最大回撤周期: {data.get('max', {}).get('len')}")
        return

    if data_type_name == "Sharpe Ratio":
        print(f"夏普比率: {data.get('sharperatio'):.3f}")
        return

    if data_type_name == 'annual_returns':
        total = 0
        count = 0
        for year in range(2021, 2021 + len(annual_returns)):
            total += annual_returns[year]
            count += 1
        average_return = total / count
        print(f'平均年度收益率：{average_return * 100:.3f}%')

    if data_type_name == "Trade Analysis":
        total_trades = data.get('total', {}).get('total', None)

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

    if not isinstance(data, dict):
        print(f"数据类型错误：{type(data)}，应为字典。")
        return


class MyPlotScheme(plot.PlotScheme):
    def __init__(self):
        super(MyPlotScheme, self).__init__()
        self.fmt_x_ticks = '%Y-%m-%d %H:%M:%S'  # Set the tick format
        self.fmt_x_data = '%Y-%m-%d %H:%M:%S'  # Set the data/hover format
        self.rowsmajor = 1
        self.rowsminor = 1


# 定义双突破策略类
class DualBreakoutStrategy(bt.Strategy):
    params = (
        ('period1', 10),  # 5日移动平均线周期
        ('period2', 50),  # 20日移动均线周期
        ('takeprofit_mult', 0.85),  # ATR倍数止盈
        ('stoploss_mult', 0.4),  # ATR倍数止损
        ('atr_threshold', 0.015),  # 使用ATR/Close比率（2%）
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def __init__(self):
        self.dataclose = self.datas[0].close
        self.dataopen = self.datas[0].open
        self.sma5 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.period1)
        self.sma20 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.period2)
        self.trend_filter = bt.indicators.EMA(self.datas[0], period=200)
        self.atr = bt.indicators.ATR(self.datas[0])
        self.order = None
        self.entry_price = None

    def next(self):
        # 熊市扩大止盈止损
        if self.dataclose[0] < self.trend_filter[0] * 0.6:  # 深度熊市
            self.p.stoploss_mult =1.5  # 扩大止损容忍度
            self.p.takeprofit_mult = 2.0  # 提高止盈目标

        # 避开美东时间14:00-14:30重要数据发布
        '''dt = self.datas[0].datetime.time()
        if dt.hour == 14 and dt.minute < 30:
            return'''

        # 根据atr设置止盈止损
        takeprofit_pct = self.atr[0] * self.p.takeprofit_mult
        stoploss_pct = self.atr[0] * self.p.stoploss_mult

        # 信号计算
        buy_signal = (self.sma5[0] > self.sma20[0]) and (self.dataclose[0] < self.trend_filter)
        sell_signal = (self.sma5[0] < self.sma20[0]) and (self.dataclose[0] > self.trend_filter)
        atr_signal = (self.atr[0] / self.dataclose[0]) > self.p.atr_threshold

        # 开多开空
        if buy_signal and not self.position and atr_signal:
            self.order = self.buy()
            self.entry_price = self.dataclose[0]

        if sell_signal and not self.position and atr_signal:
            self.order = self.sell()
            self.entry_price = self.dataclose[0]

        # 判断多空
        short = self.position.size < 0
        long = self.position.size > 0

        # 多空止损
        if self.position and self.entry_price is not None and long:
            long_loss = ((self.entry_price - self.dataclose[0]) / self.entry_price) * 100
            if long_loss >= stoploss_pct:
                self.order = self.close()
                self.log(f"多单止损 at {self.dataclose[0]:.2f}, Loss: {long_loss:.2f}%")
                self.entry_price = None
        if self.position and self.entry_price is not None and short:
            short_loss = ((self.dataclose[0] - self.entry_price) / self.entry_price) * 100
            if short_loss >= stoploss_pct:
                self.order = self.close()
                self.log(f"空单止损 at {self.dataclose[0]:.2f}, Loss: {short_loss:.2f}%")
                self.entry_price = None
        # 多空止盈
        if self.position and self.entry_price is not None and long:
            long_profit = ((self.dataclose[0] - self.entry_price) / self.entry_price) * 100
            if long_profit >= takeprofit_pct:
                self.order = self.close()
                self.log(f"Take 多 Profit triggered at {self.dataclose[0]:.2f}, Profit: {long_profit:.2f}%")
                self.entry_price = None
        if self.position and self.entry_price is not None and short:
            short_profit = ((self.entry_price - self.dataclose[0]) / self.entry_price) * 100
            if short_profit >= takeprofit_pct:
                self.order = self.close()
                self.log(f"Take 空 Profit triggered at {self.dataclose[0]:.2f}, Profit: {short_profit:.2f}%")
                self.entry_price = None

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
            self.log("OPERATION PROFIT, GROSS %.2f, 盈利 %.2f" %
                     (trade.pnl, trade.pnlcomm))


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 加载策略
    cerebro.addstrategy(DualBreakoutStrategy)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = '../数据获取/ETHUSDm-6hour.csv'

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
    cerebro.broker.setcash(100.0)
    # 设置滑点
    cerebro.broker.set_slippage_perc(0.01)
    # 设置交易量 1
    cerebro.addsizer(bt.sizers.FixedSize, stake=0.1)

    # 设置手续费0.1%
    cerebro.broker.setcommission(commission=0.00007, leverage=400)

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
#    extract_metrics(annual_returns, "annual_returns")

#    extract_metrics(Sharpe_Ratio, "Sharpe Ratio")

    extract_metrics(drawdown_analysis, "Drawdown Analysis")

    extract_metrics(trade_analysis, "Trade Analysis")
    print(Sharpe_Ratio,annual_returns)
    # 绘制
    myscheme = MyPlotScheme()
    cerebro.plot(volume=None, iplot=True, scheme=myscheme)
