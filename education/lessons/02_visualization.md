# 第 2 課：視覺化入門——看懂 F1 圈速、輪胎與天氣

## 課程目標

學完這一課，你可以：

- 用圖表看圈速變化
- 把輪胎策略畫成時間線概念
- 觀察天氣和賽道溫度的變動
- 建立「先看圖，再下結論」的分析習慣

## 1. 為什麼 F1 特別適合做視覺化？

F1 資料有很強的時間序列特性：

- 圈與圈之間的速度變化
- 進站前後的節奏改變
- 天氣和賽道溫度的波動
- 遙測資料的速度、煞車、油門曲線

如果只看平均值，很容易忽略真正的策略差異。

## 2. 先從車手圈速線圖開始

```python
import matplotlib.pyplot as plt
from src.lap_analysis import get_driver_lap_times

ver = get_driver_lap_times('VER')

plt.figure(figsize=(10, 4))
plt.plot(ver['LapNumber'], ver['LapTime_seconds'], marker='o')
plt.title('VER 圈速變化')
plt.xlabel('Lap Number')
plt.ylabel('Lap Time (seconds)')
plt.grid(True, alpha=0.3)
plt.show()
```

你可以觀察：

- 哪些圈變慢
- 哪些圈可能是進站圈
- 輪胎老化後是否有明顯衰退

## 3. 比較多位車手

```python
from src.lap_analysis import get_lap_time_evolution

subset = get_lap_time_evolution(['LEC', 'NOR', 'VER'])

for driver in subset['Driver'].unique():
    dr = subset[subset['Driver'] == driver]
    plt.plot(dr['LapNumber'], dr['LapTime_seconds'], label=driver)

plt.title('主要車手圈速比較')
plt.xlabel('Lap Number')
plt.ylabel('Lap Time (seconds)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

這種圖特別適合比較：

- 領先集團的節奏
- 不同策略下的速度走勢
- 後段是否有保胎或 push

## 4. 天氣圖：賽道溫度與空氣溫度

```python
from src.weather_analysis import get_weather_timeline

weather = get_weather_timeline()
weather['Time_minutes'] = weather['Time'].dt.total_seconds() / 60

plt.figure(figsize=(10, 4))
plt.plot(weather['Time_minutes'], weather['AirTemp'], label='Air Temp')
plt.plot(weather['Time_minutes'], weather['TrackTemp'], label='Track Temp')
plt.title('Monza 2024 天氣變化')
plt.xlabel('Time (minutes)')
plt.ylabel('Temperature (°C)')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
```

### 觀察重點

- 賽道溫度通常比氣溫高很多
- 高溫會影響輪胎衰退
- 若有雨，策略會更複雜

## 5. 輪胎策略的視覺化思路

`src.tyre_analysis.get_tyre_strategy()` 已經整理出每位車手的 stint 與 compound。
雖然這裡未必直接畫甘特圖，但你可以先把資料轉成條狀圖思維：

```python
from src.tyre_analysis import get_tyre_strategy

strategy = get_tyre_strategy()
print(strategy[['driver', 'strategy', 'n_stops']].head())
```

如果要進一步視覺化，可以把 `stint_laps` 展開後畫成分段條形圖。

## 6. 遙測資料的圖：速度曲線

```python
from src.telemetry_analysis import get_speed_profile

telemetry = get_speed_profile('VER')

plt.figure(figsize=(10, 4))
plt.plot(telemetry['Distance'], telemetry['Speed'])
plt.title('VER 速度曲線')
plt.xlabel('Distance')
plt.ylabel('Speed (km/h)')
plt.grid(True, alpha=0.3)
plt.show()
```

這類圖常用來找：

- 煞車區段
- 全油門區段
- 彎道前後的速度落差

## 7. 小練習

1. 畫出 `LEC` 與 `NOR` 的圈速比較折線圖。
2. 用 `weather.csv` 畫出氣溫和賽道溫度的雙線圖。
3. 找出 `VER` 的速度曲線中明顯下降的區段，猜測那可能是哪一類彎道。
4. 試著說明：為什麼視覺化比直接看平均值更重要？

## 8. 進階挑戰

把圖表做成三欄排版：

- 左：圈速折線圖
- 中：天氣折線圖
- 右：速度曲線圖

目標不是做出最漂亮的圖，而是練習把多種資料放進同一個分析故事裡。
