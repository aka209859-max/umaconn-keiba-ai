#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1200m が存在する競馬場を探すスクリプト
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def find_1200m_keibajo():
    """1200m が存在する競馬場を探す"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("📊 1200m のデータが存在する競馬場を探します")
    print("=" * 80)
    
    # 1200m が存在する競馬場
    cur.execute("""
    SELECT keibajo_code, COUNT(*) as cnt
    FROM nvd_ra
    WHERE kyori = '1200'
    GROUP BY keibajo_code
    ORDER BY cnt DESC
    """)
    
    print("\n📊 1200m のデータが存在する競馬場:")
    print("-" * 80)
    print(f"{'競馬場コード':<15} {'件数':<10}")
    print("-" * 80)
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  データなし")
    else:
        for row in rows:
            print(f"{row[0]:<15} {row[1]:<10}")
    
    # JOIN後の1200mデータを確認（サンプル：競馬場コード '50'）
    if len(rows) > 0:
        sample_keibajo = rows[0][0]
        
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
        WHERE ra.keibajo_code = %s
            AND ra.kyori = '1200'
        ORDER BY ra.kaisai_nen DESC, ra.kaisai_tsukihi DESC
        LIMIT 20
        """, (sample_keibajo,))
        
        rows2 = cur.fetchall()
        
        print(f"\n📊 サンプルデータ（競馬場コード '{sample_keibajo}', 1200m, {len(rows2)}件）:")
        print("-" * 120)
        print(f"{'No':<4} {'soha_time':<12} {'kohan_3f':<12} {'着順':<10} {'馬場(ダ)':<10} {'馬場(芝)':<10} "
              f"{'前半3F(v1)':<20} {'前半3F(v2)':<20}")
        print("-" * 120)
        
        for i, row in enumerate(rows2, 1):
            soha_time_raw = row[0] if row[0] else "NULL"
            kohan_3f_raw = row[1] if row[1] else "NULL"
            chakujun = row[2] if row[2] else "NULL"
            kaisai_nen = row[3]
            kaisai_tsukihi = row[4]
            baba_dirt = row[5] if row[5] else "NULL"
            baba_shiba = row[6] if row[6] else "NULL"
            
            # 数値変換可能な場合のみ計算
            try:
                soha_time_float = float(soha_time_raw)
                kohan_3f_float = float(kohan_3f_raw)
                
                # パターン1: 0.1秒単位の場合
                soha_time_v1 = soha_time_float / 10.0
                kohan_3f_v1 = kohan_3f_float / 10.0
                zenhan_3f_v1 = soha_time_v1 - kohan_3f_v1
                
                # パターン2: 秒単位の場合
                zenhan_3f_v2 = soha_time_float - kohan_3f_float
                
                v1_str = f"{zenhan_3f_v1:>5.1f}秒 ({soha_time_v1:.1f}-{kohan_3f_v1:.1f})"
                v2_str = f"{zenhan_3f_v2:>5.1f}秒 ({soha_time_float:.1f}-{kohan_3f_float:.1f})"
            except:
                v1_str = "計算不可"
                v2_str = "計算不可"
            
            print(f"{i:<4} {str(soha_time_raw):<12} {str(kohan_3f_raw):<12} {str(chakujun):<10} "
                  f"{baba_dirt:<10} {baba_shiba:<10} {v1_str:<20} {v2_str:<20}")
        
        print("\n" + "=" * 120)
        print("📝 判定基準:")
        print("-" * 120)
        print("  v1（両方とも 0.1秒単位）: soha_time / 10.0 - kohan_3f / 10.0")
        print("  v2（両方とも秒単位）:       soha_time - kohan_3f")
        print()
        print("  ✅ 1200m の前半3F は通常 35-38秒程度")
        print("  ✅ 後半3F は通常 37-40秒程度")
        print("  ✅ 走破タイムは通常 73-78秒程度")
        print()
        print("  v1 が 35-38秒の範囲なら → 両方とも 0.1秒単位で格納されている")
        print("  v2 が 35-38秒の範囲なら → 両方とも秒単位で格納されている")
        print("=" * 120)
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    find_1200m_keibajo()
