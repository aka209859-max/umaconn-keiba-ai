"""
ファクター抽出モジュール
31ファクター（単独16 + 組み合わせ15）を抽出
"""
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from datetime import datetime, timedelta


def safe_int(value, default=0):
    """
    安全にintに変換
    """
    try:
        if value is None or value == '':
            return default
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """
    安全にfloatに変換
    """
    try:
        if value is None or value == '':
            return default
        return float(value)
    except (ValueError, TypeError):
        return default


def calculate_kyakushitsu(corner_positions):
    """
    脚質を計算（コーナー通過順位から判定）
    
    Args:
        corner_positions: list of int - コーナー通過順位 [corner_1, corner_2, corner_3]
    
    Returns:
        str: '逃げ', '先行', '差し', '追込'
    """
    if not corner_positions or len(corner_positions) == 0:
        return '不明'
    
    # 有効な通過順位のみを抽出
    valid_positions = [p for p in corner_positions if p > 0]
    if not valid_positions:
        return '不明'
    
    # 平均通過順位を計算
    avg_position = sum(valid_positions) / len(valid_positions)
    
    # 脚質判定
    if avg_position <= 2.0:
        return '逃げ'
    elif avg_position <= 4.0:
        return '先行'
    elif avg_position <= 8.0:
        return '差し'
    else:
        return '追込'


def calculate_kyuyo_weeks(prev_race_date, current_race_date):
    """
    休養週数を計算
    
    Args:
        prev_race_date: str - 前走日付 (YYYYMMDD)
        current_race_date: str - 今回レース日付 (YYYYMMDD)
    
    Returns:
        int: 休養週数
    """
    try:
        if not prev_race_date or not current_race_date:
            return 0
        
        prev_date = datetime.strptime(prev_race_date, '%Y%m%d')
        curr_date = datetime.strptime(current_race_date, '%Y%m%d')
        
        days_diff = (curr_date - prev_date).days
        weeks = days_diff // 7
        
        return max(0, weeks)
    except Exception:
        return 0


def calculate_pace_change_rate(zenhan_3f, kohan_3f):
    """
    ペース変化率を計算
    
    Args:
        zenhan_3f: float - 前半3Fタイム（秒）
        kohan_3f: float - 後半3Fタイム（秒）
    
    Returns:
        float: ペース変化率（正値は失速、負値は加速）
    """
    try:
        if not zenhan_3f or not kohan_3f or zenhan_3f == 0:
            return None
        return (kohan_3f - zenhan_3f) / zenhan_3f
    except Exception:
        return None


def get_previous_race_data(conn, ketto_toroku_bango, current_race_date):
    """
    前走データを取得
    
    Args:
        conn: データベース接続
        ketto_toroku_bango: str - 血統登録番号
        current_race_date: str - 今回レース日付 (YYYYMMDD形式: '20250105')
    
    Returns:
        dict: 前走データ
            - prev_chakujun: 前走着順
            - prev_ninki: 前走人気
            - prev_kyori: 前走距離
            - prev_baba: 前走馬場
            - prev_race_date: 前走日付
    """
    try:
        cur = conn.cursor()
        
        # 前走データを取得（今回より前の最新レース）
        # Phase 1: F22（前走タイム差）、F23（前走上がり3F）を追加
        query = """
            SELECT 
                se.kakutei_chakujun as chakujun,
                se.ninkijun as ninki,
                ra.kyori,
                ra.babajotai_code_dirt as baba,
                se.kaisai_nen || se.kaisai_tsukihi as race_date,
                se.time_sa as time_sa,
                se.kohan_3f as kohan_3f
            FROM nvd_se se
            JOIN nvd_ra ra ON (
                se.kaisai_nen = ra.kaisai_nen 
                AND se.kaisai_tsukihi = ra.kaisai_tsukihi
                AND se.keibajo_code = ra.keibajo_code
                AND se.race_bango = ra.race_bango
            )
            WHERE se.ketto_toroku_bango = %s
            AND se.kaisai_nen || se.kaisai_tsukihi < %s
            ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
            LIMIT 1
        """
        
        cur.execute(query, (ketto_toroku_bango, current_race_date))
        row = cur.fetchone()
        
        if row:
            return {
                'prev_chakujun': safe_int(row[0]),
                'prev_ninki': safe_int(row[1]),
                'prev_kyori': safe_int(row[2]),
                'prev_baba': row[3] if row[3] else '不明',
                'prev_race_date': row[4] if row[4] else '',
                'prev_time_sa': safe_float(row[5], 0.0),  # F22
                'prev_kohan_3f': safe_float(row[6], 0.0)  # F23
            }
        else:
            # 前走データがない場合
            return {
                'prev_chakujun': 0,
                'prev_ninki': 0,
                'prev_kyori': 0,
                'prev_baba': '不明',
                'prev_race_date': '',
                'prev_time_sa': 0.0,
                'prev_kohan_3f': 0.0
            }
        
    except Exception as e:
        print(f"❌ 前走データ取得エラー: {e}")
        return {
            'prev_chakujun': 0,
            'prev_ninki': 0,
            'prev_kyori': 0,
            'prev_baba': '不明',
            'prev_race_date': '',
            'prev_time_sa': 0.0,
            'prev_kohan_3f': 0.0
        }
    finally:
        cur.close()


def extract_single_factors(conn, horse_data, race_data):
    """
    単独ファクター（16個）を抽出
    
    Args:
        conn: データベース接続
        horse_data: dict - nvd_se の1行分のデータ
        race_data: dict - nvd_ra の1行分のデータ
    
    Returns:
        dict: 単独ファクター
    """
    # 今回レース日付
    current_race_date = horse_data.get('kaisai_nen', '') + horse_data.get('kaisai_tsukihi', '')
    
    # 前走データを取得
    prev_data = get_previous_race_data(
        conn, 
        horse_data.get('ketto_toroku_bango', ''),
        current_race_date
    )
    
    # コーナー通過順位から脚質を計算
    corner_1 = safe_int(horse_data.get('corner_1', 0))
    corner_2 = safe_int(horse_data.get('corner_2', 0))
    corner_3 = safe_int(horse_data.get('corner_3', 0))
    kyakushitsu = calculate_kyakushitsu([corner_1, corner_2, corner_3])
    
    # 休養週数を計算
    kyuyo_weeks = calculate_kyuyo_weeks(prev_data['prev_race_date'], current_race_date)
    
    factors = {
        'F01_kishu': horse_data.get('kishu_code', ''),
        'F01_kishu_name': horse_data.get('kishumei_ryakusho', ''),
        
        'F02_chokyoshi': horse_data.get('chokyoshi_code', ''),
        'F02_chokyoshi_name': horse_data.get('chokyoshimei_ryakusho', ''),
        
        'F03_kyori': safe_int(race_data.get('kyori', 0)),
        
        'F04_baba': race_data.get('babajotai_code_dirt', '不明'),  # ★ CEO確認後に修正
        
        'F05_mawari': race_data.get('mawari_code', '不明'),
        
        'F06_joken': race_data.get('kyoso_joken_code', ''),
        'F06_joken_name': race_data.get('kyoso_joken_meisho', ''),
        
        'F07_kyakushitsu': kyakushitsu,
        
        'F08_wakuban': safe_int(horse_data.get('wakuban', 0)),
        
        'F09_prev_chakujun': prev_data['prev_chakujun'],
        
        'F10_prev_ninki': prev_data['prev_ninki'],
        
        'F11_prev_kyori': prev_data['prev_kyori'],
        
        'F12_prev_baba': prev_data['prev_baba'],
        
        'F13_kyuyo_weeks': kyuyo_weeks,
        
        'F14_bataiju': safe_int(horse_data.get('bataiju', 0)),
        
        'F15_zogen_sa': safe_int(horse_data.get('zogen_sa', 0)),
        
        'F16_seibetsu': horse_data.get('seibetsu_code', ''),
        
        # Phase 1 高優先度ファクター（2026-01-06 追加）
        'F17_barei': safe_int(horse_data.get('barei', 0)),
        
        'F22_prev_time_sa': prev_data.get('prev_time_sa', 0.0),
        
        'F23_prev_kohan_3f': prev_data.get('prev_kohan_3f', 0.0),
        
        'F28_tosu': safe_int(race_data.get('tosu', 0)),
        
        # Phase 2 ファクター（2026-01-07 追加）
        'F24_prev_wakuban': prev_data.get('prev_wakuban', None),
        
        'F25_tansho_odds': safe_float(horse_data.get('tansho_odds', 0.0)),
        
        'F26_tansho_ninki': safe_int(horse_data.get('tansho_ninkijun', 0)),
        
        'F27_track_code': race_data.get('track_code', ''),
        
        'F29_grade_code': race_data.get('grade_code', ''),
        
        # Phase 3 血統ファクター（2026-01-07 追加）
        'B15_f_blood_no': horse_data.get('f_blood_no', None),
        'B16_m_blood_no': horse_data.get('m_blood_no', None),
        'B17_ff_blood_no': horse_data.get('ff_blood_no', None),
        'B18_fm_blood_no': horse_data.get('fm_blood_no', None),
        'B19_mf_blood_no': horse_data.get('mf_blood_no', None),
        'B20_mm_blood_no': horse_data.get('mm_blood_no', None),
        
        # Phase 2 新規ファクター（2026-01-08 追加）
        'F34_estimated_ten_3f': horse_data.get('estimated_ten_3f', None),  # Ten3FEstimatorで推定
        'F35_pace_change_rate': horse_data.get('pace_change_rate', None)  # ペース変化率
    }
    
    return factors


def extract_combined_factors(single_factors):
    """
    組み合わせファクター（15個）を抽出
    
    Args:
        single_factors: dict - 単独ファクター
    
    Returns:
        dict: 組み合わせファクター
    """
    combined = {
        # C01: 騎手×距離
        'C01_kishu_kyori': f"{single_factors['F01_kishu']}_{single_factors['F03_kyori']}",
        
        # C02: 騎手×馬場状態
        'C02_kishu_baba': f"{single_factors['F01_kishu']}_{single_factors['F04_baba']}",
        
        # C03: 騎手×回り
        'C03_kishu_mawari': f"{single_factors['F01_kishu']}_{single_factors['F05_mawari']}",
        
        # C04: 騎手×条件
        'C04_kishu_joken': f"{single_factors['F01_kishu']}_{single_factors['F06_joken']}",
        
        # C05: 調教師×距離
        'C05_chokyoshi_kyori': f"{single_factors['F02_chokyoshi']}_{single_factors['F03_kyori']}",
        
        # C06: 調教師×馬場状態
        'C06_chokyoshi_baba': f"{single_factors['F02_chokyoshi']}_{single_factors['F04_baba']}",
        
        # C07: 距離×馬場状態
        'C07_kyori_baba': f"{single_factors['F03_kyori']}_{single_factors['F04_baba']}",
        
        # C08: 距離×回り
        'C08_kyori_mawari': f"{single_factors['F03_kyori']}_{single_factors['F05_mawari']}",
        
        # C09: 脚質×距離
        'C09_kyakushitsu_kyori': f"{single_factors['F07_kyakushitsu']}_{single_factors['F03_kyori']}",
        
        # C10: 脚質×馬場状態
        'C10_kyakushitsu_baba': f"{single_factors['F07_kyakushitsu']}_{single_factors['F04_baba']}",
        
        # C11: 枠番×距離
        'C11_wakuban_kyori': f"{single_factors['F08_wakuban']}_{single_factors['F03_kyori']}",
        
        # C12: 前走着順×休養週数
        'C12_prev_chakujun_kyuyo': f"{single_factors['F09_prev_chakujun']}_{single_factors['F13_kyuyo_weeks']}",
        
        # C13: 前走人気×前走着順
        'C13_prev_ninki_chakujun': f"{single_factors['F10_prev_ninki']}_{single_factors['F09_prev_chakujun']}",
        
        # C14: 馬体重増減×休養週数
        'C14_zogen_kyuyo': f"{single_factors['F15_zogen_sa']}_{single_factors['F13_kyuyo_weeks']}",
        
        # C15: 性別×距離
        'C15_seibetsu_kyori': f"{single_factors['F16_seibetsu']}_{single_factors['F03_kyori']}"
    }
    
    return combined


def extract_all_factors(conn, horse_data, race_data):
    """
    31ファクター全てを抽出
    
    Args:
        conn: データベース接続
        horse_data: dict - nvd_se の1行分のデータ
        race_data: dict - nvd_ra の1行分のデータ
    
    Returns:
        dict: 全31ファクター
    """
    # 単独ファクター（16個）
    single_factors = extract_single_factors(conn, horse_data, race_data)
    
    # 組み合わせファクター（15個）
    combined_factors = extract_combined_factors(single_factors)
    
    # 統合
    all_factors = {**single_factors, **combined_factors}
    
    return all_factors
