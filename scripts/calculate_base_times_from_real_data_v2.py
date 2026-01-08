#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
実データから競馬場別・距離別の基準タイムを計算するスクリプト（修正版）

目的: 推定値ではなく、実際のレースデータから基準タイムを算出
修正: Ten3FEstimator を使用して前半3Fを推定
"""

import sys
import os
import numpy as np

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection
from core.ten_3f_estimator import Ten3FEstimator

def calculate_base_times_from_real_data():
    """
    実データから競馬場別・距離別の基準タイムを計算
    
    計算方法:
    1. 各競馬場・距離で、良馬場・上位5頭のレースを抽出
    2. Ten3FEstimator で前半3Fを推定（1200mは確定値）
    3. 前半3F・後半3Fの中央値を計算
    """
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Ten3FEstimator を初期化
    print("🔧 Ten3FEstimator を初期化中...")
    estimator = Ten3FEstimator()
    print("✅ Ten3FEstimator 初期化完了")
    print()
    
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
            # レースデータを取得（良馬場・上位5頭）
            cur.execute("""
            SELECT 
                se.soha_time,
                se.kohan_3f,
                se.corner_1,
                se.corner_2,
                ra.tosu,
                se.kakutei_chakujun
            FROM nvd_ra ra
            JOIN nvd_se se ON 
                ra.kaisai_nen = se.kaisai_nen AND
                ra.keibajo_code = se.keibajo_code AND
                ra.kaisai_nengappi = se.kaisai_nengappi AND
                ra.race_bango = se.race_bango
            WHERE ra.keibajo_code = %s
                AND ra.kyori = %s
                AND ra.baba_jotai = '良'
                AND se.soha_time > 0
                AND se.kohan_3f > 0
                AND se.kakutei_chakujun IS NOT NULL
                AND se.kakutei_chakujun != ''
                AND se.kakutei_chakujun ~ '^[0-9]+$'
                AND CAST(se.kakutei_chakujun AS INTEGER) BETWEEN 1 AND 5
            LIMIT 1000
            """, (keibajo_code, kyori))
            
            rows = cur.fetchall()
            
            if len(rows) < 10:
                print(f"  距離 {kyori:4d}m: ⚠️ データ不足（{len(rows)}件）スキップ")
                continue
            
            zenhan_3f_list = []
            kohan_3f_list = []
            
            for row in rows:
                soha_time = float(row[0])
                kohan_3f = float(row[1])
                corner_1 = int(row[2]) if row[2] and str(row[2]).isdigit() else 0
                corner_2 = int(row[3]) if row[3] and str(row[3]).isdigit() else 0
                tosu = int(row[4]) if row[4] else 12
                
                # 前半3Fを推定
                if kyori == 1200:
                    # 1200m: 確定値
                    zenhan_3f = soha_time - kohan_3f
                else:
                    # 1400m以上: Ten3FEstimator で推定
                    zenhan_3f = estimator.estimate(
                        time_seconds=soha_time,
                        kohan_3f_seconds=kohan_3f,
                        kyori=kyori,
                        corner_1=corner_1,
                        corner_2=corner_2,
                        field_size=tosu
                    )
                
                # 物理的限界値でクランプ
                if 33.0 <= zenhan_3f <= 45.0 and 33.0 <= kohan_3f <= 45.0:
                    zenhan_3f_list.append(zenhan_3f)
                    kohan_3f_list.append(kohan_3f)
            
            if len(zenhan_3f_list) >= 10:
                # 中央値を計算
                median_zenhan = np.median(zenhan_3f_list)
                median_kohan = np.median(kohan_3f_list)
                
                results[keibajo_code][kyori] = {
                    'zenhan_3f': round(median_zenhan, 1),
                    'kohan_3f': round(median_kohan, 1),
                    'race_count': len(zenhan_3f_list)
                }
                
                method = "確定値" if kyori == 1200 else "AI推定"
                print(f"  距離 {kyori:4d}m: 前半3F={median_zenhan:5.1f}秒, 後半3F={median_kohan:5.1f}秒 ({method}, サンプル数:{len(zenhan_3f_list):5d})")
            else:
                print(f"  距離 {kyori:4d}m: ⚠️ 有効データ不足（{len(zenhan_3f_list)}件）スキップ")
    
    conn.close()
    
    # Python辞書形式で出力
    print("\n" + "="*80)
    print("✅ 基準タイム計算完了")
    print("="*80)
    print()
    print("# config/base_times.py に貼り付けてください")
    print()
    print("BASE_TIMES = {")
    for keibajo_code, kyori_data in sorted(results.items()):
        print(f"    '{keibajo_code}': {{  # 競馬場コード {keibajo_code}")
        for kyori, times in sorted(kyori_data.items()):
            print(f"        {kyori}: {{'zenhan_3f': {times['zenhan_3f']}, 'kohan_3f': {times['kohan_3f']}}},  # サンプル数: {times['race_count']}")
        print("    },")
    print("}")
    print()
    print("="*80)
    print("📁 保存先: E:\\UmaData\\nar-analytics-python-v2\\config\\base_times.py")
    print("="*80)

if __name__ == '__main__':
    calculate_base_times_from_real_data()
