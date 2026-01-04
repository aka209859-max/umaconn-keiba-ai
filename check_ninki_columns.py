"""
nvd_se テーブルの人気順関連の列名を確認
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
    print("📊 nvd_se テーブルの人気順関連の列")
    print("="*80)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_se'
        AND (column_name LIKE '%ninki%' OR column_name LIKE '%nink%')
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    if columns:
        for col in columns:
            print(f"  {col[0]:<40} {col[1]}")
    else:
        print("  人気順関連の列が見つかりませんでした")
    
    cur.close()
    conn.close()
    
    print("\n✅ 確認完了！")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
