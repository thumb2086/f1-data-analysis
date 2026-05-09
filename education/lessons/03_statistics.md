# 第 3 課：統計思維——一致性、衰退率與相關性

## 課程目標

學完這一課，你可以：

- 用平均數、標準差、變異係數描述圈速穩定性
- 理解輪胎衰退率的概念
- 用相關性看天氣與圈速的關係
- 把統計指標轉成可解釋的分析結論

## 1. 為什麼單看最快圈不夠？

F1 比賽不是單圈計時賽。
一位車手也許有很快的單圈，但如果每一圈波動很大，整體策略未必好。

因此我們要看：

- 平均圈速：整體節奏
- 標準差：波動程度
- 變異係數 CV：把波動標準化後比較

## 2. 圈速一致性

專案裡已經有對應函式：`src.lap_analysis.get_lap_consistency()`。

```python
from src.lap_analysis import get_lap_consistency

stats = get_lap_consistency('VER')
print(stats)
```

你會得到類似這種資訊：

- `mean`：平均圈速
- `std`：標準差
- `cv`：變異係數（%）
- `min` / `max`：最佳與最慢圈
- `laps_count`：樣本數

### 解讀方式

- `cv` 越小，通常代表越穩定
- `std` 很大，可能表示交通、輪胎衰退或策略變化
- 必須搭配情境解讀，不能只看數字

## 3. 車手一致性排行榜

```python
from src.lap_analysis import get_all_drivers_consistency

consistency = get_all_drivers_consistency()
print(consistency[['Driver', 'avg_laptime', 'std_laptime', 'cv', 'final_position']].head())
```

這類表格可以用來比較：

- 誰的圈速最穩
- 誰的 pace 較快但波動大
- 穩定性和最終名次是否有關係

## 4. 輪胎衰退率：用斜率看性能流失

`src.tyre_analysis.get_tyre_degradation()` 會把每個 stint 內的圈速和 `TyreLife` 做線性關係估計。

```python
from src.tyre_analysis import get_tyre_degradation

deg = get_tyre_degradation('HARD')
print(deg[['driver', 'compound', 'degradation_rate', 'laps_analyzed']].head())
```

### 怎麼理解？

- `degradation_rate` 是每增加 1 圈胎齡，圈速大約慢多少秒
- 值越大，代表衰退越明顯
- 不同胎種的衰退通常不同

### 注意

這裡使用的是簡化線性模型，適合 MVP 教學，不代表真實輪胎物理完全線性。

## 5. 天氣與圈速的相關性

先把天氣和圈速對齊：

```python
from src.weather_analysis import get_track_temp_effect

aligned = get_track_temp_effect()
print(aligned.head())
```

接著可以計算相關係數：

```python
corr = aligned[['LapTime_seconds', 'AirTemp', 'TrackTemp', 'Humidity']].corr()
print(corr)
```

### 解讀提醒

- 相關不等於因果
- `TrackTemp` 上升，圈速不一定就一定變慢，但可能有趨勢影響
- 如果有降雨，資料解讀要特別小心

## 6. 統計分析的寫作模板

當你寫分析結論時，可以用這個句型：

1. 先描述數字：平均值、標準差、斜率、相關係數
2. 再解釋現象：穩定、衰退、波動、策略改變
3. 最後補限制：樣本數少、單站資料、只是一個 baseline

例如：

> VER 在 Monza 的平均圈速不一定是最快，但其速度波動與胎齡變化可以看出明顯的 stint 特徵，因此適合用來觀察輪胎管理。

## 7. 小練習

1. 計算 `LEC`、`NOR`、`VER` 的圈速一致性，並比較 `cv`。
2. 找出 `SOFT`、`MEDIUM`、`HARD` 三種胎的平均衰退率。
3. 計算 `TrackTemp` 與 `LapTime_seconds` 的相關係數。
4. 寫一句話說明「相關性」與「因果關係」的差別。

## 8. 進階挑戰

選一位車手，畫出 `TyreLife` 對 `LapTime_seconds` 的散點圖，並加上簡單回歸線。

你不需要做到很複雜，重點是理解：

- 散點圖看的是趨勢
- 回歸線描述的是平均變化方向
- 統計值只是故事的起點，不是終點
