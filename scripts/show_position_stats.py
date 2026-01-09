#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Position指数の的中率・回収率データを表示
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

# Position指数の統計表示
cur.execute("""
    SELECT 
        keibajo_code,
        index_value,
        cnt_win,
        hit_win,
        rate_win_hit,
        adj_win_ret,
        cnt_place,
        hit_place,
        rate_place_hit,
        adj_place_ret
    FROM nar_hqs_index_stats 
    WHERE index_type = 'position'
    ORDER BY keibajo_code, CAST(index_value AS INTEGER)
    LIMIT 30
""")

print("="*120)
print("Position指数の的中率・回収率データ（先頭30件）")
print("="*120)
print(f"{'競馬場':4s} | {'指数':4s} | {'単勝試行':8s} | {'単勝的中':8s} | {'単勝率':6s} | {'単勝回収':8s} | {'複勝試行':8s} | {'複勝的中':8s} | {'複勝率':6s} | {'複勝回収':8s}")
print("-"*120)

for row in cur.fetchall():
    keibajo = row[0] or '不明'
    idx_val = row[1] or '0'
    cnt_w = row[2] or 0
    hit_w = row[3] or 0
    rate_w = row[4] or 0.0
    ret_w = row[5] or 0.0
    cnt_p = row[6] or 0
    hit_p = row[7] or 0
    rate_p = row[8] or 0.0
    ret_p = row[9] or 0.0
    
    print(f"{keibajo:4s} | {idx_val:4s} | {cnt_w:8d} | {hit_w:8d} | {rate_w:6.2f} | {ret_w:8.2f} | {cnt_p:8d} | {hit_p:8d} | {rate_p:6.2f} | {ret_p:8.2f}")

# 全体統計
cur.execute("""
    SELECT 
        index_type,
        COUNT(*) as record_count,
        SUM(cnt_win) as total_races,
        AVG(rate_win_hit) as avg_win_rate,
        AVG(adj_win_ret) as avg_win_return
    FROM nar_hqs_index_stats
    GROUP BY index_type
    ORDER BY index_type
""")

print("\n" + "="*120)
print("指数タイプ別の全体統計")
print("="*120)
print(f"{'指数タイプ':12s} | {'レコード数':10s} | {'総レース数':10s} | {'平均単勝率':10s} | {'平均単勝回収':12s}")
print("-"*120)

for row in cur.fetchall():
    idx_type = row[0] or '不明'
    rec_cnt = row[1] or 0
    total = row[2] or 0
    avg_rate = row[3] or 0.0
    avg_ret = row[4] or 0.0
    
    print(f"{idx_type:12s} | {rec_cnt:10d} | {total:10d} | {avg_rate:10.2f} | {avg_ret:12.2f}")

print("="*120)

# Position指数の分布確認
cur.execute("""
    SELECT 
        index_value,
        COUNT(*) as keibajo_count,
        SUM(cnt_win) as total_races,
        AVG(rate_win_hit) as avg_win_rate
    FROM nar_hqs_index_stats
    WHERE index_type = 'position'
    GROUP BY index_value
    ORDER BY CAST(index_value AS INTEGER)
""")

print("\n" + "="*120)
print("Position指数の分布（指数値別）")
print("="*120)
print(f"{'指数値':8s} | {'競馬場数':10s} | {'総レース数':12s} | {'平均単勝率':12s}")
print("-"*120)

for row in cur.fetchall():
    idx_val = row[0] or '0'
    keibajo_cnt = row[1] or 0
    total = row[2] or 0
    avg_rate = row[3] or 0.0
    
    print(f"{idx_val:8s} | {keibajo_cnt:10d} | {total:12d} | {avg_rate:12.2f}")

print("="*120)

conn.close()
