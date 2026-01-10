#!/usr/bin/env python3
"""
PCkeibaレース結果データの包括的分析スクリプト

目的:
1) 枠順係数の高精度化（GLM/機械学習）
2) 上がり指数のペース補正値検証
3) 4つの指数の競馬場別上限下限確認

データソース: PCkeiba全期間データ（約320万頭）
作成日: 2026-01-10
作成者: NAR-AI-YOSO Project
"""

import pandas as pd
import numpy as np
from pathlib import Path
from collections import defaultdict
import json

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
print(f'ファイル: {INPUT_CSV}')

# サンプリング読み込み（メモリ効率化）
# 全データ（320万行）をサンプリング（10%＝32万行）
SAMPLE_RATE = 0.1
print(f'  サンプリングレート: {SAMPLE_RATE * 100:.0f}%')

df = pd.read_csv(INPUT_CSV, low_memory=False, 
                 skiprows=lambda i: i > 0 and np.random.rand() > SAMPLE_RATE)
print(f'\n✅ データ読み込み完了: {len(df):,} 行（サンプリング済み）')

# ============================
# データクレンジング
# ============================
print('\n🧹 データクレンジング中...')

# 必須カラムの確認
required_cols = ['race_id', 'keibajo_code', 'kyori', 'wakuban', 'chakujun', 
                 'tosu', 'soha_time_sec', 'kohan_3f_sec', 'tansho_flag', 'fukusho_flag']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    raise ValueError(f'❌ 必須カラムが不足: {missing_cols}')

# 数値型への変換
df['keibajo_code'] = pd.to_numeric(df['keibajo_code'], errors='coerce')
df['kyori'] = pd.to_numeric(df['kyori'], errors='coerce')
df['wakuban'] = pd.to_numeric(df['wakuban'], errors='coerce')
df['chakujun'] = pd.to_numeric(df['chakujun'], errors='coerce')
df['tosu'] = pd.to_numeric(df['tosu'], errors='coerce')
df['soha_time_sec'] = pd.to_numeric(df['soha_time_sec'], errors='coerce')
df['kohan_3f_sec'] = pd.to_numeric(df['kohan_3f_sec'], errors='coerce')
df['tansho_flag'] = pd.to_numeric(df['tansho_flag'], errors='coerce')
df['fukusho_flag'] = pd.to_numeric(df['fukusho_flag'], errors='coerce')

# コーナー順位の変換
for i in range(1, 5):
    col = f'corner_{i}'
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

# 異常値除外
df = df[df['wakuban'].between(1, 8)]
df = df[df['kyori'].between(800, 3000)]
df = df[df['tosu'] >= 3]
df = df[df['soha_time_sec'] > 0]
df = df[df['kohan_3f_sec'] > 0]

print(f'✅ クレンジング完了: {len(df):,} 行（有効データ）')

# ============================
# 基本統計量
# ============================
print('\n📊 基本統計量:')
print(f'  競馬場数: {df["keibajo_code"].nunique()}')
print(f'  距離種類: {df["kyori"].nunique()}')
print(f'  期間: {df["race_date"].min()} ~ {df["race_date"].max()}')
print(f'  平均出走頭数: {df["tosu"].mean():.1f}頭')

# 競馬場別レース数
keibajo_counts = df.groupby('keibajo_code').size().sort_values(ascending=False)
print(f'\n📍 競馬場別レース数（Top 10）:')
for keibajo_code, count in keibajo_counts.head(10).items():
    keibajo_name = df[df['keibajo_code'] == keibajo_code]['keibajo_name'].iloc[0]
    print(f'  {keibajo_name} ({keibajo_code}): {count:,}頭')

# ============================
# タスク1: 枠順係数の高精度再算出
# ============================
print('\n' + '='*60)
print('タスク1: 枠順係数の高精度再算出（GLM準備）')
print('='*60)

# 枠順別の的中率を競馬場×距離別に集計
wakuban_stats = df.groupby(['keibajo_code', 'kyori', 'wakuban']).agg({
    'race_id': 'count',  # サンプル数
    'tansho_flag': 'sum',  # 単勝的中数
    'fukusho_flag': 'sum'  # 複勝的中数
}).reset_index()

wakuban_stats.columns = ['keibajo_code', 'kyori', 'wakuban', 'sample_count', 
                         'tansho_hit_count', 'fukusho_hit_count']

# 的中率の計算
wakuban_stats['tansho_hit_rate'] = (wakuban_stats['tansho_hit_count'] / 
                                    wakuban_stats['sample_count'] * 100).round(2)
wakuban_stats['fukusho_hit_rate'] = (wakuban_stats['fukusho_hit_count'] / 
                                     wakuban_stats['sample_count'] * 100).round(2)

# 競馬場名をマージ
keibajo_names = df[['keibajo_code', 'keibajo_name']].drop_duplicates()
wakuban_stats = wakuban_stats.merge(keibajo_names, on='keibajo_code', how='left')

# 出力
output_csv = OUTPUT_DIR / 'pckeiba_wakuban_stats.csv'
wakuban_stats.to_csv(output_csv, index=False)
print(f'✅ 枠順別統計量を保存: {output_csv}')
print(f'  データ数: {len(wakuban_stats):,} 行')

# ============================
# タスク2: ペース補正値の検証
# ============================
print('\n' + '='*60)
print('タスク2: ペース補正値の検証（前半3F推定）')
print('='*60)

# 前半3Fタイムの推定（1200m以下はdirect_calculation）
df['zenhan_3f_estimated'] = df['soha_time_sec'] - df['kohan_3f_sec']

# ペースタイプの分類（簡易版：全体平均との比較）
kyori_zenhan_mean = df.groupby('kyori')['zenhan_3f_estimated'].mean().to_dict()
df['zenhan_3f_mean'] = df['kyori'].map(kyori_zenhan_mean)
df['pace_deviation'] = df['zenhan_3f_estimated'] - df['zenhan_3f_mean']

# ペース分類
def classify_pace(deviation):
    if pd.isna(deviation):
        return 'M'
    elif deviation < -0.8:  # 前半が速い（ハイペース）
        return 'H'
    elif deviation > 0.8:   # 前半が遅い（スローペース）
        return 'S'
    else:
        return 'M'

df['pace_type'] = df['pace_deviation'].apply(classify_pace)

# ペース別の後半3F平均
pace_stats = df.groupby('pace_type').agg({
    'kohan_3f_sec': ['mean', 'std', 'count']
}).round(2)

print('📊 ペース別の後半3F統計量:')
print(pace_stats)

# ペース補正値の妥当性検証
pace_correction_verification = df.groupby('pace_type').agg({
    'kohan_3f_sec': 'mean',
    'soha_time_sec': 'mean',
    'race_id': 'count'
}).round(2)

pace_correction_verification.columns = ['後半3F平均', '走破タイム平均', 'サンプル数']
print('\n📊 ペース補正値の妥当性検証:')
print(pace_correction_verification)

# 基準値（Mペース）との差分
m_kohan_3f = pace_correction_verification.loc['M', '後半3F平均']
pace_correction_verification['後半3F差分'] = (
    pace_correction_verification['後半3F平均'] - m_kohan_3f
).round(2)

print('\n✅ ペース別の後半3F差分（基準値Mとの比較）:')
print(pace_correction_verification[['後半3F差分', 'サンプル数']])

# 出力
output_csv = OUTPUT_DIR / 'pckeiba_pace_verification.csv'
pace_correction_verification.to_csv(output_csv)
print(f'\n✅ ペース検証結果を保存: {output_csv}')

# ============================
# タスク3: 4つの指数の競馬場別上限下限
# ============================
print('\n' + '='*60)
print('タスク3: 4つの指数の競馬場別上限下限')
print('='*60)

# 注: 実際の指数計算には core/index_calculator.py が必要
# ここでは基礎データの統計量のみを算出

index_ranges = df.groupby('keibajo_code').agg({
    'zenhan_3f_estimated': ['min', 'max', 'mean', 'std'],  # テン指数の基礎
    'kohan_3f_sec': ['min', 'max', 'mean', 'std'],         # 上がり指数の基礎
    'soha_time_sec': ['min', 'max', 'mean', 'std'],        # 全体タイム
    'kyori': ['min', 'max', 'mean']                         # 距離
}).round(2)

print('📊 競馬場別の基礎統計量:')
print(index_ranges.head(10))

# 出力
output_csv = OUTPUT_DIR / 'pckeiba_index_ranges.csv'
index_ranges.to_csv(output_csv)
print(f'\n✅ 指数範囲統計量を保存: {output_csv}')

# ============================
# サマリー
# ============================
print('\n' + '='*60)
print('📊 分析完了サマリー')
print('='*60)
print(f'✅ タスク1: 枠順別統計量 → {OUTPUT_DIR / "pckeiba_wakuban_stats.csv"}')
print(f'✅ タスク2: ペース検証結果 → {OUTPUT_DIR / "pckeiba_pace_verification.csv"}')
print(f'✅ タスク3: 指数範囲統計量 → {OUTPUT_DIR / "pckeiba_index_ranges.csv"}')
print('\n🎯 次のステップ:')
print('  1) GLMによる枠順係数の高精度化')
print('  2) ペース補正値の最終検証')
print('  3) ベイズ推定係数との比較')
print('\n✅ Phase 3 完了！')
