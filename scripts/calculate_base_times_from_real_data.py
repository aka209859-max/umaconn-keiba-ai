#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
実データから競馬場別・距離別の基準タイムを計算するスクリプト

目的: 推定値ではなく、実際のレースデータから基準タイムを算出

前半3Fの計算方法:
- 1200m以下: 走破タイム - 後半3F（確定値）
- 1201m以上: Ten3FEstimator を使用（推定値）
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection
from core.ten_3f_estimator import Ten3FEstimator

# Ten3FEstimator のインスタンスを作成
estimator = Ten3FEstimator()

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
            # 1200m以下: soha_time - kohan_3f（確定値）
            # 1201m以上: Ten3FEstimator を使用（推定値）
            
            if kyori <= 1200:
                # 1200m以下: 走破タイム - 後半3F
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
            else:
                # 1201m以上: Ten3FEstimator を使用
                # まず実データを取得
                cur.execute("""
                SELECT 
                    CAST(se.soha_time AS NUMERIC) / 10.0 as soha_time,
                    CAST(se.kohan_3f AS NUMERIC) / 10.0 as kohan_3f,
                    CAST(se.corner_1 AS INTEGER) as corner_1,
                    CAST(se.corner_2 AS INTEGER) as corner_2,
                    CAST(se.corner_3 AS INTEGER) as corner_3,
                    CAST(se.corner_4 AS INTEGER) as corner_4
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
                LIMIT 10000
                """, (keibajo_code, kyori))
                
                rows = cur.fetchall()
                
                if len(rows) > 0:
                    # Ten3FEstimator で前半3Fを推定
                    zenhan_3f_list = []
                    kohan_3f_list = []
                    
                    for row in rows:
                        soha_time = row[0]
                        kohan_3f = row[1]
                        corner_1 = row[2] if row[2] else 0
                        corner_2 = row[3] if row[3] else 0
                        corner_3 = row[4] if row[4] else 0
                        corner_4 = row[5] if row[5] else 0
                        
                        # Ten3FEstimator で推定
                        zenhan_3f = estimator.estimate(
                            time_seconds=soha_time,
                            kohan_3f_seconds=kohan_3f,
                            kyori=kyori,
                            corner_1=corner_1,
                            corner_2=corner_2,
                            corner_3=corner_3,
                            corner_4=corner_4
                        )
                        
                        zenhan_3f_list.append(zenhan_3f)
                        kohan_3f_list.append(kohan_3f)
                    
                    # 中央値を計算
                    import numpy as np
                    median_zenhan = float(np.median(zenhan_3f_list))
                    median_kohan = float(np.median(kohan_3f_list))
                    race_count = len(rows)
                    
                    row = (median_zenhan, median_kohan, race_count)
                else:
                    row = None
                
                # SQL実行結果を上書き（統一的な処理のため）
                if row:
                    pass  # rowはすでに設定済み
                else:
                    continue
            
            row = cur.fetchone() if kyori <= 1200 else row
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
