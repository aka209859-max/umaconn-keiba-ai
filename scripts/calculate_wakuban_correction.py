"""
枠順補正計算スクリプト（実データベース版）

実データから競馬場・距離・枠番別の単勝的中率・複勝的中率を集計し、
枠順補正値を算出します。

データ期間:
- 通常の競馬場: 2016-01-01 〜 2025-12-31
- 大井（'44'）: 2023-10-01 〜 2025-12-31
- 名古屋（'48'）: 2022-04-01 〜 2025-12-31

作成日: 2026-01-09
作者: AI戦略家
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.db_config import get_db_connection
from typing import Dict, Tuple
import json

# データ期間設定
DATE_RANGES = {
    # 通常の競馬場
    'default': ('2016-01-01', '2025-12-31'),
    # 改修・移転後の競馬場
    '44': ('2023-10-01', '2025-12-31'),  # 大井（白砂全面置換）
    '48': ('2022-04-01', '2025-12-31'),  # 名古屋（大幅改修）
}

# 競馬場コード一覧（全場を含む）
KEIBAJO_CODES = [
    '30',  # 門別
    '33',  # 帯広（ばんえい専用）
    '35',  # 盛岡
    '36',  # 水沢
    '42',  # 浦和
    '43',  # 船橋
    '44',  # 大井（2023-10-01以降のデータで計算）
    '45',  # 川崎
    '46',  # 金沢
    '47',  # 笠松
    '48',  # 名古屋（2022-04-01以降のデータで計算）
    '50',  # 園田
    '51',  # 姫路
    '54',  # 高知
    '55',  # 佐賀
]

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


def get_date_range(keibajo_code: str) -> Tuple[str, str]:
    """競馬場コードに応じたデータ期間を取得"""
    return DATE_RANGES.get(keibajo_code, DATE_RANGES['default'])


def calculate_wakuban_correction():
    """実データから枠順補正を計算"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("枠順補正計算（実データベース版）")
    print("=" * 80)
    print()
    
    results = {}
    
    for keibajo_code in KEIBAJO_CODES:
        keibajo_name = KEIBAJO_NAMES[keibajo_code]
        start_date, end_date = get_date_range(keibajo_code)
        
        print(f"\n【{keibajo_name}（コード: {keibajo_code}）】")
        print(f"  データ期間: {start_date} 〜 {end_date}")
        print()
        
        # 距離別・枠番別の統計を取得
        query = """
        SELECT 
            ra.kyori AS 距離,
            se.wakuban AS 枠番,
            COUNT(*) AS レース数,
            SUM(CASE WHEN CAST(se.kakutei_chakujun AS INTEGER) = 1 THEN 1 ELSE 0 END) AS 単勝的中,
            SUM(CASE WHEN CAST(se.kakutei_chakujun AS INTEGER) <= 3 THEN 1 ELSE 0 END) AS 複勝的中,
            AVG(CASE WHEN CAST(se.kakutei_chakujun AS INTEGER) = 1 THEN CAST(se.tansho_odds AS NUMERIC) ELSE NULL END) AS 平均単勝オッズ,
            AVG(CASE WHEN CAST(se.kakutei_chakujun AS INTEGER) <= 3 THEN CAST(se.fukusho_odds AS NUMERIC) ELSE NULL END) AS 平均複勝オッズ,
            AVG(CAST(se.kakutei_chakujun AS NUMERIC)) AS 平均着順
        FROM nvd_ra ra
        JOIN nvd_se se ON ra.kaisai_nen = se.kaisai_nen 
                       AND ra.kaisai_tsukihi = se.kaisai_tsukihi
                       AND ra.keibajo_code = se.keibajo_code
                       AND ra.race_bango = se.race_bango
        WHERE ra.keibajo_code = %s
          AND ra.kaisai_nen || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 1 FOR 2), 2, '0') || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 3 FOR 2), 2, '0') >= %s
          AND ra.kaisai_nen || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 1 FOR 2), 2, '0') || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 3 FOR 2), 2, '0') <= %s
          AND se.wakuban IS NOT NULL
          AND se.wakuban != ''
          AND CAST(se.wakuban AS INTEGER) BETWEEN 1 AND 8
          AND se.kakutei_chakujun IS NOT NULL
          AND se.kakutei_chakujun != ''
          AND CAST(se.kakutei_chakujun AS INTEGER) > 0
        GROUP BY ra.kyori, se.wakuban
        ORDER BY ra.kyori, CAST(se.wakuban AS INTEGER)
        """
        
        cur.execute(query, (keibajo_code, start_date, end_date))
        rows = cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ データなし")
            continue
        
        # 距離別に集計
        kyori_stats = {}
        for row in rows:
            kyori = row[0]
            wakuban = row[1]
            race_count = row[2]
            win_count = row[3]
            place_count = row[4]
            avg_win_odds = row[5] if row[5] else 0.0
            avg_place_odds = row[6] if row[6] else 0.0
            avg_chakujun = row[7] if row[7] else 0.0
            
            if kyori not in kyori_stats:
                kyori_stats[kyori] = {}
            
            win_rate = (win_count / race_count * 100) if race_count > 0 else 0.0
            place_rate = (place_count / race_count * 100) if race_count > 0 else 0.0
            
            kyori_stats[kyori][wakuban] = {
                'race_count': race_count,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'avg_win_odds': float(avg_win_odds),
                'avg_place_odds': float(avg_place_odds),
                'avg_chakujun': float(avg_chakujun),
            }
        
        # 距離別に補正値を計算
        results[keibajo_code] = {}
        
        for kyori, waku_stats in sorted(kyori_stats.items()):
            # 全枠の平均的中率を計算
            total_races = sum(s['race_count'] for s in waku_stats.values())
            total_wins = sum(s['win_rate'] * s['race_count'] / 100 for s in waku_stats.values())
            avg_win_rate = (total_wins / total_races * 100) if total_races > 0 else 10.0
            
            print(f"  距離 {kyori:4d}m（レース数: {total_races:5d}, 平均単勝率: {avg_win_rate:5.2f}%）")
            
            results[keibajo_code][kyori] = {}
            
            for wakuban in range(1, 9):
                waku_str = str(wakuban)
                if waku_str in waku_stats:
                    stats = waku_stats[waku_str]
                    win_rate = stats['win_rate']
                    place_rate = stats['place_rate']
                    race_count = stats['race_count']
                    
                    # 補正値を計算（平均からの乖離を秒数に変換）
                    # 的中率が高い → 有利 → プラス補正
                    # 的中率が低い → 不利 → マイナス補正
                    
                    # 単勝率ベースの補正（1%あたり0.05秒）
                    win_correction = (win_rate - avg_win_rate) * 0.05
                    
                    # 複勝率ベースの補正（1%あたり0.02秒）
                    place_correction = (place_rate - (avg_win_rate * 3)) * 0.02
                    
                    # 総合補正値（重み: 単勝70%, 複勝30%）
                    correction = win_correction * 0.7 + place_correction * 0.3
                    
                    # レース数が少ない場合は補正値を小さくする
                    if race_count < 100:
                        correction *= (race_count / 100)
                    
                    results[keibajo_code][kyori][wakuban] = round(correction, 2)
                    
                    status = "有利" if correction > 0 else "不利" if correction < 0 else "平均"
                    
                    print(f"    枠{wakuban}: {win_rate:5.2f}% / {place_rate:5.2f}% "
                          f"({race_count:4d}R) → {correction:+6.2f}秒 ({status})")
                else:
                    results[keibajo_code][kyori][wakuban] = 0.0
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("計算完了")
    print("=" * 80)
    
    return results


def save_results(results: Dict):
    """結果をファイルに保存"""
    
    # JSON形式で保存
    output_file = project_root / 'output' / 'wakuban_correction.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON形式で保存: {output_file}")
    
    # Python辞書形式で保存
    output_py = project_root / 'config' / 'wakuban_correction.py'
    
    with open(output_py, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('枠順補正値（実データから計算）\n')
        f.write('\n')
        f.write('データ期間:\n')
        f.write('- 通常の競馬場: 2016-01-01 〜 2025-12-31\n')
        f.write('- 大井（\'44\'）: 2023-10-01 〜 2025-12-31\n')
        f.write('- 名古屋（\'48\'）: 2022-04-01 〜 2025-12-31\n')
        f.write('\n')
        f.write('作成日: 2026-01-09\n')
        f.write('"""\n\n')
        
        f.write('# 枠順補正値（秒単位）\n')
        f.write('# 構造: {競馬場コード: {距離: {枠番: 補正値}}}\n')
        f.write('# 正の値: 有利（タイムが速くなる）\n')
        f.write('# 負の値: 不利（タイムが遅くなる）\n')
        f.write('WAKUBAN_CORRECTION = ')
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write('\n\n\n')
        
        f.write('def get_wakuban_correction(keibajo_code: str, kyori: int, wakuban: int) -> float:\n')
        f.write('    """\n')
        f.write('    枠順補正値を取得\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        keibajo_code: 競馬場コード\n')
        f.write('        kyori: 距離（メートル）\n')
        f.write('        wakuban: 枠番（1-8）\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        補正値（秒）\n')
        f.write('    """\n')
        f.write('    if keibajo_code not in WAKUBAN_CORRECTION:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    if kyori not in WAKUBAN_CORRECTION[keibajo_code]:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    return WAKUBAN_CORRECTION[keibajo_code][kyori].get(wakuban, 0.0)\n')
    
    print(f"✅ Python形式で保存: {output_py}")


if __name__ == '__main__':
    results = calculate_wakuban_correction()
    save_results(results)
