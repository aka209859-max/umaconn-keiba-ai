"""
前走不利検知システム - バッチ処理
過去3年分の地方競馬レースデータを分析し、不利を検知してDBに保存

使用方法:
    python batch_process_trouble_detection.py --start-date 20230101 --end-date 20260107

実装範囲:
    - 地方競馬14場（ばんえい競馬61除外）
    - 過去3年分のレースデータ
    - MAD法による出遅れ検知
    - 順位逆転検知（挟まれ・外回し）
    - nar_trouble_estimated テーブルへ保存
"""

import argparse
import logging
from datetime import datetime, timedelta
from typing import List, Dict
import sys

import psycopg2
from psycopg2.extras import RealDictCursor

from config.db_config import get_db_connection
from config.course_master import KEIBAJO_NAMES
from core.nar_trouble_detection import TroubleDetector, safe_float, safe_int

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('batch_trouble_detection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class BatchTroubleProcessor:
    """
    バッチ処理クラス
    
    機能:
    1. 期間指定でレースデータを取得
    2. レースごとに不利検知を実行
    3. 結果をDBに保存
    4. 進捗レポート出力
    """
    
    def __init__(self, start_date: str, end_date: str):
        """
        初期化
        
        Args:
            start_date: 開始日（YYYYMMDD）
            end_date: 終了日（YYYYMMDD）
        """
        self.start_date = start_date
        self.end_date = end_date
        self.conn = get_db_connection()
        self.detector = TroubleDetector(self.conn)
        
        # 統計情報
        self.stats = {
            'total_races': 0,
            'processed_races': 0,
            'detected_troubles': 0,
            'errors': 0,
            'keibajo_breakdown': {}
        }
    
    def get_races_in_period(self) -> List[Dict]:
        """
        期間内の全レースを取得
        
        Returns:
            list of dict: レース情報
                - race_date: レース日付（YYYYMMDD）
                - keibajo_code: 競馬場コード
                - race_bango: レース番号
        """
        query = """
            SELECT DISTINCT
                ra.kaisai_nen || ra.kaisai_tsukihi as race_date,
                ra.keibajo_code,
                ra.race_bango
            FROM nvd_ra ra
            WHERE ra.kaisai_nen || ra.kaisai_tsukihi BETWEEN %s AND %s
              AND ra.keibajo_code != '61'  -- ばんえい競馬除外
            ORDER BY race_date, keibajo_code, race_bango
        """
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, (self.start_date, self.end_date))
        races = cursor.fetchall()
        cursor.close()
        
        self.stats['total_races'] = len(races)
        
        logger.info(
            f"📊 期間内のレース数: {len(races)}件 "
            f"({self.start_date} 〜 {self.end_date})"
        )
        
        return races
    
    def get_race_horses(self, race_date: str, keibajo_code: str, race_bango: int) -> List[Dict]:
        """
        1レース分の全馬データを取得
        
        Args:
            race_date: レース日付（YYYYMMDD）
            keibajo_code: 競馬場コード
            race_bango: レース番号
        
        Returns:
            list of dict: 馬データ
                - ketto_toroku_bango: 血統登録番号
                - time: 走破タイム（秒）
                - kohan_3f: 上がり3F（秒）
                - corner_1, corner_2, corner_3, corner_4: 通過順位
        """
        query = """
            SELECT 
                se.ketto_toroku_bango,
                se.soha_time,          -- 走破タイム（4桁文字列）
                se.kohan_3f,           -- 上がり3F（3桁文字列）
                se.corner_1,
                se.corner_2,
                se.corner_3,
                se.corner_4,
                se.kakutei_chakujun
            FROM nvd_se se
            WHERE se.kaisai_nen || se.kaisai_tsukihi = %s
              AND se.keibajo_code = %s
              AND se.race_bango = %s
              AND se.kakutei_chakujun IS NOT NULL
              AND se.kakutei_chakujun != ''
        """
        
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute(query, (race_date, keibajo_code, race_bango))
        horses = cursor.fetchall()
        cursor.close()
        
        # データ型変換
        processed_horses = []
        for horse in horses:
            # soha_time: '2048' → 124.8秒
            soha_time_str = horse.get('soha_time', '0000')
            if soha_time_str and soha_time_str != '0000':
                try:
                    minutes = int(soha_time_str[0])
                    seconds = int(soha_time_str[1:3])
                    tenths = int(soha_time_str[3])
                    time_seconds = minutes * 60 + seconds + tenths / 10.0
                except (ValueError, IndexError):
                    time_seconds = None
            else:
                time_seconds = None
            
            # kohan_3f: '375' → 37.5秒
            kohan_3f_str = horse.get('kohan_3f', '000')
            if kohan_3f_str and kohan_3f_str != '000':
                try:
                    kohan_3f_seconds = int(kohan_3f_str) / 10.0
                except (ValueError, TypeError):
                    kohan_3f_seconds = None
            else:
                kohan_3f_seconds = None
            
            # corner位置（文字列→整数）
            corner_1 = safe_int(horse.get('corner_1'))
            corner_2 = safe_int(horse.get('corner_2'))
            corner_3 = safe_int(horse.get('corner_3'))
            corner_4 = safe_int(horse.get('corner_4'))
            
            processed_horses.append({
                'ketto_toroku_bango': horse['ketto_toroku_bango'],
                'time': time_seconds,
                'kohan_3f': kohan_3f_seconds,
                'corner_1': corner_1,
                'corner_2': corner_2,
                'corner_3': corner_3,
                'corner_4': corner_4
            })
        
        return processed_horses
    
    def process_race(self, race_date: str, keibajo_code: str, race_bango: int):
        """
        1レースの不利検知を実行
        
        Args:
            race_date: レース日付（YYYYMMDD）
            keibajo_code: 競馬場コード
            race_bango: レース番号
        """
        try:
            # レースデータ取得
            horses = self.get_race_horses(race_date, keibajo_code, race_bango)
            
            if len(horses) < 5:
                logger.debug(
                    f"スキップ: {race_date} {keibajo_code}-{race_bango}R "
                    f"(データ不足: {len(horses)}頭)"
                )
                return
            
            # 不利検知実行
            trouble_results = self.detector.detect_race_troubles(horses)
            
            if trouble_results:
                # DB保存
                race_info = {
                    'race_date': race_date,
                    'keibajo_code': keibajo_code,
                    'race_bango': race_bango
                }
                self.detector.save_trouble_data(race_info, trouble_results)
                
                # 統計更新
                self.stats['detected_troubles'] += len(trouble_results)
                
                # 競馬場別統計
                keibajo_name = KEIBAJO_NAMES.get(keibajo_code, keibajo_code)
                if keibajo_name not in self.stats['keibajo_breakdown']:
                    self.stats['keibajo_breakdown'][keibajo_name] = 0
                self.stats['keibajo_breakdown'][keibajo_name] += len(trouble_results)
            
            self.stats['processed_races'] += 1
            
            # 進捗表示（100レースごと）
            if self.stats['processed_races'] % 100 == 0:
                logger.info(
                    f"⏳ 進捗: {self.stats['processed_races']}/{self.stats['total_races']}レース "
                    f"({self.stats['processed_races']/self.stats['total_races']*100:.1f}%) "
                    f"| 不利検知: {self.stats['detected_troubles']}件"
                )
        
        except Exception as e:
            logger.error(
                f"❌ エラー: {race_date} {keibajo_code}-{race_bango}R - {e}"
            )
            self.stats['errors'] += 1
    
    def run(self):
        """
        バッチ処理実行
        """
        logger.info("=" * 80)
        logger.info("🚀 前走不利検知システム - バッチ処理開始")
        logger.info("=" * 80)
        logger.info(f"期間: {self.start_date} 〜 {self.end_date}")
        logger.info(f"対象: 地方競馬14場（ばんえい競馬除外）")
        logger.info("")
        
        start_time = datetime.now()
        
        # レース一覧取得
        races = self.get_races_in_period()
        
        if not races:
            logger.warning("⚠️ 処理対象のレースが見つかりませんでした")
            return
        
        # 各レースを処理
        for race in races:
            self.process_race(
                race['race_date'],
                race['keibajo_code'],
                race['race_bango']
            )
        
        end_time = datetime.now()
        elapsed_time = end_time - start_time
        
        # 最終レポート
        logger.info("")
        logger.info("=" * 80)
        logger.info("✅ バッチ処理完了")
        logger.info("=" * 80)
        logger.info(f"処理時間: {elapsed_time}")
        logger.info(f"総レース数: {self.stats['total_races']}")
        logger.info(f"処理レース数: {self.stats['processed_races']}")
        logger.info(f"不利検知件数: {self.stats['detected_troubles']}")
        logger.info(f"エラー件数: {self.stats['errors']}")
        logger.info("")
        logger.info("📊 競馬場別 不利検知件数:")
        for keibajo, count in sorted(
            self.stats['keibajo_breakdown'].items(),
            key=lambda x: x[1],
            reverse=True
        ):
            logger.info(f"  {keibajo}: {count}件")
        logger.info("=" * 80)
        
        self.conn.close()


def main():
    """
    メイン処理
    """
    parser = argparse.ArgumentParser(
        description='前走不利検知システム - バッチ処理'
    )
    parser.add_argument(
        '--start-date',
        type=str,
        default='20230101',
        help='開始日（YYYYMMDD形式）デフォルト: 20230101'
    )
    parser.add_argument(
        '--end-date',
        type=str,
        default='20260107',
        help='終了日（YYYYMMDD形式）デフォルト: 20260107（本日）'
    )
    
    args = parser.parse_args()
    
    # バッチ処理実行
    processor = BatchTroubleProcessor(args.start_date, args.end_date)
    processor.run()


if __name__ == '__main__':
    main()
