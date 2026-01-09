"""
nvd_se テーブルのカラム名確認スクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_db_connection

def check_columns():
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT column_name, data_type, character_maximum_length
    FROM information_schema.columns
    WHERE table_name = 'nvd_se'
      AND (column_name LIKE '%agari%' 
           OR column_name LIKE '%kohan%' 
           OR column_name LIKE '%zenhan%'
           OR column_name LIKE '%soha%')
    ORDER BY column_name;
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    print("\n【nvd_se テーブルのタイム関連カラム】")
    print(f"{'カラム名':<20} {'データ型':<15} {'最大長'}")
    print("-" * 50)
    
    for row in rows:
        column_name, data_type, max_length = row
        max_length_str = str(max_length) if max_length else 'N/A'
        print(f"{column_name:<20} {data_type:<15} {max_length_str}")
    
    # サンプルデータを取得
    query2 = """
    SELECT soha_time, kohan_3f
    FROM nvd_se
    WHERE soha_time IS NOT NULL
      AND kohan_3f IS NOT NULL
    LIMIT 5
    """
    
    cur.execute(query2)
    rows2 = cur.fetchall()
    
    print("\n【サンプルデータ】")
    print(f"{'soha_time':<15} {'kohan_3f':<15}")
    print("-" * 30)
    for row in rows2:
        print(f"{row[0]:<15} {row[1]:<15}")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    check_columns()
