#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
テーブル構造確認スクリプト
================================================================================
nvd_ra テーブルの列名を確認します。
================================================================================
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def check_table_structure():
    """テーブル構造を確認"""
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 nvd_ra テーブル構造確認")
    print("="*80 + "\n")
    
    # テーブルの列名を取得
    query = """
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'nvd_ra'
    ORDER BY ordinal_position;
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"{'列名':^30} | {'データ型':^20} | {'最大文字数':^12}")
    print("-" * 80)
    
    corner_columns = []
    
    for row in results:
        column_name = row[0]
        data_type = row[1]
        max_length = row[2] if row[2] else '-'
        
        print(f"{column_name:<30} | {data_type:<20} | {str(max_length):>12}")
        
        # コーナー関連の列名を記録
        if 'corner' in column_name.lower() or 'コーナー' in column_name:
            corner_columns.append(column_name)
    
    print("\n" + "="*80)
    print("🔍 コーナー関連の列:")
    if corner_columns:
        for col in corner_columns:
            print(f"  - {col}")
    else:
        print("  コーナー関連の列が見つかりませんでした。")
        print("\n  別の列名を探しています...")
        
        # 通過順位関連の列を探す
        cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns
        WHERE table_name = 'nvd_ra' 
        AND (column_name LIKE '%通過%' OR column_name LIKE '%pass%' OR column_name LIKE '%position%')
        ORDER BY ordinal_position;
        """)
        
        pass_columns = cursor.fetchall()
        if pass_columns:
            print("\n  通過順位関連の列:")
            for col in pass_columns:
                print(f"  - {col[0]}")
    
    print("="*80 + "\n")
    
    # サンプルデータを1件取得
    print("\n" + "="*80)
    print("📊 サンプルデータ（1件）")
    print("="*80 + "\n")
    
    cursor.execute("SELECT * FROM nvd_ra LIMIT 1;")
    sample = cursor.fetchone()
    
    cursor.execute("""
    SELECT column_name 
    FROM information_schema.columns
    WHERE table_name = 'nvd_ra'
    ORDER BY ordinal_position;
    """)
    columns = [row[0] for row in cursor.fetchall()]
    
    for i, col in enumerate(columns):
        value = sample[i] if i < len(sample) else None
        print(f"{col:<30} : {value}")
    
    cursor.close()
    conn.close()


if __name__ == "__main__":
    try:
        check_table_structure()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
