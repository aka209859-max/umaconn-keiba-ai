#!/usr/bin/env python3
"""
指数正規化器の学習スクリプト（バッチ実行版）

非対話式でコマンドライン引数から設定を受け取る。

使用方法:
    python scripts/train_normalizers_batch.py <data_path> [sample_rate] [output_dir]

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
from core.ten_3f_estimator import Ten3FEstimator

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================
# 前半3F推定
# ============================

# 距離比率
DISTANCE_RATIOS = {
    1200: None,
    1230: 0.495,
    1300: 0.48,
    1400: 0.26,
    1500: 0.24,
    1600: 0.22,
    1700: 0.21,
    1800: 0.22,
    2000: 0.17,
    2100: 0.16
}

MIN_TEN_3F = 30.0
MAX_TEN_3F = 45.0


def get_distance_ratio(kyori: int) -> float:
    if kyori in DISTANCE_RATIOS and DISTANCE_RATIOS[kyori] is not None:
        return DISTANCE_RATIOS[kyori]
    
    if kyori <= 1200:
        return 0.50
    
    sorted_distances = sorted([k for k in DISTANCE_RATIOS.keys() if k > 1200 and DISTANCE_RATIOS[k] is not None])
    
    for i in range(len(sorted_distances) - 1):
        d1 = sorted_distances[i]
        d2 = sorted_distances[i + 1]
        
        if d1 <= kyori <= d2:
            r1 = DISTANCE_RATIOS[d1]
            r2 = DISTANCE_RATIOS[d2]
            ratio = r1 + (r2 - r1) * (kyori - d1) / (d2 - d1)
            return ratio
    
    if kyori > max(sorted_distances):
        return 0.15
    
    return 0.22


def estimate_zenhan_3f(soha_time_sec: float, kohan_3f_sec: float, kyori: int) -> float:
    if kyori < 1200:
        zenhan_3f = soha_time_sec - kohan_3f_sec
        return max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    if kyori == 1200:
        zenhan_3f = soha_time_sec - kohan_3f_sec
        return max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    ratio = get_distance_ratio(kyori)
    zenhan_3f = soha_time_sec * ratio
    zenhan_3f = max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    return zenhan_3f


# ============================
# データ読み込み
# ============================

def load_data(file_path: str, sample_rate: float = 1.0) -> pd.DataFrame:
    """データを読み込み"""
    logger.info(f"データ読み込み開始: {file_path}")
    logger.info(f"サンプリング率: {sample_rate * 100:.1f}%")
    
    required_cols = [
        'race_id', 'umaban', 'chakujun', 'tosu',
        'soha_time_sec', 'kohan_3f_sec', 'kyori',
        'race_date', 'keibajo_code',
        'corner_1', 'corner_2', 'corner_3', 'corner_4'
    ]
    
    if sample_rate < 1.0:
        df = pd.read_csv(
            file_path,
            usecols=lambda col: col in required_cols,
            skiprows=lambda i: i > 0 and np.random.random() > sample_rate
        )
    else:
        df = pd.read_csv(file_path, usecols=required_cols)
    
    logger.info(f"読み込み完了: {len(df):,}行")
    
    # 期間フィルタ（2023/10/13以降）
    df = df[df['race_date'] >= 20231013]
    logger.info(f"期間フィルタ後: {len(df):,}行")
    
    # クレンジング
    df = df.dropna(subset=['soha_time_sec', 'kohan_3f_sec', 'kyori', 'tosu'])
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    
    logger.info(f"クレンジング後: {len(df):,}行")
    
    return df


# ============================
# 指数計算
# ============================

def calculate_indices(df: pd.DataFrame) -> pd.DataFrame:
    """指数を計算"""
    logger.info("指数計算開始...")
    
    results = []
    
    for idx, row in df.iterrows():
        try:
            soha_time_sec = float(row['soha_time_sec'])
            kohan_3f_sec = float(row['kohan_3f_sec'])
            kyori = int(row['kyori'])
            tosu = int(row['tosu'])
            
            # 前半3F推定
            zenhan_3f = estimate_zenhan_3f(soha_time_sec, kohan_3f_sec, kyori)
            
            # コーナー4角
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
            # 基準タイム
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
            else:
                base_time = 40.5
            
            # 指数計算（簡易版：補正なし）
            agari_index = base_time - kohan_3f_sec
            ten_index = base_time - zenhan_3f
            
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = ((base_position - avg_position) / tosu) * 100
            position_index = max(0, min(100, position_index))
            
            pace_index = (ten_index + agari_index) / 2
            
            results.append({
                'ten_index': ten_index,
                'agari_index': agari_index,
                'position_index': position_index,
                'pace_index': pace_index
            })
            
        except Exception as e:
            continue
    
    result_df = pd.DataFrame(results)
    logger.info(f"指数計算完了: {len(result_df):,}件")
    
    return result_df


# ============================
# メイン処理
# ============================

def main():
    """メイン処理"""
    logger.info("="*60)
    logger.info("NAR-SI3.0 指数正規化器 学習（バッチ版）")
    logger.info("="*60)
    
    # コマンドライン引数
    if len(sys.argv) < 2:
        print("使用方法: python train_normalizers_batch.py <data_path> [sample_rate] [output_dir]")
        sys.exit(1)
    
    data_path = sys.argv[1]
    sample_rate = float(sys.argv[2]) if len(sys.argv) > 2 else 0.1
    output_dir = sys.argv[3] if len(sys.argv) > 3 else 'models/normalizers'
    
    logger.info(f"データパス: {data_path}")
    logger.info(f"サンプリング率: {sample_rate * 100:.1f}%")
    logger.info(f"出力ディレクトリ: {output_dir}")
    
    # ステップ1: データ読み込み
    df = load_data(data_path, sample_rate)
    
    if len(df) == 0:
        logger.error("データがありません")
        return
    
    # ステップ2: 指数計算
    index_df = calculate_indices(df)
    
    if len(index_df) == 0:
        logger.error("指数計算に失敗しました")
        return
    
    # ステップ3: 正規化器の学習
    logger.info("\n" + "="*60)
    logger.info("正規化器の学習開始")
    logger.info("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    # テン指数
    logger.info("\nテン指数の正規化器を学習中...")
    ten_normalizer = RacingIndexNormalizer()
    ten_normalizer.fit(index_df['ten_index'].values)
    ten_path = os.path.join(output_dir, 'ten_index_normalizer.pkl')
    ten_normalizer.save(ten_path)
    logger.info(f"保存完了: {ten_path}")
    
    # 上がり指数
    logger.info("\n上がり指数の正規化器を学習中...")
    agari_normalizer = RacingIndexNormalizer()
    agari_normalizer.fit(index_df['agari_index'].values)
    agari_path = os.path.join(output_dir, 'agari_index_normalizer.pkl')
    agari_normalizer.save(agari_path)
    logger.info(f"保存完了: {agari_path}")
    
    # 位置指数
    logger.info("\n位置指数の正規化器を学習中...")
    position_normalizer = RacingIndexNormalizer(target_range=(0, 100))
    position_normalizer.fit(index_df['position_index'].values)
    position_path = os.path.join(output_dir, 'position_index_normalizer.pkl')
    position_normalizer.save(position_path)
    logger.info(f"保存完了: {position_path}")
    
    # ペース指数
    logger.info("\nペース指数の正規化器を学習中...")
    pace_normalizer = RacingIndexNormalizer()
    pace_normalizer.fit(index_df['pace_index'].values)
    pace_path = os.path.join(output_dir, 'pace_index_normalizer.pkl')
    pace_normalizer.save(pace_path)
    logger.info(f"保存完了: {pace_path}")
    
    # 完了
    logger.info("\n" + "="*60)
    logger.info("✅ 全ての正規化器の学習が完了しました！")
    logger.info("="*60)
    logger.info(f"\n出力ディレクトリ: {output_dir}")
    logger.info(f"  - {ten_path}")
    logger.info(f"  - {agari_path}")
    logger.info(f"  - {position_path}")
    logger.info(f"  - {pace_path}")
    
    logger.info("\n🏆 Play to Win!")


if __name__ == '__main__':
    main()
