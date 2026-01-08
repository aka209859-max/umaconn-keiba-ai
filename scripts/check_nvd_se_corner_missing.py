#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nvd_se コーナー順位データ欠損率確認スクリプト
================================================================================
nvd_se テーブルのコーナー順位データ（corner_1, corner_2）の欠損率を確認します。
================================================================================
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def check_nvd_se_corner_missing():
    """nvd_se コーナー順位データの欠損率を確認"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 nvd_se コーナー順位データ欠損率確認")
    print("="*80 + "\n")
    
    # 競馬場別のコーナー順位データ欠損率を確認
    query = """
    SELECT 
        se.keibajo_code,
        COUNT(*) as total_records,
        COUNT(CASE WHEN se.corner_1 IS NULL OR se.corner_1 = '' OR se.corner_1 = '00' THEN 1 END) as corner1_missing,
        COUNT(CASE WHEN se.corner_2 IS NULL OR se.corner_2 = '' OR se.corner_2 = '00' THEN 1 END) as corner2_missing,
        ROUND(100.0 * COUNT(CASE WHEN se.corner_1 IS NULL OR se.corner_1 = '' OR se.corner_1 = '00' THEN 1 END) / COUNT(*), 2) as corner1_missing_pct,
        ROUND(100.0 * COUNT(CASE WHEN se.corner_2 IS NULL OR se.corner_2 = '' OR se.corner_2 = '00' THEN 1 END) / COUNT(*), 2) as corner2_missing_pct
    FROM nvd_se se
    JOIN nvd_ra ra ON 
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.keibajo_code = ra.keibajo_code AND
        se.race_bango = ra.race_bango
    WHERE ra.babajotai_code_dirt = '1'  -- 馬場良のみ
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != ''
        AND se.kakutei_chakujun ~ '^[0-9]+$'
    GROUP BY se.keibajo_code
    ORDER BY se.keibajo_code;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # ヘッダー
    print(f"{'競馬場':^10} | {'総レコード数':>12} | {'corner1欠損':>12} | {'corner2欠損':>12} | {'corner1欠損率':>12} | {'corner2欠損率':>12}")
    print("-" * 80)
    
    total_records = 0
    total_corner1_missing = 0
    total_corner2_missing = 0
    
    # 競馬場名マッピング
    keibajo_names = {
        '30': '門別',
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
        '55': '佐賀',
    }
    
    for row in results:
        keibajo_code = row[0]
        keibajo_name = keibajo_names.get(keibajo_code, keibajo_code)
        total = row[1]
        corner1_missing = row[2]
        corner2_missing = row[3]
        corner1_pct = row[4]
        corner2_pct = row[5]
        
        print(f"{keibajo_name:^10} | {total:>12,} | {corner1_missing:>12,} | {corner2_missing:>12,} | {corner1_pct:>11.2f}% | {corner2_pct:>11.2f}%")
        
        total_records += total
        total_corner1_missing += corner1_missing
        total_corner2_missing += corner2_missing
    
    # 合計
    print("-" * 80)
    avg_corner1_pct = 100.0 * total_corner1_missing / total_records if total_records > 0 else 0
    avg_corner2_pct = 100.0 * total_corner2_missing / total_records if total_records > 0 else 0
    print(f"{'合計':^10} | {total_records:>12,} | {total_corner1_missing:>12,} | {total_corner2_missing:>12,} | {avg_corner1_pct:>11.2f}% | {avg_corner2_pct:>11.2f}%")
    
    print("\n" + "="*80)
    print("📊 判定基準:")
    print("  - 欠損率 < 10%: Position指数は使用可能 ✅")
    print("  - 欠損率 10-30%: Position指数の精度は低いが使用可能 ⚠️")
    print("  - 欠損率 > 30%: Position指数は使えない ❌")
    print("="*80 + "\n")
    
    # 判定
    if avg_corner1_pct < 10 and avg_corner2_pct < 10:
        print("✅ 判定: Position指数は使用可能です！")
    elif avg_corner1_pct < 30 and avg_corner2_pct < 30:
        print("⚠️ 判定: Position指数の精度は低いですが使用可能です。補完ロジックの検討を推奨します。")
    else:
        print("❌ 判定: Position指数は使えません！対策が必要です。")
        print("\n対策案:")
        print("  1. Position指数を除外し、HQS 3指数（Ten, Agari, Pace）のみ使用")
        print("  2. 補完ロジックを実装（他のデータから推定）")
        print("  3. データソースを変更（別のテーブルやAPIから取得）")
    
    # 詳細分析: 距離別の欠損率
    print("\n" + "="*80)
    print("📊 距離別コーナー順位欠損率")
    print("="*80 + "\n")
    
    query_kyori = """
    SELECT 
        ra.kyori,
        COUNT(*) as total_records,
        COUNT(CASE WHEN se.corner_1 IS NULL OR se.corner_1 = '' OR se.corner_1 = '00' THEN 1 END) as corner1_missing,
        ROUND(100.0 * COUNT(CASE WHEN se.corner_1 IS NULL OR se.corner_1 = '' OR se.corner_1 = '00' THEN 1 END) / COUNT(*), 2) as corner1_missing_pct
    FROM nvd_se se
    JOIN nvd_ra ra ON 
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.keibajo_code = ra.keibajo_code AND
        se.race_bango = ra.race_bango
    WHERE ra.babajotai_code_dirt = '1'
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != ''
        AND se.kakutei_chakujun ~ '^[0-9]+$'
    GROUP BY ra.kyori
    ORDER BY ra.kyori;
    """
    
    cursor.execute(query_kyori)
    kyori_results = cursor.fetchall()
    
    print(f"{'距離':^10} | {'総レコード数':>12} | {'corner1欠損':>12} | {'欠損率':>12}")
    print("-" * 60)
    
    for row in kyori_results:
        kyori = row[0]
        total = row[1]
        corner1_missing = row[2]
        corner1_pct = row[3]
        
        print(f"{kyori:>10} | {total:>12,} | {corner1_missing:>12,} | {corner1_pct:>11.2f}%")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        check_nvd_se_corner_missing()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
