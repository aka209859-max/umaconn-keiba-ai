#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
soha_time のフォーマットを検証するスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def verify_soha_time_format():
    """soha_timeのフォーマットを検証"""
    
    print("=" * 80)
    print("soha_time フォーマット検証")
    print("=" * 80)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 大井（'44'）の1200mデータを取得
    cur.execute("""
    SELECT 
        se.soha_time,
        se.kohan_3f,
        se.kakutei_chakujun,
        ra.kaisai_nen,
        ra.kaisai_tsukihi
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.keibajo_code = se.keibajo_code AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.race_bango = se.race_bango
    WHERE ra.keibajo_code = '44'
        AND CAST(ra.kyori AS INTEGER) = 1200
        AND (ra.babajotai_code_dirt = '1' OR ra.babajotai_code_shiba = '1')
        AND se.soha_time IS NOT NULL
        AND se.soha_time != ''
        AND se.soha_time ~ '^[0-9.]+$'
        AND se.kohan_3f IS NOT NULL
        AND se.kohan_3f != ''
        AND se.kohan_3f ~ '^[0-9.]+$'
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != ''
        AND se.kakutei_chakujun ~ '^[0-9]+$'
        AND CAST(se.kakutei_chakujun AS INTEGER) BETWEEN 1 AND 5
    LIMIT 20
    """)
    
    rows = cur.fetchall()
    
    print("\n大井（'44'）1200m サンプルデータ（20件）")
    print("-" * 80)
    print(f"{'No':<4} {'soha_time':<10} {'kohan_3f':<10} {'着順':<4} {'前半3F(パターン1)':<20} {'前半3F(パターン2)':<20} {'開催年月日'}")
    print("-" * 80)
    
    for i, row in enumerate(rows, 1):
        soha_time_raw = row[0]
        kohan_3f_raw = row[1]
        chakujun = row[2]
        kaisai_nen = row[3]
        kaisai_tsukihi = row[4]
        
        # パターン1: soha_time は0.1秒単位（1134 → 113.4秒）
        soha_time_p1 = float(soha_time_raw) / 10.0
        kohan_3f_p1 = float(kohan_3f_raw) / 10.0
        zenhan_3f_p1 = soha_time_p1 - kohan_3f_p1
        
        # パターン2: soha_time は「分+0.1秒」形式（1134 → 1分13.4秒 = 73.4秒）
        soha_time_int = int(float(soha_time_raw))
        minutes = soha_time_int // 1000
        remainder = soha_time_int % 1000
        soha_time_p2 = minutes * 60 + remainder / 10.0
        kohan_3f_p2 = float(kohan_3f_raw) / 10.0
        zenhan_3f_p2 = soha_time_p2 - kohan_3f_p2
        
        print(f"{i:<4} {soha_time_raw:<10} {kohan_3f_raw:<10} {chakujun:<4} {zenhan_3f_p1:.1f}秒 ({soha_time_p1:.1f}-{kohan_3f_p1:.1f})<10 {zenhan_3f_p2:.1f}秒 ({soha_time_p2:.1f}-{kohan_3f_p2:.1f})<10 {kaisai_nen}-{kaisai_tsukihi}")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("判定基準:")
    print("- 1200mの前半3Fは通常 35-38秒程度")
    print("- 後半3Fは通常 37-40秒程度")
    print("- 走破タイムは通常 73-78秒程度")
    print("\n✅ パターン1（0.1秒単位）で前半3Fが35-38秒なら → パターン1が正解")
    print("✅ パターン2（分+0.1秒形式）で前半3Fが35-38秒なら → パターン2が正解")
    print("=" * 80)

if __name__ == "__main__":
    verify_soha_time_format()
