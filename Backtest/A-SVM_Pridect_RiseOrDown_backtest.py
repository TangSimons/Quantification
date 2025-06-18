from __future__ import (absolute_import, division, print_function, unicode_literals)
from sklearn.base import BaseEstimator, ClassifierMixin
from backtrader.plot import plot
import joblib
import numpy as np
import backtrader as bt
import pandas as pd
import os.path
import sys


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


class CustomRBF_SVM(BaseEstimator, ClassifierMixin):
    def __init__(self, C=1.0, gamma=0.25):
        self.C = C
        self.gamma = gamma

    def _rbf_kernel(self, X, Y):
        # 修正为支持矩阵运算
        return np.exp(-self.gamma * np.sum((X[:, np.newaxis] - Y) ** 2, axis=2))

    def decision_function(self, X):
        X = np.atleast_2d(X)
        K = self._rbf_kernel(X, self.support_vectors_)
        return np.dot(self.dual_coef_, K.T).flatten() + float(self.intercept_[0])

    def predict(self, X):
        X = np.atleast_2d(X)
        dec_values = self.decision_function(X)
        return np.where(dec_values >= 0, self.classes_[1], self.classes_[0]).astype(int)


class MyPlotScheme(plot.PlotScheme):
    def __init__(self):
        super(MyPlotScheme, self).__init__()
        self.fmt_x_ticks = '%Y-%m-%d %H:%M:%S'  # Set the tick format
        self.fmt_x_data = '%Y-%m-%d %H:%M:%S'  # Set the data/hover format
        self.rowsmajor = 1
        self.rowsminor = 1


class SVMPredictStrategy(bt.Strategy):
    params = (('param_file', 'svm_params.pkl'),
              ('sl_point', 0.01),  # 止损点
              ('tp_point', 0.01),  # 止盈点
              )

    def log(self, txt, dt=None):
        dt = dt or self.datas[0].datetime.datetime()
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")}, {txt}')

    def __init__(self):
        # 加载预训练参数
        params = joblib.load(self.p.param_file)

        # 手动实现标准化（避免未来数据）
        self.scaler_mean = params['scaler_mean']
        self.scaler_scale = params['scaler_scale']
        self.atr = bt.indicators.ATR(self.datas[0])
        self.rsi = bt.indicators.RSI(self.datas[0])
        self.ma5 = bt.indicators.SMA(self.datas[0], period=20)
        self.ma20 = bt.indicators.SMA(self.datas[0], period=50)
        self.support_vectors = params['support_vectors']
        self.dual_coef = params['dual_coef']
        self.intercept = params['intercept']
        self.order = None
        self.entry_price = []

    def _rbf_kernel(self, x, gamma=0.1):
        return np.exp(-gamma * np.sum((x - self.support_vectors) ** 2, axis=1))

    def next(self):
        # 准备当前特征（必须与训练时完全一致！）
        current_features = np.array([
            #self.datas[0].open[0],
            #self.datas[0].high[0],
            #self.datas[0].low[0],
            self.datas[0].close[0],
            #self.rsi[0],
            self.atr[0],
            self.ma5[0],
            self.ma20[0],
        ])
        self.entry_price.append(self.datas[0].close[0])
        #  标准化（使用训练集的统计量）
        scaled_features = (current_features - self.scaler_mean) / self.scaler_scale
        position = self.broker.getposition(data=self.datas[0]).size

        # SVM预测
        kernel_vals = self._rbf_kernel(scaled_features)
        decision = np.dot(self.dual_coef, kernel_vals) + self.intercept
        prediction = 1 if decision >= 0 else -1
        atr = self.atr[0] > 30
        close = self.datas[0].close[0]  # 当前价格

        if self.entry_price:  # 确保 entry_price 不为空
            long_profit = (close - self.entry_price[-1]) / self.entry_price[-1]
            short_profit = (self.entry_price[-1] - close) / self.entry_price[-1]
        else:
            long_profit = 0
            short_profit = 0

        # 多头止盈止损 与 平仓
        if position > 0:
            if long_profit >= self.p.tp_point or long_profit <= -self.p.sl_point or prediction == -1  and atr:
                self.close()  # 这⾥不需要再写 self.order = 了，close()会⾃动返回⼀个 Order
                self.log('多头平仓')
                self.entry_price.clear()  # 清空，下一次开仓的时候再记录

        # 空头止盈止损  与 平仓
        elif position < 0:
            if short_profit >= self.p.tp_point or short_profit <= -self.p.sl_point or prediction == 1   and atr:
                self.close()
                self.log('空头平仓')
                self.entry_price.clear()

        # 开仓
        elif position == 0:
            if prediction == 1  and atr:
                self.buy()
                self.log('开多')
                self.entry_price.append(close)  # 记录开仓价格
            elif prediction == -1 and atr:
                self.sell()
                self.log('开空')
                self.entry_price.append(close)

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
    cerebro.addstrategy(SVMPredictStrategy)

    # 设置数据获取路径
    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = "../数据获取/ETHUSDm'+'2025-01-01'+'2025-05-30.csv"

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
    cerebro.addsizer(bt.sizers.FixedSize, stake=0.01)

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

    #extract_metrics(Sharpe_Ratio, "Sharpe Ratio")

    extract_metrics(drawdown_analysis, "Drawdown Analysis")

    extract_metrics(trade_analysis, "Trade Analysis")
    print(Sharpe_Ratio, annual_returns)
    # 绘制
    myscheme = MyPlotScheme()
    cerebro.plot(volume=None, iplot=True, scheme=myscheme)
