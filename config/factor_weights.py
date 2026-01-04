"""
競馬場別ファクター重み設定

31ファクター:
- 単独ファクター: 16項目
- 組み合わせファクター: 15項目
"""

# デフォルト重み（標準的な競馬場）
DEFAULT_FACTOR_WEIGHTS = {
    # 単独ファクター（16項目）
    'prev_chakujun': 1.8,        # 前走着順
    'prev_corner_1': 1.2,        # 前走1コーナー順位
    'prev_corner_2': 1.2,        # 前走2コーナー順位
    'prev_corner_3': 1.2,        # 前走3コーナー順位
    'prev_corner_4': 1.5,        # 前走4コーナー順位
    'prev_time_sa': 1.3,         # 前走タイム差
    'prev_kohan_3f': 1.6,        # 前走上がり3F
    'umaban': 1.2,               # 馬番
    'wakuban': 1.5,              # 枠番
    'seibetsu_code': 0.9,        # 性別
    'bataiju': 1.0,              # 馬体重
    'zogen_sa': 0.8,             # 馬体重増減
    'barei': 1.1,                # 馬齢
    'chokyoshi_mei': 1.5,        # 調教師
    'kishu_mei': 1.8,            # 騎手
    'tosu': 0.8,                 # 出走頭数
    
    # 組み合わせファクター（15項目）
    'kishu_wakuban': 1.6,                    # 騎手×枠番
    'prev_kyori_current_kyori': 1.5,        # 前走距離×今走距離
    'baba_jotai_wakuban': 1.4,              # 馬場状態×枠番
    'joken_code_prev_joken': 1.2,           # 条件コード×前走条件
    'prev_chakujun_corner4': 1.6,           # 前走着順×前走4コーナー
    'prev_chakujun_kohan3f': 1.7,           # 前走着順×前走上がり3F
    'kishu_prev_chakujun': 1.5,             # 騎手×前走着順
    'seibetsu_kyori': 1.3,                  # 性別×距離
    'barei_prev_chakujun': 1.4,             # 馬齢×前走着順
    'wakuban_prev_wakuban': 1.2,            # 枠番×前走枠番
    'kishu_chokyoshi': 1.6,                 # 騎手×調教師
    'course_type': 1.5,                     # コース分類
    'mawari_code': 1.2,                     # 回り（左/右）
    'straight_kohan3f': 1.5,                # 直線距離×前走上がり3F
    'corner_count_corner': 1.4,             # コーナー回数×前走コーナー順位
}

# 競馬場別ファクター重み
KEIBAJO_FACTOR_WEIGHTS = {
    # 門別競馬（広い・タフ・パワー勝負）
    '30': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 2.0,
        'prev_kohan_3f': 2.0,
        'prev_corner_4': 1.8,
        'kishu_mei': 1.8,
        'barei': 1.5,
        'wakuban': 1.2,
        'course_type': 2.0,
        'straight_kohan3f': 1.8,
        'prev_chakujun_kohan3f': 2.0,
    },
    
    # 盛岡競馬（広い・タフ）
    '35': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 2.0,
        'prev_kohan_3f': 2.0,
        'prev_corner_4': 1.8,
        'kishu_mei': 1.8,
        'wakuban': 1.2,
        'course_type': 2.0,
    },
    
    # 水沢競馬
    '36': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 1.8,
        'kishu_mei': 1.8,
        'wakuban': 1.5,
    },
    
    # 浦和競馬（外枠不利・枠番重要）
    '42': {
        **DEFAULT_FACTOR_WEIGHTS,
        'wakuban': 2.2,
        'prev_corner_4': 2.0,
        'prev_chakujun': 1.8,
        'kishu_mei': 1.6,
        'prev_kohan_3f': 1.5,
        'kishu_wakuban': 1.8,
        'baba_jotai_wakuban': 1.8,
        'corner_count_corner': 1.8,
        'course_type': 1.8,
    },
    
    # 船橋競馬（フラット・実力通り）
    '43': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 2.0,
        'kishu_mei': 2.0,
        'chokyoshi_mei': 1.8,
        'prev_kohan_3f': 1.8,
        'wakuban': 1.2,
        'kishu_chokyoshi': 2.0,
        'prev_chakujun_kohan3f': 1.8,
        'seibetsu_kyori': 1.5,
    },
    
    # 大井競馬（内枠超有利・逃げ馬有利）
    '44': {
        **DEFAULT_FACTOR_WEIGHTS,
        'wakuban': 2.5,
        'prev_corner_1': 2.0,
        'prev_chakujun': 1.5,
        'prev_corner_4': 1.3,
        'kishu_mei': 1.5,
        'umaban': 1.2,
        'prev_kohan_3f': 1.0,
        'kishu_wakuban': 2.0,
        'baba_jotai_wakuban': 1.8,
        'mawari_code': 1.5,
    },
    
    # 川崎競馬（超内枠有利・1枠圧倒的）
    '45': {
        **DEFAULT_FACTOR_WEIGHTS,
        'wakuban': 3.0,
        'prev_corner_1': 2.2,
        'kishu_mei': 1.8,
        'prev_chakujun': 1.5,
        'prev_corner_4': 1.2,
        'umaban': 1.0,
        'kishu_wakuban': 2.5,
        'wakuban_prev_wakuban': 2.0,
    },
    
    # 金沢競馬（小回り・先行有利）
    '46': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_corner_1': 1.8,
        'wakuban': 1.8,
        'prev_corner_4': 1.8,
        'prev_chakujun': 1.6,
        'kishu_mei': 1.6,
        'corner_count_corner': 1.8,
        'course_type': 1.8,
    },
    
    # 笠松競馬（小回り・先行有利）
    '47': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_corner_1': 1.8,
        'wakuban': 1.8,
        'prev_corner_4': 1.8,
        'prev_chakujun': 1.6,
        'corner_count_corner': 1.8,
        'course_type': 1.8,
    },
    
    # 名古屋競馬（小回り・先行有利）
    '48': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_corner_1': 1.8,
        'wakuban': 1.8,
        'prev_corner_4': 1.8,
        'prev_chakujun': 1.6,
        'corner_count_corner': 1.8,
        'course_type': 1.8,
    },
    
    # 園田競馬（小回り・急カーブ）
    '50': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_corner_1': 2.0,
        'prev_corner_4': 2.0,
        'wakuban': 1.8,
        'bataiju': 1.5,
        'prev_chakujun': 1.5,
        'kishu_mei': 1.6,
        'corner_count_corner': 2.2,
        'course_type': 2.0,
        'kishu_wakuban': 1.6,
    },
    
    # 姫路競馬
    '51': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 1.8,
        'kishu_mei': 1.8,
        'wakuban': 1.5,
    },
    
    # 高知競馬
    '54': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_chakujun': 1.8,
        'kishu_mei': 1.8,
        'wakuban': 1.5,
    },
    
    # 佐賀競馬（小回り・先行有利）
    '55': {
        **DEFAULT_FACTOR_WEIGHTS,
        'prev_corner_1': 1.8,
        'wakuban': 1.8,
        'prev_corner_4': 1.8,
        'prev_chakujun': 1.6,
        'corner_count_corner': 1.8,
        'course_type': 1.8,
    },
}

def get_factor_weight(keibajo_code, factor_name):
    """
    競馬場別のファクター重みを取得
    
    Args:
        keibajo_code: 競馬場コード
        factor_name: ファクター名
    
    Returns:
        float: ファクター重み（デフォルト: 1.0）
    """
    # ばんえい（帯広）は除外
    if keibajo_code == '61':
        return 0.0
    
    weights = KEIBAJO_FACTOR_WEIGHTS.get(keibajo_code, DEFAULT_FACTOR_WEIGHTS)
    return weights.get(factor_name, 1.0)

# テスト用
if __name__ == '__main__':
    # 大井の枠番重み
    print(f"大井・枠番: {get_factor_weight('44', 'wakuban')}")  # 2.5
    
    # 川崎の枠番重み
    print(f"川崎・枠番: {get_factor_weight('45', 'wakuban')}")  # 3.0
    
    # 船橋の前走着順重み
    print(f"船橋・前走着順: {get_factor_weight('43', 'prev_chakujun')}")  # 2.0
    
    # 帯広（ばんえい）
    print(f"帯広・枠番: {get_factor_weight('61', 'wakuban')}")  # 0.0（除外）
