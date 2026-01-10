"""
指数正規化器の学習スクリプト（Windows版・Standalone）

このスクリプトは core/ への依存なしで単独で動作します。
全ての必要なコードが統合されています。

目的:
- NAR-SI3.0の4指数（テン指数、上がり指数、位置指数、ペース指数）を正規化
- RankGauss（Quantile Transformation）による統計的正規化
- 70%の張り付き問題を解消

使用方法:
    cd /d E:\\UmaData\\nar-analytics-python-v2
    python train_index_normalizers_windows.py

出力:
    models/normalizers/ten_index_normalizer.pkl
    models/normalizers/agari_index_normalizer.pkl
    models/normalizers/position_index_normalizer.pkl
    models/normalizers/pace_index_normalizer.pkl

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-10
"""

import os
import sys
import pandas as pd
import numpy as np
import joblib
import logging
from typing import Optional, Tuple, Dict
from sklearn.preprocessing import QuantileTransformer
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================
# RacingIndexNormalizer クラス（埋め込み版）
# ============================

class RacingIndexNormalizer:
    """
    競馬指数の統計的正規化クラス
    
    RankGauss (Quantile Transformation) による正規化:
    1. データをランク（順位）に変換
    2. 正規分布の累積分布関数（CDF）に基づいて値を再配置
    3. 4σ基準で [-100, 100] の範囲にスケーリング
    """
    
    def __init__(
        self, 
        target_range: Tuple[float, float] = (-100, 100), 
        sigma_cap: float = 4.0,
        n_quantiles: int = 2000,
        random_state: int = 42
    ):
        """
        初期化
        
        Args:
            target_range: 目標範囲（デフォルト: (-100, 100)）
            sigma_cap: σ基準（デフォルト: 4.0 = 99.99%のデータを含む）
            n_quantiles: 分位点の数（デフォルト: 2000、詳細な分解能）
            random_state: 乱数シード（再現性のため）
        """
        self.target_range = target_range
        self.sigma_cap = sigma_cap
        self.n_quantiles = n_quantiles
        self.random_state = random_state
        
        # QuantileTransformer の初期化
        self.qt = QuantileTransformer(
            n_quantiles=n_quantiles,
            output_distribution='normal',
            random_state=random_state,
            subsample=1000000
        )
        
        # スケーリング係数（4σ = 100点）
        self.scale_factor = target_range[1] / sigma_cap
        
        # 学習済みフラグ
        self.is_fitted = False
        
        logger.info(f"RacingIndexNormalizer initialized: "
                   f"target_range={target_range}, sigma_cap={sigma_cap}, "
                   f"n_quantiles={n_quantiles}")
    
    def fit(self, X: np.ndarray) -> 'RacingIndexNormalizer':
        """過去データを用いて分布を学習"""
        X = self._validate_input(X)
        
        if len(X) == 0:
            raise ValueError("学習データが空です")
        
        X_2d = X.reshape(-1, 1)
        
        logger.info(f"学習開始: {len(X):,}件のデータ")
        self.qt.fit(X_2d)
        self.is_fitted = True
        logger.info("学習完了")
        
        self._log_statistics(X)
        
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """指数を正規化"""
        if not self.is_fitted:
            raise RuntimeError("fit() を先に実行してください")
        
        X = self._validate_input(X)
        
        if len(X) == 0:
            return np.array([])
        
        X_2d = X.reshape(-1, 1)
        
        # Step 1: 正規分布へ変換
        z_scores = self.qt.transform(X_2d)
        
        # Step 2: スケーリング
        scaled_scores = z_scores * self.scale_factor
        
        # Step 3: 範囲制限
        final_scores = np.clip(scaled_scores, self.target_range[0], self.target_range[1])
        
        return final_scores.flatten()
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """fit と transform を一度に実行"""
        return self.fit(X).transform(X)
    
    def save(self, filepath: str):
        """学習済みモデルを保存"""
        if not self.is_fitted:
            raise RuntimeError("fit() を先に実行してください")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        joblib.dump(self, filepath)
        logger.info(f"モデルを保存しました: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RacingIndexNormalizer':
        """学習済みモデルを読み込み"""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"モデルファイルが見つかりません: {filepath}")
        
        normalizer = joblib.load(filepath)
        logger.info(f"モデルを読み込みました: {filepath}")
        
        return normalizer
    
    def _validate_input(self, X: np.ndarray) -> np.ndarray:
        """入力データの検証と変換"""
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        
        if X.ndim == 2 and X.shape[1] == 1:
            X = X.flatten()
        elif X.ndim > 1:
            raise ValueError(f"入力は1次元配列である必要があります: shape={X.shape}")
        
        if np.any(np.isnan(X)):
            logger.warning(f"NaNが含まれています: {np.sum(np.isnan(X))}件")
        
        return X
    
    def _log_statistics(self, X: np.ndarray):
        """学習データの統計情報をログ出力"""
        logger.info("=== 学習データの統計情報 ===")
        logger.info(f"データ数: {len(X):,}件")
        logger.info(f"最小値: {np.min(X):.2f}")
        logger.info(f"最大値: {np.max(X):.2f}")
        logger.info(f"平均値: {np.mean(X):.2f}")
        logger.info(f"中央値: {np.median(X):.2f}")
        logger.info(f"標準偏差: {np.std(X):.2f}")
        logger.info(f"5%点: {np.percentile(X, 5):.2f}")
        logger.info(f"25%点: {np.percentile(X, 25):.2f}")
        logger.info(f"75%点: {np.percentile(X, 75):.2f}")
        logger.info(f"95%点: {np.percentile(X, 95):.2f}")
        logger.info("=" * 30)


# ============================
# 前半3F推定ロジック（埋め込み版）
# ============================

# 距離比率定義（ten_3f_estimator.py より）
DISTANCE_RATIOS = {
    1200: None,  # 1200m は特別処理（走破タイム - 後半3F）
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

MIN_TEN_3F = 30.0  # 前半3F の物理的下限
MAX_TEN_3F = 45.0  # 前半3F の物理的上限


def get_distance_ratio(kyori: int) -> float:
    """
    距離から前半3Fの比率を取得（補間あり）
    
    Args:
        kyori: 距離（m）
    
    Returns:
        前半3Fの比率
    """
    # 完全一致
    if kyori in DISTANCE_RATIOS and DISTANCE_RATIOS[kyori] is not None:
        return DISTANCE_RATIOS[kyori]
    
    # 1200m は特別処理
    if kyori <= 1200:
        return 0.50  # 1200m以下は50%
    
    # 線形補間
    sorted_distances = sorted([k for k in DISTANCE_RATIOS.keys() if k > 1200 and DISTANCE_RATIOS[k] is not None])
    
    for i in range(len(sorted_distances) - 1):
        d1 = sorted_distances[i]
        d2 = sorted_distances[i + 1]
        
        if d1 <= kyori <= d2:
            r1 = DISTANCE_RATIOS[d1]
            r2 = DISTANCE_RATIOS[d2]
            # 線形補間
            ratio = r1 + (r2 - r1) * (kyori - d1) / (d2 - d1)
            return ratio
    
    # 範囲外の場合
    if kyori > max(sorted_distances):
        return 0.15  # 2100m超は15%
    
    return 0.22  # デフォルト


def estimate_zenhan_3f(soha_time_sec: float, kohan_3f_sec: float, kyori: int) -> float:
    """
    前半3Fを推定（3パターン対応）
    
    Args:
        soha_time_sec: 走破タイム（秒）
        kohan_3f_sec: 後半3F（秒）
        kyori: 距離（m）
    
    Returns:
        推定前半3F（秒）
    """
    # パターン1: 1200m未満 → 走破タイム - 後半3F
    if kyori < 1200:
        zenhan_3f = soha_time_sec - kohan_3f_sec
        return max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    # パターン2: 1200m ちょうど → 走破タイム - 後半3F
    if kyori == 1200:
        zenhan_3f = soha_time_sec - kohan_3f_sec
        return max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    # パターン3: 1201m以上 → 距離比率を使用
    ratio = get_distance_ratio(kyori)
    zenhan_3f = soha_time_sec * ratio
    
    # 物理的制約（30.0 ~ 45.0秒）
    zenhan_3f = max(MIN_TEN_3F, min(MAX_TEN_3F, zenhan_3f))
    
    return zenhan_3f


# ============================
# データ読み込みと前処理
# ============================

def load_and_filter_data(
    file_path: str,
    start_date: str = '20231013',
    end_date: str = '20251231',
    sample_rate: float = 1.0
) -> pd.DataFrame:
    """
    CSVデータを読み込み、フィルタリング
    
    Args:
        file_path: データファイルパス
        start_date: 開始日（YYYYMMDD）
        end_date: 終了日（YYYYMMDD）
        sample_rate: サンプリング率（0.0-1.0、1.0=全データ）
    
    Returns:
        フィルタ済みDataFrame
    """
    logger.info(f"データ読み込み開始: {file_path}")
    
    # 必要な列のみ読み込み
    required_cols = [
        'race_id', 'umaban', 'chakujun', 'tosu',
        'soha_time_sec', 'kohan_3f_sec', 'kyori',
        'race_date', 'keibajo_code', 'wakuban', 'weight_kg',
        'corner_1', 'corner_2', 'corner_3', 'corner_4'
    ]
    
    # サンプリング読み込み
    if sample_rate < 1.0:
        df = pd.read_csv(
            file_path,
            usecols=lambda col: col in required_cols,
            skiprows=lambda i: i > 0 and np.random.random() > sample_rate
        )
    else:
        df = pd.read_csv(file_path, usecols=required_cols)
    
    logger.info(f"読み込み完了: {len(df):,}行")
    
    # 期間フィルタ
    df = df[(df['race_date'] >= int(start_date)) & (df['race_date'] <= int(end_date))]
    logger.info(f"期間フィルタ後: {len(df):,}行")
    
    # データクレンジング
    df = df.dropna(subset=['race_id', 'soha_time_sec', 'kohan_3f_sec', 'kyori', 'tosu'])
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    
    logger.info(f"クレンジング後: {len(df):,}行")
    
    return df


# ============================
# 指数計算（実装版ロジック）
# ============================

def calculate_all_indices(df: pd.DataFrame) -> pd.DataFrame:
    """
    全指数を計算
    
    Args:
        df: 入力DataFrame
    
    Returns:
        指数列が追加されたDataFrame
    """
    logger.info("指数計算開始...")
    
    results = []
    
    for idx, row in df.iterrows():
        try:
            race_id = row['race_id']
            umaban = row['umaban']
            chakujun = row['chakujun']
            tosu = int(row['tosu'])
            soha_time_sec = float(row['soha_time_sec'])
            kohan_3f_sec = float(row['kohan_3f_sec'])
            kyori = int(row['kyori'])
            
            # 前半3F推定（3パターン対応）
            zenhan_3f = estimate_zenhan_3f(soha_time_sec, kohan_3f_sec, kyori)
            
            # コーナー順位（corner_4を優先）
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
            # 基準タイム（簡易版：距離のみ考慮）
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
            
            # 1. 上がり指数（×1、補正なし簡易版）
            agari_index = (base_time - kohan_3f_sec)
            
            # 2. 位置指数（0～100、コーナー4角ベース）
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = ((base_position - avg_position) / tosu) * 100
            position_index = max(0, min(100, position_index))
            
            # 3. テン指数（×1、補正なし簡易版）
            ten_index = (base_time - zenhan_3f)
            
            # 4. ペース指数（平均）
            pace_index = (ten_index + agari_index) / 2
            
            results.append({
                'race_id': race_id,
                'umaban': umaban,
                'chakujun': chakujun,
                'tosu': tosu,
                '上がり指数': agari_index,
                '位置指数': position_index,
                'テン指数': ten_index,
                'ペース指数': pace_index
            })
            
        except Exception as e:
            logger.warning(f"指数計算エラー (行 {idx}): {e}")
            continue
    
    result_df = pd.DataFrame(results)
    logger.info(f"指数計算完了: {len(result_df):,}頭")
    
    return result_df


# ============================
# 分布分析
# ============================

def analyze_distribution(data: np.ndarray, index_name: str):
    """
    指数の分布を分析してログ出力
    
    Args:
        data: 指数データ
        index_name: 指数名
    """
    logger.info(f"\n{'='*50}")
    logger.info(f"📊 {index_name} の分布分析")
    logger.info(f"{'='*50}")
    
    logger.info(f"データ数: {len(data):,}件")
    logger.info(f"最小値: {np.min(data):.2f}")
    logger.info(f"最大値: {np.max(data):.2f}")
    logger.info(f"平均値: {np.mean(data):.2f}")
    logger.info(f"中央値: {np.median(data):.2f}")
    logger.info(f"標準偏差: {np.std(data):.2f}")
    
    # 分位点
    logger.info("\n📈 分位点:")
    logger.info(f"  5%点: {np.percentile(data, 5):.2f}")
    logger.info(f"  25%点: {np.percentile(data, 25):.2f}")
    logger.info(f"  50%点 (中央値): {np.percentile(data, 50):.2f}")
    logger.info(f"  75%点: {np.percentile(data, 75):.2f}")
    logger.info(f"  95%点: {np.percentile(data, 95):.2f}")
    
    # 範囲別の集中度チェック
    if index_name in ['テン指数', '上がり指数', 'ペース指数']:
        min_range = -100
        max_range = 100
        bins = [-100, -90, -50, -10, 10, 50, 90, 100]
    else:  # 位置指数
        min_range = 0
        max_range = 100
        bins = [0, 5, 25, 50, 75, 95, 100]
    
    logger.info("\n📊 区間別分布:")
    for i in range(len(bins) - 1):
        count = np.sum((data >= bins[i]) & (data < bins[i+1]))
        pct = count / len(data) * 100
        logger.info(f"  [{bins[i]:5.0f} ~ {bins[i+1]:5.0f}): {count:7,}件 ({pct:5.2f}%)")
    
    # 最小値/最大値への張り付きチェック
    min_count = np.sum(data == min_range)
    max_count = np.sum(data == max_range)
    
    if min_count > 0:
        min_pct = min_count / len(data) * 100
        logger.info(f"\n⚠️  最小値 {min_range} への張り付き: {min_count:,}件 ({min_pct:.2f}%)")
    
    if max_count > 0:
        max_pct = max_count / len(data) * 100
        logger.info(f"⚠️  最大値 {max_range} への張り付き: {max_count:,}件 ({max_pct:.2f}%)")


# ============================
# メイン処理
# ============================

def main():
    """メイン処理"""
    logger.info("="*60)
    logger.info("🏇 NAR-SI3.0 指数正規化器 学習プログラム（Windows版）")
    logger.info("="*60)
    
    # デフォルト設定
    DEFAULT_DATA_PATH = r'E:\UmaData\nar-analytics-python-v2\data-1768047611955.csv'
    DEFAULT_START_DATE = '20231013'
    DEFAULT_END_DATE = '20251231'
    DEFAULT_SAMPLE_RATE = 1.0  # 全データ使用
    DEFAULT_OUTPUT_DIR = 'models/normalizers'
    
    # ユーザー入力
    print("\n" + "="*60)
    print("⚙️  設定入力（Enter でデフォルト値を使用）")
    print("="*60)
    
    data_path = input(f"データファイルパス [{DEFAULT_DATA_PATH}]: ").strip()
    data_path = data_path if data_path else DEFAULT_DATA_PATH
    
    start_date = input(f"開始日 (YYYYMMDD) [{DEFAULT_START_DATE}]: ").strip()
    start_date = start_date if start_date else DEFAULT_START_DATE
    
    end_date = input(f"終了日 (YYYYMMDD) [{DEFAULT_END_DATE}]: ").strip()
    end_date = end_date if end_date else DEFAULT_END_DATE
    
    sample_rate_input = input(f"サンプリング率 (0.0-1.0) [{DEFAULT_SAMPLE_RATE}]: ").strip()
    sample_rate = float(sample_rate_input) if sample_rate_input else DEFAULT_SAMPLE_RATE
    
    output_dir = input(f"出力ディレクトリ [{DEFAULT_OUTPUT_DIR}]: ").strip()
    output_dir = output_dir if output_dir else DEFAULT_OUTPUT_DIR
    
    # ファイル存在チェック
    if not os.path.exists(data_path):
        logger.error(f"❌ データファイルが見つかりません: {data_path}")
        return
    
    # ステップ1: データ読み込みと前処理
    logger.info("\n" + "="*60)
    logger.info("📂 ステップ1: データ読み込みと前処理")
    logger.info("="*60)
    
    df = load_and_filter_data(data_path, start_date, end_date, sample_rate)
    
    if len(df) == 0:
        logger.error("❌ 有効なデータがありません")
        return
    
    # ステップ2: 指数計算
    logger.info("\n" + "="*60)
    logger.info("🔢 ステップ2: 指数計算（実装版ロジック）")
    logger.info("="*60)
    
    index_df = calculate_all_indices(df)
    
    if len(index_df) == 0:
        logger.error("❌ 指数計算に失敗しました")
        return
    
    # ステップ3: 正規化前の分布分析
    logger.info("\n" + "="*60)
    logger.info("📊 ステップ3: 正規化前の分布分析")
    logger.info("="*60)
    
    analyze_distribution(index_df['テン指数'].values, 'テン指数')
    analyze_distribution(index_df['上がり指数'].values, '上がり指数')
    analyze_distribution(index_df['位置指数'].values, '位置指数')
    analyze_distribution(index_df['ペース指数'].values, 'ペース指数')
    
    # ステップ4: 正規化器の学習
    logger.info("\n" + "="*60)
    logger.info("🎓 ステップ4: 正規化器の学習")
    logger.info("="*60)
    
    # 出力ディレクトリ作成
    os.makedirs(output_dir, exist_ok=True)
    
    normalizers = {}
    
    # テン指数
    logger.info("\n🔹 テン指数の正規化器を学習中...")
    ten_normalizer = RacingIndexNormalizer()
    ten_normalizer.fit(index_df['テン指数'].values)
    ten_path = os.path.join(output_dir, 'ten_index_normalizer.pkl')
    ten_normalizer.save(ten_path)
    normalizers['ten'] = ten_normalizer
    
    # 上がり指数
    logger.info("\n🔹 上がり指数の正規化器を学習中...")
    agari_normalizer = RacingIndexNormalizer()
    agari_normalizer.fit(index_df['上がり指数'].values)
    agari_path = os.path.join(output_dir, 'agari_index_normalizer.pkl')
    agari_normalizer.save(agari_path)
    normalizers['agari'] = agari_normalizer
    
    # 位置指数（0～100）
    logger.info("\n🔹 位置指数の正規化器を学習中...")
    position_normalizer = RacingIndexNormalizer(target_range=(0, 100))
    position_normalizer.fit(index_df['位置指数'].values)
    position_path = os.path.join(output_dir, 'position_index_normalizer.pkl')
    position_normalizer.save(position_path)
    normalizers['position'] = position_normalizer
    
    # ペース指数
    logger.info("\n🔹 ペース指数の正規化器を学習中...")
    pace_normalizer = RacingIndexNormalizer()
    pace_normalizer.fit(index_df['ペース指数'].values)
    pace_path = os.path.join(output_dir, 'pace_index_normalizer.pkl')
    pace_normalizer.save(pace_path)
    normalizers['pace'] = pace_normalizer
    
    # ステップ5: 正規化後の分布確認
    logger.info("\n" + "="*60)
    logger.info("📊 ステップ5: 正規化後の分布確認")
    logger.info("="*60)
    
    ten_normalized = ten_normalizer.transform(index_df['テン指数'].values)
    agari_normalized = agari_normalizer.transform(index_df['上がり指数'].values)
    position_normalized = position_normalizer.transform(index_df['位置指数'].values)
    pace_normalized = pace_normalizer.transform(index_df['ペース指数'].values)
    
    analyze_distribution(ten_normalized, 'テン指数（正規化後）')
    analyze_distribution(agari_normalized, '上がり指数（正規化後）')
    analyze_distribution(position_normalized, '位置指数（正規化後）')
    analyze_distribution(pace_normalized, 'ペース指数（正規化後）')
    
    # 完了メッセージ
    logger.info("\n" + "="*60)
    logger.info("✅ 全ての正規化器の学習が完了しました！")
    logger.info("="*60)
    logger.info(f"\n📁 保存先: {output_dir}")
    logger.info(f"  - {ten_path}")
    logger.info(f"  - {agari_path}")
    logger.info(f"  - {position_path}")
    logger.info(f"  - {pace_path}")
    
    logger.info("\n🎯 次のステップ:")
    logger.info("  1. モデルファイルを確認")
    logger.info("  2. 予測パイプラインに統合")
    logger.info("  3. 実戦での効果を検証")
    
    logger.info("\n🏆 Play to Win!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  処理が中断されました")
    except Exception as e:
        logger.error(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
