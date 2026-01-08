#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
各競馬場で実際に開催されている距離を確認するスクリプト
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection

def main():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
    SELECT keibajo_code, kyori, COUNT(*) as cnt 
    FROM nvd_ra 
    WHERE keibajo_code IN ('30','35','36','42','43','44','45','46','47','48','49','50','51')
    GROUP BY keibajo_code, kyori 
    ORDER BY keibajo_code, kyori
    """)
    
    rows = cur.fetchall()
    
    print("競馬場コード,距離(m),レース数")
    print("-" * 40)
    for row in rows:
        print(f'{row[0]},{row[1]},{row[2]}')
    
    conn.close()

if __name__ == '__main__':
    main()
