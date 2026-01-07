-- temp_race_dataの存在確認と1200m戦データの統計
SELECT 
    'temp_race_data存在確認' as status,
    COUNT(*) as total_records
FROM temp_race_data
WHERE kyori = 1200;

-- 直近3ヶ月分の1200m戦データ統計
SELECT 
    '直近3ヶ月の1200m戦統計' as category,
    COUNT(*) as record_count,
    COUNT(DISTINCT race_date) as race_days,
    COUNT(DISTINCT keibajo_code) as track_count,
    MIN(race_date) as start_date,
    MAX(race_date) as end_date,
    AVG(time_seconds - kohan_3f_seconds) as avg_ten_3f,
    STDDEV(time_seconds - kohan_3f_seconds) as stddev_ten_3f,
    MIN(time_seconds - kohan_3f_seconds) as min_ten_3f,
    MAX(time_seconds - kohan_3f_seconds) as max_ten_3f
FROM temp_race_data
WHERE kyori = 1200
  AND kohan_3f_seconds IS NOT NULL
  AND race_date BETWEEN '20251007' AND '20260107';

-- 距離別のサンプル数（直近3ヶ月）
SELECT 
    '距離別データ分布' as category,
    kyori,
    COUNT(*) as sample_count,
    AVG(time_seconds) as avg_time,
    AVG(kohan_3f_seconds) as avg_kohan_3f
FROM temp_race_data
WHERE race_date BETWEEN '20251007' AND '20260107'
  AND kohan_3f_seconds IS NOT NULL
GROUP BY kyori
ORDER BY kyori;
