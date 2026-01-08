"""
NAR-SI Ver.2.1-B: 適正化版（バランス型）
================================================================================
補正項目:
- 斤量補正: コース別適正化（-0.2/-0.4/-0.6）
- 枠順補正: 縮小版（内枠+2, 外枠-2）
- その他: Ver.2.0と同じ値を維持

目標: 適正化された斤量・枠順 + 他の補正も維持
================================================================================
"""

import sys
sys.path.append('E:/UmaData/nar-analytics-python')

from config.db_config import get_db_connection
from psycopg2.extras import RealDictCursor

# Ver.2.0から全ての補正関数をインポート
from core.nar_si_calculator_v2_enhanced import (
    get_base_time,
    calculate_nar_si_base,
    get_previous_race_data_v2,
    get_course_adjustment,
    calculate_pace_index,
    get_night_race_adjustment,
    get_distance_adjustment_v2,
    get_track_condition_adjustment,
    get_class_adjustment
)

# Ver.2.1-Aから適正化された補正関数をインポート
from core.nar_si_calculator_v2_1_a import (
    calculate_weight_adjustment_v2_1_a,
    get_wakuban_adjustment_v2_1_a
)


def calculate_nar_si_v2_1_b(conn, horse_data, race_info):
    """
    NAR-SI Ver.2.1-B計算（バランス版）
    
    Args:
        conn: DB接続
        horse_data: 馬データ
        race_info: レース情報
    
    Returns:
        dict: 計算結果
    """
    base_nar_si = horse_data.get('prev_nar_si', 0)
    
    # コース情報取得
    course_data = get_course_adjustment(conn, race_info['keibajo_code'])
    course_classification = course_data['course_classification']
    
    # 斤量補正（適正化版）
    weight_adj = calculate_weight_adjustment_v2_1_a(
        horse_data.get('prev_bataiju'),
        horse_data.get('bataiju'),
        course_classification
    )
    
    # ペース補正（Ver.2.0と同じ）
    pace_adj = calculate_pace_index(
        horse_data.get('prev_kohan_3f'),
        horse_data.get('prev_soha_time')
    )
    
    # 枠順補正（縮小版）
    wakuban_adj = get_wakuban_adjustment_v2_1_a(
        course_classification,
        horse_data.get('wakuban')
    )
    
    # 距離適性補正（Ver.2.0と同じ）
    distance_adj = get_distance_adjustment_v2(
        conn,
        course_classification,
        horse_data.get('prev_kyori'),
        race_info.get('kyori')
    )
    
    # コース特性補正（Ver.2.0と同じ）
    course_adj = (
        course_data['base_adjustment'] +
        course_data['left_turn_adjustment'] +
        course_data['spiral_curve_adjustment'] +
        course_data['sand_depth_adjustment']
    )
    
    # ナイター補正（Ver.2.0と同じ）
    night_adj = get_night_race_adjustment(conn, race_info)
    
    # 馬場状態補正（Ver.2.0と同じ）
    track_adj = get_track_condition_adjustment(
        conn,
        race_info['keibajo_code'],
        race_info.get('babajotai_code')
    )
    
    # クラス補正（Ver.2.0と同じ）
    class_adj = get_class_adjustment(
        conn,
        race_info.get('kyoso_joken_code')
    )
    
    # 最終NAR-SI（全補正適用）
    final_nar_si = (
        base_nar_si + weight_adj + pace_adj + wakuban_adj +
        distance_adj + course_adj + night_adj + track_adj + class_adj
    )
    
    return {
        'final_nar_si': round(final_nar_si, 2),
        'base_nar_si': round(base_nar_si, 2),
        'adjustments': {
            'weight': weight_adj,
            'pace': pace_adj,
            'wakuban': wakuban_adj,
            'distance': distance_adj,
            'course': course_adj,
            'night': night_adj,
            'track': track_adj,
            'class': class_adj
        }
    }


def predict_race_with_nar_si_v2_1_b(conn, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango):
    """
    NAR-SI Ver.2.1-Bでレース予測
    """
    from psycopg2.extras import RealDictCursor
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # レース情報を取得
    cursor.execute("""
        SELECT DISTINCT
            ra.kyori,
            ra.track_code,
            ra.babajotai_code_dirt AS babajotai_code,
            ra.kyoso_joken_code,
            ra.hasso_jikoku AS hassoujikoku
        FROM nvd_ra ra
        WHERE ra.kaisai_nen = %s
          AND ra.kaisai_tsukihi = %s
          AND ra.keibajo_code = %s
          AND ra.race_bango = %s
    """, (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
    
    race_info_row = cursor.fetchone()
    if not race_info_row:
        return []
    
    race_info = {
        'keibajo_code': keibajo_code,
        'kyori': race_info_row['kyori'],
        'track_code': race_info_row['track_code'],
        'babajotai_code': race_info_row['babajotai_code'],
        'kyoso_joken_code': race_info_row['kyoso_joken_code'],
        'hassoujikoku': race_info_row['hassoujikoku'],
        'kaisai_tsukihi': kaisai_tsukihi
    }
    
    # 出走馬を取得
    cursor.execute("""
        SELECT 
            se.umaban,
            se.bamei,
            se.wakuban,
            se.bataiju,
            se.kakutei_chakujun,
            se.ketto_toroku_bango
        FROM nvd_se se
        WHERE se.kaisai_nen = %s
          AND se.kaisai_tsukihi = %s
          AND se.keibajo_code = %s
          AND se.race_bango = %s
        ORDER BY CAST(se.umaban AS INTEGER)
    """, (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
    
    horses = cursor.fetchall()
    results = []
    
    for horse in horses:
        prev_data = get_previous_race_data_v2(
            conn,
            horse['ketto_toroku_bango'],
            kaisai_nen,
            kaisai_tsukihi,
            keibajo_code,
            race_bango
        )
        
        if not prev_data:
            continue
        
        horse_data = {
            'umaban': horse['umaban'],
            'bamei': horse['bamei'],
            'wakuban': horse['wakuban'],
            'bataiju': horse['bataiju'],
            'kakutei_chakujun': horse['kakutei_chakujun'],
            'prev_nar_si': prev_data['prev_nar_si'],
            'prev_bataiju': prev_data['prev_bataiju'],
            'prev_kohan_3f': prev_data['prev_kohan_3f'],
            'prev_soha_time': prev_data['prev_soha_time'],
            'prev_kyori': prev_data['prev_kyori']
        }
        
        nar_si_result = calculate_nar_si_v2_1_b(conn, horse_data, race_info)
        
        results.append({
            'umaban': horse['umaban'],
            'bamei': horse['bamei'],
            'wakuban': horse['wakuban'],
            'kakutei_chakujun': horse['kakutei_chakujun'],
            'final_nar_si': nar_si_result['final_nar_si'],
            'base_nar_si': nar_si_result['base_nar_si'],
            'adjustments': nar_si_result['adjustments']
        })
    
    results.sort(key=lambda x: x['final_nar_si'], reverse=True)
    return results
