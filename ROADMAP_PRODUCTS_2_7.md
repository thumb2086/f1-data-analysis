# F1 專案產品 2-7 實作路線圖

## 目標
在不破壞既有 Product 1（Streamlit 儀表板 / `src/dashboard.py`）的前提下，逐步把現有 Monza 2024 原始資料，轉成可交付的產品 2-7。

## 目前可用資料與限制

### 可直接使用的原始資料
- `raw/laps.csv`：圈速、分段、輪胎、位置、刪除圈等核心資料
- `raw/results.csv`：最終排名、積分、起跑位、車隊資訊
- `raw/weather.csv`：氣溫、賽道溫度、濕度、降雨、風速
- `raw/stints.csv`：輪胎策略與 stint 長度
- `raw/race_control.csv`：安全車、黃旗、紅旗、訊息
- `raw/telemetry_VER.csv`：VER 單圈遙測資料
- `raw/schedule_2024.csv`：賽程資訊

### 現階段限制
- 目前資料明顯偏向「單站賽事」（Monza 2024）
- 遙測只有 VER 一位車手
- 尚未建立跨站歷史資料集，所以真正的預測模型與通用評分系統只能先做 MVP / baseline

## 不影響 Product 1 的 staging 原則

### Freeze 範圍
- `src/dashboard.py` 先視為已驗收主產品，避免重構其現有流程與頁面邏輯
- `src/data_loader.py` 只做向後相容的擴充，不改原函數輸出欄位語意
- 既有分析模組維持 read-only 使用方式

### 建議新增，不建議直接改動的範圍
- 新增 `src/features/`：特徵萃取與資料規格化
- 新增 `src/services/`：給 Bot、報告、API 共用的封裝層
- 新增 `src/reports/`：報告模板與輸出器
- 新增 `src/bot/`：聊天機器人指令層
- 新增 `src/rating/`、`src/prediction/`、`src/education/`：各產品專屬邏輯

### 安全做法
- 任何新功能都先透過新模組呼叫現有 `load_*` 與 `get_*` 函數
- Product 1 的圖表與頁面不共用 mutable 狀態
- 若要抽共用函數，先加新 helper，再逐步替換，不做大規模搬家

## 產品 2：賽事預測 AI 模型

### 可行定位
先做「單站預測 MVP」，不要一開始就承諾跨賽季泛化。

### 第一階段可交付
- 建立 baseline 模型資料表
- 先做三個最容易落地的目標：
  1. 最終名次分級預測（前 3 / 前 10 / 退賽）
  2. 起跑得失位預測（Grid vs Finish）
  3. 一停 / 二停策略分類
- 先用規則 + 傳統機器學習（logistic regression / random forest）做 baseline

### 立即可用特徵
- `results.csv`：GridPosition、Points、Status、Laps
- `laps.csv`：平均圈速、最快圈、CV、一致性、stint 數
- `stints.csv`：stint 數、每段長度、胎種組合
- `weather.csv`：是否降雨、平均賽道溫度、風速
- `race_control.csv`：Safety Car / Yellow Flag 次數

### 建議產出檔案
- `src/prediction/features.py`
- `src/prediction/train.py`
- `src/prediction/infer.py`
- `src/prediction/model_registry/`
- `notebooks/product2_baseline.ipynb`

### MVP 驗收標準
- 能輸入單站資料，輸出基本預測結果與信心分數
- 至少提供可解釋特徵重要度
- 清楚標示「目前僅 Monza / 單站 baseline」

### 第二階段
- 累積多站歷史資料後，再升級成真正的賽季模型
- 引入 XGBoost / LightGBM
- 再考慮更進階的 time-series 特徵

## 產品 3：自動化賽事分析報告

### 可行定位
這是現階段最容易交付的產品之一，因為分析函數已經存在。

### 第一階段可交付
- 每場比賽自動產生一份 Markdown / HTML 報告
- 報告包含：
  - 比賽總覽
  - 最終排名
  - 得失位排行
  - 最快圈與一致性
  - 輪胎策略時間軸
  - 天氣變化
  - 遙測重點摘要（以 VER 為例）

### 建議產出檔案
- `src/reports/report_builder.py`
- `src/reports/templates/monza_2024.md.j2`
- `src/reports/render.py`
- `outputs/reports/2024_italian_gp.md`
- `outputs/reports/2024_italian_gp.html`

### 可直接沿用的現有模組
- `src/lap_analysis.py`
- `src/tyre_analysis.py`
- `src/weather_analysis.py`
- `src/race_analysis.py`
- `src/telemetry_analysis.py`

### MVP 驗收標準
- 一鍵輸出報告
- 報告內圖表與表格都能自動生成
- 不需要手動 copy/paste

### 第二階段
- 新增摘要文案模板
- 新增社群版短摘要與完整版長報告
- 加入自動排程

## 產品 4：車手表現評分系統

### 可行定位
現有資料足夠做「單場評分」，但不建議先做全賽季通用 rating。

### 第一階段評分維度
- 單圈速度：最快圈、相對隊友差距
- 穩定性：CV / 圈速標準差
- 起跑表現：GridPosition vs Position
- 輪胎管理：同胎種下的衰退率
- 抗壓表現：後段圈速變化
- 進步幅度：得失位

### 建議產出檔案
- `src/rating/scoring.py`
- `src/rating/features.py`
- `src/rating/weights.yaml`
- `src/rating/leaderboard.py`
- `outputs/rating/monza_2024.csv`

### 建議做法
- 先用可解釋的加權分數，不要一開始上黑盒模型
- 分數拆成 0-100，並附上各子分項
- 先支持「單場 / 單站」排名，再做賽季累積

### MVP 驗收標準
- 每位車手可輸出總分與分項
- 分數能對應資料來源，不是純主觀
- 報表可直接供 Product 3 使用

### 第二階段
- 累積多站之後，加入賽季標準化
- 依賽道特性與隊友表現做校正

## 產品 5：Sim Racing 教練工具

### 可行定位
現階段只能先做「真實車手 benchmark 教練」，不做完整玩家上傳系統。

### 第一階段可交付
- 以 `telemetry_VER.csv` 作為標竿圈
- 提供三個核心功能：
  1. 速度曲線對比
  2. 煞車點差異偵測
  3. 油門補開時機建議

### 建議產出檔案
- `src/coaching/benchmark.py`
- `src/coaching/comparison.py`
- `src/coaching/advice.py`
- `src/coaching/export.py`
- `outputs/coaching/ver_benchmark.json`

### MVP 驗收標準
- 輸入玩家遙測 CSV 後，可對齊 Distance 軸做比較
- 能指出「早煞 / 晚煞 / 提早補油 / 過晚補油」
- 至少支援一種常見模擬器格式

### 第二階段
- 加入更多真實車手 telemetry
- 增加賽道自動辨識與圈段切分
- 提供教練建議分級

## 產品 6：社群互動 Bot

### 可行定位
這是高 CP 值產品，因為可以直接包裝現有函數。

### 第一階段可交付
- Discord Bot 先行，Telegram 可作第二階段
- 支援固定指令：
  - `/standings`
  - `/strategy`
  - `/compare VER NOR`
  - `/weather`
  - `/telemetry VER`
  - `/laps LEC`

### 建議產出檔案
- `src/bot/app.py`
- `src/bot/commands.py`
- `src/bot/renderers.py`
- `src/bot/config.py`
- `src/services/query_service.py`
- `outputs/bot/cache/`

### 設計原則
- Bot 只做呼叫與輸出格式化
- 分析邏輯留在現有模組與共用 service
- 圖表可先輸出 PNG / HTML，再丟給 bot 回傳

### MVP 驗收標準
- 指令可回傳文字摘要 + 圖表
- 同一套查詢邏輯可被報告與 Bot 共用
- 不需要人工查資料

### 第二階段
- 加入使用者參數、比賽選擇、快取
- 支援多場賽事查詢

## 產品 7：F1 數據科學教學平台

### 可行定位
這是內容型產品，最適合在前面產品穩定後做；不依賴大量新資料，但依賴良好教材整理。

### 第一階段可交付
- 以 Notebook / Markdown 課程形式輸出
- 先做 5 個模組：
  1. Pandas 基礎：讀取與整理 `laps.csv`
  2. 視覺化：圈速、輪胎、天氣圖
  3. 統計：一致性、衰退率、相關性
  4. 進階分析：得失位、策略分析
  5. 機器學習導論：baseline 預測模型

### 建議產出檔案
- `education/lessons/01_pandas_basics.md`
- `education/lessons/02_visualization.md`
- `education/lessons/03_statistics.md`
- `education/lessons/04_f1_features.md`
- `education/lessons/05_ml_baseline.md`
- `notebooks/education/*.ipynb`

### MVP 驗收標準
- 每個章節都有可執行程式碼
- 每節都用現有 F1 資料做例子
- 能獨立成為中文教學內容

### 第二階段
- 製作影片腳本與練習題
- 加入資料工程與 API 章節
- 擴充成完整課程

## 建議開發順序

### Phase 1：先把最容易交付的做完
1. Product 3 自動報告
2. Product 6 Bot
3. Product 4 評分系統 MVP

### Phase 2：補上可展示性與差異化
4. Product 5 Sim Racing 教練 MVP
5. Product 7 教學平台 MVP

### Phase 3：最後再做資料依賴較重者
6. Product 2 預測模型 baseline

## 建議的工程切分

### 基礎層
- `src/data_loader.py`：資料載入
- `src/*_analysis.py`：現有分析邏輯

### 共用層
- `src/services/`：統一查詢、格式化、圖表輸出
- `src/features/`：特徵工程

### 產品層
- `src/reports/`：Product 3
- `src/rating/`：Product 4
- `src/coaching/`：Product 5
- `src/bot/`：Product 6
- `education/`：Product 7
- `src/prediction/`：Product 2

## 最小可行交付標準

如果要在現有資料條件下「盡快完成 2-7」，建議的最小交付是：
- 產品 2：單站 baseline 預測，不宣稱跨站泛化
- 產品 3：自動報告生成器
- 產品 4：單場車手評分卡
- 產品 5：VER benchmark 教練工具
- 產品 6：Discord Bot 指令集
- 產品 7：中文教學課程 5 章

這樣可以最大化沿用現有資料與程式結構，同時讓 Product 1 保持穩定可用。
