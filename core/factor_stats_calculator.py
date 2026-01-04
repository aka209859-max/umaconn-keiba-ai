"""
ファクター統計・補正回収率計算モジュール

CEOから提供された補正回収率の計算式を実装
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.odds_correction import (
    get_odds_correction,
    get_year_weight,
    calculate_bet_amount,
    TARGET_PAYOUT
)


def calculate_corrected_return_rate(conn, keibajo_code, kyori, factor_name, factor_value):
    """
    補正回収率を計算
    
    CEOの計算式:
    補正回収率 = (ΣΣ 重み付き払戻i,t / ΣΣ 重み付きベット額i,t) × 100
    
    詳細展開:
           Σt Σi (実配当i × 補正係数k × 的中フラグi × 重み係数t)
    = ────────────────────────────────────────────────── × 100
           Σt Σi (目標払戻額 / オッズi × 重み係数t)
    
    Args:
        conn: データベース接続
        keibajo_code: 競馬場コード
        kyori: 距離
        factor_name: ファクター名
        factor_value: ファクター値
    
    Returns:
        dict: {
            'win_rate': 勝率,
            'place_rate': 連対率,
            'total_count': 総出現回数,
            'corrected_win_return': 補正単勝回収率,
            'corrected_place_return': 補正複勝回収率,
            'confidence': 信頼度
        }
    """
    
    # データ取得クエリ（2016-2025の10年分）
    query = """
    SELECT 
        se.kaisai_nen as year,
        se.tansho_odds as win_odds,
        se.kakutei_chakujun as finish_position,
        se.kakutoku_honshokin as prize_money
    FROM nvd_se se
    LEFT JOIN nvd_ra ra ON
        se.keibajo_code = ra.keibajo_code AND
        se.kaisai_nen = ra.kaisai_nen AND
        se.kaisai_tsukihi = ra.kaisai_tsukihi AND
        se.race_bango = ra.race_bango
    WHERE 
        se.keibajo_code = %s AND
        se.kaisai_nen >= '2016' AND
        se.kaisai_nen <= '2025' AND
        ra.kyori = %s AND
        {factor_condition}
    ORDER BY se.kaisai_nen, se.kaisai_tsukihi, se.race_bango
    """
    
    # ファクター条件の構築
    factor_condition = build_factor_condition(factor_name, factor_value)
    query = query.format(factor_condition=factor_condition)
    
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(query, (keibajo_code, kyori))
        results = cur.fetchall()
    
    if not results:
        return {
            'win_rate': 0,
            'place_rate': 0,
            'total_count': 0,
            'corrected_win_return': 0,
            'corrected_place_return': 0,
            'confidence': 0
        }
    
    # 補正回収率の計算
    total_weighted_win_payout = 0
    total_weighted_place_payout = 0
    total_weighted_bet = 0
    win_count = 0
    place_count = 0
    total_count = len(results)
    
    for row in results:
        year = row['year']
        win_odds = float(row['win_odds']) if row['win_odds'] else 1.0
        finish = int(row['finish_position']) if row['finish_position'] else 99
        
        # 年度別重み係数
        year_weight = get_year_weight(year)
        if year_weight == 0:
            continue
        
        # ベット額（均等払戻方式）
        bet_amount = calculate_bet_amount(win_odds)
        
        # 単勝補正係数
        win_correction = get_odds_correction(win_odds, is_fukusho=False)
        
        # 複勝補正係数（オッズを0.4倍にして使用）
        place_odds = win_odds * 0.4
        place_correction = get_odds_correction(place_odds, is_fukusho=True)
        
        # 単勝的中フラグ（1着）
        win_flag = 1 if finish == 1 else 0
        
        # 複勝的中フラグ（3着以内）
        place_flag = 1 if finish <= 3 else 0
        
        # 単勝払戻金
        win_payout = TARGET_PAYOUT * win_flag
        
        # 複勝払戻金（簡易計算：単勝オッズの40%として計算）
        place_payout = TARGET_PAYOUT * 0.4 * place_flag
        
        # 補正後払戻金
        corrected_win_payout = win_payout * win_correction
        corrected_place_payout = place_payout * place_correction
        
        # 重み付き払戻金
        weighted_win_payout = corrected_win_payout * year_weight
        weighted_place_payout = corrected_place_payout * year_weight
        
        # 重み付きベット額
        weighted_bet = bet_amount * year_weight
        
        # 累積
        total_weighted_win_payout += weighted_win_payout
        total_weighted_place_payout += weighted_place_payout
        total_weighted_bet += weighted_bet
        
        if win_flag:
            win_count += 1
        if place_flag:
            place_count += 1
    
    # 補正回収率の計算
    if total_weighted_bet > 0:
        corrected_win_return = (total_weighted_win_payout / total_weighted_bet) * 100
        corrected_place_return = (total_weighted_place_payout / total_weighted_bet) * 100
    else:
        corrected_win_return = 0
        corrected_place_return = 0
    
    # 勝率・連対率
    win_rate = (win_count / total_count) * 100 if total_count > 0 else 0
    place_rate = (place_count / total_count) * 100 if total_count > 0 else 0
    
    # 信頼度の計算（CEO式）
    avg_return = (corrected_win_return + corrected_place_return) / 2
    confidence = (avg_return - 80) * total_count
    
    return {
        'win_rate': round(win_rate, 2),
        'place_rate': round(place_rate, 2),
        'total_count': total_count,
        'corrected_win_return': round(corrected_win_return, 2),
        'corrected_place_return': round(corrected_place_return, 2),
        'confidence': round(confidence, 2)
    }


def build_factor_condition(factor_name, factor_value):
    """
    ファクター条件のSQL WHERE句を構築
    
    Args:
        factor_name: ファクター名
        factor_value: ファクター値
    
    Returns:
        SQL WHERE句（文字列）
    """
    
    # 単独ファクター
    if factor_name == 'wakuban':
        return f"se.wakuban = '{factor_value}'"
    elif factor_name == 'umaban':
        return f"se.umaban = '{factor_value}'"
    elif factor_name == 'seibetsu_code':
        return f"se.seibetsu_code = '{factor_value}'"
    elif factor_name == 'barei':
        return f"se.barei = '{factor_value}'"
    elif factor_name == 'kishumei_ryakusho':
        return f"se.kishumei_ryakusho = '{factor_value}'"
    elif factor_name == 'chokyoshimei_ryakusho':
        return f"se.chokyoshimei_ryakusho = '{factor_value}'"
    
    # 前走データファクター（前走の条件を別途取得する必要あり）
    elif factor_name.startswith('prev_'):
        # 前走データは別途処理が必要（ここでは簡易実装）
        return "1=1"  # 暫定
    
    # 組み合わせファクター
    elif '_x_' in factor_name:
        factors = factor_name.split('_x_')
        values = factor_value.split('_x_')
        conditions = []
        for f, v in zip(factors, values):
            conditions.append(build_factor_condition(f, v))
        return ' AND '.join(conditions)
    
    else:
        return "1=1"  # デフォルト


def get_factor_stats_summary(conn, keibajo_code, kyori, factor_name, factor_value):
    """
    ファクター統計のサマリを取得（AAS計算用）
    
    Args:
        conn: データベース接続
        keibajo_code: 競馬場コード
        kyori: 距離
        factor_name: ファクター名
        factor_value: ファクター値
    
    Returns:
        dict: {
            'rate_win_hit': 勝率,
            'rate_place_hit': 連対率,
            'rate_win_ret': 補正単勝回収率,
            'rate_place_ret': 補正複勝回収率,
            'cnt_win': 単勝的中回数,
            'cnt_place': 複勝的中回数,
            'total_count': 総出現回数
        }
    """
    stats = calculate_corrected_return_rate(
        conn, keibajo_code, kyori, factor_name, factor_value
    )
    
    # AAS計算用の形式に変換
    return {
        'rate_win_hit': stats['win_rate'],
        'rate_place_hit': stats['place_rate'],
        'rate_win_ret': stats['corrected_win_return'],
        'rate_place_ret': stats['corrected_place_return'],
        'cnt_win': int(stats['total_count'] * stats['win_rate'] / 100),
        'cnt_place': int(stats['total_count'] * stats['place_rate'] / 100),
        'total_count': stats['total_count']
    }


if __name__ == '__main__':
    # テスト実行
    from config.db_config import get_db_connection
    
    conn = get_db_connection()
    
    # 大井競馬場、1600m、枠番1のテスト
    stats = calculate_corrected_return_rate(
        conn, '44', 1600, 'wakuban', '1'
    )
    
    print("=== 補正回収率計算テスト ===")
    print(f"競馬場: 大井（44）")
    print(f"距離: 1600m")
    print(f"ファクター: 枠番1")
    print(f"")
    print(f"勝率: {stats['win_rate']}%")
    print(f"連対率: {stats['place_rate']}%")
    print(f"総出現回数: {stats['total_count']}")
    print(f"補正単勝回収率: {stats['corrected_win_return']}%")
    print(f"補正複勝回収率: {stats['corrected_place_return']}%")
    print(f"信頼度: {stats['confidence']}")
    
    conn.close()
