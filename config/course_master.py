"""
競馬場マスターデータ
- コース分類（広い・タフ / 小回り・先行有利 / 超短距離）
- 直線距離
- コーナー回数
"""

# 競馬場名マスター
KEIBAJO_NAMES = {
    '30': '門別',
    '35': '盛岡',
    '36': '水沢',
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎',
    '46': '金沢',
    '47': '笠松',
    '48': '名古屋',
    '50': '園田',
    '51': '姫路',
    '54': '高知',
    '55': '佐賀',
    # '61': '帯広',  # ばんえいは除外
}

# コース分類マスター
COURSE_CLASSIFICATION = {
    # 広い・タフ（差し・追い込み有利）
    'WIDE_TOUGH': {
        '30': [1600, 1700, 1800, 2000, 2100, 2400, 2600],  # 門別
        '35': [1600, 1800, 2000, 2400],                    # 盛岡
        '44': [1600, 1800, 2000, 2400],                    # 大井（外回り）
    },
    
    # 小回り・先行有利
    'SMALL_SENKO': {
        '42': 'ALL',  # 浦和（全距離）
        '46': 'ALL',  # 金沢（全距離）
        '47': 'ALL',  # 笠松（全距離）
        '48': 'ALL',  # 名古屋（全距離）
        '50': 'ALL',  # 園田（全距離）
        '55': 'ALL',  # 佐賀（全距離）
    },
    
    # 超短距離（スタート・二の脚重視）
    'SUPER_SHORT': [800, 900, 1000]  # 1000m未満
}

# 直線距離マスター（競馬場別）
STRAIGHT_LENGTH = {
    '30': 330,   # 門別
    '35': 300,   # 盛岡
    '36': 300,   # 水沢
    '42': 266,   # 浦和
    '43': 333,   # 船橋
    '44': 380,   # 大井
    '45': 330,   # 川崎
    '46': 260,   # 金沢
    '47': 250,   # 笠松
    '48': 300,   # 名古屋
    '50': 291,   # 園田
    '51': 312,   # 姫路
    '54': 310,   # 高知
    '55': 295,   # 佐賀
}

# コーナー回数マスター（距離別）
def get_corner_count(kyori):
    """
    距離からコーナー回数を推定
    """
    if kyori < 1000:
        return 2  # 超短距離: 2コーナー
    elif kyori < 1400:
        return 4  # 短距離: 4コーナー
    elif kyori < 2000:
        return 4  # 中距離: 4コーナー
    else:
        return 8  # 長距離: 8コーナー（2周）

def get_course_type(keibajo_code, kyori):
    """
    競馬場コードと距離からコース分類を取得
    
    Returns:
        'WIDE_TOUGH' | 'SMALL_SENKO' | 'SUPER_SHORT' | 'STANDARD'
    """
    # 超短距離チェック
    if kyori in COURSE_CLASSIFICATION['SUPER_SHORT']:
        return 'SUPER_SHORT'
    
    # 広い・タフチェック
    if keibajo_code in COURSE_CLASSIFICATION['WIDE_TOUGH']:
        if kyori in COURSE_CLASSIFICATION['WIDE_TOUGH'][keibajo_code]:
            return 'WIDE_TOUGH'
    
    # 小回り・先行有利チェック
    if keibajo_code in COURSE_CLASSIFICATION['SMALL_SENKO']:
        if COURSE_CLASSIFICATION['SMALL_SENKO'][keibajo_code] == 'ALL':
            return 'SMALL_SENKO'
    
    return 'STANDARD'

def get_straight_length(keibajo_code):
    """
    競馬場コードから直線距離を取得
    """
    return STRAIGHT_LENGTH.get(keibajo_code, 300)  # デフォルト300m

# テスト用
if __name__ == '__main__':
    # 大井1600m
    print(f"大井1600m: {get_course_type('44', 1600)}")  # WIDE_TOUGH
    
    # 浦和1400m
    print(f"浦和1400m: {get_course_type('42', 1400)}")  # SMALL_SENKO
    
    # 門別900m
    print(f"門別900m: {get_course_type('30', 900)}")    # SUPER_SHORT
    
    # 直線距離
    print(f"大井直線: {get_straight_length('44')}m")    # 380m
    
    # コーナー回数
    print(f"1600mコーナー: {get_corner_count(1600)}")   # 4
    print(f"2400mコーナー: {get_corner_count(2400)}")   # 8
