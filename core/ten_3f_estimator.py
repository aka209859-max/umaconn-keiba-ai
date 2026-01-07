"""
前半3F（テン3F）推定モジュール

3層構造の推定アルゴリズム:
- Layer 1: ベースライン推定（統計的比率）
- Layer 2: 展開パターン補正（コーナー順位利用）
- Layer 3: 機械学習モデル（LightGBM/RandomForest）

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-07
"""

import numpy as np
from typing import Dict, Optional, Any
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Ten3FEstimator:
    """
    前半3F（テン3F）を推定する3層アルゴリズム
    
    調査報告書に基づく実装:
    - 報告書1: 物理学的法則と走破タイムの構成方程式
    - 報告書2: 距離別ペース配分の統計値
    - 報告書3: 機械学習モデル設計
    """
    
    # 距離別の前半3F比率（報告書2より）
    # 注意: 1200m以下はcorner_1が'00'固定（DB検証済み 2026-01-08）
    DISTANCE_RATIOS = {
        1200: None,  # 確定値を使用: T_finish - T_Last3F
        1230: 0.495, # 1230m以上でcorner_1データあり
        1300: 0.48,
        1400: 0.26,  # 前半3F ≈ 走破タイムの26%
        1500: 0.24,
        1600: 0.22,  # 南関東で多い距離
        1700: 0.21,
        1800: 0.22,  # マイル系
        2000: 0.17,  # 長距離
        2100: 0.16,
    }
    
    # 物理的制約（報告書1より）
    MIN_TEN_3F = 33.0  # ダート600mの世界記録級
    MAX_TEN_3F = 45.0  # 極端なスローペース
    
    # 展開パターン補正係数（報告書2より）
    ESCAPE_CORRECTION = -0.5   # 逃げ・先行馬: 前半ペースが速い
    STALKER_CORRECTION = 0.0   # 中団: 標準ペース
    CLOSER_CORRECTION = 0.5    # 後方（差し馬）: 前半ペースが遅い
    
    def __init__(self, ml_model: Optional[Any] = None):
        """
        初期化
        
        Args:
            ml_model: Layer 3で使用する機械学習モデル（オプション）
        """
        self.ml_model = ml_model
        logger.info("Ten3FEstimator initialized")
    
    def estimate_baseline(
        self,
        time_seconds: float,
        kohan_3f_seconds: Optional[float],
        kyori: int
    ) -> float:
        """
        Layer 1: ベースライン推定（統計的比率）
        
        Args:
            time_seconds: 走破タイム（秒）
            kohan_3f_seconds: 上がり3F（秒）、Noneの場合は推定
            kyori: 距離（m）
        
        Returns:
            推定前半3F（秒）
        """
        # 1200m戦の特別処理（確定値）
        if kyori == 1200:
            if kohan_3f_seconds is not None:
                # T_First3F = T_finish - T_Last3F
                return time_seconds - kohan_3f_seconds
            else:
                # 上がり3Fがない場合の推定（前後半均等と仮定）
                return time_seconds * 0.50
        
        # 1400m以上の推定（距離別比率使用）
        ratio = self._get_distance_ratio(kyori)
        baseline = time_seconds * ratio
        
        # 物理的制約でクリッピング
        return np.clip(baseline, self.MIN_TEN_3F, self.MAX_TEN_3F)
    
    def _get_distance_ratio(self, kyori: int) -> float:
        """
        距離に対応する前半3F比率を取得（線形補間）
        
        Args:
            kyori: 距離（m）
        
        Returns:
            前半3F比率（0.0-1.0）
        """
        # 完全一致
        if kyori in self.DISTANCE_RATIOS:
            ratio = self.DISTANCE_RATIOS[kyori]
            if ratio is not None:
                return ratio
        
        # 線形補間
        sorted_distances = sorted([k for k, v in self.DISTANCE_RATIOS.items() if v is not None])
        
        for i in range(len(sorted_distances) - 1):
            d1, d2 = sorted_distances[i], sorted_distances[i+1]
            if d1 < kyori < d2:
                r1 = self.DISTANCE_RATIOS[d1]
                r2 = self.DISTANCE_RATIOS[d2]
                # 線形補間: ratio = r1 + (r2 - r1) * (kyori - d1) / (d2 - d1)
                ratio = r1 + (r2 - r1) * (kyori - d1) / (d2 - d1)
                return ratio
        
        # 範囲外の場合
        if kyori < 1200:
            return 0.50  # 短距離: 前後半均等
        else:
            return 0.15  # 超長距離: 前半の比率が低い
    
    def adjust_by_position(
        self,
        baseline_ten_3f: float,
        corner_1: Optional[int],
        corner_2: Optional[int],
        kyori: int,
        field_size: int = 12
    ) -> float:
        """
        Layer 2: 展開パターン補正（コーナー順位利用）
        
        注意: 1200m以下ではcorner_1='00'固定のためスキップ（DB検証済み 2026-01-08）
        
        Args:
            baseline_ten_3f: ベースライン推定値（秒）
            corner_1: 1コーナー通過順位
            corner_2: 2コーナー通過順位
            kyori: 距離（m）
            field_size: 出走頭数（デフォルト12頭）
        
        Returns:
            補正後の前半3F（秒）
        """
        # 1200m以下はcorner_1データなし → 補正不可
        if kyori <= 1200:
            logger.debug(f"Skip position adjustment for {kyori}m (no corner data)")
            return baseline_ten_3f
        
        # corner_1が'00'または無効な場合もスキップ
        if corner_1 is None or corner_1 == 0 or corner_2 is None or corner_2 == 0:
            logger.debug("Skip position adjustment (invalid corner data)")
            return baseline_ten_3f
        
        # 前半の平均順位（1コーナー + 2コーナー）
        early_position = (corner_1 + corner_2) / 2.0
        
        # 脚質判定と補正係数の決定
        if early_position <= 2.0:
            # 逃げ・先行馬: 前半ペースが速い
            correction = self.ESCAPE_CORRECTION
            pace_type = "escape"
        elif early_position <= 5.0:
            # 中団: 標準ペース
            correction = self.STALKER_CORRECTION
            pace_type = "stalker"
        else:
            # 後方（差し馬）: 前半ペースが遅い
            correction = self.CLOSER_CORRECTION
            pace_type = "closer"
        
        adjusted = baseline_ten_3f + correction
        
        # 物理的制約でクリッピング
        final = np.clip(adjusted, self.MIN_TEN_3F, self.MAX_TEN_3F)
        
        logger.debug(f"Position adjustment: {pace_type}, correction={correction:.2f}, "
                     f"baseline={baseline_ten_3f:.2f} -> adjusted={final:.2f}")
        
        return final
    
    def estimate_ml(
        self,
        features: Dict[str, Any]
    ) -> Optional[float]:
        """
        Layer 3: 機械学習モデルによる推定
        
        Args:
            features: 特徴量辞書 {
                'time_seconds': float,
                'kohan_3f_seconds': float,
                'kyori': int,
                'corner_1': int,
                'corner_2': int,
                'baba_jotai_code': int,
                'keibajo_code': str,
                ...
            }
        
        Returns:
            ML推定値（秒）、モデルがない場合はNone
        """
        if self.ml_model is None:
            return None
        
        try:
            # 特徴量エンジニアリング
            X = self._engineer_features(features)
            
            # 予測
            prediction = self.ml_model.predict(X)
            
            # 物理的制約でクリッピング
            ml_estimate = np.clip(prediction[0], self.MIN_TEN_3F, self.MAX_TEN_3F)
            
            logger.debug(f"ML prediction: {ml_estimate:.2f}秒")
            return ml_estimate
        
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
            return None
    
    def _engineer_features(self, features: Dict[str, Any]) -> np.ndarray:
        """
        特徴量エンジニアリング（報告書3より）
        
        Args:
            features: 元の特徴量辞書
        
        Returns:
            エンジニアリング後の特徴量配列
        """
        # 基本特徴量
        time_seconds = features.get('time_seconds', 0)
        kohan_3f_seconds = features.get('kohan_3f_seconds', 0)
        kyori = features.get('kyori', 1200)
        corner_1 = features.get('corner_1', 6)
        corner_2 = features.get('corner_2', 6)
        field_size = features.get('field_size', 12)
        
        # 派生特徴量
        avg_speed = kyori / time_seconds if time_seconds > 0 else 0  # 平均速度
        pos_c1_ratio = corner_1 / field_size if field_size > 0 else 0.5  # 位置取り比率
        early_position = (corner_1 + corner_2) / 2.0  # 前半平均順位
        
        # 特徴量配列（順序はモデル訓練時と同じにする）
        X = np.array([
            time_seconds,
            kohan_3f_seconds,
            kyori,
            corner_1,
            corner_2,
            field_size,
            avg_speed,
            pos_c1_ratio,
            early_position
        ]).reshape(1, -1)
        
        return X
    
    def estimate(
        self,
        time_seconds: float,
        kohan_3f_seconds: Optional[float],
        kyori: int,
        corner_1: Optional[int] = None,
        corner_2: Optional[int] = None,
        field_size: int = 12,
        use_ml: bool = True
    ) -> Dict[str, float]:
        """
        統合推定メソッド（Layer 1 + Layer 2 + Layer 3）
        
        ハイブリッド推定の優先順位（報告書3より）:
        1. ML推定値（use_ml=True かつ ml_modelが存在する場合）
        2. 展開パターン補正値（コーナー順位がある場合）
        3. ベースライン推定値（統計的比率）
        
        Args:
            time_seconds: 走破タイム（秒）
            kohan_3f_seconds: 上がり3F（秒）
            kyori: 距離（m）
            corner_1: 1コーナー通過順位
            corner_2: 2コーナー通過順位
            field_size: 出走頭数
            use_ml: ML推定を使用するか
        
        Returns:
            推定結果辞書 {
                'ten_3f_baseline': ベースライン推定値,
                'ten_3f_adjusted': 展開補正後の推定値,
                'ten_3f_ml': ML推定値（なければNone）,
                'ten_3f_final': 最終推定値,
                'method': 使用した推定方法
            }
        """
        # Layer 1: ベースライン推定
        baseline = self.estimate_baseline(time_seconds, kohan_3f_seconds, kyori)
        
        # Layer 2: 展開パターン補正（1200m以下はスキップ）
        adjusted = self.adjust_by_position(baseline, corner_1, corner_2, kyori, field_size)
        
        # Layer 3: 機械学習モデル
        ml_estimate = None
        if use_ml and self.ml_model is not None:
            features = {
                'time_seconds': time_seconds,
                'kohan_3f_seconds': kohan_3f_seconds if kohan_3f_seconds is not None else 0,
                'kyori': kyori,
                'corner_1': corner_1 if corner_1 is not None else 6,
                'corner_2': corner_2 if corner_2 is not None else 6,
                'field_size': field_size
            }
            ml_estimate = self.estimate_ml(features)
        
        # 最終推定値の決定（優先順位）
        # 注意: 1200m以下ではcorner_1データなし → MLまたはbaselineのみ
        if ml_estimate is not None:
            final = ml_estimate
            method = "ml"
        elif kyori > 1200 and corner_1 is not None and corner_1 > 0 and corner_2 is not None and corner_2 > 0:
            # 1400m以上でcorner_1有効な場合のみadjusted使用
            final = adjusted
            method = "adjusted"
        else:
            final = baseline
            method = "baseline"
        
        result = {
            'ten_3f_baseline': baseline,
            'ten_3f_adjusted': adjusted,
            'ten_3f_ml': ml_estimate,
            'ten_3f_final': final,
            'method': method
        }
        
        logger.info(f"Ten3F estimation: {final:.2f}秒 (method={method}, kyori={kyori}m)")
        
        return result
    
    def estimate_pace_balance(
        self,
        estimated_ten_3f: float,
        last_3f: float
    ) -> str:
        """
        ペースバランスの判定（報告書2より）
        
        Args:
            estimated_ten_3f: 推定前半3F（秒）
            last_3f: 上がり3F（秒）
        
        Returns:
            ペースバランス: 'H_PACE' | 'S_PACE' | 'EVEN'
        """
        diff = estimated_ten_3f - last_3f
        
        if diff < -1.0:
            # 前半が上がりより1秒以上速い → ハイペース
            return "H_PACE"
        elif diff > 1.0:
            # 前半が上がりより1秒以上遅い → スローペース
            return "S_PACE"
        else:
            # 前後半ほぼ均等 → 平均ペース
            return "EVEN"
