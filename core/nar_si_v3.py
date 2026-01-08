"""
NAR-SI Ver.3.0 計算エンジン（統合版）

目的: スピード指数（NAR-SI）を計算
範囲: 0.0 〜 100.0（平均50.0）
基準: 標準的な走破タイムを50.0とした相対評価

計算式:
    NAR-SI = 基準値 + (基準タイム - 実走タイム) × 補正係数

作成日: 2026-01-08
統合元: /home/user/webapp/core/nar_si_v3_*.py
"""

import sys
import os
sys.path.append('/home/user/webapp/nar-ai-yoso')

import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ============================
# 1. 定数定義
# ============================

# 南関東4場の定義
NANKANTO_VENUES = ['42', '43', '44', '45']

# 基準NAR-SI値
BASE_NAR_SI = 50.0

# 補正係数
TIME_COEFFICIENT = 10.0  # 1秒の差 = 10ポイント差


# ============================
# 2. ヘルパー関数
# ============================

def is_nankanto(keibajo_code: str) -> bool:
    """
    南関東4場かどうかを判定
    
    Args:
        keibajo_code: 競馬場コード
    
    Returns:
        bool: 南関東4場ならTrue
    """
    return str(keibajo_code) in NANKANTO_VENUES


def calculate_trend(values: List[float]) -> float:
    """
    トレンド指標を計算（最新値から最古値への変化）
    
    Args:
        values: 数値リスト（新しい順）
    
    Returns:
        float: トレンド値（正=上昇、負=下降）
    """
    if len(values) < 2:
        return 0.0
    
    # 線形回帰の傾き
    x = np.arange(len(values))
    y = np.array(values)
    
    if len(x) == 0 or len(y) == 0:
        return 0.0
    
    try:
        # 最小二乗法で傾きを計算
        slope = np.polyfit(x, y, 1)[0]
        return float(slope)
    except:
        return 0.0


def safe_float(value, default=0.0):
    """文字列を安全にfloatに変換"""
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """文字列を安全にintに変換"""
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


# ============================
# 3. NAR-SI計算（簡易版）
# ============================

def calculate_nar_si_simple(
    actual_time: float,
    base_time: float,
    baba_correction: float = 0.0
) -> float:
    """
    NAR-SIを簡易計算
    
    Args:
        actual_time: 実走タイム（秒）
        base_time: 基準タイム（秒）
        baba_correction: 馬場差補正（秒）
    
    Returns:
        float: NAR-SI値（0.0 〜 100.0）
    """
    # 基本計算
    time_diff = base_time - actual_time
    nar_si = BASE_NAR_SI + (time_diff + baba_correction) * TIME_COEFFICIENT
    
    # 範囲制限
    nar_si = max(0.0, min(100.0, nar_si))
    
    return round(nar_si, 1)


# ============================
# 4. 特徴量生成
# ============================

def generate_nar_si_features(
    past_races: List[Dict],
    current_race_info: Dict
) -> Dict[str, float]:
    """
    NAR-SI Ver.3.0の特徴量を生成
    
    Args:
        past_races: 過去3走のデータリスト（新しい順）
        current_race_info: 今回のレース情報
    
    Returns:
        dict: NAR-SI特徴量
    """
    features = {}
    
    # 過去走数（データ不足対策）
    features['past_race_count'] = len(past_races)
    
    # 過去3走のNAR-SI
    for i, race in enumerate(past_races[:3], 1):
        features[f'prev{i}_nar_si'] = race.get('nar_si', BASE_NAR_SI)
    
    # データ不足の場合は平均値で埋める
    if len(past_races) < 3:
        avg_nar_si = np.mean([r.get('nar_si', BASE_NAR_SI) for r in past_races]) if past_races else BASE_NAR_SI
        for i in range(len(past_races) + 1, 4):
            features[f'prev{i}_nar_si'] = avg_nar_si
    
    # 過去3走の着順
    for i, race in enumerate(past_races[:3], 1):
        finish = race.get('kakutei_chakujun', '99')
        features[f'prev{i}_finish'] = safe_int(finish, 99)
    
    if len(past_races) < 3:
        for i in range(len(past_races) + 1, 4):
            features[f'prev{i}_finish'] = 99
    
    # 過去3走の馬体重
    for i, race in enumerate(past_races[:3], 1):
        features[f'prev{i}_weight'] = race.get('bataiju', 450)
    
    if len(past_races) < 3:
        avg_weight = np.mean([r.get('bataiju', 450) for r in past_races]) if past_races else 450
        for i in range(len(past_races) + 1, 4):
            features[f'prev{i}_weight'] = int(avg_weight)
    
    # NAR-SIのトレンド指標
    nar_si_values = [race.get('nar_si', BASE_NAR_SI) for race in past_races[:3]]
    if len(nar_si_values) >= 2:
        features['nar_si_trend'] = calculate_trend(nar_si_values)
        features['nar_si_avg'] = float(np.mean(nar_si_values))
        features['nar_si_std'] = float(np.std(nar_si_values))
    else:
        features['nar_si_trend'] = 0.0
        features['nar_si_avg'] = nar_si_values[0] if nar_si_values else BASE_NAR_SI
        features['nar_si_std'] = 0.0
    
    # 馬体重の変化
    if len(past_races) >= 2:
        weight1 = past_races[0].get('bataiju', 450)
        weight2 = past_races[1].get('bataiju', 450)
        features['weight_change'] = weight1 - weight2
    else:
        features['weight_change'] = 0
    
    # 条件適性
    current_venue = current_race_info.get('keibajo_code', '')
    current_kyori = safe_int(current_race_info.get('kyori', 1600))
    
    # 同競馬場率
    same_venue_count = sum(1 for r in past_races[:3] if r.get('keibajo_code') == current_venue)
    features['same_venue_rate'] = same_venue_count / min(3, len(past_races)) if past_races else 0.0
    
    return features


# ============================
# 5. メイン計算関数
# ============================

def calculate_nar_si_v3(
    horse_data: Dict,
    past_races: Optional[List[Dict]] = None,
    race_info: Optional[Dict] = None
) -> Tuple[float, Dict]:
    """
    NAR-SI Ver.3.0を計算
    
    Args:
        horse_data: 馬データ
            - time_seconds: 走破タイム（秒）
            - base_time: 基準タイム（秒）
            - bataiju: 馬体重
            - etc.
        past_races: 過去3走のデータリスト（オプション）
        race_info: レース情報（オプション）
    
    Returns:
        tuple: (NAR-SI値, 特徴量dict)
    """
    # 基本NAR-SI計算
    actual_time = safe_float(horse_data.get('time_seconds'))
    base_time = safe_float(horse_data.get('base_time'), 96.0)  # デフォルト: 1600m 96秒
    
    # 馬場差補正（簡易版）
    baba_code = horse_data.get('babajotai_code_dirt', '1')
    baba_correction = 0.0  # 簡易版では補正なし（将来拡張可能）
    
    # NAR-SI計算
    nar_si = calculate_nar_si_simple(actual_time, base_time, baba_correction)
    
    # 特徴量生成（過去走データがある場合）
    features = {}
    if past_races and race_info:
        features = generate_nar_si_features(past_races, race_info)
        features['current_nar_si'] = nar_si
    
    return (nar_si, features)


# ============================
# 6. テスト関数
# ============================

if __name__ == '__main__':
    print("=" * 80)
    print("NAR-SI Ver.3.0 計算エンジン テスト")
    print("=" * 80)
    
    # テストデータ
    test_horse = {
        'time_seconds': 96.5,
        'base_time': 96.0,
        'babajotai_code_dirt': '1',
        'bataiju': 460
    }
    
    test_past_races = [
        {'nar_si': 52.0, 'kakutei_chakujun': '3', 'bataiju': 458, 'keibajo_code': '42'},
        {'nar_si': 50.5, 'kakutei_chakujun': '5', 'bataiju': 460, 'keibajo_code': '42'},
        {'nar_si': 48.0, 'kakutei_chakujun': '7', 'bataiju': 462, 'keibajo_code': '43'},
    ]
    
    test_race_info = {
        'keibajo_code': '42',
        'kyori': 1600
    }
    
    # NAR-SI計算
    nar_si, features = calculate_nar_si_v3(
        test_horse,
        test_past_races,
        test_race_info
    )
    
    print(f"\n✅ NAR-SI Ver.3.0: {nar_si}")
    print("\n特徴量:")
    for key, value in features.items():
        print(f"  - {key}: {value}")
    
    print("\n" + "=" * 80)
