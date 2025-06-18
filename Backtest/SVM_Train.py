
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn import svm
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

# 特征工程（必须与策略内完全一致）
features = data[['close','atr','close_ma5','close_ma20']].values
labels = np.where(data['returns'].shift(-1) > 0, 1, -1)  # 下一根K线涨跌

# 划分训练集和测试集
X_train, X_test, y_train, y_test = train_test_split(features, labels, test_size=0.2, random_state=42)

# 训练标准化器（仅用训练数据）
train_scaler = StandardScaler()
train_scaler.fit(X_train)

# 标准化训练集和测试集
X_train_scaled = train_scaler.transform(X_train)
X_test_scaled = train_scaler.transform(X_test)

# 训练SVM模型（标准化后的数据）
svm_model = svm.SVC(kernel='rbf', C=1.0, gamma='scale')
svm_model.fit(X_train_scaled, y_train)

# 在测试集上预测并评估
y_pred = svm_model.predict(X_test_scaled)
accuracy = accuracy_score(y_test, y_pred)
print(f"测试集准确率：{accuracy}")
# 保存模型参数（非完整模型！）
joblib.dump({
    'support_vectors': svm_model.support_vectors_,
    'dual_coef': svm_model.dual_coef_,
    'intercept': svm_model.intercept_,
    'classes': svm_model.classes_,
    'scaler_mean': train_scaler.mean_,
    'scaler_scale': train_scaler.scale_
}, 'svm_params.pkl')
def exact_result():
    return svm_model.dual_coef_, svm_model.support_vectors_, svm_model.support_
print(svm_model.dual_coef_.shape, svm_model.support_vectors_.shape, svm_model.support_.shape,svm_model.intercept_,svm_model._gamma,svm_model.classes_)