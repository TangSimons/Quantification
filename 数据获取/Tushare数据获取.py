import requests as req
import pandas as pd
import numpy as np
import tushare as ts

pro = ts.pro_api()
symbol = '600519.SH'
guizhou = pro.daily(ts_code=symbol, start_date='20240523', end_date='20250523')

#market = pro.index_daily(ts_code='000300.SH', start_date='20140101', end_date='20141231')

guizhou.dropna()
guizhou['time'] = guizhou['trade_date']
guizhou.sort_values(by='time', inplace=True)
guizhou = guizhou[['time', 'open', 'high', 'low', 'close']]
csv_filename = f"{symbol}.csv"
guizhou.to_csv(csv_filename, index=False)
