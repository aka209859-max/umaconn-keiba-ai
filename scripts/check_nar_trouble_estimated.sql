-- ============================================================
-- nar_trouble_estimatedテーブルの構造とデータ確認
-- ============================================================

-- 1. テーブル構造確認
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'nar_trouble_estimated'
ORDER BY ordinal_position;

-- 2. データ件数確認
SELECT 
    'nar_trouble_estimated全体' as category,
    COUNT(*) as total_records,
    MIN(race_date) as start_date,
    MAX(race_date) as end_date
FROM nar_trouble_estimated;

-- 3. 直近3ヶ月のデータ件数
SELECT 
    'nar_trouble_estimated（直近3ヶ月）' as category,
    COUNT(*) as total_records,
    MIN(race_date) as start_date,
    MAX(race_date) as end_date
FROM nar_trouble_estimated
WHERE race_date BETWEEN '20251007' AND '20260107';

-- 4. サンプルデータ確認（最新10件）
SELECT *
FROM nar_trouble_estimated
ORDER BY race_date DESC, keibajo_code, race_bango
LIMIT 10;
