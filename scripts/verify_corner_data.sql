-- ============================================================
-- nvd_seテーブルのcorner_1データ検証
-- 1200m戦の実際のcorner_1の値を確認
-- ============================================================

-- 1. 1200m戦のcorner_1の実データサンプル（直近10件）
SELECT 
    '1200m戦のcorner_1実データ' as category,
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    se.race_bango,
    se.ketto_toroku_bango,
    se.corner_1,
    se.corner_2,
    se.corner_3,
    se.corner_4,
    LENGTH(se.corner_1) as corner_1_length,
    LENGTH(se.corner_2) as corner_2_length,
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
ORDER BY race_date DESC
LIMIT 10;

-- 2. 1400m戦のcorner_1の実データサンプル（比較用）
SELECT 
    '1400m戦のcorner_1実データ' as category,
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    se.race_bango,
    se.ketto_toroku_bango,
    se.corner_1,
    se.corner_2,
    se.corner_3,
    se.corner_4,
    LENGTH(se.corner_1) as corner_1_length,
    se.soha_time,
    se.kohan_3f,
    ra.kyori
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE CAST(ra.kyori AS INTEGER) = 1400
  AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251207' AND '20260107'
ORDER BY race_date DESC
LIMIT 10;

-- 3. corner_1が'00'のデータ件数（全距離）
SELECT 
    'corner_1が00のデータ分布' as category,
    CAST(ra.kyori AS INTEGER) as kyori,
    COUNT(*) as total_count,
    COUNT(CASE WHEN se.corner_1 = '00' THEN 1 END) as corner_1_is_00,
    COUNT(CASE WHEN se.corner_1 IS NULL THEN 1 END) as corner_1_is_null,
    COUNT(CASE WHEN se.corner_1 = '' THEN 1 END) as corner_1_is_empty,
    COUNT(CASE WHEN se.corner_1 NOT IN ('00', '') AND se.corner_1 IS NOT NULL THEN 1 END) as corner_1_valid
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND ra.kyori IS NOT NULL
GROUP BY CAST(ra.kyori AS INTEGER)
ORDER BY CAST(ra.kyori AS INTEGER);
