#!/usr/bin/env python3
"""
各指数ごとの予測精度検証スクリプト（Windows用）

【検証目的】
NAR-SI3.0 の各指数（上がり指数、位置指数、テン指数、ペース指数）ごとに
単勝/複勝的中率と回収率を検証する

【使用方法】
python validate_each_index_accuracy_windows.py

【必要なファイル】
- PCkeibaデータCSV
- 競馬場コードマスター

【検証指標】
1. 単勝的中率: 各指数で予測1着が実際に1着になった割合
2. 複勝的中率: 各指数で予測3着以内が実際に3着以内になった割合
3. 単勝回収率: 単勝的中時の配当を仮定した回収率
4. 複勝回収率: 複勝的中時の配当を仮定した回収率
"""

import os
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ============================
# 1. データ読み込み
# ============================

def load_and_filter_data(file_path: str, start_date: str, end_date: str, sample_rate: float = 0.1):
    """
    データ読み込みとフィルタリング
    
    Args:
        file_path: データファイルパス
        start_date: 開始日（YYYYMMDD）
        end_date: 終了日（YYYYMMDD）
        sample_rate: サンプリング率（0.1 = 10%）
    
    Returns:
        フィルタ済みDataFrame
    """
    print(f"📁 データ読み込み: {file_path}")
    
    # サンプリング読み込み（メモリ節約）
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
    print(f"   クレンジング後: {len(df):,}行")
    
    return df


# ============================
# 2. 各指数計算（簡易版）
# ============================

def calculate_all_indices_simple(df: pd.DataFrame) -> pd.DataFrame:
    """
    NAR-SI3.0 の全指数を計算（簡易版）
    
    Args:
        df: 入力DataFrame
    
    Returns:
        指数計算済みDataFrame
    """
    print("\n📊 NAR-SI3.0 全指数計算開始（簡易版）...")
    
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
            
            # 前半3F推定（実測値または推定値）
            if 'actual_ten_3f' in row and pd.notna(row['actual_ten_3f']):
                zenhan_3f = float(row['actual_ten_3f'])
            else:
                zenhan_3f = soha_time_sec - kohan_3f_sec
            
            # コーナー情報（欠損値は0で埋める）
            corner_4 = int(row.get('corner_4', 0)) if pd.notna(row.get('corner_4')) else 0
            
            # 1. 上がり指数計算（簡易版）
            base_kohan_3f = 39.0  # 基準後半3F
            agari_index = (base_kohan_3f - kohan_3f_sec) * 10
            
            # 2. 位置指数計算（簡易版）
            base_time = kyori / 300.0  # 基準タイム（秒）
            position_index = (base_time - soha_time_sec) * 10
            
            # 3. テン指数計算（簡易版）
            base_zenhan_3f = 36.0  # 基準前半3F
            ten_index = (base_zenhan_3f - zenhan_3f) * 10
            
            # 4. ペース指数計算（簡易版）
            pace_index = ten_index - agari_index
            
            # 結果格納
            results.append({
                'race_id': f"{row['race_date']}_{keibajo_code}_{kyori}",
                'race_date': row['race_date'],
                'keibajo_code': keibajo_code,
                'kyori': kyori,
                'umaban': int(row.get('umaban', 0)) if pd.notna(row.get('umaban')) else 0,
                'wakuban': wakuban,
                'chakujun': int(row['chakujun']),
                'tosu': tosu,
                'agari_index': agari_index,
                'position_index': position_index,
                'ten_index': ten_index,
                'pace_index': pace_index,
                'soha_time_sec': soha_time_sec,
                'kohan_3f_sec': kohan_3f_sec,
                'zenhan_3f': zenhan_3f
            })
            
        except Exception as e:
            # エラーは無視して次へ
            continue
    
    result_df = pd.DataFrame(results)
    print(f"✅ 指数計算完了: {len(result_df):,}頭")
    
    return result_df


# ============================
# 3. 各指数ごとの予測精度評価
# ============================

def evaluate_index_accuracy(df: pd.DataFrame, index_name: str, ascending: bool = False):
    """
    各指数ごとの予測精度を評価
    
    Args:
        df: 指数計算済みDataFrame
        index_name: 評価する指数名（'agari_index', 'position_index', 'ten_index', 'pace_index'）
        ascending: ソート順（False: 降順、True: 昇順）
    
    Returns:
        評価結果の辞書
    """
    # レース単位でグループ化
    race_groups = df.groupby('race_id')
    
    results = {
        'index_name': index_name,
        'tansho_hit': 0,      # 単勝的中数
        'fukusho_hit': 0,     # 複勝的中数
        'total_races': 0,     # 総レース数
        'tansho_return': 0.0, # 単勝回収率の合計
        'fukusho_return': 0.0 # 複勝回収率の合計
    }
    
    for race_id, race_df in race_groups:
        results['total_races'] += 1
        
        # 指数でソート
        race_df = race_df.sort_values(index_name, ascending=ascending)
        
        # 予測1着（指数トップ）
        if len(race_df) == 0:
            continue
        
        predicted_1st_chakujun = race_df.iloc[0]['chakujun']
        
        # 予測3着以内（指数トップ3）
        predicted_top3_chakujun = race_df.iloc[:min(3, len(race_df))]['chakujun'].values
        
        # 単勝的中判定
        if predicted_1st_chakujun == 1:
            results['tansho_hit'] += 1
            # 単勝配当（簡易版: 平均オッズ3.0倍と仮定）
            results['tansho_return'] += 3.0
        
        # 複勝的中判定
        if any(x <= 3 for x in predicted_top3_chakujun):
            results['fukusho_hit'] += 1
            # 複勝配当（簡易版: 平均オッズ1.5倍と仮定）
            results['fukusho_return'] += 1.5
    
    # 的中率計算
    results['tansho_hitrate'] = results['tansho_hit'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    results['fukusho_hitrate'] = results['fukusho_hit'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    
    # 回収率計算
    results['tansho_return_rate'] = results['tansho_return'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    results['fukusho_return_rate'] = results['fukusho_return'] / results['total_races'] * 100 if results['total_races'] > 0 else 0.0
    
    return results


# ============================
# 4. メイン処理
# ============================

def main():
    """メイン処理"""
    
    print("=" * 100)
    print("📊 NAR-SI3.0 各指数ごとの予測精度検証（Windows用）")
    print("=" * 100)
    
    # 設定
    data_path = input("データファイルパス（空白でデフォルト）: ").strip()
    if not data_path:
        data_path = r"E:\UmaData\data-1768047611955.csv"
    
    start_date = input("開始日（YYYYMMDD、空白で20231013）: ").strip()
    if not start_date:
        start_date = "20231013"
    
    end_date = input("終了日（YYYYMMDD、空白で20251231）: ").strip()
    if not end_date:
        end_date = "20251231"
    
    sample_rate_input = input("サンプリング率（0.0～1.0、空白で0.1）: ").strip()
    if not sample_rate_input:
        sample_rate = 0.1
    else:
        sample_rate = float(sample_rate_input)
    
    print("\n" + "=" * 100)
    print(f"データパス: {data_path}")
    print(f"期間: {start_date} ～ {end_date}")
    print(f"サンプリング率: {int(sample_rate * 100)}%")
    print("=" * 100)
    
    # データ読み込み
    df = load_and_filter_data(data_path, start_date, end_date, sample_rate)
    
    # 全指数計算（簡易版）
    df_indices = calculate_all_indices_simple(df)
    
    if len(df_indices) == 0:
        print("\n❌ エラー: 指数計算結果が0件です")
        return
    
    print("\n" + "=" * 100)
    print("📈 各指数ごとの予測精度評価")
    print("=" * 100)
    
    # 各指数の評価
    indices_config = [
        {'name': 'agari_index', 'label': '上がり指数', 'ascending': False},  # 高い方が速い
        {'name': 'position_index', 'label': '位置指数', 'ascending': False},  # 高い方が速い
        {'name': 'ten_index', 'label': 'テン指数', 'ascending': False},        # 高い方が速い
        {'name': 'pace_index', 'label': 'ペース指数', 'ascending': False}      # 高い方が速い
    ]
    
    all_results = []
    
    for config in indices_config:
        print(f"\n{'='*100}")
        print(f"🎯 {config['label']} の予測精度")
        print(f"{'='*100}")
        
        result = evaluate_index_accuracy(df_indices, config['name'], config['ascending'])
        
        print(f"\n✅ {config['label']} 結果:")
        print(f"   総レース数: {result['total_races']:,}レース")
        print(f"   単勝的中数: {result['tansho_hit']:,}レース")
        print(f"   複勝的中数: {result['fukusho_hit']:,}レース")
        print(f"   単勝的中率: {result['tansho_hitrate']:.2f}%")
        print(f"   複勝的中率: {result['fukusho_hitrate']:.2f}%")
        print(f"   単勝回収率: {result['tansho_return_rate']:.2f}%")
        print(f"   複勝回収率: {result['fukusho_return_rate']:.2f}%")
        
        all_results.append({
            '指数名': config['label'],
            '総レース数': result['total_races'],
            '単勝的中数': result['tansho_hit'],
            '単勝的中率(%)': round(result['tansho_hitrate'], 2),
            '複勝的中数': result['fukusho_hit'],
            '複勝的中率(%)': round(result['fukusho_hitrate'], 2),
            '単勝回収率(%)': round(result['tansho_return_rate'], 2),
            '複勝回収率(%)': round(result['fukusho_return_rate'], 2)
        })
    
    # 結果をDataFrameに変換
    results_df = pd.DataFrame(all_results)
    
    print("\n" + "=" * 100)
    print("📊 各指数の予測精度比較")
    print("=" * 100)
    print(results_df.to_string(index=False))
    
    # 結果保存
    output_dir = os.path.dirname(data_path)
    output_path = os.path.join(output_dir, 'index_accuracy_comparison.csv')
    results_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 結果保存: {output_path}")
    
    # JSON形式でも保存
    json_output_path = os.path.join(output_dir, 'index_accuracy_comparison.json')
    results_df.to_json(json_output_path, orient='records', force_ascii=False, indent=2)
    print(f"💾 結果保存（JSON）: {json_output_path}")
    
    print("\n" + "=" * 100)
    print("✅ 予測精度検証完了！")
    print("=" * 100)
    
    # ベスト指数を表示
    best_tansho = results_df.loc[results_df['単勝的中率(%)'].idxmax()]
    best_fukusho = results_df.loc[results_df['複勝的中率(%)'].idxmax()]
    
    print(f"\n🏆 ベスト指数:")
    print(f"   単勝的中率: {best_tansho['指数名']} ({best_tansho['単勝的中率(%)']}%)")
    print(f"   複勝的中率: {best_fukusho['指数名']} ({best_fukusho['複勝的中率(%)']}%)")
    
    input("\n完了しました。Enterキーを押して終了してください...")


if __name__ == '__main__':
    main()
