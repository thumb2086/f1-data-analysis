"""
F1 數據分析專案 — 遙測分析模組
"""
import pandas as pd
import numpy as np
from .data_loader import load_telemetry


def get_telemetry_data(driver: str = 'VER') -> pd.DataFrame:
    """載入並清理遙測數據"""
    df = load_telemetry(driver)
    return df


def get_speed_profile(driver: str = 'VER') -> pd.DataFrame:
    """速度 vs 距離 曲線（用於繪圖）"""
    df = get_telemetry_data(driver)
    return df[['Distance', 'Speed', 'RelativeDistance', 'RPM', 'nGear', 'Throttle', 'Brake', 'DRS']]


def get_throttle_brake_analysis(driver: str = 'VER') -> dict:
    """油門與煞車使用分析"""
    df = get_telemetry_data(driver)
    total_points = len(df)
    full_throttle = (df['Throttle'] >= 95).sum()
    braking = df['Brake'].sum()
    coasting = ((df['Throttle'] < 5) & (df['Brake'] == False)).sum()

    # 找煞車點
    brake_points = []
    for i in range(1, len(df)):
        if df['Brake'].iloc[i] and not df['Brake'].iloc[i-1]:
            brake_points.append({
                'distance': float(df['Distance'].iloc[i]),
                'speed': float(df['Speed'].iloc[i]),
                'gear': int(df['nGear'].iloc[i]),
            })

    # DRS 區域
    drs_active = df[df['DRS'] >= 10].shape[0] if df['DRS'].max() > 0 else 0

    return {
        'driver': driver,
        'total_points': total_points,
        'full_throttle_pct': float(full_throttle / total_points * 100),
        'braking_pct': float(braking / total_points * 100),
        'coasting_pct': float(coasting / total_points * 100),
        'drs_active_pct': float(drs_active / total_points * 100) if total_points > 0 else 0,
        'avg_speed': float(df['Speed'].mean()),
        'max_speed': float(df['Speed'].max()),
        'avg_rpm': float(df['RPM'].mean()),
        'max_rpm': float(df['RPM'].max()),
        'brake_points': len(brake_points),
        'gear_usage': {int(g): int((df['nGear'] == g).sum()) for g in sorted(df['nGear'].unique())},
    }


def get_gear_time_distribution(driver: str = 'VER') -> dict:
    """各檔位使用時間佔比"""
    df = get_telemetry_data(driver)
    total = len(df)
    dist = {}
    for gear in sorted(df['nGear'].unique()):
        cnt = int((df['nGear'] == gear).sum())
        dist[int(gear)] = {
            'count': cnt,
            'pct': float(cnt / total * 100) if total > 0 else 0,
        }
    return {'driver': driver, 'total_points': total, 'gear_distribution': dist}


def get_minisector_speed(driver: str = 'VER', n_sectors: int = 20) -> pd.DataFrame:
    """將賽道分成 N 個小區段，計算每個區段的平均速度"""
    df = get_telemetry_data(driver)
    df['sector_bin'] = pd.cut(df['RelativeDistance'], bins=n_sectors, labels=False)
    sector_stats = df.groupby('sector_bin').agg(
        avg_speed=('Speed', 'mean'),
        max_speed=('Speed', 'max'),
        min_speed=('Speed', 'min'),
        avg_throttle=('Throttle', 'mean'),
        braking_pct=('Brake', 'mean'),
    ).reset_index()
    sector_stats['sector_name'] = sector_stats['sector_bin'].apply(
        lambda x: f"S{x+1:02d}"
    )
    sector_stats['distance_start'] = sector_stats['sector_bin'] / n_sectors
    return sector_stats


if __name__ == '__main__':
    print("=== VER 遙測摘要 ===")
    analysis = get_throttle_brake_analysis('VER')
    print(f"全油門: {analysis['full_throttle_pct']:.1f}%")
    print(f"煞車: {analysis['braking_pct']:.1f}%")
    print(f"滑行: {analysis['coasting_pct']:.1f}%")
    print(f"平均速度: {analysis['avg_speed']:.1f} km/h")
    print(f"最高速度: {analysis['max_speed']:.1f} km/h")