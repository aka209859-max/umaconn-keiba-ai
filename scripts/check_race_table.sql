-- ============================================================
-- レース情報テーブルの確認（距離データの所在確認）
-- ============================================================

-- 1. レース関連テーブルの一覧
SELECT 
    tablename,
    schemaname
FROM pg_tables 
WHERE schemaname = 'public' 
  AND (
    tablename LIKE '%race%' 
    OR tablename LIKE '%ra%'
    OR tablename LIKE '%nvd%'
  )
ORDER BY tablename;

-- 2. nvd_raテーブルの構造確認（レースマスタと推定）
SELECT 
    column_name, 
    data_type, 
    character_maximum_length
FROM information_schema.columns 
WHERE table_name = 'nvd_ra'
ORDER BY ordinal_position
LIMIT 50;

-- 3. nvd_raのサンプルデータ（最新3件）
SELECT *
FROM nvd_ra
ORDER BY kaisai_nen DESC, kaisai_tsukihi DESC
LIMIT 3;
