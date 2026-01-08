#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生データを確認するスクリプト（簡易版）
フィルタなしでデータを確認
"""

import sys
sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection

def check_raw_data_simple():
    """生データを確認（簡易版）"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 120)
    print("📊 生データを確認します（大井 1200m, フィルタなし）")
    print("=" * 120)
    
    # 大井 1200m のサンプルデータを取得（フィルタ最小限）
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
    WHERE ra.keibajo_code = '42'
        AND CAST(ra.kyori AS INTEGER) = 1200
    ORDER BY ra.kaisai_nen DESC, ra.kaisai_tsukihi DESC
    LIMIT 20
    """)
    
    rows = cur.fetchall()
    
    print(f"\n📊 生データサンプル（{len(rows)}件）:")
    print("-" * 120)
    print(f"{'No':<4} {'soha_time':<12} {'kohan_3f':<12} {'着順':<10} {'馬場(ダ)':<10} {'馬場(芝)':<10} "
          f"{'前半3F(v1)':<20} {'前半3F(v2)':<20}")
    print("-" * 120)
    
    for i, row in enumerate(rows, 1):
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
    
    # 馬場状態コードの集計
    cur.execute("""
    SELECT 
        ra.babajotai_code_dirt,
        ra.babajotai_code_shiba,
        COUNT(*) as cnt
    FROM nvd_ra ra
    WHERE ra.keibajo_code = '42'
        AND CAST(ra.kyori AS INTEGER) = 1200
    GROUP BY ra.babajotai_code_dirt, ra.babajotai_code_shiba
    ORDER BY cnt DESC
    LIMIT 10
    """)
    
    print("\n📊 馬場状態コードの集計（大井 1200m, TOP 10）:")
    print("-" * 80)
    print(f"{'馬場(ダート)':<15} {'馬場(芝)':<15} {'件数':<10}")
    print("-" * 80)
    for row in cur.fetchall():
        print(f"{str(row[0]):<15} {str(row[1]):<15} {row[2]:<10}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    check_raw_data_simple()
