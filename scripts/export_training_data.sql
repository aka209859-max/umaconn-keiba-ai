-- ============================================================
-- Layer 3訓練データエクスポート用SQL
-- 1400m以上、corner_1有効、直近3ヶ月
-- ============================================================

SELECT 
    se.kaisai_nen || se.kaisai_tsukihi as race_date,
    se.keibajo_code,
    CAST(ra.kyori AS INTEGER) as kyori,
    ra.track_code,
    ra.babajotai_code_dirt as baba_code,
    -- 走破タイム（秒）
    CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
    CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
    CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0 as time_seconds,
    -- 上がり3F（秒）
    CAST(se.kohan_3f AS NUMERIC) / 10.0 as kohan_3f_seconds,
    -- コーナー順位
    CAST(se.corner_1 AS INTEGER) as corner_1,
    CAST(se.corner_2 AS INTEGER) as corner_2,
    CAST(se.corner_3 AS INTEGER) as corner_3,
    CAST(se.corner_4 AS INTEGER) as corner_4,
    -- Ground Truth: 実測前半3F
    (CAST(SUBSTRING(se.soha_time, 1, 1) AS INTEGER) * 60.0 +
     CAST(SUBSTRING(se.soha_time, 2, 2) AS INTEGER) +
     CAST(SUBSTRING(se.soha_time, 4, 1) AS INTEGER) / 10.0) -
    (CAST(se.kohan_3f AS NUMERIC) / 10.0) as actual_ten_3f
FROM nvd_se se
JOIN nvd_ra ra 
    ON se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
WHERE CAST(ra.kyori AS INTEGER) >= 1400
  AND se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20251007' AND '20260107'
  AND se.soha_time IS NOT NULL 
  AND se.soha_time != '0000'
  AND se.kohan_3f IS NOT NULL 
  AND se.kohan_3f != '000'
  AND se.corner_1 IS NOT NULL
  AND CAST(se.corner_1 AS INTEGER) > 0
  AND se.corner_2 IS NOT NULL
  AND CAST(se.corner_2 AS INTEGER) > 0
ORDER BY race_date DESC;
