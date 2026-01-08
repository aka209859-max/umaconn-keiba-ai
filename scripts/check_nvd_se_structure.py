#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
nvd_se テーブル構造確認スクリプト
"""

import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def check_nvd_se_structure():
    """nvd_se テーブル構造を確認"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 nvd_se テーブル構造確認")
    print("="*80 + "\n")
    
    # テーブルの列名を取得
    query = """
    SELECT column_name, data_type
    FROM information_schema.columns
    WHERE table_name = 'nvd_se'
    ORDER BY ordinal_position;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'列名':^40} | {'データ型':^20}")
    print("-" * 80)
    
    for row in results:
        column_name = row[0]
        data_type = row[1]
        print(f"{column_name:<40} | {data_type:<20}")
    
    print("\n" + "="*80)
    
    # サンプルデータを1件取得
    print("\n📊 サンプルデータ（1件）\n")
    
    cursor.execute("SELECT * FROM nvd_se LIMIT 1;")
    sample = cursor.fetchone()
    
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns
    WHERE table_name = 'nvd_se'
    ORDER BY ordinal_position;
    """)
    columns = [row[0] for row in cursor.fetchall()]
    
    for i, col in enumerate(columns):
        value = sample[i] if i < len(sample) else None
        print(f"{col:<40} : {value}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        check_nvd_se_structure()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
