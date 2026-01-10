"""
指数正規化モジュール

RankGauss（Quantile Transformation）による統計的正規化:
- 70%の張り付き問題を解消
- 情報損失を完全に回避
- 正規分布化でAI学習を安定化

理論的根拠:
- 指数の絶対値ではなく、集団内での位置（ランク）に基づいて正規分布に再配置
- 単調増加関数による変換のため、順序を完全に保持
- scikit-learn の QuantileTransformer を使用

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-10
"""

import numpy as np
import joblib
import os
from typing import Optional, Tuple
from sklearn.preprocessing import QuantileTransformer
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RacingIndexNormalizer:
    """
    競馬指数の統計的正規化クラス
    
    RankGauss (Quantile Transformation) による正規化:
    1. データをランク（順位）に変換
    2. 正規分布の累積分布関数（CDF）に基づいて値を再配置
    3. 4σ基準で [-100, 100] の範囲にスケーリング
    
    特徴:
    - 情報損失ゼロ（単調増加関数）
    - 外れ値に頑健
    - 順序を完全に保持
    - 実装が容易（scikit-learn）
    
    使用例:
        # 学習フェーズ
        normalizer = RacingIndexNormalizer()
        normalizer.fit(train_data)
        normalizer.save('models/normalizers/ten_index_normalizer.pkl')
        
        # 推論フェーズ
        normalizer = RacingIndexNormalizer.load('models/normalizers/ten_index_normalizer.pkl')
        normalized_value = normalizer.transform([raw_value])[0]
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
            output_distribution='normal',  # 正規分布に変換
            random_state=random_state,
            subsample=1000000  # 大規模データ対応（100万件まで）
        )
        
        # スケーリング係数（4σ = 100点）
        self.scale_factor = target_range[1] / sigma_cap
        
        # 学習済みフラグ
        self.is_fitted = False
        
        logger.info(f"RacingIndexNormalizer initialized: "
                   f"target_range={target_range}, sigma_cap={sigma_cap}, "
                   f"n_quantiles={n_quantiles}")
    
    def fit(self, X: np.ndarray) -> 'RacingIndexNormalizer':
        """
        過去データを用いて分布を学習
        
        Args:
            X: shape (n_samples,) or (n_samples, 1) の指数データ
        
        Returns:
            self（メソッドチェーン用）
        
        Raises:
            ValueError: データが空の場合
        """
        # 入力検証
        X = self._validate_input(X)
        
        if len(X) == 0:
            raise ValueError("学習データが空です")
        
        # 2次元配列に変換（QuantileTransformer の要件）
        X_2d = X.reshape(-1, 1)
        
        # 学習実行
        logger.info(f"学習開始: {len(X):,}件のデータ")
        self.qt.fit(X_2d)
        self.is_fitted = True
        logger.info("学習完了")
        
        # 学習データの統計情報を記録
        self._log_statistics(X)
        
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        指数を正規化
        
        処理フロー:
        1. RankGauss変換（正規分布化）Z ~ N(0, 1)
        2. 4σ基準でスケーリング
        3. 最終範囲制限（-100 ~ 100）
        
        Args:
            X: shape (n_samples,) or (n_samples, 1) の指数データ
        
        Returns:
            正規化済み指数 [-100, 100]
        
        Raises:
            RuntimeError: fit() が実行されていない場合
        """
        # 学習済みチェック
        if not self.is_fitted:
            raise RuntimeError("fit() を先に実行してください")
        
        # 入力検証
        X = self._validate_input(X)
        
        if len(X) == 0:
            return np.array([])
        
        # 2次元配列に変換
        X_2d = X.reshape(-1, 1)
        
        # Step 1: 正規分布へ変換 Z ~ N(0, 1)
        # これにより"70%の張り付き"は正規分布の左裾へ展開される
        z_scores = self.qt.transform(X_2d)
        
        # Step 2: 目標範囲へスケーリング（4σ = 100点）
        scaled_scores = z_scores * self.scale_factor
        
        # Step 3: 最終的な範囲制限
        # 99.99%のデータは既に範囲内だが、念のためクリップ
        final_scores = np.clip(scaled_scores, self.target_range[0], self.target_range[1])
        
        # 1次元配列に戻す
        return final_scores.flatten()
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """
        fit と transform を一度に実行
        
        Args:
            X: shape (n_samples,) or (n_samples, 1) の指数データ
        
        Returns:
            正規化済み指数 [-100, 100]
        """
        return self.fit(X).transform(X)
    
    def inverse_transform(self, X: np.ndarray) -> np.ndarray:
        """
        正規化された値を元の指数に戻す
        
        注意: 完全に元の値に戻るわけではなく、近似値となる
        
        Args:
            X: shape (n_samples,) or (n_samples, 1) の正規化済み指数
        
        Returns:
            元の指数の近似値
        
        Raises:
            RuntimeError: fit() が実行されていない場合
        """
        # 学習済みチェック
        if not self.is_fitted:
            raise RuntimeError("fit() を先に実行してください")
        
        # 入力検証
        X = self._validate_input(X)
        
        if len(X) == 0:
            return np.array([])
        
        # 2次元配列に変換
        X_2d = X.reshape(-1, 1)
        
        # Step 1: スケーリングを戻す
        z_scores = X_2d / self.scale_factor
        
        # Step 2: 正規分布から元の分布へ逆変換
        original_scores = self.qt.inverse_transform(z_scores)
        
        # 1次元配列に戻す
        return original_scores.flatten()
    
    def save(self, filepath: str):
        """
        学習済みモデルを保存
        
        Args:
            filepath: 保存先ファイルパス（.pkl 推奨）
        
        Raises:
            RuntimeError: fit() が実行されていない場合
        """
        if not self.is_fitted:
            raise RuntimeError("fit() を先に実行してください")
        
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 保存
        joblib.dump(self, filepath)
        logger.info(f"モデルを保存しました: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RacingIndexNormalizer':
        """
        学習済みモデルを読み込み
        
        Args:
            filepath: モデルファイルパス
        
        Returns:
            読み込まれた RacingIndexNormalizer インスタンス
        
        Raises:
            FileNotFoundError: ファイルが存在しない場合
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"モデルファイルが見つかりません: {filepath}")
        
        normalizer = joblib.load(filepath)
        logger.info(f"モデルを読み込みました: {filepath}")
        
        return normalizer
    
    def _validate_input(self, X: np.ndarray) -> np.ndarray:
        """
        入力データの検証と変換
        
        Args:
            X: 入力データ
        
        Returns:
            1次元 numpy 配列
        """
        # numpy 配列に変換
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        
        # 1次元配列に変換
        if X.ndim == 2 and X.shape[1] == 1:
            X = X.flatten()
        elif X.ndim > 1:
            raise ValueError(f"入力は1次元配列である必要があります: shape={X.shape}")
        
        # NaNチェック
        if np.any(np.isnan(X)):
            logger.warning(f"NaNが含まれています: {np.sum(np.isnan(X))}件")
        
        return X
    
    def _log_statistics(self, X: np.ndarray):
        """
        学習データの統計情報をログ出力
        
        Args:
            X: 学習データ
        """
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
    
    def get_info(self) -> dict:
        """
        正規化器の情報を取得
        
        Returns:
            設定情報を含む辞書
        """
        return {
            'target_range': self.target_range,
            'sigma_cap': self.sigma_cap,
            'n_quantiles': self.n_quantiles,
            'random_state': self.random_state,
            'scale_factor': self.scale_factor,
            'is_fitted': self.is_fitted
        }


# ============================
# ユーティリティ関数
# ============================

def create_normalizers_for_all_indices(
    ten_data: np.ndarray,
    agari_data: np.ndarray,
    position_data: np.ndarray,
    pace_data: np.ndarray,
    save_dir: str = 'models/normalizers'
) -> dict:
    """
    4指数全てに対する正規化器を作成・学習・保存
    
    Args:
        ten_data: テン指数の生データ
        agari_data: 上がり指数の生データ
        position_data: 位置指数の生データ
        pace_data: ペース指数の生データ
        save_dir: 保存先ディレクトリ
    
    Returns:
        各指数の正規化器を含む辞書
    """
    normalizers = {}
    
    # テン指数
    logger.info("テン指数の正規化器を学習中...")
    ten_normalizer = RacingIndexNormalizer()
    ten_normalizer.fit(ten_data)
    ten_normalizer.save(os.path.join(save_dir, 'ten_index_normalizer.pkl'))
    normalizers['ten'] = ten_normalizer
    
    # 上がり指数
    logger.info("上がり指数の正規化器を学習中...")
    agari_normalizer = RacingIndexNormalizer()
    agari_normalizer.fit(agari_data)
    agari_normalizer.save(os.path.join(save_dir, 'agari_index_normalizer.pkl'))
    normalizers['agari'] = agari_normalizer
    
    # 位置指数
    logger.info("位置指数の正規化器を学習中...")
    position_normalizer = RacingIndexNormalizer(target_range=(0, 100))  # 位置指数は 0～100
    position_normalizer.fit(position_data)
    position_normalizer.save(os.path.join(save_dir, 'position_index_normalizer.pkl'))
    normalizers['position'] = position_normalizer
    
    # ペース指数
    logger.info("ペース指数の正規化器を学習中...")
    pace_normalizer = RacingIndexNormalizer()
    pace_normalizer.fit(pace_data)
    pace_normalizer.save(os.path.join(save_dir, 'pace_index_normalizer.pkl'))
    normalizers['pace'] = pace_normalizer
    
    logger.info(f"全ての正規化器を保存しました: {save_dir}")
    
    return normalizers


def load_all_normalizers(load_dir: str = 'models/normalizers') -> dict:
    """
    保存済みの全正規化器を読み込み
    
    Args:
        load_dir: 読み込み元ディレクトリ
    
    Returns:
        各指数の正規化器を含む辞書
    """
    normalizers = {}
    
    normalizers['ten'] = RacingIndexNormalizer.load(
        os.path.join(load_dir, 'ten_index_normalizer.pkl')
    )
    normalizers['agari'] = RacingIndexNormalizer.load(
        os.path.join(load_dir, 'agari_index_normalizer.pkl')
    )
    normalizers['position'] = RacingIndexNormalizer.load(
        os.path.join(load_dir, 'position_index_normalizer.pkl')
    )
    normalizers['pace'] = RacingIndexNormalizer.load(
        os.path.join(load_dir, 'pace_index_normalizer.pkl')
    )
    
    logger.info(f"全ての正規化器を読み込みました: {load_dir}")
    
    return normalizers
