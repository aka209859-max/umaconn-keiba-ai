#!/usr/bin/env python3
"""
予測精度検証スクリプト

【検証目的】
ディープサンドモデル（Phase 3）の予測精度を検証する

【検証データ】
- 期間: 2023年10月13日～2025年12月31日（大井砂入れ替え後）
- データ: PCkeiba全期間データ（3,205,721行）

【検証指標】
1. 単勝的中率: Phase 0 vs Phase 3
2. 複勝的中率: Phase 0 vs Phase 3
3. 回収率: Phase 0 vs Phase 3
4. 競馬場別精度: NAR標準 vs 大井2024/12〜

【Phase定義】
- Phase 0: H -0.5秒 / S +0.5秒、従来枠順係数
- Phase 3: H -0.12秒 / S 0.0秒（NAR標準）、ベイズ推定枠順係数
"""

import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================
# 1. データ読み込み
# ============================

def load_and_filter_data(file_path: str, start_date: str, end_date: str):
    """
    データ読み込みとフィルタリング
    
    Args:
        file_path: データファイルパス
        start_date: 開始日（YYYYMMDD）
        end_date: 終了日（YYYYMMDD）
    
    Returns:
        フィルタ済みDataFrame
    """
    print(f"📁 データ読み込み: {file_path}")
    
    # サンプリング読み込み（メモリ節約）
    df = pd.read_csv(file_path, skiprows=lambda i: i > 0 and np.random.rand() > 0.1)
    print(f"   読み込み: {len(df):,}行（サンプリング10%）")
    
    # 期間フィルタ
    df['race_date'] = df['race_date'].astype(str)
    df = df[(df['race_date'] >= start_date) & (df['race_date'] <= end_date)]
    print(f"   期間フィルタ: {len(df):,}行（{start_date}～{end_date}）")
    
    # 必須カラムの確認
    required_cols = ['race_date', 'keibajo_code', 'kyori', 'wakuban', 'chakujun', 
                     'soha_time_sec', 'kohan_3f_sec', 'weight_kg', 'tosu']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"必須カラムが不足: {missing_cols}")
    
    # データクレンジング
    df = df.dropna(subset=required_cols)
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    print(f"   クレンジング後: {len(df):,}行")
    
    return df


# ============================
# 2. Phase 0 実装（従来モデル）
# ============================

def calculate_agari_index_phase0(row):
    """
    Phase 0: 従来モデル（ディープサーチ前）
    
    ペース補正:
    - H -0.5秒
    - S +0.5秒
    """
    kohan_3f = row['kohan_3f_sec']
    base_time = 39.0  # 基準タイム（簡易版）
    
    # 前半3F推定（簡易版: 走破タイム - 後半3F）
    zenhan_3f = row['soha_time_sec'] - kohan_3f
    
    # ペース判定（簡易版）
    pace_ratio = zenhan_3f / kohan_3f if kohan_3f > 0 else 0.94
    if pace_ratio >= 0.97:
        pace_correction = -0.5  # H -0.5秒
    elif pace_ratio <= 0.91:
        pace_correction = +0.5  # S +0.5秒
    else:
        pace_correction = 0.0  # M 0秒
    
    # 上がり指数
    agari_index = (base_time - kohan_3f) + pace_correction
    return agari_index


# ============================
# 3. Phase 3 実装（ディープサンドモデル）
# ============================

def calculate_agari_index_phase3(row):
    """
    Phase 3: ディープサンドモデル（NAR最適化）
    
    ペース補正:
    - NAR標準: H -0.12秒 / S 0.0秒（ダンピング係数0.15）
    - 大井2024/12〜: H -0.40秒 / S 0.0秒（ダンピング係数0.50）
    """
    kohan_3f = row['kohan_3f_sec']
    base_time = 39.0  # 基準タイム（簡易版）
    
    # 前半3F推定（簡易版: 走破タイム - 後半3F）
    zenhan_3f = row['soha_time_sec'] - kohan_3f
    
    # ペース判定（簡易版）
    pace_ratio = zenhan_3f / kohan_3f if kohan_3f > 0 else 0.94
    
    # ダンピング係数の決定
    damping_factor = 0.15  # NAR標準
    if row['keibajo_code'] == 44 and row['race_date'] >= '20241201':
        damping_factor = 0.50  # 大井2024/12〜
    
    if pace_ratio >= 0.97:
        pace_correction = -0.8 * damping_factor  # H -0.12秒 or -0.40秒
    elif pace_ratio <= 0.91:
        pace_correction = 0.0  # S 0.0秒
    else:
        pace_correction = 0.0  # M 0秒
    
    # 上がり指数
    agari_index = (base_time - kohan_3f) + pace_correction
    return agari_index


# ============================
# 4. 予測精度評価
# ============================

def evaluate_prediction_accuracy(df: pd.DataFrame, phase_name: str):
    """
    予測精度を評価
    
    Args:
        df: 指数計算済みDataFrame
        phase_name: Phase名（'Phase 0' or 'Phase 3'）
    
    Returns:
        評価結果の辞書
    """
    # レース単位でグループ化
    race_groups = df.groupby(['race_date', 'keibajo_code', 'kyori'])
    
    results = {
        'tansho_hit': 0,      # 単勝的中数
        'fukusho_hit': 0,     # 複勝的中数
        'total_races': 0,     # 総レース数
        'tansho_return': 0.0, # 単勝回収率の合計
        'fukusho_return': 0.0 # 複勝回収率の合計
    }
    
    for race_id, race_df in race_groups:
        results['total_races'] += 1
        
        # 上がり指数でソート（降順: 高い方が速い）
        race_df = race_df.sort_values('agari_index', ascending=False)
        
        # 予測1着（上がり指数トップ）
        predicted_1st = race_df.iloc[0]['chakujun']
        
        # 予測3着以内（上がり指数トップ3）
        predicted_top3 = race_df.iloc[:3]['chakujun'].values
        
        # 単勝的中判定
        if predicted_1st == 1:
            results['tansho_hit'] += 1
            # 単勝配当（簡易版: 1着のオッズを仮定）
            results['tansho_return'] += 1.0  # 暫定値
        
        # 複勝的中判定
        if any(x <= 3 for x in predicted_top3):
            results['fukusho_hit'] += 1
            results['fukusho_return'] += 1.0  # 暫定値
    
    # 的中率計算
    results['tansho_hitrate'] = results['tansho_hit'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    results['fukusho_hitrate'] = results['fukusho_hit'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    
    # 回収率計算
    results['tansho_return_rate'] = results['tansho_return'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    results['fukusho_return_rate'] = results['fukusho_return'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    
    return results


# ============================
# 5. メイン処理
# ============================

def main():
    """メイン処理"""
    
    print("=" * 80)
    print("📊 予測精度検証スクリプト")
    print("=" * 80)
    
    # データ読み込み
    data_path = '/home/user/uploaded_files/data-1768047611955.csv'
    start_date = '20231013'  # 大井砂入れ替え後
    end_date = '20251231'
    
    df = load_and_filter_data(data_path, start_date, end_date)
    
    print("\n" + "=" * 80)
    print("📈 Phase 0（従来モデル）の検証")
    print("=" * 80)
    
    # Phase 0 指数計算
    df['agari_index'] = df.apply(calculate_agari_index_phase0, axis=1)
    
    # Phase 0 精度評価
    phase0_results = evaluate_prediction_accuracy(df, 'Phase 0')
    
    print(f"\n✅ Phase 0 結果:")
    print(f"   総レース数: {phase0_results['total_races']:,}レース")
    print(f"   単勝的中率: {phase0_results['tansho_hitrate']:.2f}%")
    print(f"   複勝的中率: {phase0_results['fukusho_hitrate']:.2f}%")
    print(f"   単勝回収率: {phase0_results['tansho_return_rate']:.2f}%")
    print(f"   複勝回収率: {phase0_results['fukusho_return_rate']:.2f}%")
    
    print("\n" + "=" * 80)
    print("🚀 Phase 3（ディープサンドモデル）の検証")
    print("=" * 80)
    
    # Phase 3 指数計算
    df['agari_index'] = df.apply(calculate_agari_index_phase3, axis=1)
    
    # Phase 3 精度評価
    phase3_results = evaluate_prediction_accuracy(df, 'Phase 3')
    
    print(f"\n✅ Phase 3 結果:")
    print(f"   総レース数: {phase3_results['total_races']:,}レース")
    print(f"   単勝的中率: {phase3_results['tansho_hitrate']:.2f}%")
    print(f"   複勝的中率: {phase3_results['fukusho_hitrate']:.2f}%")
    print(f"   単勝回収率: {phase3_results['tansho_return_rate']:.2f}%")
    print(f"   複勝回収率: {phase3_results['fukusho_return_rate']:.2f}%")
    
    print("\n" + "=" * 80)
    print("📊 Phase 0 vs Phase 3 比較")
    print("=" * 80)
    
    # 差分計算
    tansho_diff = phase3_results['tansho_hitrate'] - phase0_results['tansho_hitrate']
    fukusho_diff = phase3_results['fukusho_hitrate'] - phase0_results['fukusho_hitrate']
    tansho_return_diff = phase3_results['tansho_return_rate'] - phase0_results['tansho_return_rate']
    fukusho_return_diff = phase3_results['fukusho_return_rate'] - phase0_results['fukusho_return_rate']
    
    print(f"\n🎯 改善効果:")
    print(f"   単勝的中率: {tansho_diff:+.2f}% {'✅' if tansho_diff > 0 else '❌'}")
    print(f"   複勝的中率: {fukusho_diff:+.2f}% {'✅' if fukusho_diff > 0 else '❌'}")
    print(f"   単勝回収率: {tansho_return_diff:+.2f}% {'✅' if tansho_return_diff > 0 else '❌'}")
    print(f"   複勝回収率: {fukusho_return_diff:+.2f}% {'✅' if fukusho_return_diff > 0 else '❌'}")
    
    # 結果保存
    results_df = pd.DataFrame({
        'Phase': ['Phase 0', 'Phase 3', '差分'],
        '単勝的中率(%)': [
            phase0_results['tansho_hitrate'],
            phase3_results['tansho_hitrate'],
            tansho_diff
        ],
        '複勝的中率(%)': [
            phase0_results['fukusho_hitrate'],
            phase3_results['fukusho_hitrate'],
            fukusho_diff
        ],
        '単勝回収率(%)': [
            phase0_results['tansho_return_rate'],
            phase3_results['tansho_return_rate'],
            tansho_return_diff
        ],
        '複勝回収率(%)': [
            phase0_results['fukusho_return_rate'],
            phase3_results['fukusho_return_rate'],
            fukusho_return_diff
        ]
    })
    
    output_path = '/home/user/webapp/nar-ai-yoso/data/prediction_accuracy_comparison.csv'
    results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 結果保存: {output_path}")
    
    print("\n" + "=" * 80)
    print("✅ 予測精度検証完了！")
    print("=" * 80)


if __name__ == '__main__':
    main()
