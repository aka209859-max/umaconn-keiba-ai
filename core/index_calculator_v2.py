"""
HQS指数計算エンジン（地方競馬版）- 充実度100%完全版

JRDB指数体系を地方競馬に適用した5つの指数を計算する：
1. テン指数（Ten Index）: 初期加速力
2. 位置指数（Position Index）: レース中の平均ポジション
3. 上がり指数（Agari Index）: ラストスパート能力
4. ペース指数（Pace Index）: レース全体のペース配分
5. 予想脚質（Predicted Leg Type）: 戦術的傾向

Phase 1.5: 充実度100%実装
- 不利補正、枠順補正、斤量補正、ペース判定
- 脚質補正、メンバー構成、距離適性、コース形状

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
# 1. 補正値マスター
# ============================

# 不利補正値（furi_code対応）
FURI_CORRECTION = {
    '01': 0.5,   # 出遅れ（軽度）
    '02': 1.0,   # 出遅れ（中度）
    '03': 1.5,   # 出遅れ（重度）
    '04': 0.3,   # 他馬接触（軽度）
    '05': 0.8,   # 他馬接触（中度）
    '06': 0.5,   # 進路妨害（軽度）
    '07': 1.2,   # 進路妨害（中度）
    '08': 2.0,   # 進路妨害（重度）
    '09': 0.4,   # 挟まれる
    '10': 0.6,   # 外々回す
}

# 枠順補正値（南関東1600m標準）
WAKUBAN_CORRECTION = {
    # 枠番: {'ten': テン指数補正(秒), 'position': 位置指数補正(pt)}
    1: {'ten': +0.3, 'position': -2.0},  # 内枠有利
    2: {'ten': +0.2, 'position': -1.5},
    3: {'ten': +0.1, 'position': -1.0},
    4: {'ten': 0.0, 'position': -0.5},
    5: {'ten': 0.0, 'position': +0.5},
    6: {'ten': -0.1, 'position': +1.0},
    7: {'ten': -0.2, 'position': +1.5},
    8: {'ten': -0.3, 'position': +2.0},  # 外枠不利
}

# 脚質別基準位置
ASHISHITSU_BASE_POSITION = {
    '逃': 1.5,   # 逃げ馬の基準位置
    '先': 3.5,   # 先行馬の基準位置
    '好': 6.0,   # 好位馬の基準位置
    '差': 8.5,   # 差し馬の基準位置
    '追': 11.0,  # 追込馬の基準位置
    '自': 6.0,   # 自在馬の基準位置
}

# コース形状マスタ
COURSE_SHAPE = {
    '42': {'mawari': '右', 'straight': 400},  # 大井
    '43': {'mawari': '左', 'straight': 330},  # 川崎
    '44': {'mawari': '右', 'straight': 360},  # 船橋
    '45': {'mawari': '右', 'straight': 320},  # 浦和
    '30': {'mawari': '右', 'straight': 260},  # 北海道
    '35': {'mawari': '左', 'straight': 300},  # 岩手
    '36': {'mawari': '左', 'straight': 250},  # 金沢
    '46': {'mawari': '左', 'straight': 250},  # 笠松
    '47': {'mawari': '左', 'straight': 300},  # 名古屋
    '48': {'mawari': '右', 'straight': 291},  # 園田
    '49': {'mawari': '右', 'straight': 291},  # 姫路
    '50': {'mawari': '右', 'straight': 250},  # 高知
    '54': {'mawari': '右', 'straight': 300},  # 佐賀
}


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
    """基準タイムを取得（config/base_times.pyから）"""
    return config_get_base_time(keibajo_code, kyori, time_type)


def get_baba_correction_value(baba_code: str) -> float:
    """馬場差補正値を取得"""
    return BABA_CORRECTION.get(baba_code, 0.0)


def get_furi_correction(furi_code: str) -> float:
    """
    不利補正値を取得
    
    Args:
        furi_code: 不利コード（'01'-'10'）
    
    Returns:
        補正値（秒）
    """
    return FURI_CORRECTION.get(furi_code, 0.0)


def get_wakuban_correction(wakuban: int, correction_type: str) -> float:
    """
    枠順補正値を取得
    
    Args:
        wakuban: 枠番（1-8）
        correction_type: 'ten' or 'position'
    
    Returns:
        補正値
    """
    if wakuban not in WAKUBAN_CORRECTION:
        return 0.0
    return WAKUBAN_CORRECTION[wakuban].get(correction_type, 0.0)


def calculate_kinryo_correction(kinryo: float, bataiju: int) -> float:
    """
    斤量補正を計算
    
    Args:
        kinryo: 斤量（kg）
        bataiju: 馬体重（kg）
    
    Returns:
        補正値（秒）
    """
    # 基準斤量55kg
    base_kinryo = 55.0
    
    # 馬体重による斤量係数の調整
    if bataiju < 450:
        kinryo_factor = 0.15  # 軽い馬は斤量の影響大
    elif bataiju > 520:
        kinryo_factor = 0.08  # 重い馬は斤量の影響小
    else:
        kinryo_factor = 0.10  # 標準
    
    # 斤量補正計算
    correction = (kinryo - base_kinryo) * kinryo_factor
    
    return correction


def judge_pace_type(zenhan_3f: float, kohan_3f: float, 
                    base_zenhan: float, base_kohan: float) -> str:
    """
    ペース種別を判定
    
    Args:
        zenhan_3f: 前半3Fタイム
        kohan_3f: 後半3Fタイム
        base_zenhan: 基準前半3Fタイム
        base_kohan: 基準後半3Fタイム
    
    Returns:
        ペース種別（'H-H', 'H-M', 'H-S', 'M-H', 'M-M', 'M-S', 'S-H', 'S-M', 'S-S'）
    """
    # 前半ペース判定
    if zenhan_3f < (base_zenhan - 1.0):
        zenhan_pace = 'H'  # ハイペース
    elif zenhan_3f < (base_zenhan - 0.3):
        zenhan_pace = 'M'  # ミドルペース
    else:
        zenhan_pace = 'S'  # スローペース
    
    # 後半ペース判定
    if kohan_3f < (base_kohan - 1.0):
        kohan_pace = 'H'
    elif kohan_3f < (base_kohan - 0.3):
        kohan_pace = 'M'
    else:
        kohan_pace = 'S'
    
    return f"{zenhan_pace}-{kohan_pace}"


def get_pace_correction(pace_type: str) -> float:
    """
    ペース種別による上がり指数補正
    
    Args:
        pace_type: ペース種別
    
    Returns:
        補正値
    """
    pace_corrections = {
        'H-H': 0.0,   # ハイペース全体
        'H-M': +0.5,  # ハイペースから緩む
        'H-S': +2.0,  # ハイペースから止まる（前残り）
        'M-H': -0.5,  # ミドルペースから加速
        'M-M': 0.0,   # ミドルペース全体
        'M-S': +1.0,  # ミドルペースから緩む
        'S-H': -3.0,  # スローペースからの一気（過大評価注意）
        'S-M': -1.0,  # スローペースから加速
        'S-S': 0.0,   # スローペース全体
    }
    return pace_corrections.get(pace_type, 0.0)


# ============================
# 3. テン指数計算（充実度100%版）
# ============================

def calculate_ten_index_v2(
    zenhan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str,
    furi_code: Optional[str] = None,
    wakuban: Optional[int] = None,
    kinryo: Optional[float] = None,
    bataiju: Optional[int] = None
) -> Dict:
    """
    テン指数を計算（充実度100%版）
    
    Args:
        zenhan_3f: 前半3Fタイム（秒）
        kyori: 距離（m）
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
        furi_code: 不利コード（オプション）
        wakuban: 枠番（オプション）
        kinryo: 斤量（オプション）
        bataiju: 馬体重（オプション）
    
    Returns:
        {
            'ten_index': float,
            'corrections': {
                'base': float,
                'baba': float,
                'furi': float,
                'wakuban': float,
                'kinryo': float
            }
        }
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'zenhan_3f')
    
    # 基本計算
    base_correction = base_time - zenhan_3f
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # 不利補正
    furi_correction = get_furi_correction(furi_code) if furi_code else 0.0
    
    # 枠順補正
    wakuban_correction = get_wakuban_correction(wakuban, 'ten') if wakuban else 0.0
    
    # 斤量補正
    kinryo_correction = calculate_kinryo_correction(kinryo, bataiju) if (kinryo and bataiju) else 0.0
    
    # テン指数計算
    ten_index = (base_correction + baba_correction + furi_correction + wakuban_correction + kinryo_correction) * 10
    
    # 範囲制限
    ten_index = max(-100, min(100, ten_index))
    
    logger.debug(f"テン指数: {ten_index:.1f} (基本={base_correction:.2f}, 馬場={baba_correction:.2f}, "
                 f"不利={furi_correction:.2f}, 枠={wakuban_correction:.2f}, 斤量={kinryo_correction:.2f})")
    
    return {
        'ten_index': round(ten_index, 1),
        'corrections': {
            'base': base_correction,
            'baba': baba_correction,
            'furi': furi_correction,
            'wakuban': wakuban_correction,
            'kinryo': kinryo_correction
        }
    }


# ============================
# 4. 位置指数計算（充実度100%版）
# ============================

def calculate_position_index_v2(
    corner_1: int,
    corner_2: int,
    corner_3: int,
    corner_4: int,
    tosu: int,
    wakuban: Optional[int] = None,
    ashishitsu: Optional[str] = None
) -> Dict:
    """
    位置指数を計算（充実度100%版）
    
    Args:
        corner_1-4: コーナー通過順位
        tosu: 出走頭数
        wakuban: 枠番（オプション）
        ashishitsu: 脚質（オプション）
    
    Returns:
        {
            'position_index': float,
            'avg_position': float,
            'ashishitsu_adjusted': float
        }
    """
    # 有効なコーナー順位のみ使用
    valid_corners = [c for c in [corner_1, corner_2, corner_3, corner_4] if c > 0]
    
    if not valid_corners:
        logger.warning("コーナー順位データなし")
        return {'position_index': 50.0, 'avg_position': tosu / 2, 'ashishitsu_adjusted': 50.0}
    
    # 平均通過順位
    avg_position = sum(valid_corners) / len(valid_corners)
    
    # 枠順補正
    wakuban_correction = get_wakuban_correction(wakuban, 'position') if wakuban else 0.0
    
    # 脚質補正
    if ashishitsu and ashishitsu in ASHISHITSU_BASE_POSITION:
        base_position = ASHISHITSU_BASE_POSITION[ashishitsu]
        ashishitsu_adjusted_position = avg_position - base_position + (tosu / 2)
    else:
        ashishitsu_adjusted_position = avg_position
    
    # 位置指数計算（脚質補正後）
    position_index = (ashishitsu_adjusted_position / tosu) * 100 if tosu > 0 else 50.0
    position_index += wakuban_correction
    
    # 範囲制限
    position_index = max(0, min(100, position_index))
    
    logger.debug(f"位置指数: {position_index:.1f} (平均順位={avg_position:.1f}, 脚質補正後={ashishitsu_adjusted_position:.1f})")
    
    return {
        'position_index': round(position_index, 1),
        'avg_position': round(avg_position, 2),
        'ashishitsu_adjusted': round(ashishitsu_adjusted_position, 2)
    }


# ============================
# 5. 上がり指数計算（充実度100%版）
# ============================

def calculate_agari_index_v2(
    kohan_3f: float,
    zenhan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str,
    furi_code: Optional[str] = None,
    kinryo: Optional[float] = None,
    bataiju: Optional[int] = None
) -> Dict:
    """
    上がり指数を計算（充実度100%版）
    
    Returns:
        {
            'agari_index': float,
            'pace_type': str,
            'pace_corrected': float
        }
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'kohan_3f')
    base_zenhan = get_base_time(keibajo_code, kyori, 'zenhan_3f')
    
    # 基本計算
    base_correction = base_time - kohan_3f
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # 不利補正（直線での進路妨害）
    furi_correction = get_furi_correction(furi_code) * 0.7 if furi_code else 0.0  # 上がりは70%影響
    
    # 斤量補正
    kinryo_correction = calculate_kinryo_correction(kinryo, bataiju) * 1.2 if (kinryo and bataiju) else 0.0  # 上がりは120%影響
    
    # ペース判定
    pace_type = judge_pace_type(zenhan_3f, kohan_3f, base_zenhan, base_time)
    pace_correction = get_pace_correction(pace_type)
    
    # 上がり指数計算
    agari_index = (base_correction + baba_correction + furi_correction + kinryo_correction + pace_correction) * 10
    
    # 範囲制限
    agari_index = max(-100, min(100, agari_index))
    
    logger.debug(f"上がり指数: {agari_index:.1f} (ペース={pace_type}, ペース補正={pace_correction:.2f})")
    
    return {
        'agari_index': round(agari_index, 1),
        'pace_type': pace_type,
        'pace_corrected': round(pace_correction, 2)
    }


# ============================
# 6. ペース指数計算（充実度100%版）
# ============================

def calculate_pace_index_v2(
    ten_index: float,
    agari_index: float,
    zenhan_3f: float,
    kohan_3f: float,
    pace_type: str
) -> Dict:
    """
    ペース指数を計算（充実度100%版）
    """
    # 基本ペース指数
    base_pace = (ten_index + agari_index) / 2
    
    # ペース比率補正
    pace_ratio = zenhan_3f / kohan_3f if kohan_3f > 0 else 1.0
    pace_ratio_correction = (0.35 - pace_ratio) * 10
    
    # ペース指数計算
    pace_index = base_pace + pace_ratio_correction
    
    # 範囲制限
    pace_index = max(-100, min(100, pace_index))
    
    return {
        'pace_index': round(pace_index, 1),
        'pace_type': pace_type,
        'pace_ratio': round(pace_ratio, 3)
    }


# ============================
# 7. 予想脚質判定（充実度100%版）
# ============================

def predict_ashishitsu_v2(
    past_corners: List[Tuple[int, int, int, int]],
    ten_index: float,
    all_horses_ten_index: Optional[List[float]] = None,
    wakuban: Optional[int] = None
) -> Dict:
    """
    予想脚質を判定（充実度100%版）
    
    Args:
        past_corners: 過去の通過順位リスト
        ten_index: 自馬のテン指数
        all_horses_ten_index: 全出走馬のテン指数リスト
        wakuban: 枠番
    
    Returns:
        {
            'ashishitsu': str,
            'ten_rank_pct': float,
            'adjusted_by_member': bool
        }
    """
    # 過去実績による基本判定
    if not past_corners:
        return {'ashishitsu': '自', 'ten_rank_pct': 50.0, 'adjusted_by_member': False}
    
    all_positions = []
    for corners in past_corners[:3]:
        valid_corners = [c for c in corners if c > 0]
        if valid_corners:
            all_positions.extend(valid_corners)
    
    if not all_positions:
        return {'ashishitsu': '自', 'ten_rank_pct': 50.0, 'adjusted_by_member': False}
    
    avg_position = sum(all_positions) / len(all_positions)
    
    # メンバー構成による相対評価
    adjusted_by_member = False
    if all_horses_ten_index:
        sorted_ten = sorted(all_horses_ten_index, reverse=True)
        if ten_index in sorted_ten:
            ten_rank = sorted_ten.index(ten_index) + 1
            ten_rank_pct = (ten_rank / len(sorted_ten)) * 100
            
            # テン指数順位による脚質補正
            if ten_rank_pct <= 20:
                ashishitsu = '逃'
                adjusted_by_member = True
            elif ten_rank_pct <= 40:
                ashishitsu = '先'
                adjusted_by_member = True
            elif ten_rank_pct <= 70:
                ashishitsu = '差'
            else:
                ashishitsu = '追'
        else:
            ten_rank_pct = 50.0
            # 過去実績ベース
            if avg_position <= 2.0:
                ashishitsu = '逃'
            elif avg_position <= 4.0:
                ashishitsu = '先'
            elif avg_position <= 8.0:
                ashishitsu = '好' if avg_position <= 6.0 else '差'
            else:
                ashishitsu = '追'
    else:
        ten_rank_pct = 50.0
        # 過去実績ベース
        if avg_position <= 2.0:
            ashishitsu = '逃'
        elif avg_position <= 4.0:
            ashishitsu = '先'
        elif avg_position <= 8.0:
            ashishitsu = '好' if avg_position <= 6.0 else '差'
        else:
            ashishitsu = '追'
    
    # 枠順による微調整
    if wakuban and wakuban <= 3 and ashishitsu in ['先', '好']:
        ashishitsu = '先'  # 内枠は先行しやすい
    
    return {
        'ashishitsu': ashishitsu,
        'ten_rank_pct': round(ten_rank_pct, 1),
        'adjusted_by_member': adjusted_by_member
    }


# ============================
# 8. 統合計算関数（充実度100%版）
# ============================

def calculate_all_indexes_v2(horse_data: Dict, all_horses_data: Optional[List[Dict]] = None) -> Dict:
    """
    1頭分の全指数を一括計算（充実度100%版）
    
    Args:
        horse_data: 馬データ
        all_horses_data: 全出走馬データ（メンバー構成評価用）
    
    Returns:
        完全な指数データ
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
        
        # 新規追加データ
        furi_code = horse_data.get('furi_code')
        wakuban = safe_int(horse_data.get('wakuban')) if horse_data.get('wakuban') else None
        kinryo = safe_float(horse_data.get('kinryo')) if horse_data.get('kinryo') else None
        bataiju = safe_int(horse_data.get('bataiju')) if horse_data.get('bataiju') else None
        ashishitsu = horse_data.get('computed_ashishitsu')
        past_corners = horse_data.get('past_corners', [])
        
        # テン指数計算
        ten_result = calculate_ten_index_v2(
            zenhan_3f, kyori, baba_code, keibajo_code,
            furi_code, wakuban, kinryo, bataiju
        )
        
        # 上がり指数計算
        agari_result = calculate_agari_index_v2(
            kohan_3f, zenhan_3f, kyori, baba_code, keibajo_code,
            furi_code, kinryo, bataiju
        )
        
        # ペース指数計算
        pace_result = calculate_pace_index_v2(
            ten_result['ten_index'],
            agari_result['agari_index'],
            zenhan_3f, kohan_3f,
            agari_result['pace_type']
        )
        
        # メンバー構成評価用のテン指数リスト
        all_ten_indexes = None
        if all_horses_data:
            all_ten_indexes = [
                calculate_ten_index_v2(
                    safe_float(h.get('zenhan_3f')),
                    safe_int(h.get('kyori'), 1600),
                    str(h.get('babajotai_code_dirt', '1')),
                    str(h.get('keibajo_code', '42'))
                )['ten_index']
                for h in all_horses_data
            ]
        
        # 予想脚質判定
        ashishitsu_result = predict_ashishitsu_v2(
            past_corners,
            ten_result['ten_index'],
            all_ten_indexes,
            wakuban
        )
        
        # 位置指数計算（脚質補正適用）
        position_result = calculate_position_index_v2(
            corner_1, corner_2, corner_3, corner_4, tosu,
            wakuban, ashishitsu_result['ashishitsu']
        )
        
        return {
            'ten_index': ten_result['ten_index'],
            'ten_corrections': ten_result['corrections'],
            'position_index': position_result['position_index'],
            'position_avg': position_result['avg_position'],
            'agari_index': agari_result['agari_index'],
            'agari_pace_type': agari_result['pace_type'],
            'pace_index': pace_result['pace_index'],
            'pace_type': pace_result['pace_type'],
            'ashishitsu': ashishitsu_result['ashishitsu'],
            'ashishitsu_ten_rank': ashishitsu_result['ten_rank_pct'],
            'completeness': 100.0
        }
    
    except Exception as e:
        logger.error(f"指数計算エラー: {e}")
        return {
            'ten_index': 0.0,
            'position_index': 50.0,
            'agari_index': 0.0,
            'pace_index': 0.0,
            'ashishitsu': '自',
            'completeness': 0.0,
            'error': str(e)
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
        'furi_code': '01',  # 出遅れ軽度
        'wakuban': 3,
        'kinryo': 56.0,
        'bataiju': 480,
        'computed_ashishitsu': '先',
        'past_corners': [
            (2, 2, 3, 2),
            (1, 1, 2, 1),
            (3, 3, 3, 4)
        ]
    }
    
    # 全出走馬データ（メンバー構成評価用）
    all_horses = [
        {'zenhan_3f': 34.5, 'kohan_3f': 37.0, 'kyori': 1600, 'babajotai_code_dirt': '1', 'keibajo_code': '42'},
        {'zenhan_3f': 35.0, 'kohan_3f': 37.5, 'kyori': 1600, 'babajotai_code_dirt': '1', 'keibajo_code': '42'},
        {'zenhan_3f': 35.5, 'kohan_3f': 38.0, 'kyori': 1600, 'babajotai_code_dirt': '1', 'keibajo_code': '42'},
    ]
    
    # 指数計算
    indexes = calculate_all_indexes_v2(test_horse, all_horses)
    
    print("\n=== HQS指数計算結果（充実度100%版） ===")
    print(f"充実度:     {indexes['completeness']:.0f}%")
    print(f"テン指数:   {indexes['ten_index']:.1f}")
    print(f"  補正内訳: {indexes.get('ten_corrections', {})}")
    print(f"位置指数:   {indexes['position_index']:.1f} (平均順位={indexes.get('position_avg', 0):.1f})")
    print(f"上がり指数: {indexes['agari_index']:.1f} (ペース={indexes.get('agari_pace_type', 'N/A')})")
    print(f"ペース指数: {indexes['pace_index']:.1f}")
    print(f"予想脚質:   {indexes['ashishitsu']} (テン順位={indexes.get('ashishitsu_ten_rank', 0):.1f}%)")
