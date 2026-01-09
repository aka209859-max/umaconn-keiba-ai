"""
soha_time と kohan_3f の実データ検証スクリプト
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.db_config import get_db_connection

def verify_data():
    print("\n" + "="*60)
    print("soha_time と kohan_3f の実データ検証")
    print("="*60)
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    query = """
    SELECT 
        ra.kyori,
        se.soha_time,
        se.kohan_3f,
        se.kakutei_chakujun,
        se.bamei
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.keibajo_code = se.keibajo_code AND
        ra.race_bango = se.race_bango
    WHERE ra.keibajo_code = '30'  -- 門別
      AND ra.kaisai_nen || ra.kaisai_tsukihi >= '20241001'
      AND ra.kaisai_nen || ra.kaisai_tsukihi <= '20241231'
      AND CAST(ra.kyori AS INTEGER) = 1000
      AND se.kakutei_chakujun = '1'
      AND se.soha_time IS NOT NULL
      AND se.kohan_3f IS NOT NULL
    LIMIT 5
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    print("\n【門別 1000m の勝ち馬データサンプル】")
    print(f"{'距離':<8} {'soha_time':<12} {'kohan_3f':<12} {'着順':<8} {'馬名':<20}")
    print("-" * 70)
    
    for row in rows:
        kyori, soha_time, kohan_3f, chakujun, bamei = row
        print(f"{kyori:<8} {soha_time:<12} {kohan_3f:<12} {chakujun:<8} {bamei:<20}")
    
    # 変換テスト
    print("\n" + "="*60)
    print("変換テスト")
    print("="*60)
    
    if rows:
        row = rows[0]
        soha_time_str = str(row[1])
        kohan_3f_str = str(row[2])
        
        print(f"\n元データ: soha_time={soha_time_str}, kohan_3f={kohan_3f_str}")
        
        # パターン1: 現在の変換式（mSSd）
        soha_padded = soha_time_str.zfill(4)
        minutes = int(soha_padded[0:1])
        seconds = int(soha_padded[1:3])
        deciseconds = int(soha_padded[3:4])
        soha_seconds = minutes * 60 + seconds + deciseconds / 10.0
        kohan_seconds = float(kohan_3f_str) / 10.0
        zenhan_3f_pattern1 = soha_seconds - kohan_seconds
        
        print(f"\nパターン1（現在）: soha_time={soha_seconds:.1f}秒, kohan_3f={kohan_seconds:.1f}秒, zenhan_3f={zenhan_3f_pattern1:.1f}秒")
        
        # パターン2: soha_time が MMSSd 形式の場合（1355 = 13分55秒）
        if len(soha_time_str) >= 4:
            minutes2 = int(soha_time_str[0:2])
            seconds2 = int(soha_time_str[2:4]) if len(soha_time_str) >= 4 else 0
            deciseconds2 = int(soha_time_str[4:5]) if len(soha_time_str) >= 5 else 0
            soha_seconds2 = minutes2 * 60 + seconds2 + deciseconds2 / 10.0
            zenhan_3f_pattern2 = soha_seconds2 - kohan_seconds
            
            print(f"パターン2（MMSSd）: soha_time={soha_seconds2:.1f}秒, kohan_3f={kohan_seconds:.1f}秒, zenhan_3f={zenhan_3f_pattern2:.1f}秒")
    
    cur.close()
    conn.close()

if __name__ == '__main__':
    verify_data()
