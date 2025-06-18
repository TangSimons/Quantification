import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
import joblib
import talib as tb
# 加载历史数据（仅用于训练）
data = pd.read_csv("../数据获取/ETHUSDm'+'2025-04-01'+'2025-05-30.csv")
data['returns'] = data['close'].pct_change()
data['rsi'] = tb.RSI(data['close'])
data['atr'] = tb.ATR(data['high'],data['low'],data['close'])
data['close_ma5'] = data['close'].rolling(window=20).mean()
data['close_ma20'] = data['close'].rolling(window=50).mean()
data = data.dropna()

# 特征工程
features = data[['close','atr','close_ma5','close_ma20']].values
labels = np.where(data['returns'].shift(-1) > 0, 1, -1)  # 下一根K线涨跌



# 保存模型参数
joblib.dump({
    'support_vectors': svm_model.support_vectors_,
    'dual_coef': svm_model.dual_coef_,
    'intercept': svm_model.intercept_,
    'classes': svm_model.classes_,
    'scaler_mean': train_scaler.mean_,
    'scaler_scale': train_scaler.scale_
}, 'svm_params.pkl')