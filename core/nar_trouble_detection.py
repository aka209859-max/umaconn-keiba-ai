"""
前走不利検知システム
統計的異常検知による不利の自動検出

理論: 競馬データ（JRA/NAR）における不利・アクシデント検知のための統計的異常値検出フレームワーク
実装: Modified Z-score (MAD法)、順位逆転検知（Rank Reversal Detection）
"""

import numpy as np
from scipy import stats
import logging
from typing import List, Dict, Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TroubleDetector:
    """
    前走不利検知クラス
    
    主要機能:
    1. Modified Z-score (MAD法) による出遅れ検知
    2. 順位逆転検知（挟まれ・外回し）
    3. 統合スコア算出
    4. データベース保存
    """
    
    def __init__(self, db_connection):
        """
        初期化
        
        Args:
            db_connection: psycopg2のDB接続オブジェクト
        """
        self.conn = db_connection
        
        # 検知パラメータ
        self.MAD_THRESHOLD = 3.5          # Modified Z-score閾値（出遅れ判定）
        self.RANK_STD_THRESHOLD = 2.5     # 順位標準偏差閾値
        self.RANK_DECLINE_THRESHOLD = 3.0 # 順位後退閾値（頭数）
        
        # 重み配分
        self.SLOW_START_WEIGHT = 0.4      # 出遅れスコアの重み
        self.RANK_REVERSAL_WEIGHT = 0.6   # 順位逆転スコアの重み
    
    def detect_slow_start(self, race_horses: List[Dict]) -> List[Dict]:
        """
        出遅れ検知（MAD法）
        
        理論:
        - テン3F相当タイム = 走破タイム - 上がり3F
        - レース内での相対的な遅れを検知
        - Modified Z-score > 3.5 で出遅れ判定
        
        Args:
            race_horses: レース内の全馬データ（list of dict）
                - ketto_toroku_bango: 血統登録番号
                - time: 走破タイム（秒）
                - kohan_3f: 上がり3F（秒）
        
        Returns:
            list of dict: 不利検知結果
                - ketto_toroku_bango
                - trouble_type: 'slow_start'
                - trouble_score: 0-100
                - confidence: 0.00-1.00
                - detection_method: 'MAD'
                - raw_z_score: Modified Z-score
                - ten_equivalent: テン3F相当タイム
        """
        ten_equivalent_data = []
        
        # テン3F相当タイムを計算
        for horse in race_horses:
            time = horse.get('time')
            kohan_3f = horse.get('kohan_3f')
            
            if time and kohan_3f and time > 0 and kohan_3f > 0:
                ten_time = time - kohan_3f
                ten_equivalent_data.append({
                    'ketto_toroku_bango': horse['ketto_toroku_bango'],
                    'ten_time': ten_time,
                    'time': time,
                    'kohan_3f': kohan_3f
                })
        
        # データ不足チェック
        if len(ten_equivalent_data) < 5:
            logger.warning(
                f"出遅れ検知: データ不足（{len(ten_equivalent_data)}頭のみ）"
            )
            return []
        
        # MAD計算（ロバスト統計）
        ten_times = [h['ten_time'] for h in ten_equivalent_data]
        median = np.median(ten_times)
        mad = np.median([abs(t - median) for t in ten_times])
        
        if mad == 0 or mad < 0.01:
            logger.warning("出遅れ検知: MAD=0またはほぼ0（全馬同じペース）")
            return []
        
        results = []
        
        for horse in ten_equivalent_data:
            # Modified Z-score計算
            modified_z = 0.6745 * (horse['ten_time'] - median) / mad
            
            # 出遅れ判定（Modified Z-score > 閾値）
            if modified_z > self.MAD_THRESHOLD:
                # スコア計算（0-100に正規化）
                trouble_score = min(100.0, modified_z * 20)
                
                results.append({
                    'ketto_toroku_bango': horse['ketto_toroku_bango'],
                    'trouble_type': 'slow_start',
                    'trouble_score': round(trouble_score, 2),
                    'confidence': 0.85,
                    'detection_method': 'MAD',
                    'raw_z_score': round(modified_z, 2),
                    'rank_std': None,
                    'ten_equivalent': round(horse['ten_time'], 2),
                    'rank_decline': None
                })
                
                logger.info(
                    f"出遅れ検知: {horse['ketto_toroku_bango']} "
                    f"(テン3F相当={horse['ten_time']:.2f}s, "
                    f"中央値={median:.2f}s, MAD={mad:.2f}s, "
                    f"Z={modified_z:.2f}, スコア={trouble_score:.1f})"
                )
        
        return results
    
    def detect_rank_reversal(self, race_horses: List[Dict]) -> List[Dict]:
        """
        順位逆転検知（挟まれ・外回し）
        
        理論:
        - corner_1 → corner_4 の順位変動を分析
        - 順位標準偏差 > 閾値 → 挟まれ/外回し
        - 前半→後半で3頭以上後退 → 不利判定
        
        Args:
            race_horses: レース内の全馬データ（list of dict）
                - ketto_toroku_bango: 血統登録番号
                - corner_1, corner_2, corner_3, corner_4: 通過順位
        
        Returns:
            list of dict: 不利検知結果
                - ketto_toroku_bango
                - trouble_type: 'rank_reversal'
                - trouble_score: 0-100
                - confidence: 0.00-1.00
                - detection_method: 'rank_reversal'
                - rank_std: 順位標準偏差
                - rank_decline: 前半→後半の順位後退数
        """
        results = []
        
        for horse in race_horses:
            corners = [
                horse.get('corner_1'),
                horse.get('corner_2'),
                horse.get('corner_3'),
                horse.get('corner_4')
            ]
            
            # NULL除外・正の値のみ
            corners = [c for c in corners if c is not None and c > 0]
            
            if len(corners) < 2:
                continue
            
            # 順位変動の標準偏差
            rank_std = np.std(corners)
            
            # 前半→後半で大きく後退したか確認
            if len(corners) >= 3:
                # 前半平均（最初の2コーナー）
                early_positions = corners[:2]
                early_avg = np.mean(early_positions)
                
                # 後半平均（最後の2コーナー）
                late_positions = corners[-2:]
                late_avg = np.mean(late_positions)
                
                # 順位後退数（正の値 = 後退）
                rank_decline = late_avg - early_avg
                
                # 🚫 除外パターン: 「逃げ失速」の検知
                # 前半1-3番手 → 後半大幅後退 = 逃げてバテただけ（不利ではない）
                is_front_runner_fade = (
                    early_avg <= 3.0 and  # 前半3番手以内
                    rank_decline > 4.0     # 4頭以上後退
                )
                
                if is_front_runner_fade:
                    logger.info(
                        f"逃げ失速パターン除外: {horse['ketto_toroku_bango']} "
                        f"(前半平均={early_avg:.1f}, 後退={rank_decline:.1f}頭) "
                        f"→ 不利ではない"
                    )
                    continue
                
                # 判定基準:
                # 1. 3頭以上後退 AND 順位変動が大きい
                if rank_decline > self.RANK_DECLINE_THRESHOLD and rank_std > self.RANK_STD_THRESHOLD:
                    # スコア計算
                    trouble_score = min(100.0, rank_decline * 15 + rank_std * 10)
                    
                    results.append({
                        'ketto_toroku_bango': horse['ketto_toroku_bango'],
                        'trouble_type': 'rank_reversal',
                        'trouble_score': round(trouble_score, 2),
                        'confidence': 0.80,
                        'detection_method': 'rank_reversal',
                        'raw_z_score': None,
                        'rank_std': round(rank_std, 2),
                        'ten_equivalent': None,
                        'rank_decline': round(rank_decline, 2)
                    })
                    
                    logger.info(
                        f"順位逆転検知: {horse['ketto_toroku_bango']} "
                        f"(順位: {corners}, "
                        f"前半平均={early_avg:.1f}, 後半平均={late_avg:.1f}, "
                        f"後退={rank_decline:.1f}頭, 変動σ={rank_std:.1f}, "
                        f"スコア={trouble_score:.1f})"
                    )
                
                # オプション: Kendall's Tau による相関検証
                if len(corners) >= 4:
                    expected_order = list(range(1, len(corners) + 1))
                    try:
                        tau, p_value = stats.kendalltau(expected_order, corners)
                        
                        # 負の相関 = 順位逆転（前半良くて後半悪い）
                        if tau < -0.3 and p_value < 0.05:
                            logger.debug(
                                f"Kendall's Tau異常: {horse['ketto_toroku_bango']} "
                                f"(τ={tau:.3f}, p={p_value:.3f})"
                            )
                    except Exception as e:
                        logger.debug(f"Kendall's Tau計算エラー: {e}")
        
        return results
    
    def calculate_integrated_trouble_score(
        self,
        slow_start_results: List[Dict],
        rank_reversal_results: List[Dict]
    ) -> Dict[str, Dict]:
        """
        複数の不利検知結果を統合
        
        Args:
            slow_start_results: 出遅れ検知結果
            rank_reversal_results: 順位逆転検知結果
        
        Returns:
            dict: 統合された不利スコア（馬ごと）
                {ketto_toroku_bango: {trouble_score, trouble_type, ...}}
        """
        integrated = {}
        
        # 出遅れスコア（重み 0.4）
        for result in slow_start_results:
            ketto = result['ketto_toroku_bango']
            integrated[ketto] = {
                'trouble_score': result['trouble_score'] * self.SLOW_START_WEIGHT,
                'trouble_type': 'slow_start',
                'confidence': result['confidence'],
                'detection_method': result['detection_method'],
                'raw_z_score': result['raw_z_score'],
                'rank_std': None,
                'ten_equivalent': result['ten_equivalent'],
                'rank_decline': None
            }
        
        # 順位逆転スコア（重み 0.6）
        for result in rank_reversal_results:
            ketto = result['ketto_toroku_bango']
            
            if ketto in integrated:
                # 両方の不利がある場合（出遅れ + 順位逆転）
                integrated[ketto]['trouble_score'] += result['trouble_score'] * self.RANK_REVERSAL_WEIGHT
                integrated[ketto]['trouble_type'] = 'mixed'
                integrated[ketto]['confidence'] = (
                    integrated[ketto]['confidence'] + result['confidence']
                ) / 2
                integrated[ketto]['detection_method'] = 'ensemble'
                integrated[ketto]['rank_std'] = result['rank_std']
                integrated[ketto]['rank_decline'] = result['rank_decline']
            else:
                # 順位逆転のみ
                integrated[ketto] = {
                    'trouble_score': result['trouble_score'] * self.RANK_REVERSAL_WEIGHT,
                    'trouble_type': 'rank_reversal',
                    'confidence': result['confidence'],
                    'detection_method': result['detection_method'],
                    'raw_z_score': None,
                    'rank_std': result['rank_std'],
                    'ten_equivalent': None,
                    'rank_decline': result['rank_decline']
                }
        
        # スコアを0-100に正規化
        for ketto, data in integrated.items():
            data['trouble_score'] = min(100.0, round(data['trouble_score'], 2))
        
        return integrated
    
    def save_trouble_data(self, race_info: Dict, trouble_results: Dict[str, Dict]):
        """
        不利検知結果をDBに保存
        
        Args:
            race_info: レース情報
                - race_date: レース日付（YYYYMMDD）
                - keibajo_code: 競馬場コード
                - race_bango: レース番号
            trouble_results: 統合された不利スコア（馬ごと）
        """
        if not trouble_results:
            logger.debug(f"不利データなし: {race_info['race_date']} "
                        f"{race_info['keibajo_code']}{race_info['race_bango']}R")
            return
        
        query = """
            INSERT INTO nar_trouble_estimated (
                ketto_toroku_bango,
                race_date,
                keibajo_code,
                race_bango,
                trouble_score,
                trouble_type,
                confidence,
                detection_method,
                raw_z_score,
                rank_std,
                ten_equivalent,
                rank_decline
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ketto_toroku_bango, race_date, keibajo_code, race_bango)
            DO UPDATE SET
                trouble_score = EXCLUDED.trouble_score,
                trouble_type = EXCLUDED.trouble_type,
                confidence = EXCLUDED.confidence,
                detection_method = EXCLUDED.detection_method,
                raw_z_score = EXCLUDED.raw_z_score,
                rank_std = EXCLUDED.rank_std,
                ten_equivalent = EXCLUDED.ten_equivalent,
                rank_decline = EXCLUDED.rank_decline,
                updated_at = CURRENT_TIMESTAMP
        """
        
        cursor = self.conn.cursor()
        
        try:
            for ketto, result in trouble_results.items():
                cursor.execute(query, [
                    ketto,
                    race_info['race_date'],
                    race_info['keibajo_code'],
                    race_info['race_bango'],
                    result['trouble_score'],
                    result['trouble_type'],
                    result['confidence'],
                    result['detection_method'],
                    result['raw_z_score'],
                    result['rank_std'],
                    result['ten_equivalent'],
                    result['rank_decline']
                ])
            
            self.conn.commit()
            
            logger.info(
                f"✅ 不利データ保存完了: {race_info['race_date']} "
                f"{race_info['keibajo_code']}-{race_info['race_bango']}R "
                f"({len(trouble_results)}頭)"
            )
            
        except Exception as e:
            self.conn.rollback()
            logger.error(f"❌ 不利データ保存エラー: {e}")
            raise
        finally:
            cursor.close()
    
    def detect_race_troubles(self, race_horses: List[Dict]) -> Dict[str, Dict]:
        """
        1レース分の不利検知を実行
        
        Args:
            race_horses: レース内の全馬データ
        
        Returns:
            dict: 統合された不利スコア
        """
        # 出遅れ検知
        slow_start_results = self.detect_slow_start(race_horses)
        
        # 順位逆転検知
        rank_reversal_results = self.detect_rank_reversal(race_horses)
        
        # 統合スコア算出
        trouble_results = self.calculate_integrated_trouble_score(
            slow_start_results,
            rank_reversal_results
        )
        
        return trouble_results


# ============================================================
# ユーティリティ関数
# ============================================================

def safe_float(value, default=None):
    """安全にfloat変換"""
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def safe_int(value, default=None):
    """安全にint変換"""
    try:
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default
