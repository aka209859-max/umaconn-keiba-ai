"""
地方競馬全14競馬場の基準タイム設定（実データ版 - v10）

✅ 競馬場コード修正完了（公式発表の正しいコード）
✅ 実データから算出（2026-01-09 v10実行結果）
✅ 特殊期間フィルタ適用済み
  - 大井（'44'）: 2023-10-01 以降（オーストラリア産白砂への全面置換）
  - 名古屋（'48'）: 2022-04-01 以降（大幅改修実施）

作成日: 2026-01-09
データソース: nvd_ra, nvd_se (PostgreSQL)
計算方法: Ten3FEstimator（AI推定） + 1200m確定値
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


# ============================
# 1. 競馬場マスター（公式発表の正しいコード）
# ============================

# 地方競馬全14競馬場（NARコード）
KEIBAJO_MASTER = {
    # 北海道
    '30': {'name': '門別', 'region': '北海道', 'abbreviation': '門', 'english': 'MONBETSU'},
    
    # 東北
    '35': {'name': '盛岡', 'region': '岩手県', 'abbreviation': '盛', 'english': 'MORIOKA'},
    '36': {'name': '水沢', 'region': '岩手県', 'abbreviation': '水', 'english': 'MIZUSAWA'},
    
    # 南関東4場
    '42': {'name': '浦和', 'region': '埼玉県', 'abbreviation': '浦', 'english': 'URAWA'},
    '43': {'name': '船橋', 'region': '千葉県', 'abbreviation': '船', 'english': 'FUNABASHI'},
    '44': {'name': '大井', 'region': '東京都', 'abbreviation': '大', 'english': 'OHI'},
    '45': {'name': '川崎', 'region': '神奈川県', 'abbreviation': '川', 'english': 'KAWASAKI'},
    
    # 北陸・東海
    '46': {'name': '金沢', 'region': '石川県', 'abbreviation': '金', 'english': 'KANAZAWA'},
    '47': {'name': '笠松', 'region': '岐阜県', 'abbreviation': '笠', 'english': 'KASAMATSU'},
    '48': {'name': '名古屋', 'region': '愛知県', 'abbreviation': '古', 'english': 'NAGOYA'},
    
    # 近畿
    '50': {'name': '園田', 'region': '兵庫県', 'abbreviation': '園', 'english': 'SONODA'},
    '51': {'name': '姫路', 'region': '兵庫県', 'abbreviation': '姫', 'english': 'HIMEJI'},
    
    # 四国・九州
    '54': {'name': '高知', 'region': '高知県', 'abbreviation': '高', 'english': 'KOCHI'},
    '55': {'name': '佐賀', 'region': '佐賀県', 'abbreviation': '佐', 'english': 'SAGA'},
}

# 廃止済み競馬場（参考情報）
ABOLISHED_KEIBAJO = {
    '31': '北見（2007年廃止）',
    '32': '岩見沢（2008年廃止）',
    '34': '旭川（2004年廃止）',
    '37': '上山（2002年廃止）',
    '38': '三条（1999年廃止）',
    '39': '足利（2001年廃止）',
    '40': '宇都宮（2001年廃止）',
    '41': '高崎（2004年廃止）',
    '49': '紀三井寺（2001年廃止）',
    '52': '益田（2002年廃止）',
    '53': '福山（2001年廃止）',
    '56': '荒尾（2011年廃止）',
    '57': '中津（2001年廃止）',
}

# 特殊競馬場
SPECIAL_KEIBAJO = {
    '33': 'ばんえい帯広（特殊形態）',
}


# ============================
# 2. 基準タイム（実データ版 v10）
# ============================

# 基準タイム: 実データから算出（良馬場・上位5頭・中央値）
# データソース: E:\UmaData\nar-analytics-python-v2\output\base_times_result_20260109_010613.txt
# 計算方法: 
#   - 1200m: 確定値（soha_time - kohan_3f）
#   - その他: Ten3FEstimator（AI推定）

BASE_TIMES = {
  '30': {  # 門別
    1000: {'zenhan_3f': 33.0, 'kohan_3f': 38.5, 'race_count': 1000},
    1100: {'zenhan_3f': 35.0, 'kohan_3f': 39.2, 'race_count': 730},
    1200: {'zenhan_3f': 36.8, 'kohan_3f': 39.4, 'race_count': 1000},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 41.3, 'race_count': 525},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 41.1, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 39.7, 'race_count': 1000},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.6, 'race_count': 1000},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 39.8, 'race_count': 305},
    2600: {'zenhan_3f': 33.0, 'kohan_3f': 40.2, 'race_count': 35},
  },
  '35': {  # 盛岡
    1000: {'zenhan_3f': 33.0, 'kohan_3f': 36.3, 'race_count': 1000},
    1200: {'zenhan_3f': 37.7, 'kohan_3f': 38.9, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.4, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 39.0, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 37.3, 'race_count': 705},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.0, 'race_count': 995},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 39.0, 'race_count': 215},
    2400: {'zenhan_3f': 33.5, 'kohan_3f': 37.3, 'race_count': 145},
  },
  '36': {  # 水沢
    850: {'zenhan_3f': 33.0, 'kohan_3f': 37.2, 'race_count': 1000},
    1300: {'zenhan_3f': 41.4, 'kohan_3f': 40.5, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 40.5, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.3, 'race_count': 1000},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.9, 'race_count': 455},
    1900: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 70},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 40.4, 'race_count': 115},
  },
  '42': {  # 浦和
    800: {'zenhan_3f': 33.0, 'kohan_3f': 36.9, 'race_count': 1000},
    1300: {'zenhan_3f': 41.2, 'kohan_3f': 40.2, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 1000},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 39.6, 'race_count': 1000},
    1900: {'zenhan_3f': 33.0, 'kohan_3f': 39.6, 'race_count': 220},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 40.1, 'race_count': 862},
  },
  '43': {  # 船橋
    1000: {'zenhan_3f': 33.0, 'kohan_3f': 37.9, 'race_count': 1000},
    1200: {'zenhan_3f': 36.7, 'kohan_3f': 39.2, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 41.0, 'race_count': 225},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 40.1, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 39.7, 'race_count': 815},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.6, 'race_count': 850},
    2200: {'zenhan_3f': 33.0, 'kohan_3f': 40.8, 'race_count': 404},
    2400: {'zenhan_3f': 33.0, 'kohan_3f': 39.5, 'race_count': 40},
  },
  '44': {  # 大井（2023-10-01以降のみ）
    1000: {'zenhan_3f': 33.0, 'kohan_3f': 37.4, 'race_count': 30},
    1200: {'zenhan_3f': 36.9, 'kohan_3f': 38.8, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.2, 'race_count': 654},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.5, 'race_count': 870},
    1650: {'zenhan_3f': 33.0, 'kohan_3f': 40.2, 'race_count': 35},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 38.9, 'race_count': 25},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 190},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 39.2, 'race_count': 80},
    2600: {'zenhan_3f': 33.0, 'kohan_3f': 39.8, 'race_count': 10},
  },
  '45': {  # 川崎
    900: {'zenhan_3f': 33.0, 'kohan_3f': 37.8, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 40.5, 'race_count': 1000},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 40.5, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 40.1, 'race_count': 1000},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 40.7, 'race_count': 1000},
    2100: {'zenhan_3f': 33.0, 'kohan_3f': 39.9, 'race_count': 455},
  },
  '46': {  # 金沢
    900: {'zenhan_3f': 33.0, 'kohan_3f': 37.6, 'race_count': 467},
    1300: {'zenhan_3f': 41.3, 'kohan_3f': 39.6, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 1000},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 39.9, 'race_count': 1000},
    1900: {'zenhan_3f': 33.0, 'kohan_3f': 39.5, 'race_count': 294},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 40.0, 'race_count': 165},
    2100: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 85},
    2300: {'zenhan_3f': 33.0, 'kohan_3f': 40.6, 'race_count': 25},
    2600: {'zenhan_3f': 33.0, 'kohan_3f': 40.4, 'race_count': 10},
  },
  '47': {  # 笠松
    800: {'zenhan_3f': 33.0, 'kohan_3f': 37.0, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.1, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 38.8, 'race_count': 1000},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 38.5, 'race_count': 760},
    1900: {'zenhan_3f': 33.0, 'kohan_3f': 38.9, 'race_count': 280},
    2500: {'zenhan_3f': 33.0, 'kohan_3f': 38.8, 'race_count': 45},
  },
  '48': {  # 名古屋（2022-04-01以降のみ）
    900: {'zenhan_3f': 33.0, 'kohan_3f': 37.8, 'race_count': 67},
    920: {'zenhan_3f': 33.0, 'kohan_3f': 37.2, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.4, 'race_count': 830},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 40.1, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 39.8, 'race_count': 1000},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 39.6, 'race_count': 170},
    2100: {'zenhan_3f': 33.0, 'kohan_3f': 39.2, 'race_count': 65},
  },
  '50': {  # 園田
    820: {'zenhan_3f': 33.0, 'kohan_3f': 37.1, 'race_count': 1000},
    1230: {'zenhan_3f': 39.9, 'kohan_3f': 39.1, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 40.5, 'race_count': 1000},
    1700: {'zenhan_3f': 33.0, 'kohan_3f': 39.2, 'race_count': 1000},
    1870: {'zenhan_3f': 33.0, 'kohan_3f': 39.9, 'race_count': 1000},
    2400: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 80},
  },
  '51': {  # 姫路
    800: {'zenhan_3f': 33.0, 'kohan_3f': 37.0, 'race_count': 696},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.7, 'race_count': 1000},
    1500: {'zenhan_3f': 33.0, 'kohan_3f': 39.0, 'race_count': 1000},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 445},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 38.9, 'race_count': 80},
  },
  '54': {  # 高知
    800: {'zenhan_3f': 33.0, 'kohan_3f': 37.7, 'race_count': 390},
    1300: {'zenhan_3f': 42.5, 'kohan_3f': 41.2, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 41.1, 'race_count': 1000},
    1600: {'zenhan_3f': 33.0, 'kohan_3f': 41.2, 'race_count': 1000},
    1800: {'zenhan_3f': 33.5, 'kohan_3f': 40.7, 'race_count': 35},
    1900: {'zenhan_3f': 33.0, 'kohan_3f': 41.8, 'race_count': 90},
    2400: {'zenhan_3f': 33.5, 'kohan_3f': 40.9, 'race_count': 25},
  },
  '55': {  # 佐賀
    900: {'zenhan_3f': 33.0, 'kohan_3f': 37.6, 'race_count': 1000},
    1300: {'zenhan_3f': 41.2, 'kohan_3f': 39.6, 'race_count': 1000},
    1400: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 1000},
    1750: {'zenhan_3f': 33.0, 'kohan_3f': 39.3, 'race_count': 1000},
    1800: {'zenhan_3f': 33.0, 'kohan_3f': 39.1, 'race_count': 1000},
    1860: {'zenhan_3f': 33.0, 'kohan_3f': 39.5, 'race_count': 85},
    2000: {'zenhan_3f': 33.0, 'kohan_3f': 39.2, 'race_count': 395},
    2500: {'zenhan_3f': 33.0, 'kohan_3f': 39.8, 'race_count': 40},
  },
}


# ============================
# 3. 馬場状態補正値
# ============================

# 馬場状態補正（babajotai_code_dirt / babajotai_code_shiba）
BABA_CORRECTION = {
    '1': 0.0,   # 良
    '2': 0.3,   # 稍重（+0.3秒）
    '3': 0.6,   # 重（+0.6秒）
    '4': 1.0,   # 不良（+1.0秒）
}


# ============================
# 4. ヘルパー関数
# ============================

def get_base_time(keibajo_code: str, kyori: int, time_type: str) -> float:
    """
    基準タイムを取得
    
    Args:
        keibajo_code: 競馬場コード（30-55）
        kyori: 距離（m）
        time_type: 'zenhan_3f' or 'kohan_3f'
    
    Returns:
        基準タイム（秒）
    """
    if keibajo_code not in BASE_TIMES:
        logger.warning(f"未対応の競馬場コード: {keibajo_code}、デフォルト値を使用")
        return 33.0 if time_type == 'zenhan_3f' else 39.0
    
    venue_times = BASE_TIMES[keibajo_code]
    
    # 完全一致
    if kyori in venue_times:
        return venue_times[kyori][time_type]
    
    # 最も近い距離を検索
    closest_kyori = min(venue_times.keys(), key=lambda k: abs(k - kyori))
    keibajo_name = KEIBAJO_MASTER.get(keibajo_code, {}).get('name', keibajo_code)
    logger.info(f"{keibajo_name}競馬場: 距離{kyori}mの基準タイムなし。{closest_kyori}mを使用")
    
    return venue_times[closest_kyori][time_type]


def get_keibajo_info(keibajo_code: str) -> Dict:
    """
    競馬場情報を取得
    
    Args:
        keibajo_code: 競馬場コード
    
    Returns:
        競馬場情報の辞書
    """
    return KEIBAJO_MASTER.get(keibajo_code, {
        'name': '不明',
        'region': '不明',
        'abbreviation': '?',
        'english': 'UNKNOWN'
    })


def get_baba_correction(baba_code: str) -> float:
    """
    馬場状態補正値を取得
    
    Args:
        baba_code: 馬場状態コード（'1'-'4'）
    
    Returns:
        補正値（秒）
    """
    return BABA_CORRECTION.get(baba_code, 0.0)


# ============================
# 5. テスト用メイン関数
# ============================

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(level=logging.INFO)
    
    # テスト: 各競馬場の基準タイム確認
    print("\n=== 地方競馬全14競馬場の基準タイム（実データ版 v10） ===\n")
    
    test_kyori = 1600  # 基準距離
    
    for code in sorted(KEIBAJO_MASTER.keys()):
        info = KEIBAJO_MASTER[code]
        
        try:
            zenhan = get_base_time(code, test_kyori, 'zenhan_3f')
            kohan = get_base_time(code, test_kyori, 'kohan_3f')
            
            print(f"{info['name']:6s} ({code}): "
                  f"前半3F={zenhan:.1f}秒, 後半3F={kohan:.1f}秒 "
                  f"[{info['region']:8s}]")
        except Exception as e:
            print(f"{info['name']:6s} ({code}): エラー - {e}")
    
    print("\n=== 1200m戦の基準タイム確認 ===\n")
    
    for code in ['30', '35', '43', '44']:  # 門別、盛岡、船橋、大井
        info = KEIBAJO_MASTER[code]
        
        try:
            zenhan = get_base_time(code, 1200, 'zenhan_3f')
            kohan = get_base_time(code, 1200, 'kohan_3f')
            race_count = BASE_TIMES[code][1200]['race_count']
            
            print(f"{info['name']:6s} 1200m: "
                  f"前半3F={zenhan:.1f}秒, 後半3F={kohan:.1f}秒 "
                  f"(サンプル数: {race_count})")
        except Exception as e:
            print(f"{info['name']:6s} 1200m: データなし")
    
    print("\n✅ テスト完了")
