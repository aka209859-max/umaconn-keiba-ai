-- ============================================================
-- 前走不利検知システム - SQL版バッチ処理
-- CEO がpgAdminで直接実行できるSQL
-- ============================================================

-- 期間: 2025年12月7日〜2026年1月7日（直近1ヶ月）
-- 対象: 地方競馬14場（ばんえい競馬61除外）

-- ============================================================
-- Step 1: 一時テーブル作成（レースデータ）
-- ============================================================

DROP TABLE IF EXISTS temp_race_data CASCADE;

CREATE TEMP TABLE temp_race_data AS
SELECT 
    se.ketto_toroku_bango,
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    ra.race_bango,
    -- 走破タイム（秒に変換）
    CASE 
        WHEN se.soha_time IS NOT NULL AND se.soha_time != '0000' THEN
            CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +  -- 分
            CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +          -- 秒
            CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0     -- 0.1秒
        ELSE NULL
    END as time_seconds,
    -- 上がり3F（秒に変換）
    CASE 
        WHEN se.kohan_3f IS NOT NULL AND se.kohan_3f != '000' THEN
            CAST(se.kohan_3f AS NUMERIC) / 10.0
        ELSE NULL
    END as kohan_3f_seconds,
    -- テン3F相当タイム
    CASE 
        WHEN se.soha_time IS NOT NULL AND se.soha_time != '0000' 
             AND se.kohan_3f IS NOT NULL AND se.kohan_3f != '000' THEN
            (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
             CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
             CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
            (CAST(se.kohan_3f AS NUMERIC) / 10.0)
        ELSE NULL
    END as ten_equivalent,
    -- 通過順位
    CAST(se.corner_1 AS INTEGER) as corner_1,
    CAST(se.corner_2 AS INTEGER) as corner_2,
    CAST(se.corner_3 AS INTEGER) as corner_3,
    CAST(se.corner_4 AS INTEGER) as corner_4
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.keibajo_code = ra.keibajo_code 
    AND se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi 
    AND se.race_bango = ra.race_bango
WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251207' AND '20260107'
  AND se.keibajo_code != '61'  -- ばんえい競馬除外
  AND se.kakutei_chakujun IS NOT NULL
  AND se.kakutei_chakujun != '';

CREATE INDEX idx_temp_race ON temp_race_data(race_date, keibajo_code, race_bango);

SELECT '✅ Step 1完了: 一時テーブル作成' as status, COUNT(*) as total_horses FROM temp_race_data;

-- ============================================================
-- Step 2: 出遅れ検知（Modified Z-score / MAD法）
-- ============================================================

DROP TABLE IF EXISTS temp_slow_start CASCADE;

CREATE TEMP TABLE temp_slow_start AS
WITH race_stats AS (
    -- レースごとの統計（テン3F相当タイム）
    SELECT 
        race_date,
        keibajo_code,
        race_bango,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ten_equivalent) as median_ten,
        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABS(ten_equivalent - 
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ten_equivalent))) as mad
    FROM temp_race_data
    WHERE ten_equivalent IS NOT NULL
    GROUP BY race_date, keibajo_code, race_bango
    HAVING COUNT(*) >= 5  -- 5頭以上のレースのみ
),
z_scores AS (
    -- Modified Z-score計算
    SELECT 
        t.ketto_toroku_bango,
        t.race_date,
        t.keibajo_code,
        t.race_bango,
        t.ten_equivalent,
        s.median_ten,
        s.mad,
        -- Modified Z-score = 0.6745 * (x - median) / MAD
        CASE 
            WHEN s.mad > 0.01 THEN 
                0.6745 * (t.ten_equivalent - s.median_ten) / s.mad
            ELSE 0
        END as modified_z_score
    FROM temp_race_data t
    JOIN race_stats s
        ON t.race_date = s.race_date 
        AND t.keibajo_code = s.keibajo_code 
        AND t.race_bango = s.race_bango
    WHERE t.ten_equivalent IS NOT NULL
)
SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    'slow_start' as trouble_type,
    LEAST(100.0, modified_z_score * 20) as trouble_score,
    0.85 as confidence,
    'MAD' as detection_method,
    modified_z_score as raw_z_score,
    NULL::NUMERIC as rank_std,
    ten_equivalent,
    NULL::NUMERIC as rank_decline
FROM z_scores
WHERE modified_z_score > 3.5;  -- 閾値

SELECT '✅ Step 2完了: 出遅れ検知' as status, COUNT(*) as detected_count FROM temp_slow_start;

-- ============================================================
-- Step 3: 順位逆転検知（挟まれ・外回し）
-- ============================================================

DROP TABLE IF EXISTS temp_rank_reversal CASCADE;

CREATE TEMP TABLE temp_rank_reversal AS
WITH corner_stats AS (
    -- 順位変動の統計
    SELECT 
        ketto_toroku_bango,
        race_date,
        keibajo_code,
        race_bango,
        -- 前半平均（corner_1, corner_2）
        (COALESCE(corner_1, 0) + COALESCE(corner_2, 0)) / 2.0 as early_avg,
        -- 後半平均（corner_3, corner_4）
        (COALESCE(corner_3, 0) + COALESCE(corner_4, 0)) / 2.0 as late_avg,
        -- 順位標準偏差
        STDDEV_POP(
            ARRAY[corner_1, corner_2, corner_3, corner_4]::NUMERIC[]
        ) as rank_std
    FROM temp_race_data
    WHERE corner_1 > 0 AND corner_2 > 0 AND corner_3 > 0 AND corner_4 > 0
)
SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    'rank_reversal' as trouble_type,
    LEAST(100.0, (late_avg - early_avg) * 15 + rank_std * 10) as trouble_score,
    0.80 as confidence,
    'rank_reversal' as detection_method,
    NULL::NUMERIC as raw_z_score,
    rank_std,
    NULL::NUMERIC as ten_equivalent,
    (late_avg - early_avg) as rank_decline
FROM corner_stats
WHERE (late_avg - early_avg) > 3.0  -- 3頭以上後退
  AND rank_std > 2.5;               -- 順位変動が大きい

SELECT '✅ Step 3完了: 順位逆転検知' as status, COUNT(*) as detected_count FROM temp_rank_reversal;

-- ============================================================
-- Step 4: 統合スコア算出
-- ============================================================

DROP TABLE IF EXISTS temp_integrated_trouble CASCADE;

CREATE TEMP TABLE temp_integrated_trouble AS
WITH all_troubles AS (
    -- 出遅れスコア（重み 0.4）
    SELECT 
        ketto_toroku_bango,
        race_date,
        keibajo_code,
        race_bango,
        trouble_score * 0.4 as weighted_score,
        trouble_type,
        confidence,
        detection_method,
        raw_z_score,
        rank_std,
        ten_equivalent,
        rank_decline
    FROM temp_slow_start
    
    UNION ALL
    
    -- 順位逆転スコア（重み 0.6）
    SELECT 
        ketto_toroku_bango,
        race_date,
        keibajo_code,
        race_bango,
        trouble_score * 0.6 as weighted_score,
        trouble_type,
        confidence,
        detection_method,
        raw_z_score,
        rank_std,
        ten_equivalent,
        rank_decline
    FROM temp_rank_reversal
),
aggregated AS (
    -- 同一馬の不利を統合
    SELECT 
        ketto_toroku_bango,
        race_date,
        keibajo_code,
        race_bango,
        SUM(weighted_score) as total_score,
        CASE 
            WHEN COUNT(DISTINCT trouble_type) > 1 THEN 'mixed'
            ELSE MAX(trouble_type)
        END as trouble_type,
        AVG(confidence) as avg_confidence,
        CASE 
            WHEN COUNT(DISTINCT trouble_type) > 1 THEN 'ensemble'
            ELSE MAX(detection_method)
        END as detection_method,
        MAX(raw_z_score) as raw_z_score,
        MAX(rank_std) as rank_std,
        MAX(ten_equivalent) as ten_equivalent,
        MAX(rank_decline) as rank_decline
    FROM all_troubles
    GROUP BY ketto_toroku_bango, race_date, keibajo_code, race_bango
)
SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    LEAST(100.0, total_score) as trouble_score,
    trouble_type,
    avg_confidence as confidence,
    detection_method,
    raw_z_score,
    rank_std,
    ten_equivalent,
    rank_decline
FROM aggregated;

SELECT '✅ Step 4完了: 統合スコア算出' as status, COUNT(*) as total_troubles FROM temp_integrated_trouble;

-- ============================================================
-- Step 5: nar_trouble_estimated へ保存（UPSERT）
-- ============================================================

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
)
SELECT 
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
FROM temp_integrated_trouble
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
    updated_at = CURRENT_TIMESTAMP;

SELECT '✅ Step 5完了: データ保存' as status, COUNT(*) as saved_count FROM temp_integrated_trouble;

-- ============================================================
-- 最終レポート
-- ============================================================

SELECT 
    '🎉 バッチ処理完了！' as message,
    COUNT(*) as total_troubles,
    COUNT(DISTINCT race_date || keibajo_code || race_bango) as total_races,
    AVG(trouble_score) as avg_trouble_score,
    MIN(trouble_score) as min_score,
    MAX(trouble_score) as max_score
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107';

-- 競馬場別集計
SELECT 
    keibajo_code,
    COUNT(*) as trouble_count,
    AVG(trouble_score) as avg_score,
    MAX(trouble_score) as max_score
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107'
GROUP BY keibajo_code
ORDER BY trouble_count DESC;

-- 不利タイプ別集計
SELECT 
    trouble_type,
    COUNT(*) as count,
    AVG(trouble_score) as avg_score,
    AVG(confidence) as avg_confidence
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107'
GROUP BY trouble_type
ORDER BY count DESC;
