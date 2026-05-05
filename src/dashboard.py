"""
F1 意大利大獎賽 (Monza 2024) 數據儀表板
"""
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from src.data_loader import (
    load_laps, load_results, load_weather, load_stints, load_telemetry, get_race_info
)
from src.lap_analysis import (
    get_fastest_laps, get_driver_lap_times, get_lap_time_evolution,
    get_all_drivers_consistency
)
from src.tyre_analysis import (
    get_tyre_strategy, get_tyre_degradation, get_compound_comparison
)
from src.telemetry_analysis import (
    get_telemetry_data, get_speed_profile, get_throttle_brake_analysis,
    get_gear_time_distribution, get_minisector_speed
)
from src.race_analysis import (
    get_final_standings, get_position_change_summary, get_position_evolution,
    get_team_standings
)
from src.weather_analysis import get_weather_timeline, get_weather_summary


st.set_page_config(page_title="F1 Monza 2024 數據儀表板", layout="wide", page_icon="🏎️")

st.cache_data = st.cache_data


@st.cache_data
def load_all_data():
    return {
        'race_info': get_race_info(),
        'results': load_results(),
        'laps': load_laps(),
        'stints': load_stints(),
        'weather': load_weather(),
        'team_standings': get_team_standings(),
        'fastest_laps': get_fastest_laps(),
        'consistency': get_all_drivers_consistency(),
        'position_changes': get_position_change_summary(),
        'weather_summary': get_weather_summary(),
    }


DATA = load_all_data()

st.sidebar.title("🏎️ F1 Monza 2024")
page = st.sidebar.radio(
    "選擇頁面",
    ["比賽總覽", "圈速分析", "輪胎策略", "遙測數據 (VER)", "排名變化", "天氣"]
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
        color='TeamName', color_discrete_map=dict(zip(team_df['TeamName'], team_df['color'])),
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
        cons = cons.sort_values('cv')[['Driver', 'Team', 'avg_laptime', 'cv', 'lap_count']]
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
    laps = load_laps()
    stints = load_stints()

    timeline_data = []
    for _, stint in stints.iterrows():
        drv_num = stint['driver_number']
        drv_abb = DATA['results'][DATA['results']['DriverNumber'] == drv_num]['Abbreviation'].values
        if len(drv_abb) > 0:
            drv_abb = drv_abb[0]
            comp = stint['compound']
            start = int(stint['lap_start'])
            end = int(stint['lap_end'])
            timeline_data.append({
                '車手': drv_abb,
                'Compound': comp,
                'Start': start,
                'End': end,
                'Duration': end - start + 1
            })

    if timeline_data:
        timeline_df = pd.DataFrame(timeline_data)
        compound_colors = {'SOFT': '#FF3333', 'MEDIUM': '#FFD700', 'HARD': '#FFFFFF', 'INTER': '#00FF00', 'WET': '#0000FF'}
        timeline_df['color'] = timeline_df['Compound'].map(compound_colors)

        fig = px.timeline(
            timeline_df, x_start='Start', x_end='End', y='車手', color='Compound',
            color_discrete_map=compound_colors,
            title="輪胎使用時間軸 (Gantt)",
            labels={'Start': '開始圈', 'End': '結束圈'}
        )
        fig.update_yaxes(autorange="reversed")
        fig.update_layout(xaxis_title="圈數")
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("輪胎衰退率")
    deg = get_tyre_degradation()
    if len(deg) > 0:
        deg_display = deg[['driver', 'compound', 'degradation_rate', 'r2']].head(15).copy()
        deg_display.columns = ['車手', '輪胎', '衰退率(秒/圈)', 'R²']
        deg_display['衰退率(秒/圈)'] = deg_display['衰退率(秒/圈)'].round(4)
        deg_display['R²'] = deg_display['R²'].round(3)
        st.dataframe(deg_display, use_container_width=True, hide_index=True)

        fig = px.scatter(
            deg, x='laps_analyzed', y='degradation_rate', color='compound',
            size='r2', hover_data=['driver'],
            title="輪胎衰退率分析",
            labels={'laps_analyzed': '圈數', 'degradation_rate': '衰退率 (秒/圈)'}
        )
        st.plotly_chart(fig, use_container_width=True)

    st.divider()

    st.subheader("Compound 比較")
    compound_comp = get_compound_comparison()
    compound_stats = compound_comp.groupby('compound').agg(
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
    fig = px.line(
        speed_data, x='Distance', y='Speed', color='nGear',
        title="速度 vs 距離",
        labels={'Distance': '距離 (m)', 'Speed': '速度 (km/h)'}
    )
    fig.update_traces(line=dict(width=1))
    fig.update_layout(hovermode='closest')
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

    st.subheader("風速")
    fig = px.line(weather_df, x='Time_min', y='WindSpeed', title="風速變化", labels={'Time_min': '時間 (分鐘)', 'WindSpeed': '風速 (m/s)'})
    fig.update_traces(line_color='green')
    st.plotly_chart(fig, use_container_width=True)