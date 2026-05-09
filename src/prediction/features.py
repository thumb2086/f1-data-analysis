"""Feature extraction for the Monza 2024 prediction baseline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from src.data_loader import load_laps, load_results, load_stints, load_weather


@dataclass(frozen=True)
class PredictionConfig:
    accurate_only: bool = True


def _to_seconds(series: pd.Series) -> pd.Series:
    if pd.api.types.is_timedelta64_dtype(series):
        return series.dt.total_seconds()
    return pd.to_numeric(series, errors="coerce")


def _prepare_laps(accurate_only: bool = True) -> pd.DataFrame:
    laps = load_laps().copy()
    if accurate_only and "IsAccurate" in laps.columns:
        laps = laps[laps["IsAccurate"] == True].copy()  # noqa: E712

    for col in [
        "LapTime",
        "PitOutTime",
        "PitInTime",
        "Sector1Time",
        "Sector2Time",
        "Sector3Time",
        "Sector1SessionTime",
        "Sector2SessionTime",
        "Sector3SessionTime",
        "LapStartTime",
        "Time",
    ]:
        if col in laps.columns:
            laps[col] = pd.to_timedelta(laps[col], errors="coerce")

    for col in ["LapNumber", "Stint", "SpeedI1", "SpeedI2", "SpeedFL", "SpeedST", "TyreLife", "Position"]:
        if col in laps.columns:
            laps[col] = pd.to_numeric(laps[col], errors="coerce")

    if "LapTime" in laps.columns:
        laps["LapTime_seconds"] = laps["LapTime"].dt.total_seconds()
    else:
        laps["LapTime_seconds"] = np.nan

    if "TyreLife" in laps.columns:
        laps["TyreLife"] = pd.to_numeric(laps["TyreLife"], errors="coerce")

    return laps


def _prepare_results() -> pd.DataFrame:
    results = load_results().copy()
    for col in ["DriverNumber", "Position", "ClassifiedPosition", "GridPosition", "Points", "Laps"]:
        if col in results.columns:
            results[col] = pd.to_numeric(results[col], errors="coerce")
    results["finish_position"] = results["Position"].fillna(results.get("ClassifiedPosition"))
    return results


def _prepare_stints() -> pd.DataFrame:
    stints = load_stints().copy()
    for col in ["meeting_key", "session_key", "stint_number", "driver_number", "lap_start", "lap_end", "tyre_age_at_start"]:
        if col in stints.columns:
            stints[col] = pd.to_numeric(stints[col], errors="coerce")
    return stints


def _prepare_weather() -> pd.DataFrame:
    weather = load_weather().copy()
    if "Time" in weather.columns:
        weather["Time"] = pd.to_timedelta(weather["Time"], errors="coerce")
    for col in ["AirTemp", "Humidity", "Pressure", "TrackTemp", "WindDirection", "WindSpeed"]:
        if col in weather.columns:
            weather[col] = pd.to_numeric(weather[col], errors="coerce")
    if "Rainfall" in weather.columns:
        weather["Rainfall"] = weather["Rainfall"].astype(bool)
    return weather


def _compute_tyre_degradation(driver_laps: pd.DataFrame) -> dict[str, float]:
    slopes: list[float] = []
    weights: list[float] = []

    if "Stint" in driver_laps.columns and "TyreLife" in driver_laps.columns:
        for _, stint_df in driver_laps.groupby("Stint", dropna=True):
            clean = stint_df.dropna(subset=["TyreLife", "LapTime_seconds"])
            if len(clean) < 4 or clean["TyreLife"].nunique() < 2:
                continue
            x = clean["TyreLife"].astype(float).to_numpy()
            y = clean["LapTime_seconds"].astype(float).to_numpy()
            slope, _ = np.polyfit(x, y, 1)
            slopes.append(float(slope))
            weights.append(float(len(clean)))

    if not slopes:
        clean = driver_laps.dropna(subset=["TyreLife", "LapTime_seconds"])
        if len(clean) >= 4 and clean["TyreLife"].nunique() >= 2:
            x = clean["TyreLife"].astype(float).to_numpy()
            y = clean["LapTime_seconds"].astype(float).to_numpy()
            slope, _ = np.polyfit(x, y, 1)
            slopes.append(float(slope))
            weights.append(float(len(clean)))

    if slopes:
        return {
            "tyre_deg_sec_per_lap": float(np.average(slopes, weights=weights)),
            "tyre_deg_stints_used": float(len(slopes)),
        }

    return {
        "tyre_deg_sec_per_lap": np.nan,
        "tyre_deg_stints_used": 0.0,
    }


def _compound_usage_summary(driver_stints: pd.DataFrame) -> dict[str, float]:
    summary = {"hard_stint_share": np.nan, "medium_stint_share": np.nan, "soft_stint_share": np.nan, "stint_count": 0.0, "max_stint_laps": np.nan, "mean_stint_laps": np.nan}
    if len(driver_stints) == 0:
        return summary

    stints = driver_stints.copy()
    if "lap_start" in stints.columns and "lap_end" in stints.columns:
        stints["stint_laps"] = pd.to_numeric(stints["lap_end"], errors="coerce") - pd.to_numeric(stints["lap_start"], errors="coerce") + 1
    else:
        stints["stint_laps"] = np.nan

    summary["stint_count"] = float(stints["stint_number"].nunique()) if "stint_number" in stints.columns else float(len(stints))
    summary["max_stint_laps"] = float(stints["stint_laps"].max()) if stints["stint_laps"].notna().any() else np.nan
    summary["mean_stint_laps"] = float(stints["stint_laps"].mean()) if stints["stint_laps"].notna().any() else np.nan

    if "compound" in stints.columns and len(stints) > 0:
        counts = stints["compound"].astype(str).str.upper().value_counts(normalize=True)
        summary["hard_stint_share"] = float(counts.get("HARD", 0.0))
        summary["medium_stint_share"] = float(counts.get("MEDIUM", 0.0))
        summary["soft_stint_share"] = float(counts.get("SOFT", 0.0))

    return summary


def get_driver_prediction_features(accurate_only: bool = True) -> pd.DataFrame:
    """Build a driver-level feature table for the Monza 2024 baseline model."""
    laps = _prepare_laps(accurate_only=accurate_only)
    results = _prepare_results()
    stints = _prepare_stints()
    weather = _prepare_weather()

    weather_summary = {
        "weather_rain": bool(weather["Rainfall"].any()) if "Rainfall" in weather.columns and len(weather) else False,
        "avg_air_temp": float(weather["AirTemp"].mean()) if "AirTemp" in weather.columns and len(weather) else np.nan,
        "avg_track_temp": float(weather["TrackTemp"].mean()) if "TrackTemp" in weather.columns and len(weather) else np.nan,
        "avg_wind_speed": float(weather["WindSpeed"].mean()) if "WindSpeed" in weather.columns and len(weather) else np.nan,
    }

    rows: list[dict[str, object]] = []
    for _, result in results.iterrows():
        driver = str(result["Abbreviation"])
        driver_number = pd.to_numeric(result.get("DriverNumber"), errors="coerce")
        driver_laps = laps[laps["Driver"] == driver].sort_values("LapNumber").copy()
        driver_stints = stints[stints["driver_number"] == driver_number].copy() if pd.notna(driver_number) else stints.iloc[0:0].copy()

        lap_times = driver_laps["LapTime_seconds"].dropna()
        avg_lap_sec = float(lap_times.mean()) if len(lap_times) else np.nan
        best_lap_sec = float(lap_times.min()) if len(lap_times) else np.nan
        median_lap_sec = float(lap_times.median()) if len(lap_times) else np.nan
        lap_std_sec = float(lap_times.std()) if len(lap_times) > 1 else np.nan
        lap_cv_pct = float(lap_std_sec / avg_lap_sec * 100) if pd.notna(lap_std_sec) and pd.notna(avg_lap_sec) and avg_lap_sec else np.nan
        lap_count = float(len(lap_times))

        pace_trend_sec_per_lap = np.nan
        if len(driver_laps) >= 4 and driver_laps["LapNumber"].nunique() >= 2:
            clean = driver_laps.dropna(subset=["LapNumber", "LapTime_seconds"])
            if len(clean) >= 4:
                x = clean["LapNumber"].astype(float).to_numpy()
                y = clean["LapTime_seconds"].astype(float).to_numpy()
                slope, _ = np.polyfit(x, y, 1)
                pace_trend_sec_per_lap = float(slope)

        tyre_stats = _compute_tyre_degradation(driver_laps)
        stint_stats = _compound_usage_summary(driver_stints)

        rows.append(
            {
                "driver": driver,
                "driver_number": driver_number,
                "full_name": result.get("FullName"),
                "team_name": result.get("TeamName"),
                "grid_position": pd.to_numeric(result.get("GridPosition"), errors="coerce"),
                "finish_position": pd.to_numeric(result.get("finish_position"), errors="coerce"),
                "status": result.get("Status"),
                "points": pd.to_numeric(result.get("Points"), errors="coerce"),
                "laps_completed": pd.to_numeric(result.get("Laps"), errors="coerce"),
                "lap_count": lap_count,
                "avg_lap_sec": avg_lap_sec,
                "best_lap_sec": best_lap_sec,
                "median_lap_sec": median_lap_sec,
                "lap_std_sec": lap_std_sec,
                "lap_cv_pct": lap_cv_pct,
                "pace_trend_sec_per_lap": pace_trend_sec_per_lap,
                **tyre_stats,
                **stint_stats,
                **weather_summary,
            }
        )

    features = pd.DataFrame(rows)

    if len(features) > 0:
        team_summary = features.groupby("team_name").agg(
            team_grid_mean=("grid_position", "mean"),
            team_pace_mean=("avg_lap_sec", "mean"),
            team_cv_mean=("lap_cv_pct", "mean"),
            team_deg_mean=("tyre_deg_sec_per_lap", "mean"),
            team_stint_mean=("stint_count", "mean"),
        )
        features = features.merge(team_summary, on="team_name", how="left")

    return features.sort_values(["grid_position", "driver"], na_position="last").reset_index(drop=True)


def build_prediction_features(accurate_only: bool = True) -> pd.DataFrame:
    """Backward-compatible alias used by other products."""
    return get_driver_prediction_features(accurate_only=accurate_only)
