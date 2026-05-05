"""
F1 數據分析專案 — 圈速分析模組
"""
import pandas as pd
import numpy as np
from .data_loader import load_laps, load_results


def get_fastest_laps(accurate_only: bool = True) -> pd.DataFrame:
    """每位車手的最快圈速"""
    laps = load_laps()
    if accurate_only:
        laps = laps[laps['IsAccurate'] == True]
    fastest = laps.loc[laps.groupby('Driver')['LapTime'].idxmin()]
    fastest = fastest.sort_values('LapTime')
    fastest['LapTime_seconds'] = fastest['LapTime'].dt.total_seconds()
    return fastest[['Driver', 'Team', 'LapTime', 'LapTime_seconds', 'LapNumber',
                    'Compound', 'TyreLife', 'Position']].reset_index(drop=True)


def get_driver_lap_times(driver: str, accurate_only: bool = True) -> pd.DataFrame:
    """某位車手的所有圈速"""
    laps = load_laps()
    dr = laps[laps['Driver'] == driver].copy()
    if accurate_only:
        dr = dr[dr['IsAccurate'] == True]
    dr['LapTime_seconds'] = dr['LapTime'].dt.total_seconds()
    return dr[['LapNumber', 'LapTime', 'LapTime_seconds', 'Compound', 'TyreLife',
               'Position', 'IsPersonalBest']].sort_values('LapNumber').reset_index(drop=True)


def get_lap_time_evolution(drivers: list[str] = None, accurate_only: bool = True) -> pd.DataFrame:
    """圈速演進 — 多車手比較用"""
    laps = load_laps()
    if accurate_only:
        laps = laps[laps['IsAccurate'] == True]
    if drivers:
        laps = laps[laps['Driver'].isin(drivers)]
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()
    return laps[['LapNumber', 'Driver', 'Team', 'LapTime', 'LapTime_seconds',
                 'Compound', 'TyreLife', 'Position']].sort_values(['Driver', 'LapNumber'])


def get_lap_consistency(driver: str, accurate_only: bool = True) -> dict:
    """計算車手的圈速一致性（標準差、CV 變異係數）"""
    laps = get_driver_lap_times(driver, accurate_only)
    if len(laps) == 0:
        return {'driver': driver, 'mean': None, 'std': None, 'cv': None, 'min': None, 'max': None}
    times = laps['LapTime_seconds']
    return {
        'driver': driver,
        'mean': float(times.mean()),
        'std': float(times.std()),
        'cv': float(times.std() / times.mean() * 100),  # 變異係數 %
        'min': float(times.min()),
        'max': float(times.max()),
        'laps_count': len(times),
    }


def get_all_drivers_consistency(accurate_only: bool = True) -> pd.DataFrame:
    """所有車手的圈速一致性排名"""
    laps = load_laps()
    if accurate_only:
        laps = laps[laps['IsAccurate'] == True]
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()
    stats = laps.groupby('Driver').agg(
        avg_laptime=('LapTime_seconds', 'mean'),
        std_laptime=('LapTime_seconds', 'std'),
        min_laptime=('LapTime_seconds', 'min'),
        max_laptime=('LapTime_seconds', 'max'),
        lap_count=('LapNumber', 'count'),
        team=('Team', 'first'),
    ).reset_index()
    stats['cv'] = stats['std_laptime'] / stats['avg_laptime'] * 100
    # 加入最終排名
    results = load_results()
    pos_map = results.set_index('Abbreviation')['Position'].to_dict()
    stats['final_position'] = stats['Driver'].map(pos_map)
    return stats.sort_values('cv').reset_index(drop=True)


def get_sector_analysis(driver: str) -> dict:
    """分段分析：S1/S2/S3 時間"""
    laps = load_laps()
    dr = laps[(laps['Driver'] == driver) & (laps['IsAccurate'] == True)].copy()
    if len(dr) == 0:
        return {}
    sectors = {}
    for s in ['Sector1Time', 'Sector2Time', 'Sector3Time']:
        clean = dr[dr[s].notna()]
        sectors[s] = {
            'best': float(clean[s].min().total_seconds()),
            'avg': float(clean[s].mean().total_seconds()),
            'std': float(clean[s].std().total_seconds()),
        }
    return {'driver': driver, 'sectors': sectors}


def get_overtake_analysis() -> pd.DataFrame:
    """起跑得失位分析"""
    results = load_results()
    results['position_change'] = results['GridPosition'] - results['Position']
    results['podium'] = results['Position'] <= 3
    return results[['Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'Position',
                    'position_change', 'Points', 'podium']].sort_values('Position').reset_index(drop=True)


if __name__ == '__main__':
    print("=== 最快圈速 ===")
    print(get_fastest_laps()[['Driver', 'LapTime', 'Compound', 'TyreLife']].to_string(index=False))
    print()
    print("=== 圈速一致性排名 ===")
    print(get_all_drivers_consistency()[['Driver', 'avg_laptime', 'cv', 'final_position']].head(5).to_string(index=False))