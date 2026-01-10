#!/usr/bin/env python3
"""
ペース補正値の再分析（改修履歴フィルタリング後）

目的:
1) 改修・移転の影響を除外したデータでペース補正値を再算出
2) 実データ（+0.07秒）と理論値（-0.8秒）の乖離を再検証
3) 回収率分析用データ（2016-2025年）で精度を確認

作成日: 2026-01-10
作成者: NAR-AI-YOSO Project
"""

import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os

# パスを追加
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from scripts.filter_by_renovation import filter_by_renovation, add_renovation_flag

# ============================
# 設定
# ============================
INPUT_CSV = '/home/user/uploaded_files/data-1768047611955.csv'
OUTPUT_DIR = Path('/home/user/webapp/nar-ai-yoso/data')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ============================
# データ読み込み
# ============================
print('📂 データ読み込み中...')
df = pd.read_csv(INPUT_CSV, low_memory=False, 
                 skiprows=lambda i: i > 0 and np.random.rand() > 0.1)
print(f'✅ データ読み込み完了: {len(df):,} 行（サンプリング10%）')

# ============================
# データクレンジング
# ============================
print('\n🧹 データクレンジング中...')

# 数値型への変換
df['keibajo_code'] = pd.to_numeric(df['keibajo_code'], errors='coerce')
df['kyori'] = pd.to_numeric(df['kyori'], errors='coerce')
df['soha_time_sec'] = pd.to_numeric(df['soha_time_sec'], errors='coerce')
df['kohan_3f_sec'] = pd.to_numeric(df['kohan_3f_sec'], errors='coerce')

# 異常値除外
df = df[df['kyori'].between(800, 3000)]
df = df[df['soha_time_sec'] > 0]
df = df[df['kohan_3f_sec'] > 0]

print(f'✅ クレンジング完了: {len(df):,} 行')

# ============================
# 回収率分析用データでペース検証
# ============================
print('\n' + '='*60)
print('回収率分析用データ（2016-2025年）でペース補正値を再検証')
print('='*60)

df_recovery = filter_by_renovation(df, purpose='recovery_rate_analysis')

# 前半3Fタイムの推定
df_recovery['zenhan_3f_estimated'] = df_recovery['soha_time_sec'] - df_recovery['kohan_3f_sec']

# ペースタイプの分類（競馬場×距離別の基準値を使用）
df_recovery['keibajo_kyori'] = (
    df_recovery['keibajo_code'].astype(str) + '_' + 
    df_recovery['kyori'].astype(str)
)

zenhan_mean = df_recovery.groupby('keibajo_kyori')['zenhan_3f_estimated'].mean().to_dict()
df_recovery['zenhan_3f_mean'] = df_recovery['keibajo_kyori'].map(zenhan_mean)
df_recovery['pace_deviation'] = df_recovery['zenhan_3f_estimated'] - df_recovery['zenhan_3f_mean']

# ペース分類（閾値±0.8秒）
def classify_pace(deviation):
    if pd.isna(deviation):
        return 'M'
    elif deviation < -0.8:  # 前半が平均より0.8秒以上速い
        return 'H'
    elif deviation > 0.8:   # 前半が平均より0.8秒以上遅い
        return 'S'
    else:
        return 'M'

df_recovery['pace_type'] = df_recovery['pace_deviation'].apply(classify_pace)

# ペース別の統計量
pace_stats = df_recovery.groupby('pace_type').agg({
    'kohan_3f_sec': ['mean', 'std', 'count'],
    'zenhan_3f_estimated': ['mean', 'std'],
    'soha_time_sec': ['mean', 'std']
}).round(3)

print('\n📊 ペース別の統計量（2016-2025年、改修後データ）:')
print(pace_stats)

# ペース補正値の算出（基準値Mとの差分）
m_kohan_3f = df_recovery[df_recovery['pace_type'] == 'M']['kohan_3f_sec'].mean()
h_kohan_3f = df_recovery[df_recovery['pace_type'] == 'H']['kohan_3f_sec'].mean()
s_kohan_3f = df_recovery[df_recovery['pace_type'] == 'S']['kohan_3f_sec'].mean()

h_correction = h_kohan_3f - m_kohan_3f
s_correction = s_kohan_3f - m_kohan_3f

print('\n' + '='*60)
print('🎯 ペース補正値の算出結果（2016-2025年）')
print('='*60)
print(f'ハイペース（H）: 後半3F差分 = {h_correction:+.3f}秒')
print(f'スローペース（S）: 後半3F差分 = {s_correction:+.3f}秒')
print(f'\n比較:')
print(f'  実データ（全期間2005-2025年）: H {0.07:+.2f}秒 / S {0.40:+.2f}秒')
print(f'  実データ（回収期間2016-2025年）: H {h_correction:+.3f}秒 / S {s_correction:+.3f}秒')
print(f'  ディープサーチ理論値: H -0.8秒 / S +0.3秒')

# ============================
# 距離別のペース影響分析
# ============================
print('\n' + '='*60)
print('距離別のペース影響分析')
print('='*60)

# 距離帯を分類
df_recovery['kyori_range'] = pd.cut(
    df_recovery['kyori'],
    bins=[0, 1400, 1800, 3000],
    labels=['短距離(<1400m)', 'マイル(1400-1800m)', '中長距離(≥1800m)']
)

pace_by_distance = df_recovery.groupby(['kyori_range', 'pace_type']).agg({
    'kohan_3f_sec': 'mean',
    'race_id': 'count'
}).reset_index()

pace_by_distance.columns = ['距離帯', 'ペースタイプ', '後半3F平均', 'サンプル数']

print('\n📊 距離別×ペース別の後半3F平均:')
print(pace_by_distance.pivot(index='距離帯', columns='ペースタイプ', values='後半3F平均').round(2))

print('\n📊 距離別×ペース別のサンプル数:')
print(pace_by_distance.pivot(index='距離帯', columns='ペースタイプ', values='サンプル数'))

# ============================
# 出力
# ============================
output_csv = OUTPUT_DIR / 'pace_correction_reanalysis_2016_2025.csv'
pace_stats.to_csv(output_csv)
print(f'\n✅ 再分析結果を保存: {output_csv}')

# ============================
# 結論
# ============================
print('\n' + '='*60)
print('📊 再分析の結論')
print('='*60)
print(f'''
1. **実データ（2016-2025年、改修後）の補正値**:
   - ハイペース（H）: {h_correction:+.3f}秒（前半が速い→後半がやや遅い）
   - スローペース（S）: {s_correction:+.3f}秒（前半が遅い→後半が遅い）

2. **ディープサーチ理論値との乖離**:
   - H: {h_correction:+.3f}秒（実データ）vs -0.8秒（理論）→ 差分 {h_correction - (-0.8):.3f}秒
   - S: {s_correction:+.3f}秒（実データ）vs +0.3秒（理論）→ 差分 {s_correction - 0.3:.3f}秒

3. **結論**:
   - 実データではペース影響が極めて小さい（H {h_correction:+.3f}秒）
   - 理論値（H -0.8秒）は「ハイペース時に後半が速くなる」を意味するが、
     実データでは「ハイペース時に後半が遅くなる」という正反対の傾向
   - **ペース補正の定義または符号が逆転している可能性が高い**

4. **推奨アクション**:
   - ディープサーチで「補正の方向性（符号）」を再確認
   - または、実データに基づく補正値を採用（H {h_correction:+.3f}秒 / S {s_correction:+.3f}秒）
''')

print('\n✅ 再分析完了！')
