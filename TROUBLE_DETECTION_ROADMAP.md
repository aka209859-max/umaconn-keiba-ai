# 🎯 前走不利検知システム実装ロードマップ

**プロジェクト**: NAR-AI-YOSO 前走不利検知システム  
**作成日**: 2026-01-07  
**作成者**: AI戦略家（CSO兼クリエイティブディレクター）  
**目的**: 地方競馬データに不利フィールドが存在しないため、統計的異常検知で代替し、HQS指数とファクター分析に統合

---

## 📋 プロジェクト概要

### 🎯 目標
地方競馬の前走レースで発生した不利（出遅れ、挟まれ、外回し等）を統計的異常検知で自動検出し、次走の能力評価とファクター分析に活用する。

### 💡 戦略的価値
```
前走不利検知システム
    ↓
前走不利スコア算出 (prev_trouble_score)
    ↓
┌─────────────┬─────────────┬─────────────┐
│             │             │             │
HQS指数の     次走能力の    ファクター分析
前走不利補正   プラス評価    (F31: 前走不利度)
              「実力は      
              もっと上」    
```

**具体例:**
- 前走で大外を回された馬（不利スコア 75）
- 前走結果: 8着（見かけ上悪い）
- 実力評価: 「実力は5着相当」と推定
- 次走評価: 「前走不利があったので実力より悪く見える → 次走で巻き返し期待」
- HQS上がり指数: +1.5秒補正（不利がなければもっと速かった）

---

## 🗺️ 実装ロードマップ

### Phase 1: 前走不利検知システム実装（8-12時間）

#### Step 1-1: データベース設計・テーブル作成（1時間）

**成果物**: `trouble_detection.sql`

```sql
-- 前走不利検知結果保存テーブル
CREATE TABLE IF NOT EXISTS nar_trouble_estimated (
    ketto_toroku_bango VARCHAR(10) NOT NULL,
    race_date VARCHAR(8) NOT NULL,        -- 前走の日付（YYYYMMDD）
    keibajo_code VARCHAR(2) NOT NULL,
    race_bango INTEGER NOT NULL,
    trouble_score DECIMAL(5,2) NOT NULL,  -- 0-100の不利度スコア
    trouble_type VARCHAR(20) NOT NULL,    -- slow_start/rank_reversal/mixed
    confidence DECIMAL(3,2) NOT NULL,     -- 0.00-1.00の検知信頼度
    detection_method VARCHAR(50),          -- MAD/rank_reversal/ensemble
    raw_z_score DECIMAL(5,2),             -- 生のZスコア
    rank_std DECIMAL(5,2),                -- 順位変動の標準偏差
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ketto_toroku_bango, race_date, keibajo_code, race_bango)
);

-- インデックス作成
CREATE INDEX idx_trouble_score ON nar_trouble_estimated(trouble_score DESC);
CREATE INDEX idx_race_lookup ON nar_trouble_estimated(race_date, keibajo_code, race_bango);
CREATE INDEX idx_ketto_lookup ON nar_trouble_estimated(ketto_toroku_bango, race_date);

-- 前走不利データ取得用ビュー
CREATE OR REPLACE VIEW v_nvd_se_with_prev_trouble AS
SELECT 
    se.*,
    te.trouble_score as prev_trouble_score,
    te.trouble_type as prev_trouble_type,
    te.confidence as prev_trouble_confidence,
    te.detection_method as prev_trouble_method
FROM nvd_se se
LEFT JOIN nar_trouble_estimated te ON
    te.ketto_toroku_bango = se.ketto_toroku_bango
    AND te.race_date = se.prev_race_date
    AND te.keibajo_code = se.prev_keibajo_code
    AND te.race_bango = se.prev_race_bango;
```

**タスク**:
- [ ] PostgreSQLでテーブル作成
- [ ] インデックス作成
- [ ] ビュー作成
- [ ] 接続テスト

---

#### Step 1-2: Modified Z-score (MAD) 出遅れ検知（3時間）

**成果物**: `nar_trouble_detection.py` (出遅れ検知部分)

**理論**: TXT 4.1節「Modified Z-score (MAD法)」
- テン3F相当タイム = 走破タイム - 上がり3F
- レース内での相対的な遅れを検知
- Modified Z-score > 3.5 で出遅れ判定

**実装コード**:
```python
import numpy as np
from scipy import stats
import logging

logger = logging.getLogger(__name__)

class TroubleDetector:
    def __init__(self, db_connection):
        self.conn = db_connection
    
    def detect_slow_start(self, race_horses):
        """
        出遅れ検知（MAD法）
        
        Args:
            race_horses: レース内の全馬データ（list of dict）
                - ketto_toroku_bango
                - time (走破タイム)
                - kohan_3f (上がり3F)
        
        Returns:
            list of dict: 不利検知結果
        """
        ten_equivalent = []
        
        for horse in race_horses:
            if horse.get('time') and horse.get('kohan_3f'):
                # テン3F相当タイム推定
                ten_time = horse['time'] - horse['kohan_3f']
                ten_equivalent.append({
                    'ketto_toroku_bango': horse['ketto_toroku_bango'],
                    'ten_time': ten_time
                })
        
        if len(ten_equivalent) < 5:  # データ不足
            logger.warning(f"データ不足: {len(ten_equivalent)}頭のみ")
            return []
        
        # MAD計算（ロバスト統計）
        ten_times = [h['ten_time'] for h in ten_equivalent]
        median = np.median(ten_times)
        mad = np.median([abs(t - median) for t in ten_times])
        
        if mad == 0:
            logger.warning("MAD=0（全馬同じタイム）")
            return []
        
        results = []
        
        for horse in ten_equivalent:
            # Modified Z-score計算
            modified_z = 0.6745 * (horse['ten_time'] - median) / mad
            
            if modified_z > 3.5:  # 出遅れ検知閾値
                trouble_score = min(100, modified_z * 20)
                
                results.append({
                    'ketto_toroku_bango': horse['ketto_toroku_bango'],
                    'trouble_type': 'slow_start',
                    'trouble_score': trouble_score,
                    'confidence': 0.85,
                    'detection_method': 'MAD',
                    'raw_z_score': modified_z,
                    'rank_std': None
                })
                
                logger.info(
                    f"出遅れ検知: {horse['ketto_toroku_bango']} "
                    f"(Z={modified_z:.2f}, スコア={trouble_score:.1f})"
                )
        
        return results
```

**タスク**:
- [ ] MAD法の実装
- [ ] Modified Z-score計算
- [ ] 閾値調整（3.5で開始、後で最適化）
- [ ] ログ出力
- [ ] 単体テスト（10レース分）

---

#### Step 1-3: 順位逆転検知（3時間）

**成果物**: `nar_trouble_detection.py` (順位逆転検知部分)

**理論**: TXT 5.1節「順位逆転検知（Rank Reversal Detection）」
- corner_1 → corner_4 の順位変動を分析
- 順位標準偏差 > 閾値 → 挟まれ/外回し
- 前半→後半で3頭以上後退 → 不利判定

**実装コード**:
```python
def detect_rank_reversal(self, race_horses):
    """
    順位逆転検知（挟まれ・外回し）
    
    Args:
        race_horses: レース内の全馬データ（list of dict）
            - ketto_toroku_bango
            - corner_1, corner_2, corner_3, corner_4 (通過順位)
    
    Returns:
        list of dict: 不利検知結果
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
        
        # 前半→後半で大きく後退
        if len(corners) >= 3:
            early_avg = np.mean(corners[:2])  # 1-2コーナー平均
            late_avg = np.mean(corners[-2:])  # 3-4コーナー平均
            rank_decline = late_avg - early_avg
            
            # 判定基準:
            # - 3頭以上後退 AND 順位変動が大きい
            if rank_decline > 3 and rank_std > 2.5:
                trouble_score = min(100, rank_decline * 15 + rank_std * 10)
                
                results.append({
                    'ketto_toroku_bango': horse['ketto_toroku_bango'],
                    'trouble_type': 'rank_reversal',
                    'trouble_score': trouble_score,
                    'confidence': 0.80,
                    'detection_method': 'rank_reversal',
                    'raw_z_score': None,
                    'rank_std': rank_std
                })
                
                logger.info(
                    f"順位逆転検知: {horse['ketto_toroku_bango']} "
                    f"(後退={rank_decline:.1f}頭, 変動σ={rank_std:.1f}, "
                    f"スコア={trouble_score:.1f})"
                )
        
        # Kendall's Tau による相関検証（オプション）
        if len(corners) >= 4:
            expected_order = list(range(1, len(corners) + 1))
            tau, p_value = stats.kendalltau(expected_order, corners)
            
            if tau < -0.3 and p_value < 0.05:  # 負の相関 = 順位逆転
                logger.info(
                    f"Kendall's Tau異常: {horse['ketto_toroku_bango']} "
                    f"(τ={tau:.3f}, p={p_value:.3f})"
                )
    
    return results
```

**タスク**:
- [ ] 順位変動の標準偏差計算
- [ ] 前半→後半の順位変化分析
- [ ] Kendall's Tau検定（オプション）
- [ ] 閾値調整
- [ ] 単体テスト（10レース分）

---

#### Step 1-4: 統合スコア算出・保存（2時間）

**成果物**: `nar_trouble_detection.py` (統合処理部分)

**実装コード**:
```python
def calculate_integrated_trouble_score(self, slow_start_results, rank_reversal_results):
    """
    複数の不利検知結果を統合
    
    Args:
        slow_start_results: 出遅れ検知結果
        rank_reversal_results: 順位逆転検知結果
    
    Returns:
        dict: 統合された不利スコア（馬ごと）
    """
    integrated = {}
    
    # 出遅れスコア（重み 0.4）
    for result in slow_start_results:
        ketto = result['ketto_toroku_bango']
        integrated[ketto] = {
            'trouble_score': result['trouble_score'] * 0.4,
            'trouble_type': 'slow_start',
            'confidence': result['confidence'],
            'detection_method': result['detection_method'],
            'raw_z_score': result['raw_z_score'],
            'rank_std': None
        }
    
    # 順位逆転スコア（重み 0.6）
    for result in rank_reversal_results:
        ketto = result['ketto_toroku_bango']
        
        if ketto in integrated:
            # 両方の不利がある場合
            integrated[ketto]['trouble_score'] += result['trouble_score'] * 0.6
            integrated[ketto]['trouble_type'] = 'mixed'
            integrated[ketto]['confidence'] = (
                integrated[ketto]['confidence'] + result['confidence']
            ) / 2
            integrated[ketto]['detection_method'] = 'ensemble'
            integrated[ketto]['rank_std'] = result['rank_std']
        else:
            integrated[ketto] = {
                'trouble_score': result['trouble_score'] * 0.6,
                'trouble_type': 'rank_reversal',
                'confidence': result['confidence'],
                'detection_method': result['detection_method'],
                'raw_z_score': None,
                'rank_std': result['rank_std']
            }
    
    return integrated

def save_trouble_data(self, race_info, trouble_results):
    """
    不利検知結果をDBに保存
    
    Args:
        race_info: レース情報（日付、場所等）
        trouble_results: 統合された不利スコア
    """
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
            rank_std
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (ketto_toroku_bango, race_date, keibajo_code, race_bango)
        DO UPDATE SET
            trouble_score = EXCLUDED.trouble_score,
            trouble_type = EXCLUDED.trouble_type,
            confidence = EXCLUDED.confidence,
            detection_method = EXCLUDED.detection_method,
            raw_z_score = EXCLUDED.raw_z_score,
            rank_std = EXCLUDED.rank_std,
            created_at = CURRENT_TIMESTAMP
    """
    
    cursor = self.conn.cursor()
    
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
            result['rank_std']
        ])
    
    self.conn.commit()
    logger.info(
        f"不利データ保存完了: {race_info['race_date']} "
        f"{race_info['keibajo_code']}{race_info['race_bango']}R "
        f"({len(trouble_results)}頭)"
    )
```

**タスク**:
- [ ] 統合スコア計算（重み付け）
- [ ] DB保存処理
- [ ] UPSERT（重複時は更新）
- [ ] トランザクション管理
- [ ] エラーハンドリング

---

#### Step 1-5: バッチ処理・過去データ分析（3時間）

**成果物**: `batch_process_trouble_detection.py`

**実装コード**:
```python
#!/usr/bin/env python3
"""
前走不利検知バッチ処理
過去3年分のレースデータを分析して不利を検知
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from nar_trouble_detection import TroubleDetector
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    """DB接続"""
    return psycopg2.connect(
        host="localhost",
        database="nardb",
        user="nartora_user",
        password="your_password",
        cursor_factory=RealDictCursor
    )

def fetch_race_data(conn, start_date, end_date):
    """
    過去レースデータ取得
    
    Args:
        conn: DB接続
        start_date: 開始日（YYYYMMDD）
        end_date: 終了日（YYYYMMDD）
    
    Returns:
        list: レースごとにグループ化されたデータ
    """
    query = """
        SELECT 
            se.ketto_toroku_bango,
            se.kaisai_nen || se.kaisai_tsukihi as race_date,
            se.keibajo_code,
            ra.race_bango,
            se.corner_1,
            se.corner_2,
            se.corner_3,
            se.corner_4,
            se.kohan_3f,
            se.time,
            ra.kyori,
            ra.tosu
        FROM nvd_se se
        JOIN nvd_ra ra ON 
            se.keibajo_code = ra.keibajo_code
            AND se.kaisai_nen = ra.kaisai_nen
            AND se.kaisai_tsukihi = ra.kaisai_tsukihi
            AND se.race_bango = ra.race_bango
        WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN %s AND %s
            AND se.kakutei_chakujun IS NOT NULL
            AND se.time IS NOT NULL
        ORDER BY race_date, keibajo_code, race_bango
    """
    
    cursor = conn.cursor()
    cursor.execute(query, [start_date, end_date])
    return cursor.fetchall()

def group_by_race(race_data):
    """レース単位でグループ化"""
    races = {}
    
    for row in race_data:
        key = (row['race_date'], row['keibajo_code'], row['race_bango'])
        
        if key not in races:
            races[key] = {
                'race_date': row['race_date'],
                'keibajo_code': row['keibajo_code'],
                'race_bango': row['race_bango'],
                'horses': []
            }
        
        races[key]['horses'].append(row)
    
    return list(races.values())

def main():
    """メイン処理"""
    # 過去3年分のデータを処理
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')
    
    logger.info(f"前走不利検知バッチ開始: {start_date} - {end_date}")
    
    conn = get_db_connection()
    detector = TroubleDetector(conn)
    
    try:
        # レースデータ取得
        logger.info("レースデータ取得中...")
        race_data = fetch_race_data(conn, start_date, end_date)
        logger.info(f"取得件数: {len(race_data)}件")
        
        # レース単位でグループ化
        races = group_by_race(race_data)
        logger.info(f"レース数: {len(races)}レース")
        
        # レースごとに不利検知
        processed = 0
        detected = 0
        
        for race in races:
            # 出遅れ検知
            slow_start_results = detector.detect_slow_start(race['horses'])
            
            # 順位逆転検知
            rank_reversal_results = detector.detect_rank_reversal(race['horses'])
            
            # 統合スコア算出
            trouble_results = detector.calculate_integrated_trouble_score(
                slow_start_results, 
                rank_reversal_results
            )
            
            # DB保存
            if trouble_results:
                detector.save_trouble_data(race, trouble_results)
                detected += len(trouble_results)
            
            processed += 1
            
            if processed % 100 == 0:
                logger.info(f"処理進捗: {processed}/{len(races)}レース")
        
        logger.info(f"処理完了: {processed}レース, {detected}件の不利検知")
        
    finally:
        conn.close()

if __name__ == '__main__':
    main()
```

**タスク**:
- [ ] 過去3年分のデータ取得クエリ
- [ ] レース単位でのグループ化
- [ ] バッチ処理ループ
- [ ] 進捗ログ出力
- [ ] エラーハンドリング
- [ ] 実行（約2-3時間）

---

### Phase 2: HQS指数への統合（2-3時間）

#### Step 2-1: 前走不利補正関数の実装（1時間）

**成果物**: `core/index_calculator.py` (前走不利補正部分)

**実装コード**:
```python
def get_prev_trouble_correction(conn, ketto_toroku_bango, prev_race_date, 
                                prev_keibajo_code, prev_race_bango):
    """
    前走の不利補正を取得
    
    Args:
        conn: DB接続
        ketto_toroku_bango: 血統登録番号
        prev_race_date: 前走日付（YYYYMMDD）
        prev_keibajo_code: 前走競馬場コード
        prev_race_bango: 前走レース番号
    
    Returns:
        tuple: (補正値（秒）, 不利タイプ)
    """
    if not all([ketto_toroku_bango, prev_race_date, prev_keibajo_code, prev_race_bango]):
        return 0.0, 'なし'
    
    query = """
        SELECT trouble_score, trouble_type, confidence
        FROM nar_trouble_estimated
        WHERE ketto_toroku_bango = %s
          AND race_date = %s
          AND keibajo_code = %s
          AND race_bango = %s
    """
    
    cursor = conn.cursor()
    cursor.execute(query, [ketto_toroku_bango, prev_race_date, prev_keibajo_code, prev_race_bango])
    result = cursor.fetchone()
    
    if not result:
        return 0.0, 'なし'
    
    trouble_score = result['trouble_score']  # 0-100
    trouble_type = result['trouble_type']
    confidence = result['confidence']
    
    # スコアを補正値（秒）に変換
    # trouble_score 100 = 最大2.0秒のプラス補正
    # 前走で不利があった → 実力はもっと上 → 次走の能力評価をプラス
    correction = (trouble_score / 100) * 2.0 * confidence
    
    logger.info(
        f"前走不利補正: {ketto_toroku_bango} "
        f"(スコア={trouble_score:.1f}, タイプ={trouble_type}, "
        f"補正={correction:.2f}秒)"
    )
    
    return correction, trouble_type
```

**タスク**:
- [ ] 前走不利データ取得クエリ
- [ ] スコア→秒数変換ロジック
- [ ] 信頼度の反映
- [ ] NULL処理
- [ ] ログ出力

---

#### Step 2-2: 上がり指数への統合（1時間）

**成果物**: `core/index_calculator.py` (上がり指数計算部分の修正)

**実装コード**:
```python
def calculate_agari_index_from_prev(conn, prev_kohan_3f, prev_kyori, prev_baba_code, 
                                    prev_keibajo_code,
                                    ketto_toroku_bango=None, 
                                    prev_race_date=None, 
                                    prev_race_bango=None):
    """
    前走データから上がり指数を計算
    
    Args:
        conn: DB接続
        prev_kohan_3f: 前走上がり3F
        prev_kyori: 前走距離
        prev_baba_code: 前走馬場コード
        prev_keibajo_code: 前走競馬場コード
        ketto_toroku_bango: 血統登録番号（前走不利補正用）
        prev_race_date: 前走日付（前走不利補正用）
        prev_race_bango: 前走レース番号（前走不利補正用）
    
    Returns:
        tuple: (上がり指数, 不利タイプ)
    """
    if not prev_kohan_3f or prev_kohan_3f <= 0:
        logger.warning(f"前走上がり3Fデータなし")
        return 50.0, 'なし'
    
    # 基準タイム取得
    base_time = get_base_time(prev_keibajo_code, prev_kyori, 'kohan_3f')
    if not base_time:
        logger.warning(f"基準タイム取得失敗: {prev_keibajo_code} {prev_kyori}m")
        return 50.0, 'なし'
    
    # 馬場補正
    baba_correction = get_baba_correction_value(prev_baba_code)
    
    # 前走不利補正（NEW!）
    trouble_correction, trouble_type = get_prev_trouble_correction(
        conn,
        ketto_toroku_bango, 
        prev_race_date, 
        prev_keibajo_code, 
        prev_race_bango
    )
    
    # 指数計算
    # 前走で不利があった → 実力はもっと上 → プラス補正
    agari_index = ((base_time - prev_kohan_3f) + baba_correction + trouble_correction) * 10
    agari_index = max(-100.0, min(100.0, round(agari_index, 1)))
    
    logger.info(
        f"上がり指数 {agari_index} "
        f"(前走3F={prev_kohan_3f}s, 基準={base_time}s, "
        f"馬場補正={baba_correction}s, "
        f"前走不利補正={trouble_correction}s [{trouble_type}])"
    )
    
    return agari_index, trouble_type
```

**タスク**:
- [ ] calculate_agari_index_from_prev 関数の修正
- [ ] 前走不利補正の組み込み
- [ ] ログ出力の追加
- [ ] 単体テスト

---

#### Step 2-3: 位置指数への統合（オプション、30分）

**実装コード**:
```python
def calculate_position_index_from_prev(prev_corner_1, prev_corner_2, prev_corner_3, 
                                       prev_corner_4, prev_tosu,
                                       prev_trouble_score=0):
    """
    前走データから位置指数を計算
    
    Args:
        prev_corner_1-4: 前走通過順位
        prev_tosu: 前走出走頭数
        prev_trouble_score: 前走不利スコア（0-100）
    
    Returns:
        float: 位置指数
    """
    corners = [prev_corner_1, prev_corner_2, prev_corner_3, prev_corner_4]
    corners = [c for c in corners if c is not None and c > 0]
    
    if not corners or not prev_tosu or prev_tosu <= 0:
        logger.warning(f"前走通過順位データ不足")
        return 50.0
    
    avg_position = sum(corners) / len(corners)
    
    # 前走不利補正（オプション）
    # 不利があった場合、実力順位はもっと前と推定
    if prev_trouble_score > 50:
        position_correction = (prev_trouble_score / 100) * 2.0  # 最大2頭分前
        avg_position = max(1.0, avg_position - position_correction)
        logger.info(f"位置指数に前走不利補正: {position_correction:.1f}頭分前")
    
    position_index = round((avg_position / prev_tosu) * 100, 1)
    
    logger.info(
        f"位置指数 {position_index} "
        f"(前走平均順位={avg_position:.1f}/{prev_tosu}頭)"
    )
    
    return position_index
```

**タスク**:
- [ ] 位置指数への前走不利補正（オプション）
- [ ] テスト

---

### Phase 3: ファクター定義への追加（30分）

#### Step 3-1: ファクター定義追加

**成果物**: `config/factor_definitions.py` (F31-F33追加)

**実装コード**:
```python
# Phase 4: 前走不利検知統合（2026-01-07追加）
{
    'id': 'F31',
    'name': '前走不利度スコア',
    'category': '前走不利',
    'table': 'nar_trouble_estimated',
    'column': 'trouble_score',
    'display_column': 'trouble_score',
    'description': '前走レースでの不利度（0-100）統計的異常検知',
    'data_type': 'decimal',
    'factor_type': 'single',
    'join_condition': """
        LEFT JOIN nar_trouble_estimated te ON
            te.ketto_toroku_bango = se.ketto_toroku_bango
            AND te.race_date = se.prev_race_date
            AND te.keibajo_code = se.prev_keibajo_code
            AND te.race_bango = se.prev_race_bango
    """,
    'notes': '出遅れ・順位逆転を統計的異常検知で自動検出'
},
{
    'id': 'F32',
    'name': '前走不利タイプ',
    'category': '前走不利',
    'table': 'nar_trouble_estimated',
    'column': 'trouble_type',
    'display_column': 'trouble_type',
    'description': '出遅れ/挟まれ/外回し等の分類',
    'data_type': 'varchar',
    'factor_type': 'single',
    'values': ['slow_start', 'rank_reversal', 'mixed', 'なし'],
    'notes': 'slow_start: 出遅れ, rank_reversal: 順位逆転, mixed: 複合'
},
{
    'id': 'F33',
    'name': '前走不利検知信頼度',
    'category': '前走不利',
    'table': 'nar_trouble_estimated',
    'column': 'confidence',
    'display_column': 'confidence',
    'description': '不利検知の信頼度（0.00-1.00）',
    'data_type': 'decimal',
    'factor_type': 'single',
    'notes': '0.85以上: 高信頼, 0.70-0.85: 中信頼, 0.70未満: 低信頼'
}
```

**タスク**:
- [ ] F31-F33定義追加
- [ ] JOIN条件の記述
- [ ] データ型・値域の定義
- [ ] 説明文の作成

---

#### Step 3-2: データ取得クエリの更新

**成果物**: `core/data_fetcher.py` (前走不利データ取得部分)

**実装コード**:
```python
def get_tomorrow_races_with_prev_trouble(conn):
    """
    明日の出走馬データ（前走不利データ含む）を取得
    """
    query = """
        SELECT 
            se.*,
            te.trouble_score as prev_trouble_score,
            te.trouble_type as prev_trouble_type,
            te.confidence as prev_trouble_confidence
        FROM nvd_se se
        LEFT JOIN nar_trouble_estimated te ON
            te.ketto_toroku_bango = se.ketto_toroku_bango
            AND te.race_date = se.prev_race_date
            AND te.keibajo_code = se.prev_keibajo_code
            AND te.race_bango = se.prev_race_bango
        WHERE se.kaisai_nen || se.kaisai_tsukihi = %s
        ORDER BY se.keibajo_code, se.race_bango, se.umaban
    """
    
    tomorrow = get_tomorrow_date()
    cursor = conn.cursor()
    cursor.execute(query, [tomorrow])
    return cursor.fetchall()
```

**タスク**:
- [ ] LEFT JOIN追加
- [ ] prev_trouble_* カラム取得
- [ ] テスト

---

### Phase 4: 検証・テスト（2-3時間）

#### Step 4-1: 単体テスト

**成果物**: `tests/test_trouble_detection.py`

```python
import unittest
from nar_trouble_detection import TroubleDetector

class TestTroubleDetection(unittest.TestCase):
    def setUp(self):
        self.detector = TroubleDetector(get_test_db_connection())
    
    def test_detect_slow_start(self):
        """出遅れ検知テスト"""
        race_horses = [
            {'ketto_toroku_bango': 'A001', 'time': 80.0, 'kohan_3f': 38.0},  # テン42.0
            {'ketto_toroku_bango': 'A002', 'time': 78.0, 'kohan_3f': 38.0},  # テン40.0
            {'ketto_toroku_bango': 'A003', 'time': 85.0, 'kohan_3f': 38.0},  # テン47.0（出遅れ）
        ]
        
        results = self.detector.detect_slow_start(race_horses)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['ketto_toroku_bango'], 'A003')
        self.assertEqual(results[0]['trouble_type'], 'slow_start')
        self.assertGreater(results[0]['trouble_score'], 50)
    
    def test_detect_rank_reversal(self):
        """順位逆転検知テスト"""
        race_horses = [
            {
                'ketto_toroku_bango': 'B001',
                'corner_1': 2, 'corner_2': 3, 'corner_3': 7, 'corner_4': 8
            },  # 大きく後退
        ]
        
        results = self.detector.detect_rank_reversal(race_horses)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['trouble_type'], 'rank_reversal')
        self.assertGreater(results[0]['trouble_score'], 40)

if __name__ == '__main__':
    unittest.main()
```

**タスク**:
- [ ] 出遅れ検知テスト
- [ ] 順位逆転検知テスト
- [ ] 統合スコアテスト
- [ ] エッジケーステスト

---

#### Step 4-2: 統合テスト

**成果物**: `tests/test_hqs_with_trouble.py`

```python
def test_agari_index_with_prev_trouble():
    """前走不利補正込みの上がり指数テスト"""
    
    # テストケース1: 前走不利なし
    agari_index_1, trouble_type_1 = calculate_agari_index_from_prev(
        conn=test_conn,
        prev_kohan_3f=37.5,
        prev_kyori=1400,
        prev_baba_code='2',
        prev_keibajo_code='30',
        ketto_toroku_bango='TEST001',
        prev_race_date='20260101',
        prev_race_bango=1
    )
    
    print(f"前走不利なし: 上がり指数={agari_index_1}, タイプ={trouble_type_1}")
    
    # テストケース2: 前走大外を回された（trouble_score=75）
    # 事前にダミーデータ挿入
    insert_dummy_trouble(test_conn, 'TEST002', '20260101', '30', 1, 75.0, 'rank_reversal')
    
    agari_index_2, trouble_type_2 = calculate_agari_index_from_prev(
        conn=test_conn,
        prev_kohan_3f=39.0,  # 同じ条件
        prev_kyori=1400,
        prev_baba_code='2',
        prev_keibajo_code='30',
        ketto_toroku_bango='TEST002',
        prev_race_date='20260101',
        prev_race_bango=1
    )
    
    print(f"前走大外を回された: 上がり指数={agari_index_2}, タイプ={trouble_type_2}")
    
    # 不利があった馬の方が指数が高くなるはず
    assert agari_index_2 > agari_index_1, "前走不利補正が機能していない"
```

**タスク**:
- [ ] HQS指数への統合テスト
- [ ] 前走不利あり/なしの比較
- [ ] ファクター取得テスト

---

#### Step 4-3: 実データ検証

**成果物**: `validation_report.md`

**検証内容**:
1. 過去100レースのサンプル抽出
2. 不利検知結果の目視確認
3. 競馬場・距離別の検知率分析
4. Precision @ K評価

```python
def validate_trouble_detection():
    """実データでの検証"""
    
    query = """
        SELECT 
            se.bamei,
            se.kaisai_nen || se.kaisai_tsukihi as race_date,
            se.keibajo_code,
            ra.race_bango,
            se.kakutei_chakujun,
            te.trouble_score,
            te.trouble_type,
            te.confidence
        FROM nvd_se se
        LEFT JOIN nar_trouble_estimated te ON ...
        WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20250101' AND '20251231'
        ORDER BY te.trouble_score DESC NULLS LAST
        LIMIT 100
    """
    
    results = execute_query(query)
    
    # 上位100件の不利検知結果を分析
    # - 競馬場別分布
    # - 不利タイプ別分布
    # - スコア分布
    # - 目視確認
```

**タスク**:
- [ ] サンプル抽出
- [ ] 検知結果の分析
- [ ] 競馬場・距離別集計
- [ ] レポート作成

---

## 📊 成功基準

### Phase 1（前走不利検知システム）
- ✅ `nar_trouble_estimated` テーブル作成完了
- ✅ 過去3年分のレースデータ分析完了
- ✅ 出遅れ検知精度 > 75%
- ✅ 順位逆転検知精度 > 80%
- ✅ 統合スコア算出・保存完了

### Phase 2（HQS統合）
- ✅ 前走不利データを次走の能力評価に反映
- ✅ 上がり指数に前走不利補正適用
- ✅ テストケース「前走大外を回された馬」で動作確認
- ✅ 不利あり/なしで指数差を確認

### Phase 3（ファクター追加）
- ✅ F31-F33（前走不利度・タイプ・信頼度）定義追加
- ✅ prev_race_date でJOIN可能
- ✅ データ取得クエリ動作確認

### Phase 4（検証）
- ✅ 単体テスト全件パス
- ✅ 統合テスト全件パス
- ✅ 実データ検証完了
- ✅ Precision @ 100 > 60%（目標）

---

## 📈 期待効果

### 1. HQS指数の精度向上
- **現状**: 前走不利補正なし
- **実装後**: 統計的不利検知で補正適用
- **期待向上幅**: +8-12%（充実度 83% → 91-95%）

### 2. 予想精度への貢献
```
具体例: 前走で大外を回された馬
- 前走結果: 8着（見かけ上悪い）
- 不利スコア: 75
- 実力評価: 「実力は5着相当」
- 次走評価: 「巻き返し期待」
- 上がり指数: +1.5秒補正
```

### 3. ファクター分析の拡充
```sql
-- 前走不利馬の次走成績分析
SELECT 
    CASE 
        WHEN prev_trouble_score >= 70 THEN '大きな不利'
        WHEN prev_trouble_score >= 40 THEN '中程度の不利'
        ELSE '軽微な不利'
    END as trouble_level,
    COUNT(*) as race_count,
    AVG(CASE WHEN kakutei_chakujun <= 3 THEN 1 ELSE 0 END) as top3_rate,
    AVG(tansho_haraimodoshi) as avg_payoff
FROM v_nvd_se_with_prev_trouble
WHERE prev_trouble_score > 30
GROUP BY trouble_level;
```

**期待結果**:
- 大きな不利があった馬の次走複勝率: 30-40%
- 中程度の不利があった馬の次走複勝率: 25-35%
- 軽微な不利があった馬の次走複勝率: 20-30%

---

## 🗓️ 実装スケジュール

### 今日（2026-01-07）
- **14:00-15:00**: Phase 1 Step 1-1（DBテーブル作成）
- **15:00-18:00**: Phase 1 Step 1-2（出遅れ検知実装）
- **18:00-21:00**: Phase 1 Step 1-3（順位逆転検知実装）
- **21:00-23:00**: Phase 1 Step 1-4（統合スコア算出）

### 明日（2026-01-08）
- **09:00-12:00**: Phase 1 Step 1-5（バッチ処理・過去データ分析）
- **13:00-15:00**: Phase 2（HQS指数への統合）
- **15:00-16:00**: Phase 3（ファクター定義追加）
- **16:00-18:00**: Phase 4（検証・テスト）
- **18:00-19:00**: ドキュメント作成・レポート

**推定完了**: 2026-01-08 19:00

---

## 📚 参照資料

1. **理論・手法**:
   - 添付ファイル「競馬データ（JRA/NAR）における不利・アクシデント検知のための統計的異常値検出フレームワーク.txt」
   - TXT 4.1節: Modified Z-score (MAD法)
   - TXT 5.1節: 順位逆転検知（Rank Reversal Detection）
   - TXT 6.1節: Isolation Forest（Phase 2で実装予定）

2. **データ検証**:
   - 前回提供した「前半3F推定の実データ検証プロンプト」

3. **実装環境**:
   - NAR-SI Ver.4.0
   - PostgreSQL（nardb）
   - nvd_se, nvd_ra テーブル

---

## 🚀 次のアクション

1. **GitHubに保存**: このロードマップを保存してコミット
2. **CEO承認待ち**: 実装開始の最終確認
3. **Phase 1開始**: DBテーブル作成から着手

**Play to Win. 10x Mindset. 実装準備完了！🚀**

---

## 📝 変更履歴

- 2026-01-07 14:00: ロードマップ初版作成
- 前走不利検知システムの全体設計完了
- Phase 1-4の詳細実装計画策定
- 成功基準・期待効果の明確化
