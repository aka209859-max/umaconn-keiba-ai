#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
HQS指数実績データ収集スクリプト（競馬場別期間対応版）
================================================================================
4つの指数の実績を競馬場別の適切な期間で集計：
- テン指数
- 位置指数
- 上がり指数
- ペース指数

競馬場別期間設定:
- 大井（42）: 2023年10月〜2025年12月31日（砂変更後）
- 名古屋（47）: 2022年4月〜2025年12月31日（大幅改修後）
- その他: 2016年1月〜2025年12月31日（長期データ）
================================================================================
"""

import sys
import os
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple
import logging

# ロギング設定（ファイルとコンソールの両方に出力）
log_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'output', f'collect_index_stats_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=logging.DEBUG,  # DEBUG レベルに変更
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
logger.info(f"ログファイル: {log_file}")

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from config.db_config import get_db_connection
from core.index_calculator import (
    calculate_ten_index,
    calculate_position_index,
    calculate_agari_index,
    calculate_pace_index,
    safe_float,
    safe_int
)


# ================================================================================
# 競馬場別期間設定
# ================================================================================

# パターンA: 砂変更後（大井）
SAND_CHANGE_TRACKS = {
    '42': {
        'name': '大井',
        'start_date': '20231001',
        'end_date': '20251231',
        'reason': 'オーストラリア産白砂への全面置換'
    }
}

# パターンB: 大幅改修後（名古屋）
RENOVATION_TRACKS = {
    '47': {
        'name': '名古屋',
        'start_date': '20220401',
        'end_date': '20251231',
        'reason': '大幅改修実施'
    }
}

# パターンC: 長期データ（その他）
STANDARD_TRACKS = [
    '30',  # 門別（北海道）
    '35',  # 盛岡（岩手）
    '36',  # 金沢（石川）
    '43',  # 川崎（神奈川）
    '44',  # 船橋（千葉）
    '45',  # 浦和（埼玉）
    '46',  # 笠松（岐阜）
    '48',  # 園田（兵庫）
    '49',  # 姫路（兵庫）
    '50',  # 高知（高知）
    '51',  # 佐賀（佐賀）
]

# 除外対象
EXCLUDED_TRACKS = ['83', '54']  # 帯広ばんえい、高知（race_bango='12'のみ除外）


def get_period_for_track(keibajo_code: str) -> Tuple[str, str, str]:
    """
    競馬場コードから適切な集計期間を取得
    
    Returns:
        (start_date, end_date, reason)
    """
    if keibajo_code in SAND_CHANGE_TRACKS:
        track_info = SAND_CHANGE_TRACKS[keibajo_code]
        return (track_info['start_date'], track_info['end_date'], track_info['reason'])
    elif keibajo_code in RENOVATION_TRACKS:
        track_info = RENOVATION_TRACKS[keibajo_code]
        return (track_info['start_date'], track_info['end_date'], track_info['reason'])
    else:
        return ('20160101', '20251231', '長期データ（大幅改修なし）')


# ================================================================================
# データ取得
# ================================================================================

def parse_corner_position(corner_str: str, umaban: str, debug=False) -> int:
    """
    nvd_ra.corner_tsuka_juni_X から指定馬番のコーナー順位を取得
    
    フォーマット例: "21(3,5),8,10,1,4,13,"
    - 2 = 2番馬が1位
    - 1 = 1番馬が2位  
    - (3,5) = 3番馬と5番馬が同着3位
    - 8 = 8番馬が5位
    
    Args:
        corner_str: コーナー通過順位文字列
        umaban: 馬番（文字列または整数）
        debug: デバッグログを出力するか
    
    Returns:
        コーナー順位（見つからない場合は0）
    """
    if not corner_str or corner_str.strip() == '' or corner_str == '00':
        if debug:
            logger.debug(f"コーナーデータなし: corner_str='{corner_str}', umaban={umaban}")
        return 0
    
    try:
        target_umaban = str(umaban).strip()
        # 0埋めパターンも試す（例: '01', '02', ...）
        target_umaban_padded = target_umaban.zfill(2)
        position = 1  # 順位カウンター
        
        # カンマで分割（先に全体のスペースを削除）
        parts = [p.strip() for p in corner_str.strip().rstrip(',').split(',')]
        
        for part in parts:
            if not part:
                continue
            
            # 同着の場合: (3,5) のような形式、または (3,4)-9 のようなパターン
            if '(' in part:
                # カッコの中身のみを抽出
                bracket_content = part[part.index('(')+1:part.index(')')]
                horses = bracket_content.split(',')
                for horse in horses:
                    horse_stripped = horse.strip()
                    if horse_stripped == target_umaban or horse_stripped == target_umaban_padded:
                        if debug:
                            logger.debug(f"✅ 同着で発見: corner_str='{corner_str}', umaban={umaban}, position={position}")
                        return position
                position += len(horses)
            else:
                # ハイフンやイコールで繋がっている場合の処理
                # 例: '6-8', '3=8', '2-6' → 最初の馬番のみを使用
                cleaned_part = part.split('-')[0].split('=')[0].strip()
                
                if cleaned_part == target_umaban or cleaned_part == target_umaban_padded:
                    if debug:
                        logger.debug(f"✅ 発見: corner_str='{corner_str}', umaban={umaban}, position={position}, part='{part}', cleaned='{cleaned_part}'")
                    return position
                position += 1
        
        if debug:
            logger.debug(f"❌ 見つからず: corner_str='{corner_str}', umaban={umaban}, target={target_umaban}/{target_umaban_padded}, parts={parts}")
        return 0  # 見つからない場合
    except Exception as e:
        logger.warning(f"コーナー順位パースエラー (馬番{umaban}): {e}")
        return 0


def parse_fukusho_odds(odds_fukusho_str: str, umaban: str) -> float:
    """
    nvd_o1.odds_fukusho から指定馬番の複勝オッズを取得
    
    フォーマット: 固定長 336文字
    各馬番のオッズは16文字ブロック:
    - 馬番(2桁) + オッズ(5桁) + 人気(3桁) + 票数(5桁) + 予備(1桁)
    
    例: 01001000130 = 馬番01、オッズ10.0、人気013
    """
    if not odds_fukusho_str or odds_fukusho_str.strip() == '':
        return 0.0
    
    try:
        # 馬番を2桁に変換
        target_umaban = str(umaban).zfill(2)
        
        # 16文字ごとに分割
        block_size = 16
        for i in range(0, len(odds_fukusho_str), block_size):
            block = odds_fukusho_str[i:i+block_size]
            if len(block) < 7:  # 最低限のデータがない場合スキップ
                continue
            
            # 馬番(2桁) + オッズ(5桁)
            uma = block[0:2]
            odds_str = block[2:7]
            
            if uma == target_umaban:
                # オッズ文字列を数値に変換（例: "00130" → 1.3）
                if odds_str.strip() == '' or '*' in odds_str or '-' in odds_str:
                    return 0.0
                odds_value = float(odds_str) / 100.0
                return odds_value
        
        return 0.0
    except Exception as e:
        print(f"Warning: 複勝オッズパースエラー (馬番{umaban}): {e}")
        return 0.0


def collect_race_data(conn, keibajo_code: str, start_date: str, end_date: str) -> List[Dict]:
    """
    指定期間・競馬場のレースデータを取得
    """
    cursor = conn.cursor()
    
    query = """
    SELECT 
        ra.kaisai_nen,
        ra.kaisai_tsukihi,
        ra.keibajo_code,
        ra.race_bango,
        ra.kyori,
        ra.track_code,
        ra.babajotai_code_dirt as baba_code,
        ra.corner_tsuka_juni_1,
        ra.corner_tsuka_juni_2,
        ra.corner_tsuka_juni_3,
        ra.corner_tsuka_juni_4,
        se.umaban,
        se.kakutei_chakujun,
        se.kohan_3f,
        se.soha_time,
        se.tansho_odds,
        od.odds_fukusho
    FROM nvd_ra ra
    JOIN nvd_se se ON 
        ra.kaisai_nen = se.kaisai_nen AND
        ra.kaisai_tsukihi = se.kaisai_tsukihi AND
        ra.keibajo_code = se.keibajo_code AND
        ra.race_bango = se.race_bango
    LEFT JOIN nvd_o1 od ON
        ra.kaisai_nen = od.kaisai_nen AND
        ra.kaisai_tsukihi = od.kaisai_tsukihi AND
        ra.keibajo_code = od.keibajo_code AND
        ra.race_bango = od.race_bango
    WHERE ra.keibajo_code = %s
        AND ra.kaisai_nen || ra.kaisai_tsukihi >= %s
        AND ra.kaisai_nen || ra.kaisai_tsukihi <= %s
        AND CAST(ra.kyori AS INTEGER) >= 1400
        AND se.kakutei_chakujun IS NOT NULL
        AND se.kakutei_chakujun != ''
        AND se.kakutei_chakujun ~ '^[0-9]+$'
    """
    
    # 高知の最終レース除外
    if keibajo_code == '54':
        query += " AND ra.race_bango != '12'"
    
    query += " ORDER BY ra.kaisai_nen, ra.kaisai_tsukihi, ra.race_bango"
    
    cursor.execute(query, (keibajo_code, start_date, end_date))
    
    columns = [desc[0] for desc in cursor.description]
    races = []
    debug_count = 0  # デバッグ用カウンター
    for row in cursor.fetchall():
        race_data = dict(zip(columns, row))
        
        # nvd_ra.corner_tsuka_juni_X から個別馬のコーナー順位を抽出
        umaban = race_data.get('umaban', '01')
        enable_debug = (debug_count < 10)  # 最初の10件のみデバッグログ出力
        
        race_data['corner_1'] = parse_corner_position(race_data.get('corner_tsuka_juni_1', ''), umaban, debug=enable_debug)
        race_data['corner_2'] = parse_corner_position(race_data.get('corner_tsuka_juni_2', ''), umaban, debug=enable_debug)
        race_data['corner_3'] = parse_corner_position(race_data.get('corner_tsuka_juni_3', ''), umaban, debug=enable_debug)
        race_data['corner_4'] = parse_corner_position(race_data.get('corner_tsuka_juni_4', ''), umaban, debug=enable_debug)
        
        if enable_debug:
            # corner_tsuka_juni の生データも出力
            logger.debug(f"📊 レース{debug_count+1}: 馬番={umaban}")
            logger.debug(f"   corner_tsuka_juni_1 = '{race_data.get('corner_tsuka_juni_1', '')}' → c1={race_data['corner_1']}")
            logger.debug(f"   corner_tsuka_juni_2 = '{race_data.get('corner_tsuka_juni_2', '')}' → c2={race_data['corner_2']}")
            logger.debug(f"   corner_tsuka_juni_3 = '{race_data.get('corner_tsuka_juni_3', '')}' → c3={race_data['corner_3']}")
            logger.debug(f"   corner_tsuka_juni_4 = '{race_data.get('corner_tsuka_juni_4', '')}' → c4={race_data['corner_4']}")
            debug_count += 1
        
        # nvd_o1.odds_fukusho から馬番のオッズを抽出
        if 'odds_fukusho' in race_data and race_data['odds_fukusho']:
            fukusho_odds = parse_fukusho_odds(
                race_data['odds_fukusho'], 
                race_data.get('umaban', '01')
            )
            race_data['fukusho_odds'] = fukusho_odds
        else:
            race_data['fukusho_odds'] = 0.0
        
        races.append(race_data)
    
    cursor.close()
    return races


def estimate_zenhan_3f(soha_time: float, kohan_3f: float, kyori: int) -> float:
    """
    前半3Fを推定（簡易版）
    
    推定式: zenhan_3f = (soha_time - kohan_3f) × (600 / (kyori - 600))
    """
    if kohan_3f is None or kohan_3f <= 0:
        # デフォルト値（距離から推定）
        return 36.0 + (kyori - 1200) * 0.003
    
    remaining_distance = kyori - 600
    if remaining_distance <= 0:
        return 36.0
    
    remaining_time = soha_time - kohan_3f
    zenhan_3f = remaining_time * (600.0 / remaining_distance)
    
    # 妥当性チェック（30〜45秒の範囲）
    if zenhan_3f < 30.0 or zenhan_3f > 45.0:
        return 36.0 + (kyori - 1200) * 0.003
    
    return zenhan_3f


def calculate_indexes_for_horse(horse_data: Dict) -> Dict[str, float]:
    """
    1頭の馬の4つの指数を計算
    """
    # データの安全な取得
    kyori = safe_int(horse_data.get('kyori'), 1200)
    soha_time = safe_float(horse_data.get('soha_time'), 0.0)
    kohan_3f = safe_float(horse_data.get('kohan_3f'), 0.0)
    baba_code = str(horse_data.get('baba_code', '1'))
    keibajo_code = str(horse_data.get('keibajo_code', '42'))
    tosu = safe_int(horse_data.get('tosu'), 10)
    
    corner_1 = safe_int(horse_data.get('corner_1'), 0)
    corner_2 = safe_int(horse_data.get('corner_2'), 0)
    corner_3 = safe_int(horse_data.get('corner_3'), 0)
    corner_4 = safe_int(horse_data.get('corner_4'), 0)
    
    # Ten3F推定
    zenhan_3f = estimate_zenhan_3f(soha_time, kohan_3f, kyori)
    
    # 4つの指数を計算
    try:
        ten_index = calculate_ten_index(
            zenhan_3f=zenhan_3f,
            kyori=kyori,
            baba_code=baba_code,
            keibajo_code=keibajo_code
        )
    except Exception as e:
        ten_index = 0.0
    
    try:
        position_index = calculate_position_index(
            corner_1=corner_1,
            corner_2=corner_2,
            corner_3=corner_3,
            corner_4=corner_4,
            tosu=tosu
        )
    except Exception as e:
        position_index = 50.0
    
    try:
        agari_index = calculate_agari_index(
            kohan_3f=kohan_3f,
            kyori=kyori,
            baba_code=baba_code,
            keibajo_code=keibajo_code
        )
    except Exception as e:
        agari_index = 0.0
    
    try:
        pace_index = calculate_pace_index(
            ten_index=ten_index,
            agari_index=agari_index,
            zenhan_3f=zenhan_3f,
            kohan_3f=kohan_3f
        )
    except Exception as e:
        pace_index = 0.0
    
    # 10刻みに丸める
    return {
        'ten': round(ten_index / 10) * 10,
        'position': round(position_index / 10) * 10,
        'agari': round(agari_index / 10) * 10,
        'pace': round(pace_index / 10) * 10
    }


# ================================================================================
# 実績データ集計
# ================================================================================

def update_stats(stats: Dict, index_type: str, index_value: float, 
                result: int, odds_win: float, odds_place: float):
    """
    実績データを更新
    """
    key = (index_type, int(index_value))
    
    if key not in stats:
        stats[key] = {
            'cnt_win': 0,
            'hit_win': 0,
            'total_win_odds': 0.0,
            'cnt_place': 0,
            'hit_place': 0,
            'total_place_odds': 0.0
        }
    
    # 単勝実績
    stats[key]['cnt_win'] += 1
    stats[key]['total_win_odds'] += odds_win
    if result == 1:  # 1着
        stats[key]['hit_win'] += 1
    
    # 複勝実績
    stats[key]['cnt_place'] += 1
    stats[key]['total_place_odds'] += odds_place
    if result <= 3:  # 3着以内
        stats[key]['hit_place'] += 1


def calculate_adjusted_return(hit_count: int, total_count: int, total_odds: float) -> float:
    """
    補正回収率を計算
    
    補正回収率 = (的中率 × 平均オッズ) / 期待的中率 × 100
    
    DECIMAL(6,2) の範囲内に制限: -9999.99 〜 9999.99
    """
    if total_count == 0:
        return 0.0
    
    hit_rate = hit_count / total_count
    avg_odds = total_odds / total_count
    
    # 期待的中率 = 1.0 / avg_odds
    expected_hit_rate = 1.0 / avg_odds if avg_odds > 0 else 0
    
    if expected_hit_rate > 0:
        adjusted_return = (hit_rate * avg_odds) / expected_hit_rate * 100
    else:
        adjusted_return = 0.0
    
    # DECIMAL(6,2) の範囲内に制限（-9999.99 〜 9999.99）
    adjusted_return = max(-9999.99, min(9999.99, adjusted_return))
    
    return round(adjusted_return, 2)


def save_stats_to_db(conn, keibajo_code: str, stats: Dict):
    """
    実績データをDBに保存
    """
    cursor = conn.cursor()
    
    insert_query = """
    INSERT INTO nar_hqs_index_stats 
    (keibajo_code, index_type, index_value, 
     cnt_win, hit_win, rate_win_hit, total_win_odds, adj_win_ret,
     cnt_place, hit_place, rate_place_hit, total_place_odds, adj_place_ret)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON CONFLICT (keibajo_code, index_type, index_value)
    DO UPDATE SET
        cnt_win = nar_hqs_index_stats.cnt_win + EXCLUDED.cnt_win,
        hit_win = nar_hqs_index_stats.hit_win + EXCLUDED.hit_win,
        total_win_odds = nar_hqs_index_stats.total_win_odds + EXCLUDED.total_win_odds,
        cnt_place = nar_hqs_index_stats.cnt_place + EXCLUDED.cnt_place,
        hit_place = nar_hqs_index_stats.hit_place + EXCLUDED.hit_place,
        total_place_odds = nar_hqs_index_stats.total_place_odds + EXCLUDED.total_place_odds,
        rate_win_hit = (nar_hqs_index_stats.hit_win + EXCLUDED.hit_win)::DECIMAL / 
                       (nar_hqs_index_stats.cnt_win + EXCLUDED.cnt_win) * 100,
        rate_place_hit = (nar_hqs_index_stats.hit_place + EXCLUDED.hit_place)::DECIMAL / 
                         (nar_hqs_index_stats.cnt_place + EXCLUDED.cnt_place) * 100,
        updated_at = NOW()
    """
    
    for (index_type, index_value), data in stats.items():
        rate_win_hit = (data['hit_win'] / data['cnt_win'] * 100) if data['cnt_win'] > 0 else 0
        rate_place_hit = (data['hit_place'] / data['cnt_place'] * 100) if data['cnt_place'] > 0 else 0
        
        adj_win_ret = calculate_adjusted_return(
            data['hit_win'], data['cnt_win'], data['total_win_odds']
        )
        adj_place_ret = calculate_adjusted_return(
            data['hit_place'], data['cnt_place'], data['total_place_odds']
        )
        
        # 平均オッズを計算（累積値を件数で割る）
        avg_win_odds = (data['total_win_odds'] / data['cnt_win']) if data['cnt_win'] > 0 else 0.0
        avg_place_odds = (data['total_place_odds'] / data['cnt_place']) if data['cnt_place'] > 0 else 0.0
        
        # DECIMAL(10,2) の範囲内に制限（最大 99,999,999.99）
        # 平均オッズなので通常は数百以下だが、念のため制限
        safe_total_win_odds = max(0.0, min(99999999.99, round(avg_win_odds, 2)))
        safe_total_place_odds = max(0.0, min(99999999.99, round(avg_place_odds, 2)))
        
        # すべての数値を安全な範囲に制限
        safe_rate_win_hit = max(-99999999.99, min(99999999.99, round(rate_win_hit, 2)))
        safe_rate_place_hit = max(-99999999.99, min(99999999.99, round(rate_place_hit, 2)))
        safe_adj_win_ret = max(-99999999.99, min(99999999.99, round(adj_win_ret, 2)))
        safe_adj_place_ret = max(-99999999.99, min(99999999.99, round(adj_place_ret, 2)))
        
        try:
            cursor.execute(insert_query, (
                keibajo_code, index_type, str(index_value),
                data['cnt_win'], data['hit_win'], safe_rate_win_hit, 
                safe_total_win_odds, safe_adj_win_ret,
                data['cnt_place'], data['hit_place'], safe_rate_place_hit,
                safe_total_place_odds, safe_adj_place_ret
            ))
        except Exception as e:
            print(f"\n{'='*80}")
            print(f"❌ データ挿入エラー")
            print(f"{'='*80}")
            print(f"競馬場: {keibajo_code}")
            print(f"指数タイプ: {index_type}")
            print(f"指数値: {index_value}")
            print(f"\n単勝データ:")
            print(f"  cnt_win={data['cnt_win']}, hit_win={data['hit_win']}, rate_win_hit={safe_rate_win_hit}")
            print(f"  total_win_odds(累積)={data['total_win_odds']}, avg_win_odds(平均)={avg_win_odds:.2f}")
            print(f"  safe_total_win_odds={safe_total_win_odds}, adj_win_ret={safe_adj_win_ret}")
            print(f"\n複勝データ:")
            print(f"  cnt_place={data['cnt_place']}, hit_place={data['hit_place']}, rate_place_hit={safe_rate_place_hit}")
            print(f"  total_place_odds(累積)={data['total_place_odds']}, avg_place_odds(平均)={avg_place_odds:.2f}")
            print(f"  safe_total_place_odds={safe_total_place_odds}, adj_place_ret={safe_adj_place_ret}")
            print(f"\n元データ:")
            print(f"  rate_win_hit(元)={rate_win_hit}")
            print(f"  rate_place_hit(元)={rate_place_hit}")
            print(f"  adj_win_ret(元)={adj_win_ret}")
            print(f"  adj_place_ret(元)={adj_place_ret}")
            print(f"\nエラー: {str(e)}")
            print(f"{'='*80}\n")
            logger.error(f"データ挿入エラー: {keibajo_code}, {index_type}, {index_value}")
            raise
    
    conn.commit()
    cursor.close()


# ================================================================================
# メイン処理
# ================================================================================

def main():
    """メイン処理"""
    print("\n" + "="*80)
    print("HQS指数実績データ収集スクリプト（競馬場別期間対応版）")
    print("="*80 + "\n")
    
    conn = get_db_connection()
    
    # 全競馬場のリスト
    all_tracks = list(SAND_CHANGE_TRACKS.keys()) + list(RENOVATION_TRACKS.keys()) + STANDARD_TRACKS
    
    # 除外対象を削除
    all_tracks = [t for t in all_tracks if t not in EXCLUDED_TRACKS]
    
    print(f"対象競馬場数: {len(all_tracks)}場\n")
    
    for keibajo_code in all_tracks:
        start_date, end_date, reason = get_period_for_track(keibajo_code)
        
        print(f"\n{'='*80}")
        print(f"📊 競馬場コード: {keibajo_code}")
        print(f"   期間: {start_date} 〜 {end_date}")
        print(f"   理由: {reason}")
        print(f"{'='*80}")
        
        # レースデータ取得
        races = collect_race_data(conn, keibajo_code, start_date, end_date)
        print(f"   取得レース数: {len(races):,}件")
        
        if len(races) == 0:
            print("   ⚠️ データなし。スキップします。")
            continue
        
        # 実績データ集計
        stats = defaultdict(dict)
        processed = 0
        
        for race in races:
            try:
                indexes = calculate_indexes_for_horse(race)
                result = safe_int(race.get('kakutei_chakujun'), 99)
                odds_win = safe_float(race.get('tansho_odds'), 0.0)
                odds_place = safe_float(race.get('fukusho_odds'), 0.0)
                
                for index_type, index_value in indexes.items():
                    update_stats(stats, index_type, index_value, result, odds_win, odds_place)
                
                processed += 1
                
                if processed % 1000 == 0:
                    print(f"   処理中... {processed:,}/{len(races):,} ({processed/len(races)*100:.1f}%)")
                    
            except Exception as e:
                # エラーは無視して続行
                pass
        
        # DBに保存
        save_stats_to_db(conn, keibajo_code, stats)
        print(f"   ✅ 完了: {processed:,}件処理")
    
    conn.close()
    
    print("\n" + "="*80)
    print("🎉 全競馬場のデータ収集完了！")
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
