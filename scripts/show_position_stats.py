#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position指数の統計データを表示
"""

import psycopg2

# データベース接続
conn = psycopg2.connect(
    host='localhost',
    dbname='pckeiba',
    user='postgres',
    password='keiba2025'
)

cur = conn.cursor()

# Position指数の統計サンプル表示
cur.execute("""
    SELECT keibajo_code, kyori, 
           position_index_avg, position_index_stddev,
           position_index_max, position_index_min,
           data_count
    FROM nar_hqs_index_stats 
    WHERE position_index_avg IS NOT NULL 
    ORDER BY keibajo_code, kyori 
    LIMIT 20
""")

print("="*100)
print("Position指数の統計データ（先頭20件）")
print("="*100)
print(f"{'競馬場':8s} | {'距離':6s} | {'平均':8s} | {'標準偏差':8s} | {'最大':8s} | {'最小':8s} | {'件数':6s}")
print("-"*100)

for row in cur.fetchall():
    keibajo = row[0] if row[0] else '不明'
    kyori = row[1] if row[1] else '不明'
    avg = row[2] if row[2] is not None else 0.0
    stddev = row[3] if row[3] is not None else 0.0
    max_val = row[4] if row[4] is not None else 0.0
    min_val = row[5] if row[5] is not None else 0.0
    count = row[6] if row[6] is not None else 0
    
    print(f"{keibajo:8s} | {kyori:6s} | {avg:8.2f} | {stddev:8.2f} | {max_val:8.2f} | {min_val:8.2f} | {count:6d}")

# 全体統計
cur.execute("""
    SELECT 
        COUNT(*) as total_records,
        COUNT(CASE WHEN position_index_avg IS NOT NULL THEN 1 END) as position_records,
        COUNT(CASE WHEN ten_index_avg IS NOT NULL THEN 1 END) as ten_records,
        COUNT(CASE WHEN agari_index_avg IS NOT NULL THEN 1 END) as agari_records,
        COUNT(CASE WHEN pace_index_avg IS NOT NULL THEN 1 END) as pace_records
    FROM nar_hqs_index_stats
""")

stats = cur.fetchone()
print("\n" + "="*100)
print("全体統計")
print("="*100)
print(f"総レコード数:        {stats[0]:6d}件")
print(f"Position指数データ: {stats[1]:6d}件 ({stats[1]/stats[0]*100:5.1f}%)")
print(f"テン指数データ:     {stats[2]:6d}件 ({stats[2]/stats[0]*100:5.1f}%)")
print(f"上がり指数データ:   {stats[3]:6d}件 ({stats[3]/stats[0]*100:5.1f}%)")
print(f"ペース指数データ:   {stats[4]:6d}件 ({stats[4]/stats[0]*100:5.1f}%)")
print("="*100)

conn.close()
