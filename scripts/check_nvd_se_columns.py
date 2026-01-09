#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nvd_seテーブルの列構造を確認するスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection

def check_nvd_se_columns():
    """nvd_seテーブルの列構造を確認"""
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("="*80)
    print("nvd_se テーブルの列構造")
    print("="*80)
    print()
    
    cur.execute("""
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'nvd_se'
    ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    
    print(f"列数: {len(columns)}件")
    print()
    
    for col_name, data_type, max_length in columns:
        if max_length:
            print(f"  {col_name:30s} {data_type}({max_length})")
        else:
            print(f"  {col_name:30s} {data_type}")
    
    print()
    print("="*80)
    print("3Fタイム関連の列を検索")
    print("="*80)
    print()
    
    time_related = [col for col, _, _ in columns if '3f' in col.lower() or 'time' in col.lower() or 'han' in col.lower()]
    
    if time_related:
        print("3Fタイム関連の列:")
        for col in time_related:
            print(f"  - {col}")
    else:
        print("⚠️ 3Fタイム関連の列が見つかりません")
    
    print()
    print("="*80)
    print("サンプルデータを取得")
    print("="*80)
    print()
    
    cur.execute("""
    SELECT * FROM nvd_se LIMIT 1
    """)
    
    sample = cur.fetchone()
    col_names = [desc[0] for desc in cur.description]
    
    for i, col_name in enumerate(col_names):
        print(f"  {col_name:30s} = {sample[i]}")
    
    conn.close()

if __name__ == '__main__':
    check_nvd_se_columns()
