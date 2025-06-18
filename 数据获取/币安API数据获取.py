from binance.client import Client
import pandas as pd
import datetime


proxies = {
    'http': 'http://127.0.0.1:10796',
    'https': 'http://127.0.0.1:10796'
}

# 如果你没有 API key，也可以不填，仍能获取公共行情数据
client = Client(requests_params={"proxies": proxies})

# 获取 ETH/USDT 的 1 小时 K 线数据，默认获取最近 500 条
klines = client.get_klines(symbol='ETHUSDT', interval=Client.KLINE_INTERVAL_1HOUR)

# 转换为 Pandas DataFrame
df = pd.DataFrame(klines, columns=[
    'timestamp', 'open', 'high', 'low', 'close', 'volume',
    'close_time', 'quote_asset_volume', 'number_of_trades',
    'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
])

# 转换时间戳
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# 只保留需要的列并格式化
df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']]
df[['open', 'high', 'low', 'close', 'volume']] = df[['open', 'high', 'low', 'close', 'volume']].astype(float)

# 保存csv
df.to_csv('币安ethusdt.csv',index=False)
