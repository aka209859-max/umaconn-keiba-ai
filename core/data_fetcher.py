"""
データ取得モジュール
- 明日のレースデータ取得
- 前走データ取得（馬IDベース）
- レース情報取得
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta


def get_tomorrow_date():
    """
    明日の日付を取得（YYYYMMDD形式）
    """
    tomorrow = datetime.now() + timedelta(days=1)
    return tomorrow.strftime('%Y%m%d')


def get_tomorrow_races(conn, target_date=None):
    """
    明日の出走馬データを取得
    
    Args:
        conn: データベース接続
        target_date: 対象日付（YYYYMMDD形式）。Noneの場合は明日
    
    Returns:
        list: 出走馬データのリスト
    """
    if target_date is None:
        target_date = get_tomorrow_date()
    
    query = """
    SELECT 
        keibajo_code,
        race_bango,
        umaban,
        wakuban,
        bamei,
        ketto_toroku_bango,
        kishumei_ryakusho as kishu_mei,
        chokyoshimei_ryakusho as chokyoshi_mei,
        barei,
        seibetsu_code,
        bataiju,
        zogen_sa,
        tansho_odds,
        tansho_ninkijun,
        kaisai_nen,
        kaisai_tsukihi
    FROM nvd_se
    WHERE kaisai_nen || kaisai_tsukihi = %s
      AND keibajo_code != '61'
    ORDER BY keibajo_code, race_bango, umaban
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (target_date,))
        results = cur.fetchall()
    
    print(f"✅ 明日のレースデータ取得: {len(results)}頭")
    return results


def get_previous_race_by_id(conn, ketto_toroku_bango, keibajo_code, current_date):
    """
    馬ID（血統登録番号）で前走データを取得
    
    Args:
        conn: データベース接続
        ketto_toroku_bango: 血統登録番号（馬ID）
        keibajo_code: 競馬場コード
        current_date: 今走の日付（YYYYMMDD形式）
    
    Returns:
        dict: 前走データ（なければNone）
    """
    query = """
    SELECT 
        kakutei_chakujun as prev_chakujun,
        corner_1 as prev_corner_1,
        corner_2 as prev_corner_2,
        corner_3 as prev_corner_3,
        corner_4 as prev_corner_4,
        time_sa as prev_time_sa,
        kohan_3f as prev_kohan_3f,
        wakuban as prev_wakuban,
        tansho_ninkijun as prev_ninkijun,
        keibajo_code as prev_keibajo_code,
        kaisai_nen || kaisai_tsukihi as prev_race_date
    FROM nvd_se se
    LEFT JOIN nvd_ra ra ON 
        se.keibajo_code = ra.keibajo_code AND
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.race_bango = ra.race_bango
    WHERE 
        se.ketto_toroku_bango = %s AND
        se.keibajo_code = %s AND
        se.kakutei_chakujun IS NOT NULL AND
        se.kakutei_chakujun != '' AND
        se.kaisai_nen || se.kaisai_tsukihi < %s
    ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
    LIMIT 1
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (ketto_toroku_bango, keibajo_code, current_date))
        result = cur.fetchone()
    
    return result


def get_race_info(conn, keibajo_code, kaisai_date, race_bango):
    """
    レース情報を取得（nvd_ra から）
    
    Args:
        conn: データベース接続
        keibajo_code: 競馬場コード
        kaisai_date: 開催日（YYYYMMDD形式）
        race_bango: レース番号
    
    Returns:
        dict: レース情報
    """
    query = """
    SELECT 
        kyori,
        track_code,
        baba_jotai_code,
        mawari_code,
        tosu,
        race_mei,
        grade_code,
        joken_code
    FROM nvd_ra
    WHERE 
        keibajo_code = %s AND
        kaisai_nen || kaisai_tsukihi = %s AND
        race_bango = %s
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (keibajo_code, kaisai_date, race_bango))
        result = cur.fetchone()
    
    return result


def get_races_by_date(conn, target_date):
    """
    指定日付のレース一覧を取得（レース単位）
    
    Args:
        conn: データベース接続
        target_date: 対象日付（YYYYMMDD形式）
    
    Returns:
        list: レース情報のリスト
    """
    query = """
    SELECT DISTINCT
        keibajo_code,
        race_bango,
        kaisai_nen || kaisai_tsukihi as kaisai_date
    FROM nvd_se
    WHERE kaisai_nen || kaisai_tsukihi = %s
      AND keibajo_code != '61'
    ORDER BY keibajo_code, race_bango
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (target_date,))
        results = cur.fetchall()
    
    print(f"✅ 対象レース数: {len(results)}レース")
    return results


def enrich_horse_data_with_prev_race(conn, horses_data, current_date):
    """
    出走馬データに前走データを追加
    
    Args:
        conn: データベース接続
        horses_data: 出走馬データのリスト
        current_date: 今走の日付（YYYYMMDD形式）
    
    Returns:
        list: 前走データが追加された出走馬データ
    """
    enriched_data = []
    prev_race_found = 0
    prev_race_not_found = 0
    
    for horse in horses_data:
        # 前走データ取得
        prev_race = get_previous_race_by_id(
            conn,
            horse['ketto_toroku_bango'],
            horse['keibajo_code'],
            current_date
        )
        
        if prev_race:
            # 前走データをマージ
            horse_with_prev = {**horse, **prev_race}
            enriched_data.append(horse_with_prev)
            prev_race_found += 1
        else:
            # 前走データなし（新馬など）
            horse['prev_chakujun'] = None
            horse['prev_corner_1'] = None
            horse['prev_corner_2'] = None
            horse['prev_corner_3'] = None
            horse['prev_corner_4'] = None
            horse['prev_time_sa'] = None
            horse['prev_kohan_3f'] = None
            horse['prev_wakuban'] = None
            horse['prev_ninkijun'] = None
            horse['prev_keibajo_code'] = None
            horse['prev_race_date'] = None
            enriched_data.append(horse)
            prev_race_not_found += 1
    
    print(f"  前走データあり: {prev_race_found}頭")
    print(f"  前走データなし: {prev_race_not_found}頭")
    
    return enriched_data


# テスト用
if __name__ == '__main__':
    import sys
    sys.path.append('/home/user/webapp/nar-ai-yoso')
    from config.db_config import DB_CONFIG
    
    # データベース接続
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # 明日の日付
        tomorrow = get_tomorrow_date()
        print(f"対象日付: {tomorrow}")
        
        # 明日のレース一覧
        races = get_races_by_date(conn, tomorrow)
        print(f"\n対象レース数: {len(races)}レース")
        
        # 明日の出走馬データ
        horses = get_tomorrow_races(conn, tomorrow)
        print(f"\n出走馬数: {len(horses)}頭")
        
        # 前走データ追加
        if horses:
            print("\n前走データ取得中...")
            enriched_horses = enrich_horse_data_with_prev_race(conn, horses[:5], tomorrow)
            
            # サンプル表示
            if enriched_horses:
                print("\n【サンプルデータ】")
                sample = enriched_horses[0]
                print(f"競馬場: {sample['keibajo_code']}")
                print(f"レース: {sample['race_bango']}R")
                print(f"馬番: {sample['umaban']}番")
                print(f"馬名: {sample['bamei']}")
                print(f"騎手: {sample['kishu_mei']}")
                print(f"前走着順: {sample.get('prev_chakujun', 'なし')}")
                print(f"前走4コーナー: {sample.get('prev_corner_4', 'なし')}")
    
    finally:
        conn.close()
        print("\n✅ テスト完了")
