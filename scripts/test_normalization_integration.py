#!/usr/bin/env python3
"""
正規化統合テストスクリプト

目的:
- core/index_calculator.py に統合された正規化機能のテスト
- 正規化前後の指数比較
- A/Bテスト用のサンプルデータ生成

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-10
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from core.index_calculator import calculate_all_indexes
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data(data_path: str, sample_size: int = 100):
    """テストデータを読み込み"""
    logger.info(f"📂 データ読み込み: {data_path}")
    df = pd.read_csv(data_path)
    
    # サンプリング
    if len(df) > sample_size:
        df = df.sample(n=sample_size, random_state=42)
    
    logger.info(f"✅ データ読み込み完了: {len(df)}件")
    return df


def test_normalization(df: pd.DataFrame):
    """正規化のテスト"""
    logger.info("\n" + "="*80)
    logger.info("🧪 正規化統合テスト開始")
    logger.info("="*80)
    
    results_with_norm = []
    results_without_norm = []
    
    for idx, row in df.iterrows():
        horse_data = {
            'zenhan_3f': row.get('zenhan_3f'),
            'kohan_3f': row.get('kohan_3f'),
            'corner_1': row.get('corner_1'),
            'corner_2': row.get('corner_2'),
            'corner_3': row.get('corner_3'),
            'corner_4': row.get('corner_4'),
            'kyori': row.get('kyori'),
            'babajotai_code_dirt': row.get('babajotai_code_dirt', '1'),
            'keibajo_code': row.get('keibajo_code', '42'),
            'tosu': row.get('tosu', 12),
            'furi_code': row.get('furi_code', '00'),
            'wakuban': row.get('wakuban', 0),
            'kinryo': row.get('kinryo', 54.0),
            'bataiju': row.get('bataiju', 460.0),
            'soha_time': row.get('soha_time'),
        }
        
        # 正規化あり
        result_norm = calculate_all_indexes(horse_data, apply_normalization=True)
        results_with_norm.append(result_norm)
        
        # 正規化なし
        result_raw = calculate_all_indexes(horse_data, apply_normalization=False)
        results_without_norm.append(result_raw)
    
    # DataFrameに変換
    df_norm = pd.DataFrame(results_with_norm)
    df_raw = pd.DataFrame(results_without_norm)
    
    return df_norm, df_raw


def compare_distributions(df_norm: pd.DataFrame, df_raw: pd.DataFrame):
    """正規化前後の分布を比較"""
    logger.info("\n" + "="*80)
    logger.info("📊 分布比較レポート")
    logger.info("="*80)
    
    indices = ['ten_index', 'agari_index', 'position_index', 'pace_index']
    
    for index_name in indices:
        logger.info(f"\n【{index_name}】")
        
        # 正規化前
        if f'{index_name}_raw' in df_norm.columns:
            raw_values = df_norm[f'{index_name}_raw']
            logger.info(f"  正規化前:")
            logger.info(f"    Min:    {raw_values.min():.2f}")
            logger.info(f"    Max:    {raw_values.max():.2f}")
            logger.info(f"    Mean:   {raw_values.mean():.2f}")
            logger.info(f"    Median: {raw_values.median():.2f}")
            logger.info(f"    Std:    {raw_values.std():.2f}")
        
        # 正規化後
        if index_name in df_norm.columns:
            norm_values = df_norm[index_name]
            logger.info(f"  正規化後:")
            logger.info(f"    Min:    {norm_values.min():.2f}")
            logger.info(f"    Max:    {norm_values.max():.2f}")
            logger.info(f"    Mean:   {norm_values.mean():.2f}")
            logger.info(f"    Median: {norm_values.median():.2f}")
            logger.info(f"    Std:    {norm_values.std():.2f}")
        
        # 張り付き度（集中度）の計算
        if f'{index_name}_raw' in df_norm.columns:
            raw_values = df_norm[f'{index_name}_raw']
            # -10~0区間の割合
            concentration = ((raw_values >= -10) & (raw_values < 0)).sum() / len(raw_values) * 100
            logger.info(f"  張り付き度（-10~0区間）: {concentration:.1f}%")
            
            if concentration > 80:
                logger.info(f"    ⚠️ 高い張り付き問題あり")
            else:
                logger.info(f"    ✅ 改善されました")


def generate_comparison_report(df_norm: pd.DataFrame, df_raw: pd.DataFrame, output_path: str):
    """比較レポートを生成"""
    logger.info(f"\n📝 比較レポート生成: {output_path}")
    
    # 正規化前後の値を結合
    comparison = pd.DataFrame()
    
    for index_name in ['ten_index', 'agari_index', 'position_index', 'pace_index']:
        if f'{index_name}_raw' in df_norm.columns:
            comparison[f'{index_name}_raw'] = df_norm[f'{index_name}_raw']
        if index_name in df_norm.columns:
            comparison[f'{index_name}_normalized'] = df_norm[index_name]
    
    # CSV保存
    comparison.to_csv(output_path, index=False)
    logger.info(f"✅ 比較レポート保存完了: {output_path}")


def main():
    """メイン処理"""
    # データパス
    data_path = '/home/user/uploaded_files/data-1768047611955.csv'
    output_dir = '/home/user/webapp/nar-ai-yoso/models/normalizers'
    
    # テストデータ読み込み
    df = load_test_data(data_path, sample_size=1000)
    
    # 正規化テスト
    df_norm, df_raw = test_normalization(df)
    
    # 分布比較
    compare_distributions(df_norm, df_raw)
    
    # 比較レポート生成
    output_path = os.path.join(output_dir, 'normalization_comparison_test.csv')
    generate_comparison_report(df_norm, df_raw, output_path)
    
    logger.info("\n" + "="*80)
    logger.info("🎉 正規化統合テスト完了！")
    logger.info("="*80)
    logger.info("\n✅ 次のステップ:")
    logger.info("  1. 比較レポートを確認")
    logger.info("  2. 予測モデルでA/Bテスト実施")
    logger.info("  3. 的中率・回収率の改善を検証")
    logger.info("\nPlay to Win! 🏆\n")


if __name__ == "__main__":
    main()
