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
class alpha(bt.Strategy):
    params = (
        ('beta_gz', 0.56),  # 假设贵州茅台相对于沪深300的beta值 (示例值)
        ('market_exposure', 10000),  # 设定总的市场敞口（基础资金）
        ('min_stake', 1)  # A股最小交易单位100股
    )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.date(0)  # 通常只用日期即可，除非你有日内数据
        print(f'{dt.isoformat()}, {txt}')

    def __init__(self):
        self.market = self.datas[0]
        self.gz = self.datas[1]

        # 为每个数据源维护独立的订单引用
        self.order_market = None
        self.order_gz = None

        # 用于跟踪持仓情况
        self.position_market = self.getposition(self.market)
        self.position_gz = self.getposition(self.gz)

        self.count = 0  # 计数器用于示例平仓，实际策略应基于条件

    def notify_order(self, order):
        # 你的 notify_order 逻辑可以沿用我上次给你修正过的版本，它已经很完善了。
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    '买入已执行，标的: %s, 价格: %.2f, 成本: %.2f, 佣金: %.2f, 数量: %.2f' %
                    (order.data._name,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size))

            elif order.issell():
                self.log(
                    '卖出已执行，标的: %s, 价格: %.2f, 成本: %.2f, 佣金: %.2f, 数量: %.2f.' %
                    (order.data._name,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.executed.size))

            # 清除订单引用
            if order.data == self.market:
                self.order_market = None
            elif order.data == self.gz:
                self.order_gz = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log(f'订单取消/保证金不足/被拒绝，标的: {order.data._name}')
            if order.data == self.market:
                self.order_market = None
            elif order.data == self.gz:
                self.order_gz = None

    def next(self):
        # 示例：简单的首次开仓逻辑
        # 在实际对冲策略中，这里应该有更复杂的条件，例如：
        # - 计算当前的 Beta 值是否偏离了目标值
        # - 检查市场波动性、流动性等

        # 如果目前没有持仓（或达到重新平衡条件）
        if not self.position_market and not self.position_gz:
            # 计算个股（gz）的买入数量
            # 假设我们用 market_exposure 的一部分资金买入gz，
            # 并用另一部分资金对冲 market
            # 这里需要根据你的 Beta 对冲策略具体定义，
            # 例如：对冲后的头寸价值应为0，或中性。

            # 假设对冲的思路是：
            # 1. 买入一定价值的个股 (gz)
            # 2. 根据该价值和 Beta 值，计算需要卖出的指数（market）的价值
            # 3. 将价值转换为股数

            # 1. 计算个股 (gz) 的买入数量
            # 假设我们用 params.market_exposure * (1 - params.beta_gz) 的资金来买入 gz
            # 这不是严格的 beta 对冲，只是一个示例，beta 对冲通常是：
            # 个股价值 = 总资金 * 权重 (例如，权重为1，则买入全部资金的个股)
            # 指数对冲价值 = 个股价值 * beta

            # 假设我们要构建一个 10000 元的个股多头敞口
            target_gz_value = self.p.market_exposure  # 比如10000元

            # 计算买入 gz 的数量
            # size = 目标价值 / 当前股价
            size_gz = int(target_gz_value / self.gz.close[0])
            size_gz = (size_gz // self.p.min_stake) * self.p.min_stake  # 确保是1的整数倍
            if size_gz == 0:  # 避免买入0股
                self.log(f"计算出的 {self.gz._name} 数量为0，无法下单。")
                return  # 或继续下一个数据源的计算

            # 计算对冲 market (指数) 的卖出数量
            # 对冲价值 = 个股多头价值 * Beta值
            hedge_market_value = target_gz_value * self.p.beta_gz

            # 转换为卖出 market 的股数 (注意这里如果是期货/期权，计算方式会不同)
            # 如果是现货指数ETF或指数基金，可以这样计算
            size_market = int(hedge_market_value / self.market.close[0])
            # A股指数基金也通常有最小交易单位，这里简化处理，只取整
            # size_market = (size_market // self.p.min_stake) * self.p.min_stake
            if size_market == 0:
                self.log(f"计算出的 {self.market._name} 数量为0，无法下单。")
                return  # 或继续下一个数据源的计算

            # 下单
            if not self.position_gz and self.order_gz is None:
                self.log(f'BUY {self.gz._name} CREATE, Size: {size_gz}, Price: {self.gz.close[0]:.2f}')
                self.order_gz = self.buy(data=self.gz, size=size_gz)

            # 注意：卖空 A 股现货指数是受限的，通常需要通过股指期货或其他衍生品实现。
            # 如果你的 market 是一个可以卖空的标的 (例如指数ETF，或者你连接了期货经纪商)，
            # 那么下面的 sell 操作才能执行。
            if not self.position_market and self.order_market is None:
                self.log(f'SELL {self.market._name} CREATE, Size: {size_market}, Price: {self.market.close[0]:.2f}')
                self.order_market = self.sell(data=self.market, size=size_market)

        # 示例平仓逻辑：
        # 实际对冲策略的平仓或调整，应该基于更复杂的条件，
        # 例如，当两个头寸的利差达到某个目标，或者 Beta 值显著变化需要重新平衡。
        self.count += 1
        if self.count == 243:
            if self.position_market:
                self.log(f'CLOSE ALL {self.market._name} POSITIONS')
                self.close(data=self.market)
            if self.position_gz:
                self.log(f'CLOSE ALL {self.gz._name} POSITIONS')
                self.close(data=self.gz)


if __name__ == '__main__':
    cerebro = bt.Cerebro()

    # 加载策略
    cerebro.addstrategy(alpha)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    print(modpath)
    datapath = '../数据获取/000300-20240523-20250523-1D.csv'
    datapath1 = '../数据获取/600519.SH-20240523-20250523-1D.csv'
    # 添加数据
    df = pd.read_csv(datapath, parse_dates=['time'], index_col='time')
    df1 = pd.read_csv(datapath1, parse_dates=['time'], index_col='time')
    df.index = pd.to_datetime(df.index)
    df1.index = pd.to_datetime(df1.index)
    data = bt.feeds.PandasData(dataname=df)
    data1 = bt.feeds.PandasData(dataname=df1)

    cerebro.adddata(data)
    cerebro.adddata(data1)

    # 添加分析器
    cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='tradeanalyzer')
    cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharperatio')
    cerebro.addanalyzer(bt.analyzers.AnnualReturn, _name='annualreturn')

    # 设置初始资金
    cerebro.broker.setcash(10000.0)

    # 设置交易量 1
    cerebro.addsizer(bt.sizers.FixedSize, stake=1)

    # 设置手续费0.1%
    cerebro.broker.setcommission(commission=0.001, leverage=1)

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
