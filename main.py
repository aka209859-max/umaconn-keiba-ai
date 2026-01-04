"""
NAR AI予想システム - メインスクリプト

実行方法:
    python main.py [対象日付]
    
例:
    python main.py              # 明日の予想を生成
    python main.py 20260106     # 2026年1月6日の予想を生成
"""

import sys
import psycopg2
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.db_config import DB_CONFIG
from core.data_fetcher import (
    get_tomorrow_date,
    get_tomorrow_races,
    get_races_by_date,
    get_race_info,
    enrich_horse_data_with_prev_race
)
from core.aas_calculator import calculate_race_aas_scores
from core.prediction_generator import save_all_predictions


def main():
    """
    メイン処理
    """
    # 対象日付の取得
    if len(sys.argv) > 1:
        target_date = sys.argv[1]
    else:
        target_date = get_tomorrow_date()
    
    print(f"{'='*50}")
    print(f"NAR AI予想システム")
    print(f"対象日付: {target_date}")
    print(f"{'='*50}\n")
    
    # データベース接続
    print("📊 データベースに接続中...")
    conn = psycopg2.connect(**DB_CONFIG)
    
    try:
        # ステップ1: 対象レース一覧を取得
        print("\n【ステップ1】対象レース一覧取得")
        races = get_races_by_date(conn, target_date)
        
        if not races:
            print("❌ 対象日のレースデータが見つかりません")
            return
        
        print(f"✅ 対象レース数: {len(races)}レース\n")
        
        # ステップ2: 出走馬データ取得
        print("【ステップ2】出走馬データ取得")
        horses = get_tomorrow_races(conn, target_date)
        
        if not horses:
            print("❌ 出走馬データが見つかりません")
            return
        
        print(f"✅ 出走馬数: {len(horses)}頭\n")
        
        # ステップ3: 前走データ追加
        print("【ステップ3】前走データ取得・統合")
        enriched_horses = enrich_horse_data_with_prev_race(conn, horses, target_date)
        print(f"✅ データ統合完了\n")
        
        # ステップ4: レース情報取得
        print("【ステップ4】レース情報取得")
        race_infos = {}
        for race in races:
            keibajo_code = race['keibajo_code']
            race_bango = race['race_bango']
            kaisai_date = race['kaisai_date']
            
            race_info = get_race_info(conn, keibajo_code, kaisai_date, race_bango)
            race_key = f"{keibajo_code}_{race_bango}"
            race_infos[race_key] = race_info
        
        print(f"✅ レース情報取得完了: {len(race_infos)}レース\n")
        
        # ステップ5: レースごとにAAS得点計算
        print("【ステップ5】AAS得点計算")
        all_predictions = defaultdict(list)
        
        for race in races:
            keibajo_code = race['keibajo_code']
            race_bango = race['race_bango']
            race_key = f"{keibajo_code}_{race_bango}"
            
            # このレースの出走馬を抽出
            race_horses = [
                h for h in enriched_horses
                if h['keibajo_code'] == keibajo_code and h['race_bango'] == race_bango
            ]
            
            if not race_horses:
                print(f"  ⚠️  {keibajo_code} {race_bango}R: 出走馬データなし")
                continue
            
            # レース情報
            race_info = race_infos.get(race_key)
            if not race_info:
                print(f"  ⚠️  {keibajo_code} {race_bango}R: レース情報なし")
                continue
            
            # レース情報に競馬場コードを追加
            race_info['keibajo_code'] = keibajo_code
            
            # AAS得点計算
            try:
                predictions = calculate_race_aas_scores(conn, race_horses, race_info)
                
                all_predictions[keibajo_code].append({
                    'race_bango': race_bango,
                    'predictions': predictions
                })
                
                # 1位の馬を表示
                if predictions:
                    top_horse = predictions[0]
                    print(f"  ✅ {keibajo_code} {race_bango}R: "
                          f"{top_horse['umaban']}番 {top_horse['bamei']} "
                          f"(AAS: {top_horse['total_aas']:.1f}点)")
            
            except Exception as e:
                print(f"  ❌ {keibajo_code} {race_bango}R: エラー - {e}")
                continue
        
        print(f"\n✅ AAS得点計算完了: {sum(len(v) for v in all_predictions.values())}レース\n")
        
        # ステップ6: 予想をファイル保存
        print("【ステップ6】予想ファイル保存")
        base_output_dir = "E:/UmaData/nar-analytics-python/predictions"
        
        saved_files = save_all_predictions(
            all_predictions,
            race_infos,
            target_date,
            base_output_dir
        )
        
        # 保存結果表示
        print(f"\n✅ 基本予想: {len(saved_files['basic'])}ファイル")
        print(f"✅ note用: {len(saved_files['note'])}ファイル")
        print(f"✅ プレミアム: {len(saved_files['premium'])}ファイル")
        
        print(f"\n{'='*50}")
        print(f"✅ 予想生成完了！")
        print(f"出力先: {base_output_dir}/{target_date}/")
        print(f"{'='*50}")
    
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print("\n📊 データベース接続を閉じました")


if __name__ == '__main__':
    main()
