#!/usr/bin/env python3
"""
HQS 4指数の分布確認スクリプト（Windows用）

【目的】
各指数の値が10区切り・5区切りでどのように分布しているかを確認する

【使用方法】
python check_index_distribution_windows.py

【出力】
- 各指数の10区切り分布（-100～-90、-90～-80、...、90～100）
- 各指数の5区切り分布（-100～-95、-95～-90、...、95～100）
- CSV/JSON形式で保存
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
    """HQS 4指数を計算（実装準拠版）"""
    print("🔢 HQS 4指数計算開始（実装準拠版）...")
    
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
            
            # 前半3F推定
            if 'actual_ten_3f' in row and pd.notna(row['actual_ten_3f']):
                zenhan_3f = float(row['actual_ten_3f'])
            else:
                zenhan_3f = soha_time_sec - kohan_3f_sec
            
            # コーナー順位
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
            # 基準タイム（距離別）
            try:
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
            
            # 1. テン指数（Ten Index）
            ten_index = ((base_time - zenhan_3f)) * 10
            ten_index = max(-100, min(100, ten_index))
            
            # 2. 位置指数（Position Index）
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = ((base_position - avg_position) / tosu) * 100
            position_index = max(0, min(100, position_index))
            
            # 3. 上がり指数（Agari Index）
            agari_index = ((base_time - kohan_3f_sec)) * 10
            agari_index = max(-100, min(100, agari_index))
            
            # 4. ペース指数（Pace Index）
            pace_index = ten_index - agari_index
            pace_index = max(-100, min(100, pace_index))
            
            results.append({
                'race_id': row['race_id'],
                'umaban': row['umaban'],
                'chakujun': row['chakujun'],
                'tosu': tosu,
                'テン指数': ten_index,
                '位置指数': position_index,
                '上がり指数': agari_index,
                'ペース指数': pace_index
            })
            
        except Exception as e:
            continue
    
    result_df = pd.DataFrame(results)
    print(f"   指数計算完了: {len(result_df):,}頭\n")
    
    return result_df


# ============================
# 分布計算
# ============================

def calculate_distribution(df: pd.DataFrame, index_name: str, bin_size: int) -> dict:
    """指数の分布を計算"""
    values = df[index_name].dropna()
    
    # 範囲を決定
    if index_name == '位置指数':
        min_val = 0
        max_val = 100
    else:
        min_val = -100
        max_val = 100
    
    # ビンを作成
    bins = list(range(min_val, max_val + bin_size, bin_size))
    labels = [f"{bins[i]}～{bins[i+1]}" for i in range(len(bins)-1)]
    
    # ヒストグラム作成
    counts, _ = np.histogram(values, bins=bins)
    
    # パーセンテージ計算
    total = len(values)
    percentages = [(count / total * 100) if total > 0 else 0 for count in counts]
    
    # 結果を辞書形式で返す
    distribution = []
    for i, label in enumerate(labels):
        distribution.append({
            '範囲': label,
            '件数': int(counts[i]),
            '割合(%)': round(percentages[i], 2)
        })
    
    return {
        '指数名': index_name,
        '区切り': f'{bin_size}刻み',
        'データ数': total,
        '分布': distribution
    }


def print_distribution(dist: dict):
    """分布を表示"""
    print(f"\n{'='*80}")
    print(f"📊 {dist['指数名']} の分布（{dist['区切り']}）")
    print(f"{'='*80}")
    print(f"データ数: {dist['データ数']:,}頭\n")
    
    print(f"{'範囲':>15} {'件数':>12} {'割合(%)':>12}")
    print("-" * 80)
    
    for item in dist['分布']:
        print(f"{item['範囲']:>15} {item['件数']:>12,} {item['割合(%)']:>12.2f}")


# ============================
# メイン処理
# ============================

def main():
    print("=" * 100)
    print("📊 HQS 4指数の分布確認（10区切り・5区切り）")
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
    
    # 各指数の分布を計算
    index_names = ['テン指数', '位置指数', '上がり指数', 'ペース指数']
    
    # 10区切り
    print("\n" + "=" * 100)
    print("📊 10区切りの分布")
    print("=" * 100)
    
    distributions_10 = []
    for index_name in index_names:
        dist = calculate_distribution(df_with_indices, index_name, 10)
        distributions_10.append(dist)
        print_distribution(dist)
    
    # 5区切り
    print("\n" + "=" * 100)
    print("📊 5区切りの分布")
    print("=" * 100)
    
    distributions_5 = []
    for index_name in index_names:
        dist = calculate_distribution(df_with_indices, index_name, 5)
        distributions_5.append(dist)
        print_distribution(dist)
    
    # 出力ディレクトリ
    output_dir = os.path.dirname(data_path) if os.path.dirname(data_path) else '.'
    
    # 10区切りの結果を保存
    output_data_10 = []
    for dist in distributions_10:
        for item in dist['分布']:
            output_data_10.append({
                '指数名': dist['指数名'],
                '範囲': item['範囲'],
                '件数': item['件数'],
                '割合(%)': item['割合(%)']
            })
    
    df_10 = pd.DataFrame(output_data_10)
    csv_path_10 = os.path.join(output_dir, 'index_distribution_10.csv')
    json_path_10 = os.path.join(output_dir, 'index_distribution_10.json')
    df_10.to_csv(csv_path_10, index=False, encoding='utf-8-sig')
    df_10.to_json(json_path_10, orient='records', force_ascii=False, indent=2)
    
    # 5区切りの結果を保存
    output_data_5 = []
    for dist in distributions_5:
        for item in dist['分布']:
            output_data_5.append({
                '指数名': dist['指数名'],
                '範囲': item['範囲'],
                '件数': item['件数'],
                '割合(%)': item['割合(%)']
            })
    
    df_5 = pd.DataFrame(output_data_5)
    csv_path_5 = os.path.join(output_dir, 'index_distribution_5.csv')
    json_path_5 = os.path.join(output_dir, 'index_distribution_5.json')
    df_5.to_csv(csv_path_5, index=False, encoding='utf-8-sig')
    df_5.to_json(json_path_5, orient='records', force_ascii=False, indent=2)
    
    print("\n" + "=" * 100)
    print("✅ 結果保存完了")
    print("=" * 100)
    print(f"【10区切り】")
    print(f"CSV: {csv_path_10}")
    print(f"JSON: {json_path_10}")
    print(f"\n【5区切り】")
    print(f"CSV: {csv_path_5}")
    print(f"JSON: {json_path_5}")
    print("=" * 100)
    
    input("\n✅ HQS 4指数の分布確認完了！Enterで終了...")


if __name__ == '__main__':
    main()
