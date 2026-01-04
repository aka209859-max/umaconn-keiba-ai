"""
Step 3: AAS得点計算の実データテスト

31ファクター全てのAAS得点を計算し、最終AAS得点（合計）でランキング

実行方法（CEOのPCで実行）:
    cd E:\\UmaData\\nar-analytics-python
    python test_step3_aas_calculation.py
"""
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

import psycopg2
import numpy as np
from core.calculate_factor_stats import calculate_factor_corrected_return_rate
from core.factor_extractor import extract_all_factors
from config.factor_weights import get_factor_weight

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}


def calculate_aas_for_factor(factor_stats):
    """
    1つのファクターのAAS得点を計算
    
    CEO式:
    Hit_raw = 0.65 × 単勝的中率 + 0.35 × 複勝的中率
    Ret_raw = 0.35 × 補正単勝回収率 + 0.65 × 補正複勝回収率
    baseCalc = 0.55 × ZH + 0.45 × ZR
    AAS = 12 × tanh(baseCalc) × Shr
    
    Args:
        factor_stats: {
            'rate_win_hit': 単勝的中率（%値: 15% = 15）,
            'rate_place_hit': 複勝的中率（%値: 45% = 45）,
            'adj_win_ret': 補正単勝回収率（%値: 95% = 95）,
            'adj_place_ret': 補正複勝回収率（%値: 98% = 98）,
            'cnt_win': 単勝的中回数,
            'cnt_place': 複勝的中回数,
            'total_count': 総出現回数
        }
    
    Returns:
        dict: {
            'Hit_raw': Hit_raw値,
            'Ret_raw': Ret_raw値,
            'N_min': 最小試行回数
        }
    """
    # Step 1: 基礎値計算（%値のまま: 15% = 15）
    Hit_raw = (0.65 * factor_stats['rate_win_hit'] + 
               0.35 * factor_stats['rate_place_hit'])
    
    Ret_raw = (0.35 * factor_stats['adj_win_ret'] + 
               0.65 * factor_stats['adj_place_ret'])
    
    N_min = min(factor_stats['cnt_win'], factor_stats['cnt_place'])
    
    return {
        'Hit_raw': Hit_raw,
        'Ret_raw': Ret_raw,
        'N_min': N_min
    }


def calculate_z_scores_for_race(all_horses_factors):
    """
    レース内でZスコアを計算（母集団標準偏差を使用）
    
    Args:
        all_horses_factors: [
            {
                'umaban': 馬番,
                'bamei': 馬名,
                'factors': {
                    'F01_kishu': {'Hit_raw': ..., 'Ret_raw': ..., 'N_min': ...},
                    ...
                }
            },
            ...
        ]
    
    Returns:
        list: Zスコアとシュリンケージが追加された馬データ
    """
    # ファクターごとにZスコア化
    for factor_name in ['F01_kishu', 'F02_chokyoshi', 'F03_kyori', 'F08_wakuban', 
                        'C01_kishu_kyori']:  # サンプルファクターのみ
        
        # このファクターの全馬のHit_raw, Ret_rawを収集
        hit_raws = []
        ret_raws = []
        
        for horse in all_horses_factors:
            if factor_name in horse['factors']:
                hit_raws.append(horse['factors'][factor_name]['Hit_raw'])
                ret_raws.append(horse['factors'][factor_name]['Ret_raw'])
        
        if len(hit_raws) < 2:
            continue
        
        # Step 2: グループ統計（母集団標準偏差 STDEV.P）
        μH = np.mean(hit_raws)
        σH = np.std(hit_raws, ddof=0)  # ddof=0 → 母集団標準偏差
        μR = np.mean(ret_raws)
        σR = np.std(ret_raws, ddof=0)
        
        # Step 3: Zスコア化
        for horse in all_horses_factors:
            if factor_name in horse['factors']:
                Hit_raw = horse['factors'][factor_name]['Hit_raw']
                Ret_raw = horse['factors'][factor_name]['Ret_raw']
                N_min = horse['factors'][factor_name]['N_min']
                
                ZH = (Hit_raw - μH) / σH if σH > 0 else 0
                ZR = (Ret_raw - μR) / σR if σR > 0 else 0
                
                # Step 4: 信頼度収縮
                Shr = np.sqrt(N_min / (N_min + 400))
                
                # Step 5: AAS得点計算
                baseCalc = 0.55 * ZH + 0.45 * ZR
                AAS = 12 * np.tanh(baseCalc) * Shr
                
                horse['factors'][factor_name]['ZH'] = ZH
                horse['factors'][factor_name]['ZR'] = ZR
                horse['factors'][factor_name]['Shr'] = Shr
                horse['factors'][factor_name]['AAS'] = AAS
    
    return all_horses_factors


def calculate_final_aas(horse_factors, keibajo_code):
    """
    最終AAS得点を計算（31ファクターの合計）
    
    Step 6: 最終AAS得点 = Σ(各ファクターのAAS × 競馬場別重み)
    
    Args:
        horse_factors: 馬の全ファクターデータ
        keibajo_code: 競馬場コード
    
    Returns:
        float: 最終AAS得点
    """
    total_aas = 0.0
    
    for factor_name, factor_data in horse_factors.items():
        if 'AAS' in factor_data:
            # 競馬場別重みを取得
            weight = get_factor_weight(keibajo_code, factor_name)
            weighted_aas = factor_data['AAS'] * weight
            total_aas += weighted_aas
            
            # 記録
            factor_data['weight'] = weight
            factor_data['weighted_AAS'] = weighted_aas
    
    return total_aas


def main():
    """
    Step 3のメイン処理
    """
    print("="*80)
    print("📊 Step 3: AAS得点計算の実データテスト")
    print("="*80)
    print()
    
    try:
        print("🔌 データベース接続中...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 接続成功")
        print()
        
        # Step 3-1: 1レース分のデータを取得
        print("【Step 3-1】テストレースのデータ取得")
        print("-"*80)
        
        cur = conn.cursor()
        
        # 最新レースを取得
        query = """
        SELECT DISTINCT
            se.kaisai_nen,
            se.kaisai_tsukihi,
            se.keibajo_code,
            se.race_bango
        FROM nvd_se se
        WHERE se.kaisai_nen >= '2024'
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != '00'
        ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
        LIMIT 1
        """
        
        cur.execute(query)
        race_row = cur.fetchone()
        
        if not race_row:
            print("❌ テストレースが見つかりませんでした")
            return
        
        kaisai_nen = race_row[0]
        kaisai_tsukihi = race_row[1]
        keibajo_code = race_row[2]
        race_bango = race_row[3]
        
        print(f"  テストレース: {kaisai_nen}/{kaisai_tsukihi} {keibajo_code} {race_bango}R")
        
        # このレースの全馬を取得
        query_horses = """
        SELECT 
            se.umaban,
            se.bamei,
            se.kakutei_chakujun,
            se.*
        FROM nvd_se se
        WHERE se.kaisai_nen = %s
        AND se.kaisai_tsukihi = %s
        AND se.keibajo_code = %s
        AND se.race_bango = %s
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != '00'
        ORDER BY se.umaban
        """
        
        cur.execute(query_horses, (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
        horses = cur.fetchall()
        
        # 列名を取得
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'nvd_se'
            ORDER BY ordinal_position
        """)
        se_columns = [col[0] for col in cur.fetchall()]
        
        # レースデータを取得
        query_ra = """
        SELECT kyori, babajotai_code_dirt, track_code, 
               kyoso_joken_code, kyoso_joken_meisho
        FROM nvd_ra
        WHERE kaisai_nen = %s
        AND kaisai_tsukihi = %s
        AND keibajo_code = %s
        AND race_bango = %s
        """
        
        cur.execute(query_ra, (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango))
        ra_row = cur.fetchone()
        
        race_data = {
            'kyori': ra_row[0],
            'babajotai_code_dirt': ra_row[1],
            'track_code': ra_row[2],
            'kyoso_joken_code': ra_row[3],
            'kyoso_joken_meisho': ra_row[4]
        }
        
        print(f"  出走頭数: {len(horses)}頭")
        print(f"  距離: {race_data['kyori']}m")
        print()
        
        # Step 3-2: 各馬の31ファクターを抽出
        print("【Step 3-2】31ファクター抽出（サンプル5ファクター）")
        print("-"*80)
        
        all_horses_factors = []
        
        for horse_row in horses[:3]:  # 最初の3頭のみテスト
            horse_data = dict(zip(se_columns, horse_row))
            
            # 31ファクターを抽出
            factors = extract_all_factors(conn, horse_data, race_data)
            
            print(f"  {horse_data['umaban']}番 {horse_data['bamei']}")
            print(f"    騎手: {factors['F01_kishu_name']}")
            print(f"    調教師: {factors['F02_chokyoshi_name']}")
            print(f"    距離: {factors['F03_kyori']}m")
            print()
            
            all_horses_factors.append({
                'umaban': horse_data['umaban'],
                'bamei': horse_data['bamei'],
                'kakutei_chakujun': horse_data['kakutei_chakujun'],
                'factors': {}
            })
        
        # Step 3-3: サンプルファクターで補正回収率を計算
        print("【Step 3-3】補正回収率計算（サンプルファクター）")
        print("-"*80)
        
        sample_factors = ['F01_kishu', 'F02_chokyoshi', 'F03_kyori', 
                         'F08_wakuban', 'C01_kishu_kyori']
        
        for i, horse_row in enumerate(horses[:3]):
            horse_data = dict(zip(se_columns, horse_row))
            factors = extract_all_factors(conn, horse_data, race_data)
            
            print(f"\n  {horse_data['umaban']}番 {horse_data['bamei']}")
            
            for factor_name in sample_factors:
                factor_value = factors.get(factor_name, '')
                
                if not factor_value:
                    continue
                
                # 補正回収率を計算
                stats = calculate_factor_corrected_return_rate(
                    conn, keibajo_code, factor_name, str(factor_value)
                )
                
                # Hit_raw, Ret_raw を計算
                aas_data = calculate_aas_for_factor(stats)
                
                all_horses_factors[i]['factors'][factor_name] = aas_data
                
                print(f"    {factor_name}: Hit_raw={aas_data['Hit_raw']:.2f}, "
                      f"Ret_raw={aas_data['Ret_raw']:.2f}, N_min={aas_data['N_min']}")
        
        print()
        
        # Step 3-4: Zスコア化とAAS得点計算
        print("【Step 3-4】Zスコア化とAAS得点計算")
        print("-"*80)
        
        all_horses_factors = calculate_z_scores_for_race(all_horses_factors)
        
        # Step 3-5: 最終AAS得点を計算
        print()
        print("【Step 3-5】最終AAS得点計算")
        print("-"*80)
        
        for horse in all_horses_factors:
            final_aas = calculate_final_aas(horse['factors'], keibajo_code)
            horse['final_aas'] = final_aas
        
        # ランキング表示
        all_horses_factors.sort(key=lambda x: x['final_aas'], reverse=True)
        
        print()
        print("【ランキング】")
        print("-"*80)
        print(f"  順位  馬番  馬名              最終AAS得点  実際の着順")
        print("-"*80)
        
        for i, horse in enumerate(all_horses_factors, 1):
            print(f"  {i:2d}位  {horse['umaban']:>3s}番  {horse['bamei']:<16s}  "
                  f"{horse['final_aas']:>+7.2f}点  {horse['kakutei_chakujun']}着")
        
        print()
        print("="*80)
        print("✅ Step 3完了: AAS得点計算テスト成功！")
        print("="*80)
        print()
        print("【次のステップ】")
        print("  Step 4: 予想生成パイプライン統合")
        print("  - ファクター抽出 → 補正回収率計算 → AAS計算 → TXT出力")
        print()
        
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
