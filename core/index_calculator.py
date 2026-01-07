"""
HQS指数計算エンジン（地方競馬版）

JRDB指数体系を地方競馬に適用した5つの指数を計算する：
1. テン指数（Ten Index）: 初期加速力
2. 位置指数（Position Index）: レース中の平均ポジション
3. 上がり指数（Agari Index）: ラストスパート能力
4. ペース指数（Pace Index）: レース全体のペース配分
5. 予想脚質（Predicted Leg Type）: 戦術的傾向

作成日: 2026-01-07
作成者: AI戦略家（CSO兼クリエイティブディレクター）
"""

import math
import sys
import os
from typing import Dict, Optional, List, Tuple
import logging

# config/base_times.py をインポート
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.base_times import BASE_TIMES, BABA_CORRECTION, ORGANIZERS, get_base_time as config_get_base_time

logger = logging.getLogger(__name__)


# ============================
# 2. ヘルパー関数
# ============================

def safe_float(value, default: float = 0.0) -> float:
    """安全なfloat変換"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default: int = 0) -> int:
    """安全なint変換"""
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def get_base_time(keibajo_code: str, kyori: int, time_type: str) -> float:
    """
    基準タイムを取得（config/base_times.pyから）
    
    Args:
        keibajo_code: 競馬場コード（30-65）
        kyori: 距離（m）
        time_type: 'zenhan_3f' or 'kohan_3f'
    
    Returns:
        基準タイム（秒）
    """
    return config_get_base_time(keibajo_code, kyori, time_type)


def get_baba_correction_value(baba_code: str) -> float:
    """
    馬場差補正値を取得
    
    Args:
        baba_code: 馬場状態コード（'1'-'4'）
    
    Returns:
        補正値（秒）
    """
    return BABA_CORRECTION.get(baba_code, 0.0)


# ============================
# 3. テン指数計算
# ============================

def calculate_ten_index(
    zenhan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str
) -> float:
    """
    テン指数を計算
    
    テン指数 = ((基準3Fタイム - 実走3Fタイム) + 馬場差補正) × 10
    
    Args:
        zenhan_3f: 前半3Fタイム（秒）
        kyori: 距離（m）
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
    
    Returns:
        テン指数（-100 〜 +100）
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'zenhan_3f')
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # テン指数計算
    ten_index = ((base_time - zenhan_3f) + baba_correction) * 10
    
    # 範囲制限
    ten_index = max(-100, min(100, ten_index))
    
    logger.debug(f"テン指数: {ten_index:.1f} (3F={zenhan_3f}s, 基準={base_time}s, 馬場補正={baba_correction}s)")
    
    return round(ten_index, 1)


# ============================
# 4. 位置指数計算
# ============================

def calculate_position_index(
    corner_1: int,
    corner_2: int,
    corner_3: int,
    corner_4: int,
    tosu: int
) -> float:
    """
    位置指数を計算
    
    位置指数 = (平均通過順位 / 出走頭数) × 100
    
    Args:
        corner_1: 1コーナー通過順位
        corner_2: 2コーナー通過順位
        corner_3: 3コーナー通過順位
        corner_4: 4コーナー通過順位
        tosu: 出走頭数
    
    Returns:
        位置指数（0 〜 100、小さいほど先頭に近い）
    """
    # 有効なコーナー順位のみ使用
    valid_corners = [c for c in [corner_1, corner_2, corner_3, corner_4] if c > 0]
    
    if not valid_corners:
        logger.warning("コーナー順位データなし")
        return 50.0
    
    # 平均通過順位
    avg_position = sum(valid_corners) / len(valid_corners)
    
    # 位置指数（0-100の範囲に正規化）
    position_index = (avg_position / tosu) * 100 if tosu > 0 else 50.0
    
    logger.debug(f"位置指数: {position_index:.1f} (平均順位={avg_position:.1f}/{tosu}頭)")
    
    return round(position_index, 1)


# ============================
# 5. 上がり指数計算
# ============================

def calculate_agari_index(
    kohan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str
) -> float:
    """
    上がり指数を計算
    
    上がり指数 = ((基準後半3Fタイム - 実走後半3Fタイム) + 馬場差補正) × 10
    
    Args:
        kohan_3f: 後半3Fタイム（秒）
        kyori: 距離（m）
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
    
    Returns:
        上がり指数（-100 〜 +100）
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'kohan_3f')
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # 上がり指数計算
    agari_index = ((base_time - kohan_3f) + baba_correction) * 10
    
    # 範囲制限
    agari_index = max(-100, min(100, agari_index))
    
    logger.debug(f"上がり指数: {agari_index:.1f} (3F={kohan_3f}s, 基準={base_time}s, 馬場補正={baba_correction}s)")
    
    return round(agari_index, 1)


# ============================
# 6. ペース指数計算
# ============================

def calculate_pace_index(
    ten_index: float,
    agari_index: float,
    zenhan_3f: float,
    kohan_3f: float
) -> float:
    """
    ペース指数を計算
    
    ペース指数 = (テン指数 + 上がり指数) / 2 + ペース配分補正
    ペース配分補正 = (0.35 - zenhan_3f/kohan_3f) × 10
    
    Args:
        ten_index: テン指数
        agari_index: 上がり指数
        zenhan_3f: 前半3Fタイム（秒）
        kohan_3f: 後半3Fタイム（秒）
    
    Returns:
        ペース指数（-100 〜 +100）
    """
    # 基本ペース指数（テンと上がりの平均）
    base_pace = (ten_index + agari_index) / 2
    
    # ペース比率補正
    pace_ratio = zenhan_3f / kohan_3f if kohan_3f > 0 else 1.0
    pace_correction = (0.35 - pace_ratio) * 10
    
    # ペース指数計算
    pace_index = base_pace + pace_correction
    
    # 範囲制限
    pace_index = max(-100, min(100, pace_index))
    
    logger.debug(f"ペース指数: {pace_index:.1f} (基本={base_pace:.1f}, ペース比={pace_ratio:.2f}, 補正={pace_correction:.1f})")
    
    return round(pace_index, 1)


# ============================
# 7. 予想脚質判定
# ============================

def predict_ashishitsu(
    past_corners: List[Tuple[int, int, int, int]],
    current_members: Optional[List[Dict]] = None
) -> str:
    """
    予想脚質を判定
    
    過去3走の通過順位パターンから脚質を判定
    
    Args:
        past_corners: 過去の通過順位リスト [(c1, c2, c3, c4), ...]
        current_members: 今回のメンバー構成（相対評価用）
    
    Returns:
        予想脚質（'逃', '先', '差', '追', '好', '自'）
    """
    if not past_corners:
        logger.warning("過去通過順位データなし")
        return '自'
    
    # 過去3走の平均通過順位を計算
    all_positions = []
    for corners in past_corners[:3]:  # 最新3走
        valid_corners = [c for c in corners if c > 0]
        if valid_corners:
            all_positions.extend(valid_corners)
    
    if not all_positions:
        return '自'
    
    avg_position = sum(all_positions) / len(all_positions)
    
    # 脚質判定
    if avg_position <= 2.0:
        ashishitsu = '逃'
    elif avg_position <= 4.0:
        ashishitsu = '先'
    elif avg_position <= 8.0:
        if avg_position <= 6.0:
            ashishitsu = '好'
        else:
            ashishitsu = '差'
    else:
        ashishitsu = '追'
    
    logger.debug(f"予想脚質: {ashishitsu} (平均順位={avg_position:.1f})")
    
    return ashishitsu


# ============================
# 8. 統合計算関数
# ============================

def calculate_all_indexes(horse_data: Dict) -> Dict:
    """
    1頭分の全指数を一括計算
    
    Args:
        horse_data: 馬データ
            必須キー: zenhan_3f, kohan_3f, corner_1-4, kyori, 
                     babajotai_code_dirt, keibajo_code, tosu
    
    Returns:
        指数データ
            {
                'ten_index': float,
                'position_index': float,
                'agari_index': float,
                'pace_index': float,
                'ashishitsu': str
            }
    """
    try:
        # データ取得
        zenhan_3f = safe_float(horse_data.get('zenhan_3f'))
        kohan_3f = safe_float(horse_data.get('kohan_3f'))
        corner_1 = safe_int(horse_data.get('corner_1'))
        corner_2 = safe_int(horse_data.get('corner_2'))
        corner_3 = safe_int(horse_data.get('corner_3'))
        corner_4 = safe_int(horse_data.get('corner_4'))
        kyori = safe_int(horse_data.get('kyori'), 1600)
        baba_code = str(horse_data.get('babajotai_code_dirt', '1'))
        keibajo_code = str(horse_data.get('keibajo_code', '42'))
        tosu = safe_int(horse_data.get('tosu'), 12)
        
        # 各指数を計算
        ten_index = calculate_ten_index(zenhan_3f, kyori, baba_code, keibajo_code)
        position_index = calculate_position_index(corner_1, corner_2, corner_3, corner_4, tosu)
        agari_index = calculate_agari_index(kohan_3f, kyori, baba_code, keibajo_code)
        pace_index = calculate_pace_index(ten_index, agari_index, zenhan_3f, kohan_3f)
        
        # 予想脚質（過去データがある場合）
        past_corners = horse_data.get('past_corners', [])
        ashishitsu = predict_ashishitsu(past_corners)
        
        return {
            'ten_index': ten_index,
            'position_index': position_index,
            'agari_index': agari_index,
            'pace_index': pace_index,
            'ashishitsu': ashishitsu
        }
    
    except Exception as e:
        logger.error(f"指数計算エラー: {e}")
        return {
            'ten_index': 0.0,
            'position_index': 50.0,
            'agari_index': 0.0,
            'pace_index': 0.0,
            'ashishitsu': '自'
        }


# ============================
# 9. テスト用メイン関数
# ============================

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.DEBUG)
    
    # テストデータ
    test_horse = {
        'zenhan_3f': 35.0,
        'kohan_3f': 37.5,
        'corner_1': 2,
        'corner_2': 2,
        'corner_3': 3,
        'corner_4': 2,
        'kyori': 1600,
        'babajotai_code_dirt': '1',
        'keibajo_code': '42',
        'tosu': 12,
        'past_corners': [
            (2, 2, 3, 2),
            (1, 1, 2, 1),
            (3, 3, 3, 4)
        ]
    }
    
    # 指数計算
    indexes = calculate_all_indexes(test_horse)
    
    print("\n=== HQS指数計算結果 ===")
    print(f"テン指数:   {indexes['ten_index']:.1f}")
    print(f"位置指数:   {indexes['position_index']:.1f}")
    print(f"上がり指数: {indexes['agari_index']:.1f}")
    print(f"ペース指数: {indexes['pace_index']:.1f}")
    print(f"予想脚質:   {indexes['ashishitsu']}")
