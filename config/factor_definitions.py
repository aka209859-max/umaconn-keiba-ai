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
    },
    # Phase 1 高優先度ファクター（2026-01-06 追加）
    {
        'id': 'F17',
        'name': '馬齢',
        'table': 'nvd_se',
        'column': 'barei',
        'display_column': 'barei'
    },
    {
        'id': 'F22',
        'name': '前走タイム差',
        'table': 'nvd_se',
        'column': 'prev_time_sa',  # 前走データから取得
        'display_column': 'prev_time_sa'
    },
    {
        'id': 'F23',
        'name': '前走上がり3F',
        'table': 'nvd_se',
        'column': 'prev_kohan_3f',  # 前走データから取得
        'display_column': 'prev_kohan_3f'
    },
    {
        'id': 'F28',
        'name': '出走頭数',
        'table': 'nvd_ra',
        'column': 'tosu',
        'display_column': 'tosu'
    },
    # Phase 2 中優先度ファクター（2026-01-07 追加）
    {
        'id': 'F25',
        'name': '単勝オッズ',
        'table': 'nvd_se',
        'column': 'tansho_odds',
        'display_column': 'tansho_odds'
    },
    {
        'id': 'F26',
        'name': '単勝人気順',
        'table': 'nvd_se',
        'column': 'tansho_ninkijun',
        'display_column': 'tansho_ninkijun'
    },
    {
        'id': 'F27',
        'name': 'トラックコード',
        'table': 'nvd_ra',
        'column': 'track_code',
        'display_column': 'track_code'
    },
    {
        'id': 'F29',
        'name': 'グレードコード',
        'table': 'nvd_ra',
        'column': 'grade_code',
        'display_column': 'grade_code'
    },
    # Phase 3 血統ファクター（2026-01-07 追加・修正）
    # 重要: 血統データは nvd_um（競走馬マスタ）テーブルに存在
    # nvd_se には存在しない！
    # 取得には ketto_toroku_bango をキーに nvd_um と LEFT JOIN が必須
    {
        'id': 'B15',
        'name': '父ID',
        'table': 'nvd_um',
        'column': 'fufu_ketto_toroku_bango',  # 正式列名（デープサーチ確認済み）
        'display_column': 'fufu_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango'  # nvd_se との結合キー
    },
    {
        'id': 'B16',
        'name': '母ID',
        'table': 'nvd_um',
        'column': 'bobo_ketto_toroku_bango',  # 正式列名
        'display_column': 'bobo_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango'
    },
    {
        'id': 'B17',
        'name': '父父ID',
        'table': 'nvd_um',
        'column': 'fufu_ketto_toroku_bango',  # 父の父（再帰JOIN）
        'display_column': 'fufu_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango',
        'recursive': True,  # 2段階JOIN必要
        'parent_table': 'sire'  # 父テーブルからさらにJOIN
    },
    {
        'id': 'B18',
        'name': '父母ID',
        'table': 'nvd_um',
        'column': 'bobo_ketto_toroku_bango',  # 父の母（再帰JOIN）
        'display_column': 'bobo_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango',
        'recursive': True,
        'parent_table': 'sire'
    },
    {
        'id': 'B19',
        'name': '母父ID（BMS）',
        'table': 'nvd_um',
        'column': 'hahachichi_ketto_toroku_bango',  # 正式列名（母の父）
        'display_column': 'hahachichi_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango',
        'note': 'BMS（Broodmare Sire）: 地方競馬で重要'
    },
    {
        'id': 'B20',
        'name': '母母ID',
        'table': 'nvd_um',
        'column': 'bobo_ketto_toroku_bango',  # 母の母（再帰JOIN）
        'display_column': 'bobo_ketto_toroku_bango',
        'join_key': 'ketto_toroku_bango',
        'recursive': True,
        'parent_table': 'dam'  # 母テーブルからさらにJOIN
    },
    # Phase 3 その他ファクター（2026-01-07 追加）
    {
        'id': 'F24',
        'name': '前走枠番',
        'table': 'nvd_se',
        'column': 'prev_wakuban',  # 前走データから取得
        'display_column': 'prev_wakuban'
    },
    # Phase 2 新規ファクター（2026-01-08 追加）
    {
        'id': 'F34',
        'name': '推定前半3F',
        'table': 'computed',
        'column': 'estimated_ten_3f',  # Ten3FEstimatorで計算
        'display_column': 'estimated_ten_3f',
        'note': 'Ten3FEstimator（Layer 1-3）で推定した前半3Fタイム（秒）'
    },
    {
        'id': 'F35',
        'name': 'ペース変化率',
        'table': 'computed',
        'column': 'pace_change_rate',  # (kohan_3f - zenhan_3f) / zenhan_3f で計算
        'display_column': 'pace_change_rate',
        'note': 'ペース変化率 = (後半3F - 前半3F) / 前半3F（正値は失速、負値は加速）'
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
