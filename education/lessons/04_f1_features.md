# 第 4 課：F1 特徵工程與進階分析

## 課程目標

學完這一課，你可以：

- 從原始 F1 資料中萃取分析特徵
- 理解得失位、策略、天氣、遙測如何組合成特徵
- 用現有模組做更高層次的賽事解讀
- 為後面的機器學習課打基礎

## 1. 什麼是特徵工程？

特徵工程就是把原始資料轉成更有分析價值的欄位。

例如：

- `GridPosition - Position` = 得失位
- 平均圈速 = pace 特徵
- `std / mean` = 穩定性特徵
- `n_stops` = 策略特徵
- `rain` = 天氣特徵
- `full_throttle_pct` = 遙測風格特徵

這些特徵比原始欄位更適合做比較和建模。

## 2. 得失位分析

```python
from src.race_analysis import get_position_change_summary

pos = get_position_change_summary()
print(pos[['Abbreviation', 'GridPosition', 'Position', 'change_label']].head(10))
```

### 解讀

- 正值：比起跑位進步
- 負值：比起跑位退步
- 這個指標很適合快速看誰超越了預期

在 Monza 2024 中，這種分析可以直接對照報告中的名次變動。

## 3. 輪胎策略特徵

```python
from src.tyre_analysis import get_tyre_strategy

strategy = get_tyre_strategy()
print(strategy[['driver', 'n_stops', 'stops_label', 'compounds', 'strategy']].head())
```

### 可以衍生的特徵

- `n_stops`
- `stint_count`
- `first_compound`
- `last_compound`
- `longest_stint`
- `strategy_pattern`

例如：

- `1-stop` 可能代表更長的 stint 管理
- `2-stop` 可能代表更積極的 pace
- `3-stop` 可能反映特殊情況或被動策略

## 4. 天氣與賽況特徵

```python
from src.weather_analysis import get_weather_summary

ws = get_weather_summary()
print(ws)
```

你可以把這些資訊轉成模型特徵：

- `rainfall`: 是否下雨
- `avg_track_temp`: 平均賽道溫度
- `wind_speed_avg`: 平均風速
- `records_count`: 天氣樣本數

這些特徵在比賽後分析很重要，因為它們會影響輪胎與節奏。

## 5. 遙測特徵

```python
from src.telemetry_analysis import get_throttle_brake_analysis

tele = get_throttle_brake_analysis('VER')
print(tele)
```

可用特徵包括：

- `full_throttle_pct`
- `braking_pct`
- `coasting_pct`
- `avg_speed`
- `max_speed`
- `avg_rpm`
- `brake_points`

### 這些特徵可以回答什麼？

- 車手是偏進攻還是偏保守？
- 煞車點多不多？
- 速度曲線是否有明顯特徵？

## 6. 把多個資料源合併成一張特徵表

下面是一個簡化示意：

```python
import pandas as pd
from src.race_analysis import get_position_change_summary
from src.lap_analysis import get_all_drivers_consistency
from src.tyre_analysis import get_tyre_strategy

pos = get_position_change_summary()
cons = get_all_drivers_consistency()
strat = get_tyre_strategy()

features = pos.merge(cons[['Driver', 'avg_laptime', 'cv']], left_on='Abbreviation', right_on='Driver', how='left')
features = features.merge(strat[['driver', 'n_stops']], left_on='Abbreviation', right_on='driver', how='left')

print(features.head())
```

這一步就是從「分析單一表」邁向「建模資料表」的關鍵。

## 7. F1 特徵設計原則

1. 可解釋：要知道特徵從哪來
2. 可重複：每次跑出來結果一致
3. 不洩漏答案：不要把最終結果直接當特徵
4. 跟業務問題一致：你想預測什麼，就設計什麼特徵

## 8. 小練習

1. 為 `results.csv` 新增一個 `position_change` 欄位。
2. 從 `get_tyre_strategy()` 中挑出 `n_stops` 作為分類特徵。
3. 把 `get_weather_summary()` 的 `rainfall` 轉成 0/1。
4. 說明為什麼 `Position` 不能直接拿來預測 `Position`。

## 9. 進階挑戰

請你設計一張「車手特徵表」，至少包含：

- 車手代號
- 平均圈速
- 圈速 CV
- 得失位
- 進站次數
- 是否有降雨
- 平均速度

這張表就是下一課機器學習 baseline 的核心輸入。
