"""
ペース補正値の最適化スクリプト（実データベース版）

実データから「ペースタイプ（H/M/S）」ごとの後半3F差分を分析し、
最適な補正値を算出します。

現行値:
- ハイペース (H): -0.5秒
- スローペース (S): +0.5秒

目的:
- 実データから「ハイペース時、ダート馬は実際には何秒バテているのか？」を明らかにする
- 統計的に正しい補正値を導出

データ期間:
- 通常の競馬場: 2016-01-01 〜 2025-12-31
- 大井（'44'）: 2023-10-01 〜 2025-12-31（除外推奨）
- 名古屋（'48'）: 2022-04-01 〜 2025-12-31（除外推奨）

作成日: 2026-01-09
作者: AI戦略家
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.db_config import get_db_connection
from config.base_times import BASE_TIMES
from typing import Dict, Tuple
import json

# データ期間設定
DATE_RANGES = {
    'default': ('2016-01-01', '2025-12-31'),
    '44': ('2023-10-01', '2025-12-31'),  # 大井（除外推奨）
    '48': ('2022-04-01', '2025-12-31'),  # 名古屋（除外推奨）
}

# 競馬場コード一覧（大井・名古屋を除く）
KEIBAJO_CODES = [
    '30',  # 門別
    # '33',  # 帯広（ばんえい専用）
    '35',  # 盛岡
    '36',  # 水沢
    '42',  # 浦和
    '43',  # 船橋
    # '44',  # 大井（除外）
    '45',  # 川崎
    '46',  # 金沢
    '47',  # 笠松
    # '48',  # 名古屋（除外）
    '50',  # 園田
    '51',  # 姫路
    '54',  # 高知
    '55',  # 佐賀
]

# 競馬場名マッピング
KEIBAJO_NAMES = {
    '30': '門別', '33': '帯広', '35': '盛岡', '36': '水沢',
    '42': '浦和', '43': '船橋', '44': '大井', '45': '川崎',
    '46': '金沢', '47': '笠松', '48': '名古屋', '50': '園田',
    '51': '姫路', '54': '高知', '55': '佐賀',
}


def get_date_range(keibajo_code: str) -> Tuple[str, str]:
    """競馬場コードに応じたデータ期間を取得"""
    return DATE_RANGES.get(keibajo_code, DATE_RANGES['default'])


def judge_pace_type(zenhan_3f: float, kohan_3f: float, keibajo_code: str, kyori: int) -> str:
    """
    ペースタイプを判定
    
    Args:
        zenhan_3f: 前半3Fタイム（秒）
        kohan_3f: 後半3Fタイム（秒）
        keibajo_code: 競馬場コード
        kyori: 距離（m）
    
    Returns:
        ペースタイプ ('H', 'M', 'S')
    """
    # BASE_TIMESから基準タイムを取得
    if keibajo_code not in BASE_TIMES:
        return 'M'
    
    if kyori not in BASE_TIMES[keibajo_code]:
        return 'M'
    
    base_times = BASE_TIMES[keibajo_code][kyori]
    base_zenhan = base_times.get('zenhan_3f', 0)
    base_kohan = base_times.get('kohan_3f', 0)
    
    if base_zenhan <= 0 or base_kohan <= 0:
        return 'M'
    
    # ペース比率の計算
    pace_ratio = zenhan_3f / kohan_3f if kohan_3f > 0 else 1.0
    base_pace_ratio = base_zenhan / base_kohan
    
    # 差分
    pace_diff = pace_ratio - base_pace_ratio
    
    # ペースタイプ判定
    if pace_diff >= 0.03:
        return 'H'  # ハイペース
    elif pace_diff <= -0.03:
        return 'S'  # スローペース
    else:
        return 'M'  # ミドルペース


def calculate_pace_correction():
    """実データからペース補正値を計算"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("ペース補正値計算（実データベース版）")
    print("=" * 80)
    print()
    print("分析対象: 2016年〜2025年の地方競馬全レース（大井・名古屋を除く）")
    print()
    
    # 全競馬場のデータを統合して分析
    query = """
    WITH base_data AS (
        SELECT 
            ra.keibajo_code,
            ra.kyori,
            CAST(se.zenhan_3f AS NUMERIC) / 10.0 AS zenhan_3f,
            CAST(se.kohan_3f AS NUMERIC) / 10.0 AS kohan_3f,
            CAST(se.kakutei_chakujun AS INTEGER) AS chakujun,
            CAST(se.soha_time AS NUMERIC) / 10.0 AS soha_time
        FROM nvd_ra ra
        JOIN nvd_se se ON ra.kaisai_nen = se.kaisai_nen 
                       AND ra.kaisai_tsukihi = se.kaisai_tsukihi
                       AND ra.keibajo_code = se.keibajo_code
                       AND ra.race_bango = se.race_bango
        WHERE ra.keibajo_code = ANY(%s)
          AND ra.kaisai_nen || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 1 FOR 2), 2, '0') || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 3 FOR 2), 2, '0') >= '2016-01-01'
          AND ra.kaisai_nen || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 1 FOR 2), 2, '0') || '-' || 
              LPAD(SUBSTRING(ra.kaisai_tsukihi FROM 3 FOR 2), 2, '0') <= '2025-12-31'
          AND se.zenhan_3f IS NOT NULL
          AND se.zenhan_3f != ''
          AND CAST(se.zenhan_3f AS NUMERIC) > 0
          AND se.kohan_3f IS NOT NULL
          AND se.kohan_3f != ''
          AND CAST(se.kohan_3f AS NUMERIC) > 0
          AND se.kakutei_chakujun IS NOT NULL
          AND se.kakutei_chakujun != ''
          AND CAST(se.kakutei_chakujun AS INTEGER) > 0
          AND se.soha_time IS NOT NULL
          AND se.soha_time != ''
          AND CAST(se.soha_time AS NUMERIC) > 0
    )
    SELECT 
        keibajo_code,
        kyori,
        zenhan_3f,
        kohan_3f,
        chakujun,
        soha_time
    FROM base_data
    """
    
    cur.execute(query, (KEIBAJO_CODES,))
    rows = cur.fetchall()
    
    print(f"✅ データ取得完了: {len(rows):,} 頭のデータ")
    print()
    
    # ペースタイプごとに分類
    pace_stats = {
        'H': {'kohan_list': [], 'win_count': 0, 'race_count': 0},
        'M': {'kohan_list': [], 'win_count': 0, 'race_count': 0},
        'S': {'kohan_list': [], 'win_count': 0, 'race_count': 0},
    }
    
    # 競馬場・距離ごとの基準後半3Fを計算
    base_kohan_cache = {}
    
    for row in rows:
        keibajo_code = row[0]
        kyori = row[1]
        zenhan_3f = row[2]
        kohan_3f = row[3]
        chakujun = row[4]
        soha_time = row[5]
        
        # BASE_TIMESから基準後半3Fを取得
        cache_key = f"{keibajo_code}_{kyori}"
        if cache_key not in base_kohan_cache:
            if keibajo_code in BASE_TIMES and kyori in BASE_TIMES[keibajo_code]:
                base_kohan_cache[cache_key] = BASE_TIMES[keibajo_code][kyori].get('kohan_3f', 0)
            else:
                base_kohan_cache[cache_key] = 0
        
        base_kohan = base_kohan_cache[cache_key]
        
        if base_kohan <= 0:
            continue
        
        # ペースタイプ判定
        pace_type = judge_pace_type(zenhan_3f, kohan_3f, keibajo_code, kyori)
        
        # 後半3F差分（実走 - 基準）
        kohan_diff = kohan_3f - base_kohan
        
        pace_stats[pace_type]['kohan_list'].append(kohan_diff)
        pace_stats[pace_type]['race_count'] += 1
        
        if chakujun == 1:
            pace_stats[pace_type]['win_count'] += 1
    
    # 統計を表示
    print("=" * 80)
    print("ペースタイプ別の統計")
    print("=" * 80)
    print()
    
    results = {}
    
    for pace_type in ['H', 'M', 'S']:
        stats = pace_stats[pace_type]
        count = stats['race_count']
        win_count = stats['win_count']
        kohan_list = stats['kohan_list']
        
        if count == 0:
            continue
        
        # 平均差分
        avg_diff = sum(kohan_list) / count
        
        # 単勝率
        win_rate = (win_count / count * 100) if count > 0 else 0.0
        
        pace_name = {
            'H': 'ハイペース',
            'M': 'ミドルペース',
            'S': 'スローペース'
        }[pace_type]
        
        print(f"{pace_name}（{pace_type}）:")
        print(f"  レース数: {count:,} 頭")
        print(f"  単勝率: {win_rate:.2f}%")
        print(f"  後半3F平均差分: {avg_diff:+.3f}秒（実走 - 基準）")
        
        # 推奨補正値（上がり指数への補正）
        # 基準より遅い → プラス補正（ハンデ）
        # 基準より速い → マイナス補正（ペナルティ）
        recommended_correction = -avg_diff
        
        print(f"  推奨補正値: {recommended_correction:+.3f}秒")
        print()
        
        results[pace_type] = {
            'race_count': count,
            'win_rate': round(win_rate, 2),
            'avg_kohan_diff': round(avg_diff, 3),
            'recommended_correction': round(recommended_correction, 3),
        }
    
    cur.close()
    conn.close()
    
    print("=" * 80)
    print("計算完了")
    print("=" * 80)
    
    return results


def save_results(results: Dict):
    """結果をファイルに保存"""
    
    # JSON形式で保存
    output_file = project_root / 'output' / 'pace_correction_optimal.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON形式で保存: {output_file}")
    
    # Python辞書形式で保存
    output_py = project_root / 'config' / 'pace_correction_optimal.py'
    
    with open(output_py, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('ペース補正値（実データから計算）\n')
        f.write('\n')
        f.write('ペースタイプ:\n')
        f.write('- H: ハイペース（前半速い → 後半バテる）\n')
        f.write('- M: ミドルペース（標準的なペース配分）\n')
        f.write('- S: スローペース（前半遅い → 後半余力あり）\n')
        f.write('\n')
        f.write('データ期間: 2016-01-01 〜 2025-12-31\n')
        f.write('対象: 地方競馬全場（大井・名古屋を除く）\n')
        f.write('\n')
        f.write('作成日: 2026-01-09\n')
        f.write('"""\n\n')
        
        f.write('# ペース補正値（秒単位）\n')
        f.write('# 上がり指数に加算する補正値\n')
        f.write('# 正の値: ハンデ（タイムが遅くなる要因）\n')
        f.write('# 負の値: ペナルティ（タイムが速くなる要因）\n')
        f.write('PACE_CORRECTION = {\n')
        f.write(f'    "H": {results["H"]["recommended_correction"]},  # ハイペース\n')
        f.write(f'    "M": {results["M"]["recommended_correction"]},  # ミドルペース\n')
        f.write(f'    "S": {results["S"]["recommended_correction"]},  # スローペース\n')
        f.write('}\n\n\n')
        
        f.write('def get_pace_correction(pace_type: str) -> float:\n')
        f.write('    """\n')
        f.write('    ペース補正値を取得\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        pace_type: ペースタイプ（\'H\', \'M\', \'S\'）\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        補正値（秒）\n')
        f.write('    """\n')
        f.write('    return PACE_CORRECTION.get(pace_type, 0.0)\n')
    
    print(f"✅ Python形式で保存: {output_py}")


if __name__ == '__main__':
    results = calculate_pace_correction()
    save_results(results)
