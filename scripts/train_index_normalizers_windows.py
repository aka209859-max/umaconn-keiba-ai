# -*- coding: utf-8 -*-
r"""
NAR-SI3.0 Index Normalizer Training Script (Windows Standalone Version)

This script trains index normalizers using RankGauss (Quantile Transformation).
No dependency on core/ module - all code is embedded.

Usage:
    python train_index_normalizers_windows.py

Output:
    models/normalizers/ten_index_normalizer.pkl
    models/normalizers/agari_index_normalizer.pkl
    models/normalizers/position_index_normalizer.pkl
    models/normalizers/pace_index_normalizer.pkl

Author: NAR-AI-YOSO Development Team
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

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================
# RacingIndexNormalizer Class
# ============================

class RacingIndexNormalizer:
    """
    Racing index statistical normalizer using RankGauss (Quantile Transformation).
    
    Features:
    - Zero information loss
    - Robust to outliers
    - Preserves order
    - Easy implementation with scikit-learn
    """
    
    def __init__(
        self, 
        target_range: Tuple[float, float] = (-100, 100), 
        sigma_cap: float = 4.0,
        n_quantiles: int = 2000,
        random_state: int = 42
    ):
        self.target_range = target_range
        self.sigma_cap = sigma_cap
        self.n_quantiles = n_quantiles
        self.random_state = random_state
        
        self.qt = QuantileTransformer(
            n_quantiles=n_quantiles,
            output_distribution='normal',
            random_state=random_state,
            subsample=1000000
        )
        
        self.scale_factor = target_range[1] / sigma_cap
        self.is_fitted = False
        
        logger.info(f"RacingIndexNormalizer initialized: "
                   f"target_range={target_range}, sigma_cap={sigma_cap}, "
                   f"n_quantiles={n_quantiles}")
    
    def fit(self, X: np.ndarray) -> 'RacingIndexNormalizer':
        X = self._validate_input(X)
        
        if len(X) == 0:
            raise ValueError("Training data is empty")
        
        X_2d = X.reshape(-1, 1)
        
        logger.info(f"Training started: {len(X):,} samples")
        self.qt.fit(X_2d)
        self.is_fitted = True
        logger.info("Training completed")
        
        self._log_statistics(X)
        
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("Call fit() first")
        
        X = self._validate_input(X)
        
        if len(X) == 0:
            return np.array([])
        
        X_2d = X.reshape(-1, 1)
        
        # Step 1: Transform to normal distribution
        z_scores = self.qt.transform(X_2d)
        
        # Step 2: Scale to target range
        scaled_scores = z_scores * self.scale_factor
        
        # Step 3: Clip to final range
        final_scores = np.clip(scaled_scores, self.target_range[0], self.target_range[1])
        
        return final_scores.flatten()
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        return self.fit(X).transform(X)
    
    def save(self, filepath: str):
        if not self.is_fitted:
            raise RuntimeError("Call fit() first")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        joblib.dump(self, filepath)
        logger.info(f"Model saved: {filepath}")
    
    @classmethod
    def load(cls, filepath: str) -> 'RacingIndexNormalizer':
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Model file not found: {filepath}")
        
        normalizer = joblib.load(filepath)
        logger.info(f"Model loaded: {filepath}")
        
        return normalizer
    
    def _validate_input(self, X: np.ndarray) -> np.ndarray:
        if not isinstance(X, np.ndarray):
            X = np.array(X)
        
        if X.ndim == 2 and X.shape[1] == 1:
            X = X.flatten()
        elif X.ndim > 1:
            raise ValueError(f"Input must be 1D array: shape={X.shape}")
        
        if np.any(np.isnan(X)):
            logger.warning(f"NaN values found: {np.sum(np.isnan(X))}")
        
        return X
    
    def _log_statistics(self, X: np.ndarray):
        logger.info("=== Training Data Statistics ===")
        logger.info(f"Count: {len(X):,}")
        logger.info(f"Min: {np.min(X):.2f}")
        logger.info(f"Max: {np.max(X):.2f}")
        logger.info(f"Mean: {np.mean(X):.2f}")
        logger.info(f"Median: {np.median(X):.2f}")
        logger.info(f"Std: {np.std(X):.2f}")
        logger.info(f"5th percentile: {np.percentile(X, 5):.2f}")
        logger.info(f"25th percentile: {np.percentile(X, 25):.2f}")
        logger.info(f"75th percentile: {np.percentile(X, 75):.2f}")
        logger.info(f"95th percentile: {np.percentile(X, 95):.2f}")
        logger.info("=" * 30)


# ============================
# Front 3F Estimation Logic
# ============================

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
# Data Loading and Preprocessing
# ============================

def load_and_filter_data(
    file_path: str,
    start_date: str = '20231013',
    end_date: str = '20251231',
    sample_rate: float = 1.0
) -> pd.DataFrame:
    logger.info(f"Loading data: {file_path}")
    
    required_cols = [
        'race_id', 'umaban', 'chakujun', 'tosu',
        'soha_time_sec', 'kohan_3f_sec', 'kyori',
        'race_date', 'keibajo_code', 'wakuban', 'weight_kg',
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
    
    logger.info(f"Loaded: {len(df):,} rows")
    
    df = df[(df['race_date'] >= int(start_date)) & (df['race_date'] <= int(end_date))]
    logger.info(f"After date filter: {len(df):,} rows")
    
    df = df.dropna(subset=['race_id', 'soha_time_sec', 'kohan_3f_sec', 'kyori', 'tosu'])
    df = df[df['soha_time_sec'] > 0]
    df = df[df['kohan_3f_sec'] > 0]
    df = df[df['tosu'] >= 4]
    
    logger.info(f"After cleaning: {len(df):,} rows")
    
    return df


# ============================
# Index Calculation
# ============================

def calculate_all_indices(df: pd.DataFrame) -> pd.DataFrame:
    logger.info("Calculating indices...")
    
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
            
            zenhan_3f = estimate_zenhan_3f(soha_time_sec, kohan_3f_sec, kyori)
            
            if 'corner_4' in row and pd.notna(row['corner_4']):
                corner_4 = int(row['corner_4'])
            else:
                corner_4 = int(row['chakujun']) if 'chakujun' in row else tosu // 2
            
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
            
            agari_index = (base_time - kohan_3f_sec)
            
            avg_position = corner_4
            base_position = tosu / 2.0
            position_index = ((base_position - avg_position) / tosu) * 100
            position_index = max(0, min(100, position_index))
            
            ten_index = (base_time - zenhan_3f)
            
            pace_index = (ten_index + agari_index) / 2
            
            results.append({
                'race_id': race_id,
                'umaban': umaban,
                'chakujun': chakujun,
                'tosu': tosu,
                'agari_index': agari_index,
                'position_index': position_index,
                'ten_index': ten_index,
                'pace_index': pace_index
            })
            
        except Exception as e:
            logger.warning(f"Error calculating indices (row {idx}): {e}")
            continue
    
    result_df = pd.DataFrame(results)
    logger.info(f"Indices calculated: {len(result_df):,} horses")
    
    return result_df


# ============================
# Distribution Analysis
# ============================

def analyze_distribution(data: np.ndarray, index_name: str):
    logger.info(f"\n{'='*50}")
    logger.info(f"Distribution Analysis: {index_name}")
    logger.info(f"{'='*50}")
    
    logger.info(f"Count: {len(data):,}")
    logger.info(f"Min: {np.min(data):.2f}")
    logger.info(f"Max: {np.max(data):.2f}")
    logger.info(f"Mean: {np.mean(data):.2f}")
    logger.info(f"Median: {np.median(data):.2f}")
    logger.info(f"Std: {np.std(data):.2f}")
    
    logger.info("\nPercentiles:")
    logger.info(f"  5th: {np.percentile(data, 5):.2f}")
    logger.info(f"  25th: {np.percentile(data, 25):.2f}")
    logger.info(f"  50th (Median): {np.percentile(data, 50):.2f}")
    logger.info(f"  75th: {np.percentile(data, 75):.2f}")
    logger.info(f"  95th: {np.percentile(data, 95):.2f}")
    
    if 'position' in index_name.lower():
        bins = [0, 5, 25, 50, 75, 95, 100]
        min_range = 0
        max_range = 100
    else:
        bins = [-100, -90, -50, -10, 10, 50, 90, 100]
        min_range = -100
        max_range = 100
    
    logger.info("\nDistribution by range:")
    for i in range(len(bins) - 1):
        count = np.sum((data >= bins[i]) & (data < bins[i+1]))
        pct = count / len(data) * 100
        logger.info(f"  [{bins[i]:5.0f} ~ {bins[i+1]:5.0f}): {count:7,} ({pct:5.2f}%)")
    
    min_count = np.sum(data == min_range)
    max_count = np.sum(data == max_range)
    
    if min_count > 0:
        min_pct = min_count / len(data) * 100
        logger.info(f"\nConcentration at min value {min_range}: {min_count:,} ({min_pct:.2f}%)")
    
    if max_count > 0:
        max_pct = max_count / len(data) * 100
        logger.info(f"Concentration at max value {max_range}: {max_count:,} ({max_pct:.2f}%)")


# ============================
# Main Process
# ============================

def main():
    logger.info("="*60)
    logger.info("NAR-SI3.0 Index Normalizer Training (Windows)")
    logger.info("="*60)
    
    DEFAULT_DATA_PATH = r'E:\UmaData\nar-analytics-python-v2\data-1768047611955.csv'
    DEFAULT_START_DATE = '20231013'
    DEFAULT_END_DATE = '20251231'
    DEFAULT_SAMPLE_RATE = 1.0
    DEFAULT_OUTPUT_DIR = 'models/normalizers'
    
    print("\n" + "="*60)
    print("Settings (Press Enter for defaults)")
    print("="*60)
    
    data_path = input(f"Data file path [{DEFAULT_DATA_PATH}]: ").strip()
    data_path = data_path if data_path else DEFAULT_DATA_PATH
    
    start_date = input(f"Start date (YYYYMMDD) [{DEFAULT_START_DATE}]: ").strip()
    start_date = start_date if start_date else DEFAULT_START_DATE
    
    end_date = input(f"End date (YYYYMMDD) [{DEFAULT_END_DATE}]: ").strip()
    end_date = end_date if end_date else DEFAULT_END_DATE
    
    sample_rate_input = input(f"Sample rate (0.0-1.0) [{DEFAULT_SAMPLE_RATE}]: ").strip()
    sample_rate = float(sample_rate_input) if sample_rate_input else DEFAULT_SAMPLE_RATE
    
    output_dir = input(f"Output directory [{DEFAULT_OUTPUT_DIR}]: ").strip()
    output_dir = output_dir if output_dir else DEFAULT_OUTPUT_DIR
    
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        return
    
    logger.info("\n" + "="*60)
    logger.info("Step 1: Load and preprocess data")
    logger.info("="*60)
    
    df = load_and_filter_data(data_path, start_date, end_date, sample_rate)
    
    if len(df) == 0:
        logger.error("No valid data")
        return
    
    logger.info("\n" + "="*60)
    logger.info("Step 2: Calculate indices")
    logger.info("="*60)
    
    index_df = calculate_all_indices(df)
    
    if len(index_df) == 0:
        logger.error("Index calculation failed")
        return
    
    logger.info("\n" + "="*60)
    logger.info("Step 3: Pre-normalization distribution")
    logger.info("="*60)
    
    analyze_distribution(index_df['ten_index'].values, 'Ten Index')
    analyze_distribution(index_df['agari_index'].values, 'Agari Index')
    analyze_distribution(index_df['position_index'].values, 'Position Index')
    analyze_distribution(index_df['pace_index'].values, 'Pace Index')
    
    logger.info("\n" + "="*60)
    logger.info("Step 4: Train normalizers")
    logger.info("="*60)
    
    os.makedirs(output_dir, exist_ok=True)
    
    normalizers = {}
    
    logger.info("\nTraining Ten Index normalizer...")
    ten_normalizer = RacingIndexNormalizer()
    ten_normalizer.fit(index_df['ten_index'].values)
    ten_path = os.path.join(output_dir, 'ten_index_normalizer.pkl')
    ten_normalizer.save(ten_path)
    normalizers['ten'] = ten_normalizer
    
    logger.info("\nTraining Agari Index normalizer...")
    agari_normalizer = RacingIndexNormalizer()
    agari_normalizer.fit(index_df['agari_index'].values)
    agari_path = os.path.join(output_dir, 'agari_index_normalizer.pkl')
    agari_normalizer.save(agari_path)
    normalizers['agari'] = agari_normalizer
    
    logger.info("\nTraining Position Index normalizer...")
    position_normalizer = RacingIndexNormalizer(target_range=(0, 100))
    position_normalizer.fit(index_df['position_index'].values)
    position_path = os.path.join(output_dir, 'position_index_normalizer.pkl')
    position_normalizer.save(position_path)
    normalizers['position'] = position_normalizer
    
    logger.info("\nTraining Pace Index normalizer...")
    pace_normalizer = RacingIndexNormalizer()
    pace_normalizer.fit(index_df['pace_index'].values)
    pace_path = os.path.join(output_dir, 'pace_index_normalizer.pkl')
    pace_normalizer.save(pace_path)
    normalizers['pace'] = pace_normalizer
    
    logger.info("\n" + "="*60)
    logger.info("Step 5: Post-normalization distribution")
    logger.info("="*60)
    
    ten_normalized = ten_normalizer.transform(index_df['ten_index'].values)
    agari_normalized = agari_normalizer.transform(index_df['agari_index'].values)
    position_normalized = position_normalizer.transform(index_df['position_index'].values)
    pace_normalized = pace_normalizer.transform(index_df['pace_index'].values)
    
    analyze_distribution(ten_normalized, 'Ten Index (Normalized)')
    analyze_distribution(agari_normalized, 'Agari Index (Normalized)')
    analyze_distribution(position_normalized, 'Position Index (Normalized)')
    analyze_distribution(pace_normalized, 'Pace Index (Normalized)')
    
    logger.info("\n" + "="*60)
    logger.info("Training completed successfully!")
    logger.info("="*60)
    logger.info(f"\nOutput directory: {output_dir}")
    logger.info(f"  - {ten_path}")
    logger.info(f"  - {agari_path}")
    logger.info(f"  - {position_path}")
    logger.info(f"  - {pace_path}")
    
    logger.info("\nNext steps:")
    logger.info("  1. Verify model files")
    logger.info("  2. Integrate into prediction pipeline")
    logger.info("  3. Evaluate performance")
    
    logger.info("\nPlay to Win!")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nProcess interrupted")
    except Exception as e:
        logger.error(f"\nError occurred: {e}")
        import traceback
        traceback.print_exc()
