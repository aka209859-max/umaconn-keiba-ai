"""
AAS得点計算テスト（CEOのPC上で実行）

保存先: E:\UmaData\nar-analytics-python\test_aas_calculation.py
実行方法: python test_aas_calculation.py
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import numpy as np
import sys

# データベース接続設定
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}


def get_odds_correction(odds, is_fukusho=False):
    """オッズから補正係数を取得（簡易版）"""
    # 単勝補正係数（簡易版）
    if odds < 1.6:
        return 0.94
    elif odds < 10.0:
        return 1.00
    elif odds < 50.0:
        return 1.07
    else:
        return 1.50


def calculate_corrected_return_rate(conn, keibajo_code, kyori, factor_name, factor_value):
    """
    補正回収率を計算（簡易版テスト）
    
    実際の実装では、2016-2025年の10年分のデータを使用し、
    期間別重み付けを行います。
    """
    
    # テスト用のサンプルクエリ（大井競馬場、1600m、枠番1）
    query = """
    SELECT 
        kaisai_nen as year,
        tansho_odds::float as win_odds,
        kakutei_chakujun::int as finish_position
    FROM nvd_se se
    LEFT JOIN nvd_ra ra ON
        se.keibajo_code = ra.keibajo_code AND
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.race_bango = ra.race_bango
    WHERE 
        se.keibajo_code = %s AND
        se.kaisai_nen >= '2020' AND
        se.kaisai_nen <= '2025' AND
        ra.kyori = %s AND
        se.wakuban = %s AND
        se.kakutei_chakujun IS NOT NULL AND
        se.kakutei_chakujun != '' AND
        se.tansho_odds IS NOT NULL AND
        se.tansho_odds != ''
    LIMIT 100
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (keibajo_code, kyori, factor_value))
        results = cur.fetchall()
    
    if not results:
        return {
            'win_rate': 0,
            'place_rate': 0,
            'total_count': 0,
            'corrected_win_return': 0,
            'corrected_place_return': 0
        }
    
    # 簡易計算
    total_count = len(results)
    win_count = sum(1 for r in results if r['finish_position'] == 1)
    place_count = sum(1 for r in results if r['finish_position'] <= 3)
    
    win_rate = (win_count / total_count) * 100 if total_count > 0 else 0
    place_rate = (place_count / total_count) * 100 if total_count > 0 else 0
    
    # 補正回収率の簡易計算
    total_bet = 0
    total_win_payout = 0
    
    for r in results:
        odds = r['win_odds']
        finish = r['finish_position']
        
        # 均等払戻方式
        bet_amount = 10000 / odds if odds > 0 else 0
        total_bet += bet_amount
        
        if finish == 1:
            # 補正係数を適用
            correction = get_odds_correction(odds)
            payout = 10000 * correction
            total_win_payout += payout
    
    corrected_win_return = (total_win_payout / total_bet) * 100 if total_bet > 0 else 0
    
    return {
        'win_rate': round(win_rate, 2),
        'place_rate': round(place_rate, 2),
        'total_count': total_count,
        'corrected_win_return': round(corrected_win_return, 2),
        'corrected_place_return': round(corrected_win_return * 0.9, 2)  # 簡易計算
    }


def test_aas_calculation():
    """AAS得点計算のテスト"""
    try:
        print('=' * 70)
        print('  AAS得点計算テスト')
        print('=' * 70)
        print()
        
        print('🔌 データベース接続中...')
        conn = psycopg2.connect(**DB_CONFIG)
        print('✅ 接続成功')
        print()
        
        # テスト1: 補正回収率計算
        print('【テスト1: 補正回収率計算】')
        print('対象: 大井競馬場（44）、1600m、枠番1')
        print()
        
        stats = calculate_corrected_return_rate(
            conn, '44', 1600, 'wakuban', '1'
        )
        
        print(f'  総出現回数: {stats["total_count"]}件')
        print(f'  勝率: {stats["win_rate"]}%')
        print(f'  連対率: {stats["place_rate"]}%')
        print(f'  補正単勝回収率: {stats["corrected_win_return"]}%')
        print(f'  補正複勝回収率: {stats["corrected_place_return"]}%')
        print()
        
        # テスト2: AAS得点計算（簡易版）
        print('【テスト2: AAS得点計算（1頭のみ）】')
        
        # Hit_raw, Ret_raw の計算
        Hit_raw = 0.65 * stats['win_rate'] + 0.35 * stats['place_rate']
        Ret_raw = 0.35 * stats['corrected_win_return'] + 0.65 * stats['corrected_place_return']
        
        print(f'  Hit_raw = 0.65 × {stats["win_rate"]} + 0.35 × {stats["place_rate"]}')
        print(f'          = {Hit_raw:.2f}')
        print()
        print(f'  Ret_raw = 0.35 × {stats["corrected_win_return"]} + 0.65 × {stats["corrected_place_return"]}')
        print(f'          = {Ret_raw:.2f}')
        print()
        
        # Shrinkage係数
        N_min = stats['total_count']
        Shr = np.sqrt(N_min / (N_min + 400))
        print(f'  N_min = {N_min}')
        print(f'  Shrinkage = √({N_min} / ({N_min} + 400)) = {Shr:.6f}')
        print()
        
        print('✅ テスト成功！')
        print()
        print('=' * 70)
        print('  次のステップ: 明日のレースデータで予想を生成')
        print('=' * 70)
        
        conn.close()
        
    except Exception as e:
        print()
        print('=' * 70)
        print(f'❌ エラー: {e}')
        print('=' * 70)
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    test_aas_calculation()
