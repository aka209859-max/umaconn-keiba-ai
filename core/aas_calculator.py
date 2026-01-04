"""
AAS得点計算モジュール

AAS (Adaptive Ability Score) 計算:
1. 各ファクターの補正回収率データ取得
2. Hit_raw, Ret_raw 計算
3. レース内でZスコア化
4. AAS得点算出（-12 ~ +12）
5. 競馬場別重みを適用
"""

import numpy as np
import sys
sys.path.append('/home/user/webapp/nar-ai-yoso')

from config.factor_weights import get_factor_weight
from config.course_master import (
    get_course_type, 
    get_straight_length, 
    get_corner_count
)


def safe_float(value, default=0.0):
    """
    文字列を安全にfloatに変換
    """
    if value is None or value == '':
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def safe_int(value, default=0):
    """
    文字列を安全にintに変換
    """
    if value is None or value == '':
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def get_factor_stats(conn, keibajo_code, factor_name, factor_value, kyori=None):
    """
    ファクターの統計データ（補正回収率）を取得
    
    CEOの補正回収率計算ロジックを統合済み
    
    Args:
        conn: データベース接続
        keibajo_code: 競馬場コード
        factor_name: ファクター名
        factor_value: ファクター値
        kyori: 距離（オプション）
    
    Returns:
        dict: {
            'cntWin': 単勝試行回数,
            'cntPlace': 複勝試行回数,
            'rateWinHit': 単勝的中率（0-100の%値）,
            'ratePlaceHit': 複勝的中率（0-100の%値）,
            'rateWinRet': 補正単勝回収率（0-100の%値）,
            'ratePlaceRet': 補正複勝回収率（0-100の%値）
        }
    """
    from core.factor_stats_calculator import get_factor_stats_summary
    
    # 距離がない場合はデフォルト値
    if kyori is None:
        kyori = 1600
    
    try:
        # 補正回収率を計算
        stats = get_factor_stats_summary(
            conn, keibajo_code, kyori, factor_name, str(factor_value)
        )
        
        # AAS計算用の形式で返す（%値）
        return {
            'cntWin': stats['cnt_win'],
            'cntPlace': stats['cnt_place'],
            'rateWinHit': stats['rate_win_hit'],      # %値
            'ratePlaceHit': stats['rate_place_hit'],  # %値
            'rateWinRet': stats['rate_win_ret'],      # %値（補正済み）
            'ratePlaceRet': stats['rate_place_ret']   # %値（補正済み）
        }
    except Exception as e:
        print(f"Warning: ファクター統計取得エラー: {factor_name}={factor_value}, Error: {e}")
        # エラー時はデフォルト値を返す
        return {
            'cntWin': 10,
            'cntPlace': 10,
            'rateWinHit': 10.0,
            'ratePlaceHit': 30.0,
            'rateWinRet': 75.0,
            'ratePlaceRet': 80.0
        }


def calculate_hit_ret_raw(factor_stats):
    """
    Hit_raw, Ret_raw を計算
    
    CEOの計算式:
    Hit_raw = 0.65 × 単勝的中率 + 0.35 × 複勝的中率
    Ret_raw = 0.35 × 補正単勝回収率 + 0.65 × 補正複勝回収率
    
    Args:
        factor_stats: ファクターの統計データ（%値: 15% = 15）
    
    Returns:
        tuple: (Hit_raw, Ret_raw, N_min)
    """
    N_min = min(factor_stats['cntWin'], factor_stats['cntPlace'])
    
    # 的中率（%値そのまま使用: 15% = 15）
    Hit_raw = (0.65 * factor_stats['rateWinHit'] + 
               0.35 * factor_stats['ratePlaceHit'])
    
    # 回収率（%値そのまま使用: 85% = 85）
    Ret_raw = (0.35 * factor_stats['rateWinRet'] + 
               0.65 * factor_stats['ratePlaceRet'])
    
    return Hit_raw, Ret_raw, N_min


def calculate_shrinkage(N_min):
    """
    Shrinkage係数を計算
    
    Args:
        N_min: 最小試行回数
    
    Returns:
        float: Shrinkage係数
    """
    return np.sqrt(N_min / (N_min + 400))


def calculate_aas_score_from_z(ZH, ZR, Shr):
    """
    ZスコアからAAS得点を計算
    
    Args:
        ZH: Hit_rawのZスコア
        ZR: Ret_rawのZスコア
        Shr: Shrinkage係数
    
    Returns:
        float: AAS得点（-12 ~ +12）
    """
    baseCalc = 0.55 * ZH + 0.45 * ZR
    aas_score = 12 * np.tanh(baseCalc) * Shr
    return aas_score


def extract_single_factor_value(horse, factor_name):
    """
    単独ファクターの値を抽出
    
    Args:
        horse: 馬データ
        factor_name: ファクター名
    
    Returns:
        値（文字列 or 数値）
    """
    # 単独ファクターのマッピング
    factor_mapping = {
        'prev_chakujun': 'prev_chakujun',
        'prev_corner_1': 'prev_corner_1',
        'prev_corner_2': 'prev_corner_2',
        'prev_corner_3': 'prev_corner_3',
        'prev_corner_4': 'prev_corner_4',
        'prev_time_sa': 'prev_time_sa',
        'prev_kohan_3f': 'prev_kohan_3f',
        'umaban': 'umaban',
        'wakuban': 'wakuban',
        'seibetsu_code': 'seibetsu_code',
        'bataiju': 'bataiju',
        'zogen_sa': 'zogen_sa',
        'barei': 'barei',
        'chokyoshi_mei': 'chokyoshi_mei',
        'kishu_mei': 'kishu_mei',
    }
    
    column_name = factor_mapping.get(factor_name)
    if column_name:
        return horse.get(column_name)
    
    return None


def extract_composite_factor_value(horse, race_info, factor_name):
    """
    複合ファクターの値を抽出
    
    Args:
        horse: 馬データ
        race_info: レース情報
        factor_name: ファクター名
    
    Returns:
        tuple or str: 組み合わせ値
    """
    if factor_name == 'kishu_wakuban':
        return (horse.get('kishu_mei'), horse.get('wakuban'))
    
    elif factor_name == 'prev_kyori_current_kyori':
        # TODO: 前走距離を取得
        return ('1600', race_info.get('kyori'))
    
    elif factor_name == 'baba_jotai_wakuban':
        return (race_info.get('baba_jotai_code'), horse.get('wakuban'))
    
    elif factor_name == 'prev_chakujun_corner4':
        return (horse.get('prev_chakujun'), horse.get('prev_corner_4'))
    
    elif factor_name == 'prev_chakujun_kohan3f':
        return (horse.get('prev_chakujun'), horse.get('prev_kohan_3f'))
    
    elif factor_name == 'kishu_prev_chakujun':
        return (horse.get('kishu_mei'), horse.get('prev_chakujun'))
    
    elif factor_name == 'seibetsu_kyori':
        return (horse.get('seibetsu_code'), race_info.get('kyori'))
    
    elif factor_name == 'barei_prev_chakujun':
        return (horse.get('barei'), horse.get('prev_chakujun'))
    
    elif factor_name == 'wakuban_prev_wakuban':
        return (horse.get('wakuban'), horse.get('prev_wakuban'))
    
    elif factor_name == 'kishu_chokyoshi':
        return (horse.get('kishu_mei'), horse.get('chokyoshi_mei'))
    
    elif factor_name == 'course_type':
        kyori = safe_int(race_info.get('kyori'))
        return get_course_type(race_info.get('keibajo_code'), kyori)
    
    elif factor_name == 'mawari_code':
        return race_info.get('mawari_code')
    
    elif factor_name == 'straight_kohan3f':
        straight = get_straight_length(race_info.get('keibajo_code'))
        kohan3f = horse.get('prev_kohan_3f')
        return (straight, kohan3f)
    
    elif factor_name == 'corner_count_corner':
        kyori = safe_int(race_info.get('kyori'))
        corner_count = get_corner_count(kyori)
        # 平均コーナー順位
        corners = [
            safe_float(horse.get('prev_corner_1')),
            safe_float(horse.get('prev_corner_2')),
            safe_float(horse.get('prev_corner_3')),
            safe_float(horse.get('prev_corner_4'))
        ]
        valid_corners = [c for c in corners if c > 0]
        avg_corner = np.mean(valid_corners) if valid_corners else 0
        return (corner_count, avg_corner)
    
    return None


def is_valid_factor_value(value):
    """
    ファクター値が有効かチェック
    """
    if value is None:
        return False
    if isinstance(value, str) and value == '':
        return False
    if isinstance(value, tuple):
        return all(v is not None and v != '' for v in value)
    return True


def calculate_race_aas_scores(conn, horses_data, race_info):
    """
    レース内の全馬のAAS得点を計算
    
    Args:
        conn: データベース接続
        horses_data: 出走馬データのリスト
        race_info: レース情報
    
    Returns:
        list: AAS得点が追加された馬データのリスト
    """
    keibajo_code = race_info.get('keibajo_code')
    kyori = safe_int(race_info.get('kyori'))
    
    # 全ファクター名リスト
    single_factors = [
        'prev_chakujun', 'prev_corner_1', 'prev_corner_2', 'prev_corner_3',
        'prev_corner_4', 'prev_time_sa', 'prev_kohan_3f', 'umaban', 'wakuban',
        'seibetsu_code', 'bataiju', 'zogen_sa', 'barei', 'chokyoshi_mei', 'kishu_mei'
    ]
    
    composite_factors = [
        'kishu_wakuban', 'prev_kyori_current_kyori', 'baba_jotai_wakuban',
        'joken_code_prev_joken', 'prev_chakujun_corner4', 'prev_chakujun_kohan3f',
        'kishu_prev_chakujun', 'seibetsu_kyori', 'barei_prev_chakujun',
        'wakuban_prev_wakuban', 'kishu_chokyoshi', 'course_type', 'mawari_code',
        'straight_kohan3f', 'corner_count_corner'
    ]
    
    all_factors = single_factors + composite_factors
    
    # 各馬の各ファクターのHit_raw, Ret_rawを収集
    horses_hit_ret = []
    
    for horse in horses_data:
        horse_data = {'horse': horse, 'factors': {}}
        
        for factor_name in all_factors:
            # ファクター値を取得
            if factor_name in single_factors:
                factor_value = extract_single_factor_value(horse, factor_name)
            else:
                factor_value = extract_composite_factor_value(horse, race_info, factor_name)
            
            # 有効な値でない場合はスキップ
            if not is_valid_factor_value(factor_value):
                continue
            
            # 補正回収率データ取得
            factor_stats = get_factor_stats(conn, keibajo_code, factor_name, factor_value, kyori)
            
            # Hit_raw, Ret_raw 計算
            Hit_raw, Ret_raw, N_min = calculate_hit_ret_raw(factor_stats)
            
            horse_data['factors'][factor_name] = {
                'value': factor_value,
                'Hit_raw': Hit_raw,
                'Ret_raw': Ret_raw,
                'N_min': N_min
            }
        
        horses_hit_ret.append(horse_data)
    
    # ファクターごとにZスコア化
    for factor_name in all_factors:
        # このファクターの全馬のHit_raw, Ret_rawを収集
        hit_raws = []
        ret_raws = []
        
        for horse_data in horses_hit_ret:
            if factor_name in horse_data['factors']:
                hit_raws.append(horse_data['factors'][factor_name]['Hit_raw'])
                ret_raws.append(horse_data['factors'][factor_name]['Ret_raw'])
        
        # グループ統計
        if len(hit_raws) > 1:
            μH = np.mean(hit_raws)
            σH = np.std(hit_raws)
            μR = np.mean(ret_raws)
            σR = np.std(ret_raws)
            
            # Zスコア計算
            for horse_data in horses_hit_ret:
                if factor_name in horse_data['factors']:
                    Hit_raw = horse_data['factors'][factor_name]['Hit_raw']
                    Ret_raw = horse_data['factors'][factor_name]['Ret_raw']
                    N_min = horse_data['factors'][factor_name]['N_min']
                    
                    ZH = (Hit_raw - μH) / σH if σH > 0 else 0
                    ZR = (Ret_raw - μR) / σR if σR > 0 else 0
                    
                    # Shrinkage係数
                    Shr = calculate_shrinkage(N_min)
                    
                    # AAS得点
                    aas_score = calculate_aas_score_from_z(ZH, ZR, Shr)
                    
                    # 競馬場別重みを適用
                    weight = get_factor_weight(keibajo_code, factor_name)
                    weighted_aas = aas_score * weight
                    
                    horse_data['factors'][factor_name]['ZH'] = ZH
                    horse_data['factors'][factor_name]['ZR'] = ZR
                    horse_data['factors'][factor_name]['Shr'] = Shr
                    horse_data['factors'][factor_name]['aas_score'] = aas_score
                    horse_data['factors'][factor_name]['weight'] = weight
                    horse_data['factors'][factor_name]['weighted_aas'] = weighted_aas
    
    # 総合AAS得点を計算
    results = []
    for horse_data in horses_hit_ret:
        total_aas = sum(
            factor_data['weighted_aas']
            for factor_data in horse_data['factors'].values()
            if 'weighted_aas' in factor_data
        )
        
        result = {
            **horse_data['horse'],
            'total_aas': total_aas,
            'factor_details': horse_data['factors']
        }
        results.append(result)
    
    # 総合得点でソート
    results.sort(key=lambda x: x['total_aas'], reverse=True)
    
    return results


# テスト用
if __name__ == '__main__':
    # Hit_raw, Ret_raw 計算テスト
    factor_stats = {
        'cntWin': 100,
        'cntPlace': 100,
        'rateWinHit': 0.15,
        'ratePlaceHit': 0.45,
        'rateWinRet': 0.85,
        'ratePlaceRet': 0.90
    }
    
    Hit_raw, Ret_raw, N_min = calculate_hit_ret_raw(factor_stats)
    print(f"Hit_raw: {Hit_raw:.3f}")
    print(f"Ret_raw: {Ret_raw:.3f}")
    print(f"N_min: {N_min}")
    
    # Shrinkage計算テスト
    Shr = calculate_shrinkage(N_min)
    print(f"Shrinkage: {Shr:.3f}")
    
    # AAS得点計算テスト
    ZH = 1.5
    ZR = 1.0
    aas_score = calculate_aas_score_from_z(ZH, ZR, Shr)
    print(f"AAS Score: {aas_score:.2f}")
