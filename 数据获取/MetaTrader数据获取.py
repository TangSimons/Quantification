import pandas as pd
import MetaTrader5 as mt5

# 连接到 MT5
if not mt5.initialize():
    print("初始化失败")
    mt5.shutdown()
    quit()

# 设置要获取的品种和时间范围
symbol = "ETHUSDm"
start_time = "2025-04-01"
end_time = "2025-05-30"
timeframe = mt5.TIMEFRAME_H1 # 日线数据
start_date = pd.to_datetime(start_time)
end_date = pd.to_datetime(end_time)

# 获取历史数据
rates = mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

# 转换为 DataFrame
df = pd.DataFrame(rates)
df['time'] = pd.to_datetime(df['time'], unit='s')
df.dropna()
# 保存为 CSV
csv_filename = f"{symbol}'+'{start_time}'+'{end_time}.csv"
df.to_csv(csv_filename, index=False)

print(f"数据已保存为 {csv_filename}")

# 断开连接
mt5.shutdown()