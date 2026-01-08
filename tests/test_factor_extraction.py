"""
ファクター抽出のテストスクリプト
"""
import sys
sys.path.append('E:\\UmaData\\nar-analytics-python')

import psycopg2
from core.factor_extractor import extract_all_factors

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
    cur = conn.cursor()
    
    print("\n" + "="*80)
    print("📊 最新レースデータを取得")
    print("="*80)
    
    # 最新レースの1頭分のデータを取得
    query = """
        SELECT 
            se.*
        FROM nvd_se se
        WHERE se.kaisai_nen >= '2024'
        ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        LIMIT 1
    """
    
    cur.execute(query)
    row = cur.fetchone()
    
    if not row:
        print("❌ テストデータが見つかりませんでした")
        exit(1)
    
    # 列名を取得
    cur.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'nvd_se'
        ORDER BY ordinal_position
    """)
    se_columns = [col[0] for col in cur.fetchall()]
    
    # horse_data を作成
    horse_data = dict(zip(se_columns, row))
    
    # レースデータを取得
    query_ra = """
        SELECT kyori, babajotai_code_dirt, mawari_code, 
               kyoso_joken_code, kyoso_joken_meisho
        FROM nvd_ra
        WHERE kaisai_nen = %s
        AND kaisai_tsukihi = %s
        AND keibajo_code = %s
        AND race_bango = %s
    """
    
    cur.execute(query_ra, (
        horse_data['kaisai_nen'],
        horse_data['kaisai_tsukihi'],
        horse_data['keibajo_code'],
        horse_data['race_bango']
    ))
    
    ra_row = cur.fetchone()
    
    if not ra_row:
        print("❌ レースデータが見つかりませんでした")
        exit(1)
    
    # race_data を作成
    race_data = {
        'kyori': ra_row[0],
        'babajotai_code_dirt': ra_row[1],
        'mawari_code': ra_row[2],
        'kyoso_joken_code': ra_row[3],
        'kyoso_joken_meisho': ra_row[4]
    }
    
    print(f"\n  レース: {horse_data['kaisai_nen']}/{horse_data['kaisai_tsukihi']} "
          f"{horse_data['keibajo_code']} {horse_data['race_bango']}R")
    print(f"  馬名: {horse_data['bamei']}")
    print(f"  騎手: {horse_data['kishumei_ryakusho']}")
    
    print("\n" + "="*80)
    print("🔍 31ファクター抽出テスト")
    print("="*80)
    
    # ファクター抽出
    factors = extract_all_factors(conn, horse_data, race_data)
    
    print("\n【単独ファクター（16個）】")
    print("-"*80)
    print(f"  F01 騎手:          {factors['F01_kishu_name']} ({factors['F01_kishu']})")
    print(f"  F02 調教師:        {factors['F02_chokyoshi_name']} ({factors['F02_chokyoshi']})")
    print(f"  F03 距離適性:      {factors['F03_kyori']}m")
    print(f"  F04 馬場状態:      {factors['F04_baba']}")
    print(f"  F05 回り:          {factors['F05_mawari']}")
    print(f"  F06 条件:          {factors['F06_joken_name']} ({factors['F06_joken']})")
    print(f"  F07 脚質:          {factors['F07_kyakushitsu']}")
    print(f"  F08 枠番:          {factors['F08_wakuban']}")
    print(f"  F09 前走着順:      {factors['F09_prev_chakujun']}着")
    print(f"  F10 前走人気:      {factors['F10_prev_ninki']}番人気")
    print(f"  F11 前走距離:      {factors['F11_prev_kyori']}m")
    print(f"  F12 前走馬場:      {factors['F12_prev_baba']}")
    print(f"  F13 休養週数:      {factors['F13_kyuyo_weeks']}週")
    print(f"  F14 馬体重:        {factors['F14_bataiju']}kg")
    print(f"  F15 馬体重増減:    {factors['F15_zogen_sa']:+d}kg")
    print(f"  F16 性別:          {factors['F16_seibetsu']}")
    
    print("\n【組み合わせファクター（15個）】")
    print("-"*80)
    print(f"  C01 騎手×距離:                {factors['C01_kishu_kyori']}")
    print(f"  C02 騎手×馬場状態:            {factors['C02_kishu_baba']}")
    print(f"  C03 騎手×回り:                {factors['C03_kishu_mawari']}")
    print(f"  C04 騎手×条件:                {factors['C04_kishu_joken']}")
    print(f"  C05 調教師×距離:              {factors['C05_chokyoshi_kyori']}")
    print(f"  C06 調教師×馬場状態:          {factors['C06_chokyoshi_baba']}")
    print(f"  C07 距離×馬場状態:            {factors['C07_kyori_baba']}")
    print(f"  C08 距離×回り:                {factors['C08_kyori_mawari']}")
    print(f"  C09 脚質×距離:                {factors['C09_kyakushitsu_kyori']}")
    print(f"  C10 脚質×馬場状態:            {factors['C10_kyakushitsu_baba']}")
    print(f"  C11 枠番×距離:                {factors['C11_wakuban_kyori']}")
    print(f"  C12 前走着順×休養週数:        {factors['C12_prev_chakujun_kyuyo']}")
    print(f"  C13 前走人気×前走着順:        {factors['C13_prev_ninki_chakujun']}")
    print(f"  C14 馬体重増減×休養週数:      {factors['C14_zogen_kyuyo']}")
    print(f"  C15 性別×距離:                {factors['C15_seibetsu_kyori']}")
    
    print("\n✅ 全31ファクター抽出成功！")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"\n❌ エラー: {e}")
    import traceback
    traceback.print_exc()
