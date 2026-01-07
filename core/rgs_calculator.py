"""
RGS 1.0 (Racing Grade Score 1.0) 計算エンジン

目的: ファクターの絶対的な収益性評価
範囲: -10.0 〜 +10.0
基準: 回収率80%との差分（絶対基準）

計算式（7ステップ）:
    Step 1: W = cntWin + cntPlace
    Step 2: X = min(1, sqrt(W/500)) [信頼度]
    Step 3: Y = adjWinRet×0.3 + adjPlaceRet×0.7
    Step 4: Z = Y - 80 [基準線80%との差分]
    Step 5: AA = Z × X [信頼度調整]
    Step 6: AB = AA / 25 [正規化]
    Step 7: RGS = 10 × tanh(AB)

判定基準:
    RGS ≥ +7.0: 回収率110%以上、強く推奨
    RGS ≥ +2.0: 回収率90%以上、推奨
    -2.0 < RGS < +2.0: 回収率80%前後、中立
    RGS ≤ -2.0: 回収率70%以下、非推奨

作成日: 2026-01-06
"""

import math


def calculate_rgs(cntWin, cntPlace, adjWinRet, adjPlaceRet):
    """
    RGS 1.0 を計算
    
    Args:
        cntWin (int): 単勝データ数
        cntPlace (int): 複勝データ数
        adjWinRet (float): 補正後単勝回収率（%）
        adjPlaceRet (float): 補正後複勝回収率（%）
    
    Returns:
        float: RGS スコア（-10.0 〜 +10.0）
    """
    # Step 1: レコード数合計
    W = cntWin + cntPlace
    
    # データ不足の場合は0を返す
    if W == 0:
        return 0.0
    
    # Step 2: 信頼度係数（小サンプル対策）
    X = min(1.0, math.sqrt(W / 500.0))
    
    # Step 3: 加重平均回収率（複勝70%重視）
    Y = adjWinRet * 0.3 + adjPlaceRet * 0.7
    
    # Step 4: 80%基準との差分
    Z = Y - 80.0
    
    # Step 5: 信頼度調整
    AA = Z * X
    
    # Step 6: 正規化
    AB = AA / 25.0
    
    # Step 7: tanh変換で-10〜+10に収める
    RGS = 10.0 * math.tanh(AB)
    
    return RGS


def interpret_rgs(rgs_score):
    """
    RGS スコアを解釈
    
    Args:
        rgs_score (float): RGS スコア
    
    Returns:
        dict: 解釈結果
            - category: 'strong', 'recommended', 'neutral', 'not_recommended'
            - label: '強く推奨', '推奨', '中立', '非推奨'
            - estimated_return: 推定回収率（%）
    """
    if rgs_score >= 7.0:
        return {
            'category': 'strong',
            'label': '強く推奨',
            'estimated_return': 110.0
        }
    elif rgs_score >= 2.0:
        return {
            'category': 'recommended',
            'label': '推奨',
            'estimated_return': 90.0
        }
    elif rgs_score > -2.0:
        return {
            'category': 'neutral',
            'label': '中立',
            'estimated_return': 80.0
        }
    else:
        return {
            'category': 'not_recommended',
            'label': '非推奨',
            'estimated_return': 70.0
        }


def calculate_rgs_for_factor(factor_stats):
    """
    ファクター統計データから RGS を計算
    
    Args:
        factor_stats (dict): ファクター統計データ
            - cntWin: 単勝データ数
            - cntPlace: 複勝データ数
            - adjWinRet: 補正後単勝回収率
            - adjPlaceRet: 補正後複勝回収率
    
    Returns:
        dict: RGS 計算結果
            - rgs_score: RGS スコア
            - interpretation: 解釈結果
            - confidence: 信頼度 (0.0〜1.0)
    """
    cntWin = factor_stats.get('cntWin', 0)
    cntPlace = factor_stats.get('cntPlace', 0)
    adjWinRet = factor_stats.get('adjWinRet', 0.0)
    adjPlaceRet = factor_stats.get('adjPlaceRet', 0.0)
    
    # RGS計算
    rgs_score = calculate_rgs(cntWin, cntPlace, adjWinRet, adjPlaceRet)
    
    # 信頼度計算
    W = cntWin + cntPlace
    confidence = min(1.0, math.sqrt(W / 500.0))
    
    # 解釈
    interpretation = interpret_rgs(rgs_score)
    
    return {
        'rgs_score': round(rgs_score, 2),
        'interpretation': interpretation,
        'confidence': round(confidence, 3),
        'data_count': W
    }


def calculate_rgs_for_horse(horse_factors_stats):
    """
    馬の全ファクターから RGS 総合スコアを計算
    
    Args:
        horse_factors_stats (list): 各ファクターの統計データリスト
            [{'factor_id': 'F01', 'cntWin': 100, ...}, ...]
    
    Returns:
        dict: RGS 総合評価
            - total_rgs: 総合RGSスコア
            - factor_scores: 各ファクターのRGSスコア
            - recommendation: 総合推奨度
    """
    total_rgs = 0.0
    factor_scores = []
    
    for factor_stat in horse_factors_stats:
        result = calculate_rgs_for_factor(factor_stat)
        total_rgs += result['rgs_score']
        
        factor_scores.append({
            'factor_id': factor_stat.get('factor_id', ''),
            'factor_name': factor_stat.get('factor_name', ''),
            'rgs_score': result['rgs_score'],
            'confidence': result['confidence'],
            'interpretation': result['interpretation']
        })
    
    # 総合推奨度
    avg_rgs = total_rgs / len(horse_factors_stats) if horse_factors_stats else 0.0
    recommendation = interpret_rgs(avg_rgs)
    
    return {
        'total_rgs': round(total_rgs, 2),
        'average_rgs': round(avg_rgs, 2),
        'factor_scores': factor_scores,
        'recommendation': recommendation
    }


# テスト用サンプルコード
if __name__ == '__main__':
    print("=" * 60)
    print("RGS 1.0 計算エンジン テスト")
    print("=" * 60)
    
    # テストケース1: 高収益ファクター
    print("\n【テストケース1】高収益ファクター（回収率110%）")
    rgs1 = calculate_rgs(cntWin=300, cntPlace=500, adjWinRet=110.0, adjPlaceRet=105.0)
    print(f"  単勝データ数: 300, 複勝データ数: 500")
    print(f"  単勝回収率: 110%, 複勝回収率: 105%")
    print(f"  ➜ RGS = {rgs1:.2f}")
    print(f"  ➜ 解釈: {interpret_rgs(rgs1)}")
    
    # テストケース2: 中立ファクター
    print("\n【テストケース2】中立ファクター（回収率80%）")
    rgs2 = calculate_rgs(cntWin=200, cntPlace=400, adjWinRet=80.0, adjPlaceRet=80.0)
    print(f"  単勝データ数: 200, 複勝データ数: 400")
    print(f"  単勝回収率: 80%, 複勝回収率: 80%")
    print(f"  ➜ RGS = {rgs2:.2f}")
    print(f"  ➜ 解釈: {interpret_rgs(rgs2)}")
    
    # テストケース3: 低収益ファクター
    print("\n【テストケース3】低収益ファクター（回収率60%）")
    rgs3 = calculate_rgs(cntWin=150, cntPlace=300, adjWinRet=60.0, adjPlaceRet=65.0)
    print(f"  単勝データ数: 150, 複勝データ数: 300")
    print(f"  単勝回収率: 60%, 複勝回収率: 65%")
    print(f"  ➜ RGS = {rgs3:.2f}")
    print(f"  ➜ 解釈: {interpret_rgs(rgs3)}")
    
    # テストケース4: 小サンプル（信頼度補正）
    print("\n【テストケース4】小サンプル（回収率110%だが信頼度低）")
    rgs4 = calculate_rgs(cntWin=10, cntPlace=20, adjWinRet=110.0, adjPlaceRet=105.0)
    print(f"  単勝データ数: 10, 複勝データ数: 20")
    print(f"  単勝回収率: 110%, 複勝回収率: 105%")
    print(f"  信頼度: {min(1.0, math.sqrt(30 / 500.0)):.3f}")
    print(f"  ➜ RGS = {rgs4:.2f} （信頼度補正により抑制）")
    print(f"  ➜ 解釈: {interpret_rgs(rgs4)}")
    
    print("\n" + "=" * 60)
    print("✅ RGS 1.0 計算エンジン テスト完了")
    print("=" * 60)
