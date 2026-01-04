"""
PostgreSQL接続テスト

このファイルをCEOのPC（E:\UmaData\nar-analytics-python\）に配置して実行してください。
"""

import psycopg2
from psycopg2.extras import RealDictCursor

# データベース接続設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}

def test_connection():
    """PostgreSQL接続テスト"""
    try:
        print('=' * 70)
        print('  PostgreSQL接続テスト')
        print('=' * 70)
        print()
        
        print('🔌 接続中...')
        conn = psycopg2.connect(**DB_CONFIG)
        print('✅ データベース接続成功！')
        print()
        
        cur = conn.cursor()
        
        # テスト1: データ件数確認
        print('【テスト1: nvd_se テーブルのデータ件数】')
        cur.execute('SELECT COUNT(*) FROM nvd_se WHERE kaisai_nen >= %s', ('2016',))
        count = cur.fetchone()[0]
        print(f'  nvd_se (2016年以降): {count:,}件')
        
        cur.execute('SELECT COUNT(*) FROM nvd_ra WHERE kaisai_nen >= %s', ('2016',))
        count = cur.fetchone()[0]
        print(f'  nvd_ra (2016年以降): {count:,}件')
        print()
        
        # テスト2: 明日のデータ確認
        print('【テスト2: 明日以降のデータ確認】')
        cur.execute("""
            SELECT COUNT(*) 
            FROM nvd_se 
            WHERE kaisai_nen || kaisai_tsukihi >= TO_CHAR(CURRENT_DATE + 1, 'YYYYMMDD')
        """)
        count = cur.fetchone()[0]
        print(f'  明日以降の出走データ: {count:,}件')
        print()
        
        # テスト3: サンプルデータ取得
        print('【テスト3: 最新レースのサンプルデータ】')
        cur.execute("""
            SELECT 
                keibajo_code,
                kaisai_nen,
                kaisai_tsukihi,
                race_bango,
                umaban,
                bamei,
                kishumei_ryakusho
            FROM nvd_se
            ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
            LIMIT 3
        """)
        
        rows = cur.fetchall()
        print(f'  競馬場 | 開催年 | 開催月日 | R | 馬番 | 馬名 | 騎手')
        print('  ' + '-' * 60)
        for row in rows:
            print(f'  {row[0]:^6} | {row[1]:^6} | {row[2]:^8} | {row[3]:^2} | {row[4]:^4} | {row[5]:^10} | {row[6]:^10}')
        
        cur.close()
        conn.close()
        print()
        print('=' * 70)
        print('✅ 全テスト成功！PostgreSQL接続OK！')
        print('=' * 70)
        
        return True
        
    except Exception as e:
        print()
        print('=' * 70)
        print(f'❌ エラー: {e}')
        print('=' * 70)
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    test_connection()
