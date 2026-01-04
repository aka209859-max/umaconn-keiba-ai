"""
31ファクターの定義とデータベース列のマッピング
"""

# 単独ファクター（16個）
SINGLE_FACTORS = [
    {
        'id': 'F01',
        'name': '騎手',
        'table': 'nvd_se',
        'column': 'kishu_code',
        'display_column': 'kishumei_ryakusho'
    },
    {
        'id': 'F02',
        'name': '調教師',
        'table': 'nvd_se',
        'column': 'chokyoshi_code',
        'display_column': 'chokyoshimei_ryakusho'
    },
    {
        'id': 'F03',
        'name': '距離適性',
        'table': 'nvd_ra',
        'column': 'kyori',
        'display_column': 'kyori'
    },
    {
        'id': 'F04',
        'name': '馬場状態',
        'table': 'nvd_ra',
        'column': 'babajotai_code_dirt',  # ダート馬場状態
        'display_column': 'babajotai_code_dirt'
    },
    {
        'id': 'F05',
        'name': '回り',
        'table': 'nvd_ra',
        'column': 'mawari_code',  # 左/右
        'display_column': 'mawari_code'
    },
    {
        'id': 'F06',
        'name': '条件',
        'table': 'nvd_ra',
        'column': 'kyoso_joken_code',  # クラス条件
        'display_column': 'kyoso_joken_meisho'
    },
    {
        'id': 'F07',
        'name': '脚質',
        'table': 'nvd_se',
        'column': 'computed_ashishitsu',  # 計算で求める
        'display_column': 'computed_ashishitsu'
    },
    {
        'id': 'F08',
        'name': '枠番',
        'table': 'nvd_se',
        'column': 'wakuban',
        'display_column': 'wakuban'
    },
    {
        'id': 'F09',
        'name': '前走着順',
        'table': 'nvd_se',
        'column': 'prev_chakujun',  # 前走データから取得
        'display_column': 'prev_chakujun'
    },
    {
        'id': 'F10',
        'name': '前走人気',
        'table': 'nvd_se',
        'column': 'prev_ninki',  # 前走データから取得
        'display_column': 'prev_ninki'
    },
    {
        'id': 'F11',
        'name': '前走距離',
        'table': 'nvd_se',
        'column': 'prev_kyori',  # 前走データから取得
        'display_column': 'prev_kyori'
    },
    {
        'id': 'F12',
        'name': '前走馬場',
        'table': 'nvd_se',
        'column': 'prev_baba',  # 前走データから取得
        'display_column': 'prev_baba'
    },
    {
        'id': 'F13',
        'name': '休養週数',
        'table': 'nvd_se',
        'column': 'computed_kyuyo_weeks',  # 計算で求める
        'display_column': 'computed_kyuyo_weeks'
    },
    {
        'id': 'F14',
        'name': '馬体重',
        'table': 'nvd_se',
        'column': 'bataiju',
        'display_column': 'bataiju'
    },
    {
        'id': 'F15',
        'name': '馬体重増減',
        'table': 'nvd_se',
        'column': 'zogen_sa',
        'display_column': 'zogen_sa'
    },
    {
        'id': 'F16',
        'name': '性別',
        'table': 'nvd_se',
        'column': 'seibetsu_code',
        'display_column': 'seibetsu_code'
    }
]

# 組み合わせファクター（15個）
COMBINED_FACTORS = [
    {
        'id': 'C01',
        'name': '騎手×距離',
        'factors': ['F01', 'F03']
    },
    {
        'id': 'C02',
        'name': '騎手×馬場状態',
        'factors': ['F01', 'F04']
    },
    {
        'id': 'C03',
        'name': '騎手×回り',
        'factors': ['F01', 'F05']
    },
    {
        'id': 'C04',
        'name': '騎手×条件',
        'factors': ['F01', 'F06']
    },
    {
        'id': 'C05',
        'name': '調教師×距離',
        'factors': ['F02', 'F03']
    },
    {
        'id': 'C06',
        'name': '調教師×馬場状態',
        'factors': ['F02', 'F04']
    },
    {
        'id': 'C07',
        'name': '距離×馬場状態',
        'factors': ['F03', 'F04']
    },
    {
        'id': 'C08',
        'name': '距離×回り',
        'factors': ['F03', 'F05']
    },
    {
        'id': 'C09',
        'name': '脚質×距離',
        'factors': ['F07', 'F03']
    },
    {
        'id': 'C10',
        'name': '脚質×馬場状態',
        'factors': ['F07', 'F04']
    },
    {
        'id': 'C11',
        'name': '枠番×距離',
        'factors': ['F08', 'F03']
    },
    {
        'id': 'C12',
        'name': '前走着順×休養週数',
        'factors': ['F09', 'F13']
    },
    {
        'id': 'C13',
        'name': '前走人気×前走着順',
        'factors': ['F10', 'F09']
    },
    {
        'id': 'C14',
        'name': '馬体重増減×休養週数',
        'factors': ['F15', 'F13']
    },
    {
        'id': 'C15',
        'name': '性別×距離',
        'factors': ['F16', 'F03']
    }
]

# 全31ファクター
ALL_FACTORS = SINGLE_FACTORS + COMBINED_FACTORS


def get_factor_by_id(factor_id):
    """
    ファクターIDからファクター定義を取得
    """
    for factor in ALL_FACTORS:
        if factor['id'] == factor_id:
            return factor
    return None


def get_single_factor_ids():
    """
    単独ファクターのIDリストを取得
    """
    return [f['id'] for f in SINGLE_FACTORS]


def get_combined_factor_ids():
    """
    組み合わせファクターのIDリストを取得
    """
    return [f['id'] for f in COMBINED_FACTORS]
