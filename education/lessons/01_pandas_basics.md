# 第 1 課：Pandas 基礎與 F1 資料載入

## 課程目標

學完這一課，你可以：

- 讀取專案中的 F1 CSV 資料
- 理解 DataFrame 的欄位與資料型別
- 使用 `filter`、`sort_values`、`groupby` 做基本整理
- 把原始賽事資料轉成可分析的表格

## 1. 為什麼先學 Pandas？

F1 分析最常見的第一步不是建模，而是把原始資料整理成可比較的格式。
例如：

- `laps.csv` 可以用來分析每一圈的速度與輪胎狀態
- `results.csv` 可以看最終名次與起跑位
- `weather.csv` 可以觀察氣溫和賽道溫度變化

在這個專案中，資料載入已經封裝在 `src/data_loader.py`，你可以直接重用。

## 2. 資料載入範例

```python
from src.data_loader import load_laps, load_results, load_weather

laps = load_laps()
results = load_results()
weather = load_weather()

print(laps.head())
print(results[['Abbreviation', 'FullName', 'GridPosition', 'Position']].head())
print(weather[['Time', 'AirTemp', 'TrackTemp']].head())
```

### 你會看到什麼？

- `load_laps()` 會把時間欄位轉成 `timedelta`
- `load_results()` 會把名次、起跑位與積分轉成數值
- `load_weather()` 會把天氣時間軸與溫度欄位整理好

## 3. 觀察欄位與型別

分析之前，先確認欄位長什麼樣：

```python
print(laps.info())
print(results.info())
print(weather.info())
```

常見重點：

- `LapTime`、`Sector1Time` 這類欄位是時間型別
- `Driver`、`Team` 是分類欄位
- `LapNumber`、`Position`、`TyreLife` 是數值欄位

## 4. 基本整理：篩選、排序、欄位選取

### 篩選某位車手

```python
ver_laps = laps[laps['Driver'] == 'VER']
print(ver_laps[['LapNumber', 'LapTime', 'Compound', 'TyreLife']].head())
```

### 只看有效圈

```python
clean_laps = laps[laps['IsAccurate'] == True]
```

### 找出最快圈

```python
fastest_lap = clean_laps.loc[clean_laps['LapTime'].idxmin()]
print(fastest_lap[['Driver', 'LapNumber', 'LapTime', 'Compound']])
```

### 依圈速排序

```python
leaderboard = clean_laps.sort_values('LapTime')
print(leaderboard[['Driver', 'LapNumber', 'LapTime']].head(10))
```

## 5. groupby 的第一個實戰：每位車手的平均圈速

```python
clean_laps = laps[laps['IsAccurate'] == True].copy()
clean_laps['LapTime_seconds'] = clean_laps['LapTime'].dt.total_seconds()

avg_lap = (
    clean_laps.groupby('Driver')
    .agg(avg_laptime=('LapTime_seconds', 'mean'),
         laps=('LapNumber', 'count'))
    .reset_index()
    .sort_values('avg_laptime')
)

print(avg_lap.head())
```

這個寫法很重要，因為後面的統計、特徵工程、機器學習都會用到同樣模式。

## 6. 和現有模組對照

專案裡已經有可直接參考的函式：

- `src.lap_analysis.get_driver_lap_times()`
- `src.lap_analysis.get_fastest_laps()`
- `src.race_analysis.get_final_standings()`
- `src.weather_analysis.get_weather_summary()`

你可以把這些函式當成「資料處理範本」。

## 7. 小練習

1. 載入 `laps.csv`，找出 `Driver == 'LEC'` 的所有圈數。
2. 計算每位車手的平均圈速，並依平均圈速由快到慢排序。
3. 找出 `results.csv` 中前 5 名車手的 `GridPosition` 與 `Position`。
4. 請回答：`load_laps()` 為什麼要先把 `LapTime` 轉成時間型別？

## 8. 進階挑戰

試著做一個表格，欄位包含：

- `Driver`
- `avg_laptime`
- `min_laptime`
- `max_laptime`
- `lap_count`

提示：先用 `groupby('Driver').agg(...)`，再用 `reset_index()`。
