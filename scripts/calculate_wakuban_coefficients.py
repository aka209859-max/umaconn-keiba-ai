#!/usr/bin/env python3
"""
位置指数の枠順係数を実データから算出

目的:
- 全競馬場×距離×枠番別の単勝/複勝的中率から枠順係数を算出
- 現行の固定係数（waku_correction * 15）を実データベースの係数に置き換える

入力:
- data-1768033229370.csv（全競馬場×距離×枠番別の的中率）

出力:
- wakuban_coefficients.csv（競馬場×距離×枠番別の係数）
- wakuban_coefficients.json（プログラムで使用する形式）

計算式:
- 平均的中率 = (単勝的中率 + 複勝的中率) / 2
- 基準値 = 各競馬場×距離の全枠平均的中率
- 枠順係数 = (平均的中率 - 基準値) × スケール係数

Author: NAR-AI-YOSO Project
Date: 2026-01-10
"""

import pandas as pd
import json
from pathlib import Path
from collections import defaultdict

# ============================
# 設定
# ============================

INPUT_CSV = '/home/user/uploaded_files/data-1768033229370.csv'
OUTPUT_CSV = '/home/user/webapp/nar-ai-yoso/data/wakuban_coefficients.csv'
OUTPUT_JSON = '/home/user/webapp/nar-ai-yoso/data/wakuban_coefficients.json'

# スケール係数（位置指数への影響度）
# 現行: waku_correction * 15
# 新方式: (的中率差 - 基準値) × SCALE_FACTOR
SCALE_FACTOR = 1.5  # 1%の的中率差 = 1.5点の指数差

# ============================
# データ読み込み
# ============================

print("📂 データ読み込み中...")
df = pd.read_csv(INPUT_CSV)

print(f"✅ データ読み込み完了: {len(df)} 行")
print(f"   競馬場数: {df['keibajo_code'].nunique()}")
print(f"   距離数: {df['distance'].nunique()}")
print(f"   枠番数: {df['waku'].nunique()}")

# ============================
# 平均的中率の計算
# ============================

print("\n📊 平均的中率を計算中...")

# 単勝と複勝の平均的中率
df['avg_hit_rate'] = (df['tansho_hit_rate'] + df['fukusho_hit_rate']) / 2

print(f"✅ 平均的中率の計算完了")
print(f"   最小: {df['avg_hit_rate'].min():.2f}%")
print(f"   最大: {df['avg_hit_rate'].max():.2f}%")
print(f"   平均: {df['avg_hit_rate'].mean():.2f}%")

# ============================
# 競馬場×距離別の基準値を計算
# ============================

print("\n🎯 基準値（各競馬場×距離の全枠平均）を計算中...")

baseline = df.groupby(['keibajo_code', 'distance'])['avg_hit_rate'].mean().reset_index()
baseline.columns = ['keibajo_code', 'distance', 'baseline_rate']

print(f"✅ 基準値の計算完了: {len(baseline)} 組み合わせ")

# データをマージ
df = df.merge(baseline, on=['keibajo_code', 'distance'], how='left')

# ============================
# 枠順係数の計算
# ============================

print("\n🔧 枠順係数を計算中...")

# 係数 = (平均的中率 - 基準値) × スケール係数
df['wakuban_coefficient'] = (df['avg_hit_rate'] - df['baseline_rate']) * SCALE_FACTOR

print(f"✅ 枠順係数の計算完了")
print(f"   最小: {df['wakuban_coefficient'].min():.2f}")
print(f"   最大: {df['wakuban_coefficient'].max():.2f}")
print(f"   平均: {df['wakuban_coefficient'].mean():.2f}")

# ============================
# CSV出力
# ============================

print(f"\n💾 CSV出力中: {OUTPUT_CSV}")

output_df = df[[
    'keibajo_code', 'keibajo_name', 'distance', 'waku',
    'sample_count', 'tansho_hit_rate', 'fukusho_hit_rate',
    'avg_hit_rate', 'baseline_rate', 'wakuban_coefficient'
]].copy()

# ディレクトリ作成
Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

output_df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"✅ CSV出力完了: {len(output_df)} 行")

# ============================
# JSON出力（プログラム用）
# ============================

print(f"\n💾 JSON出力中: {OUTPUT_JSON}")

# 構造: {keibajo_code: {kyori: {wakuban: coefficient}}}
coefficients = defaultdict(lambda: defaultdict(dict))

for _, row in df.iterrows():
    keibajo = str(int(row['keibajo_code']))
    kyori = int(row['distance'])
    waku = int(row['waku'])
    coef = round(float(row['wakuban_coefficient']), 2)
    
    coefficients[keibajo][kyori][waku] = coef

# JSON書き込み
with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
    json.dump(coefficients, f, ensure_ascii=False, indent=2)

print(f"✅ JSON出力完了")

# ============================
# 統計サマリー
# ============================

print("\n" + "="*60)
print("📊 枠順係数の統計サマリー（競馬場別）")
print("="*60)

summary = df.groupby('keibajo_name').agg({
    'wakuban_coefficient': ['min', 'max', 'mean', 'std']
}).round(2)

print(summary)

print("\n" + "="*60)
print("📊 枠順係数の統計サマリー（距離別）")
print("="*60)

summary_distance = df.groupby('distance').agg({
    'wakuban_coefficient': ['min', 'max', 'mean', 'std']
}).round(2)

print(summary_distance)

print("\n" + "="*60)
print("🎯 特徴的な枠番係数（トップ10）")
print("="*60)

top10 = output_df.nlargest(10, 'wakuban_coefficient')[
    ['keibajo_name', 'distance', 'waku', 'wakuban_coefficient', 'avg_hit_rate']
]
print(top10.to_string(index=False))

print("\n" + "="*60)
print("⚠️ 注意が必要な枠番係数（ワースト10）")
print("="*60)

worst10 = output_df.nsmallest(10, 'wakuban_coefficient')[
    ['keibajo_name', 'distance', 'waku', 'wakuban_coefficient', 'avg_hit_rate']
]
print(worst10.to_string(index=False))

print("\n" + "="*60)
print("✅ 完了！")
print("="*60)
print(f"📁 出力ファイル:")
print(f"   - {OUTPUT_CSV}")
print(f"   - {OUTPUT_JSON}")
print("="*60)
