#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大井の距離データを詳細確認するスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def check_ooi_kyori_detail():
    """大井の距離データを詳細確認"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 大井（'42'）の距離データを詳細確認します")
    print("=" * 80)
    
    # 全距離パターンとサンプルデータ
    cur.execute("""
    SELECT DISTINCT 
        kyori,
        LENGTH(kyori) as len,
        COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
    GROUP BY kyori, LENGTH(kyori)
    ORDER BY cnt DESC
    """)
    
    print("\n📊 距離データの詳細:")
    print("-" * 80)
    print(f"{'kyori（生データ）':<20} {'文字数':<10} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        kyori_raw = row[0] if row[0] else "NULL"
        length = row[1]
        cnt = row[2]
        print(f"{str(kyori_raw):<20} {length:<10} {cnt:<10}")
    
    # kyori='1200' のデータを検索（完全一致）
    cur.execute("""
    SELECT COUNT(*) 
    FROM nvd_ra
    WHERE keibajo_code = '42' AND kyori = '1200'
    """)
    count_1200 = cur.fetchone()[0]
    print(f"\n📊 kyori='1200' のデータ: {count_1200}件")
    
    # kyori='12' のデータを検索（完全一致）
    cur.execute("""
    SELECT COUNT(*) 
    FROM nvd_ra
    WHERE keibajo_code = '42' AND kyori = '12'
    """)
    count_12 = cur.fetchone()[0]
    print(f"📊 kyori='12' のデータ: {count_12}件")
    
    # サンプルデータを取得（5件）
    cur.execute("""
    SELECT 
        kaisai_nen,
        kaisai_tsukihi,
        race_bango,
        kyori,
        LENGTH(kyori) as len
    FROM nvd_ra
    WHERE keibajo_code = '42'
    ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
    LIMIT 10
    """)
    
    print("\n📊 サンプルデータ（最新10件）:")
    print("-" * 80)
    print(f"{'開催年':<10} {'開催月日':<10} {'R':<5} {'距離':<10} {'文字数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10} {row[2]:<5} {row[3]:<10} {row[4]:<10}")
    
    # nvd_se との JOIN でデータを確認
    cur.execute("""
    SELECT 
        ra.kyori,
        se.soha_time,
        se.kohan_3f,
        ra.kaisai_nen,
        ra.kaisai_tsukihi
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.keibajo_code = se.keibajo_code AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.race_bango = se.race_bango
    WHERE ra.keibajo_code = '42'
        AND ra.kyori IN ('1200', '12', '1300', '13', '0800', '08', '1400', '14')
    LIMIT 5
    """)
    
    print("\n📊 JOIN後のサンプルデータ:")
    print("-" * 80)
    print(f"{'距離':<10} {'soha_time':<15} {'kohan_3f':<15} {'開催年':<10} {'開催月日':<10}")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<10} {str(row[1]):<15} {str(row[2]):<15} {row[3]:<10} {row[4]:<10}")
    
    print("\n" + "=" * 80)
    print("✅ 確認完了")
    print("=" * 80)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_ooi_kyori_detail()
