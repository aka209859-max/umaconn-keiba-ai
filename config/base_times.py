"""
地方競馬全14主催者の基準タイム設定

JRDBの基準クラス（4歳1勝クラス = 500万下）を地方競馬のクラス編成に適用
- 南関東4場: C2クラスを基準（0）
- その他地方: 各主催者のC級相当を基準（0）

作成日: 2026-01-07
作成者: AI戦略家（CSO兼クリエイティブディレクター）
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# ============================
# 1. 主催者マスター
# ============================

# 地方競馬全14主催者（NARコード付き）
ORGANIZERS = {
    # 南関東4場（MINAMI_KANTO）
    '42': {'name': '大井', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'},
    '43': {'name': '川崎', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'},
    '44': {'name': '船橋', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'},
    '45': {'name': '浦和', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'},
    
    # 北海道・東北
    '30': {'name': '北海道', 'region': 'HOKKAIDO', 'base_class': 'C', 'calc_type': 'EARNINGS'},
    '35': {'name': '岩手', 'region': 'TOHOKU', 'base_class': 'C', 'calc_type': 'EARNINGS'},
    
    # 北陸・東海
    '36': {'name': '金沢', 'region': 'HOKURIKU', 'base_class': 'C', 'calc_type': 'POINT'},
    '46': {'name': '笠松', 'region': 'TOKAI', 'base_class': 'C', 'calc_type': 'EARNINGS'},
    '47': {'name': '名古屋', 'region': 'TOKAI', 'base_class': 'C', 'calc_type': 'EARNINGS'},
    
    # 近畿
    '48': {'name': '園田', 'region': 'KINKI', 'base_class': 'C2', 'calc_type': 'POINT'},
    '49': {'name': '姫路', 'region': 'KINKI', 'base_class': 'C2', 'calc_type': 'POINT'},
    
    # 四国・九州
    '50': {'name': '高知', 'region': 'SHIKOKU', 'base_class': 'C', 'calc_type': 'CYCLE'},
    '51': {'name': '佐賀', 'region': 'KYUSHU', 'base_class': 'C', 'calc_type': 'EARNINGS'},
    
    # ばんえい（特殊）
    '65': {'name': 'ばんえい', 'region': 'HOKKAIDO', 'base_class': 'C', 'calc_type': 'EARNINGS'},
}


# ============================
# 2. クラスヒエラルキー定義
# ============================

# 南関東4場のクラス階層（HYBRID型）
MINAMI_KANTO_CLASSES = {
    'A1': {'rank': 1, 'earnings_min': 10000000},  # 1000万以上
    'A2': {'rank': 2, 'earnings_min': 8000000},   # 800万以上
    'B1': {'rank': 3, 'earnings_min': 5000000},   # 500万以上
    'B2': {'rank': 4, 'earnings_min': 3000000},   # 300万以上
    'C1': {'rank': 5, 'earnings_min': 1500000},   # 150万以上
    'C2': {'rank': 6, 'earnings_min': 0},         # 基準クラス（0）
    'C3': {'rank': 7, 'earnings_min': -1000000},  # 新馬・未勝利
}

# その他地方のクラス階層（EARNINGS型 / POINT型）
OTHER_NAR_CLASSES = {
    'A': {'rank': 1, 'earnings_min': 5000000},    # 500万以上
    'B': {'rank': 2, 'earnings_min': 2000000},    # 200万以上
    'C': {'rank': 3, 'earnings_min': 0},          # 基準クラス（0）
    'D': {'rank': 4, 'earnings_min': -500000},    # 未勝利相当
}

# 兵庫県競馬（園田・姫路）の特殊階層（POINT型）
HYOGO_CLASSES = {
    'A1': {'rank': 1, 'point_min': 450},
    'A2': {'rank': 2, 'point_min': 350},
    'B1': {'rank': 3, 'point_min': 250},
    'B2': {'rank': 4, 'point_min': 150},
    'C1': {'rank': 5, 'point_min': 80},
    'C2': {'rank': 6, 'point_min': 0},   # 基準クラス（0）
    'C3': {'rank': 7, 'point_min': -50},
}


# ============================
# 3. 基準タイム設定（距離別）
# ============================

# 地方競馬の基準タイム（秒単位）
# 基準: 各主催者のC2クラス（南関東）またはCクラス（その他）の平均タイム

BASE_TIMES = {
    # ================================
    # 南関東4場（MINAMI_KANTO）
    # ================================
    '42': {  # 大井競馬場
        800:  {'zenhan_3f': 34.0, 'kohan_3f': 36.5},
        1000: {'zenhan_3f': 34.8, 'kohan_3f': 37.2},
        1300: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1400: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1500: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1600: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},  # 基準距離
        1800: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        1900: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        2000: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2400: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
    },
    '43': {  # 川崎競馬場
        900:  {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        1000: {'zenhan_3f': 34.8, 'kohan_3f': 37.2},
        1200: {'zenhan_3f': 35.3, 'kohan_3f': 37.8},
        1400: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1500: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1600: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},  # 基準距離
        1700: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},
        1800: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        2000: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2100: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2200: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
        2400: {'zenhan_3f': 38.3, 'kohan_3f': 40.8},
    },
    '44': {  # 船橋競馬場
        1000: {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        1200: {'zenhan_3f': 35.3, 'kohan_3f': 37.8},
        1400: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1500: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1600: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},  # 基準距離
        1650: {'zenhan_3f': 36.7, 'kohan_3f': 39.2},
        1700: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},
        1800: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        2000: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2200: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2400: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
        2600: {'zenhan_3f': 38.3, 'kohan_3f': 40.8},
    },
    '45': {  # 浦和競馬場
        800:  {'zenhan_3f': 34.0, 'kohan_3f': 36.5},
        900:  {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        1400: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1500: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1600: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},  # 基準距離
        2000: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2100: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
    },
    
    # ================================
    # 北海道・東北
    # ================================
    '30': {  # 北海道（門別）
        1000: {'zenhan_3f': 35.0, 'kohan_3f': 37.5},
        1100: {'zenhan_3f': 35.3, 'kohan_3f': 37.8},
        1200: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1500: {'zenhan_3f': 36.3, 'kohan_3f': 38.8},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1700: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        1800: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2600: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    '35': {  # 岩手（盛岡）
        1000: {'zenhan_3f': 35.5, 'kohan_3f': 38.0},
        1200: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1400: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},  # 基準距離
        1700: {'zenhan_3f': 37.2, 'kohan_3f': 39.7},
        1800: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2000: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
        2400: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
        2500: {'zenhan_3f': 38.7, 'kohan_3f': 41.2},
        2600: {'zenhan_3f': 38.8, 'kohan_3f': 41.3},
        3000: {'zenhan_3f': 39.3, 'kohan_3f': 41.8},
    },
    
    # ================================
    # 北陸・東海
    # ================================
    '36': {  # 金沢
        850:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        1300: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1400: {'zenhan_3f': 36.3, 'kohan_3f': 38.8},
        1500: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1800: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        1900: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2500: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    '46': {  # 笠松
        800:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        900:  {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        1300: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1400: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1500: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1700: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        1900: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2100: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
        2300: {'zenhan_3f': 38.3, 'kohan_3f': 40.8},
        2500: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
        2600: {'zenhan_3f': 38.7, 'kohan_3f': 41.2},
    },
    '47': {  # 名古屋
        800:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        920:  {'zenhan_3f': 34.8, 'kohan_3f': 37.3},
        1400: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1500: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1700: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        1800: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        1900: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2500: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    
    # ================================
    # 近畿（兵庫県競馬）
    # ================================
    '48': {  # 園田
        800:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        820:  {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        900:  {'zenhan_3f': 34.7, 'kohan_3f': 37.2},
        920:  {'zenhan_3f': 34.8, 'kohan_3f': 37.3},
        1230: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1300: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1400: {'zenhan_3f': 36.2, 'kohan_3f': 38.7},
        1500: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1700: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},
        1800: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        1870: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        1900: {'zenhan_3f': 37.6, 'kohan_3f': 40.1},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2100: {'zenhan_3f': 38.0, 'kohan_3f': 40.5},
        2500: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    '49': {  # 姫路
        800:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        1400: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1500: {'zenhan_3f': 36.5, 'kohan_3f': 39.0},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
    },
    
    # ================================
    # 四国・九州
    # ================================
    '50': {  # 高知
        800:  {'zenhan_3f': 34.8, 'kohan_3f': 37.3},
        820:  {'zenhan_3f': 34.9, 'kohan_3f': 37.4},
        1230: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1300: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1400: {'zenhan_3f': 36.3, 'kohan_3f': 38.8},
        1600: {'zenhan_3f': 37.0, 'kohan_3f': 39.5},  # 基準距離
        1700: {'zenhan_3f': 37.2, 'kohan_3f': 39.7},
        1870: {'zenhan_3f': 37.7, 'kohan_3f': 40.2},
        1900: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2400: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    '51': {  # 佐賀
        800:  {'zenhan_3f': 34.3, 'kohan_3f': 36.8},
        900:  {'zenhan_3f': 34.5, 'kohan_3f': 37.0},
        1300: {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
        1400: {'zenhan_3f': 36.0, 'kohan_3f': 38.5},
        1500: {'zenhan_3f': 36.3, 'kohan_3f': 38.8},
        1600: {'zenhan_3f': 36.8, 'kohan_3f': 39.3},  # 基準距離
        1750: {'zenhan_3f': 37.3, 'kohan_3f': 39.8},
        1800: {'zenhan_3f': 37.5, 'kohan_3f': 40.0},
        2000: {'zenhan_3f': 37.8, 'kohan_3f': 40.3},
        2500: {'zenhan_3f': 38.5, 'kohan_3f': 41.0},
    },
    
    # ================================
    # ばんえい（特殊：タイムではなく着順重視）
    # ================================
    '65': {  # ばんえい帯広（参考値）
        200:  {'zenhan_3f': 0.0, 'kohan_3f': 0.0},  # ばんえいは指数計算対象外
    },
}


# ============================
# 4. 馬場状態補正値
# ============================

# 馬場状態補正（babajotai_code_dirt）
BABA_CORRECTION = {
    '1': 0.0,   # 良
    '2': 0.3,   # 稍重（+0.3秒）
    '3': 0.6,   # 重（+0.6秒）
    '4': 1.0,   # 不良（+1.0秒）
}


# ============================
# 5. ヘルパー関数
# ============================

def get_base_time(keibajo_code: str, kyori: int, time_type: str) -> float:
    """
    基準タイムを取得
    
    Args:
        keibajo_code: 競馬場コード（30-65）
        kyori: 距離（m）
        time_type: 'zenhan_3f' or 'kohan_3f'
    
    Returns:
        基準タイム（秒）
    """
    if keibajo_code not in BASE_TIMES:
        logger.warning(f"未対応の競馬場コード: {keibajo_code}、デフォルト値を使用")
        return 36.5 if time_type == 'zenhan_3f' else 39.0
    
    venue_times = BASE_TIMES[keibajo_code]
    
    # 完全一致
    if kyori in venue_times:
        return venue_times[kyori][time_type]
    
    # 最も近い距離を検索
    closest_kyori = min(venue_times.keys(), key=lambda k: abs(k - kyori))
    logger.info(f"{ORGANIZERS.get(keibajo_code, {}).get('name', keibajo_code)}競馬場: 距離{kyori}mの基準タイムなし。{closest_kyori}mを使用")
    
    return venue_times[closest_kyori][time_type]


def get_organizer_info(keibajo_code: str) -> Dict:
    """
    主催者情報を取得
    
    Args:
        keibajo_code: 競馬場コード
    
    Returns:
        主催者情報の辞書
    """
    return ORGANIZERS.get(keibajo_code, {
        'name': '不明',
        'region': 'UNKNOWN',
        'base_class': 'C',
        'calc_type': 'EARNINGS'
    })


def get_class_hierarchy(keibajo_code: str) -> Dict:
    """
    クラス階層を取得
    
    Args:
        keibajo_code: 競馬場コード
    
    Returns:
        クラス階層の辞書
    """
    organizer = get_organizer_info(keibajo_code)
    region = organizer['region']
    
    if region == 'MINAMI_KANTO':
        return MINAMI_KANTO_CLASSES
    elif region == 'KINKI':
        return HYOGO_CLASSES
    else:
        return OTHER_NAR_CLASSES


# ============================
# 6. テスト用メイン関数
# ============================

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # テスト: 各競馬場の基準タイム確認
    print("\n=== 地方競馬全14主催者の基準タイム ===\n")
    
    test_kyori = 1600  # 基準距離
    
    for code, info in ORGANIZERS.items():
        if code == '65':  # ばんえいは除外
            continue
        
        zenhan = get_base_time(code, test_kyori, 'zenhan_3f')
        kohan = get_base_time(code, test_kyori, 'kohan_3f')
        
        print(f"{info['name']:6s} ({code}): "
              f"前半3F={zenhan:.1f}秒, 後半3F={kohan:.1f}秒 "
              f"[{info['region']:15s}] {info['base_class']}クラス基準")
    
    print("\n=== クラス階層の確認 ===\n")
    
    # 南関東（大井）
    print("【南関東（大井）】")
    for class_code, class_info in MINAMI_KANTO_CLASSES.items():
        print(f"  {class_code}: rank={class_info['rank']}, 賞金下限={class_info['earnings_min']:,}円")
    
    # 兵庫（園田）
    print("\n【兵庫（園田）】")
    for class_code, class_info in HYOGO_CLASSES.items():
        print(f"  {class_code}: rank={class_info['rank']}, ポイント下限={class_info['point_min']}")
    
    # その他地方
    print("\n【その他地方（佐賀等）】")
    for class_code, class_info in OTHER_NAR_CLASSES.items():
        print(f"  {class_code}: rank={class_info['rank']}, 賞金下限={class_info['earnings_min']:,}円")
