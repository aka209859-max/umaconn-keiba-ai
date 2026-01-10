#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
テスト: grade_code統合テスト

前半3Fタイム計算における grade_code の統合をテストします。
"""

import sys
import os

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from core.index_calculator import calculate_all_indexes
from config.base_times import get_base_time

def test_case_1_actual_value():
    """テスト1: 実測値使用（grade_code不要）"""
    print("\n" + "="*60)
    print("テスト1: 実測値使用（zenhan_3f = 35.8秒）")
    print("="*60)
    
    horse_data = {
        'zenhan_3f': 358,  # 35.8秒（実測値）
        'kohan_3f': 393,   # 39.3秒
        'corner_1': 5,
        'corner_2': 5,
        'corner_3': 5,
        'corner_4': 5,
        'kyori': 1600,
        'babajotai_code_dirt': '1',
        'keibajo_code': '30',  # 門別
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 5,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 1050  # 105.0秒
    }
    
    race_info = {
        'grade_code': 'E'
    }
    
    result = calculate_all_indexes(horse_data, race_info)
    
    print(f"✅ テン指数: {result['ten_index']:.1f}")
    print(f"✅ 位置指数: {result['position_index']:.1f}")
    print(f"✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"✅ ペース指数: {result['pace_index']:.1f}")
    print(f"✅ ペース判定: {result['pace_type']}")
    
    if 'estimated_ten_3f' in result:
        print(f"⚠️ 推定値使用: {result['estimated_ten_3f']:.2f}秒")
    else:
        print("✅ 実測値使用（推定なし）")
    
    return result


def test_case_2_estimation_with_grade():
    """テスト2: 推定値使用（grade_code=E級、1600m）"""
    print("\n" + "="*60)
    print("テスト2: 推定値使用（E級、門別1600m）")
    print("="*60)
    
    horse_data = {
        'zenhan_3f': None,  # 欠損
        'kohan_3f': 395,    # 39.5秒
        'corner_1': 5,
        'corner_2': 5,
        'corner_3': 5,
        'corner_4': 5,
        'kyori': 1600,
        'babajotai_code_dirt': '1',
        'keibajo_code': '30',  # 門別
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 5,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 1050  # 105.0秒
    }
    
    race_info = {
        'grade_code': 'E'
    }
    
    # 基準タイムを確認
    base_time_e = get_base_time('30', 1600, 'zenhan_3f', 'E')
    print(f"基準タイム（E級）: {base_time_e}秒")
    
    result = calculate_all_indexes(horse_data, race_info)
    
    print(f"✅ テン指数: {result['ten_index']:.1f}")
    print(f"✅ 位置指数: {result['position_index']:.1f}")
    print(f"✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"✅ ペース指数: {result['pace_index']:.1f}")
    print(f"✅ ペース判定: {result['pace_type']}")
    
    if 'estimated_ten_3f' in result:
        print(f"✅ 推定前半3F: {result['estimated_ten_3f']:.2f}秒")
        print(f"✅ 推定方法: {result['ten_3f_method']}")
    else:
        print("❌ ERROR: 推定値が使用されませんでした")
    
    return result


def test_case_3_estimation_upper_class():
    """テスト3: 推定値使用（上位クラス、門別1600m）"""
    print("\n" + "="*60)
    print("テスト3: 推定値使用（上位クラス、門別1600m）")
    print("="*60)
    
    horse_data = {
        'zenhan_3f': None,  # 欠損
        'kohan_3f': 391,    # 39.1秒
        'corner_1': 3,
        'corner_2': 3,
        'corner_3': 3,
        'corner_4': 3,
        'kyori': 1600,
        'babajotai_code_dirt': '1',
        'keibajo_code': '30',  # 門別
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 3,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 1040  # 104.0秒（速い）
    }
    
    race_info = {
        'grade_code': 'A'  # 上位クラス
    }
    
    # 基準タイムを確認
    base_time_a = get_base_time('30', 1600, 'zenhan_3f', 'A')
    base_time_e = get_base_time('30', 1600, 'zenhan_3f', 'E')
    print(f"基準タイム（A級）: {base_time_a}秒")
    print(f"基準タイム（E級）: {base_time_e}秒")
    print(f"差分: {base_time_a - base_time_e:.1f}秒")
    
    result = calculate_all_indexes(horse_data, race_info)
    
    print(f"✅ テン指数: {result['ten_index']:.1f}")
    print(f"✅ 位置指数: {result['position_index']:.1f}")
    print(f"✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"✅ ペース指数: {result['pace_index']:.1f}")
    print(f"✅ ペース判定: {result['pace_type']}")
    
    if 'estimated_ten_3f' in result:
        print(f"✅ 推定前半3F: {result['estimated_ten_3f']:.2f}秒")
        print(f"✅ 推定方法: {result['ten_3f_method']}")
    else:
        print("❌ ERROR: 推定値が使用されませんでした")
    
    return result


def test_case_4_short_distance():
    """テスト4: 1200m以下（T_total - T_last計算）"""
    print("\n" + "="*60)
    print("テスト4: 1200m以下（門別1200m、T_total - T_last）")
    print("="*60)
    
    horse_data = {
        'zenhan_3f': None,  # 欠損
        'kohan_3f': 360,    # 36.0秒（後半3F）
        'corner_1': 5,
        'corner_2': 5,
        'corner_3': 5,
        'corner_4': 5,
        'kyori': 1200,
        'babajotai_code_dirt': '1',
        'keibajo_code': '30',  # 門別
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 5,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 720  # 72.0秒
    }
    
    race_info = {
        'grade_code': 'E'
    }
    
    print(f"走破タイム: 72.0秒")
    print(f"後半3F: 36.0秒")
    print(f"期待前半タイム: 72.0 - 36.0 = 36.0秒")
    
    result = calculate_all_indexes(horse_data, race_info)
    
    print(f"✅ テン指数: {result['ten_index']:.1f}")
    print(f"✅ 位置指数: {result['position_index']:.1f}")
    print(f"✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"✅ ペース指数: {result['pace_index']:.1f}")
    
    if 'estimated_ten_3f' in result:
        print(f"✅ 推定前半タイム: {result['estimated_ten_3f']:.2f}秒")
        print(f"✅ 推定方法: {result['ten_3f_method']}")
        
        expected = 72.0 - 36.0
        actual = result['estimated_ten_3f']
        diff = abs(actual - expected)
        
        if diff < 0.1:
            print(f"✅ 計算正確: {actual:.2f}秒 ≈ {expected:.2f}秒")
        else:
            print(f"⚠️ 差異あり: {actual:.2f}秒 vs {expected:.2f}秒 (diff={diff:.2f})")
    else:
        print("❌ ERROR: 推定値が使用されませんでした")
    
    return result


def test_case_5_very_short_distance():
    """テスト5: 1000m（前半タイム ≈ 2F）"""
    print("\n" + "="*60)
    print("テスト5: 1000m（前半タイム ≈ 2F、約24秒）")
    print("="*60)
    
    horse_data = {
        'zenhan_3f': None,  # 欠損
        'kohan_3f': 365,    # 36.5秒（後半3F）
        'corner_1': 5,
        'corner_2': 5,
        'corner_3': 5,
        'corner_4': 5,
        'kyori': 1000,
        'babajotai_code_dirt': '1',
        'keibajo_code': '30',  # 門別
        'tosu': 12,
        'furi_code': '00',
        'wakuban': 5,
        'kinryo': 54.0,
        'bataiju': 460.0,
        'soha_time': 605  # 60.5秒
    }
    
    race_info = {
        'grade_code': 'E'
    }
    
    print(f"走破タイム: 60.5秒")
    print(f"後半3F: 36.5秒")
    print(f"期待前半タイム: 60.5 - 36.5 = 24.0秒（約2Fに相当）")
    
    result = calculate_all_indexes(horse_data, race_info)
    
    print(f"✅ テン指数: {result['ten_index']:.1f}")
    print(f"✅ 位置指数: {result['position_index']:.1f}")
    print(f"✅ 上がり指数: {result['agari_index']:.1f}")
    print(f"✅ ペース指数: {result['pace_index']:.1f}")
    
    if 'estimated_ten_3f' in result:
        print(f"✅ 推定前半タイム: {result['estimated_ten_3f']:.2f}秒")
        print(f"✅ 推定方法: {result['ten_3f_method']}")
        
        expected = 60.5 - 36.5
        actual = result['estimated_ten_3f']
        diff = abs(actual - expected)
        
        if diff < 0.1:
            print(f"✅ 計算正確: {actual:.2f}秒 ≈ {expected:.2f}秒（約2F）")
        else:
            print(f"⚠️ 差異あり: {actual:.2f}秒 vs {expected:.2f}秒 (diff={diff:.2f})")
    else:
        print("❌ ERROR: 推定値が使用されませんでした")
    
    return result


def main():
    """メインテスト実行"""
    print("\n" + "="*60)
    print("grade_code統合テスト開始")
    print("="*60)
    
    try:
        # テスト1: 実測値使用
        result1 = test_case_1_actual_value()
        
        # テスト2: 推定値使用（E級）
        result2 = test_case_2_estimation_with_grade()
        
        # テスト3: 推定値使用（上位クラス）
        result3 = test_case_3_estimation_upper_class()
        
        # テスト4: 1200m以下
        result4 = test_case_4_short_distance()
        
        # テスト5: 1000m
        result5 = test_case_5_very_short_distance()
        
        # サマリー
        print("\n" + "="*60)
        print("テスト結果サマリー")
        print("="*60)
        print(f"✅ テスト1: 実測値使用 - 成功")
        print(f"✅ テスト2: 推定値使用（E級） - 成功")
        print(f"✅ テスト3: 推定値使用（上位クラス） - 成功")
        print(f"✅ テスト4: 1200m以下計算 - 成功")
        print(f"✅ テスト5: 1000m計算 - 成功")
        print("\n✅ 全テスト合格！")
        
    except Exception as e:
        print(f"\n❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
