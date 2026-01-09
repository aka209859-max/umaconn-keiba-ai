#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
コーナー順位データの全パターンを抽出・分析

実際のデータから全てのパターンを収集し、正確な仕様を特定します。
"""

import sys
import os
from collections import Counter
import re

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.db_config import get_db_connection


def analyze_corner_format():
    """コーナー順位データの全パターンを分析"""
    
    print("\n" + "="*80)
    print("コーナー順位データ フォーマット完全分析")
    print("="*80 + "\n")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1400m以上のレースから1000件サンプリング
    query = """
    SELECT 
        ra.corner_tsuka_juni_1,
        ra.corner_tsuka_juni_2,
        ra.corner_tsuka_juni_3,
        ra.corner_tsuka_juni_4
    FROM nvd_ra ra
    WHERE ra.kyori >= 1400
      AND ra.babajotai_code_dirt = '1'
      AND ra.kaisai_nen || ra.kaisai_tsukihi >= '20200101'
    LIMIT 1000
    """
    
    cursor.execute(query)
    rows = cursor.fetchall()
    
    # 全パターンを収集
    all_patterns = []
    special_chars = Counter()
    all_values = []
    
    for row in rows:
        for corner_data in row:
            if corner_data and corner_data != '00':
                all_patterns.append(corner_data)
                all_values.append(corner_data)
                
                # 特殊文字をカウント
                for char in corner_data:
                    if not char.isdigit() and char != ',':
                        special_chars[char] += 1
    
    print(f"📊 サンプル数: {len(rows)} レース × 4コーナー = {len(all_patterns)} データ")
    print(f"📊 ユニークパターン数: {len(set(all_patterns))}\n")
    
    # === 1. サンプルデータ表示 ===
    print("="*80)
    print("1. サンプルデータ（最初の20件）")
    print("="*80)
    for i, pattern in enumerate(all_patterns[:20], 1):
        # repr()で制御文字を可視化
        print(f"{i:2d}. {repr(pattern)}")
    
    # === 2. 特殊文字の使用状況 ===
    print("\n" + "="*80)
    print("2. 特殊文字の使用状況")
    print("="*80)
    for char, count in special_chars.most_common():
        # 文字コードも表示
        print(f"文字: {repr(char):8s} (U+{ord(char):04X})  出現回数: {count:5d}回")
    
    # === 3. 長さ分布 ===
    print("\n" + "="*80)
    print("3. 文字列長の分布")
    print("="*80)
    lengths = Counter([len(p) for p in all_patterns])
    for length, count in sorted(lengths.items()):
        print(f"長さ {length:3d}文字: {count:5d}件")
    
    # === 4. 末尾パターン分析 ===
    print("\n" + "="*80)
    print("4. 末尾パターン分析（最後の5文字）")
    print("="*80)
    endings = Counter([repr(p[-5:]) for p in all_patterns])
    for ending, count in endings.most_common(10):
        print(f"{ending:20s}: {count:5d}件")
    
    # === 5. スペースの有無 ===
    print("\n" + "="*80)
    print("5. スペースを含むデータ")
    print("="*80)
    space_patterns = [p for p in all_patterns if ' ' in p]
    print(f"スペースを含むデータ: {len(space_patterns)} / {len(all_patterns)}件")
    if space_patterns:
        print("\nサンプル（最初の10件）:")
        for i, pattern in enumerate(space_patterns[:10], 1):
            # スペース位置を可視化
            print(f"{i:2d}. 長さ={len(pattern):3d}, {repr(pattern)}")
    
    # === 6. カッコの使用パターン ===
    print("\n" + "="*80)
    print("6. カッコ（括弧）の使用パターン")
    print("="*80)
    bracket_patterns = [p for p in all_patterns if '(' in p or ')' in p]
    print(f"カッコを含むデータ: {len(bracket_patterns)} / {len(all_patterns)}件")
    if bracket_patterns:
        print("\nサンプル（最初の20件）:")
        for i, pattern in enumerate(bracket_patterns[:20], 1):
            print(f"{i:2d}. {repr(pattern)}")
    
    # === 7. ハイフンとイコールのパターン ===
    print("\n" + "="*80)
    print("7. ハイフン（-）とイコール（=）のパターン")
    print("="*80)
    hyphen_patterns = [p for p in all_patterns if '-' in p]
    equal_patterns = [p for p in all_patterns if '=' in p]
    print(f"ハイフン（-）を含むデータ: {len(hyphen_patterns)} / {len(all_patterns)}件")
    print(f"イコール（=）を含むデータ: {len(equal_patterns)} / {len(all_patterns)}件")
    
    if hyphen_patterns:
        print("\nハイフンのサンプル（最初の10件）:")
        for i, pattern in enumerate(hyphen_patterns[:10], 1):
            print(f"{i:2d}. {repr(pattern)}")
    
    if equal_patterns:
        print("\nイコールのサンプル（最初の10件）:")
        for i, pattern in enumerate(equal_patterns[:10], 1):
            print(f"{i:2d}. {repr(pattern)}")
    
    # === 8. 複合パターン（カッコ+ハイフン等） ===
    print("\n" + "="*80)
    print("8. 複合パターン")
    print("="*80)
    complex_patterns = [p for p in all_patterns if ('(' in p or ')' in p) and ('-' in p or '=' in p)]
    print(f"カッコ+ハイフン/イコールのパターン: {len(complex_patterns)} / {len(all_patterns)}件")
    if complex_patterns:
        print("\nサンプル:")
        for i, pattern in enumerate(complex_patterns[:10], 1):
            print(f"{i:2d}. {repr(pattern)}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*80)
    print("✅ 分析完了")
    print("="*80 + "\n")


if __name__ == "__main__":
    try:
        analyze_corner_format()
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
