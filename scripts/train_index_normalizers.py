#!/usr/bin/env python3
"""
指数正規化器の学習スクリプト

過去データから4指数（テン・上がり・位置・ペース）の正規化器を学習し、
学習済みモデルを保存する。

使用方法:
    python scripts/train_index_normalizers.py

出力:
    models/normalizers/
    ├── ten_index_normalizer.pkl          # テン指数用
    ├── agari_index_normalizer.pkl        # 上がり指数用
    ├── position_index_normalizer.pkl     # 位置指数用
    └── pace_index_normalizer.pkl         # ペース指数用

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-10
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import logging
from core.index_normalizer import RacingIndexNormalizer
from core.index_calculator import calculate_ten_index, calculate_agari_index, calculate_position_index, calculate_pace_index
from config.base_times import get_base_time

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================
# 設定
# ============================

# デフォルト設定
DEFAULT_DATA_PATH = r'E:\UmaData\nar-analytics-python-v2\data-1768047611955.csv'
DEFAULT_START_DATE = '20231013'  # 大井砂入れ替え後
DEFAULT_END_DATE = '20251231'
DEFAULT_SAMPLE_RATE = 0.1  # 10%サンプリング（テスト用）
DEFAULT_OUTPUT_DIR = 'models/normalizers'

# ============================
# データ読み込み
# ============================

def load_and_filter_data(
    file_path: str,
    start_date: str,
    end_date: str,
    sample_rate: float = 0.1
) -> pd.DataFrame:
    """
    データ読み込みとフィルタリング
    
    Args:
        file_path: データファイルパス
        start_date: 開始日（YYYYMMDD）
        end_date: 終了日（YYYYMMDD）
        sample_rate: サンプリング率（0.0～1.0）
    
    Returns:
        フィルタ済みデータフレーム
    """
    logger.info(f"📁 データ読み込み: {file_path}")
    
    # サンプリング読み込み
    df = pd.read_csv(file_path, skiprows=lambda i: i > 0 and np.random.rand() > sample_rate)
    logger.info(f"   読み込み: {len(df):,}行（サンプリング{int(sample_rate*100)}%）")
    
    # 期間フィルタ
    df['race_date'] = df['race_date'].astype(str)
    df = df[(df['race_date'] >= start_date) & (df['race_date'] <= end_date)]
    logger.info(f"   期間フィルタ: {len(df):,}行（{start_date}～{end_date}）")
    
    # データクレンジング
    df = df.dropna(subset=['race_date', 'keibajo_code', 'kyori', 'wakuban', 'chakujun',
                            'soha_time_sec', 'kohan_3f_sec', 'weight_kg', 'tosu'])
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    logger.info(f"   クレンジング後: {len(df):,}行\n")
    
    return df


# ============================
# 指数計算
# ============================

def calculate_all_indices(df: pd.DataFrame) -> pd.DataFrame:
    """
    全指数を計算（実装版のロジックを使用）
    
    Args:
        df: 入力データフレーム
    
    Returns:
        指数を含むデータフレーム
    """
    logger.info("🔢 NAR-SI3.0 全指数計算開始（実装版ロジック使用）...")
    
    results = []
    
    for idx, row in df.iterrows():
        try:
            # 基本情報
            keibajo_code = str(int(row['keibajo_code']))
            kyori = int(row['kyori'])
            wakuban = int(row['wakuban']) if pd.notna(row['wakuban']) else 0
            tosu = int(row['tosu'])
            
            # タイム情報
            soha_time_sec = float(row['soha_time_sec'])
            kohan_3f_sec = float(row['kohan_3f_sec'])
            
            # 前半3F推定（3パターン）
            if 'actual_ten_3f' in row and pd.notna(row['actual_ten_3f']):
                zenhan_3f = float(row['actual_ten_3f'])
            else:
                if kyori <= 1200:
                    # 1200m以下: 走破タイム - 後半3F
                    zenhan_3f = soha_time_sec - kohan_3f_sec
                else:
                    # 1201m以上: 距離別比率（簡易版）
                    if kyori <= 1400:
                        ratio = 0.26
                    elif kyori <= 1600:
                        ratio = 0.22
                    elif kyori <= 1800:
                        ratio = 0.22
                    elif kyori <= 2000:
                        ratio = 0.17
                    else:
                        ratio = 0.16
                    zenhan_3f = soha_time_sec * ratio
                    zenhan_3f = max(30.0, min(45.0, zenhan_3f))
            
            # コーナー順位
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
            # 基準タイム取得
            try:
                base_time_kohan = get_base_time(keibajo_code, kyori, 'kohan_3f')
                base_time_zenhan = get_base_time(keibajo_code, kyori, 'zenhan_3f')
            except:
                # フォールバック: 距離別デフォルト値
                if kyori <= 1200:
                    base_time_kohan = 37.5
                    base_time_zenhan = 37.5
                elif kyori <= 1400:
                    base_time_kohan = 38.0
                    base_time_zenhan = 38.0
                elif kyori <= 1600:
                    base_time_kohan = 39.0
                    base_time_zenhan = 39.0
                elif kyori <= 1800:
                    base_time_kohan = 39.5
                    base_time_zenhan = 39.5
                elif kyori <= 2000:
                    base_time_kohan = 40.0
                    base_time_zenhan = 40.0
                else:
                    base_time_kohan = 40.5
                    base_time_zenhan = 40.5
            
            # 1. 上がり指数（実装準拠: ×1、補正は省略）
            agari_index = base_time_kohan - kohan_3f_sec
            
            # 2. 位置指数（実装準拠）
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = 100 - (avg_position / tosu) * 100
            
            # 3. テン指数（実装準拠: ×1、補正は省略）
            ten_index = base_time_zenhan - zenhan_3f
            
            # 4. ペース指数（実装準拠: 平均、補正は省略）
            pace_index = (ten_index + agari_index) / 2
            
            # 範囲制限なし（生データのまま）
            results.append({
                'race_id': row['race_id'],
                'umaban': row['umaban'],
                'chakujun': row['chakujun'],
                'tosu': tosu,
                'ten_index_raw': ten_index,
                'agari_index_raw': agari_index,
                'position_index_raw': position_index,
                'pace_index_raw': pace_index
            })
            
        except Exception as e:
            logger.debug(f"行 {idx} でエラー: {e}")
            continue
    
    result_df = pd.DataFrame(results)
    logger.info(f"   指数計算完了: {len(result_df):,}頭\n")
    
    return result_df


# ============================
# 正規化器の学習
# ============================

def train_normalizers(
    df: pd.DataFrame,
    output_dir: str = DEFAULT_OUTPUT_DIR
) -> dict:
    """
    4指数の正規化器を学習・保存
    
    Args:
        df: 指数データを含むデータフレーム
        output_dir: 出力ディレクトリ
    
    Returns:
        学習済み正規化器の辞書
    """
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    normalizers = {}
    
    # 1. テン指数
    logger.info("=" * 80)
    logger.info("📊 テン指数の正規化器を学習中...")
    logger.info("=" * 80)
    ten_data = df['ten_index_raw'].dropna().values
    ten_normalizer = RacingIndexNormalizer()
    ten_normalizer.fit(ten_data)
    ten_normalizer.save(os.path.join(output_dir, 'ten_index_normalizer.pkl'))
    normalizers['ten'] = ten_normalizer
    logger.info("")
    
    # 2. 上がり指数
    logger.info("=" * 80)
    logger.info("📊 上がり指数の正規化器を学習中...")
    logger.info("=" * 80)
    agari_data = df['agari_index_raw'].dropna().values
    agari_normalizer = RacingIndexNormalizer()
    agari_normalizer.fit(agari_data)
    agari_normalizer.save(os.path.join(output_dir, 'agari_index_normalizer.pkl'))
    normalizers['agari'] = agari_normalizer
    logger.info("")
    
    # 3. 位置指数
    logger.info("=" * 80)
    logger.info("📊 位置指数の正規化器を学習中...")
    logger.info("=" * 80)
    position_data = df['position_index_raw'].dropna().values
    position_normalizer = RacingIndexNormalizer(target_range=(0, 100))  # 位置指数は 0～100
    position_normalizer.fit(position_data)
    position_normalizer.save(os.path.join(output_dir, 'position_index_normalizer.pkl'))
    normalizers['position'] = position_normalizer
    logger.info("")
    
    # 4. ペース指数
    logger.info("=" * 80)
    logger.info("📊 ペース指数の正規化器を学習中...")
    logger.info("=" * 80)
    pace_data = df['pace_index_raw'].dropna().values
    pace_normalizer = RacingIndexNormalizer()
    pace_normalizer.fit(pace_data)
    pace_normalizer.save(os.path.join(output_dir, 'pace_index_normalizer.pkl'))
    normalizers['pace'] = pace_normalizer
    logger.info("")
    
    logger.info("=" * 80)
    logger.info(f"✅ 全ての正規化器を保存しました: {output_dir}")
    logger.info("=" * 80)
    
    return normalizers


# ============================
# 正規化器のテスト
# ============================

def test_normalizers(df: pd.DataFrame, normalizers: dict):
    """
    正規化器のテスト
    
    Args:
        df: テストデータ
        normalizers: 正規化器の辞書
    """
    logger.info("\n" + "=" * 80)
    logger.info("🧪 正規化器のテスト")
    logger.info("=" * 80)
    
    # テスト用データ抽出（先頭1000件）
    test_df = df.head(1000).copy()
    
    # 各指数を正規化
    test_df['ten_index_normalized'] = normalizers['ten'].transform(test_df['ten_index_raw'].values)
    test_df['agari_index_normalized'] = normalizers['agari'].transform(test_df['agari_index_raw'].values)
    test_df['position_index_normalized'] = normalizers['position'].transform(test_df['position_index_raw'].values)
    test_df['pace_index_normalized'] = normalizers['pace'].transform(test_df['pace_index_raw'].values)
    
    # 統計情報の表示
    for index_name in ['ten', 'agari', 'position', 'pace']:
        raw_col = f'{index_name}_index_raw'
        norm_col = f'{index_name}_index_normalized'
        
        logger.info(f"\n📊 {index_name.upper()} Index:")
        logger.info(f"  生データ:")
        logger.info(f"    最小値: {test_df[raw_col].min():.2f}")
        logger.info(f"    最大値: {test_df[raw_col].max():.2f}")
        logger.info(f"    平均値: {test_df[raw_col].mean():.2f}")
        logger.info(f"    標準偏差: {test_df[raw_col].std():.2f}")
        
        logger.info(f"  正規化後:")
        logger.info(f"    最小値: {test_df[norm_col].min():.2f}")
        logger.info(f"    最大値: {test_df[norm_col].max():.2f}")
        logger.info(f"    平均値: {test_df[norm_col].mean():.2f}")
        logger.info(f"    標準偏差: {test_df[norm_col].std():.2f}")
        
        # -100/-95 の集中度チェック
        if index_name in ['ten', 'pace']:
            target_range = (-100, -95)
        elif index_name == 'position':
            target_range = (0, 5)
        else:
            target_range = None
        
        if target_range:
            count_raw = ((test_df[raw_col] >= target_range[0]) & 
                        (test_df[raw_col] <= target_range[1])).sum()
            count_norm = ((test_df[norm_col] >= target_range[0]) & 
                         (test_df[norm_col] <= target_range[1])).sum()
            
            logger.info(f"  {target_range} 範囲の件数:")
            logger.info(f"    生データ: {count_raw}件 ({count_raw/len(test_df)*100:.1f}%)")
            logger.info(f"    正規化後: {count_norm}件 ({count_norm/len(test_df)*100:.1f}%)")
    
    logger.info("\n" + "=" * 80)


# ============================
# メイン処理
# ============================

def main():
    """メイン処理"""
    print("=" * 100)
    print("🚀 指数正規化器の学習スクリプト")
    print("=" * 100)
    
    # 対話式設定
    data_path = input(f"データファイルパス（空白でデフォルト）: ").strip() or DEFAULT_DATA_PATH
    start_date = input(f"開始日（YYYYMMDD、空白で{DEFAULT_START_DATE}）: ").strip() or DEFAULT_START_DATE
    end_date = input(f"終了日（YYYYMMDD、空白で{DEFAULT_END_DATE}）: ").strip() or DEFAULT_END_DATE
    sample_rate_str = input(f"サンプリング率（0.0～1.0、空白で{DEFAULT_SAMPLE_RATE}）: ").strip()
    sample_rate = float(sample_rate_str) if sample_rate_str else DEFAULT_SAMPLE_RATE
    output_dir = input(f"出力ディレクトリ（空白で{DEFAULT_OUTPUT_DIR}）: ").strip() or DEFAULT_OUTPUT_DIR
    
    print("\n" + "=" * 100)
    print(f"データパス: {data_path}")
    print(f"期間: {start_date} ～ {end_date}")
    print(f"サンプリング率: {int(sample_rate*100)}%")
    print(f"出力ディレクトリ: {output_dir}")
    print("=" * 100 + "\n")
    
    # データ読み込み
    df = load_and_filter_data(data_path, start_date, end_date, sample_rate)
    
    # 指数計算
    df_with_indices = calculate_all_indices(df)
    
    # 正規化器の学習
    normalizers = train_normalizers(df_with_indices, output_dir)
    
    # テスト
    test_normalizers(df_with_indices, normalizers)
    
    print("\n" + "=" * 100)
    print("✅ 全ての処理が完了しました！")
    print("=" * 100)


if __name__ == '__main__':
    main()
