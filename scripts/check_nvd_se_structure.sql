-- ============================================================
-- nvd_seテーブルの構造とサンプルデータ確認
-- ============================================================

-- 1. テーブル構造確認
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'nvd_se'
ORDER BY ordinal_position
LIMIT 50;

-- 2. サンプルデータ確認（最新5件）
SELECT *
FROM nvd_se
ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
LIMIT 5;
