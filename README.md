# F1 數據分析專案 — Monza 2024

Monza 2024 義大利大獎賽的完整數據分析套件，涵蓋圈速、輪胎策略、遙測、排名變化、天氣分析，並延伸出 7 個可交付產品。

## 快速開始

把專案 clone 下來後，兩行指令就能開始使用：

```bash
# 1. 安裝依賴
pip install streamlit plotly pandas numpy

# 2. 啟動互動式儀表板
streamlit run https://raw.githubusercontent.com/thumb2086/f1-data-analysis/master/src/dashboard.py
```

> **⚠️ Python 3.10+ 必備。** 建議在虛擬環境中執行。

### 一次跑完所有產品（Smoke Test）

確認所有模組都能正常運作：

```bash
python3 -m compileall src && \
python3 -m src.prediction --output-dir /tmp/st/prediction && \
python3 -c "from src.reports import build_race_report; r=build_race_report(); print('Report OK:', len(r), 'sections')" && \
python3 -c "from src.rating import build_rating_leaderboard; lb=build_rating_leaderboard(); print('Rating OK:', len(lb), 'drivers')" && \
python3 src/coaching.py raw/telemetry_VER.csv --output-dir /tmp/st/coaching && \
python3 -m src.bot.demo --output-dir /tmp/st/bot --commands standings weather && \
echo "=== All smoke tests passed ==="
```

### 各產品 CLI 一覽

| 產品 | 指令 |
|------|------|
| 產品 1 — 儀表板 | `streamlit run src/dashboard.py` |
| 產品 2 — 預測 | `python -m src.prediction --output-dir outputs/prediction` |
| 產品 3 — 報告 | `python -m src.reports.report_builder` |
| 產品 4 — 評分 | (Python import: `from src.rating import build_rating_leaderboard`) |
| 產品 5 — 教練 | `python src/coaching.py raw/telemetry_VER.csv --output-dir outputs/coaching` |
| 產品 6 — Bot | `python -m src.bot.demo --output-dir outputs/bot` |
| 產品 7 — 教學 | `less education/lessons/01_pandas_basics.md` |

---

## 專案結構

## 原始資料 (raw/)

| 檔案 | 說明 |
|------|------|
| `raw/laps.csv` | 圈速、分段、輪胎、位置、刪除圈 |
| `raw/results.csv` | 最終排名、積分、起跑位、車隊資訊 |
| `raw/weather.csv` | 氣溫、賽道溫度、濕度、降雨、風速 |
| `raw/stints.csv` | 輪胎策略與 stint 長度 |
| `raw/race_control.csv` | 安全車、黃旗、紅旗、訊息 |
| `raw/telemetry_VER.csv` | VER 單圈遙測 (Speed, Throttle, Brake, RPM...) |
| `raw/schedule_2024.csv` | 賽程資訊 |
| `.gitignore` | 排除 venv / __pycache__ / outputs/ |

## 專案結構

```
data/
├── README.md                   ← 你現在正在看這個
├── ROADMAP_PRODUCTS_2_7.md     ← 產品 2-7 的實作路線圖
├── raw/                        ← Monza 2024 原始 CSV
├── outputs/
│   ├── prediction/             ← 產品 2 預測產出
│   ├── reports/                ← 產品 3 報告產出
│   ├── rating/                 ← 產品 4 評分產出
│   ├── coaching/               ← 產品 5 教練產出
│   └── bot/                    ← 產品 6 Bot 產出
├── src/
│   ├── data_loader.py          ← 資料載入層
│   ├── lap_analysis.py         ← 圈速分析
│   ├── tyre_analysis.py        ← 輪胎分析
│   ├── weather_analysis.py     ← 天氣分析
│   ├── race_analysis.py        ← 賽事分析
│   ├── telemetry_analysis.py   ← 遙測分析
│   ├── dashboard.py            ← 產品 1 - Streamlit 儀表板
│   ├── prediction/             ← 產品 2 - 賽事預測 (baseline)
│   ├── reports/                ← 產品 3 - 自動賽事分析報告
│   ├── rating/                 ← 產品 4 - 車手評分系統
│   ├── coaching.py             ← 產品 5 - Sim Racing 教練
│   └── bot/                    ← 產品 6 - 社群互動 Bot
└── education/
    └── lessons/                ← 產品 7 - 教學課程 (5 章)
```

## 產品一覽

### 產品 1 — Streamlit 互動儀表板

一鍵啟動的 Web 儀表板，整合所有產品的視覺化介面。

```bash
cd /home/thumb/data
source .venv/bin/activate
streamlit run src/dashboard.py
```

包含頁面：比賽總覽、圈速分析、輪胎策略、遙測數據、排名變化、天氣、預測模型、車手評分、教練工具、自動報告、Bot 指令輸出、教學內容。

---

### 產品 2 — 賽事預測 Baseline

基於規則的可解釋預測 baseline，針對 Monza 2024 輸出三個維度：

- 最終名次分級 (Top 3 / Top 10 / DNF)
- 起跑得失位 (Grid vs Finish)
- 一停 / 二停策略分類

```bash
# CLI
python -m src.prediction --output-dir outputs/prediction

# Python
from src.prediction.generator import generate_prediction_artifacts
paths = generate_prediction_artifacts()
```

輸出：`outputs/prediction/monza_2024_predictions.csv` + `.md`

---

### 產品 3 — 自動賽事分析報告

一鍵產出包含圖表的 Markdown/HTML 賽事報告，涵蓋排名、圈速、輪胎、天氣、遙測摘要。

```bash
# CLI
python -m src.reports.report_builder

# Python
from src.reports import generate_race_report
paths = generate_race_report(output_dir="outputs/reports")
```

輸出：`outputs/reports/2024_italian_gp.md` + `.html`

---

### 產品 4 — 車手表現評分系統

基於五個維度的加權評分 (0-100)：速度、一致性、起跑得失、輪胎管理、賽中位置變化。

```bash
# Python
from src.rating import build_rating_leaderboard
lb = build_rating_leaderboard()  # 自動存到 outputs/rating/monza_2024.csv
print(lb[['rank','driver','overall_score','pace_score']].head(10))

# 查單一車手
from src.rating import get_driver_rating
print(get_driver_rating('VER'))
```

輸出：`outputs/rating/monza_2024.csv`

---

### 產品 5 — Sim Racing 教練工具

以 VER 的實際遙測當 benchmark，比較使用者遙測，自動分析：

- 煞車點早晚比較
- 油門回補時機
- 20 段速度曲線摘要

```bash
# CLI
python src/coaching.py raw/telemetry_VER.csv --output-dir outputs/coaching

# 用自己的遙測 CSV
python src/coaching.py 你的遙測.csv

# Python
from src.coaching import compare_telemetry
result = compare_telemetry(user_csv="你的遙測.csv")
```

輸出：`outputs/coaching/coaching_report.json` + `.txt`

---

### 產品 6 — 社群互動 Bot (CLI Demo)

支援 6 個指令 (standings / strategy / compare / weather / telemetry / laps)，產出 txt + markdown + json。

```bash
# 全部指令
python -m src.bot.demo --output-dir outputs/bot

# 指定指令
python -m src.bot.demo --commands standings weather --output-dir outputs/bot
```

輸出：`outputs/bot/{指令}.txt|.md|.json`

---

### 產品 7 — 數據科學教學平台

5 章中文 F1 數據科學課程，每章含可執行程式碼範例。

```
education/lessons/
├── 01_pandas_basics.md    — Pandas 基礎：讀取與整理 laps.csv
├── 02_visualization.md    — 視覺化：圈速、輪胎、天氣圖
├── 03_statistics.md       — 統計：一致性、衰退率、相關性
├── 04_f1_features.md      — 進階分析：得失位、策略分析
└── 05_ml_baseline.md      — 機器學習導論：baseline 預測模型
```

```bash
less education/lessons/01_pandas_basics.md
```

## 一次性 Smoke Test

確認所有產品都能正常運作：

```bash
cd /home/thumb/data
source .venv/bin/activate
python3 -m compileall src && \
python3 -m src.prediction --output-dir /tmp/st/prediction && \
python3 -c "from src.reports import build_race_report; r=build_race_report(); print('Report OK:', len(r), 'sections')" && \
python3 -c "from src.rating import build_rating_leaderboard; lb=build_rating_leaderboard(); print('Rating OK:', len(lb), 'drivers')" && \
python3 src/coaching.py raw/telemetry_VER.csv --output-dir /tmp/st/coaching && \
python3 -m src.bot.demo --output-dir /tmp/st/bot --commands standings weather && \
echo "=== All smoke tests passed ==="
```

## 環境需求

- Python 3.10+
- pip install streamlit plotly pandas numpy

無其他外部依賴。