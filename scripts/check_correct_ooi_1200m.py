#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正しい競馬場コードで大井の1200mデータを確認
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def check_correct_ooi_1200m():
    """正しい競馬場コード（'44'）で大井の1200mデータを確認"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 正しい競馬場コードで大井（'44'）の1200mデータを確認します")
    print("=" * 80)
    
    # 大井（'44'）の全距離
    cur.execute("""
    SELECT kyori, COUNT(*) as cnt
    FROM nvd_ra
    WHERE keibajo_code = '44'
    GROUP BY kyori
    ORDER BY cnt DESC
    """)
    
    print("\n📊 大井（'44'）の全距離:")
    print("-" * 80)
    print(f"{'距離':<10} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{row[0]:<10} {row[1]:<10}")
    
    # 1200mのデータ
    cur.execute("""
    SELECT COUNT(*) 
    FROM nvd_ra
    WHERE keibajo_code = '44' AND kyori = '1200'
    """)
    count_1200 = cur.fetchone()[0]
    print(f"\n📊 大井（'44'）の1200mデータ: {count_1200}件")
    
    # 1200mのサンプルデータ
    if count_1200 > 0:
        cur.execute("""
        SELECT 
            se.soha_time,
            se.kohan_3f,
            se.kakutei_chakujun,
            ra.kaisai_nen,
            ra.kaisai_tsukihi,
            ra.babajotai_code_dirt,
            ra.babajotai_code_shiba
        FROM nvd_ra ra
        JOIN nvd_se se ON 
            ra.kaisai_nen = se.kaisai_nen AND
            ra.keibajo_code = se.keibajo_code AND
            ra.kaisai_tsukihi = se.kaisai_tsukihi AND
            ra.race_bango = se.race_bango
        WHERE ra.keibajo_code = '44'
            AND ra.kyori = '1200'
        ORDER BY ra.kaisai_nen DESC, ra.kaisai_tsukihi DESC
        LIMIT 10
        """)
        
        print("\n📊 大井（'44'）1200m サンプルデータ（10件）:")
        print("-" * 120)
        print(f"{'soha_time':<12} {'kohan_3f':<12} {'着順':<10} {'馬場(ダ)':<10} {'馬場(芝)':<10} {'開催年':<10} {'開催月日':<10}")
        print("-" * 120)
        
        for row in cur.fetchall():
            soha_time = row[0]
            kohan_3f = row[1]
            chakujun = row[2]
            kaisai_nen = row[3]
            kaisai_tsukihi = row[4]
            baba_dirt = row[5] if row[5] else "NULL"
            baba_shiba = row[6] if row[6] else "NULL"
            
            print(f"{str(soha_time):<12} {str(kohan_3f):<12} {str(chakujun):<10} "
                  f"{baba_dirt:<10} {baba_shiba:<10} {kaisai_nen:<10} {kaisai_tsukihi:<10}")
    
    # 全競馬場コードを正しく確認
    print("\n" + "=" * 80)
    print("📊 正しい競馬場コード一覧（データベース）")
    print("=" * 80)
    
    cur.execute("""
    SELECT keibajo_code, COUNT(*) as cnt
    FROM nvd_ra
    GROUP BY keibajo_code
    ORDER BY keibajo_code
    """)
    
    print(f"\n{'コード':<10} {'件数':<10} {'正しい競馬場名':<20}")
    print("-" * 80)
    
    correct_names = {
        '30': '門別',
        '33': '帯広（ばんえい）',
        '35': '盛岡',
        '36': '水沢',
        '42': '浦和',
        '43': '船橋',
        '44': '大井',
        '45': '川崎',
        '46': '金沢',
        '47': '笠松',
        '48': '名古屋',
        '50': '園田',
        '51': '姫路',
        '54': '高知',
        '55': '佐賀'
    }
    
    for row in cur.fetchall():
        code = row[0]
        cnt = row[1]
        name = correct_names.get(code, '不明')
        print(f"{code:<10} {cnt:<10} {name:<20}")
    
    print("\n" + "=" * 80)
    print("✅ 確認完了")
    print("=" * 80)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_correct_ooi_1200m()
