"""
競馬場別・指数別の詳細統計スクリプト

各競馬場ごとに4つの指数（Position, Ten, Agari, Pace）の分布を集計し、
競馬場ごとの特性を明らかにします。

作成日: 2026-01-09
作者: AI戦略家
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.db_config import get_db_connection

# 競馬場名マッピング
KEIBAJO_NAMES = {
    '30': '門別',
    '33': '帯広',
    '35': '盛岡',
    '36': '水沢',
    '42': '浦和',
    '43': '船橋',
    '44': '大井',
    '45': '川崎',
    '46': '金沢',
    '47': '笠松',
    '48': '名古屋',
    '50': '園田',
    '51': '姫路',
    '54': '高知',
    '55': '佐賀',
}


def show_keibajo_index_stats():
    """競馬場別・指数別の統計を表示"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 100)
    print("競馬場別・HQS指数統計")
    print("=" * 100)
    print()
    
    # 指数タイプごとに処理
    for index_type in ['position', 'ten', 'agari', 'pace']:
        print(f"\n{'=' * 100}")
        print(f"{index_type.upper()}指数の競馬場別分布")
        print("=" * 100)
        print()
        
        # 競馬場ごとの統計を取得
        query = """
        SELECT 
            keibajo_code,
            index_value,
            SUM(total_races) AS total_races,
            SUM(cnt_win) AS cnt_win,
            SUM(cnt_place) AS cnt_place,
            AVG(avg_win_rate) AS avg_win_rate,
            AVG(avg_place_rate) AS avg_place_rate
        FROM nar_hqs_index_stats
        WHERE index_type = %s
        GROUP BY keibajo_code, index_value
        ORDER BY keibajo_code, CAST(index_value AS INTEGER)
        """
        
        cur.execute(query, (index_type,))
        rows = cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ データなし")
            continue
        
        # 競馬場ごとに集計
        keibajo_stats = {}
        for row in rows:
            keibajo_code = row[0]
            index_value = row[1]
            total_races = row[2]
            cnt_win = row[3]
            cnt_place = row[4]
            avg_win_rate = row[5]
            avg_place_rate = row[6]
            
            if keibajo_code not in keibajo_stats:
                keibajo_stats[keibajo_code] = {}
            
            keibajo_stats[keibajo_code][index_value] = {
                'total_races': total_races,
                'cnt_win': cnt_win,
                'cnt_place': cnt_place,
                'avg_win_rate': avg_win_rate,
                'avg_place_rate': avg_place_rate,
            }
        
        # 競馬場ごとに表示
        for keibajo_code in sorted(keibajo_stats.keys()):
            keibajo_name = KEIBAJO_NAMES.get(keibajo_code, f'不明({keibajo_code})')
            stats = keibajo_stats[keibajo_code]
            
            # 総レース数
            total_races = sum(s['total_races'] for s in stats.values())
            
            # 指数値の範囲
            index_values = sorted([int(v) for v in stats.keys()])
            if not index_values:
                continue
            
            min_value = min(index_values)
            max_value = max(index_values)
            
            # 最頻値（モード）
            mode_value = max(stats.items(), key=lambda x: x[1]['total_races'])[0]
            mode_count = stats[mode_value]['total_races']
            mode_rate = (mode_count / total_races * 100) if total_races > 0 else 0
            
            print(f"【{keibajo_name}（{keibajo_code}）】")
            print(f"  総レース数: {total_races:,}")
            print(f"  指数範囲: {min_value} 〜 {max_value}")
            print(f"  最頻値: {mode_value} ({mode_count:,}レース, {mode_rate:.1f}%)")
            
            # 上位5つの指数値を表示
            top_5 = sorted(stats.items(), key=lambda x: x[1]['total_races'], reverse=True)[:5]
            print(f"  上位5つの指数値:")
            for idx, (value, data) in enumerate(top_5, 1):
                win_rate = data['avg_win_rate']
                place_rate = data['avg_place_rate']
                count = data['total_races']
                print(f"    {idx}. 指数{value}: {count:,}レース (単勝率{win_rate:.2f}%, 複勝率{place_rate:.2f}%)")
            
            print()
    
    # 競馬場別の総合統計
    print("\n" + "=" * 100)
    print("競馬場別の総合統計")
    print("=" * 100)
    print()
    
    query = """
    SELECT 
        keibajo_code,
        COUNT(DISTINCT index_type) AS index_count,
        SUM(total_races) AS total_races,
        AVG(avg_win_rate) AS avg_win_rate
    FROM nar_hqs_index_stats
    GROUP BY keibajo_code
    ORDER BY keibajo_code
    """
    
    cur.execute(query)
    rows = cur.fetchall()
    
    print(f"{'競馬場':<10} {'コード':<6} {'総レース数':<15} {'平均単勝率':<10}")
    print("-" * 50)
    
    for row in rows:
        keibajo_code = row[0]
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, f'不明({keibajo_code})')
        index_count = row[1]
        total_races = row[2]
        avg_win_rate = row[3]
        
        print(f"{keibajo_name:<10} {keibajo_code:<6} {total_races:<15,} {avg_win_rate:<10.2f}%")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 100)
    print("分析完了")
    print("=" * 100)


def show_keibajo_comparison():
    """競馬場間の比較分析"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("\n" + "=" * 100)
    print("競馬場間の比較分析")
    print("=" * 100)
    print()
    
    # 各指数の平均値と標準偏差を競馬場ごとに計算
    for index_type in ['position', 'ten', 'agari', 'pace']:
        print(f"\n【{index_type.upper()}指数の競馬場別比較】")
        print("-" * 100)
        
        query = """
        SELECT 
            keibajo_code,
            AVG(CAST(index_value AS NUMERIC)) AS avg_value,
            STDDEV(CAST(index_value AS NUMERIC)) AS stddev_value,
            MIN(CAST(index_value AS INTEGER)) AS min_value,
            MAX(CAST(index_value AS INTEGER)) AS max_value,
            SUM(total_races) AS total_races
        FROM nar_hqs_index_stats
        WHERE index_type = %s
        GROUP BY keibajo_code
        ORDER BY avg_value DESC
        """
        
        cur.execute(query, (index_type,))
        rows = cur.fetchall()
        
        print(f"{'競馬場':<10} {'平均値':<10} {'標準偏差':<10} {'最小値':<8} {'最大値':<8} {'レース数':<12}")
        print("-" * 70)
        
        for row in rows:
            keibajo_code = row[0]
            keibajo_name = KEIBAJO_NAMES.get(keibajo_code, f'不明({keibajo_code})')
            avg_value = row[1] if row[1] else 0
            stddev_value = row[2] if row[2] else 0
            min_value = row[3] if row[3] else 0
            max_value = row[4] if row[4] else 0
            total_races = row[5]
            
            print(f"{keibajo_name:<10} {avg_value:<10.2f} {stddev_value:<10.2f} {min_value:<8} {max_value:<8} {total_races:<12,}")
    
    cur.close()
    conn.close()


if __name__ == '__main__':
    show_keibajo_index_stats()
    show_keibajo_comparison()
