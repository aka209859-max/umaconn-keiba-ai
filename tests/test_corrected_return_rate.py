"""
Step 2: 補正回収率計算の実データテスト

サンプルファクター（騎手）で補正回収率を計算
"""
import psycopg2
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.odds_correction import get_odds_correction_factor

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}

# 期間別重み（2016-2025）
YEAR_WEIGHTS = {
    '2016': 1, '2017': 2, '2018': 3, '2019': 4, '2020': 5,
    '2021': 6, '2022': 7, '2023': 8, '2024': 9, '2025': 10
}

# 目標払戻額
TARGET_PAYOUT = 10000

def safe_float(value, default=0.0):
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value, default=0):
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default

try:
    print("🔌 データベース接続中...")
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 Step 2: 補正回収率計算テスト")
    print("="*80)
    
    # サンプルファクター: 騎手を1名選択
    print("\n【Step 1】サンプル騎手を選択")
    print("-"*80)
    
    query = """
        SELECT kishu_code, kishumei_ryakusho, COUNT(*) as race_count
        FROM nvd_se
        WHERE kaisai_nen >= '2016' AND kaisai_nen <= '2025'
        AND kishu_code IS NOT NULL AND kishu_code != ''
        GROUP BY kishu_code, kishumei_ryakusho
        HAVING COUNT(*) >= 100
        ORDER BY COUNT(*) DESC
        LIMIT 1
    """
    
    cur.execute(query)
    row = cur.fetchone()
    
    if not row:
        print("❌ サンプル騎手が見つかりませんでした")
        exit(1)
    
    kishu_code = row[0]
    kishu_name = row[1]
    race_count = row[2]
    
    print(f"  サンプル騎手: {kishu_name} ({kishu_code})")
    print(f"  レース数: {race_count:,}件")
    
    # 過去データを集計（2016-2025年）
    print("\n【Step 2】過去データ集計（2016-2025年）")
    print("-"*80)
    
    query = """
        SELECT 
            se.kaisai_nen,
            se.tansho_odds,
            se.fukusho_odds,
            se.kakutei_chakujun,
            se.tansho_haito,
            se.fukusho_haito
        FROM nvd_se se
        WHERE se.kishu_code = %s
        AND se.kaisai_nen >= '2016' AND se.kaisai_nen <= '2025'
        AND se.kakutei_chakujun IS NOT NULL
        AND se.tansho_odds IS NOT NULL
        ORDER BY se.kaisai_nen, se.kaisai_tsukihi
    """
    
    cur.execute(query, (kishu_code,))
    rows = cur.fetchall()
    
    print(f"  取得データ数: {len(rows):,}件")
    
    # 単勝・複勝の補正回収率を計算
    print("\n【Step 3】補正回収率を計算")
    print("-"*80)
    
    # 単勝
    total_win_weighted_payout = 0.0
    total_win_weighted_bet = 0.0
    win_hit_count = 0
    win_total_count = 0
    
    # 複勝
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
    win_corrected_return_rate = 0.0
    if total_win_weighted_bet > 0:
        win_corrected_return_rate = (total_win_weighted_payout / total_win_weighted_bet) * 100
    
    place_corrected_return_rate = 0.0
    if total_place_weighted_bet > 0:
        place_corrected_return_rate = (total_place_weighted_payout / total_place_weighted_bet) * 100
    
    # 的中率を計算
    win_hit_rate = 0.0
    if win_total_count > 0:
        win_hit_rate = (win_hit_count / win_total_count) * 100
    
    place_hit_rate = 0.0
    if place_total_count > 0:
        place_hit_rate = (place_hit_count / place_total_count) * 100
    
    print("\n【単勝】")
    print(f"  件数:            {win_total_count:,}件")
    print(f"  的中数:          {win_hit_count:,}件")
    print(f"  的中率:          {win_hit_rate:.2f}%")
    print(f"  補正回収率:      {win_corrected_return_rate:.2f}%")
    
    print("\n【複勝】")
    print(f"  件数:            {place_total_count:,}件")
    print(f"  的中数:          {place_hit_count:,}件")
    print(f"  的中率:          {place_hit_rate:.2f}%")
    print(f"  補正回収率:      {place_corrected_return_rate:.2f}%")
    
    print("\n" + "="*80)
    print("✅ Step 2完了: 補正回収率計算成功！")
    print("="*80)
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()
