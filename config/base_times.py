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
    '30': {  # 門別
        1000: {
            '上位クラス': {'zenhan_3f': 23.2, 'kohan_3f': 35.5},
            'E級': {'zenhan_3f': 23.7, 'kohan_3f': 36.5},
            '一般戦': {'zenhan_3f': 23.9, 'kohan_3f': 37.1},
        },
        1100: {
            'E級': {'zenhan_3f': 29.6, 'kohan_3f': 37.0},
            '一般戦': {'zenhan_3f': 29.7, 'kohan_3f': 37.7},
        },
        1200: {
            '上位クラス': {'zenhan_3f': 34.7, 'kohan_3f': 36.6},
            'E級': {'zenhan_3f': 35.4, 'kohan_3f': 37.2},
            '一般戦': {'zenhan_3f': 35.9, 'kohan_3f': 38.0},
        },
        1500: {
            'E級': {'zenhan_3f': 35.8, 'kohan_3f': 38.6},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 39.7},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.4, 'kohan_3f': 39.1},
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 39.3},
            '一般戦': {'zenhan_3f': 36.3, 'kohan_3f': 39.7},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.5, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 38.8},
            '一般戦': {'zenhan_3f': 36.5, 'kohan_3f': 39.3},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.8, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 36.8, 'kohan_3f': 38.7},
            '一般戦': {'zenhan_3f': 36.8, 'kohan_3f': 39.2},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 37.3, 'kohan_3f': 38.4},
        },
        2600: {
            '上位クラス': {'zenhan_3f': 38.2, 'kohan_3f': 38.9},
            'E級': {'zenhan_3f': 38.0, 'kohan_3f': 38.6},
        },
    },
    '35': {  # 盛岡
        1000: {
            '上位クラス': {'zenhan_3f': 23.1, 'kohan_3f': 34.8},
            'E級': {'zenhan_3f': 23.3, 'kohan_3f': 34.9},
            '一般戦': {'zenhan_3f': 23.7, 'kohan_3f': 35.6},
        },
        1200: {
            '上位クラス': {'zenhan_3f': 34.3, 'kohan_3f': 34.7},
            'E級': {'zenhan_3f': 35.1, 'kohan_3f': 36.3},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 37.1},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 36.5, 'kohan_3f': 37.4},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 37.2},
            '一般戦': {'zenhan_3f': 36.5, 'kohan_3f': 37.6},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.9, 'kohan_3f': 36.1},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 36.8},
            '一般戦': {'zenhan_3f': 37.0, 'kohan_3f': 37.3},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.7, 'kohan_3f': 35.9},
            'E級': {'zenhan_3f': 36.7, 'kohan_3f': 35.9},
            '一般戦': {'zenhan_3f': 36.7, 'kohan_3f': 36.0},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 37.0, 'kohan_3f': 36.8},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 36.8},
            '一般戦': {'zenhan_3f': 37.0, 'kohan_3f': 37.6},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.5, 'kohan_3f': 36.5},
        },
        2400: {
            '上位クラス': {'zenhan_3f': 38.1, 'kohan_3f': 36.1},
        },
        2500: {
            '上位クラス': {'zenhan_3f': 38.2, 'kohan_3f': 38.5},
        },
        2600: {
            '上位クラス': {'zenhan_3f': 38.3, 'kohan_3f': 35.5},
        },
    },
    '36': {  # 水沢
        850: {
            '上位クラス': {'zenhan_3f': 14.5, 'kohan_3f': 35.0},
            'E級': {'zenhan_3f': 14.5, 'kohan_3f': 35.0},
            '一般戦': {'zenhan_3f': 14.9, 'kohan_3f': 35.8},
        },
        1300: {
            '上位クラス': {'zenhan_3f': 35.3, 'kohan_3f': 38.2},
            'E級': {'zenhan_3f': 35.3, 'kohan_3f': 37.4},
            '一般戦': {'zenhan_3f': 35.3, 'kohan_3f': 38.8},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.8, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 35.8, 'kohan_3f': 38.1},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 38.9},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.3, 'kohan_3f': 37.9},
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 38.0},
            '一般戦': {'zenhan_3f': 36.3, 'kohan_3f': 38.5},
        },
        1800: {
            'E級': {'zenhan_3f': 36.8, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 36.8, 'kohan_3f': 38.4},
        },
        1900: {
            '上位クラス': {'zenhan_3f': 37.0, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 38.0, 'kohan_3f': 38.6},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 37.3, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 37.3, 'kohan_3f': 40.2},
        },
        2500: {
            '上位クラス': {'zenhan_3f': 38.2, 'kohan_3f': 38.8},
        },
    },
    '42': {  # 浦和
        800: {
            'E級': {'zenhan_3f': 11.8, 'kohan_3f': 34.6},
            '一般戦': {'zenhan_3f': 11.9, 'kohan_3f': 35.4},
        },
        1300: {
            'E級': {'zenhan_3f': 35.3, 'kohan_3f': 39.1},
            '一般戦': {'zenhan_3f': 35.3, 'kohan_3f': 38.6},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.5, 'kohan_3f': 36.9},
            'E級': {'zenhan_3f': 35.5, 'kohan_3f': 37.9},
            '一般戦': {'zenhan_3f': 35.5, 'kohan_3f': 38.7},
        },
        1500: {
            '上位クラス': {'zenhan_3f': 35.7, 'kohan_3f': 37.8},
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 38.0},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 38.8},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.1, 'kohan_3f': 37.8},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.2},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.8},
        },
        1900: {
            '上位クラス': {'zenhan_3f': 36.8, 'kohan_3f': 37.1},
            'E級': {'zenhan_3f': 36.9, 'kohan_3f': 38.4},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.1, 'kohan_3f': 37.0},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 38.6},
        },
    },
    '43': {  # 船橋
        1000: {
            '上位クラス': {'zenhan_3f': 22.5, 'kohan_3f': 35.8},
            'E級': {'zenhan_3f': 23.1, 'kohan_3f': 36.6},
            '一般戦': {'zenhan_3f': 23.5, 'kohan_3f': 37.4},
        },
        1200: {
            '上位クラス': {'zenhan_3f': 34.9, 'kohan_3f': 37.0},
            'E級': {'zenhan_3f': 35.5, 'kohan_3f': 37.4},
            '一般戦': {'zenhan_3f': 36.2, 'kohan_3f': 38.3},
        },
        1500: {
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 38.4},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 39.0},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.6},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.6},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.0},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.3, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 38.6},
            '一般戦': {'zenhan_3f': 36.5, 'kohan_3f': 39.5},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.5, 'kohan_3f': 37.5},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 38.6},
            '一般戦': {'zenhan_3f': 36.6, 'kohan_3f': 39.3},
        },
        2200: {
            '上位クラス': {'zenhan_3f': 37.5, 'kohan_3f': 38.4},
            'E級': {'zenhan_3f': 37.5, 'kohan_3f': 39.2},
            '一般戦': {'zenhan_3f': 37.6, 'kohan_3f': 40.3},
        },
        2400: {
            '上位クラス': {'zenhan_3f': 37.8, 'kohan_3f': 38.2},
        },
    },
    '44': {  # 大井
        1000: {
            'E級': {'zenhan_3f': 23.4, 'kohan_3f': 36.2},
            '一般戦': {'zenhan_3f': 23.5, 'kohan_3f': 36.6},
        },
        1200: {
            '上位クラス': {'zenhan_3f': 34.3, 'kohan_3f': 36.4},
            'E級': {'zenhan_3f': 35.1, 'kohan_3f': 36.9},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 37.6},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.8, 'kohan_3f': 36.7},
            'E級': {'zenhan_3f': 35.8, 'kohan_3f': 37.3},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 38.0},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.1, 'kohan_3f': 38.5},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.4},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.2},
        },
        1650: {
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 39.3},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.3, 'kohan_3f': 37.3},
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 37.8},
            '一般戦': {'zenhan_3f': 36.3, 'kohan_3f': 38.8},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.5, 'kohan_3f': 37.1},
            'E級': {'zenhan_3f': 36.6, 'kohan_3f': 37.9},
            '一般戦': {'zenhan_3f': 36.5, 'kohan_3f': 38.1},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.0, 'kohan_3f': 37.1},
            'E級': {'zenhan_3f': 37.1, 'kohan_3f': 38.2},
            '一般戦': {'zenhan_3f': 37.0, 'kohan_3f': 39.3},
        },
        2400: {
            '上位クラス': {'zenhan_3f': 37.5, 'kohan_3f': 37.6},
            'E級': {'zenhan_3f': 37.5, 'kohan_3f': 37.8},
        },
        2600: {
            '上位クラス': {'zenhan_3f': 37.8, 'kohan_3f': 38.1},
            'E級': {'zenhan_3f': 37.8, 'kohan_3f': 38.1},
        },
    },
    '45': {  # 川崎
        900: {
            '上位クラス': {'zenhan_3f': 16.7, 'kohan_3f': 36.1},
            'E級': {'zenhan_3f': 17.0, 'kohan_3f': 36.5},
            '一般戦': {'zenhan_3f': 17.2, 'kohan_3f': 37.0},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.5, 'kohan_3f': 38.9},
            'E級': {'zenhan_3f': 35.5, 'kohan_3f': 39.4},
            '一般戦': {'zenhan_3f': 35.5, 'kohan_3f': 39.6},
        },
        1500: {
            '上位クラス': {'zenhan_3f': 35.7, 'kohan_3f': 39.0},
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 39.3},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 39.7},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.6},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 39.1},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.3},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.0, 'kohan_3f': 39.1},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 39.2},
            '一般戦': {'zenhan_3f': 37.0, 'kohan_3f': 39.8},
        },
        2100: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 38.3},
            'E級': {'zenhan_3f': 37.4, 'kohan_3f': 38.4},
        },
    },
    '46': {  # 金沢
        900: {
            '上位クラス': {'zenhan_3f': 18.8, 'kohan_3f': 34.8},
            'E級': {'zenhan_3f': 19.1, 'kohan_3f': 36.0},
            '一般戦': {'zenhan_3f': 19.5, 'kohan_3f': 36.1},
        },
        1300: {
            '上位クラス': {'zenhan_3f': 35.3, 'kohan_3f': 37.6},
            'E級': {'zenhan_3f': 35.3, 'kohan_3f': 38.5},
            '一般戦': {'zenhan_3f': 35.3, 'kohan_3f': 38.9},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.7, 'kohan_3f': 37.3},
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 37.9},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 38.4},
        },
        1500: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.6},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.1},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.6},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.5, 'kohan_3f': 37.8},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 37.9},
            '一般戦': {'zenhan_3f': 36.5, 'kohan_3f': 38.8},
        },
        1900: {
            '上位クラス': {'zenhan_3f': 37.1, 'kohan_3f': 38.5},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 38.0},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 37.8},
        },
        2100: {
            '上位クラス': {'zenhan_3f': 37.5, 'kohan_3f': 37.0},
        },
        2600: {
            '上位クラス': {'zenhan_3f': 38.2, 'kohan_3f': 37.9},
        },
    },
    '47': {  # 笠松
        800: {
            'E級': {'zenhan_3f': 13.0, 'kohan_3f': 36.4},
            '一般戦': {'zenhan_3f': 13.0, 'kohan_3f': 36.1},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.7, 'kohan_3f': 37.2},
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 37.7},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 38.2},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.3, 'kohan_3f': 37.1},
            'E級': {'zenhan_3f': 36.3, 'kohan_3f': 37.8},
            '一般戦': {'zenhan_3f': 36.3, 'kohan_3f': 38.3},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.8, 'kohan_3f': 37.0},
            'E級': {'zenhan_3f': 36.8, 'kohan_3f': 37.7},
        },
        1900: {
            '上位クラス': {'zenhan_3f': 37.1, 'kohan_3f': 37.4},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 38.3},
        },
        2500: {
            '上位クラス': {'zenhan_3f': 38.1, 'kohan_3f': 37.2},
        },
    },
    '48': {  # 名古屋
        900: {
            'E級': {'zenhan_3f': 18.4, 'kohan_3f': 37.0},
            '一般戦': {'zenhan_3f': 18.6, 'kohan_3f': 36.5},
        },
        920: {
            '上位クラス': {'zenhan_3f': 19.0, 'kohan_3f': 35.6},
            'E級': {'zenhan_3f': 19.1, 'kohan_3f': 35.7},
            '一般戦': {'zenhan_3f': 19.7, 'kohan_3f': 36.5},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 36.2, 'kohan_3f': 37.7},
            'E級': {'zenhan_3f': 35.7, 'kohan_3f': 37.7},
            '一般戦': {'zenhan_3f': 35.7, 'kohan_3f': 38.5},
        },
        1500: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.7},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.2},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.8},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.6, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 38.4},
            '一般戦': {'zenhan_3f': 36.6, 'kohan_3f': 38.8},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 37.7},
            'E級': {'zenhan_3f': 37.4, 'kohan_3f': 38.4},
            '一般戦': {'zenhan_3f': 37.3, 'kohan_3f': 40.2},
        },
        2100: {
            '上位クラス': {'zenhan_3f': 37.6, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 37.6, 'kohan_3f': 38.2},
        },
    },
    '50': {  # 園田
        820: {
            '上位クラス': {'zenhan_3f': 13.6, 'kohan_3f': 34.8},
            'E級': {'zenhan_3f': 13.9, 'kohan_3f': 36.1},
            '一般戦': {'zenhan_3f': 14.1, 'kohan_3f': 36.6},
        },
        1230: {
            '上位クラス': {'zenhan_3f': 35.3, 'kohan_3f': 37.0},
            'E級': {'zenhan_3f': 35.3, 'kohan_3f': 38.0},
            '一般戦': {'zenhan_3f': 35.3, 'kohan_3f': 38.9},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.8, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 35.8, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 39.1},
        },
        1700: {
            '上位クラス': {'zenhan_3f': 36.7, 'kohan_3f': 38.1},
            'E級': {'zenhan_3f': 36.7, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 36.7, 'kohan_3f': 38.9},
        },
        1870: {
            '上位クラス': {'zenhan_3f': 37.2, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 37.2, 'kohan_3f': 38.5},
            '一般戦': {'zenhan_3f': 37.2, 'kohan_3f': 39.1},
        },
        2400: {
            '上位クラス': {'zenhan_3f': 38.0, 'kohan_3f': 38.1},
            'E級': {'zenhan_3f': 38.0, 'kohan_3f': 37.8},
        },
    },
    '51': {  # 姫路
        800: {
            'E級': {'zenhan_3f': 13.3, 'kohan_3f': 35.9},
            '一般戦': {'zenhan_3f': 13.5, 'kohan_3f': 36.5},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 35.6, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 35.5, 'kohan_3f': 38.0},
            '一般戦': {'zenhan_3f': 35.5, 'kohan_3f': 38.8},
        },
        1500: {
            'E級': {'zenhan_3f': 35.8, 'kohan_3f': 38.1},
            '一般戦': {'zenhan_3f': 35.8, 'kohan_3f': 38.7},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 37.0, 'kohan_3f': 40.1},
            'E級': {'zenhan_3f': 37.0, 'kohan_3f': 38.2},
            '一般戦': {'zenhan_3f': 37.0, 'kohan_3f': 39.1},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 37.3, 'kohan_3f': 37.9},
            'E級': {'zenhan_3f': 37.3, 'kohan_3f': 38.3},
        },
    },
    '54': {  # 高知
        800: {
            'E級': {'zenhan_3f': 12.9, 'kohan_3f': 36.8},
            '一般戦': {'zenhan_3f': 12.7, 'kohan_3f': 36.0},
        },
        1300: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.2},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.7},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.2},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.6},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.8},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.2},
        },
        1600: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.8},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 39.1},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 39.3},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.1, 'kohan_3f': 39.1},
            'E級': {'zenhan_3f': 36.5, 'kohan_3f': 39.8},
        },
        1900: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 39.1},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 41.2},
        },
        2400: {
            '上位クラス': {'zenhan_3f': 36.1, 'kohan_3f': 40.0},
        },
    },
    '55': {  # 佐賀
        900: {
            '上位クラス': {'zenhan_3f': 17.4, 'kohan_3f': 35.1},
            'E級': {'zenhan_3f': 17.6, 'kohan_3f': 35.1},
            '一般戦': {'zenhan_3f': 18.2, 'kohan_3f': 36.3},
        },
        1300: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.2},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 37.8},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.2},
        },
        1400: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.3},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 37.5},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.3},
        },
        1750: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.0},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.0},
            '一般戦': {'zenhan_3f': 36.0, 'kohan_3f': 38.3},
        },
        1800: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.8},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 37.8},
            '一般戦': {'zenhan_3f': 36.1, 'kohan_3f': 38.3},
        },
        1860: {
            '上位クラス': {'zenhan_3f': 36.1, 'kohan_3f': 37.4},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 38.3},
            '一般戦': {'zenhan_3f': 36.3, 'kohan_3f': 38.0},
        },
        2000: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 37.5},
            'E級': {'zenhan_3f': 36.0, 'kohan_3f': 37.9},
        },
        2500: {
            '上位クラス': {'zenhan_3f': 36.0, 'kohan_3f': 38.1},
        },
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

def get_base_time(keibajo_code: str, kyori: int, time_type: str, grade_code: str = None) -> float:
    """
    基準タイムを取得（クラス別対応）
    
    Args:
        keibajo_code: 競馬場コード（30-65）
        kyori: 距離（m）
        time_type: 'zenhan_3f' or 'kohan_3f'
        grade_code: グレードコード（オプション）クラス別基準タイムが利用可能な場合に使用
    
    Returns:
        基準タイム（秒）
    """
    if keibajo_code not in BASE_TIMES:
        logger.warning(f"未対応の競馬場コード: {keibajo_code}、デフォルト値を使用")
        return 36.5 if time_type == 'zenhan_3f' else 39.0
    
    venue_times = BASE_TIMES[keibajo_code]
    
    # 完全一致
    if kyori in venue_times:
        base_time_data = venue_times[kyori]
        
        # クラス別データがある場合
        if isinstance(base_time_data, dict) and any(k in base_time_data for k in ['上位クラス', 'E級', '一般戦']):
            # grade_code がある場合、クラス名に変換
            if grade_code:
                if grade_code == 'E':
                    class_name = 'E級'
                elif grade_code in ['A', 'B', 'C', 'D', 'P', 'Q', 'R', 'S', 'T']:
                    class_name = '上位クラス'
                else:
                    class_name = '一般戦'
                
                # クラス別データを返す
                if class_name in base_time_data and time_type in base_time_data[class_name]:
                    return base_time_data[class_name][time_type]
            
            # フォールバック: 一般戦を使用
            if '一般戦' in base_time_data and time_type in base_time_data['一般戦']:
                return base_time_data['一般戦'][time_type]
            
            # さらにフォールバック: E級を使用
            if 'E級' in base_time_data and time_type in base_time_data['E級']:
                return base_time_data['E級'][time_type]
        
        # 通常データ（クラス別でない）
        if time_type in base_time_data:
            return base_time_data[time_type]
    
    # 最も近い距離を検索
    closest_kyori = min(venue_times.keys(), key=lambda k: abs(k - kyori))
    logger.info(f"{ORGANIZERS.get(keibajo_code, {}).get('name', keibajo_code)}競馬場: 距離{kyori}mの基準タイムなし。{closest_kyori}mを使用")
    
    closest_data = venue_times[closest_kyori]
    
    # クラス別データの処理（最も近い距離）
    if isinstance(closest_data, dict) and any(k in closest_data for k in ['上位クラス', 'E級', '一般戦']):
        if grade_code:
            if grade_code == 'E':
                class_name = 'E級'
            elif grade_code in ['A', 'B', 'C', 'D', 'P', 'Q', 'R', 'S', 'T']:
                class_name = '上位クラス'
            else:
                class_name = '一般戦'
            
            if class_name in closest_data and time_type in closest_data[class_name]:
                return closest_data[class_name][time_type]
        
        # フォールバック
        if '一般戦' in closest_data and time_type in closest_data['一般戦']:
            return closest_data['一般戦'][time_type]
        if 'E級' in closest_data and time_type in closest_data['E級']:
            return closest_data['E級'][time_type]
    
    # 通常データ
    if time_type in closest_data:
        return closest_data[time_type]
    
    # 最終フォールバック
    return 36.5 if time_type == 'zenhan_3f' else 39.0


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
