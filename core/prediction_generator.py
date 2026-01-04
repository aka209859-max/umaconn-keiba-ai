"""
予想生成・TXT出力モジュール
"""

import os
from datetime import datetime
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.course_master import KEIBAJO_NAMES


def generate_prediction_text(race_data, predictions, race_info):
    """
    AI予想をTXT形式で出力
    
    Args:
        race_data: レースデータ（keibajo_code, race_bango）
        predictions: 予想結果（AAS得点でソート済み）
        race_info: レース情報（距離、馬場状態等）
    
    Returns:
        str: TXT形式の予想文
    """
    keibajo_code = race_data['keibajo_code']
    race_bango = race_data['race_bango']
    keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
    
    # ヘッダー
    output = f"{keibajo_name}競馬 {race_bango}R AI予想\n"
    output += f"━━━━━━━━━━━━━━━━━━\n\n"
    
    # レース情報
    if race_info:
        kyori = race_info.get('kyori', '不明')
        track_code_map = {'1': '芝', '2': 'ダート', '3': '障害'}
        track = track_code_map.get(race_info.get('track_code', ''), '不明')
        output += f"【レース情報】\n"
        output += f"距離: {kyori}m ({track})\n"
        output += f"出走頭数: {race_info.get('tosu', '不明')}頭\n\n"
    
    # 上位3頭
    if len(predictions) >= 3:
        top_3 = predictions[:3]
        marks = ['◎本命', '○対抗', '▲穴']
        
        for i, (mark, pred) in enumerate(zip(marks, top_3)):
            output += f"{mark}: {pred['umaban']}番 {pred['bamei']}\n"
            output += f"  騎手: {pred.get('kishu_mei', '不明')}\n"
            output += f"  AAS総合得点: {pred['total_aas']:.1f}点\n"
            
            # 前走情報
            if pred.get('prev_chakujun'):
                output += f"  前走: {pred.get('prev_chakujun', '-')}着"
                if pred.get('prev_corner_4'):
                    output += f" (4角{pred.get('prev_corner_4', '-')}位)"
                output += "\n"
            
            output += "\n"
    else:
        # 3頭未満の場合
        for i, pred in enumerate(predictions):
            marks = ['◎本命', '○対抗', '▲穴']
            mark = marks[i] if i < len(marks) else '△注'
            output += f"{mark}: {pred['umaban']}番 {pred['bamei']}\n"
            output += f"  AAS総合得点: {pred['total_aas']:.1f}点\n\n"
    
    # フッター
    output += f"━━━━━━━━━━━━━━━━━━\n"
    output += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    output += f"AI予想システム by Enable\n"
    
    return output


def generate_note_summary(all_predictions, target_date):
    """
    note投稿用の全レースまとめを生成
    
    Args:
        all_predictions: 全レースの予想結果（競馬場別）
        target_date: 対象日付（YYYYMMDD形式）
    
    Returns:
        dict: 競馬場別のまとめテキスト
    """
    keibajo_summaries = {}
    
    for keibajo_code, races in all_predictions.items():
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
        
        output = f"{keibajo_name}競馬 全{len(races)}R AI予想\n"
        output += f"{'='*40}\n\n"
        
        for race in races:
            race_bango = race['race_bango']
            predictions = race['predictions']
            
            output += f"【{race_bango}R】\n"
            
            if len(predictions) >= 3:
                output += f"◎{predictions[0]['umaban']}番 {predictions[0]['bamei']}\n"
                output += f"○{predictions[1]['umaban']}番 {predictions[1]['bamei']}\n"
                output += f"▲{predictions[2]['umaban']}番 {predictions[2]['bamei']}\n"
            
            output += "\n"
        
        output += f"{'='*40}\n"
        output += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        keibajo_summaries[keibajo_code] = output
    
    return keibajo_summaries


def generate_premium_content(all_predictions):
    """
    有料コンテンツ用の高期待値TOP10を生成
    
    Args:
        all_predictions: 全レースの予想結果
    
    Returns:
        str: プレミアムコンテンツのテキスト
    """
    # 全レース・全馬からAAS得点TOP10を抽出
    all_horses = []
    
    for keibajo_code, races in all_predictions.items():
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
        
        for race in races:
            race_bango = race['race_bango']
            for pred in race['predictions']:
                all_horses.append({
                    'keibajo_name': keibajo_name,
                    'keibajo_code': keibajo_code,
                    'race_bango': race_bango,
                    **pred
                })
    
    # AAS得点でソート
    all_horses.sort(key=lambda x: x['total_aas'], reverse=True)
    top_10 = all_horses[:10]
    
    output = f"高期待値 TOP10（全競馬場）\n"
    output += f"{'='*40}\n\n"
    
    for i, horse in enumerate(top_10, 1):
        output += f"【第{i}位】AAS得点: {horse['total_aas']:.1f}点\n"
        output += f"{horse['keibajo_name']} {horse['race_bango']}R\n"
        output += f"{horse['umaban']}番 {horse['bamei']}\n"
        output += f"騎手: {horse.get('kishu_mei', '不明')}\n"
        
        if horse.get('prev_chakujun'):
            output += f"前走: {horse.get('prev_chakujun', '-')}着\n"
        
        output += "\n"
    
    output += f"{'='*40}\n"
    output += f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return output


def save_prediction_file(content, output_dir, filename):
    """
    予想をファイルに保存
    
    Args:
        content: 保存する内容
        output_dir: 出力ディレクトリ
        filename: ファイル名
    
    Returns:
        str: 保存したファイルパス
    """
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return filepath


def save_all_predictions(all_predictions, race_infos, target_date, base_output_dir):
    """
    全ての予想を保存
    
    Args:
        all_predictions: 全レースの予想結果（競馬場別）
        race_infos: 全レースのレース情報
        target_date: 対象日付（YYYYMMDD形式）
        base_output_dir: ベース出力ディレクトリ
    
    Returns:
        dict: 保存したファイルパスのリスト
    """
    saved_files = {
        'basic': [],
        'note': [],
        'premium': []
    }
    
    # 日付別ディレクトリ
    date_dir = os.path.join(base_output_dir, target_date)
    note_dir = os.path.join(date_dir, 'note')
    premium_dir = os.path.join(date_dir, 'premium')
    
    # 1. 基本予想（レースごと）
    for keibajo_code, races in all_predictions.items():
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
        
        for race in races:
            race_bango = race['race_bango']
            predictions = race['predictions']
            
            # レース情報取得
            race_key = f"{keibajo_code}_{race_bango}"
            race_info = race_infos.get(race_key)
            
            # 予想テキスト生成
            race_data = {
                'keibajo_code': keibajo_code,
                'race_bango': race_bango
            }
            prediction_text = generate_prediction_text(race_data, predictions, race_info)
            
            # ファイル保存
            filename = f"{keibajo_name}_{race_bango.zfill(2)}R.txt"
            filepath = save_prediction_file(prediction_text, date_dir, filename)
            saved_files['basic'].append(filepath)
    
    # 2. note投稿用（競馬場別まとめ）
    note_summaries = generate_note_summary(all_predictions, target_date)
    for keibajo_code, summary_text in note_summaries.items():
        keibajo_name = KEIBAJO_NAMES.get(keibajo_code, '不明')
        filename = f"{keibajo_name}競馬_全レース.txt"
        filepath = save_prediction_file(summary_text, note_dir, filename)
        saved_files['note'].append(filepath)
    
    # 3. プレミアムコンテンツ（高期待値TOP10）
    premium_text = generate_premium_content(all_predictions)
    filename = "高期待値_TOP10.txt"
    filepath = save_prediction_file(premium_text, premium_dir, filename)
    saved_files['premium'].append(filepath)
    
    return saved_files


# テスト用
if __name__ == '__main__':
    # サンプルデータ
    race_data = {
        'keibajo_code': '44',
        'race_bango': '01'
    }
    
    predictions = [
        {
            'umaban': '3',
            'bamei': 'テストホース',
            'kishu_mei': 'テスト騎手',
            'total_aas': 67.5,
            'prev_chakujun': '2',
            'prev_corner_4': '3'
        },
        {
            'umaban': '7',
            'bamei': 'サンプルウマ',
            'kishu_mei': 'サンプル騎手',
            'total_aas': 62.3,
            'prev_chakujun': '1',
            'prev_corner_4': '1'
        },
        {
            'umaban': '5',
            'bamei': 'ダミーホース',
            'kishu_mei': 'ダミー騎手',
            'total_aas': 58.9,
            'prev_chakujun': '4',
            'prev_corner_4': '5'
        }
    ]
    
    race_info = {
        'kyori': '1600',
        'track_code': '2',
        'tosu': '12'
    }
    
    # 予想テキスト生成
    prediction_text = generate_prediction_text(race_data, predictions, race_info)
    print(prediction_text)
