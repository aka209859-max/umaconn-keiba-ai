#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全競馬場の実測BASE_TIMESを表示するスクリプト
CEO用：各競馬場の距離別タイムを確認
"""

import sys
sys.path.insert(0, r'E:\UmaData\nar-analytics-python-v2')

from config.base_times import BASE_TIMES

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
    '55': '佐賀'
}

print("=" * 100)
print("🏇 地方競馬14場 実測BASE_TIMES一覧（v10実データ版）")
print("=" * 100)
print("\n📊 データソース:")
print("  - nvd_ra, nvd_se（PostgreSQL実データ）")
print("  - 計算方法: Ten3FEstimator（AI推定） + 1200m確定値")
print("  - 特殊期間フィルタ:")
print("    • 大井（'44'）: 2023-10-01 以降（白砂置換）")
print("    • 名古屋（'48'）: 2022-04-01 以降（大幅改修）")
print("  - 後半3F > 0: すべてのデータで検証済み")
print("\n" + "=" * 100)

# 各競馬場のデータを表示
for code in sorted(BASE_TIMES.keys()):
    name = KEIBAJO_NAMES.get(code, '不明')
    
    print(f"\n🏇 【{code}】{name}競馬場")
    print("-" * 100)
    print(f"{'距離':>6} | {'前半3F':>8} | {'後半3F':>8} | {'合計タイム':>10} | {'サンプル数':>10} | {'備考'}")
    print("-" * 100)
    
    # 距離順にソート
    for kyori in sorted(BASE_TIMES[code].keys()):
        data = BASE_TIMES[code][kyori]
        zenhan = data['zenhan_3f']
        kohan = data['kohan_3f']
        total = zenhan + kohan
        race_count = data['race_count']
        
        # 1200mは確定値、それ以外はAI推定
        note = "確定値" if kyori == 1200 else "AI推定"
        
        # データ品質チェック
        if kyori == 1200:
            if 35 <= zenhan <= 38 and 37 <= kohan <= 40:
                quality = "✅"
            else:
                quality = "⚠️"
        else:
            if zenhan > 0 and kohan > 0:
                quality = "✅"
            else:
                quality = "❌"
        
        print(f"{kyori:>6}m | {zenhan:>7.1f}秒 | {kohan:>7.1f}秒 | {total:>9.1f}秒 | {race_count:>9}件 | {quality} {note}")
    
    # 競馬場ごとのサマリー
    total_distances = len(BASE_TIMES[code])
    total_samples = sum(data['race_count'] for data in BASE_TIMES[code].values())
    print("-" * 100)
    print(f"合計: {total_distances}距離, サンプル数: {total_samples:,}件")

print("\n" + "=" * 100)
print("📊 統計サマリー")
print("=" * 100)

# 全体統計
total_keibajo = len(BASE_TIMES)
total_distances = sum(len(distances) for distances in BASE_TIMES.values())
total_samples = sum(
    sum(data['race_count'] for data in distances.values())
    for distances in BASE_TIMES.values()
)

print(f"\n✅ 競馬場数: {total_keibajo}")
print(f"✅ 総距離数: {total_distances}")
print(f"✅ 総サンプル数: {total_samples:,}件")

# 1200mデータの確認
print("\n" + "=" * 100)
print("🎯 1200m確定値データ（前半3F = 走破タイム - 後半3F）")
print("=" * 100)
print(f"{'競馬場':>8} | {'前半3F':>8} | {'後半3F':>8} | {'走破タイム':>10} | {'サンプル数':>10} | {'品質'}")
print("-" * 100)

for code in sorted(BASE_TIMES.keys()):
    if 1200 in BASE_TIMES[code]:
        name = KEIBAJO_NAMES.get(code, '不明')
        data = BASE_TIMES[code][1200]
        zenhan = data['zenhan_3f']
        kohan = data['kohan_3f']
        total = zenhan + kohan
        race_count = data['race_count']
        
        # 品質チェック（1200mの正常値: 前半35-38秒, 後半37-40秒）
        if 35 <= zenhan <= 38 and 37 <= kohan <= 40:
            quality = "✅ 正常"
        else:
            quality = "⚠️ 要確認"
        
        print(f"{name:>6} | {zenhan:>7.1f}秒 | {kohan:>7.1f}秒 | {total:>9.1f}秒 | {race_count:>9}件 | {quality}")

# 南関東4場の比較
print("\n" + "=" * 100)
print("🏙️ 南関東4場の1600m比較")
print("=" * 100)
print(f"{'競馬場':>8} | {'前半3F':>8} | {'後半3F':>8} | {'合計タイム':>10} | {'サンプル数':>10}")
print("-" * 100)

minami_kanto = ['42', '43', '44', '45']
for code in minami_kanto:
    if 1600 in BASE_TIMES[code]:
        name = KEIBAJO_NAMES.get(code, '不明')
        data = BASE_TIMES[code][1600]
        zenhan = data['zenhan_3f']
        kohan = data['kohan_3f']
        total = zenhan + kohan
        race_count = data['race_count']
        
        print(f"{name:>6} | {zenhan:>7.1f}秒 | {kohan:>7.1f}秒 | {total:>9.1f}秒 | {race_count:>9}件")

print("\n" + "=" * 100)
print("✅ すべての競馬場の実測BASE_TIMESを表示しました")
print("=" * 100)
print("\n次のステップ: collect_index_stats.py を実行してください")
print("コマンド: python scripts\\collect_index_stats.py")
print("=" * 100)
