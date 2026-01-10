#!/usr/bin/env python3
"""
各指数の値の範囲確認スクリプト（Windows用）

【目的】
NAR-SI3.0 の各指数（上がり指数、位置指数、テン指数、ペース指数）の
最小値、最大値、平均値、中央値、分布を確認する

【使用方法】
python check_index_range_windows.py

【出力】
- 各指数の統計情報（最小値、最大値、平均、中央値、標準偏差）
- 分位点（5%, 25%, 50%, 75%, 95%）
- ヒストグラム情報
"""

import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================
# 設定
# ============================

# デフォルト設定
DEFAULT_DATA_PATH = r'E:\UmaData\nar-analytics-python-v2\data-1768047611955.csv'
DEFAULT_START_DATE = '20231013'
DEFAULT_END_DATE = '20251231'
DEFAULT_SAMPLE_RATE = 0.1

# ============================
# データ読み込み
# ============================

def load_and_filter_data(file_path: str, start_date: str, end_date: str, sample_rate: float = 0.1):
    """データ読み込みとフィルタリング"""
    print(f"📁 データ読み込み: {file_path}")
    
    # サンプリング読み込み
    df = pd.read_csv(file_path, skiprows=lambda i: i > 0 and np.random.rand() > sample_rate)
    print(f"   読み込み: {len(df):,}行（サンプリング{int(sample_rate*100)}%）")
    
    # 期間フィルタ
    df['race_date'] = df['race_date'].astype(str)
    df = df[(df['race_date'] >= start_date) & (df['race_date'] <= end_date)]
    print(f"   期間フィルタ: {len(df):,}行（{start_date}～{end_date}）")
    
    # データクレンジング
    df = df.dropna(subset=['race_date', 'keibajo_code', 'kyori', 'wakuban', 'chakujun', 
                            'soha_time_sec', 'kohan_3f_sec', 'weight_kg', 'tosu'])
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    print(f"   クレンジング後: {len(df):,}行\n")
    
    return df


# ============================
# 各指数計算（簡易版）
# ============================

def calculate_all_indices_simple(df: pd.DataFrame) -> pd.DataFrame:
    """NAR-SI3.0 の全指数を計算（簡易版）"""
    print("🔢 NAR-SI3.0 全指数計算開始（簡易版）...")
    
    results = []
    
    for idx, row in df.iterrows():
        try:
            # 基本情報
            keibajo_code = int(row['keibajo_code'])
            kyori = int(row['kyori'])
            wakuban = int(row['wakuban'])
            tosu = int(row['tosu'])
            
            # タイム情報
            soha_time_sec = float(row['soha_time_sec'])
            kohan_3f_sec = float(row['kohan_3f_sec'])
            
            # 前半3F推定（3パターン）
            if 'actual_ten_3f' in row and pd.notna(row['actual_ten_3f']):
                # データに実測値がある場合はそれを使用
                zenhan_3f = float(row['actual_ten_3f'])
            else:
                # 距離別の推定
                if kyori < 1200:
                    # 1200m未満: 走破タイム - 後半3F（実際は2Fなどになるが許容）
                    zenhan_3f = soha_time_sec - kohan_3f_sec
                elif kyori == 1200:
                    # 1200m: 走破タイム - 後半3F
                    zenhan_3f = soha_time_sec - kohan_3f_sec
                else:
                    # 1201m以上: ten_3f_estimator.py と同じロジック（簡易版）
                    # 基準タイム + スピード指数補正の簡易実装
                    # 注: 本実装ではten_3f_estimator.pyを使用すべきだが、
                    # データ確認用スクリプトなので簡易版を使用
                    if kyori <= 1400:
                        ratio = 0.26  # 前半3F ≈ 走破タイムの26%
                    elif kyori <= 1600:
                        ratio = 0.22
                    elif kyori <= 1800:
                        ratio = 0.22
                    elif kyori <= 2000:
                        ratio = 0.17
                    else:
                        ratio = 0.16
                    zenhan_3f = soha_time_sec * ratio
                    # 物理的制約
                    zenhan_3f = max(30.0, min(45.0, zenhan_3f))
            
            # コーナー順位
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
            # 基準タイム（競馬場・距離別）
            # デフォルト値として39.0を使用（取得失敗時）
            try:
                # 競馬場・距離別の基準タイムを取得
                if kyori <= 1200:
                    base_time = 37.5
                elif kyori <= 1400:
                    base_time = 38.0
                elif kyori <= 1600:
                    base_time = 39.0
                elif kyori <= 1800:
                    base_time = 39.5
                elif kyori <= 2000:
                    base_time = 40.0
                else:  # 2000m超
                    base_time = 40.5
            except:
                base_time = 39.0
            
            # 1. 上がり指数（実装準拠: ×1、補正は省略）
            agari_index = (base_time - kohan_3f_sec)
            agari_index = max(-100, min(100, agari_index))
            
            # 2. 位置指数（コーナー4角順位ベース）
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = ((base_position - avg_position) / tosu) * 100
            position_index = max(0, min(100, position_index))  # 範囲制限のみ追加
            
            # 3. テン指数（実装準拠: ×1、補正は省略）
            ten_index = (base_time - zenhan_3f)
            ten_index = max(-100, min(100, ten_index))
            
            # 4. ペース指数（実装準拠: 平均、補正は省略）
            pace_index = (ten_index + agari_index) / 2
            pace_index = max(-100, min(100, pace_index))
            
            results.append({
                'race_id': row['race_id'],
                'umaban': row['umaban'],
                'chakujun': row['chakujun'],
                'tosu': tosu,
                '上がり指数': agari_index,
                '位置指数': position_index,
                'テン指数': ten_index,
                'ペース指数': pace_index
            })
            
        except Exception as e:
            continue
    
    result_df = pd.DataFrame(results)
    print(f"   指数計算完了: {len(result_df):,}頭\n")
    
    return result_df


# ============================
# 統計情報計算
# ============================

def calculate_statistics(df: pd.DataFrame, index_name: str) -> dict:
    """指数の統計情報を計算"""
    values = df[index_name].dropna()
    
    stats = {
        '指数名': index_name,
        'データ数': len(values),
        '最小値': values.min(),
        '最大値': values.max(),
        '平均値': values.mean(),
        '中央値': values.median(),
        '標準偏差': values.std(),
        '5%点': values.quantile(0.05),
        '25%点': values.quantile(0.25),
        '50%点': values.quantile(0.50),
        '75%点': values.quantile(0.75),
        '95%点': values.quantile(0.95)
    }
    
    return stats


def print_statistics(stats: dict):
    """統計情報を表示"""
    print(f"\n{'='*80}")
    print(f"📊 {stats['指数名']} の統計情報")
    print(f"{'='*80}")
    print(f"データ数    : {stats['データ数']:,}頭")
    print(f"\n【基本統計量】")
    print(f"最小値      : {stats['最小値']:>10.2f}")
    print(f"最大値      : {stats['最大値']:>10.2f}")
    print(f"平均値      : {stats['平均値']:>10.2f}")
    print(f"中央値      : {stats['中央値']:>10.2f}")
    print(f"標準偏差    : {stats['標準偏差']:>10.2f}")
    print(f"\n【分位点】")
    print(f"5%点       : {stats['5%点']:>10.2f}  （下位5%の馬はこの値以下）")
    print(f"25%点      : {stats['25%点']:>10.2f}  （下位25%の馬はこの値以下）")
    print(f"50%点      : {stats['50%点']:>10.2f}  （中央値）")
    print(f"75%点      : {stats['75%点']:>10.2f}  （上位25%の馬はこの値以上）")
    print(f"95%点      : {stats['95%点']:>10.2f}  （上位5%の馬はこの値以上）")
    print(f"\n【値の範囲】")
    print(f"幅          : {stats['最大値'] - stats['最小値']:>10.2f}  （最大値 - 最小値）")


# ============================
# メイン処理
# ============================

def main():
    print("=" * 100)
    print("📊 NAR-SI3.0 各指数の値の範囲確認（Windows用）")
    print("=" * 100)
    
    # 対話式設定
    data_path = input(f"データファイルパス（空白でデフォルト）: ").strip() or DEFAULT_DATA_PATH
    start_date = input(f"開始日（YYYYMMDD、空白で{DEFAULT_START_DATE}）: ").strip() or DEFAULT_START_DATE
    end_date = input(f"終了日（YYYYMMDD、空白で{DEFAULT_END_DATE}）: ").strip() or DEFAULT_END_DATE
    sample_rate_str = input(f"サンプリング率（0.0～1.0、空白で{DEFAULT_SAMPLE_RATE}）: ").strip()
    sample_rate = float(sample_rate_str) if sample_rate_str else DEFAULT_SAMPLE_RATE
    
    print("\n" + "=" * 100)
    print(f"データパス: {data_path}")
    print(f"期間: {start_date} ～ {end_date}")
    print(f"サンプリング率: {int(sample_rate*100)}%")
    print("=" * 100 + "\n")
    
    # データ読み込み
    df = load_and_filter_data(data_path, start_date, end_date, sample_rate)
    
    # 指数計算
    df_with_indices = calculate_all_indices_simple(df)
    
    # 各指数の統計情報を計算・表示
    index_names = ['上がり指数', '位置指数', 'テン指数', 'ペース指数']
    all_stats = []
    
    for index_name in index_names:
        stats = calculate_statistics(df_with_indices, index_name)
        all_stats.append(stats)
        print_statistics(stats)
    
    # サマリーテーブル
    print("\n" + "=" * 100)
    print("📋 全指数サマリー")
    print("=" * 100)
    print(f"{'指数名':<12} {'最小値':>10} {'最大値':>10} {'平均値':>10} {'中央値':>10} {'標準偏差':>10}")
    print("-" * 100)
    
    for stats in all_stats:
        print(f"{stats['指数名']:<12} "
              f"{stats['最小値']:>10.2f} "
              f"{stats['最大値']:>10.2f} "
              f"{stats['平均値']:>10.2f} "
              f"{stats['中央値']:>10.2f} "
              f"{stats['標準偏差']:>10.2f}")
    
    # CSV/JSON出力
    output_dir = os.path.dirname(data_path) if os.path.dirname(data_path) else '.'
    
    summary_df = pd.DataFrame(all_stats)
    csv_path = os.path.join(output_dir, 'index_range_summary.csv')
    json_path = os.path.join(output_dir, 'index_range_summary.json')
    
    summary_df.to_csv(csv_path, index=False, encoding='utf-8-sig')
    summary_df.to_json(json_path, orient='records', force_ascii=False, indent=2)
    
    print("\n" + "=" * 100)
    print("✅ 結果保存完了")
    print("=" * 100)
    print(f"CSV: {csv_path}")
    print(f"JSON: {json_path}")
    print("=" * 100)
    
    input("\n✅ 各指数の値の範囲確認完了！Enterで終了...")


if __name__ == '__main__':
    main()
