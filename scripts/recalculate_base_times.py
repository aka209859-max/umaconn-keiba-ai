"""
基準タイムの再計算スクリプト

実データから競馬場別・距離別の基準タイムを算出します。
- 各競馬場・距離ごとに上位30%の平均タイムを新基準タイムとする
- zenhan_3f（前半3F）と kohan_3f（後半3F）を分けて計算
- 出力: config/base_times_recalculated.py

作成日: 2026-01-09
作成者: AI戦略家
"""

import sys
from pathlib import Path
from collections import defaultdict
import json
import os

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.db_config import get_db_connection

# safe_int ヘルパー関数
def safe_int(value, default: int = 0) -> int:
    """安全なint変換"""
    try:
        if value is None or value == '' or value == '00':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

# データ期間設定（競馬場コード修正後）
DATE_RANGES = {
    'default': ('2016-01-01', '2025-12-31'),
    '44': ('2023-10-01', '2025-12-31'),  # 大井（白砂全面置換後）
    '48': ('2022-04-01', '2025-12-31'),  # 名古屋（移転後）
}

# 競馬場コード一覧
KEIBAJO_CODES = [
    '30',  # 門別
    '35',  # 盛岡
    '36',  # 水沢
    '42',  # 浦和
    '43',  # 船橋
    '44',  # 大井
    '45',  # 川崎
    '46',  # 金沢
    '47',  # 笠松
    '48',  # 名古屋
    '50',  # 園田
    '51',  # 姫路
    '54',  # 高知
    '55',  # 佐賀
]

# 競馬場名マッピング
KEIBAJO_NAMES = {
    '30': '門別',
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


def get_date_range(keibajo_code):
    """競馬場コードに応じた集計期間を取得"""
    return DATE_RANGES.get(keibajo_code, DATE_RANGES['default'])


def recalculate_base_times():
    """基準タイムを実データから再計算"""
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    print("=" * 100)
    print("基準タイムの再計算（実データ分析）")
    print("=" * 100)
    print()
    
    # 競馬場別・距離別の基準タイム格納
    base_times_data = {}
    
    for keibajo_code in KEIBAJO_CODES:
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, f'不明({keibajo_code})')
        start_date, end_date = get_date_range(keibajo_code)
        
        print(f"\n{'=' * 100}")
        print(f"【{keibajo_name}（{keibajo_code}）】 データ期間: {start_date} 〜 {end_date}")
        print('=' * 100)
        
        # 距離別のタイムデータを取得
        # zenhan_3fの算出方法:
        # - 1200m未満: zenhan_3f = 走破タイム - 後半3F = 「前半3F（仮）」
        # - 1200m: zenhan_3f = 走破タイム - 後半3F = 「前半3F（実測値）」
        # - 1201m以上: zenhan_3f = 独自ロジックの予測値（ten_3f_estimator.pyで算出）
        # 
        # 重要: テン指数は全競馬場の全距離に適用されるため、全距離のデータを取得
        query = """
        SELECT 
            CAST(ra.kyori AS INTEGER) AS kyori,
            se.soha_time,
            se.kohan_3f,
            se.corner_1,
            se.corner_2,
            ra.grade_code
        FROM nvd_ra ra
        JOIN nvd_se se ON 
            ra.kaisai_nen = se.kaisai_nen AND
            ra.kaisai_tsukihi = se.kaisai_tsukihi AND
            ra.keibajo_code = se.keibajo_code AND
            ra.race_bango = se.race_bango
        WHERE ra.keibajo_code = %s
          AND ra.kaisai_nen || ra.kaisai_tsukihi >= %s
          AND ra.kaisai_nen || ra.kaisai_tsukihi <= %s
          AND se.kakutei_chakujun IS NOT NULL
          AND se.kakutei_chakujun != ''
          AND se.kakutei_chakujun ~ '^[0-9]+$'
          AND CAST(se.kakutei_chakujun AS INTEGER) BETWEEN 1 AND 3
          AND se.soha_time IS NOT NULL
          AND se.kohan_3f IS NOT NULL
          AND se.soha_time ~ '^[0-9]+$'
          AND se.kohan_3f ~ '^[0-9]+$'
        """
        
        # 日付フォーマットを YYYYMMDD に変換
        start_date_formatted = start_date.replace('-', '')
        end_date_formatted = end_date.replace('-', '')
        
        cur.execute(query, (keibajo_code, start_date_formatted, end_date_formatted))
        rows = cur.fetchall()
        
        if not rows:
            print(f"  ⚠️ データなし")
            continue
        
        # 距離別・クラス別にデータを集計
        distance_class_data = defaultdict(lambda: defaultdict(lambda: {'zenhan_3f': [], 'kohan_3f': []}))
        
        for row in rows:
            kyori = row[0]
            soha_time_str = str(row[1])
            kohan_3f_str = str(row[2])
            corner_1 = safe_int(row[3]) if len(row) > 3 else None
            corner_2 = safe_int(row[4]) if len(row) > 4 else None
            grade_code = str(row[5]).strip() if len(row) > 5 else ''
            
            try:
                # soha_time の変換（mSSd形式）
                # 重要: 3桁の場合（598など）に対応するため、左を0埋めして4桁にする
                soha_padded = soha_time_str.zfill(4)
                
                minutes = int(soha_padded[0:1])       # 1桁目: 分
                seconds = int(soha_padded[1:3])       # 2-3桁目: 秒
                deciseconds = int(soha_padded[3:4])   # 4桁目: 0.1秒
                
                soha_seconds = (minutes * 60) + seconds + (deciseconds / 10.0)
                
                # kohan_3f の変換（SSS形式）
                kohan_seconds = float(kohan_3f_str) / 10.0
                
                # zenhan_3f の算出
                if kyori <= 1200:
                    # 1200m以下: 走破タイム - 後半3F
                    zenhan_3f = soha_seconds - kohan_seconds
                else:
                    # 1201m以上: ten_3f_estimator.py で推定
                    from core.ten_3f_estimator import Ten3FEstimator
                    estimator = Ten3FEstimator()
                    result = estimator.estimate(
                        time_seconds=soha_seconds,
                        kohan_3f_seconds=kohan_seconds,
                        kyori=kyori,
                        corner_1=corner_1,
                        corner_2=corner_2,
                        use_ml=False,  # MLモデルなしでベースライン推定のみ
                        keibajo_code=keibajo_code,
                        grade_code=grade_code  # クラス情報あり（正確な推定）
                    )
                    zenhan_3f = result['ten_3f_final']
                
                # クラス名を取得（PCkeiba公式準拠）
                if grade_code == 'E':
                    class_name = 'E級'
                elif grade_code in ['A', 'B', 'C', 'D', 'P', 'Q', 'R', 'S', 'T']:
                    class_name = '上位クラス'
                else:
                    class_name = '一般戦'
                
                # データ検証: kohan_3fは30-50秒、zenhan_3fは正の値であればOK
                if zenhan_3f > 0 and 30.0 <= kohan_seconds <= 50.0:
                    distance_class_data[kyori][class_name]['zenhan_3f'].append(zenhan_3f)
                    distance_class_data[kyori][class_name]['kohan_3f'].append(kohan_seconds)
            except (ValueError, IndexError, ZeroDivisionError):
                # 変換エラーは無視
                continue
        
        # 距離別・クラス別の基準タイムを計算
        base_times_data[keibajo_code] = {}
        
        for kyori in sorted(distance_class_data.keys()):
            print(f"\n  【{kyori}m】")
            base_times_data[keibajo_code][kyori] = {}
            
            for class_name in ['上位クラス', 'E級', '一般戦']:
                if class_name not in distance_class_data[kyori]:
                    continue
                
                zenhan_list = sorted(distance_class_data[kyori][class_name]['zenhan_3f'])
                kohan_list = sorted(distance_class_data[kyori][class_name]['kohan_3f'])
                
                if not zenhan_list or not kohan_list:
                    continue
                
                # 上位30%の平均を基準タイムとする
                zenhan_top30_count = max(1, int(len(zenhan_list) * 0.3))
                kohan_top30_count = max(1, int(len(kohan_list) * 0.3))
                
                zenhan_top30 = zenhan_list[:zenhan_top30_count]
                kohan_top30 = kohan_list[:kohan_top30_count]
                
                zenhan_avg = sum(zenhan_top30) / len(zenhan_top30)
                kohan_avg = sum(kohan_top30) / len(kohan_top30)
                
                base_times_data[keibajo_code][kyori][class_name] = {
                    'zenhan_3f': round(zenhan_avg, 1),
                    'kohan_3f': round(kohan_avg, 1),
                }
                
                print(f"    {class_name:8s}: 前半3F={zenhan_avg:.1f}秒 (N={len(zenhan_top30):4d}), "
                      f"後半3F={kohan_avg:.1f}秒 (N={len(kohan_top30):4d})")
    
    cur.close()
    conn.close()
    
    # 出力ファイルを生成（クラス別基準タイム）
    output_file = project_root / 'config' / 'base_times_recalculated_by_class.py'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('"""\n')
        f.write('基準タイム（実データ分析に基づく再計算版・クラス別）\n')
        f.write('\n')
        f.write('各競馬場・距離・クラスごとに上位30%の平均タイムを基準タイムとして設定\n')
        f.write('- データ期間: 通常 2016-01-01 〜 2025-12-31\n')
        f.write('- 大井（44）: 2023-10-01 〜 2025-12-31（白砂全面置換後）\n')
        f.write('- 名古屋（48）: 2022-04-01 〜 2025-12-31（移転後）\n')
        f.write('\n')
        f.write('クラス分類（PCkeiba公式準拠）:\n')
        f.write('- 上位クラス: A/B/C/D/P/Q/R/S/T\n')
        f.write('- E級: E\n')
        f.write('- 一般戦: その他\n')
        f.write('\n')
        f.write('作成日: 2026-01-09\n')
        f.write('作成者: 基準タイム再計算スクリプト（クラス別版）\n')
        f.write('"""\n')
        f.write('\n')
        f.write('BASE_TIMES_BY_CLASS = {\n')
        
        for keibajo_code in sorted(base_times_data.keys()):
            keibajo_name = KEIBAJO_NAMES.get(keibajo_code, keibajo_code)
            f.write(f"    '{keibajo_code}': {{  # {keibajo_name}\n")
            
            for kyori in sorted(base_times_data[keibajo_code].keys()):
                f.write(f"        {kyori}: {{\n")
                
                for class_name in ['上位クラス', 'E級', '一般戦']:
                    if class_name in base_times_data[keibajo_code][kyori]:
                        zenhan = base_times_data[keibajo_code][kyori][class_name]['zenhan_3f']
                        kohan = base_times_data[keibajo_code][kyori][class_name]['kohan_3f']
                        f.write(f"            '{class_name}': {{'zenhan_3f': {zenhan}, 'kohan_3f': {kohan}}},\n")
                
                f.write('        },\n')
            
            f.write('    },\n')
        
        f.write('}\n')
    
    # JSON出力（クラス別）
    output_json = project_root / 'output' / 'base_times_recalculated_by_class.json'
    output_json.parent.mkdir(exist_ok=True)
    
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(base_times_data, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 100)
    print(f"✅ 基準タイムの再計算が完了しました（クラス別）")
    print(f"出力ファイル:")
    print(f"  - {output_file}")
    print(f"  - {output_json}")
    print("=" * 100)


if __name__ == '__main__':
    recalculate_base_times()
