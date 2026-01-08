#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
競馬場コードと距離を確認するスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def diagnose_keibajo_kyori():
    """競馬場コードと距離を確認"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 競馬場コードと距離を確認します")
    print("=" * 80)
    
    # nvd_ra の競馬場コード一覧
    cur.execute("""
    SELECT keibajo_code, COUNT(*) as cnt
    FROM nvd_ra
    GROUP BY keibajo_code
    ORDER BY cnt DESC
    """)
    
    print("\n📊 nvd_ra の競馬場コード一覧:")
    print("-" * 80)
    print(f"{'競馬場コード':<15} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<15} {row[1]:<10}")
    
    # 競馬場コード '42' の距離一覧
    cur.execute("""
    SELECT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
    GROUP BY kyori
    ORDER BY cnt DESC
    """)
    
    print("\n📊 競馬場コード '42' の距離一覧:")
    print("-" * 80)
    print(f"{'距離':<15} {'件数':<10}")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<10}")
    
    # nvd_se の競馬場コード一覧
    cur.execute("""
    SELECT keibajo_code, COUNT(*) as cnt
    FROM nvd_se
    GROUP BY keibajo_code
    ORDER BY cnt DESC
    """)
    
    print("\n📊 nvd_se の競馬場コード一覧:")
    print("-" * 80)
    print(f"{'競馬場コード':<15} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<15} {row[1]:<10}")
    
    # JOIN テスト（競馬場コード '42'）
    cur.execute("""
    SELECT COUNT(*)
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.keibajo_code = se.keibajo_code AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.race_bango = se.race_bango
    WHERE ra.keibajo_code = '42'
    """)
    
    join_count = cur.fetchone()[0]
    print(f"\n📊 JOIN後のレコード数（競馬場コード '42'）: {join_count:,}")
    
    # JOIN テスト（すべての競馬場コード）
    cur.execute("""
    SELECT ra.keibajo_code, COUNT(*) as cnt
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.keibajo_code = se.keibajo_code AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.race_bango = se.race_bango
    GROUP BY ra.keibajo_code
    ORDER BY cnt DESC
    """)
    
    print("\n📊 JOIN後のレコード数（競馬場コード別）:")
    print("-" * 80)
    print(f"{'競馬場コード':<15} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<15} {row[1]:<10}")
    
    print("\n" + "=" * 80)
    print("✅ 診断完了")
    print("=" * 80)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    diagnose_keibajo_kyori()
