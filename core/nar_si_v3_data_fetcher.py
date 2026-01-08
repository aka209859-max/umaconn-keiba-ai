#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
NAR-SI Ver.3.0 - 過去3走データ取得モジュール

過去3走のNAR-SI、着順、レース条件を取得する
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

sys.path.append('E:/UmaData/nar-analytics-python')

from config.db_config import get_db_connection
from psycopg2.extras import RealDictCursor


def get_previous_3_races(conn, ketto_toroku_bango, current_kaisai_nen, current_kaisai_tsukihi):
    """
    血統登録番号から過去3走のデータを取得
    
    Args:
        conn: データベース接続
        ketto_toroku_bango: 血統登録番号
        current_kaisai_nen: 今回の開催年
        current_kaisai_tsukihi: 今回の開催月日
    
    Returns:
        list: 過去3走のデータ（新しい順）
        各要素は以下の辞書:
        {
            'kaisai_nen': 開催年,
            'kaisai_tsukihi': 開催月日,
            'keibajo_code': 競馬場コード,
            'race_bango': レース番号,
            'umaban': 馬番,
            'kakutei_chakujun': 確定着順,
            'soha_time': 走破タイム,
            'bataiju': 馬体重,
            'kyori': 距離,
            'track_code': トラックコード,
            'babajotai_code': 馬場状態コード,
            'hasso_jikoku': 発走時刻,
            'kohan_3f': 後半3F,
        }
    """
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    # 今回のレースより前のデータを取得
    current_date = current_kaisai_nen + current_kaisai_tsukihi
    
    query = """
    SELECT 
        se.kaisai_nen,
        se.kaisai_tsukihi,
        se.keibajo_code,
        se.race_bango,
        se.umaban,
        se.kakutei_chakujun,
        se.soha_time,
        se.bataiju,
        ra.kyori,
        ra.track_code,
        ra.babajotai_code_dirt as babajotai_code,
        ra.hasso_jikoku,
        ra.kohan_3f
    FROM nvd_se se
    INNER JOIN nvd_ra ra ON 
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.keibajo_code = ra.keibajo_code AND
        se.race_bango = ra.race_bango
    WHERE se.ketto_toroku_bango = %s
      AND (se.kaisai_nen || se.kaisai_tsukihi) < %s
      AND se.kakutei_chakujun IS NOT NULL
      AND se.kakutei_chakujun != ''
      AND se.keibajo_code != '83'  -- ばんえい競馬除外
    ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
    LIMIT 3
    """
    
    cursor.execute(query, (ketto_toroku_bango, current_date))
    results = cursor.fetchall()
    cursor.close()
    
    return results


def calculate_nar_si_for_race(conn, kaisai_nen, kaisai_tsukihi, keibajo_code, 
                                race_bango, umaban):
    """
    特定のレースの特定の馬のNAR-SIを計算
    
    Args:
        conn: データベース接続
        kaisai_nen: 開催年
        kaisai_tsukihi: 開催月日
        keibajo_code: 競馬場コード
        race_bango: レース番号
        umaban: 馬番
    
    Returns:
        float: NAR-SI値（計算できない場合はNone）
    """
    # Ver.2.1-B（バランス版）で全レースを予測して該当馬のNAR-SIを取得
    from core.nar_si_calculator_v2_1_b import predict_race_with_nar_si_v2_1_b
    
    try:
        # レース全体を予測
        predictions = predict_race_with_nar_si_v2_1_b(
            conn, kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango
        )
        
        if not predictions:
            return None
        
        # 該当する馬番のNAR-SIを取得
        for pred in predictions:
            if pred.get('umaban') == umaban:
                return pred.get('final_nar_si')
        
        return None
    except Exception as e:
        print(f"NAR-SI計算エラー: {e}")
        return None


def get_previous_3_races_with_nar_si_fast(conn, ketto_toroku_bango, current_kaisai_nen, 
                                           current_kaisai_tsukihi):
    """
    過去3走のデータとNAR-SIを取得（高速版：テーブルから読み取り）
    
    Args:
        conn: データベース接続
        ketto_toroku_bango: 血統登録番号
        current_kaisai_nen: 今回の開催年
        current_kaisai_tsukihi: 今回の開催月日
    
    Returns:
        list: 過去3走のデータ（NAR-SI付き）
    """
    # 過去3走のレースデータを取得
    past_races = get_previous_3_races(conn, ketto_toroku_bango, 
                                      current_kaisai_nen, current_kaisai_tsukihi)
    
    if not past_races:
        return []
    
    # 各過去走に対してNAR-SIをテーブルから読み取り（高速）
    results = []
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    for race in past_races:
        kaisai_date = race['kaisai_nen'] + race['kaisai_tsukihi']
        
        # nar_si_race_results テーブルから読み取り
        try:
            cursor.execute("""
                SELECT nar_si FROM nar_si_race_results
                WHERE kaisai_date = %s 
                  AND keibajo_code = %s 
                  AND race_bango = %s 
                  AND umaban = %s
            """, (kaisai_date, race['keibajo_code'], race['race_bango'], race['umaban']))
            
            result = cursor.fetchone()
            nar_si_value = result['nar_si'] if result else 50.0
        except:
            nar_si_value = 50.0
        
        # 馬体重の安全な変換（空白や空文字列を処理）
        try:
            bataiju_value = int(race['bataiju'].strip()) if race['bataiju'] and str(race['bataiju']).strip() else 0
        except (ValueError, AttributeError):
            bataiju_value = 0
        
        results.append({
            'kaisai_date': kaisai_date,
            'keibajo_code': race['keibajo_code'],
            'kyori': int(race['kyori']) if race['kyori'] else 0,
            'track_code': race['track_code'],
            'babajotai_code': race['babajotai_code'],
            'kakutei_chakujun': int(race['kakutei_chakujun']) if race['kakutei_chakujun'] else 99,
            'nar_si': nar_si_value,
            'bataiju': bataiju_value,
            'kohan_3f': float(race['kohan_3f']) / 10.0 if race['kohan_3f'] and race['kohan_3f'] != '000' else 0.0,
            'soha_time': float(race['soha_time']) if race['soha_time'] else 0.0,
            'hasso_jikoku': race['hasso_jikoku'],
        })
    
    cursor.close()
    return results


def get_previous_3_races_with_nar_si(conn, ketto_toroku_bango, current_kaisai_nen, 
                                      current_kaisai_tsukihi):
    """
    過去3走のデータとNAR-SIを取得
    
    Args:
        conn: データベース接続
        ketto_toroku_bango: 血統登録番号
        current_kaisai_nen: 今回の開催年
        current_kaisai_tsukihi: 今回の開催月日
    
    Returns:
        list: 過去3走のデータ（NAR-SI付き）
        各要素は以下の辞書:
        {
            'kaisai_date': YYYYMMDD形式の日付,
            'keibajo_code': 競馬場コード,
            'kyori': 距離,
            'track_code': トラックコード,
            'babajotai_code': 馬場状態コード,
            'kakutei_chakujun': 確定着順,
            'nar_si': NAR-SI値,
            'bataiju': 馬体重,
            'kohan_3f': 後半3F,
            'hasso_jikoku': 発走時刻,
        }
    """
    # 過去3走のレースデータを取得
    past_races = get_previous_3_races(conn, ketto_toroku_bango, 
                                      current_kaisai_nen, current_kaisai_tsukihi)
    
    if not past_races:
        return []
    
    # 各過去走に対してNAR-SIを計算
    results = []
    for race in past_races:
        # NAR-SI を正しく計算
        nar_si_value = calculate_nar_si_for_race(
            conn,
            race['kaisai_nen'],
            race['kaisai_tsukihi'],
            race['keibajo_code'],
            race['race_bango'],
            race['umaban']
        )
        
        results.append({
            'kaisai_date': race['kaisai_nen'] + race['kaisai_tsukihi'],
            'keibajo_code': race['keibajo_code'],
            'kyori': int(race['kyori']) if race['kyori'] else 0,
            'track_code': race['track_code'],
            'babajotai_code': race['babajotai_code'],
            'kakutei_chakujun': int(race['kakutei_chakujun']) if race['kakutei_chakujun'] else 99,
            'nar_si': nar_si_value if nar_si_value is not None else 50.0,
            'bataiju': int(race['bataiju']) if race['bataiju'] else 0,
            'kohan_3f': float(race['kohan_3f']) / 10.0 if race['kohan_3f'] and race['kohan_3f'] != '000' else 0.0,
            'soha_time': float(race['soha_time']) if race['soha_time'] else 0.0,
            'hasso_jikoku': race['hasso_jikoku'],
        })
    
    return results


def test_get_previous_3_races():
    """
    過去3走データ取得のテスト
    """
    conn = get_db_connection()
    if not conn:
        print("❌ データベース接続失敗")
        return
    
    print("✅ データベース接続成功")
    print()
    
    # テスト用の馬（2024年12月31日の高知R01：ナミノハナ）
    test_ketto = '2016106186'  # 過去180走のデータを持つ実在馬
    test_kaisai_yen = '2024'
    test_kaisai_tsukihi = '1231'
    
    print(f"テスト対象: 血統登録番号 {test_ketto}")
    print(f"基準日: {test_kaisai_yen}年{test_kaisai_tsukihi[:2]}月{test_kaisai_tsukihi[2:]}日")
    print()
    
    # 過去3走を取得
    past_races = get_previous_3_races_with_nar_si(
        conn, test_ketto, test_kaisai_yen, test_kaisai_tsukihi
    )
    
    print(f"過去3走データ: {len(past_races)}件")
    print()
    
    for i, race in enumerate(past_races, 1):
        print(f"[{i}走前]")
        print(f"  日付: {race['kaisai_date']}")
        print(f"  競馬場: KB{race['keibajo_code']}")
        print(f"  距離: {race['kyori']}m")
        print(f"  馬場: {race['babajotai_code']}")
        print(f"  着順: {race['kakutei_chakujun']}着")
        print(f"  NAR-SI: {race['nar_si']:.2f}")
        print(f"  馬体重: {race['bataiju']}kg")
        print(f"  後半3F: {race['kohan_3f']:.1f}秒")
        print()
    
    conn.close()


if __name__ == '__main__':
    test_get_previous_3_races()
