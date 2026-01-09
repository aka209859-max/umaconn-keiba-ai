#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
実データから競馬場別・距離別の基準タイムを計算するスクリプト

目的: 推定値ではなく、実際のレースデータから基準タイムを算出
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection

def calculate_base_times_from_real_data():
    """
    実データから競馬場別・距離別の基準タイムを計算
    
    計算方法:
    1. 各競馬場・距離で、クラス基準（C2またはC）のレースを抽出
    2. 前半3F・後半3Fの平均タイムを計算
    3. 中央値（median）を採用して外れ値の影響を除外
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # 南関東4場のC2クラス基準タイム計算
    minami_kanto = ['42', '43', '44', '45']
    
    print("="*80)
    print("実データから基準タイムを計算中...")
    print("="*80)
    print()
    
    results = {}
    
    for keibajo_code in ['30','35','36','42','43','44','45','46','47','48','49','50','51']:
        print(f"\n競馬場コード: {keibajo_code}")
        print("-"*80)
        
        # 距離ごとに計算
        cur.execute("""
        SELECT DISTINCT kyori 
        FROM nvd_ra 
        WHERE keibajo_code = %s 
        ORDER BY kyori
        """, (keibajo_code,))
        
        kyori_list = [row[0] for row in cur.fetchall()]
        results[keibajo_code] = {}
        
        for kyori in kyori_list:
            # 前半3F・後半3Fの中央値を計算
            # 注意: zenhan_3fは存在しないため、soha_time - kohan_3f で計算
            cur.execute("""
            WITH valid_races AS (
                SELECT 
                    CAST(se.soha_time AS NUMERIC) / 10.0 - CAST(se.kohan_3f AS NUMERIC) / 10.0 as zenhan_3f,
                    CAST(se.kohan_3f AS NUMERIC) / 10.0 as kohan_3f
                FROM nvd_ra ra
                JOIN nvd_se se ON 
                    ra.kaisai_nen = se.kaisai_nen AND
                    ra.kaisai_tsukihi = se.kaisai_tsukihi AND
                    ra.keibajo_code = se.keibajo_code AND
                    ra.race_bango = se.race_bango
                WHERE ra.keibajo_code = %s
                    AND ra.kyori = %s
                    AND se.soha_time IS NOT NULL
                    AND se.soha_time != ''
                    AND se.soha_time ~ '^[0-9]+$'
                    AND CAST(se.soha_time AS NUMERIC) > 0
                    AND se.kohan_3f IS NOT NULL
                    AND se.kohan_3f != ''
                    AND se.kohan_3f ~ '^[0-9]+$'
                    AND CAST(se.kohan_3f AS NUMERIC) > 0
                    AND se.kakutei_chakujun IS NOT NULL
                    AND se.kakutei_chakujun != ''
                    AND se.kakutei_chakujun ~ '^[0-9]+$'
            )
            SELECT 
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY zenhan_3f) as median_zenhan,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY kohan_3f) as median_kohan,
                COUNT(*) as race_count
            FROM valid_races
            """, (keibajo_code, kyori))
            
            row = cur.fetchone()
            if row and row[2] > 0:
                median_zenhan = float(row[0])
                median_kohan = float(row[1])
                race_count = row[2]
                
                results[keibajo_code][kyori] = {
                    'zenhan_3f': round(median_zenhan, 1),
                    'kohan_3f': round(median_kohan, 1),
                    'race_count': race_count
                }
                
                print(f"  距離 {kyori:4d}m: 前半3F={median_zenhan:5.1f}秒, 後半3F={median_kohan:5.1f}秒 (レース数:{race_count:5d})")
    
    conn.close()
    
    # Python辞書形式で出力
    print("\n" + "="*80)
    print("BASE_TIMES = {")
    for keibajo_code, kyori_data in sorted(results.items()):
        print(f"    '{keibajo_code}': {{  # 競馬場コード {keibajo_code}")
        for kyori, times in sorted(kyori_data.items()):
            print(f"        {kyori}: {{'zenhan_3f': {times['zenhan_3f']}, 'kohan_3f': {times['kohan_3f']}}},  # レース数: {times['race_count']}")
        print("    },")
    print("}")
    print("="*80)

if __name__ == '__main__':
    calculate_base_times_from_real_data()
