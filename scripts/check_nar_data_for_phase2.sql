-- ============================================================
-- Phase 2: 前半3F推定のためのデータ確認SQL
-- nvd_seテーブルから直接1200mデータを抽出
-- ============================================================

-- 1. 1200m戦のデータ件数確認（直近3ヶ月）
SELECT 
    '1200m戦データ件数（直近3ヶ月）' as category,
    COUNT(*) as total_records,
    COUNT(DISTINCT kaisai_nen || kaisai_tsukihi) as race_days,
    COUNT(DISTINCT keibajo_code) as track_count
FROM nvd_se
WHERE CAST(kyori AS INTEGER) = 1200
  AND kaisai_nen || kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND soha_time IS NOT NULL 
  AND soha_time != '0000'
  AND kohan_3f IS NOT NULL 
  AND kohan_3f != '000';

-- 2. 1200m戦の前半3F統計（Ground Truth）
SELECT 
    '1200m戦の前半3F統計' as category,
    COUNT(*) as record_count,
    AVG(
        (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(kohan_3f AS NUMERIC) / 10.0)
    ) as avg_ten_3f,
    STDDEV(
        (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(kohan_3f AS NUMERIC) / 10.0)
    ) as stddev_ten_3f,
    MIN(
        (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(kohan_3f AS NUMERIC) / 10.0)
    ) as min_ten_3f,
    MAX(
        (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(kohan_3f AS NUMERIC) / 10.0)
    ) as max_ten_3f
FROM nvd_se
WHERE CAST(kyori AS INTEGER) = 1200
  AND kaisai_nen || kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND soha_time IS NOT NULL 
  AND soha_time != '0000'
  AND kohan_3f IS NOT NULL 
  AND kohan_3f != '000';

-- 3. 距離別データ分布（直近3ヶ月）
SELECT 
    '距離別データ分布' as category,
    CAST(kyori AS INTEGER) as kyori,
    COUNT(*) as sample_count,
    AVG(
        CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
        CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
        CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0
    ) as avg_time_seconds,
    AVG(CAST(kohan_3f AS NUMERIC) / 10.0) as avg_kohan_3f_seconds
FROM nvd_se
WHERE kaisai_nen || kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND soha_time IS NOT NULL 
  AND soha_time != '0000'
  AND kohan_3f IS NOT NULL 
  AND kohan_3f != '000'
  AND kyori IS NOT NULL
GROUP BY CAST(kyori AS INTEGER)
ORDER BY CAST(kyori AS INTEGER);

-- 4. 1200m戦の展開パターン別統計
SELECT 
    '展開パターン別統計（1200m）' as category,
    CASE 
        WHEN CAST(corner_1 AS INTEGER) <= 2 THEN '逃げ・先行'
        WHEN CAST(corner_1 AS INTEGER) <= 5 THEN '中団'
        ELSE '後方'
    END as position_pattern,
    COUNT(*) as sample_count,
    AVG(
        (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
         CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
         CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
        (CAST(kohan_3f AS NUMERIC) / 10.0)
    ) as avg_ten_3f
FROM nvd_se
WHERE CAST(kyori AS INTEGER) = 1200
  AND kaisai_nen || kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND soha_time IS NOT NULL 
  AND soha_time != '0000'
  AND kohan_3f IS NOT NULL 
  AND kohan_3f != '000'
  AND corner_1 IS NOT NULL
GROUP BY 
    CASE 
        WHEN CAST(corner_1 AS INTEGER) <= 2 THEN '逃げ・先行'
        WHEN CAST(corner_1 AS INTEGER) <= 5 THEN '中団'
        ELSE '後方'
    END
ORDER BY position_pattern;
