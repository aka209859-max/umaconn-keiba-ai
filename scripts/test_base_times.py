#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BASE_TIMES動作確認スクリプト
CEO用：ローカル環境で E:\UmaData\nar-analytics-python-v2 から実行してください
"""

import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, r'E:\UmaData\nar-analytics-python-v2')

try:
    from config.base_times import BASE_TIMES
    
    print("=" * 80)
    print("✅ BASE_TIMES読込成功！")
    print("=" * 80)
    
    # 競馬場数の確認
    print(f"\n📊 競馬場数: {len(BASE_TIMES)}")
    
    # 競馬場コード一覧
    codes = sorted(BASE_TIMES.keys())
    print(f"\n🏇 競馬場コード一覧:")
    print(f"   {codes}")
    
    # 期待値との比較
    expected_codes = ['30', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55']
    if codes == expected_codes:
        print("   ✅ すべての競馬場が存在します")
    else:
        print("   ❌ 競馬場コードに問題があります")
        print(f"   期待値: {expected_codes}")
        print(f"   実際値: {codes}")
    
    # 大井1200mの確認
    print(f"\n🎯 大井（'44'）1200mデータ:")
    if '44' in BASE_TIMES:
        if 1200 in BASE_TIMES['44']:
            data = BASE_TIMES['44'][1200]
            print(f"   前半3F: {data['zenhan_3f']}秒")
            print(f"   後半3F: {data['kohan_3f']}秒")
            print(f"   サンプル数: {data['race_count']}件")
            
            # 正常値チェック
            zenhan = data['zenhan_3f']
            kohan = data['kohan_3f']
            
            if 35 <= zenhan <= 38 and 37 <= kohan <= 40:
                print("   ✅ データは正常範囲内です")
            else:
                print("   ⚠️ データが異常値の可能性があります")
                print(f"   期待値: 前半3F 35-38秒, 後半3F 37-40秒")
        else:
            print("   ❌ 1200mデータが存在しません")
    else:
        print("   ❌ 大井（'44'）が存在しません")
    
    # すべての競馬場のサマリー
    print(f"\n📋 各競馬場の距離数:")
    keibajo_names = {
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
    }
    
    for code in codes:
        name = keibajo_names.get(code, '不明')
        distance_count = len(BASE_TIMES[code])
        print(f"   {code} ({name}): {distance_count}距離")
    
    print("\n" + "=" * 80)
    print("✅ すべてのチェックが完了しました！")
    print("=" * 80)
    print("\n次のステップ: collect_index_stats.py を実行してください")
    print("コマンド: python scripts\\collect_index_stats.py")
    print("=" * 80)
    
except ModuleNotFoundError as e:
    print("=" * 80)
    print("❌ エラー: BASE_TIMESの読込に失敗しました")
    print("=" * 80)
    print(f"\nエラー詳細: {e}")
    print("\n解決方法:")
    print("1. カレントディレクトリを確認してください:")
    print("   cd")
    print("\n2. E:\\UmaData\\nar-analytics-python-v2 に移動してください:")
    print("   E:")
    print("   cd \\UmaData\\nar-analytics-python-v2")
    print("\n3. config/base_times.py が存在するか確認してください:")
    print("   dir config\\base_times.py")
    print("\n4. 再度このスクリプトを実行してください:")
    print("   python scripts\\test_base_times.py")
    print("=" * 80)
    sys.exit(1)

except Exception as e:
    print("=" * 80)
    print("❌ 予期しないエラーが発生しました")
    print("=" * 80)
    print(f"\nエラー詳細: {e}")
    print(f"エラータイプ: {type(e).__name__}")
    print("=" * 80)
    sys.exit(1)
