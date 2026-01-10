#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4指数の出力範囲分析スクリプト

目的:
- テン指数、位置指数、上がり指数、ペース指数の実データにおける上限・下限を確認
- 競馬場別、距離別、クラス別の出力範囲を可視化
- ビン付け（得点化）のための最適な区間を決定

実行例:
    python scripts/analyze_index_ranges.py --db umatabi.db --output reports/index_ranges.csv
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.index_calculator import calculate_all_indexes

# デフォルトの競馬場コード（全14場）
KEIBAJO_CODES = [30, 35, 36, 40, 41, 42, 43, 44, 45, 46, 47, 50, 54, 55]

# デフォルトの距離帯
KYORI_RANGES = [1000, 1200, 1400, 1600, 1800, 2000, 2100, 2400]

# クラスコード（仮定）
GRADE_CODES = ['A', 'B', 'C', 'D', 'E', '一般']

def load_race_data(db_path: str, limit: int = None) -> pd.DataFrame:
    """
    データベースからレースデータを読み込み
    
    Args:
        db_path: データベースファイルのパス
        limit: 読み込むレコード数の上限（None=全件）
    
    Returns:
        pd.DataFrame: レースデータ
    """
    conn = sqlite3.connect(db_path)
    
    limit_clause = f"LIMIT {limit}" if limit else ""
    
    query = f"""
    SELECT 
        keibajo_code,
        kyori,
        grade_code,
        zenhan_3f,
        kohan_3f,
        soha_time,
        corner_1,
        corner_2,
        corner_3,
        corner_4,
        babajotai_code_dirt,
        furi_code,
        wakuban,
        kinryo,
        bataiju,
        tosu,
        kakutei_chakujun,
        tansho_odds
    FROM races
    WHERE zenhan_3f > 0 AND kohan_3f > 0 AND soha_time > 0
    {limit_clause}
    """
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    print(f"✅ データ読み込み完了: {len(df):,}レース")
    return df

def calculate_indexes_for_all(df: pd.DataFrame) -> pd.DataFrame:
    """
    全レースの4指数を計算
    
    Args:
        df: レースデータ
    
    Returns:
        pd.DataFrame: 4指数を追加したデータフレーム
    """
    results = []
    
    for idx, row in df.iterrows():
        if (idx + 1) % 1000 == 0:
            print(f"  処理中... {idx + 1:,} / {len(df):,} ({(idx+1)/len(df)*100:.1f}%)")
        
        try:
            horse_data = {
                'zenhan_3f': row['zenhan_3f'],
                'kohan_3f': row['kohan_3f'],
                'soha_time': row['soha_time'],
                'corner_1': row['corner_1'],
                'corner_2': row['corner_2'],
                'corner_3': row['corner_3'],
                'corner_4': row['corner_4'],
                'kyori': row['kyori'],
                'babajotai_code_dirt': row['babajotai_code_dirt'],
                'keibajo_code': row['keibajo_code'],
                'furi_code': row.get('furi_code', '00'),
                'wakuban': row.get('wakuban', 0),
                'tosu': row.get('tosu', 12),
                'kinryo': row.get('kinryo', 54.0),
                'bataiju': row.get('bataiju', 460.0)
            }
            
            race_info = {
                'grade_code': row.get('grade_code', 'E')
            }
            
            result = calculate_all_indexes(horse_data, race_info)
            
            results.append({
                'keibajo_code': row['keibajo_code'],
                'kyori': row['kyori'],
                'grade_code': row.get('grade_code', 'E'),
                'ten_index': result['ten_index'],
                'position_index': result['position_index'],
                'agari_index': result['agari_index'],
                'pace_index': result['pace_index'],
                'pace_type': result.get('pace_type', 'M'),
                'kakutei_chakujun': row.get('kakutei_chakujun', 99),
                'tansho_odds': row.get('tansho_odds', 0.0)
            })
        except Exception as e:
            print(f"  ⚠️ 行{idx}でエラー: {e}")
            continue
    
    return pd.DataFrame(results)

def analyze_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """
    指数の範囲を分析
    
    Args:
        df: 4指数を含むデータフレーム
    
    Returns:
        pd.DataFrame: 統計サマリー
    """
    # 全体統計
    overall_stats = {
        'segment': '全体',
        'keibajo_code': 'ALL',
        'kyori': 'ALL',
        'grade_code': 'ALL',
        'count': len(df),
        'ten_min': df['ten_index'].min(),
        'ten_max': df['ten_index'].max(),
        'ten_mean': df['ten_index'].mean(),
        'ten_std': df['ten_index'].std(),
        'pos_min': df['position_index'].min(),
        'pos_max': df['position_index'].max(),
        'pos_mean': df['position_index'].mean(),
        'pos_std': df['position_index'].std(),
        'agari_min': df['agari_index'].min(),
        'agari_max': df['agari_index'].max(),
        'agari_mean': df['agari_index'].mean(),
        'agari_std': df['agari_index'].std(),
        'pace_min': df['pace_index'].min(),
        'pace_max': df['pace_index'].max(),
        'pace_mean': df['pace_index'].mean(),
        'pace_std': df['pace_index'].std()
    }
    
    stats_list = [overall_stats]
    
    # 競馬場別統計
    for keibajo in df['keibajo_code'].unique():
        subset = df[df['keibajo_code'] == keibajo]
        stats_list.append({
            'segment': '競馬場別',
            'keibajo_code': keibajo,
            'kyori': 'ALL',
            'grade_code': 'ALL',
            'count': len(subset),
            'ten_min': subset['ten_index'].min(),
            'ten_max': subset['ten_index'].max(),
            'ten_mean': subset['ten_index'].mean(),
            'ten_std': subset['ten_index'].std(),
            'pos_min': subset['position_index'].min(),
            'pos_max': subset['position_index'].max(),
            'pos_mean': subset['position_index'].mean(),
            'pos_std': subset['position_index'].std(),
            'agari_min': subset['agari_index'].min(),
            'agari_max': subset['agari_index'].max(),
            'agari_mean': subset['agari_index'].mean(),
            'agari_std': subset['agari_index'].std(),
            'pace_min': subset['pace_index'].min(),
            'pace_max': subset['pace_index'].max(),
            'pace_mean': subset['pace_index'].mean(),
            'pace_std': subset['pace_index'].std()
        })
    
    # 距離別統計
    for kyori in df['kyori'].unique():
        subset = df[df['kyori'] == kyori]
        if len(subset) < 50:  # サンプル数が少ない場合はスキップ
            continue
        stats_list.append({
            'segment': '距離別',
            'keibajo_code': 'ALL',
            'kyori': kyori,
            'grade_code': 'ALL',
            'count': len(subset),
            'ten_min': subset['ten_index'].min(),
            'ten_max': subset['ten_index'].max(),
            'ten_mean': subset['ten_index'].mean(),
            'ten_std': subset['ten_index'].std(),
            'pos_min': subset['position_index'].min(),
            'pos_max': subset['position_index'].max(),
            'pos_mean': subset['position_index'].mean(),
            'pos_std': subset['position_index'].std(),
            'agari_min': subset['agari_index'].min(),
            'agari_max': subset['agari_index'].max(),
            'agari_mean': subset['agari_index'].mean(),
            'agari_std': subset['agari_index'].std(),
            'pace_min': subset['pace_index'].min(),
            'pace_max': subset['pace_index'].max(),
            'pace_mean': subset['pace_index'].mean(),
            'pace_std': subset['pace_index'].std()
        })
    
    return pd.DataFrame(stats_list)

def suggest_bins(df: pd.DataFrame) -> dict:
    """
    ビン付けの提案
    
    Args:
        df: 4指数を含むデータフレーム
    
    Returns:
        dict: 各指数のビン区間提案
    """
    suggestions = {}
    
    for index_name in ['ten_index', 'position_index', 'agari_index', 'pace_index']:
        data = df[index_name].dropna()
        
        # パーセンタイル法（10分位）
        percentiles = np.percentile(data, [10, 20, 30, 40, 50, 60, 70, 80, 90])
        
        # 等間隔法
        min_val = data.min()
        max_val = data.max()
        equal_bins = np.linspace(min_val, max_val, 11)
        
        suggestions[index_name] = {
            'min': float(min_val),
            'max': float(max_val),
            'mean': float(data.mean()),
            'std': float(data.std()),
            'percentile_bins': percentiles.tolist(),
            'equal_bins': equal_bins.tolist()
        }
    
    return suggestions

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='4指数の出力範囲を分析')
    parser.add_argument('--db', type=str, default='umatabi.db', help='データベースファイルのパス')
    parser.add_argument('--output', type=str, default='reports/index_ranges.csv', help='出力CSVファイルのパス')
    parser.add_argument('--limit', type=int, default=None, help='処理するレース数の上限')
    
    args = parser.parse_args()
    
    print("="*60)
    print("4指数の出力範囲分析")
    print("="*60)
    
    # データ読み込み
    print("\n[1/4] データ読み込み中...")
    df_raw = load_race_data(args.db, limit=args.limit)
    
    # 4指数計算
    print("\n[2/4] 4指数を計算中...")
    df_indexes = calculate_indexes_for_all(df_raw)
    
    # 範囲分析
    print("\n[3/4] 範囲分析中...")
    df_stats = analyze_ranges(df_indexes)
    
    # ビン提案
    print("\n[4/4] ビン付け提案を生成中...")
    bin_suggestions = suggest_bins(df_indexes)
    
    # 結果保存
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df_stats.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    # ビン提案をJSON出力
    import json
    bin_output_path = output_path.with_suffix('.json')
    with open(bin_output_path, 'w', encoding='utf-8') as f:
        json.dump(bin_suggestions, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析完了！")
    print(f"  - 統計サマリー: {output_path}")
    print(f"  - ビン提案: {bin_output_path}")
    
    # サマリー表示
    print("\n" + "="*60)
    print("【全体統計サマリー】")
    print("="*60)
    overall = df_stats[df_stats['segment'] == '全体'].iloc[0]
    print(f"\nレース数: {overall['count']:,}件\n")
    
    print(f"テン指数:")
    print(f"  範囲: {overall['ten_min']:.1f} ~ {overall['ten_max']:.1f}")
    print(f"  平均: {overall['ten_mean']:.1f} ± {overall['ten_std']:.1f}")
    
    print(f"\n位置指数:")
    print(f"  範囲: {overall['pos_min']:.1f} ~ {overall['pos_max']:.1f}")
    print(f"  平均: {overall['pos_mean']:.1f} ± {overall['pos_std']:.1f}")
    
    print(f"\n上がり指数:")
    print(f"  範囲: {overall['agari_min']:.1f} ~ {overall['agari_max']:.1f}")
    print(f"  平均: {overall['agari_mean']:.1f} ± {overall['agari_std']:.1f}")
    
    print(f"\nペース指数:")
    print(f"  範囲: {overall['pace_min']:.1f} ~ {overall['pace_max']:.1f}")
    print(f"  平均: {overall['pace_mean']:.1f} ± {overall['pace_std']:.1f}")
    
    print("\n" + "="*60)
    print("Play to Win! 🚀")
    print("="*60)

if __name__ == '__main__':
    main()
