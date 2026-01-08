-- nvd_seテーブルで「タイム」に関連するフィールドを確認
SELECT column_name, data_type, character_maximum_length
FROM information_schema.columns
WHERE table_name = 'nvd_se'
  AND table_schema = 'public'
  AND (
    column_name LIKE '%time%' 
    OR column_name LIKE '%タイム%'
  )
ORDER BY column_name;
