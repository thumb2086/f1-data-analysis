# 第 5 課：機器學習導論——建立 F1 baseline 預測模型

## 課程目標

學完這一課，你可以：

- 理解 baseline 模型在教學與產品中的用途
- 把 F1 特徵表切成訓練集與測試集
- 建立一個簡單的分類或回歸模型
- 用最基本的方法評估模型效果

## 1. 先講清楚：什麼是 baseline？

Baseline 不是最強模型，而是「先把流程跑通」的最小可用版本。

在這個 F1 專案裡，baseline 的目標可能是：

- 預測車手是否能進前 3
- 預測最終名次分級
- 預測得失位是正還是負

因為目前資料主要是 Monza 2024 單站，所以這裡更適合把它當教學範例，而不是最終生產模型。

## 2. 準備特徵表

你可以先把前面課程做過的特徵整理成一張表：

```python
import pandas as pd

from src.race_analysis import get_position_change_summary
from src.lap_analysis import get_all_drivers_consistency
from src.tyre_analysis import get_tyre_strategy
from src.weather_analysis import get_weather_summary

pos = get_position_change_summary()
cons = get_all_drivers_consistency()
strat = get_tyre_strategy()
weather = get_weather_summary()

features = pos.merge(
    cons[['Driver', 'avg_laptime', 'cv']],
    left_on='Abbreviation', right_on='Driver', how='left'
).merge(
    strat[['driver', 'n_stops']],
    left_on='Abbreviation', right_on='driver', how='left'
)

features['rainfall'] = int(weather['rainfall'])
features = features.fillna(0)

print(features.head())
```

## 3. 做一個簡單分類目標

例如，我們想預測是否進前 3：

```python
features['is_podium'] = (features['Position'] <= 3).astype(int)
```

這種目標比直接預測精確名次更容易上手。

## 4. 切分訓練與測試

如果資料量很小，切分結果會不穩定；但教學上仍然要示範標準流程。

```python
from sklearn.model_selection import train_test_split

X = features[['GridPosition', 'avg_laptime', 'cv', 'n_stops', 'position_change', 'rainfall']]
y = features['is_podium']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.3, random_state=42, stratify=y
)
```

## 5. 建立最小可用模型

```python
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix

model = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),
    ('clf', LogisticRegression(max_iter=1000))
])

model.fit(X_train, y_train)
pred = model.predict(X_test)

print(confusion_matrix(y_test, pred))
print(classification_report(y_test, pred))
```

### 為什麼先用 Logistic Regression？

- 簡單
- 可解釋
- 適合作為 baseline
- 容易看出哪些特徵有影響

## 6. 觀察特徵重要性

如果想看係數方向：

```python
import pandas as pd

coef = pd.Series(model.named_steps['clf'].coef_[0], index=X.columns)
print(coef.sort_values(ascending=False))
```

### 解讀

- 正值：有助於預測進前 3
- 負值：對進前 3 不利
- 這只是線性模型的視角，並不代表真實世界唯一答案

## 7. 常見教學重點

### 資料太少怎麼辦？

- 誠實說明這是單站 baseline
- 不要過度宣稱模型泛化能力
- 把重點放在方法與流程，而不是分數高低

### 資料洩漏是什麼？

如果你把 `Position` 當成特徵去預測 `Position`，模型會作弊。

### 為什麼 baseline 很重要？

因為它讓你知道：

- 資料有沒有問題
- 特徵是否合理
- 流程能不能端到端跑通

## 8. 小練習

1. 把目標改成「是否得分」，重新訓練一次模型。
2. 嘗試加入 `Points` 以外的特徵，觀察結果變化。
3. 比較 `LogisticRegression` 和 `RandomForestClassifier` 的差異。
4. 用一句話說明為什麼這個模型只能算 Monza 2024 baseline。

## 9. 進階挑戰

試著把模型包成一個函式：

- 輸入：特徵表
- 輸出：預測結果、機率、簡單文字解釋

這會是後續 Product 2 預測系統的雛形，也能和 Product 3 報告、Product 6 Bot 共用。
