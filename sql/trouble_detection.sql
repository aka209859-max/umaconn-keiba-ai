-- ============================================================
-- 前走不利検知システム データベース定義
-- ============================================================
-- 作成日: 2026-01-07
-- 目的: 統計的異常検知による前走不利の自動検出
-- ============================================================

-- ============================================================
-- 1. 前走不利検知結果保存テーブル
-- ============================================================

CREATE TABLE IF NOT EXISTS nar_trouble_estimated (
    -- 主キー情報
    ketto_toroku_bango VARCHAR(10) NOT NULL,     -- 血統登録番号
    race_date VARCHAR(8) NOT NULL,                -- 前走の日付（YYYYMMDD）
    keibajo_code VARCHAR(2) NOT NULL,             -- 競馬場コード
    race_bango INTEGER NOT NULL,                  -- レース番号
    
    -- 不利検知結果
    trouble_score DECIMAL(5,2) NOT NULL,          -- 0-100の不利度スコア
    trouble_type VARCHAR(20) NOT NULL,            -- slow_start/rank_reversal/mixed
    confidence DECIMAL(3,2) NOT NULL,             -- 0.00-1.00の検知信頼度
    
    -- 検知詳細情報
    detection_method VARCHAR(50),                  -- MAD/rank_reversal/ensemble
    raw_z_score DECIMAL(5,2),                     -- 生のZスコア（MAD法用）
    rank_std DECIMAL(5,2),                        -- 順位変動の標準偏差（順位逆転用）
    ten_equivalent DECIMAL(5,2),                  -- テン3F相当タイム（秒）
    rank_decline DECIMAL(5,2),                    -- 前半→後半の順位後退数
    
    -- メタ情報
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 主キー制約
    PRIMARY KEY (ketto_toroku_bango, race_date, keibajo_code, race_bango)
);

-- ============================================================
-- 2. インデックス作成
-- ============================================================

-- 不利スコア降順検索用（高スコアから取得）
CREATE INDEX IF NOT EXISTS idx_trouble_score 
    ON nar_trouble_estimated(trouble_score DESC);

-- レース検索用（日付・場所・レース番号）
CREATE INDEX IF NOT EXISTS idx_race_lookup 
    ON nar_trouble_estimated(race_date, keibajo_code, race_bango);

-- 馬検索用（血統登録番号・日付）
CREATE INDEX IF NOT EXISTS idx_ketto_lookup 
    ON nar_trouble_estimated(ketto_toroku_bango, race_date);

-- 不利タイプ別検索用
CREATE INDEX IF NOT EXISTS idx_trouble_type 
    ON nar_trouble_estimated(trouble_type);

-- 信頼度別検索用
CREATE INDEX IF NOT EXISTS idx_confidence 
    ON nar_trouble_estimated(confidence DESC);

-- ============================================================
-- 3. 前走不利データ取得用ビュー
-- ============================================================

CREATE OR REPLACE VIEW v_nvd_se_with_prev_trouble AS
SELECT 
    se.*,
    -- 前走不利データを結合
    te.trouble_score as prev_trouble_score,
    te.trouble_type as prev_trouble_type,
    te.confidence as prev_trouble_confidence,
    te.detection_method as prev_trouble_method,
    te.raw_z_score as prev_trouble_z_score,
    te.rank_std as prev_trouble_rank_std,
    te.ten_equivalent as prev_trouble_ten_time,
    te.rank_decline as prev_trouble_rank_decline
FROM nvd_se se
LEFT JOIN nar_trouble_estimated te ON
    te.ketto_toroku_bango = se.ketto_toroku_bango
    AND te.race_date = (
        -- 前走日付を構築（prev_race_date フィールドを使用）
        CASE 
            WHEN se.prev_race_date IS NOT NULL THEN se.prev_race_date
            ELSE NULL
        END
    )
    AND te.keibajo_code = se.prev_keibajo_code
    AND te.race_bango = se.prev_race_bango;

-- ============================================================
-- 4. 統計分析用ビュー
-- ============================================================

-- 不利タイプ別集計ビュー
CREATE OR REPLACE VIEW v_trouble_stats_by_type AS
SELECT 
    trouble_type,
    COUNT(*) as detection_count,
    AVG(trouble_score) as avg_score,
    AVG(confidence) as avg_confidence,
    MIN(trouble_score) as min_score,
    MAX(trouble_score) as max_score
FROM nar_trouble_estimated
GROUP BY trouble_type
ORDER BY avg_score DESC;

-- 競馬場別不利発生率ビュー
CREATE OR REPLACE VIEW v_trouble_stats_by_keibajo AS
SELECT 
    keibajo_code,
    COUNT(DISTINCT race_date || keibajo_code || race_bango) as total_races,
    COUNT(*) as trouble_count,
    ROUND(COUNT(*)::DECIMAL / COUNT(DISTINCT race_date || keibajo_code || race_bango) * 100, 2) as trouble_rate_pct,
    AVG(trouble_score) as avg_score,
    AVG(confidence) as avg_confidence
FROM nar_trouble_estimated
GROUP BY keibajo_code
ORDER BY trouble_rate_pct DESC;

-- 年月別不利検知トレンド
CREATE OR REPLACE VIEW v_trouble_trend_by_month AS
SELECT 
    SUBSTRING(race_date, 1, 6) as year_month,
    COUNT(*) as trouble_count,
    AVG(trouble_score) as avg_score,
    AVG(confidence) as avg_confidence,
    COUNT(CASE WHEN trouble_type = 'slow_start' THEN 1 END) as slow_start_count,
    COUNT(CASE WHEN trouble_type = 'rank_reversal' THEN 1 END) as rank_reversal_count,
    COUNT(CASE WHEN trouble_type = 'mixed' THEN 1 END) as mixed_count
FROM nar_trouble_estimated
GROUP BY SUBSTRING(race_date, 1, 6)
ORDER BY year_month DESC;

-- ============================================================
-- 5. 便利なクエリ例
-- ============================================================

-- 例1: 直近1ヶ月の高不利スコア馬TOP100
-- SELECT * FROM nar_trouble_estimated
-- WHERE race_date >= TO_CHAR(CURRENT_DATE - INTERVAL '1 month', 'YYYYMMDD')
-- ORDER BY trouble_score DESC
-- LIMIT 100;

-- 例2: 特定の馬の不利履歴
-- SELECT 
--     race_date,
--     keibajo_code,
--     race_bango,
--     trouble_score,
--     trouble_type,
--     confidence
-- FROM nar_trouble_estimated
-- WHERE ketto_toroku_bango = 'YOUR_KETTO'
-- ORDER BY race_date DESC;

-- 例3: 前走不利があった馬の次走成績
-- SELECT 
--     se.bamei,
--     se.kaisai_nen || se.kaisai_tsukihi as current_race_date,
--     se.kakutei_chakujun,
--     te.prev_trouble_score,
--     te.prev_trouble_type,
--     CASE 
--         WHEN se.kakutei_chakujun <= 3 THEN 1 
--         ELSE 0 
--     END as is_top3
-- FROM v_nvd_se_with_prev_trouble te
-- JOIN nvd_se se ON se.ketto_toroku_bango = te.ketto_toroku_bango
-- WHERE te.prev_trouble_score > 50
-- ORDER BY te.prev_trouble_score DESC;

-- ============================================================
-- 6. テーブル説明コメント
-- ============================================================

COMMENT ON TABLE nar_trouble_estimated IS '前走不利検知結果テーブル（統計的異常検知）';
COMMENT ON COLUMN nar_trouble_estimated.trouble_score IS '不利度スコア（0-100）高いほど大きな不利';
COMMENT ON COLUMN nar_trouble_estimated.trouble_type IS '不利タイプ：slow_start（出遅れ）/rank_reversal（順位逆転）/mixed（複合）';
COMMENT ON COLUMN nar_trouble_estimated.confidence IS '検知信頼度（0.00-1.00）高いほど確実';
COMMENT ON COLUMN nar_trouble_estimated.detection_method IS '検知手法：MAD（Modified Z-score）/rank_reversal/ensemble';
COMMENT ON COLUMN nar_trouble_estimated.raw_z_score IS 'Modified Z-score（MAD法、3.5以上で出遅れ判定）';
COMMENT ON COLUMN nar_trouble_estimated.rank_std IS '順位変動の標準偏差（2.5以上で不安定）';
COMMENT ON COLUMN nar_trouble_estimated.ten_equivalent IS 'テン3F相当タイム（走破タイム - 上がり3F）';
COMMENT ON COLUMN nar_trouble_estimated.rank_decline IS '前半→後半の順位後退数（3頭以上で不利判定）';

-- ============================================================
-- 完了
-- ============================================================
-- このSQLファイルを実行してテーブル作成完了
-- 次: nar_trouble_detection.py の実装
-- ============================================================
