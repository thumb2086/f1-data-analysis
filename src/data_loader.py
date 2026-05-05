"""
F1 數據分析專案 — 數據載入與清理模組
"""
import pandas as pd
import os

RAW_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'raw')


def load_laps() -> pd.DataFrame:
    """載入圈速資料"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'laps.csv'))
    # 轉換時間欄位
    time_cols = ['Time', 'LapTime', 'PitOutTime', 'PitInTime',
                 'Sector1Time', 'Sector2Time', 'Sector3Time',
                 'Sector1SessionTime', 'Sector2SessionTime', 'Sector3SessionTime',
                 'LapStartTime']
    for col in time_cols:
        if col in df.columns:
            df[col] = pd.to_timedelta(df[col])
    # 轉換數值欄位
    numeric_cols = ['LapNumber', 'Stint', 'SpeedI1', 'SpeedI2', 'SpeedFL', 'SpeedST',
                    'TyreLife', 'Position']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    # 轉換 boolean
    bool_cols = ['IsPersonalBest', 'FreshTyre', 'Deleted', 'FastF1Generated', 'IsAccurate']
    for col in bool_cols:
        if col in df.columns:
            df[col] = df[col].astype(bool)
    return df


def load_results() -> pd.DataFrame:
    """載入比賽結果"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'results.csv'))
    numeric_cols = ['DriverNumber', 'Position', 'ClassifiedPosition', 'GridPosition',
                    'Points', 'Laps']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def load_weather() -> pd.DataFrame:
    """載入天氣資料"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'weather.csv'))
    df['Time'] = pd.to_timedelta(df['Time'])
    numeric_cols = ['AirTemp', 'Humidity', 'Pressure', 'TrackTemp', 'WindDirection', 'WindSpeed']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Rainfall'] = df['Rainfall'].astype(bool)
    return df


def load_stints() -> pd.DataFrame:
    """載入輪胎 stint 資料"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'stints.csv'))
    numeric_cols = ['meeting_key', 'session_key', 'stint_number', 'driver_number',
                    'lap_start', 'lap_end', 'tyre_age_at_start']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def load_race_control() -> pd.DataFrame:
    """載入賽道控制訊息"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'race_control.csv'))
    return df


def load_telemetry(driver_code: str = 'VER') -> pd.DataFrame:
    """載入遙測資料"""
    file_path = os.path.join(RAW_DIR, f'telemetry_{driver_code}.csv')
    df = pd.read_csv(file_path)
    df['SessionTime'] = pd.to_timedelta(df['SessionTime'])
    df['Time'] = pd.to_timedelta(df['Time'])
    numeric_cols = ['Distance', 'RelativeDistance', 'RPM', 'Speed', 'nGear', 'Throttle',
                    'DRS', 'DistanceToDriverAhead', 'X', 'Y', 'Z']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    df['Brake'] = df['Brake'].astype(bool)
    return df


def load_schedule() -> pd.DataFrame:
    """載入賽程表"""
    df = pd.read_csv(os.path.join(RAW_DIR, 'schedule_2024.csv'))
    return df


def get_race_info() -> dict:
    """取得比賽基本資訊"""
    results = load_results()
    laps = load_laps()
    weather = load_weather()
    return {
        'event': '2024 Italian Grand Prix',
        'circuit': 'Monza',
        'date': '2024-09-01',
        'drivers': len(results),
        'finishers': len(results[results['Status'] == 'Finished']),
        'total_laps': int(laps['LapNumber'].max()),
        'weather': {
            'temp_min': float(weather['AirTemp'].min()),
            'temp_max': float(weather['AirTemp'].max()),
            'track_temp_min': float(weather['TrackTemp'].min()),
            'track_temp_max': float(weather['TrackTemp'].max()),
            'rain': bool(weather['Rainfall'].any()),
        },
        'winner': results.loc[results['Position'] == 1, 'FullName'].values[0],
        'winner_team': results.loc[results['Position'] == 1, 'TeamName'].values[0],
    }


if __name__ == '__main__':
    info = get_race_info()
    print(f"{info['event']} @ {info['circuit']}")
    print(f"Drivers: {info['drivers']}, Finishers: {info['finishers']}, Laps: {info['total_laps']}")
    print(f"Winner: {info['winner']} ({info['winner_team']})")