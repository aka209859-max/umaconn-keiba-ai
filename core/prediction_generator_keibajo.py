"""
予想生成・TXT出力モジュール（競馬場ごと出力対応版）

CEO要求:
- 競馬場ごとに1ファイル（レースごとではない）
- シンプル版（主要ファクター非表示）
- ランク: SS/S/A/B/C/D/E/F
"""

import os
from datetime import datetime
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.course_master import KEIBAJO_NAMES


def assign_rank(aas_score):
    """
    AAS得点からランクを割り当て
    
    Args:
        aas_score: AAS得点
    
    Returns:
        str: ランク（SS/S/A/B/C/D/E/F）
    """
    if aas_score >= 20:
        return 'SS'
    elif aas_score >= 15:
        return 'S'
    elif aas_score >= 10:
        return 'A'
    elif aas_score >= 5:
        return 'B'
    elif aas_score >= 0:
        return 'C'
    elif aas_score >= -5:
        return 'D'
    elif aas_score >= -10:
        return 'E'
    else:
        return 'F'


def generate_keibajo_prediction_text(keibajo_code, races_data, target_date):
    """
    競馬場別の予想TXTを生成
    
    Args:
        keibajo_code: 競馬場コード
        races_data: [
            {
                'race_bango': レース番号,
                'race_info': レース情報,
                'predictions': ソート済みの予想結果
            },
            ...
        ]
        target_date: 対象日付（YYYYMMDD形式）
    
    Returns:
        str: TXT形式の予想文
    """
    keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
    
    # 日付フォーマット（YYYYMMDD → YYYY年MM月DD日）
    year = target_date[:4]
    month = target_date[4:6]
    day = target_date[6:8]
    date_str = f"{year}年{month}月{day}日"
    
    output = "=" * 80 + "\n"
    output += f"{date_str} {keibajo_name}競馬場 全レース予想\n"
    output += "=" * 80 + "\n\n"
    
    for race in races_data:
        race_bango = race['race_bango']
        race_info = race['race_info']
        predictions = race['predictions']
        
        # レース情報
        kyori = race_info.get('kyori', '不明')
        track_code = race_info.get('track_code', '不明')
        track_name = 'ダート' if track_code == '24' else 'その他'
        joken_name = race_info.get('kyoso_joken_meisho', '不明')
        
        output += "━" * 80 + "\n"
        output += f"■ {race_bango.zfill(2)}R {track_name}{kyori}m {joken_name}\n"
        output += "━" * 80 + "\n\n"
        
        # 予想ランキング
        output += "順位  馬番  馬名              最終AAS得点  ランク\n"
        output += "-" * 80 + "\n"
        
        for i, pred in enumerate(predictions, 1):
            umaban = pred.get('umaban', '??')
            bamei = pred.get('bamei', '不明')
            total_aas = pred.get('total_aas', 0.0)
            rank = assign_rank(total_aas)
            
            # 馬名を16文字に調整（日本語対応）
            bamei_display = bamei[:8] if len(bamei) > 8 else bamei
            bamei_display = bamei_display + '　' * (8 - len(bamei_display))
            
            output += f" {i:2d}    {umaban:>3s}   {bamei_display}   {total_aas:>+7.1f}      {rank}\n"
        
        output += "\n"
    
    # フッター
    output += "=" * 80 + "\n"
    output += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += "NAR AI予想システム by Enable\n"
    output += "=" * 80 + "\n"
    
    return output


def save_keibajo_prediction(keibajo_code, races_data, target_date, output_dir):
    """
    競馬場別の予想をファイルに保存
    
    Args:
        keibajo_code: 競馬場コード
        races_data: レースデータ
        target_date: 対象日付（YYYYMMDD形式）
        output_dir: 出力ディレクトリ
    
    Returns:
        str: 保存したファイルパス
    """
    keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
    
    # 予想テキスト生成
    prediction_text = generate_keibajo_prediction_text(keibajo_code, races_data, target_date)
    
    # ファイル保存
    os.makedirs(output_dir, exist_ok=True)
    filename = f"{target_date}_{keibajo_name}_予想.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(prediction_text)
    
    return filepath


def save_all_predictions_by_keibajo(all_predictions, target_date, base_output_dir):
    """
    全ての予想を競馬場ごとに保存
    
    Args:
        all_predictions: {
            'keibajo_code': [
                {
                    'race_bango': レース番号,
                    'race_info': レース情報,
                    'predictions': 予想結果
                },
                ...
            ],
            ...
        }
        target_date: 対象日付（YYYYMMDD形式）
        base_output_dir: ベース出力ディレクトリ
    
    Returns:
        list: 保存したファイルパスのリスト
    """
    saved_files = []
    
    # 日付別ディレクトリ
    output_dir = os.path.join(base_output_dir, target_date)
    
    # 競馬場ごとに保存
    for keibajo_code, races_data in all_predictions.items():
        filepath = save_keibajo_prediction(
            keibajo_code, races_data, target_date, output_dir
        )
        saved_files.append(filepath)
    
    return saved_files


# テスト用
if __name__ == '__main__':
    # サンプルデータ
    test_predictions = {
        '44': [  # 大井
            {
                'race_bango': '01',
                'race_info': {
                    'kyori': '1200',
                    'track_code': '24',
                    'kyoso_joken_meisho': '3歳未勝利'
                },
                'predictions': [
                    {
                        'umaban': '14',
                        'bamei': 'テストホース',
                        'total_aas': 28.5
                    },
                    {
                        'umaban': '11',
                        'bamei': 'サンプルウマ',
                        'total_aas': 25.3
                    },
                    {
                        'umaban': '4',
                        'bamei': 'ダミーホース',
                        'total_aas': 22.8
                    }
                ]
            },
            {
                'race_bango': '02',
                'race_info': {
                    'kyori': '1600',
                    'track_code': '24',
                    'kyoso_joken_meisho': 'サラ系3歳'
                },
                'predictions': [
                    {
                        'umaban': '7',
                        'bamei': 'モックウマ',
                        'total_aas': 30.2
                    },
                    {
                        'umaban': '3',
                        'bamei': 'テストバ',
                        'total_aas': 27.1
                    }
                ]
            }
        ]
    }
    
    target_date = '20250105'
    output_dir = './test_output'
    
    saved_files = save_all_predictions_by_keibajo(
        test_predictions, target_date, output_dir
    )
    
    print("✅ テスト完了")
    print(f"保存ファイル: {saved_files}")
