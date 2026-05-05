"""
F1 數據分析專案 — 天氣分析模組
"""
import pandas as pd
import numpy as np
from .data_loader import load_weather, load_laps


def get_weather_timeline() -> pd.DataFrame:
    """天氣隨時間變化"""
    weather = load_weather()
    weather['Time_minutes'] = weather['Time'].dt.total_seconds() / 60
    return weather


def get_track_temp_effect() -> pd.DataFrame:
    """賽道溫度對圈速的影響"""
    weather = load_weather()
    laps = load_laps()
    laps = laps[laps['IsAccurate'] == True].copy()
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()

    # 將天氣資料與圈速對齊（取每一圈開始時最近的天氣記錄）
    laps['LapStartTime_sec'] = laps['LapStartTime'].dt.total_seconds()
    weather['Time_sec'] = weather['Time'].dt.total_seconds()

    # 合併：取每圈開始前最近的天氣記錄
    idx = pd.merge_asof(
        laps.sort_values('LapStartTime_sec'),
        weather.sort_values('Time_sec'),
        left_on='LapStartTime_sec', right_on='Time_sec',
        direction='backward'
    )
    return idx[['LapNumber', 'Driver', 'LapTime_seconds', 'AirTemp', 'TrackTemp',
                'Humidity', 'Rainfall']].sort_values(['Driver', 'LapNumber']).reset_index(drop=True)


def get_weather_summary() -> dict:
    """天氣摘要"""
    weather = load_weather()
    return {
        'air_temp': {
            'min': float(weather['AirTemp'].min()),
            'max': float(weather['AirTemp'].max()),
            'avg': float(weather['AirTemp'].mean()),
        },
        'track_temp': {
            'min': float(weather['TrackTemp'].min()),
            'max': float(weather['TrackTemp'].max()),
            'avg': float(weather['TrackTemp'].mean()),
        },
        'humidity': {
            'min': float(weather['Humidity'].min()),
            'max': float(weather['Humidity'].max()),
            'avg': float(weather['Humidity'].mean()),
        },
        'pressure': {
            'min': float(weather['Pressure'].min()),
            'max': float(weather['Pressure'].max()),
        },
        'rainfall': bool(weather['Rainfall'].any()),
        'wind_speed': {
            'avg': float(weather['WindSpeed'].mean()),
            'max': float(weather['WindSpeed'].max()),
        },
        'records_count': len(weather),
    }


if __name__ == '__main__':
    ws = get_weather_summary()
    print(f"氣溫: {ws['air_temp']['min']:.1f} ~ {ws['air_temp']['max']:.1f}°C")
    print(f"賽道溫度: {ws['track_temp']['min']:.1f} ~ {ws['track_temp']['max']:.1f}°C")
    print(f"濕度: {ws['humidity']['min']:.0f} ~ {ws['humidity']['max']:.0f}%")
    print(f"降雨: {'有' if ws['rainfall'] else '無'}")
    print(f"風速: {ws['wind_speed']['avg']:.1f} m/s (最大 {ws['wind_speed']['max']:.1f} m/s)")