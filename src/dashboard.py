"""F1 Monza 2024 整合儀表板 - 產品 1~7 全功能入口
"""
from __future__ import annotations

import io
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.data_loader import (
    get_race_info, load_laps, load_results, load_weather, load_stints, load_telemetry,
)
from src.lap_analysis import (
    get_all_drivers_consistency, get_driver_lap_times, get_fastest_laps,
    get_lap_time_evolution,
)
from src.tyre_analysis import (
    get_compound_comparison, get_tyre_degradation, get_tyre_strategy,
)
from src.telemetry_analysis import (
    get_gear_time_distribution, get_minisector_speed, get_speed_profile,
    get_throttle_brake_analysis,
)
from src.race_analysis import (
    get_final_standings, get_position_change_summary, get_position_evolution,
    get_team_standings,
)
from src.weather_analysis import get_weather_summary, get_weather_timeline

# ── 產品 2~7 模組 ──────────────────────────────────────────
from src.coaching import compare_telemetry
from src.prediction.generator import generate_prediction_artifacts, load_prediction_table
from src.rating import build_rating_leaderboard, get_driver_rating
from src.reports import build_race_report, generate_race_report

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "raw"
EDUCATION_DIR = PROJECT_ROOT / "education" / "lessons"


st.set_page_config(page_title="F1 Monza 2024 整合儀表板", layout="wide", page_icon="🏎️")


# ── Helpers ──────────────────────────────────────────────────

def _format_prediction_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.select_dtypes(include="float").columns:
        out[col] = out[col].round(3)
    return out


def _display_rating_metrics(row):
    cols = st.columns(5)
    cols[0].metric("🏁 總分", f"{row['overall_score']:.1f}")
    cols[1].metric("⚡ 速度", f"{row['pace_score']:.1f}")
    cols[2].metric("🎯 一致性", f"{row['consistency_score']:.1f}")
    cols[3].metric("📈 起跑得失", f"{row['start_finish_gain_score']:.1f}")
    cols[4].metric("🏜 輪胎管理", f"{row['tyre_management_score']:.1f}")


def _read_lesson(path: Path) -> str | None:
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


# ── Cached data ─────────────────────────────────────────────

@st.cache_data
def _load_all_data():
    return {
        "race_info": get_race_info(),
        "results": load_results(),
        "laps": load_laps(),
        "stints": load_stints(),
        "weather": load_weather(),
        "team_standings": get_team_standings(),
        "fastest_laps": get_fastest_laps(),
        "consistency": get_all_drivers_consistency(),
        "position_changes": get_position_change_summary(),
        "weather_summary": get_weather_summary(),
    }


@st.cache_data
def _get_rating_lb():
    return build_rating_leaderboard(save=False)


@st.cache_data
def _get_prediction_df():
    p = generate_prediction_artifacts(save=False, accurate_only=True)
    return load_prediction_table(p["csv"])


@st.cache_data
def _get_race_report():
    return build_race_report()


DATA = _load_all_data()

# ── Sidebar ──────────────────────────────────────────────────

st.sidebar.title("🏎️ F1 Monza 2024")
page = st.sidebar.radio(
    "選擇頁面",
    [
        "比賽總覽",
        "圈速分析",
        "輪胎策略",
        "遙測數據 (VER)",
        "排名變化",
        "天氣",
        "🔮 預測模型",       # 產品 2
        "⭐ 車手評分",       # 產品 4
        "🎯 教練工具",       # 產品 5
        "📄 自動報告",       # 產品 3
        "🤖 Bot 指令",       # 產品 6
        "📖 教學內容",       # 產品 7
    ],
)

if page == "比賽總覽":
    st.header("🏁 比賽總覽")
    st.subheader("2024 意大利大獎賽 @ Monza")

    info = DATA['race_info']
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🏆 冠軍", info['winner'])
    col2.metric("天氣", "乾燥" if not info['weather']['rain'] else "降雨")
    col3.metric("總圈數", f"{info['total_laps']} 圈")
    col4.metric("參賽車手", f"{info['drivers']} 位")

    st.divider()

    st.subheader("最終排名")
    results_df = DATA['results'][['Position', 'Abbreviation', 'FullName', 'TeamName', 'Points', 'GridPosition']].copy()
    results_df['Position'] = results_df['Position'].astype(int)
    st.dataframe(results_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("車隊積分")
    team_df = DATA['team_standings'].copy()
    fig = px.bar(
        team_df, x='TeamName', y='total_points',
        color='TeamName', color_discrete_map=dict(zip(team_df['TeamName'], ['#' + c for c in team_df['color']])),
        title="車隊總積分",
        labels={'TeamName': '車隊', 'total_points': '積分'}
    )
    fig.update_layout(showlegend=False, xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


elif page == "圈速分析":
    st.header("⏱️ 圈速分析")

    drivers = DATA['results']['Abbreviation'].tolist()
    default_drivers = ['LEC', 'PIA', 'NOR']
    selected_drivers = st.multiselect("選擇車手", drivers, default=default_drivers)

    if selected_drivers:
        st.subheader("圈速演進")
        laps_df = get_lap_time_evolution(selected_drivers)
        fig = px.line(
            laps_df, x='LapNumber', y='LapTime_seconds', color='Driver',
            title="圈速 vs 圈數",
            labels={'LapNumber': '圈數', 'LapTime_seconds': '圈速 (秒)'}
        )
        fig.update_traces(mode='lines+markers', marker=dict(size=4))
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

        st.divider()

        st.subheader("最快圈速")
        fastest = DATA['fastest_laps'][DATA['fastest_laps']['Driver'].isin(selected_drivers)][
            ['Driver', 'Team', 'LapTime_seconds', 'LapNumber', 'Compound', 'TyreLife']
        ].copy()
        fastest['LapTime_seconds'] = fastest['LapTime_seconds'].round(3)
        st.dataframe(fastest, use_container_width=True, hide_index=True)

        st.divider()

        st.subheader("圈速一致性排名 (CV 越低越好)")
        cons = DATA['consistency'].copy()
        cons = cons[cons['Driver'].isin(selected_drivers)]
        cons = cons.sort_values('cv')[['Driver', 'team', 'avg_laptime', 'cv', 'lap_count']]
        cons['avg_laptime'] = cons['avg_laptime'].round(3)
        cons['cv'] = cons['cv'].round(2)
        st.dataframe(cons, use_container_width=True, hide_index=True)


elif page == "輪胎策略":
    st.header(" Tire 輪胎策略")

    st.subheader("策略摘要")
    strategy = get_tyre_strategy()
    strat_display = strategy[['driver', 'strategy', 'n_stops', 'total_laps']].copy()
    strat_display.columns = ['車手', '策略', '進站次數', '總圈數']
    st.dataframe(strat_display, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("輪胎使用時間軸")
    stints = load_stints()
    results_df = DATA['results']

    drv_map = dict(zip(results_df['DriverNumber'], results_df['Abbreviation']))
    stints['driver'] = stints['driver_number'].map(drv_map)
    stints['compound'] = stints['compound'].astype(str)

    compound_colors = {'SOFT': '#FF3333', 'MEDIUM': '#FFD700', 'HARD': '#CCCCCC',
                       'INTERMEDIATE': '#00FF00', 'WET': '#0000FF'}

    # 按最終排名排序
    position_map = dict(zip(results_df['Abbreviation'], results_df['Position']))
    driver_order = sorted(stints['driver'].unique(), key=lambda d: position_map.get(d, 99))

    max_lap = int(stints['lap_end'].max())

    fig = go.Figure()

    for i, driver in enumerate(driver_order):
        driver_stints = stints[stints['driver'] == driver].sort_values('lap_start')
        for _, stint in driver_stints.iterrows():
            start = int(stint['lap_start'])
            end = int(stint['lap_end'])
            comp = stint['compound']
            color = compound_colors.get(comp, '#888888')
            fig.add_trace(go.Bar(
                y=[driver],
                x=[end - start],
                base=start,
                orientation='h',
                marker=dict(color=color, line=dict(color='white', width=1)),
                name=comp,
                legendgroup=comp,
                showlegend=i == 0,
                width=0.7,
                text=comp if (end - start) >= 5 else '',
                textposition='inside',
                insidetextfont=dict(size=13, color='black', family='Arial Black'),
                hovertemplate=f"{driver}<br>{comp}<br>Lap {start}-{end}<br>{end-start+1} laps<extra></extra>",
            ))

    # 圈數格線
    for lap in range(0, max_lap + 1, 5):
        fig.add_vline(x=lap, line_width=0.5, line_color='rgba(255,255,255,0.15)')

    fig.update_layout(
        title="輪胎使用時間軸 (Hover 看詳細)",
        xaxis_title="圈數",
        xaxis=dict(
            dtick=5,
            range=[-1, max_lap + 3],
            gridcolor='rgba(255,255,255,0.1)',
        ),
        yaxis=dict(autorange='reversed', title=None),
        barmode='stack',
        height=650,
        hovermode='closest',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=10, r=20, t=40, b=40),
        legend=dict(title='輪胎', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("輪胎衰退率")
    deg = get_tyre_degradation()
    if len(deg) > 0:
        # 過濾：只保留衰退率>0（排除安全車/交通/策略變化的干擾）
        # 以及 R²≥0.05（些微線性趨勢即可），樣本≥8 圈
        deg_clean = deg[(deg['degradation_rate'] > 0) & (deg['laps_analyzed'] >= 8)].copy()
        # 如果有 R² 高一點的資料更好，但不要過濾到沒東西
        if len(deg_clean) < 5:
            deg_clean = deg[(deg['degradation_rate'] > 0) & (deg['laps_analyzed'] >= 5)].copy()
        # 標記可信度
        deg_clean['confidence'] = deg_clean['r2'].apply(lambda x: '高' if x >= 0.3 else ('中' if x >= 0.1 else '低'))

        deg_display = deg_clean[['driver', 'compound', 'degradation_rate', 'r2', 'laps_analyzed']].head(20).copy()
        deg_display.columns = ['車手', '輪胎', '衰退率(秒/圈)', 'R²', '分析圈數']
        deg_display['衰退率(秒/圈)'] = deg_display['衰退率(秒/圈)'].round(4)
        deg_display['R²'] = deg_display['R²'].round(3)
        st.dataframe(deg_display, use_container_width=True, hide_index=True)

        if len(deg_clean) > 0:
            # 長條圖：每位車手一條 bar，按衰退率降冪排序，顏色 = 胎種
            top_deg = deg_clean.sort_values('degradation_rate', ascending=False).head(20)
            # 加上明暗表示可信度（用 opacity 或 pattern）
            fig = px.bar(
                top_deg,
                x='driver', y='degradation_rate',
                color='compound',
                pattern_shape='confidence',
                barmode='group',
                title="輪胎衰退率分析 — 每位車手每圈衰退(秒)",
                labels={'driver': '車手', 'degradation_rate': '衰退率 (秒/圈)', 'compound': '胎種'},
                hover_data={'r2': ':.3f', 'laps_analyzed': True, 'confidence': True},
                text='degradation_rate',
            )
            fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
            fig.update_layout(
                height=450,
                margin=dict(l=10, r=20, t=40, b=100),
                xaxis_tickangle=-45,
            )
            st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Compound 比較")
    compound_comp = get_compound_comparison()
    compound_stats = compound_comp.groupby('Compound').agg(
        avg_time=('avg_laptime', 'mean'),
        min_time=('min_laptime', 'min'),
        laps=('laps', 'sum')
    ).reset_index()
    fig = px.box(
        compound_comp, x='Compound', y='avg_laptime', color='Compound',
        title="不同 Compound 圈速分佈",
        labels={'avg_laptime': '平均圈速 (秒)'}
    )
    st.plotly_chart(fig, use_container_width=True)


elif page == "遙測數據 (VER)":
    st.header("📊 遙測數據 - VER")

    st.subheader("速度曲線")
    speed_data = get_speed_profile('VER')
    
    # 方法 A：一條連續速度線 + 檔位著色分段
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=speed_data['Distance'], y=speed_data['Speed'],
        mode='lines',
        line=dict(color='#00BFFF', width=2),
        name='速度',
        hovertemplate='距離 %{x:.0f}m<br>速度 %{y:.0f} km/h<extra></extra>'
    ))
    # 疊加檔位標記（取樣避免太密）
    sample = speed_data.iloc[::20]  # 每 20 點取一個標記
    fig.add_trace(go.Scatter(
        x=sample['Distance'], y=sample['Speed'],
        mode='markers+text',
        marker=dict(
            color=sample['nGear'], colorscale='Viridis',
            size=6, showscale=True, colorbar=dict(title='檔位'),
        ),
        text=sample['nGear'].astype(int),
        textposition='top center',
        textfont=dict(size=9, color='white'),
        name='檔位',
        hovertemplate='距離 %{x:.0f}m<br>速度 %{y:.0f} km/h<br>Gear %{text}<extra></extra>',
    ))
    fig.update_layout(
        title="速度 vs 距離（顏色 = 檔位）",
        xaxis_title="距離 (m)", yaxis_title="速度 (km/h)",
        hovermode='closest',
    )
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    tb_analysis = get_throttle_brake_analysis('VER')

    c1, c2, c3 = st.columns(3)
    c1.metric("全油門比例", f"{tb_analysis['full_throttle_pct']:.1f}%")
    c2.metric("煞車比例", f"{tb_analysis['braking_pct']:.1f}%")
    c3.metric("滑行比例", f"{tb_analysis['coasting_pct']:.1f}%")

    st.subheader("油門/煞車使用")
    tb_df = pd.DataFrame({
        '類型': ['全油門 (≥95%)', '煞車', '滑行'],
        '比例': [tb_analysis['full_throttle_pct'], tb_analysis['braking_pct'], tb_analysis['coasting_pct']]
    })
    fig = px.bar(tb_df, x='類型', y='比例', color='類型', title="油門/煞車使用比例")
    fig.update_layout(yaxis_title="百分比 (%)")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("檔位使用分佈")
    gear_dist = get_gear_time_distribution('VER')
    gear_df = pd.DataFrame([
        {'檔位': f"Gear {k}", '圈數': v['count'], '比例': v['pct']}
        for k, v in gear_dist['gear_distribution'].items()
    ])
    fig = px.pie(gear_df, values='圈數', names='檔位', title="檔位使用分佈")
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("小區段速度")
    minisector = get_minisector_speed('VER', n_sectors=20)
    fig = px.bar(
        minisector, x='sector_name', y='avg_speed',
        title="各區段平均速度",
        labels={'sector_name': '區段', 'avg_speed': '平均速度 (km/h)'}
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)


elif page == "排名變化":
    st.header("📈 排名變化")

    drivers = DATA['results']['Abbreviation'].tolist()
    selected = st.multiselect("選擇車手", drivers, default=['LEC', 'PIA', 'NOR', 'VER', 'HAM'])

    st.subheader("每圈排名")
    if selected:
        pos_evo = get_position_evolution(selected)
        fig = px.line(
            pos_evo, x='LapNumber', y='Position', color='Driver',
            title="每圈排名變化",
            labels={'LapNumber': '圈數', 'Position': '排名'}
        )
        fig.update_traces(mode='lines+markers', marker=dict(size=3))
        fig.update_layout(yaxis=dict(autorange='reversed'))
        fig.update_layout(hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("得失位排行榜")
    pos_change = DATA['position_changes'].copy()
    pos_change['position_change'] = pos_change['position_change'].astype(int)
    display_cols = ['Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'Position', 'position_change']
    pos_change_display = pos_change[display_cols].copy()
    pos_change_display.columns = ['縮寫', '車手', '車隊', '起跑位', '最終位', '得失位']
    st.dataframe(pos_change_display, use_container_width=True, hide_index=True)

    gained = pos_change[pos_change['position_change'] > 0].head(5)
    lost = pos_change[pos_change['position_change'] < 0].head(5)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🏆 最佳進步")
        st.dataframe(gained[['Abbreviation', 'position_change']].rename(columns={'Abbreviation': '車手', 'position_change': '前進位數'}), hide_index=True)
    with c2:
        st.subheader("📉 最大退步")
        st.dataframe(lost[['Abbreviation', 'position_change']].rename(columns={'Abbreviation': '車手', 'position_change': '退後位數'}), hide_index=True)


elif page == "天氣":
    st.header("🌤️ 天氣數據")

    ws = DATA['weather_summary']
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("氣溫", f"{ws['air_temp']['min']:.1f} ~ {ws['air_temp']['max']:.1f}°C")
    c2.metric("賽道溫度", f"{ws['track_temp']['min']:.1f} ~ {ws['track_temp']['max']:.1f}°C")
    c3.metric("濕度", f"{ws['humidity']['min']:.0f} ~ {ws['humidity']['max']:.0f}%")
    c4.metric("風速", f"{ws['wind_speed']['avg']:.1f} m/s")

    st.divider()

    weather_df = get_weather_timeline()
    weather_df['Time_min'] = weather_df['Time_minutes'].round(1)

    st.subheader("氣溫與賽道溫度")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=weather_df['Time_min'], y=weather_df['AirTemp'], name='氣溫', line=dict(color='orange')))
    fig.add_trace(go.Scatter(x=weather_df['Time_min'], y=weather_df['TrackTemp'], name='賽道溫度', line=dict(color='red')))
    fig.update_layout(title="氣溫 vs 賽道溫度", xaxis_title="時間 (分鐘)", yaxis_title="溫度 (°C)", hovermode='x unified')
    st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("濕度")
    fig = px.line(weather_df, x='Time_min', y='Humidity', title="濕度變化", labels={'Time_min': '時間 (分鐘)', 'Humidity': '濕度 (%)'})
    fig.update_traces(line_color='blue')
    st.plotly_chart(fig, use_container_width=True)

    st.divider()


# ═══════════════════════════════════════════════════════════
# 產品 2 — 預測模型
# ═══════════════════════════════════════════════════════════

elif page == "🔮 預測模型":
    st.header("🔮 賽事預測 Baseline")
    st.caption("基於規則的可解釋預測模型 (Monza 2024 單站 baseline)")

    with st.spinner("載入預測資料..."):
        try:
            pred_df = _get_prediction_df()
        except Exception:
            generate_prediction_artifacts()
            pred_df = _get_prediction_df()

    st.subheader("車手預測結果")
    display_cols = [c for c in ["rank", "driver", "full_name", "team_name",
                                 "predicted_result_class", "predicted_gain_band",
                                 "predicted_strategy", "confidence"]
                    if c in pred_df.columns]
    st.dataframe(
        _format_prediction_df(pred_df[display_cols]),
        use_container_width=True, hide_index=True,
    )

    if "predicted_result_class" in pred_df.columns:
        st.divider()
        st.subheader("結果分類分佈")
        col1, col2, col3 = st.columns(3)
        col1.metric("🏆 Top 3", int((pred_df["predicted_result_class"] == "Top 3").sum()))
        col2.metric("📋 Top 10", int((pred_df["predicted_result_class"] == "Top 10").sum()))
        col3.metric("❌ DNF", int((pred_df["predicted_result_class"] == "DNF").sum()))

        fig = px.pie(
            pred_df, names="predicted_result_class",
            title="預測結果類別比例",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("📥 下載原始資料"):
        csv_bytes = pred_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "下載 predictions.csv",
            data=csv_bytes, file_name="monza_2024_predictions.csv",
            mime="text/csv",
        )

    st.info("⚠️ 目前為單站 baseline，僅供參考。跨賽季模型需累積多站資料。")


# ═══════════════════════════════════════════════════════════
# 產品 4 — 車手評分
# ═══════════════════════════════════════════════════════════

elif page == "⭐ 車手評分":
    st.header("⭐ 車手表現評分 (Monza 2024)")
    st.caption("五維度加權評分：速度 30% · 一致性 20% · 起跑得失 20% · 輪胎管理 15% · 賽中位置 15%")

    with st.spinner("計算評分..."):
        lb_df = _get_rating_lb()

    tab1, tab2 = st.tabs(["🏆 Leaderboard", "🔍 查詢車手"])

    with tab1:
        cols_display = [c for c in [
            "rank", "driver", "full_name", "team_name", "overall_score",
            "pace_score", "consistency_score", "start_finish_gain_score",
            "tyre_management_score", "position_gain_loss_score",
        ] if c in lb_df.columns]
        st.dataframe(
            _format_prediction_df(lb_df[cols_display]),
            use_container_width=True, hide_index=True,
        )

        st.divider()
        st.subheader("總分 Top 10")
        top10 = lb_df.head(10)
        fig = px.bar(
            top10, x="driver", y="overall_score",
            color="team_name",
            title="車手總分排行",
            labels={"driver": "車手", "overall_score": "總分", "team_name": "車隊"},
            text_auto=".1f",
        )
        fig.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        driver_list = sorted(lb_df["driver"].unique().tolist())
        sel = st.selectbox("選擇車手", driver_list)
        row = lb_df[lb_df["driver"] == sel]
        if not row.empty:
            r = row.iloc[0]
            _display_rating_metrics(r)
            st.dataframe(
                _format_prediction_df(row),
                use_container_width=True, hide_index=True,
            )

    with st.expander("📥 下載評分資料"):
        csv_bytes = lb_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "下載 rating.csv",
            data=csv_bytes, file_name="monza_2024_ratings.csv",
            mime="text/csv",
        )


# ═══════════════════════════════════════════════════════════
# 產品 5 — 教練工具
# ═══════════════════════════════════════════════════════════

elif page == "🎯 教練工具":
    st.header("🎯 Sim Racing 教練工具")
    st.caption("以 VER 實際遙測為 benchmark，分析煞車點、油門時機與速度曲線")

    mode = st.radio("模式", ["使用預設 VER vs VER（基準測試）", "上傳自備遙測 CSV"], horizontal=True)

    user_csv = RAW_DIR / "telemetry_VER.csv"
    if mode == "上傳自備遙測 CSV":
        uploaded = st.file_uploader("上傳你的遙測 CSV (需要 Distance, Speed, Throttle, Brake 欄位)", type="csv")
        if uploaded is not None:
            tmp_path = PROJECT_ROOT / ".uploaded_telemetry.csv"
            tmp_path.write_bytes(uploaded.getvalue())
            user_csv = tmp_path
        else:
            st.info("請上傳 CSV 或切換回預設模式")

    if st.button("🚀 執行遙測比較", type="primary"):
        with st.spinner("比對中..."):
            try:
                result = compare_telemetry(user_csv=str(user_csv))
                events = result.get("events", [])
                feedback = result.get("feedback", [])

                st.success("比對完成！")

                c1, c2, c3 = st.columns(3)
                c1.metric("📏 重疊區間", f"{result['overlap_distance']['start_m']:.0f}~{result['overlap_distance']['end_m']:.0f}m")
                c2.metric("⚡ 平均速度差", f"{result['speed_delta']['mean_kph']:+.2f} km/h")
                c3.metric("🔄 配對煞車區", result["event_count"]["paired_zones"])

                if feedback:
                    st.subheader("📋 教練回饋")
                    for msg in feedback:
                        st.write(f"- {msg}")

                if events:
                    st.subheader("煞車 / 油門事件")
                    ev_df = pd.DataFrame(events)
                    ev_df = ev_df.round(2)
                    st.dataframe(ev_df, use_container_width=True, hide_index=True)

                segments = result.get("segment_summary", [])
                if segments:
                    st.subheader("區段速度摘要")
                    seg_df = pd.DataFrame(segments)
                    fig = px.line(
                        seg_df, x="distance_start", y=["avg_speed_ref", "avg_speed_user"],
                        labels={"value": "速度 (km/h)", "distance_start": "距離 (m)", "variable": "類型"},
                        title="Benchmark vs 使用者速度曲線",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                st.info(f"完整報告：{result['output_files']['json']}")

            except Exception as e:
                st.error(f"比較失敗：{e}")

    st.divider()
    st.subheader("📊 VER 基準遙測")
    speed_data = get_speed_profile("VER")
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=speed_data['Distance'], y=speed_data['Speed'],
        mode='lines',
        line=dict(color='#00BFFF', width=2),
        name='速度',
        hovertemplate='距離 %{x:.0f}m<br>速度 %{y:.0f} km/h<extra></extra>'
    ))
    sample = speed_data.iloc[::20]
    fig.add_trace(go.Scatter(
        x=sample['Distance'], y=sample['Speed'],
        mode='markers+text',
        marker=dict(
            color=sample['nGear'], colorscale='Viridis',
            size=6, showscale=True, colorbar=dict(title='檔位'),
        ),
        text=sample['nGear'].astype(int),
        textposition='top center',
        textfont=dict(size=9, color='white'),
        name='檔位',
        hovertemplate='距離 %{x:.0f}m<br>速度 %{y:.0f} km/h<br>Gear %{text}<extra></extra>',
    ))
    fig.update_layout(
        title="VER 速度曲線 (基準)",
        xaxis_title="距離 (m)", yaxis_title="速度 (km/h)",
        hovermode='closest',
    )
    st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# 產品 3 — 自動報告
# ═══════════════════════════════════════════════════════════

elif page == "📄 自動報告":
    st.header("📄 自動賽事分析報告")
    st.caption("一鍵生成 Monza 2024 完整賽事報告")

    col1, col2 = st.columns([1, 2])
    with col1:
        if st.button("📝 生成 Markdown 報告", type="primary", use_container_width=True):
            with st.spinner("正在生成報告..."):
                paths = generate_race_report(output_dir=str(PROJECT_ROOT / "outputs" / "reports"))
                st.success(f"報告已產出！")
                for k, v in paths.items():
                    st.write(f"- **{k}**: `{v}`")

    with col2:
        if st.button("🔄 重新計算 (記憶體)", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    st.divider()
    st.subheader("📋 報告預覽")

    with st.spinner("載入報告內容..."):
        report = _get_race_report()

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏁 排名", "📈 得失位", "⏱ 最快圈", " Tire 輪胎", "🌤 天氣"])

    with tab1:
        st.dataframe(report["standings"], use_container_width=True, hide_index=True)

    with tab2:
        st.dataframe(report["position_changes"], use_container_width=True, hide_index=True)
        if "position_change" in report["position_changes"].columns:
            fig = report["figures"]["position_change"]
            st.plotly_chart(fig, use_container_width=True)

    with tab3:
        st.dataframe(report["fastest_laps"], use_container_width=True, hide_index=True)
        fig = report["figures"]["fastest_laps"]
        st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.dataframe(report["tyre_strategy"], use_container_width=True, hide_index=True)
        fig = report["figures"]["tyre_strategy"]
        st.plotly_chart(fig, use_container_width=True)

    with tab5:
        ws = report["weather_summary"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("氣溫", f"{ws['air_temp']['min']:.1f} ~ {ws['air_temp']['max']:.1f}°C")
        c2.metric("賽道", f"{ws['track_temp']['min']:.1f} ~ {ws['track_temp']['max']:.1f}°C")
        c3.metric("濕度", f"{ws['humidity']['min']:.0f} ~ {ws['humidity']['max']:.0f}%")
        c4.metric("風速", f"{ws['wind_speed']['avg']:.1f} m/s")

    with st.expander("📥 下載報告"):
        if st.button("生成 HTML 報告"):
            paths = generate_race_report()
            for k, v in paths.items():
                st.write(f"- **{k}**: `{v}`")


# ═══════════════════════════════════════════════════════════
# 產品 6 — Bot 指令
# ═══════════════════════════════════════════════════════════

elif page == "🤖 Bot 指令":
    st.header("🤖 Bot 指令模擬")
    st.caption("點擊執行 Bot 指令，查看文字 + JSON 輸出")

    from src.bot.commands import BotCommandRunner
    from src.bot.services import BotService
    from src.bot.types import DEFAULT_BOT_OUTPUT_DIR, DEFAULT_COMPARE_BENCHMARK_CSV, DEFAULT_COMPARE_USER_CSV

    service = BotService(
        driver="VER",
        compare_user_csv=str(DEFAULT_COMPARE_USER_CSV),
        compare_benchmark_csv=str(DEFAULT_COMPARE_BENCHMARK_CSV),
        output_dir=str(DEFAULT_BOT_OUTPUT_DIR),
    )
    runner = BotCommandRunner(service)

    commands_available = [
        "standings", "strategy", "compare", "weather", "telemetry", "laps",
    ]

    selected_cmd = st.selectbox("選擇指令", commands_available)

    extra_driver = "VER"
    if selected_cmd in ("telemetry", "laps"):
        extra_driver = st.text_input("車手代碼", "VER")

    if st.button(f"🚀 執行 /{selected_cmd}", type="primary"):
        with st.spinner(f"執行 /{selected_cmd}..."):
            kwargs = {"driver": extra_driver}
            if selected_cmd == "compare":
                kwargs.update({
                    "user_csv": str(DEFAULT_COMPARE_USER_CSV),
                    "benchmark_csv": str(DEFAULT_COMPARE_BENCHMARK_CSV),
                })
            exec_result = runner.render(selected_cmd, **kwargs)

        tab_txt, tab_md, tab_json = st.tabs(["📝 文字", "📄 Markdown", "🔣 JSON"])

        with tab_txt:
            st.code(exec_result.text, language="text")

        with tab_md:
            st.markdown(exec_result.markdown)

        with tab_json:
            parsed = json.loads(exec_result.json_text)
            st.json(parsed)

    st.divider()
    st.subheader("Bot 輸出檔案")
    bot_files = sorted(DEFAULT_BOT_OUTPUT_DIR.glob("*"))
    if bot_files:
        for f in bot_files:
            st.write(f"- `{f.relative_to(PROJECT_ROOT)}`")
    else:
        st.info("尚未有輸出。可用 CLI `python -m src.bot.demo` 產生。")

    st.info("💡 Bot 指令實為 CLI demo，輸出純文字 + Markdown + JSON；可用作 Discord/Telegram Bot 的服務層呼叫。")


# ═══════════════════════════════════════════════════════════
# 產品 7 — 教學內容
# ═══════════════════════════════════════════════════════════

elif page == "📖 教學內容":
    st.header("📖 F1 數據科學教學平台")
    st.caption("5 章中文 F1 數據科學課程，直接在此閱讀")

    lesson_map = [
        ("01_pandas_basics.md", "📊 第 1 章 — Pandas 基礎：讀取與整理 laps.csv"),
        ("02_visualization.md", "📈 第 2 章 — 視覺化：圈速、輪胎、天氣圖"),
        ("03_statistics.md", "📉 第 3 章 — 統計：一致性、衰退率、相關性"),
        ("04_f1_features.md", "🔬 第 4 章 — 進階分析：得失位、策略分析"),
        ("05_ml_baseline.md", "🤖 第 5 章 — 機器學習導論：baseline 預測模型"),
    ]

    lesson_names = [label for _, label in lesson_map]
    lesson_files = {label: EDUCATION_DIR / fname for fname, label in lesson_map}

    selected_lesson = st.radio("選擇課程", lesson_names, horizontal=True)

    fpath = lesson_files[selected_lesson]
    content = _read_lesson(fpath)

    if content:
        st.markdown(content)
    else:
        st.warning(f"檔案 `{fpath}` 不存在或無法讀取")

    st.divider()
    st.info("每章皆有可執行的 Python 範例。建議在 Jupyter Notebook 或 VS Code 中實際操作。")