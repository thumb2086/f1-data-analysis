"""Monza 2024 車手評分 leaderboard 產生器。"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from .features import build_rating_features
from .scoring import score_rating_features

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT_PATH = PROJECT_ROOT / 'outputs' / 'rating' / 'monza_2024.csv'


def build_rating_leaderboard(output_path: str | Path | None = None, save: bool = True, accurate_only: bool = True) -> pd.DataFrame:
    """建立 Monza 2024 車手評分 leaderboard。"""
    features = build_rating_features(accurate_only=accurate_only)
    scored = score_rating_features(features)

    leaderboard = scored.sort_values(['overall_score', 'finish_position'], ascending=[False, True]).reset_index(drop=True)
    leaderboard.insert(0, 'rank', range(1, len(leaderboard) + 1))

    cols = [
        'rank', 'driver', 'full_name', 'team_name', 'status', 'grid_position', 'finish_position',
        'overall_score', 'pace_score', 'consistency_score', 'start_finish_gain_score',
        'tyre_management_score', 'position_gain_loss_score',
        'avg_lap_sec', 'best_lap_sec', 'lap_std_sec', 'lap_cv_pct', 'pace_metric_sec',
        'start_finish_gain', 'position_gain', 'position_loss', 'position_net', 'position_moves',
        'tyre_deg_sec_per_lap', 'tyre_deg_model_r2', 'tyre_deg_stints_used', 'points', 'laps_completed',
        'rating_rank',
    ]
    cols = [c for c in cols if c in leaderboard.columns]
    leaderboard = leaderboard[cols]

    if save:
        path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT_PATH
        path.parent.mkdir(parents=True, exist_ok=True)
        leaderboard.to_csv(path, index=False)

    return leaderboard


def load_rating_leaderboard(path: str | Path | None = None) -> pd.DataFrame:
    """讀取已輸出的 leaderboard。"""
    file_path = Path(path) if path is not None else DEFAULT_OUTPUT_PATH
    return pd.read_csv(file_path)


def get_driver_rating(driver: str, leaderboard: pd.DataFrame | None = None) -> dict:
    """取得單一車手的評分資料，供 Product 3 / Bot 重用。"""
    df = leaderboard if leaderboard is not None else build_rating_leaderboard(save=False)
    row = df[df['driver'] == driver]
    if row.empty:
        raise KeyError(f'找不到車手: {driver}')
    return row.iloc[0].to_dict()


if __name__ == '__main__':
    lb = build_rating_leaderboard()
    print('=== Monza 2024 車手評分前五名 ===')
    print(lb[['rank', 'driver', 'overall_score', 'pace_score', 'consistency_score', 'start_finish_gain_score']].head(5).to_string(index=False))
    print(f"\n已輸出: {DEFAULT_OUTPUT_PATH}")
