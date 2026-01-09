"""
馬場差補正計算スクリプト（実データベース版）

実データから馬場状態別のタイム影響を集計し、
馬場差補正値を算出します。

馬場状態コード:
- '1': 良
- '2': 稍重
- '3': 重
- '4': 不良

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
    'default': ('2016-01-01', '2025-12-31'),
    '44': ('2023-10-01', '2025-12-31'),  # 大井
    '48': ('2022-04-01', '2025-12-31'),  # 名古屋
}

# 競馬場コード一覧
KEIBAJO_CODES = [
    '30', '33', '35', '36', '42', '43', '44', '45',
    '46', '47', '48', '50', '51', '54', '55'
]

# 競馬場名マッピング
KEIBAJO_NAMES = {
    '30': '門別', '33': '帯広', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋', '50': '園田',
    '51': '姫路', '54': '高知', '55': '佐賀',
}

# 馬場状態名マッピング
BABA_NAMES = {
    '1': '良',
    '2': '稍重',
    '3': '重',
    '4': '不良',
}


def get_date_range(keibajo_code: str) -> Tuple[str, str]:
    """競馬場コードに応じたデータ期間を取得"""
    return DATE_RANGES.get(keibajo_code, DATE_RANGES['default'])


def calculate_baba_correction():
    """実データから馬場差補正を計算"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("馬場差補正計算（実データベース版）")
    print("=" * 80)
    print()
    
    results = {}
    
    for keibajo_code in KEIBAJO_CODES:
        keibajo_name = KEIBAJO_NAMES[keibajo_code]
        start_date, end_date = get_date_range(keibajo_code)
        
        print(f"\n【{keibajo_name}（コード: {keibajo_code}）】")
        print(f"  データ期間: {start_date} 〜 {end_date}")
        print()
        
        # 距離別・馬場状態別の平均タイムを取得
        query = """
        SELECT 
            ra.kyori AS 距離,
            ra.baba_jotai AS 馬場状態,
            COUNT(*) AS レース数,
            AVG(CAST(se.soha_time AS NUMERIC) / 10.0) AS 平均走破タイム,
            AVG(CAST(se.zenhan_3f AS NUMERIC) / 10.0) AS 平均前半3F,
            AVG(CAST(se.kohan_3f AS NUMERIC) / 10.0) AS 平均後半3F,
            STDDEV(CAST(se.soha_time AS NUMERIC) / 10.0) AS 標準偏差
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
          AND ra.baba_jotai IN ('1', '2', '3', '4')
          AND se.soha_time IS NOT NULL
          AND se.soha_time != ''
          AND CAST(se.soha_time AS NUMERIC) > 0
          AND se.zenhan_3f IS NOT NULL
          AND se.zenhan_3f != ''
          AND CAST(se.zenhan_3f AS NUMERIC) > 0
          AND se.kohan_3f IS NOT NULL
          AND se.kohan_3f != ''
          AND CAST(se.kohan_3f AS NUMERIC) > 0
          AND se.kakutei_chakujun IS NOT NULL
          AND se.kakutei_chakujun != ''
          AND CAST(se.kakutei_chakujun AS INTEGER) > 0
        GROUP BY ra.kyori, ra.baba_jotai
        HAVING COUNT(*) >= 10
        ORDER BY ra.kyori, ra.baba_jotai
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
            baba_code = row[1]
            race_count = row[2]
            avg_time = row[3] if row[3] else 0.0
            avg_zenhan = row[4] if row[4] else 0.0
            avg_kohan = row[5] if row[5] else 0.0
            stddev = row[6] if row[6] else 0.0
            
            if kyori not in kyori_stats:
                kyori_stats[kyori] = {}
            
            kyori_stats[kyori][baba_code] = {
                'race_count': race_count,
                'avg_time': float(avg_time),
                'avg_zenhan': float(avg_zenhan),
                'avg_kohan': float(avg_kohan),
                'stddev': float(stddev),
            }
        
        # 距離別に補正値を計算
        results[keibajo_code] = {}
        
        for kyori, baba_stats in sorted(kyori_stats.items()):
            # 「良」を基準として、各馬場状態の補正値を計算
            if '1' not in baba_stats:
                continue
            
            base_time = baba_stats['1']['avg_time']
            base_zenhan = baba_stats['1']['avg_zenhan']
            base_kohan = baba_stats['1']['avg_kohan']
            
            print(f"  距離 {kyori:4d}m（基準: 良 = {base_time:.1f}秒）")
            
            results[keibajo_code][kyori] = {}
            
            for baba_code in ['1', '2', '3', '4']:
                baba_name = BABA_NAMES[baba_code]
                
                if baba_code in baba_stats:
                    stats = baba_stats[baba_code]
                    avg_time = stats['avg_time']
                    race_count = stats['race_count']
                    
                    # 補正値 = 実際のタイム - 基準タイム（良）
                    correction = avg_time - base_time
                    
                    # レース数が少ない場合は補正値を小さくする
                    if race_count < 50:
                        correction *= (race_count / 50)
                    
                    results[keibajo_code][kyori][baba_code] = round(correction, 2)
                    
                    print(f"    {baba_name}（'{baba_code}'）: {avg_time:6.1f}秒 "
                          f"({race_count:4d}R) → {correction:+6.2f}秒")
                else:
                    # データがない場合は0.0
                    results[keibajo_code][kyori][baba_code] = 0.0
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("計算完了")
    print("=" * 80)
    
    return results


def save_results(results: Dict):
    """結果をファイルに保存"""
    
    # JSON形式で保存
    output_file = project_root / 'output' / 'baba_correction.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON形式で保存: {output_file}")
    
    # Python辞書形式で保存
    output_py = project_root / 'config' / 'baba_correction.py'
    
    with open(output_py, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('馬場差補正値（実データから計算）\n')
        f.write('\n')
        f.write('馬場状態コード:\n')
        f.write('- \'1\': 良\n')
        f.write('- \'2\': 稍重\n')
        f.write('- \'3\': 重\n')
        f.write('- \'4\': 不良\n')
        f.write('\n')
        f.write('データ期間:\n')
        f.write('- 通常の競馬場: 2016-01-01 〜 2025-12-31\n')
        f.write('- 大井（\'44\'）: 2023-10-01 〜 2025-12-31\n')
        f.write('- 名古屋（\'48\'）: 2022-04-01 〜 2025-12-31\n')
        f.write('\n')
        f.write('作成日: 2026-01-09\n')
        f.write('"""\n\n')
        
        f.write('# 馬場差補正値（秒単位）\n')
        f.write('# 構造: {競馬場コード: {距離: {馬場状態コード: 補正値}}}\n')
        f.write('# 正の値: 馬場が悪くなるとタイムが遅くなる\n')
        f.write('# 負の値: 馬場が悪くなるとタイムが速くなる（稀）\n')
        f.write('BABA_CORRECTION = ')
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write('\n\n\n')
        
        f.write('def get_baba_correction(keibajo_code: str, kyori: int, baba_code: str) -> float:\n')
        f.write('    """\n')
        f.write('    馬場差補正値を取得\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        keibajo_code: 競馬場コード\n')
        f.write('        kyori: 距離（メートル）\n')
        f.write('        baba_code: 馬場状態コード（\'1\',\'2\',\'3\',\'4\'）\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        補正値（秒）\n')
        f.write('    """\n')
        f.write('    if keibajo_code not in BABA_CORRECTION:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    if kyori not in BABA_CORRECTION[keibajo_code]:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    return BABA_CORRECTION[keibajo_code][kyori].get(baba_code, 0.0)\n')
    
    print(f"✅ Python形式で保存: {output_py}")


if __name__ == '__main__':
    results = calculate_baba_correction()
    save_results(results)
