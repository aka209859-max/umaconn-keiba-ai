"""
データベース接続設定
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',  # pgAdminと同じ
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',  # 新しいパスワード（CEOが設定後）
    'dbname': 'pckeiba'
}


def get_db_connection():
    """
    データベース接続を取得
    
    Returns:
        psycopg2.connection: データベース接続オブジェクト
    """
    return psycopg2.connect(**DB_CONFIG)


# 接続テスト用関数
def test_connection():
    """
    データベース接続テスト
    """
    try:
        conn = get_db_connection()
        print("✅ データベース接続成功")
        conn.close()
        return True
    except Exception as e:
        print(f"❌ データベース接続失敗: {e}")
        return False

if __name__ == '__main__':
    test_connection()
