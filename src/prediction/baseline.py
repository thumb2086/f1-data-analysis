"""Explainable baseline predictions for Monza 2024."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .features import get_driver_prediction_features


@dataclass(frozen=True)
class BaselineWeights:
    grid_weight: float = 0.34
    pace_weight: float = 0.32
    consistency_weight: float = 0.16
    degradation_weight: float = 0.10
    team_weight: float = 0.08


DEFAULT_WEIGHTS = BaselineWeights()


def _min_max(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    if valid.empty:
        return pd.Series([50.0] * len(values), index=values.index, dtype=float)

    min_v = float(valid.min())
    max_v = float(valid.max())
    if np.isclose(max_v, min_v):
        return pd.Series([50.0] * len(values), index=values.index, dtype=float)

    if higher_is_better:
        scores = (values - min_v) / (max_v - min_v) * 100.0
    else:
        scores = (max_v - values) / (max_v - min_v) * 100.0
    return scores.clip(0, 100).fillna(50.0).astype(float)


def _safe_rank(series: pd.Series, ascending: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    valid = values.dropna()
    if valid.empty:
        return pd.Series([np.nan] * len(values), index=values.index, dtype=float)
    return values.rank(method="first", ascending=ascending)


def _gain_band(predicted_gain: float) -> str:
    if pd.isna(predicted_gain):
        return "Unknown"
    if predicted_gain >= 5:
        return "Gain 5+"
    if predicted_gain >= 1:
        return "Gain 1-4"
    if predicted_gain <= -5:
        return "Loss 5+"
    if predicted_gain <= -1:
        return "Loss 1-4"
    return "Hold"


def _strategy_label(stint_count: float, max_stint_laps: float, hard_stint_share: float, tyre_deg_sec_per_lap: float) -> tuple[str, float]:
    if pd.isna(stint_count):
        return "Unknown", 0.0

    # F1 strategy convention: 2 stints ~= one-stop, 3+ stints ~= two-stop or more.
    # The MVP target is binary, so 3+ stints are collapsed into the two-stop bucket.
    if stint_count <= 2:
        confidence = 0.65
        confidence += 0.20 if pd.notna(max_stint_laps) and max_stint_laps >= 24 else 0.05
        confidence += 0.15 if pd.notna(hard_stint_share) and hard_stint_share >= 0.25 else 0.05
        if pd.notna(tyre_deg_sec_per_lap) and tyre_deg_sec_per_lap <= 0.045:
            confidence += 0.05
        return "One-stop", float(np.clip(confidence, 0.0, 1.0))

    confidence = 0.65
    confidence += 0.20 if pd.notna(max_stint_laps) and max_stint_laps < 24 else 0.08
    confidence += 0.10 if stint_count >= 3 else 0.0
    return "Two-stop", float(np.clip(confidence, 0.0, 1.0))


def predict_driver_baseline(features: pd.DataFrame) -> pd.DataFrame:
    """Score each driver with a transparent rule-based baseline."""
    df = features.copy()

    df["grid_score"] = _min_max(df["grid_position"], higher_is_better=False)
    df["pace_score"] = _min_max(df["avg_lap_sec"], higher_is_better=False)
    df["consistency_score"] = _min_max(df["lap_cv_pct"], higher_is_better=False)
    df["degradation_score"] = _min_max(df["tyre_deg_sec_per_lap"], higher_is_better=False)
    df["team_score"] = _min_max(df["team_grid_mean"], higher_is_better=False)
    df["stint_score"] = _min_max(df["stint_count"], higher_is_better=False)

    df["finish_score"] = (
        df["grid_score"] * DEFAULT_WEIGHTS.grid_weight
        + df["pace_score"] * DEFAULT_WEIGHTS.pace_weight
        + df["consistency_score"] * DEFAULT_WEIGHTS.consistency_weight
        + df["degradation_score"] * DEFAULT_WEIGHTS.degradation_weight
        + df["team_score"] * DEFAULT_WEIGHTS.team_weight
    )

    df["predicted_finish_rank"] = _safe_rank(df["finish_score"], ascending=False)
    df["predicted_finish_rank"] = df["predicted_finish_rank"].astype("Int64")

    def classify_rank(rank: float) -> str:
        if pd.isna(rank):
            return "DNF"
        if rank <= 3:
            return "Top 3"
        if rank <= 10:
            return "Top 10"
        return "DNF"

    df["predicted_result_class"] = df["predicted_finish_rank"].apply(classify_rank)

    df["predicted_gain"] = pd.to_numeric(df["grid_position"], errors="coerce") - pd.to_numeric(df["predicted_finish_rank"], errors="coerce")
    df["predicted_gain_band"] = df["predicted_gain"].apply(_gain_band)

    strategy_results = df.apply(
        lambda row: _strategy_label(
            row.get("stint_count"),
            row.get("max_stint_laps"),
            row.get("hard_stint_share"),
            row.get("tyre_deg_sec_per_lap"),
        ),
        axis=1,
        result_type="expand",
    )
    df["predicted_strategy"] = strategy_results[0]
    df["strategy_confidence"] = strategy_results[1].astype(float)

    df["result_confidence"] = np.clip(df["finish_score"] / 100.0, 0.0, 1.0)
    df["result_confidence"] = df["result_confidence"].round(3)
    df["strategy_confidence"] = df["strategy_confidence"].round(3)

    df["predicted_result_explanation"] = df.apply(
        lambda row: (
            f"Grid {int(row['grid_position']) if pd.notna(row['grid_position']) else '-'}"
            f" + pace {row['pace_score']:.0f}/100"
            f" + consistency {row['consistency_score']:.0f}/100"
            f" -> rank {int(row['predicted_finish_rank']) if pd.notna(row['predicted_finish_rank']) else '-'}"
        ),
        axis=1,
    )
    df["predicted_strategy_explanation"] = df.apply(
        lambda row: (
            f"{int(row['stint_count']) if pd.notna(row['stint_count']) else '-'} stints"
            f", longest stint {int(row['max_stint_laps']) if pd.notna(row['max_stint_laps']) else '-'} laps"
            f", hard-stint share {row['hard_stint_share']:.0%}"
        ),
        axis=1,
    )

    if "finish_position" in df.columns:
        df["actual_gain"] = pd.to_numeric(df["grid_position"], errors="coerce") - pd.to_numeric(df["finish_position"], errors="coerce")
        df["actual_gain_band"] = df["actual_gain"].apply(_gain_band)
        df["actual_strategy"] = np.where(df["stint_count"] <= 2, "One-stop", "Two-stop")

    sort_cols = ["predicted_finish_rank", "driver"] if "driver" in df.columns else ["predicted_finish_rank"]
    return df.sort_values(sort_cols, na_position="last").reset_index(drop=True)


def build_prediction_table(accurate_only: bool = True) -> pd.DataFrame:
    features = get_driver_prediction_features(accurate_only=accurate_only)
    return predict_driver_baseline(features)
