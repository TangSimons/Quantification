import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, time
import time as time_module
from Great_Send_Order_API import create_long_order, create_short_order, stop_long_order, stop_short_order
from sklearn.base import BaseEstimator, ClassifierMixin
import numpy as np
import matplotlib.pyplot as plt
import talib as tb
import joblib


class CustomRBF_SVM(BaseEstimator, ClassifierMixin):

    def __init__(self, C=1.0, gamma=0.12499999999999992):
        self.params = joblib.load(r'C:\Users\唐涛\Desktop\pycharm\Backtest\svm_params.pkl')
        self.C = C
        self.gamma = gamma
        self.scaler_mean = self.params['scaler_mean']
        self.scaler_scale = self.params['scaler_scale']
        self.support_vectors = self.params['support_vectors']
        self.dual_coef = self.params['dual_coef']
        self.intercept = self.params['intercept']

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


def is_trading_time():
    now = datetime.now().time()
    return time(0, 1) <= now <= time(23, 58)


def init_mt5():
    if not mt5.initialize():
        print("MT5 初始化失败, 错误代码:", mt5.last_error())
        quit()
    print("MT5 初始化成功")


def get_data(symbol, timeframe, n_bars=200):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df


def get_current_positions(symbol):
    """获取指定品种的当前持仓"""
    positions = mt5.positions_get(symbol=symbol)
    if positions is None:
        return []
    return positions


def calculate_indicators(df):
    df['ma10'] = tb.SMA(df['close'], timeperiod=10)
    df['ma50'] = tb.SMA(df['close'], timeperiod=20)
    df['atr'] = tb.ATR(df['high'], df['low'], df['close'])
    df['rsi'] = tb.RSI(df['close'])
    return df


def _rbf_kernel(x, support_vectors, gamma=0.1):
    return np.exp(-gamma * np.sum((x - support_vectors) ** 2, axis=1))


def run_strategy():
    symbol = "ETHUSDm"
    timeframe = mt5.TIMEFRAME_H1
    max_trades_per_day = 10000
    trade_count = 0
    long_count = 0  # 计数多单
    short_count = 0  # 计数空单
    time_history = []  # 画图
    equity_history = []  # 画图
    open_long_positions = {}  # 做多订单字典 key为order_id,值为symbol
    open_short_positions = {}  # 做空订单字典
    long_entry_price = []  # 做多价列表
    short_entry_price = []  # 做空价列表
    takeprofit_mult = 0.9  # ATR倍数止盈
    stoploss_mult = 0.9  # ATR倍数止损

    init_mt5()
    while trade_count < max_trades_per_day:
        if not is_trading_time():
            print("当前非交易时段，等待...")
            time_module.sleep(10)
            continue

        # 数据获取
        df = get_data(symbol, timeframe)
        df = calculate_indicators(df)
        last_bar = df.iloc[-1]
        current_features = np.array([
            last_bar['open'],
            last_bar['high'],
            last_bar['low'],
            last_bar['close'],
            last_bar['rsi'],
            last_bar['atr'],
            last_bar['ma10'],
            last_bar['ma50'],
        ])
        # 信号判断
        self = CustomRBF_SVM()
        scaled_features = (current_features - self.scaler_mean) / self.scaler_scale

        # SVM预测
        kernel_vals = _rbf_kernel(scaled_features, self.support_vectors)
        decision = np.dot(self.dual_coef, kernel_vals) + self.intercept
        prediction = 1 if decision >= 0 else -1

        #  将预测转换为信号
        buy_signal = prediction
        sell_signal = 1 if prediction == -1 else 0
        atr_signal = 1 if last_bar['atr'] > 30 else 0

        # 根据atr设置止盈止损
        atr_value = last_bar['atr']
        takeprofit_pct = atr_value * takeprofit_mult
        stoploss_pct = atr_value * stoploss_mult

        # 判断是否持仓
        current_positions = get_current_positions(symbol)
        position = len(current_positions) > 0



        if not position:
            # 判断做多
            if buy_signal and atr_signal:
                print(
                    '----------------------------------------------------------------------------------------------------------')
                print(f"{datetime.now()} - 触发买入做多信号")
                print(
                    '----------------------------------------------------------------------------------------------------------')
                result, order_id, order_long_price = create_long_order(symbol)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    open_long_positions[order_id] = symbol  # 添加多单id
                    long_entry_price.append(order_long_price)  # 添加开多价格
                    time_history.append(datetime.now())
                    equity_history.append(mt5.account_info().equity)
                    trade_count += 1
                    long_count += 1
                    print('-------------------------------------------')
                    print(f"做多订单成功，交易次数: {trade_count}/1000")
                    print(f"做多价格：{order_long_price}")
                    print(f"做多总次数:{long_count}")
                    print('-------------------------------------------')

            # 判断做空
            if sell_signal and atr_signal:
                print(
                    '----------------------------------------------------------------------------------------------------------')
                print(f"{datetime.now()} - 触发卖出做空信号")
                print(
                    '----------------------------------------------------------------------------------------------------------')
                result, order_id, order_short_price = create_short_order(symbol)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    open_short_positions[order_id] = symbol  # 添加空单id
                    short_entry_price.append(order_short_price)  # 添加空单价格
                    time_history.append(datetime.now())
                    equity_history.append(mt5.account_info().equity)
                    trade_count += 1
                    short_count += 1
                    print('-------------------------------------------')
                    print(f"做空订单成功，交易次数: {trade_count}/1000")
                    print(f"做空价格：{order_short_price}")
                    print(f"做空总次数:{short_count}")
                    print('-------------------------------------------')
        # 判断持有多仓，还是空仓
        long = 1 if len(open_long_positions) > 0 else 0
        short = 1 if len(open_short_positions) > 0 else 0

        if position:
            # 多单止损
            if len(long_entry_price) >= 1 and long:
                loss = ((long_entry_price[-1] - last_bar['close']) / long_entry_price[-1]) * 100
                if loss >= stoploss_pct:
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    print(f"{datetime.now()} - 触发多单止损信号")
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    for order_id, pos_symbol in list(open_long_positions.items()):
                        result, order_close_long_price = stop_long_order(pos_symbol, order_id)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            del open_long_positions[order_id]  # 从字典移除已止损多单id
                            del long_entry_price[-1]  # 删除做多价格
                            time_history.append(datetime.now())
                            equity_history.append(mt5.account_info().equity)
                            trade_count += 1
                            print('-------------------------------------------')
                            print(f"止损多仓成功，订单ID: {order_id}，交易次数: {trade_count}/1000")
                            print(f"止损多仓价格:{order_close_long_price}")
                            print('-------------------------------------------')

            # 空单止损
            if len(short_entry_price) >= 1 and short:
                loss = ((last_bar['close'] - short_entry_price[-1]) / short_entry_price[-1]) * 100
                if loss >= stoploss_pct:
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    print(f"{datetime.now()} - 触发空单止损信号")
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    for order_id, pos_symbol in list(open_short_positions.items()):
                        result, order_close_short_price = stop_short_order(pos_symbol, order_id)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            del open_short_positions[order_id]  # 从字典移除已止损空单id
                            del short_entry_price[-1]  # 删除做空价格
                            time_history.append(datetime.now())
                            equity_history.append(mt5.account_info().equity)
                            trade_count += 1
                            print('-------------------------------------------')
                            print(f"止损空仓成功，订单ID: {order_id}，交易次数: {trade_count}/1000")
                            print(f"止损空仓价格:{order_close_short_price}")
                            print('-------------------------------------------')

            # 多单止盈
            if len(long_entry_price) >= 1 and long:
                profit = ((last_bar['close'] - long_entry_price[-1]) / long_entry_price[-1]) * 100
                if profit >= takeprofit_pct:
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    print(f"{datetime.now()} - 触发多单止盈信号")
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    for order_id, pos_symbol in list(open_long_positions.items()):
                        result, order_close_long_price = stop_long_order(pos_symbol, order_id)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            del open_long_positions[order_id]  # 从字典移除已止盈多单id
                            del long_entry_price[-1]  # 删除做多价格
                            time_history.append(datetime.now())
                            equity_history.append(mt5.account_info().equity)
                            trade_count += 1
                            print('-------------------------------------------')
                            print(f"止盈多单成功，订单ID: {order_id}，交易次数: {trade_count}/1000")
                            print(f"止盈多单价格:{order_close_long_price}")
                            print('-------------------------------------------')
            # 空单止盈
            if len(short_entry_price) >= 1 and short:
                profit = ((long_entry_price[-1] - last_bar['close']) / long_entry_price[-1]) * 100
                if profit >= takeprofit_pct:
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    print(f"{datetime.now()} - 触发空单止盈信号")
                    print(
                        '----------------------------------------------------------------------------------------------------------')
                    for order_id, pos_symbol in list(open_short_positions.items()):
                        result, order_close_short_price = stop_short_order(pos_symbol, order_id)
                        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                            del open_short_positions[order_id]  # 从字典移除已止盈空单id
                            del short_entry_price[-1]  # 删除做空价格
                            time_history.append(datetime.now())
                            equity_history.append(mt5.account_info().equity)
                            trade_count += 1
                            print('-------------------------------------------')
                            print(f"止盈空单成功，订单ID: {order_id}，交易次数: {trade_count}/1000")
                            print(f"止盈空单价格:{order_close_short_price}")
                            print('-------------------------------------------')

        else:
            print(
                '----------------------------------------------------------------------------------------------------------')
            print(datetime.now().time(), '不满足交易条件')
            print(buy_signal, sell_signal, atr_signal)
            print(
                '-----------------------------------------------------------------------------------------------------------')

        time_module.sleep(10)

    print("交易次数已达上限，停止策略")
    fig, ax = plt.subplots()
    ax.plot(time_history, equity_history, label='收益曲线')
    fig.autofmt_xdate()
    plt.show()
    mt5.shutdown()


if __name__ == "__main__":
    run_strategy()
