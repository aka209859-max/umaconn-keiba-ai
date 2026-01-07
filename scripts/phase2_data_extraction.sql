-- ============================================================
-- Phase 2: 前半3F推定のためのデータ抽出SQL
-- nvd_ra × nvd_se をJOINして必要データを取得
-- 期間: 直近3ヶ月（2025-10-07 〜 2026-01-07）
-- ============================================================

-- 1. 1200m戦のデータ件数確認（Ground Truth用）
SELECT 
    '1200m戦データ件数（直近3ヶ月）' as category,
    COUNT(*) as total_records,
    COUNT(DISTINCT se.kaisai_nen || se.kaisai_tsukihi) as race_days,
    COUNT(DISTINCT se.keibajo_code) as track_count
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE CAST(ra.kyori AS INTEGER) = 1200
  AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND se.soha_time IS NOT NULL 
  AND se.soha_time != '0000'
  AND se.kohan_3f IS NOT NULL 
  AND se.kohan_3f != '000';

-- 2. 1200m戦の前半3F統計（Ground Truth）
SELECT 
    '1200m戦の前半3F統計' as category,
    COUNT(*) as record_count,
    AVG(
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0)
    ) as avg_ten_3f,
    STDDEV(
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0)
    ) as stddev_ten_3f,
    MIN(
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0)
    ) as min_ten_3f,
    MAX(
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0)
    ) as max_ten_3f
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE CAST(ra.kyori AS INTEGER) = 1200
  AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND se.soha_time IS NOT NULL 
  AND se.soha_time != '0000'
  AND se.kohan_3f IS NOT NULL 
  AND se.kohan_3f != '000';

-- 3. 距離別データ分布（直近3ヶ月）
SELECT 
    '距離別データ分布' as category,
    CAST(ra.kyori AS INTEGER) as kyori,
    COUNT(*) as sample_count,
    AVG(
        CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
        CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
        CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0
    ) as avg_time_seconds,
    AVG(CAST(se.kohan_3f AS NUMERIC) / 10.0) as avg_kohan_3f_seconds
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND se.soha_time IS NOT NULL 
  AND se.soha_time != '0000'
  AND se.kohan_3f IS NOT NULL 
  AND se.kohan_3f != '000'
  AND ra.kyori IS NOT NULL
GROUP BY CAST(ra.kyori AS INTEGER)
ORDER BY CAST(ra.kyori AS INTEGER);

-- 4. 1200m戦の展開パターン別統計
SELECT 
    '展開パターン別統計（1200m）' as category,
    CASE 
        WHEN CAST(se.corner_1 AS INTEGER) <= 2 THEN '逃げ・先行'
        WHEN CAST(se.corner_1 AS INTEGER) <= 5 THEN '中団'
        ELSE '後方'
    END as position_pattern,
    COUNT(*) as sample_count,
    AVG(
        (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(se.kohan_3f AS NUMERIC) / 10.0)
    ) as avg_ten_3f
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE CAST(ra.kyori AS INTEGER) = 1200
  AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND se.soha_time IS NOT NULL 
  AND se.soha_time != '0000'
  AND se.kohan_3f IS NOT NULL 
  AND se.kohan_3f != '000'
  AND se.corner_1 IS NOT NULL
  AND se.corner_1 != '00'
GROUP BY 
    CASE 
        WHEN CAST(se.corner_1 AS INTEGER) <= 2 THEN '逃げ・先行'
        WHEN CAST(se.corner_1 AS INTEGER) <= 5 THEN '中団'
        ELSE '後方'
    END
ORDER BY position_pattern;
