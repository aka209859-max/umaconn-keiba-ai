-- 前半3F計算の検証
-- サンプル: 直近10件のデータで計算を確認

SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    ROUND(CAST(ten_equivalent AS NUMERIC), 2) as ten_equivalent_calculated,
    ROUND(CAST(trouble_score AS NUMERIC), 2) as trouble_score,
    trouble_type,
    detection_method
FROM nar_trouble_estimated
WHERE trouble_type IN ('slow_start', 'mixed')
  AND ten_equivalent IS NOT NULL
ORDER BY race_date DESC, trouble_score DESC
LIMIT 10;
