#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config/base_times.py 自動更新スクリプト
CEO用：v11の結果を自動的にconfig/base_times.pyに反映
"""

import sys
import os
import shutil
from datetime import datetime

# プロジェクトルートを設定
project_root = r'E:\UmaData\nar-analytics-python-v2'
sys.path.insert(0, project_root)

def update_base_times():
    """v11の結果からconfig/base_times.pyを更新"""
    
    # ファイルパス
    output_dir = os.path.join(project_root, 'output')
    config_dir = os.path.join(project_root, 'config')
    
    # 最新のresultファイルを探す
    result_files = [f for f in os.listdir(output_dir) if f.startswith('base_times_result_') and f.endswith('.txt')]
    if not result_files:
        print("❌ エラー: outputディレクトリにbase_times_result_*.txtが見つかりません")
        return False
    
    # 最新のファイルを取得
    result_files.sort(reverse=True)
    latest_result = os.path.join(output_dir, result_files[0])
    
    print(f"📂 最新の結果ファイル: {result_files[0]}")
    
    # resultファイルからBASE_TIMESを抽出
    with open(latest_result, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # BASE_TIMES の開始位置を探す
    start_marker = 'BASE_TIMES = {'
    start_pos = content.find(start_marker)
    
    if start_pos == -1:
        print("❌ エラー: BASE_TIMES が見つかりません")
        return False
    
    # BASE_TIMES の終了位置を探す（最後の }）
    end_marker = '\n}\n'
    end_pos = content.find(end_marker, start_pos)
    
    if end_pos == -1:
        print("❌ エラー: BASE_TIMES の終了が見つかりません")
        return False
    
    # BASE_TIMES を抽出
    base_times_content = content[start_pos:end_pos + len(end_marker)]
    
    print(f"✅ BASE_TIMES を抽出しました（{len(base_times_content)}文字）")
    
    # config/base_times.py のバックアップを作成
    base_times_py = os.path.join(config_dir, 'base_times.py')
    
    if os.path.exists(base_times_py):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(config_dir, f'base_times_backup_{timestamp}.py')
        shutil.copy2(base_times_py, backup_file)
        print(f"💾 バックアップ作成: {os.path.basename(backup_file)}")
    
    # 新しいconfig/base_times.pyを作成
    new_content = f'''"""
地方競馬全14競馬場の基準タイム設定（実データ版 - v14）

✅ 競馬場コード修正完了（公式発表の正しいコード）
✅ 実データから算出（{result_files[0].replace('base_times_result_', '').replace('.txt', '')}）
✅ 特殊期間フィルタ適用済み
  - 大井（'44'）: 2023-10-01 以降（オーストラリア産白砂への全面置換）
  - 名古屋（'48'）: 2022-04-01 以降（大幅改修実施）
✅ soha_time（実測走破タイム）追加
✅ 1200m厳密計算（median_zenhan_3f = median_soha_time - median_kohan_3f）

データ構造:
{{
  'keibajo_code': {{
    kyori: {{
      'soha_time': float,      # 実測走破タイム（秒）
      'zenhan_3f': float,      # 前半3F（1200m=厳密計算, それ以外=AI推定ペース）
      'kohan_3f': float,       # 後半3F（実測値）
      'race_count': int        # サンプル数
    }}
  }}
}}

注意事項:
- 1200m: zenhan_3f = soha_time - kohan_3f（厳密計算、強制一致）
- それ以外: zenhan_3fはTen3FEstimatorによる「ペース指標」
- Ten指数計算では soha_time を基準タイムとして使用

作成日: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
データソース: nvd_ra, nvd_se (PostgreSQL)
計算方法: Ten3FEstimator（AI推定） + 1200m厳密計算（v14）
"""

from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

# ============================
# 1. 主催者マスター
# ============================

# 地方競馬全14主催者（NARコード付き）
ORGANIZERS = {{
    # 南関東4場（MINAMI_KANTO）
    '42': {{'name': '浦和', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'}},
    '43': {{'name': '船橋', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'}},
    '44': {{'name': '大井', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'}},
    '45': {{'name': '川崎', 'region': 'MINAMI_KANTO', 'base_class': 'C2', 'calc_type': 'HYBRID'}},
    
    # 北海道・東北
    '30': {{'name': '門別', 'region': 'HOKKAIDO', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    '35': {{'name': '盛岡', 'region': 'TOHOKU', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    '36': {{'name': '水沢', 'region': 'TOHOKU', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    
    # 北陸・東海
    '46': {{'name': '金沢', 'region': 'HOKURIKU', 'base_class': 'C', 'calc_type': 'POINT'}},
    '47': {{'name': '笠松', 'region': 'TOKAI', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    '48': {{'name': '名古屋', 'region': 'TOKAI', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    
    # 近畿
    '50': {{'name': '園田', 'region': 'KINKI', 'base_class': 'C2', 'calc_type': 'POINT'}},
    '51': {{'name': '姫路', 'region': 'KINKI', 'base_class': 'C2', 'calc_type': 'POINT'}},
    
    # 四国・九州
    '54': {{'name': '高知', 'region': 'SHIKOKU', 'base_class': 'C', 'calc_type': 'CYCLE'}},
    '55': {{'name': '佐賀', 'region': 'KYUSHU', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
    
    # ばんえい（特殊）
    '65': {{'name': 'ばんえい', 'region': 'HOKKAIDO', 'base_class': 'C', 'calc_type': 'EARNINGS'}},
}}

# ============================
# 2. 基準タイム設定
# ============================

{base_times_content}

# ============================
# 3. 馬場状態補正値
# ============================

# 馬場状態補正（babajotai_code_dirt）
BABA_CORRECTION = {{
    '1': 0.0,   # 良
    '2': 0.3,   # 稍重（+0.3秒）
    '3': 0.6,   # 重（+0.6秒）
    '4': 1.0,   # 不良（+1.0秒）
}}

# ============================
# 4. ヘルパー関数
# ============================

# 競馬場名マッピング
KEIBAJO_NAMES = {{
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
    '55': '佐賀'
}}

def get_base_time(keibajo_code: str, kyori: int, time_type: str = 'soha_time') -> Optional[float]:
    """
    指定された競馬場・距離の基準タイムを取得
    
    Args:
        keibajo_code: 競馬場コード（例: '44'）
        kyori: 距離（m）（例: 1600）
        time_type: タイムタイプ（'soha_time', 'zenhan_3f', 'kohan_3f'）
    
    Returns:
        基準タイム（秒）、存在しない場合はNone
    """
    if keibajo_code not in BASE_TIMES:
        logger.warning(f"競馬場コード {{keibajo_code}} が見つかりません")
        return None
    
    if kyori not in BASE_TIMES[keibajo_code]:
        # 最も近い距離を探す
        available_kyori = sorted(BASE_TIMES[keibajo_code].keys())
        closest_kyori = min(available_kyori, key=lambda x: abs(x - kyori))
        logger.warning(f"距離 {{kyori}}m が見つかりません。最も近い距離 {{closest_kyori}}m を使用します")
        kyori = closest_kyori
    
    data = BASE_TIMES[keibajo_code][kyori]
    
    if time_type not in data:
        logger.warning(f"タイムタイプ {{time_type}} が見つかりません")
        return None
    
    return data[time_type]


if __name__ == "__main__":
    # テスト実行
    print("=" * 80)
    print("BASE_TIMES テスト")
    print("=" * 80)
    
    # 競馬場数を確認
    print(f"\\n競馬場数: {{len(BASE_TIMES)}}")
    
    # 各競馬場の距離数を確認
    print("\\n各競馬場の距離数:")
    for code in sorted(BASE_TIMES.keys()):
        name = KEIBAJO_NAMES.get(code, '不明')
        distance_count = len(BASE_TIMES[code])
        print(f"  {{code}} ({{name}}): {{distance_count}}距離")
    
    # 大井1200mのデータを確認
    print("\\n大井（'44'）1200mのデータ:")
    if '44' in BASE_TIMES and 1200 in BASE_TIMES['44']:
        data = BASE_TIMES['44'][1200]
        print(f"  走破タイム: {{data['soha_time']}}秒")
        print(f"  前半3F: {{data['zenhan_3f']}}秒")
        print(f"  後半3F: {{data['kohan_3f']}}秒")
        print(f"  サンプル数: {{data['race_count']}}件")
        
        # 1200mの検証
        calc_time = data['zenhan_3f'] + data['kohan_3f']
        diff = abs(data['soha_time'] - calc_time)
        if diff <= 0.1:
            print(f"  ✅ 検証: {{data['soha_time']}}秒 ≈ {{data['zenhan_3f']}}秒 + {{data['kohan_3f']}}秒 = {{calc_time}}秒")
        else:
            print(f"  ⚠️ 検証: {{data['soha_time']}}秒 ≠ {{data['zenhan_3f']}}秒 + {{data['kohan_3f']}}秒 = {{calc_time}}秒")
    
    # get_base_time 関数のテスト
    print("\\nget_base_time 関数のテスト:")
    test_cases = [
        ('44', 1200, 'soha_time'),
        ('44', 1600, 'soha_time'),
        ('43', 1000, 'zenhan_3f')
    ]
    
    for code, kyori, time_type in test_cases:
        name = KEIBAJO_NAMES.get(code, '不明')
        value = get_base_time(code, kyori, time_type)
        print(f"  {{name}}({{code}}) {{kyori}}m {{time_type}}: {{value}}秒")
    
    print("\\n" + "=" * 80)
    print("✅ テスト完了")
    print("=" * 80)
'''
    
    # ファイルに書き込み
    with open(base_times_py, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"✅ config/base_times.py を更新しました")
    
    # 動作確認
    print("\n動作確認中...")
    try:
        # 既存のモジュールをリロード
        if 'config.base_times' in sys.modules:
            del sys.modules['config.base_times']
        
        from config.base_times import BASE_TIMES
        
        print(f"✅ BASE_TIMES読込成功")
        print(f"   競馬場数: {len(BASE_TIMES)}")
        print(f"   大井1200m: {BASE_TIMES['44'][1200]}")
        
        return True
    except Exception as e:
        print(f"❌ エラー: {e}")
        return False


if __name__ == "__main__":
    print("=" * 80)
    print("config/base_times.py 自動更新スクリプト")
    print("=" * 80)
    print()
    
    success = update_base_times()
    
    if success:
        print("\n" + "=" * 80)
        print("✅ 更新完了！")
        print("=" * 80)
        print("\n次のステップ:")
        print("  python scripts\\collect_index_stats.py")
    else:
        print("\n" + "=" * 80)
        print("❌ 更新失敗")
        print("=" * 80)
