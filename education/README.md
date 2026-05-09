# F1 數據科學教學平台（Product 7 MVP）

這是一套以 Monza 2024 F1 資料為例的中文教學內容，目標是把現有專案的分析能力整理成 5 個可以獨立閱讀與練習的 Markdown 課程。

## 課程結構

1. `education/lessons/01_pandas_basics.md`：Pandas 基礎與資料載入
2. `education/lessons/02_visualization.md`：視覺化入門
3. `education/lessons/03_statistics.md`：統計思維與車手穩定性
4. `education/lessons/04_f1_features.md`：F1 特徵工程與進階分析
5. `education/lessons/05_ml_baseline.md`：機器學習 baseline 入門

## 這份教材使用的資料

- `raw/laps.csv`
- `raw/results.csv`
- `raw/weather.csv`
- `raw/stints.csv`
- `raw/race_control.csv`
- `raw/telemetry_VER.csv`
- `raw/schedule_2024.csv`

## 相關程式模組

- `src/data_loader.py`
- `src/lap_analysis.py`
- `src/tyre_analysis.py`
- `src/weather_analysis.py`
- `src/race_analysis.py`
- `src/telemetry_analysis.py`

## 使用方式

每一課都包含：

- 概念說明
- 可直接參考的程式碼片段
- 練習題

教材設計原則：

- 以單站 Monza 2024 為核心案例
- 所有範例都盡量對應現有模組與資料欄位
- 不假設有跨站歷史資料
- 適合後續再擴充成 Notebook 或互動課程
