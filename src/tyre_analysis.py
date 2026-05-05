"""
F1 數據分析專案 — 輪胎策略與衰退分析模組
"""
import pandas as pd
import numpy as np
from .data_loader import load_laps, load_stints, load_results


def get_tyre_strategy() -> pd.DataFrame:
    """每位車手的輪胎策略摘要"""
    stints = load_stints()
    results = load_results()
    summary_rows = []
    for drv_num, group in stints.groupby('driver_number'):
        group = group.sort_values('stint_number')
        compounds = []
        stint_lengths = []
        total_laps = 0
        for _, s in group.iterrows():
            length = int(s['lap_end'] - s['lap_start'] + 1)
            compounds.append(str(s['compound']))
            stint_lengths.append(length)
            total_laps += length
        n_stops = int(group['stint_number'].max()) - 1
        # 查車手名稱
        drv_info = results[results['DriverNumber'] == drv_num]
        abb = drv_info['Abbreviation'].values[0] if len(drv_info) > 0 else f'#{drv_num}'
        final_pos = drv_info['Position'].values[0] if len(drv_info) > 0 else None
        summary_rows.append({
            'driver': abb,
            'driver_number': int(drv_num),
            'n_stops': n_stops,
            'stops_label': f"{n_stops}-stop",
            'compounds': ' -> '.join(compounds),
            'stint_laps': stint_lengths,
            'total_laps': total_laps,
            'strategy': f"{' -> '.join(f'{c}({l})' for c, l in zip(compounds, stint_lengths))}",
            'final_position': final_pos,
        })
    return pd.DataFrame(summary_rows).sort_values('final_position').reset_index(drop=True)


def get_tyre_degradation(compound: str = None) -> pd.DataFrame:
    """計算輪胎衰退率（每圈衰退多少秒）"""
    laps = load_laps()
    laps = laps[laps['IsAccurate'] == True].copy()
    if compound:
        laps = laps[laps['Compound'] == compound]
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()

    # 對每位車手 × 每個 stint 做線性迴歸
    results = []
    for (driver, stint, compound_name), group in laps.groupby(['Driver', 'Stint', 'Compound']):
        if len(group) < 4:  # 太少圈不計算
            continue
        x = group['TyreLife'].values.reshape(-1, 1)
        y = group['LapTime_seconds'].values
        if np.std(x) == 0:
            continue
        slope, intercept = np.polyfit(x.flatten(), y, 1)
        results.append({
            'driver': driver,
            'stint': int(stint),
            'compound': str(compound_name),
            'degradation_rate': float(slope),  # 秒/圈
            'intercept': float(intercept),  # 新胎預測圈速
            'laps_analyzed': len(group),
            'r2': float(np.corrcoef(x.flatten(), y)[0, 1] ** 2) if len(group) > 2 else 0,
        })

    return pd.DataFrame(results).sort_values('degradation_rate') if results else pd.DataFrame()


def get_compound_comparison() -> pd.DataFrame:
    """不同胎種的圈速比較"""
    laps = load_laps()
    laps = laps[laps['IsAccurate'] == True]
    laps['LapTime_seconds'] = laps['LapTime'].dt.total_seconds()
    stats = laps.groupby(['Driver', 'Compound']).agg(
        avg_laptime=('LapTime_seconds', 'mean'),
        min_laptime=('LapTime_seconds', 'min'),
        max_laptime=('LapTime_seconds', 'max'),
        std_laptime=('LapTime_seconds', 'std'),
        laps=('LapNumber', 'count'),
        avg_tyre_life=('TyreLife', 'mean'),
    ).reset_index()
    return stats


def simulate_pit_strategy(driver: str, pit_lap: int, base_laptime: float,
                          undercut_gain: float = 0.3, deg_rate: float = 0.08) -> dict:
    """
    模擬不同進站策略對總時間的影響
    """
    laps = load_laps()
    dr_laps = laps[(laps['Driver'] == driver) & (laps['IsAccurate'] == True)].copy()
    total_laps = int(dr_laps['LapNumber'].max())

    pit_time_loss = 22.0  # 進站損失時間（約 22 秒）
    results = []

    for n_stops in range(1, 4):  # 1 停、2 停、3 停
        if n_stops == 1:
            pit_laps = [total_laps // 2]
        elif n_stops == 2:
            pit_laps = [total_laps // 3, total_laps * 2 // 3]
        else:
            pit_laps = [total_laps // 4, total_laps // 2, total_laps * 3 // 4]

        total_time = 0.0
        current_tyre_life = 1
        for lap in range(1, total_laps + 1):
            # 進站
            if lap in pit_laps:
                total_time += pit_time_loss
                current_tyre_life = 1  # 換新胎
            # 圈速（隨輪胎衰退變慢）
            lap_time = base_laptime + deg_rate * current_tyre_life
            total_time += lap_time
            current_tyre_life += 1

        results.append({
            'n_stops': n_stops,
            'total_time_seconds': total_time,
            'pit_laps': pit_laps,
            'total_minutes': total_time / 60,
        })

    return {'driver': driver, 'total_laps': total_laps, 'pit_loss_sec': pit_time_loss, 'scenarios': results}


if __name__ == '__main__':
    print("=== 輪胎策略 ===")
    strat = get_tyre_strategy()
    print(strat[['driver', 'strategy', 'n_stops']].to_string(index=False))
    print()
    print("=== 輪胎衰退率 (SOFT) ===")
    deg = get_tyre_degradation('SOFT')
    if len(deg) > 0:
        print(deg[['driver', 'compound', 'degradation_rate']].head(10).to_string(index=False))