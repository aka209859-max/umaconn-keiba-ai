#!/usr/bin/env python3
"""
競馬場改修履歴に基づくデータフィルタリング

目的:
1) 改修・移転の影響を除外
2) 機械学習用: 全期間データ（改修前後を競馬場コード別に扱う）
3) 回収率分析用: 2016-2025年データ（姫路は2020年以降のみ）

作成日: 2026-01-10
作成者: NAR-AI-YOSO Project
"""

import pandas as pd
from pathlib import Path

# ============================
# 改修履歴データ
# ============================
RENOVATION_HISTORY = {
    '名古屋競馬場': {
        'keibajo_code': 48,
        'renovation_date': '20220407',
        'impact': 'コース全面変更（弥富市へ移転）',
        'handling': '改修前後で別競馬場として扱う'
    },
    '姫路競馬場': {
        'keibajo_code': 51,
        'closed_start': '20120601',  # 推定
        'reopened_date': '20200114',
        'impact': '約7年半休止（洪水調整池整備）',
        'handling': '2020年1月14日以降のデータのみ使用'
    },
    '大井競馬場': {
        'keibajo_code': 44,
        'renovation_date_sand': '20231013',
        'impact': '本馬場砂入れ替え（重大：馬場特性が大きく変化）',
        'handling': '2023年10月13日以降のデータのみ使用'
    }
}

# ============================
# データ期間の定義
# ============================
PERIOD_CONFIG = {
    'machine_learning': {
        'start_date': '20050101',
        'end_date': '20251231',
        'description': '機械学習・サンプル用（全期間）'
    },
    'recovery_rate_analysis': {
        'start_date': '20231013',  # 大井競馬場砂入れ替え後
        'end_date': '20251231',
        'description': '回収率分析用（2023年10月13日～2025年12月31日）'
    }
}

# ============================
# フィルタリング関数
# ============================
def filter_by_renovation(df: pd.DataFrame, purpose: str = 'machine_learning') -> pd.DataFrame:
    """
    競馬場改修履歴に基づくデータフィルタリング
    
    Args:
        df: PCkeibaデータ（race_date, keibajo_code必須）
        purpose: 'machine_learning' または 'recovery_rate_analysis'
    
    Returns:
        フィルタリング済みDataFrame
    """
    print(f'\n🔍 データフィルタリング開始（用途: {purpose}）')
    print(f'元データ: {len(df):,} 行')
    
    # race_dateを文字列型に変換
    df['race_date'] = df['race_date'].astype(str)
    
    # 期間フィルタリング
    config = PERIOD_CONFIG[purpose]
    df_filtered = df[
        (df['race_date'] >= config['start_date']) & 
        (df['race_date'] <= config['end_date'])
    ].copy()
    
    print(f'期間フィルタリング後: {len(df_filtered):,} 行 ({config["description"]})')
    
    # 姫路競馬場の休止期間を除外
    himeji_code = RENOVATION_HISTORY['姫路競馬場']['keibajo_code']
    himeji_reopened = RENOVATION_HISTORY['姫路競馬場']['reopened_date']
    
    himeji_before = len(df_filtered[df_filtered['keibajo_code'] == himeji_code])
    df_filtered = df_filtered[
        ~((df_filtered['keibajo_code'] == himeji_code) & 
          (df_filtered['race_date'] < himeji_reopened))
    ]
    himeji_after = len(df_filtered[df_filtered['keibajo_code'] == himeji_code])
    
    print(f'姫路競馬場フィルタリング: {himeji_before:,} → {himeji_after:,} 行（2020年1月14日以降のみ）')
    
    print(f'✅ フィルタリング完了: {len(df_filtered):,} 行')
    
    return df_filtered


def add_renovation_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    改修前後のフラグを追加（機械学習用）
    
    Args:
        df: PCkeibaデータ
    
    Returns:
        renovation_flagカラムを追加したDataFrame
    """
    df['renovation_flag'] = 'normal'
    
    # 名古屋競馬場の改修前後
    nagoya_code = RENOVATION_HISTORY['名古屋競馬場']['keibajo_code']
    nagoya_renovation = RENOVATION_HISTORY['名古屋競馬場']['renovation_date']
    
    df.loc[
        (df['keibajo_code'] == nagoya_code) & 
        (df['race_date'] < nagoya_renovation),
        'renovation_flag'
    ] = 'nagoya_old_course'
    
    df.loc[
        (df['keibajo_code'] == nagoya_code) & 
        (df['race_date'] >= nagoya_renovation),
        'renovation_flag'
    ] = 'nagoya_new_course'
    
    print('\n📊 改修フラグ統計:')
    print(df['renovation_flag'].value_counts())
    
    return df


# ============================
# メイン処理
# ============================
if __name__ == '__main__':
    # サンプルデータでテスト
    INPUT_CSV = '/home/user/uploaded_files/data-1768047611955.csv'
    
    print('📂 データ読み込み中...')
    
    # サンプリング読み込み（10%）
    import numpy as np
    df = pd.read_csv(INPUT_CSV, low_memory=False, 
                     skiprows=lambda i: i > 0 and np.random.rand() > 0.1)
    
    print(f'✅ データ読み込み完了: {len(df):,} 行')
    
    # 機械学習用フィルタリング
    df_ml = filter_by_renovation(df, purpose='machine_learning')
    df_ml = add_renovation_flag(df_ml)
    
    # 回収率分析用フィルタリング
    df_recovery = filter_by_renovation(df, purpose='recovery_rate_analysis')
    
    print('\n' + '='*60)
    print('📊 フィルタリング結果サマリー')
    print('='*60)
    print(f'機械学習用: {len(df_ml):,} 行（2005-2025年、全期間）')
    print(f'回収率分析用: {len(df_recovery):,} 行（2016-2025年、10年間）')
    print('\n✅ フィルタリング完了！')
