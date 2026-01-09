#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
実データから計算した基準タイム設定

作成日: 2026-01-09
作成者: AI戦略家（CSO兼クリエイティブディレクター）
データソース: 実データの中央値（外れ値除外）

前半3Fの計算方法:
- 1200m以下: 走破タイム - 後半3F（確定値）
- 1201m以上: Ten3FEstimator を使用（推定値）
"""

BASE_TIMES = {
    '30': {  # 競馬場コード 30
        1000: {'zenhan_3f': 64.9, 'kohan_3f': 38.5},  # レース数: 44604
        1100: {'zenhan_3f': 70.8, 'kohan_3f': 39.4},  # レース数: 2932
        1200: {'zenhan_3f': 76.8, 'kohan_3f': 39.3},  # レース数: 66724
        1500: {'zenhan_3f': 33.8, 'kohan_3f': 41.5},  # レース数: 1838
        1600: {'zenhan_3f': 33.0, 'kohan_3f': 41.5},  # レース数: 4471
        1700: {'zenhan_3f': 33.0, 'kohan_3f': 40.2},  # レース数: 10000
        1800: {'zenhan_3f': 35.0, 'kohan_3f': 40.3},  # レース数: 10000
        2000: {'zenhan_3f': 36.0, 'kohan_3f': 40.2},  # レース数: 1746
        2600: {'zenhan_3f': 38.3, 'kohan_3f': 40.8},  # レース数: 162
    },
    '35': {  # 競馬場コード 35
        1000: {'zenhan_3f': 64.5, 'kohan_3f': 36.8},  # レース数: 8858
        1200: {'zenhan_3f': 77.5, 'kohan_3f': 38.7},  # レース数: 31614
        1400: {'zenhan_3f': 33.8, 'kohan_3f': 39.7},  # レース数: 10000
        1600: {'zenhan_3f': 33.0, 'kohan_3f': 39.4},  # レース数: 10000
        1700: {'zenhan_3f': 33.5, 'kohan_3f': 37.8},  # レース数: 2363
        1800: {'zenhan_3f': 34.7, 'kohan_3f': 39.5},  # レース数: 2898
        2000: {'zenhan_3f': 35.8, 'kohan_3f': 39.5},  # レース数: 827
        2400: {'zenhan_3f': 35.4, 'kohan_3f': 38.0},  # レース数: 433
        2500: {'zenhan_3f': 37.6, 'kohan_3f': 40.1},  # レース数: 17
        2600: {'zenhan_3f': 38.1, 'kohan_3f': 38.5},  # レース数: 18
    },
    '36': {  # 競馬場コード 36
        850: {'zenhan_3f': 15.6, 'kohan_3f': 36.9},  # レース数: 7932
        1300: {'zenhan_3f': 45.0, 'kohan_3f': 40.4},  # レース数: 10000
        1400: {'zenhan_3f': 34.5, 'kohan_3f': 40.5},  # レース数: 10000
        1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.2},  # レース数: 10000
        1800: {'zenhan_3f': 35.3, 'kohan_3f': 40.0},  # レース数: 2129
        1900: {'zenhan_3f': 40.3, 'kohan_3f': 40.0},  # レース数: 601
        2000: {'zenhan_3f': 36.2, 'kohan_3f': 40.4},  # レース数: 612
        2500: {'zenhan_3f': 37.4, 'kohan_3f': 40.3},  # レース数: 107
    },
    '42': {  # 競馬場コード 42
        800: {'zenhan_3f': 12.7, 'kohan_3f': 36.6},  # レース数: 8932
        1300: {'zenhan_3f': 45.0, 'kohan_3f': 40.7},  # レース数: 6249
        1400: {'zenhan_3f': 34.4, 'kohan_3f': 40.1},  # レース数: 10000
        1500: {'zenhan_3f': 33.7, 'kohan_3f': 40.5},  # レース数: 10000
        1600: {'zenhan_3f': 33.5, 'kohan_3f': 40.1},  # レース数: 10000
        1900: {'zenhan_3f': 40.2, 'kohan_3f': 40.0},  # レース数: 961
        2000: {'zenhan_3f': 36.7, 'kohan_3f': 40.8},  # レース数: 3442
    },
    '43': {  # 競馬場コード 43
        1000: {'zenhan_3f': 64.1, 'kohan_3f': 38.3},  # レース数: 13088
        1200: {'zenhan_3f': 77.1, 'kohan_3f': 39.7},  # レース数: 50607
        1400: {'zenhan_3f': 34.8, 'kohan_3f': 41.3},  # レース数: 1237
        1500: {'zenhan_3f': 33.5, 'kohan_3f': 40.5},  # レース数: 10000
        1600: {'zenhan_3f': 33.5, 'kohan_3f': 40.3},  # レース数: 10000
        1700: {'zenhan_3f': 33.5, 'kohan_3f': 40.3},  # レース数: 4193
        1800: {'zenhan_3f': 34.9, 'kohan_3f': 40.5},  # レース数: 4624
        2200: {'zenhan_3f': 34.7, 'kohan_3f': 41.7},  # レース数: 1557
        2400: {'zenhan_3f': 36.1, 'kohan_3f': 41.1},  # レース数: 266
    },
    '44': {  # 競馬場コード 44
        1000: {'zenhan_3f': 64.5, 'kohan_3f': 38.5},  # レース数: 4148
        1200: {'zenhan_3f': 76.6, 'kohan_3f': 39.0},  # レース数: 115263
        1400: {'zenhan_3f': 33.8, 'kohan_3f': 39.9},  # レース数: 10000
        1500: {'zenhan_3f': 33.5, 'kohan_3f': 40.6},  # レース数: 10000
        1600: {'zenhan_3f': 33.5, 'kohan_3f': 40.4},  # レース数: 10000
        1650: {'zenhan_3f': 33.5, 'kohan_3f': 40.7},  # レース数: 803
        1700: {'zenhan_3f': 33.5, 'kohan_3f': 39.7},  # レース数: 2473
        1800: {'zenhan_3f': 34.8, 'kohan_3f': 39.8},  # レース数: 10000
        2000: {'zenhan_3f': 35.8, 'kohan_3f': 39.8},  # レース数: 3503
        2400: {'zenhan_3f': 36.0, 'kohan_3f': 40.2},  # レース数: 373
        2600: {'zenhan_3f': 38.0, 'kohan_3f': 40.4},  # レース数: 393
    },
    '45': {  # 競馬場コード 45
        900: {'zenhan_3f': 18.0, 'kohan_3f': 38.2},  # レース数: 14931
        1400: {'zenhan_3f': 34.8, 'kohan_3f': 41.0},  # レース数: 10000
        1500: {'zenhan_3f': 33.5, 'kohan_3f': 41.0},  # レース数: 10000
        1600: {'zenhan_3f': 33.5, 'kohan_3f': 40.7},  # レース数: 10000
        2000: {'zenhan_3f': 37.0, 'kohan_3f': 41.7},  # レース数: 4451
        2100: {'zenhan_3f': 35.4, 'kohan_3f': 40.9},  # レース数: 2208
    },
    '46': {  # 競馬場コード 46
        900: {'zenhan_3f': 20.3, 'kohan_3f': 37.7},  # レース数: 1435
        1300: {'zenhan_3f': 45.0, 'kohan_3f': 39.9},  # レース数: 4388
        1400: {'zenhan_3f': 34.8, 'kohan_3f': 40.3},  # レース数: 10000
        1500: {'zenhan_3f': 33.7, 'kohan_3f': 40.6},  # レース数: 10000
        1700: {'zenhan_3f': 33.0, 'kohan_3f': 40.0},  # レース数: 6237
        1900: {'zenhan_3f': 40.5, 'kohan_3f': 40.2},  # レース数: 1270
        2000: {'zenhan_3f': 36.4, 'kohan_3f': 40.5},  # レース数: 696
        2100: {'zenhan_3f': 35.0, 'kohan_3f': 39.8},  # レース数: 325
        2300: {'zenhan_3f': 35.5, 'kohan_3f': 41.1},  # レース数: 140
        2600: {'zenhan_3f': 38.7, 'kohan_3f': 41.3},  # レース数: 147
    },
    '47': {  # 競馬場コード 47
        800: {'zenhan_3f': 13.9, 'kohan_3f': 37.4},  # レース数: 5347
        1400: {'zenhan_3f': 34.4, 'kohan_3f': 39.7},  # レース数: 10000
        1600: {'zenhan_3f': 33.0, 'kohan_3f': 39.3},  # レース数: 10000
        1800: {'zenhan_3f': 35.1, 'kohan_3f': 39.1},  # レース数: 1947
        1900: {'zenhan_3f': 40.4, 'kohan_3f': 39.5},  # レース数: 926
        2500: {'zenhan_3f': 37.5, 'kohan_3f': 39.3},  # レース数: 154
    },
    '48': {  # 競馬場コード 48
        800: {'zenhan_3f': 14.3, 'kohan_3f': 37.4},  # レース数: 9356
        900: {'zenhan_3f': 19.3, 'kohan_3f': 37.9},  # レース数: 215
        920: {'zenhan_3f': 20.5, 'kohan_3f': 37.6},  # レース数: 4783
        1300: {'zenhan_3f': 45.0, 'kohan_3f': 39.9},  # レース数: 1474
        1400: {'zenhan_3f': 34.6, 'kohan_3f': 40.1},  # レース数: 10000
        1500: {'zenhan_3f': 33.7, 'kohan_3f': 40.9},  # レース数: 10000
        1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.1},  # レース数: 10000
        1700: {'zenhan_3f': 33.5, 'kohan_3f': 40.4},  # レース数: 7413
        1800: {'zenhan_3f': 44.5, 'kohan_3f': 40.6},  # レース数: 3209
        1900: {'zenhan_3f': 40.5, 'kohan_3f': 40.5},  # レース数: 1834
        2000: {'zenhan_3f': 36.6, 'kohan_3f': 40.6},  # レース数: 792
        2100: {'zenhan_3f': 35.3, 'kohan_3f': 40.5},  # レース数: 222
        2500: {'zenhan_3f': 37.4, 'kohan_3f': 40.4},  # レース数: 180
    },
    '49': {  # 競馬場コード 49
    },
    '50': {  # 競馬場コード 50
        820: {'zenhan_3f': 14.6, 'kohan_3f': 37.5},  # レース数: 9663
        1230: {'zenhan_3f': 45.0, 'kohan_3f': 39.4},  # レース数: 10000
        1400: {'zenhan_3f': 34.9, 'kohan_3f': 40.3},  # レース数: 10000
        1700: {'zenhan_3f': 33.5, 'kohan_3f': 39.6},  # レース数: 10000
        1870: {'zenhan_3f': 42.0, 'kohan_3f': 40.4},  # レース数: 6588
        2400: {'zenhan_3f': 36.9, 'kohan_3f': 39.9},  # レース数: 287
    },
    '51': {  # 競馬場コード 51
        800: {'zenhan_3f': 13.9, 'kohan_3f': 37.3},  # レース数: 2208
        1400: {'zenhan_3f': 34.8, 'kohan_3f': 39.8},  # レース数: 10000
        1500: {'zenhan_3f': 33.6, 'kohan_3f': 39.6},  # レース数: 4241
        1800: {'zenhan_3f': 44.8, 'kohan_3f': 39.7},  # レース数: 1197
        2000: {'zenhan_3f': 37.1, 'kohan_3f': 39.7},  # レース数: 225
    },
}


# 馬場状態補正値（JRDB体系準拠）
BABA_CORRECTION = {
    '1': 0.0,   # 良
    '2': 0.3,   # 稍重
    '3': 0.6,   # 重
    '4': 1.0,   # 不良
}


# 主催者情報（14主催者）
ORGANIZERS = {
    '42': {'name': '大井', 'region': 'MINAMI_KANTO'},
    '43': {'name': '川崎', 'region': 'MINAMI_KANTO'},
    '44': {'name': '船橋', 'region': 'MINAMI_KANTO'},
    '45': {'name': '浦和', 'region': 'MINAMI_KANTO'},
    '30': {'name': '北海道', 'region': 'NAR'},
    '35': {'name': '岩手', 'region': 'NAR'},
    '36': {'name': '金沢', 'region': 'NAR'},
    '46': {'name': '笠松', 'region': 'NAR'},
    '47': {'name': '名古屋', 'region': 'NAR'},
    '48': {'name': '園田', 'region': 'HYOGO'},
    '49': {'name': '姫路', 'region': 'HYOGO'},
    '50': {'name': '高知', 'region': 'NAR'},
    '51': {'name': '佐賀', 'region': 'NAR'},
    '65': {'name': 'ばんえい', 'region': 'BANEI'},
}


def get_base_time(keibajo_code: str, kyori: int, time_type: str) -> float:
    """
    基準タイムを取得
    
    Args:
        keibajo_code: 競馬場コード
        kyori: 距離（m）
        time_type: 'zenhan_3f' または 'kohan_3f'
    
    Returns:
        基準タイム（秒）
    """
    if keibajo_code not in BASE_TIMES:
        raise ValueError(f"競馬場コード {keibajo_code} は未定義です")
    
    if kyori not in BASE_TIMES[keibajo_code]:
        # 最も近い距離の基準タイムを使用
        available_kyori = sorted(BASE_TIMES[keibajo_code].keys())
        if not available_kyori:
            raise ValueError(f"競馬場コード {keibajo_code} にデータがありません")
        
        # 最も近い距離を選択
        closest_kyori = min(available_kyori, key=lambda x: abs(x - kyori))
        kyori = closest_kyori
    
    return BASE_TIMES[keibajo_code][kyori][time_type]
