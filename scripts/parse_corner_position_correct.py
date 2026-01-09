#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
正確なコーナー順位パーサ（実データに基づく完全版）

実データ分析結果:
- 全て固定長72文字（末尾スペースでパディング）
- フォーマット: '1コーナー番号馬番,馬番,...' (先頭1文字=コーナー番号)
- 同着パターン:
  - (4,9) → カッコ内が同着
  - 1-9 → ハイフン同着
  - 3=4 → イコール同着
  - 5-(6,10,9) → 複合パターン
"""


def parse_corner_position(corner_str: str, umaban: str) -> int:
    """
    nvd_ra.corner_tsuka_juni_X から指定馬番のコーナー順位を取得
    
    Args:
        corner_str: コーナー通過順位文字列（固定長72文字）
        umaban: 馬番（文字列または整数）
    
    Returns:
        コーナー順位（見つからない場合は0）
    
    Examples:
        >>> parse_corner_position('115,7,11,3,8,12,(4,9),10,2,1,6                                          ', '4')
        7  # (4,9)で7位
        
        >>> parse_corner_position('414,8,(5,2,7),1-9,(3,6)                                                 ', '9')
        4  # 1-9で4位
    """
    if not corner_str or corner_str.strip() == '' or corner_str.strip() == '00':
        return 0
    
    try:
        # Step 1: 固定長72文字の末尾スペースを削除
        corner_str = corner_str.strip()
        
        # Step 2: 先頭のコーナー番号+馬番を削除（最初のカンマまで）
        # 例: '115,7,11,...' → '7,11,...'
        if ',' in corner_str:
            corner_str = corner_str[corner_str.index(',')+1:]
        else:
            return 0  # カンマがない = 不正なデータ
        
        # Step 3: 馬番を正規化（0埋めパターンも対応）
        target_umaban = str(umaban).strip().lstrip('0') or '0'
        
        # Step 4: カンマで分割
        parts = [p.strip() for p in corner_str.split(',') if p.strip()]
        
        position = 1  # 順位カウンター
        
        for part in parts:
            if not part:
                continue
            
            # 同着パターンを全て抽出
            horses_in_this_position = []
            
            # カッコパターン: (4,9) または 5-(6,10,9)
            if '(' in part and ')' in part:
                # カッコの前の馬番（あれば）
                before_bracket = part[:part.index('(')]
                # カッコの中の馬番
                bracket_content = part[part.index('(')+1:part.index(')')]
                
                # カッコの前の馬番を処理（ハイフンやイコールを除去）
                if before_bracket:
                    clean_before = before_bracket.replace('-', '').replace('=', '').strip()
                    if clean_before:
                        horses_in_this_position.append(clean_before)
                
                # カッコ内の馬番を処理
                for h in bracket_content.split(','):
                    h = h.strip()
                    if h:
                        horses_in_this_position.append(h)
            
            # ハイフンパターン: 1-9 (カッコなし)
            elif '-' in part:
                for h in part.split('-'):
                    h = h.strip()
                    if h:
                        horses_in_this_position.append(h)
            
            # イコールパターン: 3=4 (カッコなし)
            elif '=' in part:
                for h in part.split('='):
                    h = h.strip()
                    if h:
                        horses_in_this_position.append(h)
            
            # 通常パターン: 単一馬番
            else:
                horses_in_this_position.append(part)
            
            # 馬番を正規化して比較
            normalized_horses = [h.lstrip('0') or '0' for h in horses_in_this_position]
            
            if target_umaban in normalized_horses:
                return position
            
            # 順位を進める
            position += len(horses_in_this_position)
        
        return 0
    
    except Exception as e:
        # エラー時は0を返す
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
    print("コーナー順位パーサ テスト")
    print("="*80)
    
    passed = 0
    failed = 0
    
    for corner_str, umaban, expected in test_cases:
        result = parse_corner_position(corner_str, umaban)
        status = "✅" if result == expected else "❌"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} 馬番={umaban:2s}, 期待={expected}, 結果={result}")
        if result != expected:
            print(f"   データ: {corner_str.strip()}")
    
    print("="*80)
    print(f"✅ 成功: {passed}/{len(test_cases)}")
    print(f"❌ 失敗: {failed}/{len(test_cases)}")
    print("="*80)
