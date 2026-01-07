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
# 不利補正マッピング
# ============================

FURI_CORRECTION = {
    # 不利コード: (補正値_秒, 説明)
    '01': (0.5, '出遅れ'),
    '02': (0.8, '大きく出遅れ'),
    '03': (0.3, 'やや出遅れ'),
    '04': (1.0, '挟まれる'),
    '05': (0.8, '進路がなくなる'),
    '06': (0.6, 'ダッシュつかず'),
    '07': (1.2, '砂をかぶる'),
    '08': (0.7, '内をつかれて外に出される'),
    '09': (0.9, '押し出される'),
    '10': (1.5, '大外を回される'),
    '11': (1.0, '外を回される'),
    '12': (0.8, 'ゴチャつく'),
    '13': (1.8, '落馬'),
    '14': (2.0, '故障'),
    '15': (0.5, '躓く'),
    '16': (0.6, 'よれる'),
    '17': (0.4, '掛かる'),
    '18': (0.7, 'ささる'),
    '19': (1.0, '前が詰まる'),
    '20': (0.8, '接触'),
    '21': (0.5, 'バテる'),
    '22': (1.2, '不利大'),
    '23': (0.6, '不利'),
    '24': (0.3, 'やや不利'),
    '25': (0.9, '直線で不利'),
    '26': (1.1, '4角で不利'),
    '27': (0.8, '3角で不利'),
    '28': (0.7, '向正面で不利'),
    '29': (0.6, 'スタートで不利'),
    '30': (1.3, '追突'),
}


def get_furi_correction(furi_code: str) -> Tuple[float, str]:
    """
    不利補正値を取得
    
    Args:
        furi_code: 不利コード（2桁数字の文字列）
    
    Returns:
        (補正値_秒, 説明)
    """
    if not furi_code or furi_code == '00' or furi_code == '':
        return (0.0, 'なし')
    
    return FURI_CORRECTION.get(furi_code, (0.0, '不明'))


# ============================
# 枠順補正マッピング
# ============================

def get_wakuban_correction(wakuban: int, tosu: int, kyori: int) -> Tuple[float, str]:
    """
    枠順補正値を計算
    
    Args:
        wakuban: 枠番（1-8）
        tosu: 出走頭数
        kyori: 距離（m）
    
    Returns:
        (補正値_秒, 説明)
    """
    if wakuban <= 0 or tosu <= 0:
        return (0.0, 'データなし')
    
    # 枠番を相対位置に変換（0.0=最内 〜 1.0=最外）
    relative_position = (wakuban - 1) / max(tosu - 1, 1)
    
    # 距離別の枠順影響度
    if kyori < 1400:
        # 短距離: 内枠有利、外枠不利
        base_correction = (0.5 - relative_position) * 0.6
        desc = '短距離・内枠有利'
    elif kyori < 1800:
        # マイル: 中枠やや有利
        if 0.3 <= relative_position <= 0.7:
            base_correction = 0.2
            desc = 'マイル・中枠有利'
        else:
            base_correction = (0.5 - abs(relative_position - 0.5)) * 0.3
            desc = 'マイル・端枠やや不利'
    else:
        # 中長距離: 外枠やや有利（展開待ち）
        base_correction = (relative_position - 0.5) * 0.2
        desc = '中長距離・外枠やや有利'
    
    return (round(base_correction, 2), desc)


# ============================
# 斤量補正マッピング
# ============================

def get_kinryo_correction(kinryo: float, bataiju: float) -> Tuple[float, str]:
    """
    斤量補正値を計算
    
    JRAの統計では、1kgあたり約0.2秒（200m）の差
    地方競馬も同様と仮定し、1kgあたり0.1秒の補正
    
    Args:
        kinryo: 負担重量（kg）
        bataiju: 馬体重（kg）
    
    Returns:
        (補正値_秒, 説明)
    """
    if kinryo <= 0:
        return (0.0, 'データなし')
    
    # 基準斤量: 地方競馬C2クラスの標準斤量 54kg
    base_kinryo = 54.0
    
    # 斤量差（kg）
    kinryo_diff = kinryo - base_kinryo
    
    # 斤量補正: 1kgあたり0.1秒
    # 重い場合は負の補正（タイム差が開く）、軽い場合は正の補正（タイムが速くなる）
    kinryo_correction = -kinryo_diff * 0.1
    
    # 馬体重による補正（オプション: 馬体重が大きいほど斤量の影響が小さい）
    if bataiju > 0:
        # 標準馬体重: 460kg
        weight_ratio = bataiju / 460.0
        # 馬体重が大きいほど斤量の影響が小さい（0.9〜1.1の範囲で調整）
        weight_factor = 0.9 + (1.0 - weight_ratio) * 0.2
        weight_factor = max(0.8, min(1.2, weight_factor))
        kinryo_correction = kinryo_correction * weight_factor
        desc = f'斤量{kinryo:.1f}kg（基準{base_kinryo}kg）, 馬体重{bataiju}kg'
    else:
        desc = f'斤量{kinryo:.1f}kg（基準{base_kinryo}kg）'
    
    return (round(kinryo_correction, 2), desc)


# ============================
# 3. テン指数計算
# ============================

def calculate_ten_index(
    zenhan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str,
    furi_code: str = '00',
    wakuban: int = 0,
    tosu: int = 12,
    kinryo: float = 54.0,
    bataiju: float = 460.0
) -> float:
    """
    テン指数を計算
    
    テン指数 = ((基準3Fタイム - 実走3Fタイム) + 馬場差補正 + 不利補正 + 枠順補正 + 斤量補正) × 10
    
    Args:
        zenhan_3f: 前半3Fタイム（秒）
        kyori: 距離（m）
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
        furi_code: 不利コード（デフォルト: '00'=なし）
        wakuban: 枠番（デフォルト: 0=補正なし）
        tosu: 出走頭数（デフォルト: 12）
        kinryo: 負担重量（kg, デフォルト: 54.0）
        bataiju: 馬体重（kg, デフォルト: 460.0）
    
    Returns:
        テン指数（-100 〜 +100）
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'zenhan_3f')
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # 不利補正（スタート不利・前半不利のみ適用）
    furi_correction, furi_desc = get_furi_correction(furi_code)
    # スタート不利（01-03, 06, 29）と向正面不利（28）のみテン指数に適用
    ten_furi_codes = ['01', '02', '03', '06', '28', '29']
    if furi_code not in ten_furi_codes:
        furi_correction = 0.0
    
    # 枠順補正（短距離のテン指数に影響）
    waku_correction, waku_desc = get_wakuban_correction(wakuban, tosu, kyori)
    if kyori >= 1800:  # 中長距離ではテン指数への枠順影響は小さい
        waku_correction = waku_correction * 0.3
    
    # 斤量補正
    kinryo_correction, kinryo_desc = get_kinryo_correction(kinryo, bataiju)
    
    # テン指数計算
    ten_index = ((base_time - zenhan_3f) + baba_correction + furi_correction + waku_correction + kinryo_correction) * 10
    
    # 範囲制限
    ten_index = max(-100, min(100, ten_index))
    
    logger.debug(f"テン指数: {ten_index:.1f} (3F={zenhan_3f}s, 基準={base_time}s, 馬場補正={baba_correction}s, 不利補正={furi_correction}s [{furi_desc}], 枠順補正={waku_correction}s [{waku_desc}], 斤量補正={kinryo_correction}s [{kinryo_desc}])")
    
    return round(ten_index, 1)


# ============================
# 4. 位置指数計算
# ============================

def calculate_position_index(
    corner_1: int,
    corner_2: int,
    corner_3: int,
    corner_4: int,
    tosu: int,
    wakuban: int = 0,
    kyori: int = 1600
) -> float:
    """
    位置指数を計算
    
    位置指数 = (平均通過順位 / 出走頭数) × 100 + 枠順補正
    
    Args:
        corner_1: 1コーナー通過順位
        corner_2: 2コーナー通過順位
        corner_3: 3コーナー通過順位
        corner_4: 4コーナー通過順位
        tosu: 出走頭数
        wakuban: 枠番（デフォルト: 0=補正なし）
        kyori: 距離（m）
    
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
    
    # 枠順補正（短距離で内枠有利、外枠不利）
    waku_correction, waku_desc = get_wakuban_correction(wakuban, tosu, kyori)
    # 位置指数への影響は逆符号（内枠ほど先頭に近い＝指数が小さくなる）
    position_waku_correction = -waku_correction * 15  # 位置指数への影響度調整
    
    position_index = position_index + position_waku_correction
    
    # 範囲制限
    position_index = max(0, min(100, position_index))
    
    logger.debug(f"位置指数: {position_index:.1f} (平均順位={avg_position:.1f}/{tosu}頭, 枠順補正={position_waku_correction:.1f} [{waku_desc}])")
    
    return round(position_index, 1)


# ============================
# 5. 上がり指数計算
# ============================

def calculate_agari_index(
    kohan_3f: float,
    kyori: int,
    baba_code: str,
    keibajo_code: str,
    furi_code: str = '00',
    kinryo: float = 54.0,
    bataiju: float = 460.0
) -> float:
    """
    上がり指数を計算
    
    上がり指数 = ((基準後半3Fタイム - 実走後半3Fタイム) + 馬場差補正 + 不利補正 + 斤量補正) × 10
    
    Args:
        kohan_3f: 後半3Fタイム（秒）
        kyori: 距離（m）
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
        furi_code: 不利コード（デフォルト: '00'=なし）
        kinryo: 負担重量（kg, デフォルト: 54.0）
        bataiju: 馬体重（kg, デフォルト: 460.0）
    
    Returns:
        上がり指数（-100 〜 +100）
    """
    # 基準タイムを取得
    base_time = get_base_time(keibajo_code, kyori, 'kohan_3f')
    
    # 馬場差補正
    baba_correction = get_baba_correction_value(baba_code)
    
    # 不利補正（直線・4角不利のみ適用）
    furi_correction, furi_desc = get_furi_correction(furi_code)
    # 直線不利（25）、4角不利（26）、3角不利（27）、その他ゴール前不利を適用
    agari_furi_codes = ['04', '05', '08', '09', '10', '11', '12', '19', '22', '23', '24', '25', '26', '27', '30']
    if furi_code not in agari_furi_codes:
        furi_correction = 0.0
    
    # 斤量補正（上がりタイムは斤量の影響が大きい）
    kinryo_correction, kinryo_desc = get_kinryo_correction(kinryo, bataiju)
    # 上がり3Fは斤量の影響が1.2倍（疲労による影響）
    kinryo_correction = kinryo_correction * 1.2
    
    # 上がり指数計算
    agari_index = ((base_time - kohan_3f) + baba_correction + furi_correction + kinryo_correction) * 10
    
    # 範囲制限
    agari_index = max(-100, min(100, agari_index))
    
    logger.debug(f"上がり指数: {agari_index:.1f} (3F={kohan_3f}s, 基準={base_time}s, 馬場補正={baba_correction}s, 不利補正={furi_correction}s [{furi_desc}], 斤量補正={kinryo_correction}s [{kinryo_desc}])")
    
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
    current_members: Optional[List[Dict]] = None,
    wakuban: int = 0,
    tosu: int = 12,
    kyori: int = 1600
) -> str:
    """
    予想脚質を判定
    
    過去3走の通過順位パターンから脚質を判定
    
    Args:
        past_corners: 過去の通過順位リスト [(c1, c2, c3, c4), ...]
        current_members: 今回のメンバー構成（相対評価用）
        wakuban: 枠番
        tosu: 出走頭数
        kyori: 距離
    
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
    
    # 枠順補正（短距離の内枠は前に行きやすい）
    waku_correction, waku_desc = get_wakuban_correction(wakuban, tosu, kyori)
    if kyori < 1400:
        # 短距離では枠順の影響大
        position_adjustment = -waku_correction * 2  # 内枠は順位が前になりやすい
    else:
        # 中長距離では枠順の影響小
        position_adjustment = -waku_correction * 0.5
    
    adjusted_position = avg_position + position_adjustment
    
    # 脚質判定
    if adjusted_position <= 2.0:
        ashishitsu = '逃'
    elif adjusted_position <= 4.0:
        ashishitsu = '先'
    elif adjusted_position <= 8.0:
        if adjusted_position <= 6.0:
            ashishitsu = '好'
        else:
            ashishitsu = '差'
    else:
        ashishitsu = '追'
    
    logger.debug(f"予想脚質: {ashishitsu} (平均順位={avg_position:.1f}, 枠順補正後={adjusted_position:.1f}, 枠={wakuban}番[{waku_desc}])")
    
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
        furi_code = str(horse_data.get('furi_code', '00'))
        wakuban = safe_int(horse_data.get('wakuban'), 0)
        kinryo = safe_float(horse_data.get('kinryo'), 54.0)
        bataiju = safe_float(horse_data.get('bataiju'), 460.0)
        
        # 各指数を計算
        ten_index = calculate_ten_index(zenhan_3f, kyori, baba_code, keibajo_code, furi_code, wakuban, tosu, kinryo, bataiju)
        position_index = calculate_position_index(corner_1, corner_2, corner_3, corner_4, tosu, wakuban, kyori)
        agari_index = calculate_agari_index(kohan_3f, kyori, baba_code, keibajo_code, furi_code, kinryo, bataiju)
        pace_index = calculate_pace_index(ten_index, agari_index, zenhan_3f, kohan_3f)
        
        # 予想脚質（過去データがある場合）
        past_corners = horse_data.get('past_corners', [])
        ashishitsu = predict_ashishitsu(past_corners, wakuban=wakuban, tosu=tosu, kyori=kyori)
        
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
        'furi_code': '00',  # 不利なし
        'wakuban': 3,  # 3枠（内枠寄り）
        'kinryo': 54.0,  # 標準斤量
        'bataiju': 460.0,  # 標準馬体重
        'past_corners': [
            (2, 2, 3, 2),
            (1, 1, 2, 1),
            (3, 3, 3, 4)
        ]
    }
    
    # 不利あり＋外枠＋重斤量のテストデータ
    test_horse_furi = {
        'zenhan_3f': 36.5,
        'kohan_3f': 39.5,
        'corner_1': 8,
        'corner_2': 7,
        'corner_3': 6,
        'corner_4': 5,
        'kyori': 1600,
        'babajotai_code_dirt': '2',
        'keibajo_code': '42',
        'tosu': 12,
        'furi_code': '10',  # 大外を回される
        'wakuban': 8,  # 8枠（最外）
        'kinryo': 57.0,  # 重斤量（+3kg）
        'bataiju': 440.0,  # 軽めの馬体重
        'past_corners': [
            (8, 7, 6, 5),
            (9, 8, 7, 6),
            (7, 6, 5, 4)
        ]
    }
    
    # 指数計算（不利なし）
    indexes = calculate_all_indexes(test_horse)
    
    print("\n=== HQS指数計算結果（不利なし）===")
    print(f"テン指数:   {indexes['ten_index']:.1f}")
    print(f"位置指数:   {indexes['position_index']:.1f}")
    print(f"上がり指数: {indexes['agari_index']:.1f}")
    print(f"ペース指数: {indexes['pace_index']:.1f}")
    print(f"予想脚質:   {indexes['ashishitsu']}")
    
    # 指数計算（不利あり＋外枠＋重斤量）
    indexes_furi = calculate_all_indexes(test_horse_furi)
    
    print("\n=== HQS指数計算結果（大外を回される＋重斤量）===")
    print(f"テン指数:   {indexes_furi['ten_index']:.1f}")
    print(f"位置指数:   {indexes_furi['position_index']:.1f}")
    print(f"上がり指数: {indexes_furi['agari_index']:.1f}")
    print(f"ペース指数: {indexes_furi['pace_index']:.1f}")
    print(f"予想脚質:   {indexes_furi['ashishitsu']}")
