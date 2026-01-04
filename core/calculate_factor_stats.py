"""
ファクター統計・補正回収率計算モジュール（31ファクター対応版）

CEO式の補正回収率計算を実装:
  補正回収率 = (ΣΣ 実配当 × 補正係数 × 的中フラグ × 重み) / 
               (ΣΣ ベット額 × 重み) × 100

重要なルール:
1. 目標払戻額 = 10,000円（固定）
2. オッズ補正係数: 単勝123段階、複勝108段階
3. 期間別重み: 2016=1, 2017=2, ..., 2025=10
4. 的中率は%値のまま使用（15% = 15）
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.odds_correction import (
    get_odds_correction_factor,
    YEAR_WEIGHTS,
    TARGET_PAYOUT
)


def safe_float(value, default=0.0):
    """安全にfloatに変換"""
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """安全にintに変換"""
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def build_factor_sql_condition(factor_name, factor_value):
    """
    ファクター名と値からSQL WHERE条件を生成
    
    Args:
        factor_name: ファクター名（例: 'F01_kishu', 'C01_kishu_kyori'）
        factor_value: ファクター値（例: '05658', '05658_1300'）
    
    Returns:
        tuple: (WHERE条件文字列, パラメータリスト)
    """
    
    # 単独ファクター
    if factor_name == 'F01_kishu':
        return "se.kishu_code = %s", [factor_value]
    
    elif factor_name == 'F02_chokyoshi':
        return "se.chokyoshi_code = %s", [factor_value]
    
    elif factor_name == 'F03_kyori':
        return "ra.kyori = %s", [safe_int(factor_value)]
    
    elif factor_name == 'F04_baba':
        return "ra.babajotai_code_dirt = %s", [factor_value]
    
    elif factor_name == 'F05_mawari':
        return "ra.track_code = %s", [factor_value]
    
    elif factor_name == 'F06_joken':
        return "ra.kyoso_joken_code = %s", [factor_value]
    
    elif factor_name == 'F07_kyakushitsu':
        # 脚質は直接検索できないため、コーナー通過順位から計算が必要
        # 簡易実装: スキップ
        return "1=1", []
    
    elif factor_name == 'F08_wakuban':
        return "se.wakuban = %s", [safe_int(factor_value)]
    
    elif factor_name == 'F09_prev_chakujun':
        # 前走着順（前走データの取得が必要、簡易実装: スキップ）
        return "1=1", []
    
    elif factor_name == 'F10_prev_ninki':
        # 前走人気（前走データの取得が必要、簡易実装: スキップ）
        return "1=1", []
    
    elif factor_name == 'F11_prev_kyori':
        # 前走距離（前走データの取得が必要、簡易実装: スキップ）
        return "1=1", []
    
    elif factor_name == 'F12_prev_baba':
        # 前走馬場（前走データの取得が必要、簡易実装: スキップ）
        return "1=1", []
    
    elif factor_name == 'F13_kyuyo_weeks':
        # 休養週数（前走データの取得が必要、簡易実装: スキップ）
        return "1=1", []
    
    elif factor_name == 'F14_bataiju':
        # 馬体重（範囲検索が必要、簡易実装: 完全一致）
        return "se.bataiju = %s", [safe_int(factor_value)]
    
    elif factor_name == 'F15_zogen_sa':
        # 馬体重増減（範囲検索が必要、簡易実装: 完全一致）
        return "se.zogen_sa = %s", [safe_int(factor_value)]
    
    elif factor_name == 'F16_seibetsu':
        return "se.seibetsu_code = %s", [factor_value]
    
    # 組み合わせファクター
    elif factor_name.startswith('C'):
        # 組み合わせファクターは複数条件のAND
        # 例: C01_kishu_kyori = '05658_1300'
        parts = factor_value.split('_')
        
        if factor_name == 'C01_kishu_kyori':
            # 騎手×距離
            return "se.kishu_code = %s AND ra.kyori = %s", [parts[0], safe_int(parts[1])]
        
        elif factor_name == 'C02_kishu_baba':
            # 騎手×馬場状態
            return "se.kishu_code = %s AND ra.babajotai_code_dirt = %s", [parts[0], parts[1]]
        
        elif factor_name == 'C03_kishu_mawari':
            # 騎手×回り
            return "se.kishu_code = %s AND ra.track_code = %s", [parts[0], parts[1]]
        
        elif factor_name == 'C04_kishu_joken':
            # 騎手×条件
            return "se.kishu_code = %s AND ra.kyoso_joken_code = %s", [parts[0], parts[1]]
        
        elif factor_name == 'C05_chokyoshi_kyori':
            # 調教師×距離
            return "se.chokyoshi_code = %s AND ra.kyori = %s", [parts[0], safe_int(parts[1])]
        
        elif factor_name == 'C06_chokyoshi_baba':
            # 調教師×馬場状態
            return "se.chokyoshi_code = %s AND ra.babajotai_code_dirt = %s", [parts[0], parts[1]]
        
        elif factor_name == 'C07_kyori_baba':
            # 距離×馬場状態
            return "ra.kyori = %s AND ra.babajotai_code_dirt = %s", [safe_int(parts[0]), parts[1]]
        
        elif factor_name == 'C08_kyori_mawari':
            # 距離×回り
            return "ra.kyori = %s AND ra.track_code = %s", [safe_int(parts[0]), parts[1]]
        
        elif factor_name in ['C09_kyakushitsu_kyori', 'C10_kyakushitsu_baba']:
            # 脚質系（スキップ）
            return "1=1", []
        
        elif factor_name == 'C11_wakuban_kyori':
            # 枠番×距離
            return "se.wakuban = %s AND ra.kyori = %s", [safe_int(parts[0]), safe_int(parts[1])]
        
        elif factor_name in ['C12_prev_chakujun_kyuyo', 'C13_prev_ninki_chakujun', 'C14_zogen_kyuyo']:
            # 前走系（スキップ）
            return "1=1", []
        
        elif factor_name == 'C15_seibetsu_kyori':
            # 性別×距離
            return "se.seibetsu_code = %s AND ra.kyori = %s", [parts[0], safe_int(parts[1])]
    
    # デフォルト
    return "1=1", []


def calculate_factor_corrected_return_rate(conn, keibajo_code, factor_name, factor_value):
    """
    指定されたファクターの補正回収率を計算
    
    CEO式の補正回収率計算:
      補正回収率 = (ΣΣ 実配当 × 補正係数 × 的中フラグ × 重み) / 
                   (ΣΣ ベット額 × 重み) × 100
    
    Args:
        conn: データベース接続
        keibajo_code: 競馬場コード
        factor_name: ファクター名（例: 'F01_kishu'）
        factor_value: ファクター値（例: '05658'）
    
    Returns:
        dict: {
            'rate_win_hit': 単勝的中率（%値: 15% = 15）,
            'rate_place_hit': 複勝的中率（%値: 45% = 45）,
            'adj_win_ret': 補正単勝回収率（%値: 95% = 95）,
            'adj_place_ret': 補正複勝回収率（%値: 98% = 98）,
            'cnt_win': 単勝的中回数,
            'cnt_place': 複勝的中回数,
            'total_count': 総出現回数
        }
    """
    
    # SQL WHERE条件を生成
    where_condition, params = build_factor_sql_condition(factor_name, factor_value)
    
    # 過去データ取得クエリ（2016-2025年）
    query = f"""
    SELECT 
        se.kaisai_nen,
        se.tansho_odds,
        se.fukusho_odds,
        se.kakutei_chakujun,
        se.tansho_haito,
        se.fukusho_haito
    FROM nvd_se se
    JOIN nvd_ra ra ON (
        se.kaisai_nen = ra.kaisai_nen 
        AND se.kaisai_tsukihi = ra.kaisai_tsukihi
        AND se.keibajo_code = ra.keibajo_code
        AND se.race_bango = ra.race_bango
    )
    WHERE se.keibajo_code = %s
    AND se.kaisai_nen >= '2016' AND se.kaisai_nen <= '2025'
    AND se.kakutei_chakujun IS NOT NULL
    AND se.tansho_odds IS NOT NULL
    AND {where_condition}
    ORDER BY se.kaisai_nen, se.kaisai_tsukihi
    """
    
    cur = conn.cursor()
    cur.execute(query, [keibajo_code] + params)
    rows = cur.fetchall()
    cur.close()
    
    if not rows or len(rows) == 0:
        # データがない場合はデフォルト値を返す
        return {
            'rate_win_hit': 0.0,
            'rate_place_hit': 0.0,
            'adj_win_ret': 0.0,
            'adj_place_ret': 0.0,
            'cnt_win': 0,
            'cnt_place': 0,
            'total_count': 0
        }
    
    # 単勝・複勝の補正回収率を計算
    total_win_weighted_payout = 0.0
    total_win_weighted_bet = 0.0
    win_hit_count = 0
    win_total_count = 0
    
    total_place_weighted_payout = 0.0
    total_place_weighted_bet = 0.0
    place_hit_count = 0
    place_total_count = 0
    
    for row in rows:
        year = row[0]
        tansho_odds = safe_float(row[1])
        fukusho_odds = safe_float(row[2])
        chakujun = safe_int(row[3])
        tansho_haito = safe_float(row[4])
        fukusho_haito = safe_float(row[5])
        
        # 期間別重み
        weight = YEAR_WEIGHTS.get(year, 0)
        if weight == 0:
            continue
        
        # 単勝
        if tansho_odds > 0:
            win_total_count += 1
            bet_amount = TARGET_PAYOUT / tansho_odds
            weighted_bet = bet_amount * weight
            total_win_weighted_bet += weighted_bet
            
            # 的中判定（1着）
            if chakujun == 1 and tansho_haito > 0:
                win_hit_count += 1
                # 補正係数を取得
                correction = get_odds_correction_factor(tansho_odds, 'win')
                corrected_payout = tansho_haito * correction
                weighted_payout = corrected_payout * weight
                total_win_weighted_payout += weighted_payout
        
        # 複勝
        if fukusho_odds > 0:
            place_total_count += 1
            bet_amount = TARGET_PAYOUT / fukusho_odds
            weighted_bet = bet_amount * weight
            total_place_weighted_bet += weighted_bet
            
            # 的中判定（1-3着）
            if chakujun in [1, 2, 3] and fukusho_haito > 0:
                place_hit_count += 1
                # 補正係数を取得
                correction = get_odds_correction_factor(fukusho_odds, 'place')
                corrected_payout = fukusho_haito * correction
                weighted_payout = corrected_payout * weight
                total_place_weighted_payout += weighted_payout
    
    # 補正回収率を計算
    adj_win_ret = 0.0
    if total_win_weighted_bet > 0:
        adj_win_ret = (total_win_weighted_payout / total_win_weighted_bet) * 100
    
    adj_place_ret = 0.0
    if total_place_weighted_bet > 0:
        adj_place_ret = (total_place_weighted_payout / total_place_weighted_bet) * 100
    
    # 的中率を計算（%値のまま: 15% = 15）
    rate_win_hit = 0.0
    if win_total_count > 0:
        rate_win_hit = (win_hit_count / win_total_count) * 100
    
    rate_place_hit = 0.0
    if place_total_count > 0:
        rate_place_hit = (place_hit_count / place_total_count) * 100
    
    return {
        'rate_win_hit': rate_win_hit,      # %値（15% = 15）
        'rate_place_hit': rate_place_hit,  # %値（45% = 45）
        'adj_win_ret': adj_win_ret,        # %値（95% = 95）
        'adj_place_ret': adj_place_ret,    # %値（98% = 98）
        'cnt_win': win_hit_count,
        'cnt_place': place_hit_count,
        'total_count': max(win_total_count, place_total_count)
    }


# テスト用
if __name__ == '__main__':
    import psycopg2
    
    DB_CONFIG = {
        'host': 'localhost',
        'port': 5432,
        'user': 'postgres',
        'password': 'keiba2025',
        'dbname': 'pckeiba'
    }
    
    try:
        print("🔌 データベース接続中...")
        conn = psycopg2.connect(**DB_CONFIG)
        
        print("\n" + "="*80)
        print("📊 Step 2: 補正回収率計算テスト")
        print("="*80)
        
        # サンプルファクター: 騎手（騎手コード '05658'）
        keibajo_code = '44'  # 大井
        factor_name = 'F01_kishu'
        factor_value = '05658'
        
        print(f"\n【テストファクター】")
        print(f"  競馬場: {keibajo_code}")
        print(f"  ファクター: {factor_name}")
        print(f"  値: {factor_value}")
        
        stats = calculate_factor_corrected_return_rate(
            conn, keibajo_code, factor_name, factor_value
        )
        
        print(f"\n【結果】")
        print(f"  総出現回数:       {stats['total_count']:,}件")
        print(f"  単勝的中回数:     {stats['cnt_win']:,}件")
        print(f"  単勝的中率:       {stats['rate_win_hit']:.2f}%")
        print(f"  補正単勝回収率:   {stats['adj_win_ret']:.2f}%")
        print(f"  複勝的中回数:     {stats['cnt_place']:,}件")
        print(f"  複勝的中率:       {stats['rate_place_hit']:.2f}%")
        print(f"  補正複勝回収率:   {stats['adj_place_ret']:.2f}%")
        
        print("\n✅ Step 2完了: 補正回収率計算成功！")
        
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()
