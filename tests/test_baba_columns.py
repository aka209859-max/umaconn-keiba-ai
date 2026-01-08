"""
馬場状態関連の列名を確認するスクリプト
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
    print("📊 nvd_ra テーブルの馬場状態関連の列")
    print("="*80)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_ra' 
        AND column_name LIKE '%baba%'
        ORDER BY ordinal_position
    """)
    
    columns = cur.fetchall()
    if columns:
        for col in columns:
            print(f"  {col[0]:<40} {col[1]}")
    else:
        print("  馬場状態関連の列が見つかりませんでした")
    
    print("\n" + "="*80)
    print("📊 サンプルデータ（最新3レース）")
    print("="*80)
    
    # 馬場状態関連の全列を取得
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_ra' 
        AND column_name LIKE '%baba%'
        ORDER BY ordinal_position
    """)
    
    baba_columns = [row[0] for row in cur.fetchall()]
    
    if baba_columns:
        columns_str = ", ".join(baba_columns)
        query = f"""
            SELECT kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, 
                   kyori, {columns_str}
            FROM nvd_ra
            WHERE kaisai_nen >= '2024'
            ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
            LIMIT 3
        """
        
        cur.execute(query)
        rows = cur.fetchall()
        
        # ヘッダー
        print(f"\n  {'年':<6} {'月日':<10} {'場':<4} {'R':<4} {'距離':<6} ", end="")
        for col in baba_columns:
            print(f"{col:<20} ", end="")
        print()
        print("  " + "-"*100)
        
        # データ
        for row in rows:
            print(f"  {row[0]:<6} {row[1]:<10} {row[2]:<4} {row[3]:<4} {row[4]:<6} ", end="")
            for i in range(5, len(row)):
                val = row[i] if row[i] else '(null)'
                print(f"{val:<20} ", end="")
            print()
    
    cur.close()
    conn.close()
    
    print("\n✅ 確認完了！")
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
