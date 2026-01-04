"""
データベース接続設定
"""

DB_CONFIG = {
    'host': '127.0.0.1',
    'port': 5432,
    'user': 'postgres',
    'password': 'postgres',  # CEO: 実際のパスワードに変更してください
    'dbname': 'pckeiba'
}

# 接続テスト用関数
def test_connection():
    """
    データベース接続テスト
    """
    import psycopg2
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ データベース接続成功")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return False

if __name__ == '__main__':
    test_connection()
