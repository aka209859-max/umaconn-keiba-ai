#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正確なコーナー順位パーサ（完全版 - 正規表現使用）

実データ分析結果に基づく完全な実装
"""

import re


def parse_corner_position(corner_str: str, umaban: str, debug: bool = False) -> int:
    """
    nvd_ra.corner_tsuka_juni_X から指定馬番のコーナー順位を取得
    
    Args:
        corner_str: コーナー通過順位文字列（固定長72文字）
        umaban: 馬番（文字列または整数）
        debug: デバッグ出力
    
    Returns:
        コーナー順位（見つからない場合は0）
    """
    if not corner_str or corner_str.strip() == '' or corner_str.strip() == '00':
        return 0
    
    try:
        # Step 1: 固定長72文字の末尾スペースを削除
        corner_str = corner_str.strip()
        if debug:
            print(f"  [DEBUG] Step 1: corner_str = '{corner_str}'")
        
        # Step 2: 先頭のコーナー番号+馬番を削除（最初のカンマまで）
        if ',' in corner_str:
            corner_str = corner_str[corner_str.index(',')+1:]
            if debug:
                print(f"  [DEBUG] Step 2: corner_str = '{corner_str}'")
        else:
            return 0
        
        # Step 3: 馬番を正規化
        target_umaban = str(umaban).strip().lstrip('0') or '0'
        if debug:
            print(f"  [DEBUG] Step 3: target_umaban = '{target_umaban}'")
        
        # Step 4: 正規表現で要素を分割
        # パターン: カッコ付き、ハイフン/イコール、または単一馬番
        # 例: (4,9) | 1-9 | 3=4 | 5-(6,10) | 単一馬番
        pattern = r'\([^)]+\)|[^,]+-\([^)]+\)|[^,]+=\([^)]+\)|[^,]+-[^,]+|[^,]+=[^,]+|[^,]+'
        parts = [p.strip() for p in re.findall(pattern, corner_str) if p.strip()]
        
        if debug:
            print(f"  [DEBUG] Step 4: parts = {parts}")
        
        position = 1
        
        for part in parts:
            if not part:
                continue
            
            if debug:
                print(f"  [DEBUG] 処理中: part='{part}', position={position}")
            
            # この順位に含まれる全馬番を抽出
            horses = []
            
            # カッコパターン: (4,9) または 5-(6,10,9) または 4=(1,3)
            if '(' in part and ')' in part:
                # カッコの前の部分（あれば）
                before_bracket = part[:part.index('(')]
                before_bracket = before_bracket.replace('-', '').replace('=', '').strip()
                if before_bracket and before_bracket.isdigit():
                    horses.append(before_bracket)
                
                # カッコ内の馬番
                bracket_content = part[part.index('(')+1:part.index(')')]
                for h in bracket_content.split(','):
                    h = h.strip()
                    if h and h.isdigit():
                        horses.append(h)
            
            # ハイフンパターン: 1-9 (カッコなし)
            elif '-' in part:
                for h in part.split('-'):
                    h = h.strip()
                    if h and h.isdigit():
                        horses.append(h)
            
            # イコールパターン: 3=4 (カッコなし)
            elif '=' in part:
                for h in part.split('='):
                    h = h.strip()
                    if h and h.isdigit():
                        horses.append(h)
            
            # 通常パターン
            elif part.isdigit():
                horses.append(part)
            
            # 馬番を正規化して比較
            normalized_horses = [h.lstrip('0') or '0' for h in horses]
            
            if debug:
                print(f"  [DEBUG] horses = {horses}")
                print(f"  [DEBUG] normalized_horses = {normalized_horses}")
            
            if target_umaban in normalized_horses:
                if debug:
                    print(f"  [DEBUG] ✅ 発見！ position={position}")
                return position
            
            position += len(horses)
        
        return 0
    
    except Exception as e:
        if debug:
            print(f"  [DEBUG] ❌ Exception: {e}")
        return 0


# テストケース
if __name__ == "__main__":
    test_cases = [
        ('115,7,11,3,8,12,(4,9),10,2,1,6                                          ', '4', 7),
        ('115,7,11,3,8,12,(4,9),10,2,1,6                                          ', '9', 7),
        ('414,8,(5,2,7),1-9,(3,6)                                                 ', '9', 4),
        ('414,8,(5,2,7),1-9,(3,6)                                                 ', '1', 4),
        ('412,10,6,9,7-8,5,1,3=4                                                  ', '7', 5),
        ('412,10,6,9,7-8,5,1,3=4                                                  ', '8', 5),
        ('412,10,6,9,7-8,5,1,3=4                                                  ', '3', 8),
        ('412,10,6,9,7-8,5,1,3=4                                                  ', '4', 8),
        ('314,8,2,1,7,5-(6,10,9),3                                                ', '5', 6),
        ('314,8,2,1,7,5-(6,10,9),3                                                ', '6', 6),
        ('316,9,5,4=1,3,8,7,2                                                     ', '4', 3),
        ('316,9,5,4=1,3,8,7,2                                                     ', '1', 3),
    ]
    
    print("="*80)
    print("コーナー順位パーサ テスト（正規表現版）")
    print("="*80 + "\n")
    
    passed = 0
    failed = 0
    
    for corner_str, umaban, expected in test_cases:
        result = parse_corner_position(corner_str, umaban, debug=False)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
            print(f"{status} 馬番={umaban:2s}, 期待={expected}, 結果={result}")
        else:
            failed += 1
            print(f"\n{status} 馬番={umaban:2s}, 期待={expected}, 結果={result}")
            print(f"   データ: {corner_str.strip()}")
            print("   --- デバッグ ---")
            parse_corner_position(corner_str, umaban, debug=True)
            print("   --- デバッグ終了 ---")
    
    print("\n" + "="*80)
    print(f"✅ 成功: {passed}/{len(test_cases)}")
    print(f"❌ 失敗: {failed}/{len(test_cases)}")
    print("="*80)
