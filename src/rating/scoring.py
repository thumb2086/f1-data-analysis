"""車手評分規則與加權。"""
from __future__ import annotations

import numpy as np
import pandas as pd

DEFAULT_WEIGHTS = {
    'pace_score': 0.30,
    'consistency_score': 0.20,
    'start_finish_gain_score': 0.20,
    'tyre_management_score': 0.15,
    'position_gain_loss_score': 0.15,
}

SCORE_COLUMNS = list(DEFAULT_WEIGHTS.keys())


def _min_max_score(series: pd.Series, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors='coerce')
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


def score_rating_features(features: pd.DataFrame) -> pd.DataFrame:
    """將原始特徵轉成 0-100 的子分數與總分。"""
    df = features.copy()

    df['pace_score'] = _min_max_score(df['pace_metric_sec'], higher_is_better=False)
    df['consistency_score'] = _min_max_score(df['lap_cv_pct'], higher_is_better=False)
    df['start_finish_gain_score'] = _min_max_score(df['start_finish_gain'], higher_is_better=True)
    df['tyre_management_score'] = _min_max_score(df['tyre_deg_sec_per_lap'], higher_is_better=False)
    df['position_gain_loss_score'] = _min_max_score(df['position_net'], higher_is_better=True)

    df['overall_score'] = 0.0
    for column, weight in DEFAULT_WEIGHTS.items():
        df['overall_score'] += df[column] * weight

    df['overall_score'] = df['overall_score'].clip(0, 100)
    df['rating_rank'] = df['overall_score'].rank(method='first', ascending=False).astype(int)
    return df
