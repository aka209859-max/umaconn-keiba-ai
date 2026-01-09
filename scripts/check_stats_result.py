#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HQS指数統計データ確認スクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def check_stats():
    """統計データを確認"""
    
    print("\n" + "="*80)
    print("HQS指数統計データ確認")
    print("="*80 + "\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 総件数
    cursor.execute("SELECT COUNT(*) FROM nar_hqs_index_stats")
    total = cursor.fetchone()[0]
    print(f"✅ 総統計データ件数: {total}件\n")
    
    # Position指数の統計サンプル
    print("="*80)
    print("Position指数統計サンプル（10件）")
    print("="*80)
    
    query = """
    SELECT 
        keibajo_code,
        kyori,
        position_index_avg,
        position_index_stddev,
        total_count
    FROM nar_hqs_index_stats
    WHERE position_index_avg IS NOT NULL
    ORDER BY keibajo_code, CAST(kyori AS INTEGER)
    LIMIT 10
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    print(f"{'競馬場':6s} | {'距離':6s} | {'平均':8s} | {'標準偏差':8s} | {'件数':6s}")
    print("-" * 60)
    
    for row in rows:
        keibajo_code, kyori, avg, stddev, count = row
        print(f"{keibajo_code:6s} | {kyori:6s} | {avg:8.2f} | {stddev:8.2f} | {count:6d}")
    
    # 競馬場別の統計件数
    print("\n" + "="*80)
    print("競馬場別統計データ件数")
    print("="*80)
    
    query = """
    SELECT 
        keibajo_code,
        COUNT(*) as count,
        SUM(total_count) as total_races
    FROM nar_hqs_index_stats
    GROUP BY keibajo_code
    ORDER BY keibajo_code
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    keibajo_names = {
        '30': '門別', '35': '盛岡', '36': '水沢', '42': '浦和',
        '43': '船橋', '44': '大井', '45': '川崎', '46': '金沢',
        '47': '笠松', '48': '名古屋', '50': '園田', '51': '姫路',
        '54': '高知', '55': '佐賀'
    }
    
    print(f"{'競馬場':6s} | {'名称':8s} | {'統計件数':8s} | {'総レース数':10s}")
    print("-" * 60)
    
    for row in rows:
        keibajo_code, count, total_races = row
        name = keibajo_names.get(keibajo_code, '不明')
        print(f"{keibajo_code:6s} | {name:8s} | {count:8d} | {total_races:10d}")
    
    # Position指数が計算されたデータの割合
    print("\n" + "="*80)
    print("Position指数計算状況")
    print("="*80)
    
    query = """
    SELECT 
        COUNT(*) FILTER (WHERE position_index_avg IS NOT NULL) as with_position,
        COUNT(*) FILTER (WHERE position_index_avg IS NULL) as without_position,
        COUNT(*) as total
    FROM nar_hqs_index_stats
    """
    
    cursor.execute(query)
    row = cursor.fetchone()
    with_position, without_position, total = row
    
    print(f"Position指数あり: {with_position}件 ({100*with_position/total:.1f}%)")
    print(f"Position指数なし: {without_position}件 ({100*without_position/total:.1f}%)")
    print(f"合計: {total}件")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ 確認完了")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        check_stats()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
