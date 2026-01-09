"""
soha_time と kohan_3f のデータ構造を確認するデバッグスクリプト

作成日: 2026-01-09
作成者: AI戦略家
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.db_config import get_db_connection


def debug_soha_time():
    """soha_time と kohan_3f のデータを確認"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 100)
    print("soha_time と kohan_3f のデータ確認")
    print("=" * 100)
    print()
    
    # 大井競馬場のデータを10件取得
    query = """
    SELECT 
        ra.kyori,
        se.soha_time,
        se.kohan_3f,
        se.kakutei_chakujun
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.keibajo_code = se.keibajo_code AND
        ra.race_bango = se.race_bango
    WHERE ra.keibajo_code = '44'
      AND ra.kaisai_nen || ra.kaisai_tsukihi >= '20231001'
      AND ra.kaisai_nen || ra.kaisai_tsukihi <= '20251231'
      AND se.kakutei_chakujun IS NOT NULL
      AND se.kakutei_chakujun != ''
      AND se.kakutei_chakujun ~ '^[0-9]+$'
      AND CAST(se.kakutei_chakujun AS INTEGER) BETWEEN 1 AND 3
      AND se.soha_time IS NOT NULL
      AND se.kohan_3f IS NOT NULL
    LIMIT 20
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"{'距離':<8} {'soha_time':<15} {'kohan_3f':<15} {'着順':<8} {'型':<15}")
    print("-" * 80)
    
    for row in rows:
        kyori = row[0]
        soha_time = row[1]
        kohan_3f = row[2]
        chakujun = row[3]
        
        soha_time_type = type(soha_time).__name__
        
        print(f"{kyori:<8} {str(soha_time):<15} {str(kohan_3f):<15} {chakujun:<8} {soha_time_type:<15}")
    
    print()
    print("=" * 100)
    print("計算テスト")
    print("=" * 100)
    print()
    
    # 計算テスト
    if rows:
        row = rows[0]
        soha_time = row[1]
        kohan_3f = row[2]
        
        print(f"元データ:")
        print(f"  soha_time: {soha_time} (型: {type(soha_time).__name__})")
        print(f"  kohan_3f: {kohan_3f} (型: {type(kohan_3f).__name__})")
        print()
        
        # パターン1: 単純な減算
        try:
            zenhan_3f_v1 = float(soha_time) - float(kohan_3f)
            print(f"パターン1（単純減算）:")
            print(f"  zenhan_3f = float(soha_time) - float(kohan_3f)")
            print(f"  zenhan_3f = {float(soha_time)} - {float(kohan_3f)} = {zenhan_3f_v1}")
        except Exception as e:
            print(f"パターン1 エラー: {e}")
        
        print()
        
        # パターン2: soha_time を秒に変換（1125 → 72.5秒）
        try:
            soha_time_str = str(soha_time)
            if len(soha_time_str) >= 3:
                minutes = int(soha_time_str[:-2])
                seconds = int(soha_time_str[-2:])
                soha_time_sec = minutes * 60 + seconds + (float(soha_time) % 1)
                zenhan_3f_v2 = soha_time_sec - float(kohan_3f)
                print(f"パターン2（MMSSをMM分SS秒に変換）:")
                print(f"  soha_time_str = '{soha_time_str}'")
                print(f"  minutes = {minutes}, seconds = {seconds}")
                print(f"  soha_time_sec = {minutes} * 60 + {seconds} = {soha_time_sec}")
                print(f"  zenhan_3f = {soha_time_sec} - {float(kohan_3f)} = {zenhan_3f_v2}")
        except Exception as e:
            print(f"パターン2 エラー: {e}")
    
    cur.close()
    conn.close()


if __name__ == '__main__':
    debug_soha_time()
