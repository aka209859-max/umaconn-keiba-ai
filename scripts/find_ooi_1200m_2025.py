#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2025年の大井1200mデータを探すスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def find_ooi_1200m_2025():
    """2025年の大井1200mデータを探す"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 2025年の大井1200mデータを探します")
    print("=" * 80)
    
    # 2025年の大井の全距離
    cur.execute("""
    SELECT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
        AND kaisai_nen = '2025'
    GROUP BY kyori
    ORDER BY cnt DESC
    """)
    
    print("\n📊 2025年の大井の全距離:")
    print("-" * 80)
    print(f"{'距離':<10} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10}")
    
    # 2024年の大井の全距離
    cur.execute("""
    SELECT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
        AND kaisai_nen = '2024'
    GROUP BY kyori
    ORDER BY cnt DESC
    """)
    
    print("\n📊 2024年の大井の全距離:")
    print("-" * 80)
    print(f"{'距離':<10} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10}")
    
    # 2023年の大井の全距離
    cur.execute("""
    SELECT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '42'
        AND kaisai_nen = '2023'
    GROUP BY kyori
    ORDER BY cnt DESC
    """)
    
    print("\n📊 2023年の大井の全距離:")
    print("-" * 80)
    print(f"{'距離':<10} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10}")
    
    # 全年度の1200mデータ
    cur.execute("""
    SELECT keibajo_code, kaisai_nen, COUNT(*) as cnt
    FROM nvd_ra
    WHERE kyori = '1200'
    GROUP BY keibajo_code, kaisai_nen
    ORDER BY kaisai_nen DESC, keibajo_code
    LIMIT 20
    """)
    
    print("\n📊 全年度の1200mデータ（TOP 20）:")
    print("-" * 80)
    print(f"{'競馬場コード':<15} {'開催年':<10} {'件数':<10}")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<10} {row[2]:<10}")
    
    print("\n" + "=" * 80)
    print("✅ 確認完了")
    print("=" * 80)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    find_ooi_1200m_2025()
