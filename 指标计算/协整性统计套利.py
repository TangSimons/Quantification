import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import statsmodels.api as sm

btc = pd.read_csv(r'C:\Users\唐涛\Desktop\pycharm\数据获取\000300.csv')
xau = pd.read_csv(r'C:\Users\唐涛\Desktop\pycharm\数据获取\600519.SH.csv')

# 1. 将 'time' 列转换为 datetime 类型并设置为索引
btc['time'] = pd.to_datetime(btc['time'])
btc.set_index('time', inplace=True)

xau['time'] = pd.to_datetime(xau['time'])
xau.set_index('time', inplace=True)

btc_daily_close = btc['close'].resample('D').last().dropna()
xau_daily_close = xau['close'].resample('D').last().dropna()

# 3. 合并数据，确保日期对齐
# inner merge 会只保留两个系列中都存在的日期
combined_df = pd.DataFrame({
    'btc_close': btc_daily_close,
    'xau_close': xau_daily_close
}).dropna() # 再次dropna以防合并后出现NaN（例如某个日期只有一方有数据）

if combined_df.empty:
    print("错误：合并后的DataFrame为空。请检查数据范围和日期格式是否一致。")
    exit()

# 4. 取对数价格，通常在协整性分析中使用对数价格
btc_log_close = np.log(combined_df['btc_close'])
xau_log_close = np.log(combined_df['xau_close'])

val = sm.tsa.stattools.coint(btc_log_close,xau_log_close)
print(val)