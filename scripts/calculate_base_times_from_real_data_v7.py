#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
基準タイム計算スクリプト（実データ版 v7 - 競馬場コード修正版）
- 競馬場コード修正: 公式発表の正しいコードを使用
  - 30=門別, 35=盛岡, 36=水沢, 42=浦和, 43=船橋, 44=大井, 45=川崎
  - 46=金沢, 47=笠松, 48=名古屋, 50=園田, 51=姫路, 54=高知, 55=佐賀
- 馬場状態コード: '1'（良馬場）
- soha_time: 「分+0.1秒」フォーマット（例: 1134 → 1分13.4秒 = 73.4秒）
- kohan_3f: 0.1秒単位（例: 370 → 37.0秒）
"""

import sys
import os
from datetime import datetime

sys.path.append('E:\\UmaData\\nar-analytics-python-v2')

from config.db_config import get_db_connection
from core.ten_3f_estimator import Ten3FEstimator

def convert_soha_time(soha_time_raw):
    """
    soha_time を秒に変換
    フォーマット: 「分+0.1秒」
    例: 1134 → 1分13.4秒 = 73.4秒
    """
    soha_time_int = int(float(soha_time_raw))
    minutes = soha_time_int // 1000  # 先頭の桁
    remainder = soha_time_int % 1000  # 残り
    seconds = remainder / 10.0
    return minutes * 60 + seconds

def convert_kohan_3f(kohan_3f_raw):
    """
    kohan_3f を秒に変換
    フォーマット: 0.1秒単位
    例: 370 → 37.0秒
    """
    return float(kohan_3f_raw) / 10.0

def calculate_base_times_from_real_data():
    """実データから基準タイムを計算"""
    
    # 出力ディレクトリを作成
    output_dir = 'E:\\UmaData\\nar-analytics-python-v2\\output'
    os.makedirs(output_dir, exist_ok=True)
    
    # 出力ファイルパス
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(output_dir, f'base_times_result_{timestamp}.txt')
    
    # ファイルを開く
    with open(output_file, 'w', encoding='utf-8') as f:
        # Ten3FEstimator を初期化
        msg = "🔧 Ten3FEstimator を初期化中..."
        print(msg)
        f.write(msg + "\n")
        
        estimator = Ten3FEstimator()
        
        msg = "✅ Ten3FEstimator 初期化完了"
        print(msg)
        f.write(msg + "\n")
        
        msg = "\n" + "=" * 80 + "\n実データから基準タイムを計算中（時間フォーマット対応版）\n" + "=" * 80 + "\n"
        print(msg)
        f.write(msg + "\n")
        
        # データベース接続
        conn = get_db_connection()
        cur = conn.cursor()
        
        # 対象競馬場コード（正しい公式コード）
        # 30=門別, 35=盛岡, 36=水沢, 42=浦和, 43=船橋, 44=大井, 45=川崎, 46=金沢, 47=笠松, 48=名古屋, 50=園田, 51=姫路, 54=高知, 55=佐賀
        keibajo_codes = ['30', '35', '36', '42', '43', '44', '45', '46', '47', '48', '50', '51', '54', '55']
        
        base_times = {}
        
        for keibajo_code in keibajo_codes:
            msg = f"\n競馬場コード: {keibajo_code}\n" + "-" * 80
            print(msg)
            f.write(msg + "\n")
            
            # 距離リストを取得
            cur.execute("""
                SELECT DISTINCT CAST(kyori AS INTEGER)
                FROM nvd_ra
                WHERE keibajo_code = %s
                    AND kyori ~ '^[0-9]+$'
                ORDER BY CAST(kyori AS INTEGER)
            """, (keibajo_code,))
            
            kyori_list = [int(row[0]) for row in cur.fetchall() if row[0]]
            
            base_times[keibajo_code] = {}
            
            for kyori in kyori_list:
                # レースデータを取得（良馬場・上位5頭）
                cur.execute("""
                SELECT 
                    se.soha_time,
                    se.kohan_3f,
                    CASE WHEN se.corner_1 ~ '^[0-9]+$' THEN CAST(se.corner_1 AS INTEGER) ELSE 0 END as corner_1,
                    CASE WHEN se.corner_2 ~ '^[0-9]+$' THEN CAST(se.corner_2 AS INTEGER) ELSE 0 END as corner_2,
                    CAST(ra.shusso_tosu AS INTEGER) as shusso_tosu,
                    se.kakutei_chakujun
                FROM nvd_ra ra
                JOIN nvd_se se ON 
                    ra.kaisai_nen = se.kaisai_nen AND
                    ra.keibajo_code = se.keibajo_code AND
                    ra.kaisai_tsukihi = se.kaisai_tsukihi AND
                    ra.race_bango = se.race_bango
                WHERE ra.keibajo_code = %s
                    AND CAST(ra.kyori AS INTEGER) = %s
                    AND (ra.babajotai_code_dirt = '1' OR ra.babajotai_code_shiba = '1')
                    AND se.soha_time IS NOT NULL
                    AND se.soha_time != ''
                    AND se.soha_time ~ '^[0-9.]+$'
                    AND se.kohan_3f IS NOT NULL
                    AND se.kohan_3f != ''
                    AND se.kohan_3f ~ '^[0-9.]+$'
                    AND se.kakutei_chakujun IS NOT NULL
                    AND se.kakutei_chakujun != ''
                    AND se.kakutei_chakujun ~ '^[0-9]+$'
                    AND CAST(se.kakutei_chakujun AS INTEGER) BETWEEN 1 AND 5
                LIMIT 1000
                """, (keibajo_code, kyori))
                
                rows = cur.fetchall()
                
                # データ不足の場合はスキップ
                if len(rows) < 10:
                    msg = f"  距離 {kyori:4d}m: ⚠️ データ不足（{len(rows)}件）スキップ"
                    print(msg)
                    f.write(msg + "\n")
                    continue
                
                # 前半3Fと後半3Fのリスト
                zenhan_3f_list = []
                kohan_3f_list = []
                
                for row in rows:
                    try:
                        # 🔥 重要：時間フォーマット変換
                        soha_time = convert_soha_time(row[0])
                        kohan_3f = convert_kohan_3f(row[1])
                        corner_1 = int(row[2]) if row[2] else 0
                        corner_2 = int(row[3]) if row[3] else 0
                        tosu = int(row[4]) if row[4] else 12
                        
                        # 前半3Fを推定
                        if kyori == 1200:
                            # 1200m戦は確定値
                            zenhan_3f = soha_time - kohan_3f
                            method = "確定値"
                        else:
                            # 1400m以上はTen3FEstimatorで推定
                            result = estimator.estimate(
                                time_seconds=soha_time,
                                kohan_3f_seconds=kohan_3f,
                                corner_1=corner_1,
                                corner_2=corner_2,
                                kyori=kyori,
                                field_size=tosu
                            )
                            zenhan_3f = result['ten_3f_final']
                            method = "AI推定"
                        
                        zenhan_3f_list.append(zenhan_3f)
                        kohan_3f_list.append(kohan_3f)
                    except Exception as e:
                        # エラー時はスキップ
                        continue
                
                # データ不足の場合はスキップ
                if len(zenhan_3f_list) < 10:
                    msg = f"  距離 {kyori:4d}m: ⚠️ データ不足（{len(zenhan_3f_list)}件）スキップ"
                    print(msg)
                    f.write(msg + "\n")
                    continue
                
                # 中央値を計算
                zenhan_3f_list.sort()
                kohan_3f_list.sort()
                
                n = len(zenhan_3f_list)
                median_zenhan_3f = zenhan_3f_list[n // 2] if n % 2 == 1 else (zenhan_3f_list[n // 2 - 1] + zenhan_3f_list[n // 2]) / 2
                median_kohan_3f = kohan_3f_list[n // 2] if n % 2 == 1 else (kohan_3f_list[n // 2 - 1] + kohan_3f_list[n // 2]) / 2
                
                # 結果を保存
                base_times[keibajo_code][kyori] = {
                    'zenhan_3f': round(median_zenhan_3f, 1),
                    'kohan_3f': round(median_kohan_3f, 1),
                    'race_count': n
                }
                
                msg = f"  距離 {kyori:4d}m: 前半3F={median_zenhan_3f:.1f}秒, 後半3F={median_kohan_3f:.1f}秒 ({method}, サンプル数: {n:4d})"
                print(msg)
                f.write(msg + "\n")
        
        cur.close()
        conn.close()
        
        msg = "\n" + "=" * 80 + "\n✅ 基準タイム計算完了\n" + "=" * 80
        print(msg)
        f.write(msg + "\n")
        
        # BASE_TIMES を出力
        f.write("\n以下を config/base_times.py に貼り付けてください：\n\n")
        f.write("BASE_TIMES = {\n")
        for keibajo_code in sorted(base_times.keys()):
            f.write(f"  '{keibajo_code}': {{\n")
            for kyori in sorted(base_times[keibajo_code].keys()):
                data = base_times[keibajo_code][kyori]
                f.write(f"    {kyori}: {{'zenhan_3f': {data['zenhan_3f']}, 'kohan_3f': {data['kohan_3f']}, 'race_count': {data['race_count']}}},\n")
            f.write("  },\n")
        f.write("}\n")
        
        f.write(f"\n保存先: E:\\UmaData\\nar-analytics-python-v2\\config\\base_times.py\n")
    
    print(f"\n✅ 結果を保存しました: {output_file}")

if __name__ == "__main__":
    calculate_base_times_from_real_data()
