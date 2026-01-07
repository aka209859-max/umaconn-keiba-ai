-- ============================================================
-- 1200m戦データのデバッグSQL
-- corner_1のデータ形式と分布を確認
-- ============================================================

-- 1. 1200m戦のcorner_1データ分布（直近3ヶ月）
SELECT 
    '1200m戦のcorner_1分布' as category,
    se.corner_1,
    COUNT(*) as count,
    CASE 
        WHEN se.corner_1 IS NULL THEN 'NULL'
        WHEN se.corner_1 = '' THEN 'EMPTY'
        WHEN se.corner_1 = '00' THEN 'ZERO'
        ELSE 'VALID'
    END as data_status
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
GROUP BY se.corner_1
ORDER BY count DESC
LIMIT 20;

-- 2. 1200m戦のサンプルデータ（corner_1が有効なデータ）
SELECT 
    '1200m戦サンプルデータ' as category,
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    se.race_bango,
    se.ketto_toroku_bango,
    se.corner_1,
    se.corner_2,
    se.corner_3,
    se.corner_4,
    se.soha_time,
    se.kohan_3f,
    ra.kyori
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
ORDER BY race_date DESC
LIMIT 10;

-- 3. 全距離のcorner_1データ分布（比較用）
SELECT 
    '全距離のcorner_1分布' as category,
    CAST(ra.kyori AS INTEGER) as kyori,
    COUNT(*) as total_count,
    COUNT(CASE WHEN se.corner_1 IS NOT NULL AND se.corner_1 != '00' AND se.corner_1 != '' THEN 1 END) as valid_corner_1_count,
    ROUND(
        100.0 * COUNT(CASE WHEN se.corner_1 IS NOT NULL AND se.corner_1 != '00' AND se.corner_1 != '' THEN 1 END) / 
        NULLIF(COUNT(*), 0), 
        2
    ) as valid_percentage
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
