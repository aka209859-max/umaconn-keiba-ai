"""
馬体重補正計算スクリプト（実データベース版・レース内相対値）

実データから馬体重とレース結果の関係を分析し、
レース内での相対的な馬体重による補正値を算出します。

馬体重カテゴリ:
- 最軽量: レース内で最も軽い
- 平均以下: レース平均より軽い
- 平均: レース平均±5kg
- 平均以上: レース平均より重い
- 最重量: レース内で最も重い

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
from typing import Dict, Tuple, List
import json

# データ期間設定
DATE_RANGES = {
    'default': ('2016-01-01', '2025-12-31'),
    '44': ('2023-10-01', '2025-12-31'),  # 大井
    '48': ('2022-04-01', '2025-12-31'),  # 名古屋
}

# 競馬場コード一覧（全場を含む）
KEIBAJO_CODES = [
    '30', '33', '35', '36', '42', '43', 
    '44',  # 大井（2023-10-01以降のデータで計算）
    '45', '46', '47', 
    '48',  # 名古屋（2022-04-01以降のデータで計算）
    '50', '51', '54', '55'
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


def calculate_bataiju_correction():
    """実データから馬体重補正を計算（レース内相対値）"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 80)
    print("馬体重補正計算（実データベース版・レース内相対値）")
    print("=" * 80)
    print()
    
    results = {}
    
    for keibajo_code in KEIBAJO_CODES:
        keibajo_name = KEIBAJO_NAMES[keibajo_code]
        start_date, end_date = get_date_range(keibajo_code)
        
        print(f"\n【{keibajo_name}（コード: {keibajo_code}）】")
        print(f"  データ期間: {start_date} 〜 {end_date}")
        print()
        
        # レースごとの馬体重データを取得
        query = """
        WITH race_stats AS (
            SELECT 
                ra.kaisai_nen,
                ra.kaisai_tsukihi,
                ra.keibajo_code,
                ra.race_bango,
                ra.kyori,
                AVG(CAST(se.bataiju AS NUMERIC)) AS avg_bataiju,
                MIN(CAST(se.bataiju AS NUMERIC)) AS min_bataiju,
                MAX(CAST(se.bataiju AS NUMERIC)) AS max_bataiju,
                STDDEV(CAST(se.bataiju AS NUMERIC)) AS stddev_bataiju
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
              AND se.bataiju IS NOT NULL
              AND se.bataiju != ''
              AND CAST(se.bataiju AS NUMERIC) > 0
              AND se.kakutei_chakujun IS NOT NULL
              AND se.kakutei_chakujun != ''
              AND CAST(se.kakutei_chakujun AS INTEGER) > 0
            GROUP BY ra.kaisai_nen, ra.kaisai_tsukihi, ra.keibajo_code, ra.race_bango, ra.kyori
            HAVING COUNT(*) >= 5
        )
        SELECT 
            rs.kyori,
            se.bataiju,
            rs.avg_bataiju,
            rs.min_bataiju,
            rs.max_bataiju,
            se.kakutei_chakujun,
            se.soha_time,
            CASE 
                WHEN CAST(se.bataiju AS NUMERIC) = rs.min_bataiju THEN 'min'
                WHEN CAST(se.bataiju AS NUMERIC) < rs.avg_bataiju - 5 THEN 'below_avg'
                WHEN CAST(se.bataiju AS NUMERIC) BETWEEN rs.avg_bataiju - 5 AND rs.avg_bataiju + 5 THEN 'avg'
                WHEN CAST(se.bataiju AS NUMERIC) > rs.avg_bataiju + 5 THEN 'above_avg'
                WHEN CAST(se.bataiju AS NUMERIC) = rs.max_bataiju THEN 'max'
                ELSE 'avg'
            END AS category
        FROM race_stats rs
        JOIN nvd_se se ON rs.kaisai_nen = se.kaisai_nen 
                       AND rs.kaisai_tsukihi = se.kaisai_tsukihi
                       AND rs.keibajo_code = se.keibajo_code
                       AND rs.race_bango = se.race_bango
        WHERE se.bataiju IS NOT NULL
          AND se.bataiju != ''
          AND CAST(se.bataiju AS NUMERIC) > 0
          AND se.kakutei_chakujun IS NOT NULL
          AND se.kakutei_chakujun != ''
          AND CAST(se.kakutei_chakujun AS INTEGER) > 0
          AND se.soha_time IS NOT NULL
          AND se.soha_time != ''
          AND CAST(se.soha_time AS NUMERIC) > 0
        """
        
        cur.execute(query, (keibajo_code, start_date, end_date))
        rows = cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ データなし")
            continue
        
        # 距離別・カテゴリ別に集計
        kyori_stats = {}
        for row in rows:
            kyori = row[0]
            bataiju = row[1]
            avg_bataiju = row[2]
            min_bataiju = row[3]
            max_bataiju = row[4]
            chakujun = row[5]
            soha_time = row[6]
            category = row[7]
            
            if kyori not in kyori_stats:
                kyori_stats[kyori] = {
                    'min': [],
                    'below_avg': [],
                    'avg': [],
                    'above_avg': [],
                    'max': []
                }
            
            kyori_stats[kyori][category].append({
                'bataiju': float(bataiju),
                'chakujun': int(chakujun),
                'soha_time': float(soha_time) / 10.0,
            })
        
        # 距離別に補正値を計算
        results[keibajo_code] = {}
        
        for kyori, cat_stats in sorted(kyori_stats.items()):
            print(f"  距離 {kyori:4d}m")
            
            # 平均カテゴリを基準とする
            if not cat_stats['avg']:
                continue
            
            avg_chakujun = sum(h['chakujun'] for h in cat_stats['avg']) / len(cat_stats['avg'])
            avg_time = sum(h['soha_time'] for h in cat_stats['avg']) / len(cat_stats['avg'])
            
            results[keibajo_code][kyori] = {}
            
            for category in ['min', 'below_avg', 'avg', 'above_avg', 'max']:
                if not cat_stats[category]:
                    results[keibajo_code][kyori][category] = 0.0
                    continue
                
                cat_chakujun = sum(h['chakujun'] for h in cat_stats[category]) / len(cat_stats[category])
                cat_time = sum(h['soha_time'] for h in cat_stats[category]) / len(cat_stats[category])
                count = len(cat_stats[category])
                
                # 補正値 = 基準タイム - カテゴリタイム
                # 速い → プラス補正、遅い → マイナス補正
                correction = avg_time - cat_time
                
                # レース数が少ない場合は補正値を小さくする
                if count < 100:
                    correction *= (count / 100)
                
                results[keibajo_code][kyori][category] = round(correction, 2)
                
                category_name = {
                    'min': '最軽量',
                    'below_avg': '平均以下',
                    'avg': '平均',
                    'above_avg': '平均以上',
                    'max': '最重量'
                }[category]
                
                status = "速い" if correction > 0 else "遅い" if correction < 0 else "平均"
                
                print(f"    {category_name:8s}: 平均着順{cat_chakujun:4.1f} "
                      f"({count:5d}頭) → {correction:+6.2f}秒 ({status})")
    
    cur.close()
    conn.close()
    
    print("\n" + "=" * 80)
    print("計算完了")
    print("=" * 80)
    
    return results


def save_results(results: Dict):
    """結果をファイルに保存"""
    
    # JSON形式で保存
    output_file = project_root / 'output' / 'bataiju_correction.json'
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ JSON形式で保存: {output_file}")
    
    # Python辞書形式で保存
    output_py = project_root / 'config' / 'bataiju_correction.py'
    
    with open(output_py, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('馬体重補正値（実データから計算・レース内相対値）\n')
        f.write('\n')
        f.write('カテゴリ:\n')
        f.write('- min: 最軽量（レース内で最も軽い）\n')
        f.write('- below_avg: 平均以下（レース平均より軽い）\n')
        f.write('- avg: 平均（レース平均±5kg）\n')
        f.write('- above_avg: 平均以上（レース平均より重い）\n')
        f.write('- max: 最重量（レース内で最も重い）\n')
        f.write('\n')
        f.write('データ期間:\n')
        f.write('- 通常の競馬場: 2016-01-01 〜 2025-12-31\n')
        f.write('- 大井（\'44\'）: 2023-10-01 〜 2025-12-31\n')
        f.write('- 名古屋（\'48\'）: 2022-04-01 〜 2025-12-31\n')
        f.write('\n')
        f.write('作成日: 2026-01-09\n')
        f.write('"""\n\n')
        
        f.write('# 馬体重補正値（秒単位）\n')
        f.write('# 構造: {競馬場コード: {距離: {カテゴリ: 補正値}}}\n')
        f.write('# 正の値: 有利（タイムが速い）\n')
        f.write('# 負の値: 不利（タイムが遅い）\n')
        f.write('BATAIJU_CORRECTION = ')
        f.write(json.dumps(results, ensure_ascii=False, indent=2))
        f.write('\n\n\n')
        
        f.write('def get_bataiju_category(bataiju: float, race_avg: float, race_min: float, race_max: float) -> str:\n')
        f.write('    """\n')
        f.write('    馬体重カテゴリを判定\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        bataiju: 馬体重（kg）\n')
        f.write('        race_avg: レース平均馬体重（kg）\n')
        f.write('        race_min: レース最軽量（kg）\n')
        f.write('        race_max: レース最重量（kg）\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        カテゴリ（\'min\', \'below_avg\', \'avg\', \'above_avg\', \'max\'）\n')
        f.write('    """\n')
        f.write('    if bataiju == race_min:\n')
        f.write('        return "min"\n')
        f.write('    elif bataiju == race_max:\n')
        f.write('        return "max"\n')
        f.write('    elif bataiju < race_avg - 5:\n')
        f.write('        return "below_avg"\n')
        f.write('    elif bataiju > race_avg + 5:\n')
        f.write('        return "above_avg"\n')
        f.write('    else:\n')
        f.write('        return "avg"\n')
        f.write('\n\n')
        
        f.write('def get_bataiju_correction(keibajo_code: str, kyori: int, category: str) -> float:\n')
        f.write('    """\n')
        f.write('    馬体重補正値を取得\n')
        f.write('    \n')
        f.write('    Args:\n')
        f.write('        keibajo_code: 競馬場コード\n')
        f.write('        kyori: 距離（メートル）\n')
        f.write('        category: カテゴリ（\'min\', \'below_avg\', \'avg\', \'above_avg\', \'max\'）\n')
        f.write('    \n')
        f.write('    Returns:\n')
        f.write('        補正値（秒）\n')
        f.write('    """\n')
        f.write('    if keibajo_code not in BATAIJU_CORRECTION:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    if kyori not in BATAIJU_CORRECTION[keibajo_code]:\n')
        f.write('        return 0.0\n')
        f.write('    \n')
        f.write('    return BATAIJU_CORRECTION[keibajo_code][kyori].get(category, 0.0)\n')
    
    print(f"✅ Python形式で保存: {output_py}")


if __name__ == '__main__':
    results = calculate_bataiju_correction()
    save_results(results)
