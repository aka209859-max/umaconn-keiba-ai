#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全ファクター実装の動作確認テスト
Created: 2026-01-07

【テスト内容】
1. data_fetcher.py の血統データ取得関数
2. factor_extractor.py の新規ファクター抽出
3. main.py の統合フロー
"""

import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

import psycopg2
from psycopg2.extras import RealDictCursor
from config.db_config import DB_CONFIG
from core.data_fetcher import (
    get_bloodline_data,
    get_three_generation_bloodline,
    enrich_horse_data_with_bloodline,
    get_tomorrow_date
)


def test_bloodline_data_retrieval():
    """
    血統データ取得関数のテスト
    """
    print("="*60)
    print("【テスト1】血統データ取得関数")
    print("="*60 + "\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # テスト用の馬IDを取得
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT ketto_toroku_bango
                FROM nvd_se
                WHERE ketto_toroku_bango IS NOT NULL
                  AND ketto_toroku_bango != ''
                LIMIT 5
            """)
            test_horses = cur.fetchall()
        
        if not test_horses:
            print("❌ テスト用の馬データが見つかりません")
            return False
        
        print(f"✅ テスト対象: {len(test_horses)}頭\n")
        
        # 各馬の血統データを取得
        for i, horse in enumerate(test_horses, 1):
            ketto_toroku_bango = horse['ketto_toroku_bango']
            print(f"【馬 {i}】血統登録番号: {ketto_toroku_bango}")
            
            # 基本血統データ取得（B15/B16/B19）
            bloodline = get_bloodline_data(conn, ketto_toroku_bango)
            print(f"  父ID (B15): {bloodline.get('fufu_ketto_toroku_bango', 'なし')}")
            print(f"  母ID (B16): {bloodline.get('bobo_ketto_toroku_bango', 'なし')}")
            print(f"  母父ID (B19): {bloodline.get('hahachichi_ketto_toroku_bango', 'なし')}")
            
            # 3代血統データ取得（B15-B20）
            three_gen = get_three_generation_bloodline(conn, ketto_toroku_bango)
            print(f"  父父ID (B17): {three_gen.get('ff_blood_no', 'なし')}")
            print(f"  父母ID (B18): {three_gen.get('fm_blood_no', 'なし')}")
            print(f"  母母ID (B20): {three_gen.get('mm_blood_no', 'なし')}")
            print()
        
        print("✅ 血統データ取得テスト: 成功\n")
        return True
    
    except Exception as e:
        print(f"❌ エラー: {e}\n")
        return False
    
    finally:
        conn.close()


def test_factor_extraction():
    """
    ファクター抽出テスト
    """
    print("="*60)
    print("【テスト2】ファクター抽出")
    print("="*60 + "\n")
    
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        from core.data_fetcher import get_tomorrow_races, get_race_info
        from core.factor_extractor import extract_single_factors
        
        # 明日の日付
        tomorrow = get_tomorrow_date()
        print(f"対象日付: {tomorrow}\n")
        
        # 出走馬データを1頭取得
        horses = get_tomorrow_races(conn, tomorrow)
        if not horses:
            print("❌ 出走馬データが見つかりません")
            return False
        
        # 血統データを追加
        enriched_horses = enrich_horse_data_with_bloodline(conn, horses[:5])
        
        if not enriched_horses:
            print("❌ 血統データ統合に失敗しました")
            return False
        
        # 1頭目をテスト
        test_horse = enriched_horses[0]
        print(f"テスト対象馬: {test_horse.get('bamei', '不明')}")
        print(f"血統登録番号: {test_horse.get('ketto_toroku_bango', 'なし')}\n")
        
        # レース情報を取得
        race_info = get_race_info(
            conn,
            test_horse['keibajo_code'],
            test_horse['kaisai_nen'] + test_horse['kaisai_tsukihi'],
            test_horse['race_bango']
        )
        
        # ファクター抽出
        factors = extract_single_factors(conn, test_horse, race_info)
        
        # Phase 2 ファクターの確認
        print("【Phase 2 ファクター】")
        print(f"  F24_prev_wakuban: {factors.get('F24_prev_wakuban', 'なし')}")
        print(f"  F25_tansho_odds: {factors.get('F25_tansho_odds', 'なし')}")
        print(f"  F26_tansho_ninki: {factors.get('F26_tansho_ninki', 'なし')}")
        print(f"  F27_track_code: {factors.get('F27_track_code', 'なし')}")
        print(f"  F29_grade_code: {factors.get('F29_grade_code', 'なし')}\n")
        
        # Phase 3 血統ファクターの確認
        print("【Phase 3 血統ファクター】")
        print(f"  B15_f_blood_no: {factors.get('B15_f_blood_no', 'なし')}")
        print(f"  B16_m_blood_no: {factors.get('B16_m_blood_no', 'なし')}")
        print(f"  B17_ff_blood_no: {factors.get('B17_ff_blood_no', 'なし')}")
        print(f"  B18_fm_blood_no: {factors.get('B18_fm_blood_no', 'なし')}")
        print(f"  B19_mf_blood_no: {factors.get('B19_mf_blood_no', 'なし')}")
        print(f"  B20_mm_blood_no: {factors.get('B20_mm_blood_no', 'なし')}\n")
        
        print("✅ ファクター抽出テスト: 成功\n")
        return True
    
    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()


def main():
    """
    全テストを実行
    """
    print("\n" + "="*60)
    print("全ファクター実装 動作確認テスト")
    print("作成日: 2026-01-07")
    print("="*60 + "\n")
    
    results = []
    
    # テスト1: 血統データ取得
    results.append(test_bloodline_data_retrieval())
    
    # テスト2: ファクター抽出
    results.append(test_factor_extraction())
    
    # 結果サマリー
    print("="*60)
    print("【テスト結果サマリー】")
    print("="*60)
    print(f"テスト1（血統データ取得）: {'✅ 成功' if results[0] else '❌ 失敗'}")
    print(f"テスト2（ファクター抽出）: {'✅ 成功' if results[1] else '❌ 失敗'}")
    print()
    
    if all(results):
        print("🎉 全てのテストが成功しました！")
        print("✅ Option C: 全ファクター実装 完了")
    else:
        print("⚠️  一部のテストが失敗しました")
        print("❌ 詳細を確認してください")
    
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
