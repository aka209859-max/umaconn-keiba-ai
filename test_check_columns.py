"""
データベースの列名を確認するスクリプト
"""
import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}

try:
    print("🔌 データベース接続中...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 nvd_se テーブルの列名一覧")
    print("="*80)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_se'
        ORDER BY ordinal_position
    """)
    
    se_columns = cur.fetchall()
    for col in se_columns[:50]:  # 最初の50列
        print(f"  {col[0]:<30} {col[1]}")
    
    print(f"\n  ... 全 {len(se_columns)} 列")
    
    print("\n" + "="*80)
    print("📊 nvd_ra テーブルの列名一覧")
    print("="*80)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_ra'
        ORDER BY ordinal_position
    """)
    
    ra_columns = cur.fetchall()
    for col in ra_columns[:50]:  # 最初の50列
        print(f"  {col[0]:<30} {col[1]}")
    
    print(f"\n  ... 全 {len(ra_columns)} 列")
    
    cur.close()
    conn.close()
    
    print("\n✅ 列名確認完了！")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
