#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大井の全距離パターンを確認するスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def check_ooi_all_kyori():
    """大井の全距離パターンを確認"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 大井（'42'）の全距離パターンを確認します")
    print("=" * 80)
    
    # 大井の全距離パターン（重複なし）
    cur.execute("""
    SELECT DISTINCT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
    GROUP BY kyori
    ORDER BY kyori
    """)
    
    print("\n📊 大井（'42'）の全距離パターン:")
    print("-" * 80)
    print(f"{'kyori（生データ）':<20} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        kyori_raw = row[0] if row[0] else "NULL"
        cnt = row[1]
        print(f"{str(kyori_raw):<20} {cnt:<10}")
    
    # '1200' を含む距離を検索
    cur.execute("""
    SELECT DISTINCT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
        AND kyori LIKE '%1200%'
    GROUP BY kyori
    """)
    
    print("\n📊 '1200' を含む距離:")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<20} {row[1]:<10}")
    
    # '12' を含む距離を検索
    cur.execute("""
    SELECT DISTINCT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
        AND kyori LIKE '%12%'
    GROUP BY kyori
    ORDER BY kyori
    """)
    
    print("\n📊 '12' を含む距離:")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<20} {row[1]:<10}")
    
    print("\n" + "=" * 80)
    print("✅ 確認完了")
    print("=" * 80)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_ooi_all_kyori()
