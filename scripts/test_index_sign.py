#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指数の符号を確認するテストスクリプト
"""

import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.index_calculator import calculate_ten_index, calculate_agari_index

# テストケース1: 速い馬（基準より速い）
print("="*80)
print("テストケース1: 速い馬（基準より0.5秒速い）")
print("="*80)
zenhan_3f_fast = 36.0  # 速い
base_zenhan = 36.5     # 基準（大井1600m相当）
print(f"実走前半3F: {zenhan_3f_fast}秒")
print(f"基準前半3F: {base_zenhan}秒")
print(f"差分: {base_zenhan - zenhan_3f_fast}秒（プラス=速い）")

ten_index_fast = calculate_ten_index(
    zenhan_3f=zenhan_3f_fast,
    kyori=1600,
    baba_code='1',  # 良馬場
    keibajo_code='42'  # 大井
)
print(f"テン指数: {ten_index_fast}")
print(f"期待値: プラス（良いパフォーマンス）")
print(f"実際: {'✅ OK' if ten_index_fast > 0 else '❌ NG（符号が逆）'}")
print()

# テストケース2: 遅い馬（基準より遅い）
print("="*80)
print("テストケース2: 遅い馬（基準より0.5秒遅い）")
print("="*80)
zenhan_3f_slow = 37.0  # 遅い
print(f"実走前半3F: {zenhan_3f_slow}秒")
print(f"基準前半3F: {base_zenhan}秒")
print(f"差分: {base_zenhan - zenhan_3f_slow}秒（マイナス=遅い）")

ten_index_slow = calculate_ten_index(
    zenhan_3f=zenhan_3f_slow,
    kyori=1600,
    baba_code='1',
    keibajo_code='42'
)
print(f"テン指数: {ten_index_slow}")
print(f"期待値: マイナス（悪いパフォーマンス）")
print(f"実際: {'✅ OK' if ten_index_slow < 0 else '❌ NG（符号が逆）'}")
print()

# テストケース3: 上がり指数（速い馬）
print("="*80)
print("テストケース3: 上がり指数（速い馬）")
print("="*80)
kohan_3f_fast = 38.5  # 速い
base_kohan = 39.0     # 基準
print(f"実走後半3F: {kohan_3f_fast}秒")
print(f"基準後半3F: {base_kohan}秒")
print(f"差分: {base_kohan - kohan_3f_fast}秒（プラス=速い）")

agari_index_fast = calculate_agari_index(
    kohan_3f=kohan_3f_fast,
    kyori=1600,
    baba_code='1',
    keibajo_code='42'
)
print(f"上がり指数: {agari_index_fast}")
print(f"期待値: プラス（良いパフォーマンス）")
print(f"実際: {'✅ OK' if agari_index_fast > 0 else '❌ NG（符号が逆）'}")
print()

# 結論
print("="*80)
print("結論")
print("="*80)
if ten_index_fast > 0 and ten_index_slow < 0 and agari_index_fast > 0:
    print("✅ 符号は正しい: プラスが良い、マイナスが悪い")
else:
    print("❌ 符号が逆: 修正が必要")
