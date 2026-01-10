# タスク3: 位置指数の枠順係数再計算ツール

**作成日**: 2026-01-10  
**目的**: 全競馬場×距離別の単勝/複勝的中率から最適な枠順係数を算出

---

## 📋 実装仕様

### **入力データ**
- **期間**: 2016-01-01 〜 2025-12-31
- **対象**: 全14競馬場
- **距離**: 各競馬場の全距離
- **必要カラム**:
  - 競馬場コード (keibajo_code)
  - 距離 (kyori)
  - 枠番 (wakuban)
  - 出走頭数 (tosu)
  - 着順 (chakujun)
  - 単勝オッズ (tansho_odds)
  - 複勝オッズ (fukusho_odds)

### **分析指標**
1. **単勝的中率**: 枠番別の1着率
2. **複勝的中率**: 枠番別の3着以内率
3. **単勝回収率**: 枠番別の平均回収率
4. **複勝回収率**: 枠番別の平均回収率

### **出力形式**
```python
# CSV出力
keibajo_code,keibajo_name,kyori,wakuban,races,win_rate,place_rate,win_roi,place_roi,optimal_coeff
30,門別,1000,1,450,15.2,42.3,85.5,92.1,+2.5
30,門別,1000,2,445,14.8,41.1,83.2,90.5,+1.8
...
```

---

## 🔧 実装コード

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
\"\"\"
位置指数の枠順係数再計算ツール

全競馬場×距離別の単勝/複勝的中率から最適な枠順係数を算出
\"\"\"

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from collections import defaultdict

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config.course_master import KEIBAJO_NAMES


def calculate_waku_statistics(
    db_path: str,
    start_date: str = '2016-01-01',
    end_date: str = '2025-12-31'
) -> pd.DataFrame:
    \"\"\"
    枠番別の統計を計算
    
    Args:
        db_path: データベースパス
        start_date: 開始日
        end_date: 終了日
    
    Returns:
        枠番別統計のDataFrame
    \"\"\"
    conn = sqlite3.connect(db_path)
    
    query = f\"\"\"
    SELECT 
        keibajo_code,
        kyori,
        wakuban,
        tosu,
        chakujun,
        tansho_odds,
        fukusho_odds
    FROM race_results
    WHERE 
        kaisai_date BETWEEN '{start_date}' AND '{end_date}'
        AND keibajo_code IN ('30','35','36','42','43','44','45','46','47','48','50','51','54','55')
        AND wakuban > 0
        AND chakujun > 0
    \"\"\"
    
    df = pd.read_sql_query(query, conn)
    conn.close()
    
    # 統計計算
    stats_list = []
    
    for (keibajo, kyori), group in df.groupby(['keibajo_code', 'kyori']):
        for wakuban in range(1, 9):  # 1-8枠
            waku_data = group[group['wakuban'] == wakuban]
            
            if len(waku_data) < 10:  # 最低10レース
                continue
            
            # 的中率計算
            total_races = len(waku_data)
            win_count = len(waku_data[waku_data['chakujun'] == 1])
            place_count = len(waku_data[waku_data['chakujun'] <= 3])
            
            win_rate = (win_count / total_races * 100) if total_races > 0 else 0
            place_rate = (place_count / total_races * 100) if total_races > 0 else 0
            
            # 回収率計算
            win_roi = 0.0
            place_roi = 0.0
            
            if win_count > 0:
                win_payouts = waku_data[waku_data['chakujun'] == 1]['tansho_odds'].sum()
                win_roi = (win_payouts / total_races * 100) if total_races > 0 else 0
            
            if place_count > 0:
                place_payouts = waku_data[waku_data['chakujun'] <= 3]['fukusho_odds'].sum()
                place_roi = (place_payouts / total_races * 100) if total_races > 0 else 0
            
            stats_list.append({
                'keibajo_code': keibajo,
                'keibajo_name': KEIBAJO_NAMES.get(keibajo, keibajo),
                'kyori': kyori,
                'wakuban': wakuban,
                'races': total_races,
                'win_rate': round(win_rate, 2),
                'place_rate': round(place_rate, 2),
                'win_roi': round(win_roi, 2),
                'place_roi': round(place_roi, 2)
            })
    
    stats_df = pd.DataFrame(stats_list)
    
    # 最適係数の計算
    stats_df = calculate_optimal_coefficients(stats_df)
    
    return stats_df


def calculate_optimal_coefficients(df: pd.DataFrame) -> pd.DataFrame:
    \"\"\"
    競馬場×距離別の最適枠順係数を計算
    
    基準: 全枠の平均的中率を0とし、各枠の偏差から係数を算出
    \"\"\"
    df['optimal_coeff'] = 0.0
    
    for (keibajo, kyori), group in df.groupby(['keibajo_code', 'kyori']):
        # 平均的中率
        avg_win_rate = group['win_rate'].mean()
        avg_place_rate = group['place_rate'].mean()
        
        # 的中率の偏差を係数化
        # 複勝的中率を重視（単勝:複勝 = 3:7）
        for idx in group.index:
            win_diff = group.loc[idx, 'win_rate'] - avg_win_rate
            place_diff = group.loc[idx, 'place_rate'] - avg_place_rate
            
            # 係数 = (単勝偏差 × 0.3 + 複勝偏差 × 0.7) / 2
            coeff = (win_diff * 0.3 + place_diff * 0.7) / 2
            
            df.loc[idx, 'optimal_coeff'] = round(coeff, 2)
    
    return df


def generate_summary_report(df: pd.DataFrame, output_dir: str = 'output'):
    \"\"\"
    サマリーレポートを生成
    \"\"\"
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. 全体サマリー
    summary = []
    for (keibajo, kyori), group in df.groupby(['keibajo_code', 'kyori']):
        keibajo_name = group['keibajo_name'].iloc[0]
        
        # 内枠（1-3枠）vs 外枠（6-8枠）
        inner = group[group['wakuban'] <= 3]
        outer = group[group['wakuban'] >= 6]
        
        if len(inner) > 0 and len(outer) > 0:
            inner_win = inner['win_rate'].mean()
            outer_win = outer['win_rate'].mean()
            inner_place = inner['place_rate'].mean()
            outer_place = outer['place_rate'].mean()
            
            summary.append({
                'keibajo_code': keibajo,
                'keibajo_name': keibajo_name,
                'kyori': kyori,
                'inner_win_rate': round(inner_win, 2),
                'outer_win_rate': round(outer_win, 2),
                'win_bias': round(inner_win - outer_win, 2),
                'inner_place_rate': round(inner_place, 2),
                'outer_place_rate': round(outer_place, 2),
                'place_bias': round(inner_place - outer_place, 2)
            })
    
    summary_df = pd.DataFrame(summary)
    summary_df.to_csv(f'{output_dir}/waku_bias_summary.csv', index=False, encoding='utf-8-sig')
    
    print(f\"\\n✅ サマリーレポート: {output_dir}/waku_bias_summary.csv\")
    print(f\"\\n【内枠有利度トップ5】（複勝的中率差）\")
    top5 = summary_df.nlargest(5, 'place_bias')
    for _, row in top5.iterrows():
        print(f\"  {row['keibajo_name']:6} {row['kyori']:4}m: 内枠 {row['inner_place_rate']:.1f}% vs 外枠 {row['outer_place_rate']:.1f}% (差 +{row['place_bias']:.1f}%)\")


def main():
    \"\"\"メイン実行\"\"\"
    import argparse
    
    parser = argparse.ArgumentParser(description='位置指数の枠順係数再計算')
    parser.add_argument('--db', default='data/nar_races.db', help='データベースパス')
    parser.add_argument('--start', default='2016-01-01', help='開始日')
    parser.add_argument('--end', default='2025-12-31', help='終了日')
    parser.add_argument('--output', default='output', help='出力ディレクトリ')
    
    args = parser.parse_args()
    
    print(\"=\"*60)
    print(\"位置指数の枠順係数再計算\")
    print(\"=\"*60)
    print(f\"期間: {args.start} 〜 {args.end}\")
    print(f\"データベース: {args.db}\")
    print(f\"出力先: {args.output}\")
    
    # 統計計算
    print(\"\\n枠番別統計を計算中...\")
    stats_df = calculate_waku_statistics(args.db, args.start, args.end)
    
    # CSV出力
    os.makedirs(args.output, exist_ok=True)
    output_path = f'{args.output}/waku_coefficients.csv'
    stats_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print(f\"\\n✅ 枠順係数: {output_path}\")
    print(f\"   総データ数: {len(stats_df)}行\")
    
    # サマリーレポート
    generate_summary_report(stats_df, args.output)
    
    print(\"\\n✅ 完了！\")


if __name__ == \"__main__\":
    main()
```

---

## 🚀 実行方法

```bash
# CEO環境（Windows）
E:
cd \\UmaData\\nar-analytics-python-v2

# 実行
python scripts\\calculate_waku_coefficients.py --db data\\nar_races.db --output output

# 出力ファイル
# output/waku_coefficients.csv        - 全競馬場×距離×枠番の係数
# output/waku_bias_summary.csv        - 内枠vs外枠のバイアスサマリー
```

---

## 📊 出力例

### **waku_coefficients.csv**
```csv
keibajo_code,keibajo_name,kyori,wakuban,races,win_rate,place_rate,win_roi,place_roi,optimal_coeff
30,門別,1000,1,450,15.2,42.3,85.5,92.1,+2.5
30,門別,1000,2,445,14.8,41.1,83.2,90.5,+1.8
30,門別,1000,3,448,13.5,39.8,79.8,88.3,+0.5
30,門別,1000,4,442,12.1,38.2,75.5,85.1,-0.8
30,門別,1000,5,438,11.8,37.5,73.2,83.9,-1.2
30,門別,1000,6,435,10.5,35.8,68.9,81.2,-2.5
30,門別,1000,7,430,9.8,34.2,65.1,78.5,-3.8
30,門別,1000,8,425,8.5,32.1,60.3,75.2,-5.2
```

### **waku_bias_summary.csv**
```csv
keibajo_code,keibajo_name,kyori,inner_win_rate,outer_win_rate,win_bias,inner_place_rate,outer_place_rate,place_bias
30,門別,1000,14.5,9.6,+4.9,41.1,34.0,+7.1
30,門別,1200,13.8,10.2,+3.6,39.5,35.8,+3.7
```

---

**作成者**: Enable CEO & AI戦略家  
**Play to Win!** 🚀
