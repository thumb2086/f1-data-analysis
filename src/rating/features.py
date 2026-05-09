"""車手評分特徵萃取。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

from src.data_loader import load_laps, load_results


@dataclass(frozen=True)
class RatingConfig:
    accurate_only: bool = True


def _prepare_laps(accurate_only: bool = True) -> pd.DataFrame:
    laps = load_laps().copy()
    if accurate_only and 'IsAccurate' in laps.columns:
        laps = laps[laps['IsAccurate'] == True].copy()
    laps = laps.dropna(subset=['Driver', 'LapNumber', 'LapTime'])
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()
    if 'Position' in laps.columns:
        laps['Position'] = pd.to_numeric(laps['Position'], errors='coerce')
    if 'TyreLife' in laps.columns:
        laps['TyreLife'] = pd.to_numeric(laps['TyreLife'], errors='coerce')
    if 'Stint' in laps.columns:
        laps['Stint'] = pd.to_numeric(laps['Stint'], errors='coerce')
    return laps


def _prepare_results() -> pd.DataFrame:
    results = load_results().copy()
    for col in ['Position', 'ClassifiedPosition', 'GridPosition', 'Points', 'Laps', 'DriverNumber']:
        if col in results.columns:
            results[col] = pd.to_numeric(results[col], errors='coerce')
    results['finish_position'] = results['Position'].fillna(results['ClassifiedPosition'])
    return results


def _compute_tyre_degradation(driver_laps: pd.DataFrame) -> dict:
    slopes: list[float] = []
    weights: list[float] = []
    r2_values: list[float] = []

    if 'Stint' in driver_laps.columns and 'TyreLife' in driver_laps.columns:
        grouped = driver_laps.groupby('Stint', dropna=True)
        for stint, group in grouped:
            clean = group.dropna(subset=['TyreLife', 'LapTime_seconds']).copy()
            if len(clean) < 4 or clean['TyreLife'].nunique() < 2:
                continue
            x = clean['TyreLife'].astype(float).to_numpy()
            y = clean['LapTime_seconds'].astype(float).to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            slopes.append(float(slope))
            weights.append(float(len(clean)))
            if len(clean) > 2:
                corr = np.corrcoef(x, y)[0, 1]
                if np.isfinite(corr):
                    r2_values.append(float(corr ** 2))

    if not slopes:
        clean = driver_laps.dropna(subset=['TyreLife', 'LapTime_seconds']).copy()
        if len(clean) >= 4 and clean['TyreLife'].nunique() >= 2:
            x = clean['TyreLife'].astype(float).to_numpy()
            y = clean['LapTime_seconds'].astype(float).to_numpy()
            slope, intercept = np.polyfit(x, y, 1)
            slopes.append(float(slope))
            weights.append(float(len(clean)))
            if len(clean) > 2:
                corr = np.corrcoef(x, y)[0, 1]
                if np.isfinite(corr):
                    r2_values.append(float(corr ** 2))

    if slopes:
        weighted_slope = float(np.average(slopes, weights=weights))
        avg_r2 = float(np.mean(r2_values)) if r2_values else np.nan
        return {
            'tyre_deg_sec_per_lap': weighted_slope,
            'tyre_deg_model_r2': avg_r2,
            'tyre_deg_stints_used': len(slopes),
        }

    return {
        'tyre_deg_sec_per_lap': np.nan,
        'tyre_deg_model_r2': np.nan,
        'tyre_deg_stints_used': 0,
    }


def get_driver_rating_features(accurate_only: bool = True) -> pd.DataFrame:
    """建立 Monza 2024 車手評分用的原始特徵表。"""
    laps = _prepare_laps(accurate_only=accurate_only)
    results = _prepare_results()

    rows = []
    for _, result in results.iterrows():
        driver = result['Abbreviation']
        driver_laps = laps[laps['Driver'] == driver].sort_values('LapNumber').copy()

        lap_times = driver_laps['LapTime_seconds'].dropna()
        avg_lap_sec = float(lap_times.mean()) if len(lap_times) else np.nan
        best_lap_sec = float(lap_times.min()) if len(lap_times) else np.nan
        lap_std_sec = float(lap_times.std()) if len(lap_times) > 1 else np.nan
        lap_cv_pct = float(lap_std_sec / avg_lap_sec * 100) if pd.notna(lap_std_sec) and pd.notna(avg_lap_sec) and avg_lap_sec else np.nan
        pace_metric_sec = float(0.7 * avg_lap_sec + 0.3 * best_lap_sec) if pd.notna(avg_lap_sec) and pd.notna(best_lap_sec) else np.nan

        # 起跑 vs 終點
        grid_position = pd.to_numeric(result.get('GridPosition'), errors='coerce')
        finish_position = pd.to_numeric(result.get('finish_position'), errors='coerce')
        start_finish_gain = float(grid_position - finish_position) if pd.notna(grid_position) and pd.notna(finish_position) else np.nan

        # 賽中位置變化：只看相鄰圈數的變化，不把起跑位算進來
        position_gain = np.nan
        position_loss = np.nan
        position_net = np.nan
        position_moves = np.nan
        if len(driver_laps) > 1 and 'Position' in driver_laps.columns:
            pos_series = pd.to_numeric(driver_laps['Position'], errors='coerce').dropna()
            if len(pos_series) > 1:
                deltas = pos_series.shift(1) - pos_series
                deltas = deltas.dropna()
                position_gain = float(deltas[deltas > 0].sum()) if len(deltas) else 0.0
                position_loss = float((-deltas[deltas < 0]).sum()) if len(deltas) else 0.0
                position_net = float(position_gain - position_loss)
                position_moves = float(position_gain + position_loss)

        tyre_stats = _compute_tyre_degradation(driver_laps)

        rows.append({
            'driver': driver,
            'full_name': result.get('FullName'),
            'team_name': result.get('TeamName'),
            'driver_number': result.get('DriverNumber'),
            'grid_position': grid_position,
            'finish_position': finish_position,
            'laps_completed': pd.to_numeric(result.get('Laps'), errors='coerce'),
            'status': result.get('Status'),
            'points': pd.to_numeric(result.get('Points'), errors='coerce'),
            'avg_lap_sec': avg_lap_sec,
            'best_lap_sec': best_lap_sec,
            'lap_std_sec': lap_std_sec,
            'lap_cv_pct': lap_cv_pct,
            'pace_metric_sec': pace_metric_sec,
            'start_finish_gain': start_finish_gain,
            'position_gain': position_gain,
            'position_loss': position_loss,
            'position_net': position_net,
            'position_moves': position_moves,
            **tyre_stats,
        })

    features = pd.DataFrame(rows)
    return features.sort_values('finish_position', na_position='last').reset_index(drop=True)


def build_rating_features(accurate_only: bool = True) -> pd.DataFrame:
    """向後相容的別名。"""
    return get_driver_rating_features(accurate_only=accurate_only)
