"""Test degradation chart logic v2"""
from src.dashboard import get_tyre_degradation
import plotly.express as px

deg = get_tyre_degradation()
deg_clean = deg[(deg['degradation_rate'] > 0) & (deg['laps_analyzed'] >= 8)].copy()
if len(deg_clean) < 5:
    deg_clean = deg[(deg['degradation_rate'] > 0) & (deg['laps_analyzed'] >= 5)].copy()
deg_clean['confidence'] = deg_clean['r2'].apply(lambda x: '高' if x >= 0.3 else ('中' if x >= 0.1 else '低'))

print(f'原始資料: {len(deg)} 筆')
print(f'過濾後: {len(deg_clean)} 筆')
print()
top_deg = deg_clean.sort_values('degradation_rate', ascending=False).head(20)
print('=== 圖表資料 (top 20) ===')
print(top_deg[['driver','compound','degradation_rate','r2','laps_analyzed','confidence']].to_string(index=False))
print()

fig = px.bar(
    top_deg,
    x='driver', y='degradation_rate',
    color='compound',
    pattern_shape='confidence',
    barmode='group',
    title='輪胎衰退率分析',
    labels={'driver': '車手', 'degradation_rate': '衰退率 (秒/圈)', 'compound': '胎種'},
    hover_data={'r2': ':.3f', 'laps_analyzed': True, 'confidence': True},
    text='degradation_rate',
)
fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
fig.update_layout(height=450, margin=dict(l=10, r=20, t=40, b=100), xaxis_tickangle=-45)
print('圖表建立成功')
print(f'data traces: {len(fig.data)}')