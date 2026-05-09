from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.io import to_html

from src.data_loader import get_race_info, load_stints
from src.lap_analysis import get_fastest_laps
from src.race_analysis import get_final_standings, get_position_change_summary
from src.telemetry_analysis import get_speed_profile, get_throttle_brake_analysis
from src.tyre_analysis import get_tyre_strategy
from src.weather_analysis import get_weather_summary, get_weather_timeline

from .render import render_template


REPORT_OUTPUT_DIR = Path(__file__).resolve().parents[2] / "outputs" / "reports"


def _format_number(value: Any, digits: int = 2) -> str:
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int,)):
        return str(value)
    if isinstance(value, float):
        if math.isnan(value):
            return "-"
        return f"{value:.{digits}f}"
    return str(value)


def dataframe_to_markdown(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or len(df) == 0:
        return "_No data available_"

    display_df = df.copy()
    if max_rows is not None:
        display_df = display_df.head(max_rows)

    columns = [str(col) for col in display_df.columns]
    rows = []
    for _, row in display_df.iterrows():
        rows.append([_format_number(row[col]) for col in display_df.columns])

    widths = [len(col) for col in columns]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(cell))

    def fmt_row(values: list[str]) -> str:
        return "| " + " | ".join(values[idx].ljust(widths[idx]) for idx in range(len(values))) + " |"

    header = fmt_row(columns)
    separator = "| " + " | ".join("-" * widths[idx] for idx in range(len(columns))) + " |"
    body = "\n".join(fmt_row(row) for row in rows)
    return "\n".join([header, separator, body])


def dataframe_to_html(df: pd.DataFrame, max_rows: int | None = None) -> str:
    if df is None or len(df) == 0:
        return "<p><em>No data available</em></p>"
    display_df = df.copy()
    if max_rows is not None:
        display_df = display_df.head(max_rows)
    return display_df.to_html(index=False, classes="report-table", border=0, escape=True)


def _position_change_figure(position_changes: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        position_changes,
        x="Abbreviation",
        y="position_change",
        color="position_change",
        color_continuous_scale=["#d73027", "#f7f7f7", "#1a9850"],
        title="Grid vs Finish Position Change",
        labels={"Abbreviation": "Driver", "position_change": "Positions gained"},
    )
    fig.update_layout(coloraxis_showscale=False, xaxis_tickangle=-45)
    fig.add_hline(y=0, line_width=1, line_color="#444")
    return fig


def _fastest_laps_figure(fastest_laps: pd.DataFrame) -> go.Figure:
    fig = px.bar(
        fastest_laps.sort_values("LapTime_seconds"),
        x="Driver",
        y="LapTime_seconds",
        color="Team",
        title="Fastest Lap Time by Driver",
        labels={"LapTime_seconds": "Lap time (s)", "Driver": "Driver"},
    )
    fig.update_layout(xaxis_tickangle=-45)
    fig.update_yaxes(autorange="reversed")
    return fig


def _tyre_strategy_figure() -> go.Figure:
    stints = load_stints().copy()
    strategy = get_tyre_strategy()
    if len(stints) == 0 or len(strategy) == 0:
        return go.Figure()

    # Map driver number to abbreviation
    driver_map = strategy.set_index("driver")["driver_number"].to_dict()
    reverse_map = {v: k for k, v in driver_map.items()}
    stints["driver"] = stints["driver_number"].map(reverse_map)
    stints = stints.dropna(subset=["driver"])

    compound_colors = {
        "SOFT": "#ff4d4d",
        "MEDIUM": "#ffd633",
        "HARD": "#d9d9d9",
        "INTERMEDIATE": "#2ecc71",
        "WET": "#3498db",
    }
    fig = go.Figure()
    for _, row in stints.iterrows():
        fig.add_trace(
            go.Bar(
                y=[row["driver"]],
                x=[int(row["lap_end"]) - int(row["lap_start"]) + 1],
                base=int(row["lap_start"]),
                orientation="h",
                marker=dict(color=compound_colors.get(str(row["compound"]), "#888888")),
                hovertemplate=(
                    f"{row['driver']}<br>Compound: {row['compound']}"
                    f"<br>Lap {int(row['lap_start'])}-{int(row['lap_end'])}"
                    f"<extra></extra>"
                ),
                showlegend=False,
            )
        )
    fig.update_layout(
        title="Tyre Strategy Timeline",
        xaxis_title="Lap",
        yaxis_title="Driver",
        barmode="stack",
        height=650,
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def _weather_figure(weather_timeline: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    if len(weather_timeline) > 0:
        if "Time_minutes" not in weather_timeline.columns:
            weather_timeline = weather_timeline.copy()
            weather_timeline["Time_minutes"] = weather_timeline["Time"].dt.total_seconds() / 60
        fig.add_trace(go.Scatter(x=weather_timeline["Time_minutes"], y=weather_timeline["AirTemp"], name="Air temp"))
        fig.add_trace(go.Scatter(x=weather_timeline["Time_minutes"], y=weather_timeline["TrackTemp"], name="Track temp"))
        fig.add_trace(go.Scatter(x=weather_timeline["Time_minutes"], y=weather_timeline["Humidity"], name="Humidity", yaxis="y2"))
        fig.update_layout(
            title="Weather Timeline",
            xaxis_title="Session time (min)",
            yaxis=dict(title="Temperature / Humidity"),
            yaxis2=dict(title="Humidity", overlaying="y", side="right", showgrid=False),
        )
    return fig


def _telemetry_figure(driver: str = "VER") -> go.Figure:
    speed_profile = get_speed_profile(driver)
    fig = px.line(
        speed_profile,
        x="Distance",
        y="Speed",
        color="nGear",
        title=f"{driver} Telemetry Speed Profile",
        labels={"Distance": "Distance (m)", "Speed": "Speed (km/h)", "nGear": "Gear"},
    )
    fig.update_traces(line=dict(width=1))
    return fig


def build_race_report(driver: str = "VER") -> dict[str, Any]:
    race_info = get_race_info()
    final_standings = get_final_standings()
    position_changes = get_position_change_summary()
    fastest_laps = get_fastest_laps()
    tyre_strategy = get_tyre_strategy()
    weather_summary = get_weather_summary()
    weather_timeline = get_weather_timeline()
    telemetry_summary = get_throttle_brake_analysis(driver)
    speed_profile = get_speed_profile(driver)

    standings_display = final_standings[["Position", "Abbreviation", "FullName", "TeamName", "GridPosition", "Points", "Status"]].copy()
    position_display = position_changes[["Abbreviation", "FullName", "TeamName", "GridPosition", "Position", "position_change", "change_label", "Points"]].copy()
    fastest_display = fastest_laps[["Driver", "Team", "LapTime", "LapTime_seconds", "LapNumber", "Compound", "TyreLife", "Position"]].copy()
    tyre_display = tyre_strategy[["driver", "n_stops", "stops_label", "compounds", "strategy", "final_position"]].copy()

    summary = {
        "winner": race_info["winner"],
        "winner_team": race_info["winner_team"],
        "total_laps": race_info["total_laps"],
        "drivers": race_info["drivers"],
        "finishers": race_info["finishers"],
        "weather_rain": race_info["weather"]["rain"],
        "temp_min": race_info["weather"]["temp_min"],
        "temp_max": race_info["weather"]["temp_max"],
        "track_temp_min": race_info["weather"]["track_temp_min"],
        "track_temp_max": race_info["weather"]["track_temp_max"],
    }

    figures = {
        "position_change": _position_change_figure(position_changes),
        "fastest_laps": _fastest_laps_figure(fastest_laps),
        "tyre_strategy": _tyre_strategy_figure(),
        "weather": _weather_figure(weather_timeline),
        "telemetry": _telemetry_figure(driver),
    }

    return {
        "summary": summary,
        "race_info": race_info,
        "standings": standings_display,
        "position_changes": position_display,
        "fastest_laps": fastest_display,
        "tyre_strategy": tyre_display,
        "weather_summary": weather_summary,
        "weather_timeline": weather_timeline,
        "telemetry_summary": telemetry_summary,
        "speed_profile": speed_profile,
        "figures": figures,
    }


def _html_figures(figures: dict[str, go.Figure]) -> dict[str, str]:
    return {
        name: to_html(fig, include_plotlyjs=False, full_html=False) for name, fig in figures.items()
    }


def generate_race_report(output_dir: Path | None = None, driver: str = "VER") -> dict[str, Path]:
    context = build_race_report(driver=driver)
    output_dir = Path(output_dir) if output_dir else REPORT_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    html_context = dict(context)
    html_context["figure_html"] = _html_figures(context["figures"])
    html_context["standings_html"] = dataframe_to_html(context["standings"])
    html_context["position_changes_html"] = dataframe_to_html(context["position_changes"])
    html_context["fastest_laps_html"] = dataframe_to_html(context["fastest_laps"])
    html_context["tyre_strategy_html"] = dataframe_to_html(context["tyre_strategy"])
    html_context["weather_html"] = dataframe_to_html(
        pd.DataFrame([
            {"Metric": "Air temp min", "Value": context["summary"]["temp_min"]},
            {"Metric": "Air temp max", "Value": context["summary"]["temp_max"]},
            {"Metric": "Track temp min", "Value": context["summary"]["track_temp_min"]},
            {"Metric": "Track temp max", "Value": context["summary"]["track_temp_max"]},
            {"Metric": "Rainfall", "Value": context["summary"]["weather_rain"]},
        ])
    )
    html_context["telemetry_html"] = dataframe_to_html(
        pd.DataFrame([
            {"Metric": "Full throttle %", "Value": context["telemetry_summary"]["full_throttle_pct"]},
            {"Metric": "Braking %", "Value": context["telemetry_summary"]["braking_pct"]},
            {"Metric": "Coasting %", "Value": context["telemetry_summary"]["coasting_pct"]},
            {"Metric": "Average speed", "Value": context["telemetry_summary"]["avg_speed"]},
            {"Metric": "Max speed", "Value": context["telemetry_summary"]["max_speed"]},
            {"Metric": "Brake points", "Value": context["telemetry_summary"]["brake_points"]},
        ])
    )
    html_context["driver"] = driver

    md_context = dict(context)
    md_context["standings_md"] = dataframe_to_markdown(context["standings"])
    md_context["position_changes_md"] = dataframe_to_markdown(context["position_changes"])
    md_context["fastest_laps_md"] = dataframe_to_markdown(context["fastest_laps"])
    md_context["tyre_strategy_md"] = dataframe_to_markdown(context["tyre_strategy"])
    md_context["driver"] = driver

    md_text = render_template("monza_2024.md.j2", md_context)
    html_text = render_template("monza_2024.html.j2", html_context)

    md_path = output_dir / "2024_italian_gp.md"
    html_path = output_dir / "2024_italian_gp.html"
    md_path.write_text(md_text, encoding="utf-8")
    html_path.write_text(html_text, encoding="utf-8")
    return {"markdown": md_path, "html": html_path}


if __name__ == "__main__":
    paths = generate_race_report()
    print(f"Markdown report: {paths['markdown']}")
    print(f"HTML report: {paths['html']}")
