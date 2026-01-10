#!/usr/bin/env python3
"""
枠順係数のベイズ縮小推定（Bayesian Shrinkage Estimation）

目的:
- サンプル数を考慮した統計的に信頼性の高い枠順係数を算出
- 過剰適合（Overfitting）を防止
- 信頼区間（95% CI）付き推定

理論的背景:
- Beta分布による事後推定
- James-Stein推定量による縮小推定
- サンプル数が少ない場合、全体平均に近づける

Author: NAR-AI-YOSO Project
Date: 2026-01-10
"""

import pandas as pd
import numpy as np
from scipy.stats import beta
import json
from pathlib import Path
from collections import defaultdict

# ============================
# 設定
# ============================

INPUT_CSV = '/home/user/uploaded_files/data-1768033229370.csv'
OUTPUT_CSV = '/home/user/webapp/nar-ai-yoso/data/wakuban_coefficients_bayesian.csv'
OUTPUT_JSON = '/home/user/webapp/nar-ai-yoso/data/wakuban_coefficients_bayesian.json'

# スケール係数（位置指数への影響度）
SCALE_FACTOR = 1.5  # 1%の的中率差 = 1.5点の指数差

# ベイズ推定のハイパーパラメータ
OVERALL_HIT_RATE = 0.10  # 全体平均10%と仮定
ALPHA_PRIOR = OVERALL_HIT_RATE * 100  # α = 10
BETA_PRIOR = (1 - OVERALL_HIT_RATE) * 100  # β = 90

# 統計的有意性の閾値
SIGNIFICANCE_LEVEL = 0.05  # 5%有意水準

# ============================
# ベイズ推定関数
# ============================

def bayesian_shrinkage(k, n, alpha_prior, beta_prior):
    """
    ベイズ縮小推定による的中率の事後期待値
    
    Args:
        k: 的中数（successes）
        n: サンプル数（trials）
        alpha_prior: 事前分布のαパラメータ
        beta_prior: 事前分布のβパラメータ
    
    Returns:
        posterior_mean: 事後期待値（真の的中率の推定値）
        ci_lower: 95%信頼区間の下限
        ci_upper: 95%信頼区間の上限
        shrinkage_rate: 縮小率（0%〜100%）
    """
    # 事後分布のパラメータ
    alpha_post = alpha_prior + k
    beta_post = beta_prior + (n - k)
    
    # 事後期待値（縮小推定）
    posterior_mean = alpha_post / (alpha_post + beta_post)
    
    # 95%信頼区間
    ci_lower = beta.ppf(0.025, alpha_post, beta_post)
    ci_upper = beta.ppf(0.975, alpha_post, beta_post)
    
    # 縮小率の計算
    # サンプル数が多いほど観測値に近づく（縮小率0%）
    # サンプル数が少ないほど事前分布に近づく（縮小率100%）
    mle = k / n if n > 0 else 0.5  # 最尤推定（Maximum Likelihood Estimation）
    prior_mean = alpha_prior / (alpha_prior + beta_prior)
    
    if mle == posterior_mean:
        shrinkage_rate = 0.0
    else:
        shrinkage_rate = abs(posterior_mean - mle) / abs(prior_mean - mle) * 100 if mle != prior_mean else 100.0
    
    return posterior_mean, ci_lower, ci_upper, shrinkage_rate

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
# ベイズ推定による枠順係数の計算
# ============================

print("\n🔬 ベイズ推定を実行中...")

# 結果を格納するリスト
results = []

for idx, row in df.iterrows():
    # 的中数とサンプル数を計算
    avg_hit_rate_decimal = row['avg_hit_rate'] / 100
    k = row['sample_count'] * avg_hit_rate_decimal  # 的中数
    n = row['sample_count']  # サンプル数
    
    # ベイズ推定
    posterior_mean, ci_lower, ci_upper, shrinkage_rate = bayesian_shrinkage(
        k, n, ALPHA_PRIOR, BETA_PRIOR
    )
    
    # 基準値との差分を係数化
    baseline = row['baseline_rate'] / 100
    coefficient = (posterior_mean - baseline) * SCALE_FACTOR * 100
    
    # 統計的有意性の判定
    # 基準値が95%信頼区間に含まれる場合、統計的に有意でないため係数を0に
    is_significant = not (ci_lower < baseline < ci_upper)
    
    if not is_significant:
        coefficient = 0.0
    
    # 結果を格納
    results.append({
        'keibajo_code': row['keibajo_code'],
        'keibajo_name': row['keibajo_name'],
        'distance': row['distance'],
        'waku': row['waku'],
        'sample_count': row['sample_count'],
        'tansho_hit_rate': row['tansho_hit_rate'],
        'fukusho_hit_rate': row['fukusho_hit_rate'],
        'avg_hit_rate': row['avg_hit_rate'],
        'baseline_rate': row['baseline_rate'],
        'mle_hit_rate': (k / n * 100) if n > 0 else 0,  # 最尤推定
        'bayesian_hit_rate': posterior_mean * 100,  # ベイズ推定
        'ci_lower': ci_lower * 100,
        'ci_upper': ci_upper * 100,
        'shrinkage_rate': shrinkage_rate,
        'is_significant': is_significant,
        'wakuban_coefficient': coefficient
    })

# DataFrameに変換
df_bayesian = pd.DataFrame(results)

print(f"✅ ベイズ推定の完了")
print(f"   最小係数: {df_bayesian['wakuban_coefficient'].min():.2f}")
print(f"   最大係数: {df_bayesian['wakuban_coefficient'].max():.2f}")
print(f"   平均係数: {df_bayesian['wakuban_coefficient'].mean():.2f}")
print(f"   統計的有意な係数の数: {df_bayesian['is_significant'].sum()} / {len(df_bayesian)}")

# ============================
# CSV出力
# ============================

print(f"\n💾 CSV出力中: {OUTPUT_CSV}")

# ディレクトリ作成
Path(OUTPUT_CSV).parent.mkdir(parents=True, exist_ok=True)

df_bayesian.to_csv(OUTPUT_CSV, index=False, encoding='utf-8-sig')
print(f"✅ CSV出力完了: {len(df_bayesian)} 行")

# ============================
# JSON出力（プログラム用）
# ============================

print(f"\n💾 JSON出力中: {OUTPUT_JSON}")

# 構造: {keibajo_code: {kyori: {wakuban: coefficient}}}
coefficients = defaultdict(lambda: defaultdict(dict))

for _, row in df_bayesian.iterrows():
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
print("📊 ベイズ推定の統計サマリー（現行方式との比較）")
print("="*60)

# 元のデータ（現行方式）を読み込み
df_old = pd.read_csv('/home/user/webapp/nar-ai-yoso/data/wakuban_coefficients.csv')

# 比較
comparison = pd.DataFrame({
    '指標': ['最小係数', '最大係数', '平均係数', '標準偏差', '極端な係数(|係数|>10)の数', '係数=0の数'],
    '現行方式': [
        df_old['wakuban_coefficient'].min(),
        df_old['wakuban_coefficient'].max(),
        df_old['wakuban_coefficient'].mean(),
        df_old['wakuban_coefficient'].std(),
        (df_old['wakuban_coefficient'].abs() > 10).sum(),
        (df_old['wakuban_coefficient'] == 0).sum()
    ],
    'ベイズ推定': [
        df_bayesian['wakuban_coefficient'].min(),
        df_bayesian['wakuban_coefficient'].max(),
        df_bayesian['wakuban_coefficient'].mean(),
        df_bayesian['wakuban_coefficient'].std(),
        (df_bayesian['wakuban_coefficient'].abs() > 10).sum(),
        (df_bayesian['wakuban_coefficient'] == 0).sum()
    ]
})

print(comparison.to_string(index=False))

print("\n" + "="*60)
print("🔍 サンプル数による縮小率の統計")
print("="*60)

# サンプル数でビン分け
df_bayesian['sample_bin'] = pd.cut(
    df_bayesian['sample_count'], 
    bins=[0, 100, 500, 1000, 5000, 10000],
    labels=['<100', '100-500', '500-1000', '1000-5000', '5000+']
)

shrinkage_summary = df_bayesian.groupby('sample_bin').agg({
    'shrinkage_rate': ['mean', 'std'],
    'sample_count': 'count'
}).round(2)

print(shrinkage_summary)

print("\n" + "="*60)
print("✅ 完了！")
print("="*60)
print(f"📁 出力ファイル:")
print(f"   - {OUTPUT_CSV}")
print(f"   - {OUTPUT_JSON}")
print("="*60)
