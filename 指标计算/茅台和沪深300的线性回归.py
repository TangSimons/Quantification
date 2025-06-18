import matplotlib.pyplot as plt
import matplotlib as mtl
import pandas as pd
import statsmodels.api as sm

mtl.rcParams['font.sans-serif'] = ['Microsoft YaHei']

# 读取数据
market = pd.read_csv(r'C:\Users\唐涛\Desktop\pycharm\000300.csv')
gz = pd.read_csv(r'C:\Users\唐涛\Desktop\pycharm\600519.SH.csv')

gz['time'] = gz['time'].astype(str)
gz['time'] = pd.to_datetime(gz['time'], format='%Y%m%d')
gz['time'] = gz['time'].dt.tz_localize(None)  # 移除時區

market['time'] = pd.to_datetime(market['time'])
market['time'] = market['time'].dt.tz_localize(None)  # 移除时区

# 使用公共的时间范围进行绘图 (关键步骤)
start_date = max(market['time'].min(), gz['time'].min())
end_date = min(market['time'].max(), gz['time'].max())

market_filtered = market[(market['time'] >= start_date) & (market['time'] <= end_date)]
gz_filtered = gz[(gz['time'] >= start_date) & (gz['time'] <= end_date)]

# 绘制图形
plt.plot(market_filtered['time'], market_filtered['close'], color='red', label='沪深300')
plt.plot(gz_filtered['time'], gz_filtered['close'], label='贵州茅台')

plt.xlabel('日期')
plt.ylabel('收盘价')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.legend()
#plt.show()

x = gz['close'].pct_change()[1:]
y = market['close'].pct_change()[1:]
X = sm.add_constant(x)  # 添加截距
model = sm.OLS(y, X).fit()
a = model.params[0]
b = model.params[1]
print("截距（常数项）a:", model.params[0])
print("斜率（x的系数）b:", model.params[1])

portfolio = -b*y+a
portfolio.plot()
x.plot()
y.plot()
#plt.show()
