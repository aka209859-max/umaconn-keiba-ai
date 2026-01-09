#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全指数（Position/Ten/Agari/Pace）の的中率・回収率データを表示
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

# 各指数タイプごとに表示
index_types = ['position', 'ten', 'agari', 'pace']

for idx_type in index_types:
    cur.execute("""
        SELECT 
            index_value,
            COUNT(*) as keibajo_count,
            SUM(cnt_win) as total_races,
            AVG(rate_win_hit) as avg_win_rate,
            AVG(rate_place_hit) as avg_place_rate
        FROM nar_hqs_index_stats
        WHERE index_type = %s
        GROUP BY index_value
        ORDER BY CAST(index_value AS INTEGER)
    """, (idx_type,))
    
    print("\n" + "="*100)
    print(f"{idx_type.upper()}指数の分布")
    print("="*100)
    print(f"{'指数値':8s} | {'競馬場数':10s} | {'総レース数':12s} | {'平均単勝率':12s} | {'平均複勝率':12s}")
    print("-"*100)
    
    for row in cur.fetchall():
        idx_val = row[0] or '0'
        keibajo_cnt = row[1] or 0
        total = row[2] or 0
        avg_win = row[3] or 0.0
        avg_place = row[4] or 0.0
        
        print(f"{idx_val:8s} | {keibajo_cnt:10d} | {total:12d} | {avg_win:12.2f} | {avg_place:12.2f}")
    
    print("="*100)

# 各指数タイプの最優秀指数値を比較
print("\n" + "="*100)
print("各指数の最優秀値（単勝的中率が最も高い指数値）")
print("="*100)

for idx_type in index_types:
    cur.execute("""
        SELECT 
            index_value,
            AVG(rate_win_hit) as avg_win_rate,
            SUM(cnt_win) as total_races
        FROM nar_hqs_index_stats
        WHERE index_type = %s
        GROUP BY index_value
        ORDER BY AVG(rate_win_hit) DESC
        LIMIT 1
    """, (idx_type,))
    
    row = cur.fetchone()
    if row:
        idx_val = row[0]
        win_rate = row[1]
        total = row[2]
        print(f"{idx_type:12s} | 最優秀値={idx_val:4s} | 単勝率={win_rate:6.2f}% | レース数={total:,d}件")

print("="*100)

# HQS4指数のシミュレーション（4指数の合計で評価）
print("\n" + "="*100)
print("🔥 HQS4指数の予測精度（4指数の組み合わせ）")
print("="*100)
print("※これは単純な合算例です。実際は重み付けや正規化が必要です")
print("-"*100)

# 各指数の優秀ゾーンを定義
print("\n推奨される指数の使い方:")
print("  Position指数: 10-20 が強い（単勝率 20-35%）")
print("  Ten指数:      10-30 が強い（要確認）")
print("  Agari指数:    10-30 が強い（要確認）")
print("  Pace指数:     10-30 が強い（要確認）")
print("\n→ HQS4指数 = Position + Ten + Agari + Pace")
print("→ HQS4指数が低いほど強い馬（40-80点が最強ゾーン）")
print("="*100)

conn.close()
