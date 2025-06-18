import requests as req
import pandas as pd
import numpy as np

symbol = '000300'

url = 'https://tsanghi.com/api/fin/index/CHN/daily?token=c9f838a6754348ca9187a57448974b0b&ticker=000300&order=2'

response = req.get(url)
data = response.json()
data = pd.DataFrame(data['data'])
data['time'] = data['date']
data.sort_values(by = 'time',inplace=True)
data = data[['time', 'open', 'high', 'low', 'close']]
csv_filename = f'{symbol}.csv'
data.to_csv(csv_filename,index=False)