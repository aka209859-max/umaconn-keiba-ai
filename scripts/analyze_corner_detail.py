#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
コーナー順位データ詳細分析スクリプト
================================================================================
corner_1 = '00' のデータを詳しく分析します。
================================================================================
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def analyze_corner_data():
    """コーナー順位データを詳細分析"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 コーナー順位データ詳細分析")
    print("="*80 + "\n")
    
    # corner_1 = '00' のサンプルデータを取得
    query = """
    SELECT 
        ra.kaisai_nen,
        ra.kaisai_tsukihi,
        ra.keibajo_code,
        ra.race_bango,
        ra.kyori,
        ra.track_code,
        se.umaban,
        se.corner_1,
        se.corner_2,
        se.corner_3,
        se.corner_4,
        se.kakutei_chakujun,
        ra.corner_tsuka_juni_1,
        ra.corner_tsuka_juni_2,
        ra.corner_tsuka_juni_3,
        ra.corner_tsuka_juni_4
    FROM nvd_se se
    JOIN nvd_ra ra ON 
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.keibajo_code = ra.keibajo_code AND
        se.race_bango = ra.race_bango
    WHERE ra.babajotai_code_dirt = '1'
        AND se.corner_1 = '00'
        AND CAST(ra.kyori AS INTEGER) >= 1400
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != ''
    LIMIT 10;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print("📋 corner_1 = '00' のサンプルデータ (1400m以上):\n")
    print(f"{'年月日':^12} | {'場':^4} | {'R':^3} | {'距離':^6} | {'馬番':^4} | {'着順':^4} | {'se.c1':^6} | {'se.c2':^6} | {'se.c3':^6} | {'se.c4':^6} | {'ra.c1':^20}")
    print("-" * 120)
    
    for row in results:
        year = row[0]
        date = row[1]
        keibajo = row[2]
        race = row[3]
        kyori = row[4]
        track = row[5]
        umaban = row[6]
        c1 = row[7]
        c2 = row[8]
        c3 = row[9]
        c4 = row[10]
        chakujun = row[11]
        ra_c1 = row[12]
        
        print(f"{year}{date} | {keibajo:^4} | {race:>3} | {kyori:>6} | {umaban:^4} | {chakujun:^4} | {c1:^6} | {c2:^6} | {c3:^6} | {c4:^6} | {ra_c1[:20]:<20}")
    
    # 統計: corner_1 = '00' だが ra.corner_tsuka_juni_1 にデータがある件数
    print("\n" + "="*80)
    print("📊 corner_1 = '00' だが ra.corner_tsuka_juni_1 にデータがある件数")
    print("="*80 + "\n")
    
    query2 = """
    SELECT 
        COUNT(*) as total,
        COUNT(CASE WHEN ra.corner_tsuka_juni_1 IS NOT NULL AND ra.corner_tsuka_juni_1 != '' AND ra.corner_tsuka_juni_1 != '00' THEN 1 END) as ra_has_data
    FROM nvd_se se
    JOIN nvd_ra ra ON 
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.keibajo_code = ra.keibajo_code AND
        se.race_bango = ra.race_bango
    WHERE ra.babajotai_code_dirt = '1'
        AND se.corner_1 = '00'
        AND CAST(ra.kyori AS INTEGER) >= 1400
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != '';
    """
    
    cursor.execute(query2)
    result = cursor.fetchone()
    
    total = result[0]
    ra_has_data = result[1]
    pct = 100.0 * ra_has_data / total if total > 0 else 0
    
    print(f"se.corner_1 = '00' の総数: {total:,}件")
    print(f"ra.corner_tsuka_juni_1 にデータがある: {ra_has_data:,}件 ({pct:.2f}%)")
    print(f"ra.corner_tsuka_juni_1 もない: {total - ra_has_data:,}件 ({100-pct:.2f}%)")
    
    # 結論
    print("\n" + "="*80)
    print("💡 結論:")
    print("="*80 + "\n")
    
    if pct > 50:
        print("✅ nvd_se.corner_1 = '00' でも、nvd_ra.corner_tsuka_juni_1 にはデータがあります！")
        print("   → collect_index_stats.py は nvd_ra.corner_tsuka_juni_1 から取得すべきです。")
    else:
        print("❌ nvd_ra.corner_tsuka_juni_1 にもデータがありません。")
        print("   → 本当にコーナー順位データが欠損しています。")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        analyze_corner_data()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
