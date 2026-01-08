"""
Layer 3: 機械学習モデル訓練スクリプト

LightGBMを使用して前半3F推定モデルを訓練する
訓練データ: 1400m以上でcorner_1が有効なデータ（直近3ヶ月）

Author: AI戦略家（NAR-AI-YOSO開発チーム）
Date: 2026-01-08
"""

import psycopg2
import pandas as pd
import numpy as np
from lightgbm import LGBMRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import joblib
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトルート
PROJECT_ROOT = Path(__file__).parent.parent
MODEL_DIR = PROJECT_ROOT / "models"
MODEL_DIR.mkdir(exist_ok=True)


def load_training_data(conn_params: dict) -> pd.DataFrame:
    """
    訓練データの取得
    
    条件:
    - 1400m以上
    - corner_1が有効（corner_1 > 0）
    - 直近3ヶ月（2025-10-07 〜 2026-01-07）
    
    Returns:
        訓練データのDataFrame
    """
    logger.info("訓練データを取得中...")
    
    query = """
    SELECT 
        se.kaisai_nen || se.kaisai_tsukihi as race_date,
        se.keibajo_code,
        se.race_bango,
        se.ketto_toroku_bango,
        CAST(ra.kyori AS INTEGER) as kyori,
        ra.track_code,
        ra.babajotai_code_dirt as baba_code,
        -- 走破タイム（秒）
        CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
        CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
        CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0 as time_seconds,
        -- 上がり3F（秒）
        CAST(se.kohan_3f AS NUMERIC) / 10.0 as kohan_3f_seconds,
        -- コーナー順位
        CAST(se.corner_1 AS INTEGER) as corner_1,
        CAST(se.corner_2 AS INTEGER) as corner_2,
        CAST(se.corner_3 AS INTEGER) as corner_3,
        CAST(se.corner_4 AS INTEGER) as corner_4,
        -- 実測前半3F（1200mデータから推定）
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0) as actual_ten_3f
    FROM nvd_se se
    JOIN nvd_ra ra 
        ON se.kaisai_nen = ra.kaisai_nen 
        AND se.kaisai_tsukihi = ra.kaisai_tsukihi
        AND se.keibajo_code = ra.keibajo_code
        AND se.race_bango = ra.race_bango
    WHERE CAST(ra.kyori AS INTEGER) >= 1400
      AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
      AND se.soha_time IS NOT NULL 
      AND se.soha_time != '0000'
      AND se.kohan_3f IS NOT NULL 
      AND se.kohan_3f != '000'
      AND se.corner_1 IS NOT NULL
      AND CAST(se.corner_1 AS INTEGER) > 0
      AND se.corner_2 IS NOT NULL
      AND CAST(se.corner_2 AS INTEGER) > 0
    ORDER BY race_date DESC;
    """
    
    conn = psycopg2.connect(**conn_params)
    df = pd.read_sql(query, conn)
    conn.close()
    
    logger.info(f"訓練データ取得完了: {len(df)}件")
    logger.info(f"距離分布:\n{df['kyori'].value_counts().sort_index()}")
    logger.info(f"期間: {df['race_date'].min()} 〜 {df['race_date'].max()}")
    
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    特徴量エンジニアリング
    
    Args:
        df: 元データ
    
    Returns:
        特徴量追加後のDataFrame
    """
    logger.info("特徴量エンジニアリング中...")
    
    # 基本統計量
    df['avg_speed'] = df['kyori'] / df['time_seconds']  # 平均速度
    df['early_position'] = (df['corner_1'] + df['corner_2']) / 2.0  # 前半平均順位
    df['late_position'] = (df['corner_3'] + df['corner_4']) / 2.0  # 後半平均順位
    df['position_change'] = df['early_position'] - df['late_position']  # 順位変動
    
    # 距離カテゴリ
    df['distance_category'] = pd.cut(
        df['kyori'], 
        bins=[0, 1400, 1600, 1800, 3000],
        labels=['sprint', 'mile', 'middle', 'long']
    )
    
    # 馬場状態（カテゴリ変数をダミー化）
    df['baba_良'] = (df['baba_code'] == '0').astype(int)
    df['baba_稍重'] = (df['baba_code'] == '1').astype(int)
    df['baba_重'] = (df['baba_code'] == '2').astype(int)
    df['baba_不良'] = (df['baba_code'] == '3').astype(int)
    
    logger.info(f"特徴量エンジニアリング完了: {df.shape[1]}カラム")
    
    return df


def train_lightgbm(df: pd.DataFrame) -> LGBMRegressor:
    """
    LightGBMモデルの訓練
    
    Args:
        df: 訓練データ
    
    Returns:
        訓練済みモデル
    """
    logger.info("LightGBMモデルを訓練中...")
    
    # 特徴量とターゲットの分離
    feature_cols = [
        'time_seconds', 'kohan_3f_seconds', 'kyori',
        'corner_1', 'corner_2', 'corner_3', 'corner_4',
        'avg_speed', 'early_position', 'late_position', 'position_change',
        'baba_良', 'baba_稍重', 'baba_重', 'baba_不良'
    ]
    
    X = df[feature_cols]
    y = df['actual_ten_3f']
    
    # 訓練データとテストデータに分割
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    logger.info(f"訓練データ: {len(X_train)}件, テストデータ: {len(X_test)}件")
    
    # LightGBMパラメータ（調査報告書より）
    params = {
        'objective': 'regression',
        'metric': 'rmse',
        'learning_rate': 0.05,
        'num_leaves': 31,
        'max_depth': -1,
        'min_child_samples': 20,
        'n_estimators': 500,
        'random_state': 42,
        'verbose': -1
    }
    
    # モデル訓練
    model = LGBMRegressor(**params)
    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        eval_metric='rmse',
        callbacks=[
            # early_stopping(stopping_rounds=50)
        ]
    )
    
    # 予測と評価
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    train_rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))
    test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
    train_mae = mean_absolute_error(y_train, y_pred_train)
    test_mae = mean_absolute_error(y_test, y_pred_test)
    
    logger.info(f"訓練データ RMSE: {train_rmse:.4f}秒, MAE: {train_mae:.4f}秒")
    logger.info(f"テストデータ RMSE: {test_rmse:.4f}秒, MAE: {test_mae:.4f}秒")
    
    # 特徴量の重要度
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    logger.info(f"特徴量の重要度（Top 5）:\n{feature_importance.head()}")
    
    return model


def save_model(model: LGBMRegressor, model_path: Path):
    """
    モデルの保存
    
    Args:
        model: 訓練済みモデル
        model_path: 保存先パス
    """
    joblib.dump(model, model_path)
    logger.info(f"モデル保存完了: {model_path}")


def main():
    """メイン処理"""
    logger.info("=" * 80)
    logger.info("Layer 3: LightGBMモデル訓練開始")
    logger.info("=" * 80)
    
    # DB接続パラメータ
    conn_params = {
        'host': 'localhost',
        'database': 'nar_keiba',
        'user': 'postgres',
        'password': 'postgres'
    }
    
    try:
        # 1. 訓練データ取得
        df = load_training_data(conn_params)
        
        if len(df) < 100:
            logger.error("訓練データが不足しています（最低100件必要）")
            return
        
        # 2. 特徴量エンジニアリング
        df = engineer_features(df)
        
        # 3. モデル訓練
        model = train_lightgbm(df)
        
        # 4. モデル保存
        model_path = MODEL_DIR / "ten_3f_lgbm_model.pkl"
        save_model(model, model_path)
        
        logger.info("=" * 80)
        logger.info("Layer 3: LightGBMモデル訓練完了 ✅")
        logger.info("=" * 80)
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
