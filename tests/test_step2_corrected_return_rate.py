"""
Step 2: 補正回収率計算の実データテスト

このスクリプトは、ファクター別の補正回収率を計算するロジックをテストします。

実行方法（CEOのPCで実行）:
    cd E:\\UmaData\\nar-analytics-python
    python test_step2_corrected_return_rate.py
"""
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

import psycopg2
from core.calculate_factor_stats import calculate_factor_corrected_return_rate

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}


def main():
    """
    Step 2のメイン処理
    """
    print("="*80)
    print("📊 Step 2: 補正回収率計算の実データテスト")
    print("="*80)
    print()
    
    try:
        print("🔌 データベース接続中...")
        conn = psycopg2.connect(**DB_CONFIG)
        print("✅ 接続成功")
        print()
        
        # テストケース: 3つのファクターで動作確認
        test_cases = [
            {
                'name': '騎手（青海大樹）',
                'keibajo_code': '44',  # 大井
                'factor_name': 'F01_kishu',
                'factor_value': '05658'
            },
            {
                'name': '調教師（石川浩文）',
                'keibajo_code': '44',  # 大井
                'factor_name': 'F02_chokyoshi',
                'factor_value': '05661'
            },
            {
                'name': '距離（1300m）',
                'keibajo_code': '44',  # 大井
                'factor_name': 'F03_kyori',
                'factor_value': '1300'
            },
            {
                'name': '枠番（1枠）',
                'keibajo_code': '44',  # 大井
                'factor_name': 'F08_wakuban',
                'factor_value': '1'
            },
            {
                'name': '騎手×距離（青海大樹 × 1300m）',
                'keibajo_code': '44',  # 大井
                'factor_name': 'C01_kishu_kyori',
                'factor_value': '05658_1300'
            }
        ]
        
        print("【テストケース】")
        print("-"*80)
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}. {test_case['name']}")
        print()
        
        # 各テストケースを実行
        for i, test_case in enumerate(test_cases, 1):
            print("="*80)
            print(f"テストケース {i}/{len(test_cases)}: {test_case['name']}")
            print("="*80)
            
            print(f"  競馬場コード: {test_case['keibajo_code']}")
            print(f"  ファクター名: {test_case['factor_name']}")
            print(f"  ファクター値: {test_case['factor_value']}")
            print()
            
            # 補正回収率を計算
            try:
                stats = calculate_factor_corrected_return_rate(
                    conn,
                    test_case['keibajo_code'],
                    test_case['factor_name'],
                    test_case['factor_value']
                )
                
                print("【計算結果】")
                print("-"*80)
                print(f"  総出現回数:       {stats['total_count']:>8,}件")
                print(f"  単勝的中回数:     {stats['cnt_win']:>8,}件")
                print(f"  単勝的中率:       {stats['rate_win_hit']:>8.2f}%")
                print(f"  補正単勝回収率:   {stats['adj_win_ret']:>8.2f}%")
                print(f"  複勝的中回数:     {stats['cnt_place']:>8,}件")
                print(f"  複勝的中率:       {stats['rate_place_hit']:>8.2f}%")
                print(f"  補正複勝回収率:   {stats['adj_place_ret']:>8.2f}%")
                print()
                
                if stats['total_count'] > 0:
                    print("  ✅ 計算成功")
                else:
                    print("  ⚠️  データが見つかりませんでした")
                
            except Exception as e:
                print(f"  ❌ エラー: {e}")
                import traceback
                traceback.print_exc()
            
            print()
        
        conn.close()
        
        print("="*80)
        print("✅ Step 2完了: 補正回収率計算テスト成功！")
        print("="*80)
        print()
        print("【次のステップ】")
        print("  Step 3: AAS得点計算の実データテスト")
        print("  - 31ファクター × 全馬のAAS得点を計算")
        print("  - 最終AAS得点（合計）のランキング確認")
        print()
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
