"""
F1 數據分析專案 — 比賽排名與得分分析模組
"""
import pandas as pd
import numpy as np
from .data_loader import load_results, load_laps


def get_final_standings() -> pd.DataFrame:
    """最終排名"""
    results = load_results()
    return results[['Position', 'Abbreviation', 'FullName', 'TeamName', 'GridPosition',
                    'Points', 'Laps', 'Status']].sort_values('Position').reset_index(drop=True)


def get_position_change_summary() -> pd.DataFrame:
    """起跑 vs 最終排名變化（得失位分析）"""
    results = load_results()
    results['position_change'] = results['GridPosition'] - results['Position']
    results['change_label'] = results['position_change'].apply(
        lambda x: f"+{int(x)}" if x > 0 else (str(int(x)) if x < 0 else "0")
    )
    results['gained_positions'] = results['position_change'] > 0
    return results[['Abbreviation', 'FullName', 'TeamName', 'GridPosition', 'Position',
                    'position_change', 'change_label', 'Points']].sort_values(
                        'position_change', ascending=False).reset_index(drop=True)


def get_position_evolution(drivers: list[str] = None) -> pd.DataFrame:
    """每圈位置變化"""
    laps = load_laps()
    laps = laps[laps['IsAccurate'] == True]
    if drivers:
        laps = laps[laps['Driver'].isin(drivers)]
    return laps[['LapNumber', 'Driver', 'Position', 'Team']].sort_values(['Driver', 'LapNumber']).reset_index(drop=True)


def get_top_speed_trap() -> pd.DataFrame:
    """最快速度排名（Speed Trap）"""
    laps = load_laps()
    laps = laps[laps['IsAccurate'] == True]
    fastest = laps.loc[laps.groupby('Driver')['SpeedST'].idxmax()]
    fastest = fastest.sort_values('SpeedST', ascending=False)
    return fastest[['Driver', 'Team', 'SpeedST', 'LapNumber', 'Compound', 'TyreLife']].reset_index(drop=True)


def get_race_winner_stats() -> dict:
    """冠軍統計資訊"""
    results = load_results()
    laps = load_laps()
    winner = results[results['Position'] == 1].iloc[0]
    winner_code = winner['Abbreviation']
    winner_laps = laps[(laps['Driver'] == winner_code) & (laps['IsAccurate'] == True)]

    return {
        'driver': winner_code,
        'full_name': winner['FullName'],
        'team': winner['TeamName'],
        'grid': int(winner['GridPosition']),
        'points': int(winner['Points']),
        'laps_completed': int(winner['Laps']),
        'avg_laptime_seconds': float(winner_laps['LapTime'].dt.total_seconds().mean()),
        'fastest_lap_seconds': float(winner_laps['LapTime'].dt.total_seconds().min()),
        'led_laps': int((laps[laps['Driver'] == winner_code].groupby('LapNumber')['Position'].first() == 1).sum()),
    }


def get_team_standings() -> pd.DataFrame:
    """車隊積分"""
    results = load_results()
    team_pts = results.groupby('TeamName').agg(
        total_points=('Points', 'sum'),
        drivers=('Abbreviation', lambda x: ' / '.join(sorted(x))),
        best_position=('Position', 'min'),
    ).reset_index().sort_values('total_points', ascending=False)
    team_pts['color'] = results.drop_duplicates('TeamName').set_index('TeamName')['TeamColor'].reindex(team_pts['TeamName']).values
    return team_pts


if __name__ == '__main__':
    print("=== 最終排名 ===")
    print(get_final_standings()[['Position', 'Abbreviation', 'TeamName', 'Points']].to_string(index=False))
    print()
    print("=== 得失位 ===")
    print(get_position_change_summary()[['Abbreviation', 'GridPosition', 'Position', 'change_label']].head(5).to_string(index=False))