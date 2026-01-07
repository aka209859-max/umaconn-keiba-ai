-- ============================================================
-- 前走不利検知システム - SQL版バッチ処理（最終修正版 v4）
-- 期間: 2025年12月7日〜2026年1月7日（直近1ヶ月）
-- エラー修正: race_bango の型変換を追加
-- ============================================================

-- Step 1: 一時テーブル作成
DROP TABLE IF EXISTS temp_race_data CASCADE;

CREATE TEMP TABLE temp_race_data AS
SELECT 
    se.ketto_toroku_bango,
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    CAST(se.race_bango AS INTEGER) as race_bango,  -- VARCHAR → INTEGER に変換
    CASE 
        WHEN se.soha_time IS NOT NULL AND se.soha_time != '0000' THEN
            CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
            CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
            CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0
        ELSE NULL
    END as time_seconds,
    CASE 
        WHEN se.kohan_3f IS NOT NULL AND se.kohan_3f != '000' THEN
            CAST(se.kohan_3f AS NUMERIC) / 10.0
        ELSE NULL
    END as kohan_3f_seconds,
    CASE 
        WHEN se.soha_time IS NOT NULL AND se.soha_time != '0000' 
             AND se.kohan_3f IS NOT NULL AND se.kohan_3f != '000' THEN
            (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
             CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
             CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
            (CAST(se.kohan_3f AS NUMERIC) / 10.0)
        ELSE NULL
    END as ten_equivalent,
    CAST(se.corner_1 AS INTEGER) as corner_1,
    CAST(se.corner_2 AS INTEGER) as corner_2,
    CAST(se.corner_3 AS INTEGER) as corner_3,
    CAST(se.corner_4 AS INTEGER) as corner_4
FROM nvd_se se
WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251207' AND '20260107'
  AND se.keibajo_code != '61'
  AND se.kakutei_chakujun IS NOT NULL
  AND se.kakutei_chakujun != ''
  AND se.race_bango IS NOT NULL;

CREATE INDEX idx_temp_race ON temp_race_data(race_date, keibajo_code, race_bango);

SELECT '✅ Step 1完了: 一時テーブル作成' as status, COUNT(*) as total_horses FROM temp_race_data;

-- Step 2: 出遅れ検知（修正版: 2段階に分割）
DROP TABLE IF EXISTS temp_slow_start CASCADE;

-- Step 2-1: レースごとの中央値を計算
DROP TABLE IF EXISTS temp_race_medians CASCADE;

CREATE TEMP TABLE temp_race_medians AS
SELECT 
    race_date,
    keibajo_code,
    race_bango,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ten_equivalent) as median_ten
FROM temp_race_data
WHERE ten_equivalent IS NOT NULL
GROUP BY race_date, keibajo_code, race_bango
HAVING COUNT(*) >= 5;

-- Step 2-2: MAD（中央絶対偏差）を計算
DROP TABLE IF EXISTS temp_race_mad CASCADE;

CREATE TEMP TABLE temp_race_mad AS
SELECT 
    t.race_date,
    t.keibajo_code,
    t.race_bango,
    m.median_ten,
    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABS(t.ten_equivalent - m.median_ten)) as mad
FROM temp_race_data t
JOIN temp_race_medians m
    ON t.race_date = m.race_date 
    AND t.keibajo_code = m.keibajo_code 
    AND t.race_bango = m.race_bango
WHERE t.ten_equivalent IS NOT NULL
GROUP BY t.race_date, t.keibajo_code, t.race_bango, m.median_ten;

-- Step 2-3: Modified Z-score計算と出遅れ判定
CREATE TEMP TABLE temp_slow_start AS
WITH z_scores AS (
    SELECT 
        t.ketto_toroku_bango,
        t.race_date,
        t.keibajo_code,
        t.race_bango,
        t.ten_equivalent,
        s.median_ten,
        s.mad,
        CASE 
            WHEN s.mad > 0.01 THEN 
                0.6745 * (t.ten_equivalent - s.median_ten) / s.mad
            ELSE 0
        END as modified_z_score
    FROM temp_race_data t
    JOIN temp_race_mad s
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
WHERE modified_z_score > 3.5;

SELECT '✅ Step 2完了: 出遅れ検知' as status, COUNT(*) as detected_count FROM temp_slow_start;

-- Step 3: 順位逆転検知
DROP TABLE IF EXISTS temp_rank_reversal CASCADE;

CREATE TEMP TABLE temp_rank_reversal AS
WITH corner_stats AS (
    SELECT 
        ketto_toroku_bango,
        race_date,
        keibajo_code,
        race_bango,
        (corner_1 + corner_2) / 2.0 as early_avg,
        (corner_3 + corner_4) / 2.0 as late_avg,
        -- 順位標準偏差を手動計算
        SQRT(
            (POWER(corner_1 - (corner_1 + corner_2 + corner_3 + corner_4) / 4.0, 2) +
             POWER(corner_2 - (corner_1 + corner_2 + corner_3 + corner_4) / 4.0, 2) +
             POWER(corner_3 - (corner_1 + corner_2 + corner_3 + corner_4) / 4.0, 2) +
             POWER(corner_4 - (corner_1 + corner_2 + corner_3 + corner_4) / 4.0, 2)) / 4.0
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
WHERE (late_avg - early_avg) > 3.0
  AND rank_std > 2.5
  -- 🚫 除外: 「逃げ失速」パターン（前半3番手以内 → 4頭以上後退）
  AND NOT (early_avg <= 3.0 AND (late_avg - early_avg) > 4.0);

SELECT '✅ Step 3完了: 順位逆転検知' as status, COUNT(*) as detected_count FROM temp_rank_reversal;

-- Step 4: 統合スコア算出
DROP TABLE IF EXISTS temp_integrated_trouble CASCADE;

CREATE TEMP TABLE temp_integrated_trouble AS
WITH all_troubles AS (
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

-- Step 5: データ保存
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

-- 最終レポート
SELECT 
    '🎉 バッチ処理完了！' as message,
    COUNT(*) as total_troubles,
    COUNT(DISTINCT race_date || keibajo_code || race_bango::TEXT) as total_races,
    ROUND(AVG(trouble_score), 2) as avg_trouble_score,
    ROUND(MIN(trouble_score), 2) as min_score,
    ROUND(MAX(trouble_score), 2) as max_score
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107';

-- 競馬場別集計
SELECT 
    keibajo_code,
    COUNT(*) as trouble_count,
    ROUND(AVG(trouble_score), 2) as avg_score,
    ROUND(MAX(trouble_score), 2) as max_score
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107'
GROUP BY keibajo_code
ORDER BY trouble_count DESC;

-- 不利タイプ別集計
SELECT 
    trouble_type,
    COUNT(*) as count,
    ROUND(AVG(trouble_score), 2) as avg_score,
    ROUND(AVG(confidence), 2) as avg_confidence
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107'
GROUP BY trouble_type
ORDER BY count DESC;

-- サンプルデータ表示（上位10件）
SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    ROUND(trouble_score, 2) as trouble_score,
    trouble_type,
    ROUND(confidence, 2) as confidence
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251207' AND '20260107'
ORDER BY trouble_score DESC
LIMIT 10;
