import pandas as pd
import requests as req
import datetime

url = "https://api.huobi.pro/market/history/kline"
params = {
    'symbol': 'ethusdt',
    'period': '60min',# 1min, 5min, 15min, 30min, 60min, 4hour, 1day, 1mon, 1week, 1year
    'size': '2000'  # 获取2000条数据
}

proxies = {
    'http': 'http://127.0.0.1:10796',
    'https': 'http://127.0.0.1:10796'
}

try:
    response = req.get(url, params=params, proxies=proxies, timeout=5)
    response.raise_for_status()
    data = response.json()
    if data['status'] == 'ok' and 'data' in data:
        df = pd.DataFrame(data['data'])
        df['time'] = pd.to_datetime(df['id'], unit='s')
        print(df.head(5))
        df.set_index(df['time'], inplace=True)
        df.sort_index(inplace=True)
        print(df.head(5))
        # 选择需要的列
        df = df[['time','open', 'high', 'low', 'close','vol']]
        print(df.head())
        df.to_csv(params['symbol']+ '.csv',index=False)
    else:
        print("API返回数据格式异常:", data)

except req.exceptions.RequestException as e:
    print("请求失败:", e)
