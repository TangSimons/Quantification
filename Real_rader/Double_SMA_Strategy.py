import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, time
import time as time_module
from Send_Order_API import create_order,stop_order
import matplotlib.pyplot as plt


def is_trading_time():
    now = datetime.now().time()
    return time(0, 1) <= now <= time(23, 58)


def init_mt5():
    if not mt5.initialize():
        print("MT5 初始化失败, 错误代码:", mt5.last_error())
        quit()
    print("MT5 初始化成功")


def get_data(symbol, timeframe, n_bars=100):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, n_bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)
    return df


def calculate_indicators(df):
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()
    df['atr'] = df['high'] - df['low']
    return df


def run_strategy():
    symbol = "ETHUSDm"
    timeframe = mt5.TIMEFRAME_M3
    max_trades_per_day = 1000
    trade_count = 0
    open_positions = {}
    buy_count = 0
    sell_count = 0
    time_list = []
    profit = []

    init_mt5()
    while trade_count < max_trades_per_day:
        if not is_trading_time():
            print("当前非交易时段，等待...")
            time_module.sleep(3600)
            continue

        df = get_data(symbol, timeframe)
        df = calculate_indicators(df)
        last_bar = df.iloc[-1]

        buy_signal = (last_bar['ma5'] > last_bar['ma20']) and (last_bar['close'] > last_bar['open'])
        sell_signal = (last_bar['ma5'] < last_bar['ma20']) and (last_bar['close'] < last_bar['open'])

        if buy_signal:
            print(
                '----------------------------------------------------------------------------------------------------------')
            print(f"{datetime.now()} - 触发买入信号")
            print(
                '----------------------------------------------------------------------------------------------------------')
            result, order_id, order_buy_price = create_order(symbol)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                open_positions[order_id] = symbol
                time_list.append(datetime.now())
                profit.append(mt5.account_info().equity)
                trade_count += 1
                buy_count += 1
                print('-------------------------------------------')
                print(f"买入订单成功，交易次数: {trade_count}/1000")
                print(f"买入价格：{order_buy_price}")
                print(f"买入总次数:{buy_count}")
                print('-------------------------------------------')

        elif sell_signal:
            print(
                '----------------------------------------------------------------------------------------------------------')
            print(f"{datetime.now()} - 触发卖出信号")
            print(
                '----------------------------------------------------------------------------------------------------------')
            for order_id, pos_symbol in list(open_positions.items()):
                result, order_sell_price = stop_order(pos_symbol, order_id)
                if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                    del open_positions[order_id]  # 从字典移除已平仓订单
                    time_list.append(datetime.now())
                    profit.append(mt5.account_info().equity)
                    trade_count += 1
                    sell_count += 1
                    print('-------------------------------------------')
                    print(f"平仓成功，订单ID: {order_id}，交易次数: {trade_count}/1000")
                    print(f"平仓价格:{order_sell_price}")
                    print(f"卖出总次数：{sell_count}")
                    print('-------------------------------------------')

        else:
            print(
                '----------------------------------------------------------------------------------------------------------')
            print(datetime.now().time(), '不满足交易条件')
            print(last_bar['ma5'], last_bar['ma20'], last_bar['close'], last_bar['open'], last_bar['atr'],
                  df['atr'].mean() * 1.5)
            print(
                '-----------------------------------------------------------------------------------------------------------')

        time_module.sleep(181)

    print("交易次数已达上限，停止策略")
    fig, ax = plt.subplots()
    ax.plot(time_list, profit, label='收益曲线')
    fig.autofmt_xdate()
    plt.show()
    mt5.shutdown()


if __name__ == "__main__":
    run_strategy()
