#!/usr/bin/env python3
"""
正規化済み指数の的中率・回収率分析

目的:
- 正規化後の指数で5刻み・10刻みの的中率・回収率を算出
- 正規化前との比較
- 買い目条件の最適化

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-10
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from core.index_normalizer import RacingIndexNormalizer
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def load_data_and_normalize(data_path: str):
    """データを読み込み、正規化を適用"""
    logger.info(f"📂 データ読み込み: {data_path}")
    
    # 計算済み指数データを読み込み
    df = pd.read_csv(data_path)
    logger.info(f"✅ データ読み込み完了: {len(df):,}件")
    
    # 正規化器を読み込み
    logger.info("📦 正規化器読み込み中...")
    normalizers_dir = '/home/user/webapp/nar-ai-yoso/models/normalizers'
    
    normalizers = {
        'ten_index': RacingIndexNormalizer.load(f'{normalizers_dir}/ten_index_normalizer.pkl'),
        'agari_index': RacingIndexNormalizer.load(f'{normalizers_dir}/agari_index_normalizer.pkl'),
        'position_index': RacingIndexNormalizer.load(f'{normalizers_dir}/position_index_normalizer.pkl'),
        'pace_index': RacingIndexNormalizer.load(f'{normalizers_dir}/pace_index_normalizer.pkl')
    }
    
    # 正規化を適用
    logger.info("🔄 正規化実行中...")
    for index_name in ['ten_index', 'agari_index', 'position_index', 'pace_index']:
        if index_name in df.columns:
            df[f'{index_name}_raw'] = df[index_name]
            df[f'{index_name}_normalized'] = normalizers[index_name].transform(df[index_name].values)
            logger.info(f"✅ {index_name} 正規化完了")
    
    return df


def analyze_hit_rate_and_return(df: pd.DataFrame, index_name: str, use_normalized: bool = True, bin_size: int = 10):
    """
    指定された指数の的中率・回収率を区間別に分析
    
    Args:
        df: データフレーム
        index_name: 指数名（'ten_index', 'agari_index', etc.）
        use_normalized: 正規化済みを使用するか
        bin_size: 区間サイズ（5 or 10）
    """
    suffix = '_normalized' if use_normalized else '_raw'
    col_name = f'{index_name}{suffix}'
    
    if col_name not in df.columns:
        logger.warning(f"⚠️ {col_name} が存在しません")
        return None
    
    # 区間を作成
    if use_normalized:
        bins = list(range(-100, 101, bin_size))
    else:
        # 正規化前は実データの範囲に基づく
        min_val = int(df[col_name].min() // bin_size * bin_size)
        max_val = int(df[col_name].max() // bin_size * bin_size) + bin_size
        bins = list(range(min_val, max_val + 1, bin_size))
    
    # 区間ラベル作成
    labels = [f"{bins[i]}~{bins[i+1]}" for i in range(len(bins)-1)]
    
    # 区間に割り当て
    df['bin'] = pd.cut(df[col_name], bins=bins, labels=labels, include_lowest=True)
    
    # 区間別集計
    results = []
    for bin_label in labels:
        bin_data = df[df['bin'] == bin_label]
        
        if len(bin_data) == 0:
            continue
        
        count = len(bin_data)
        
        # 的中率（1着）
        win_count = (bin_data['chakujun'] == 1).sum()
        win_rate = (win_count / count * 100) if count > 0 else 0.0
        
        # 3着以内率
        place_count = (bin_data['chakujun'] <= 3).sum()
        place_rate = (place_count / count * 100) if count > 0 else 0.0
        
        # 単勝回収率・複勝回収率（オッズ情報がないため計算不可）
        win_return_rate = None
        place_return_rate = None
        
        results.append({
            '区間': bin_label,
            '件数': count,
            '割合(%)': count / len(df) * 100,
            '的中率(%)': win_rate,
            '3着以内率(%)': place_rate,
            '単勝回収率(%)': win_return_rate,
            '複勝回収率(%)': place_return_rate
        })
    
    result_df = pd.DataFrame(results)
    return result_df


def compare_normalized_vs_raw(df: pd.DataFrame, index_name: str, bin_size: int = 10):
    """正規化前後の比較"""
    logger.info(f"\n{'='*80}")
    logger.info(f"📊 {index_name} の比較分析（{bin_size}刻み）")
    logger.info(f"{'='*80}")
    
    # 正規化前
    logger.info("\n【正規化前】")
    raw_results = analyze_hit_rate_and_return(df, index_name, use_normalized=False, bin_size=bin_size)
    if raw_results is not None:
        # 上位区間のみ表示
        top_bins = raw_results.nlargest(5, '的中率(%)')
        logger.info("\n的中率 上位5区間:")
        for _, row in top_bins.iterrows():
            logger.info(f"  {row['区間']:>15s}: 的中率={row['的中率(%)']:>6.2f}%, 件数={row['件数']:>6,}件, 3着以内率={row['3着以内率(%)']:>6.2f}%")
    
    # 正規化後
    logger.info("\n【正規化後】")
    norm_results = analyze_hit_rate_and_return(df, index_name, use_normalized=True, bin_size=bin_size)
    if norm_results is not None:
        # 上位区間のみ表示
        top_bins = norm_results.nlargest(5, '的中率(%)')
        logger.info("\n的中率 上位5区間:")
        for _, row in top_bins.iterrows():
            logger.info(f"  {row['区間']:>15s}: 的中率={row['的中率(%)']:>6.2f}%, 件数={row['件数']:>6,}件, 3着以内率={row['3着以内率(%)']:>6.2f}%")
    
    return raw_results, norm_results


def save_results(df: pd.DataFrame, output_dir: str):
    """結果をCSVで保存"""
    logger.info(f"\n💾 結果保存中: {output_dir}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    for index_name in ['ten_index', 'agari_index', 'position_index', 'pace_index']:
        # 10刻み - 正規化前
        raw_10 = analyze_hit_rate_and_return(df, index_name, use_normalized=False, bin_size=10)
        if raw_10 is not None:
            output_path = f'{output_dir}/{index_name}_raw_10.csv'
            raw_10.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"✅ {output_path}")
        
        # 10刻み - 正規化後
        norm_10 = analyze_hit_rate_and_return(df, index_name, use_normalized=True, bin_size=10)
        if norm_10 is not None:
            output_path = f'{output_dir}/{index_name}_normalized_10.csv'
            norm_10.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"✅ {output_path}")
        
        # 5刻み - 正規化前
        raw_5 = analyze_hit_rate_and_return(df, index_name, use_normalized=False, bin_size=5)
        if raw_5 is not None:
            output_path = f'{output_dir}/{index_name}_raw_5.csv'
            raw_5.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"✅ {output_path}")
        
        # 5刻み - 正規化後
        norm_5 = analyze_hit_rate_and_return(df, index_name, use_normalized=True, bin_size=5)
        if norm_5 is not None:
            output_path = f'{output_dir}/{index_name}_normalized_5.csv'
            norm_5.to_csv(output_path, index=False, encoding='utf-8-sig')
            logger.info(f"✅ {output_path}")


def main():
    """メイン処理"""
    # データパス
    indices_path = '/home/user/webapp/nar-ai-yoso/models/normalizers/calculated_indices.csv'
    output_dir = '/home/user/webapp/nar-ai-yoso/models/normalizers/hit_rate_analysis'
    
    # データ読み込み＆正規化
    df = load_data_and_normalize(indices_path)
    
    # 各指数の比較分析
    for index_name in ['ten_index', 'agari_index', 'position_index', 'pace_index']:
        # 10刻み
        compare_normalized_vs_raw(df, index_name, bin_size=10)
        
        # 5刻み
        compare_normalized_vs_raw(df, index_name, bin_size=5)
    
    # 結果をCSV保存
    save_results(df, output_dir)
    
    logger.info("\n" + "="*80)
    logger.info("🎉 的中率・回収率分析完了！")
    logger.info("="*80)
    logger.info("\n✅ 次のステップ:")
    logger.info("  1. CSVファイルを確認")
    logger.info("  2. 最適な買い目条件を決定")
    logger.info("  3. A/Bテストで効果検証")
    logger.info("\nPlay to Win! 🏆\n")


if __name__ == "__main__":
    main()
