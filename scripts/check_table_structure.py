#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
nar_hqs_index_stats テーブルの構造を確認
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

# テーブル構造を確認
cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'nar_hqs_index_stats'
    ORDER BY ordinal_position
""")

print("="*80)
print("nar_hqs_index_stats テーブルの列構造")
print("="*80)
print(f"{'列名':30s} | {'データ型':20s} | {'最大長':10s}")
print("-"*80)

for row in cur.fetchall():
    col_name = row[0]
    data_type = row[1]
    max_length = str(row[2]) if row[2] else 'N/A'
    print(f"{col_name:30s} | {data_type:20s} | {max_length:10s}")

print("="*80)

# サンプルデータを1件取得
cur.execute("SELECT * FROM nar_hqs_index_stats LIMIT 1")
row = cur.fetchone()

if row:
    print("\n" + "="*80)
    print("サンプルデータ（1件目）")
    print("="*80)
    
    # 列名を取得
    col_names = [desc[0] for desc in cur.description]
    
    for col_name, value in zip(col_names, row):
        print(f"{col_name:30s} = {value}")
    
    print("="*80)
else:
    print("\n⚠️ データが存在しません")

conn.close()
