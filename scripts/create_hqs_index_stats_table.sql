-- ================================================================================
-- HQS指数実績データ保存用テーブル
-- ================================================================================
-- 4つの指数（テン・位置・上がり・ペース）の実績データを競馬場別に保存
-- 
-- 使用目的:
-- 1. 各指数値ごとの単勝・複勝的中率を記録
-- 2. 補正回収率を計算してHQSスコア算出の基礎データとする
-- 3. 競馬場別の傾向分析
-- ================================================================================

-- 既存テーブルを削除（再作成の場合）
DROP TABLE IF EXISTS nar_hqs_index_stats CASCADE;

-- テーブル作成
CREATE TABLE nar_hqs_index_stats (
    -- 主キー
    keibajo_code CHAR(2) NOT NULL,           -- 競馬場コード（30-54）
    index_type VARCHAR(20) NOT NULL,         -- 指数種別（'ten', 'position', 'agari', 'pace'）
    index_value VARCHAR(10) NOT NULL,        -- 指数値（-100〜+100を10刻み、文字列化）
    
    -- 単勝実績
    cnt_win INTEGER DEFAULT 0,               -- 単勝試行回数
    hit_win INTEGER DEFAULT 0,               -- 単勝的中回数
    rate_win_hit DECIMAL(5,2) DEFAULT 0,     -- 単勝的中率（%）
    total_win_odds DECIMAL(10,2) DEFAULT 0,  -- 単勝オッズ合計
    adj_win_ret DECIMAL(6,2) DEFAULT 0,      -- 補正単勝回収率（%）
    
    -- 複勝実績
    cnt_place INTEGER DEFAULT 0,             -- 複勝試行回数
    hit_place INTEGER DEFAULT 0,             -- 複勝的中回数
    rate_place_hit DECIMAL(5,2) DEFAULT 0,   -- 複勝的中率（%）
    total_place_odds DECIMAL(10,2) DEFAULT 0,-- 複勝オッズ合計
    adj_place_ret DECIMAL(6,2) DEFAULT 0,    -- 補正複勝回収率（%）
    
    -- メタデータ
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 主キー制約
    PRIMARY KEY (keibajo_code, index_type, index_value)
);

-- インデックス作成（検索高速化）
CREATE INDEX idx_hqs_index_stats_type ON nar_hqs_index_stats(index_type);
CREATE INDEX idx_hqs_index_stats_keibajo ON nar_hqs_index_stats(keibajo_code);
CREATE INDEX idx_hqs_index_stats_hit_rate ON nar_hqs_index_stats(rate_win_hit DESC);

-- コメント追加
COMMENT ON TABLE nar_hqs_index_stats IS 'HQS指数実績データ（競馬場別・指数別）';
COMMENT ON COLUMN nar_hqs_index_stats.keibajo_code IS '競馬場コード';
COMMENT ON COLUMN nar_hqs_index_stats.index_type IS '指数種別（ten/position/agari/pace）';
COMMENT ON COLUMN nar_hqs_index_stats.index_value IS '指数値（-100〜+100を10刻み）';
COMMENT ON COLUMN nar_hqs_index_stats.cnt_win IS '単勝試行回数';
COMMENT ON COLUMN nar_hqs_index_stats.hit_win IS '単勝的中回数';
COMMENT ON COLUMN nar_hqs_index_stats.rate_win_hit IS '単勝的中率（%）';
COMMENT ON COLUMN nar_hqs_index_stats.adj_win_ret IS '補正単勝回収率（%）';
COMMENT ON COLUMN nar_hqs_index_stats.cnt_place IS '複勝試行回数';
COMMENT ON COLUMN nar_hqs_index_stats.hit_place IS '複勝的中回数';
COMMENT ON COLUMN nar_hqs_index_stats.rate_place_hit IS '複勝的中率（%）';
COMMENT ON COLUMN nar_hqs_index_stats.adj_place_ret IS '補正複勝回収率（%）';

-- ================================================================================
-- サンプルクエリ
-- ================================================================================

-- 1. 競馬場別の指数実績サマリ
-- SELECT 
--     keibajo_code,
--     index_type,
--     COUNT(*) as index_count,
--     SUM(cnt_win) as total_races,
--     AVG(rate_win_hit) as avg_win_hit_rate,
--     AVG(rate_place_hit) as avg_place_hit_rate
-- FROM nar_hqs_index_stats
-- GROUP BY keibajo_code, index_type
-- ORDER BY keibajo_code, index_type;

-- 2. 最も的中率が高い指数値トップ10（単勝）
-- SELECT 
--     keibajo_code,
--     index_type,
--     index_value,
--     cnt_win,
--     hit_win,
--     rate_win_hit,
--     adj_win_ret
-- FROM nar_hqs_index_stats
-- WHERE cnt_win >= 100  -- 試行回数が100回以上
-- ORDER BY rate_win_hit DESC
-- LIMIT 10;

-- 3. テン指数の分布（大井競馬場）
-- SELECT 
--     index_value,
--     cnt_win,
--     rate_win_hit,
--     rate_place_hit,
--     adj_win_ret,
--     adj_place_ret
-- FROM nar_hqs_index_stats
-- WHERE keibajo_code = '42' AND index_type = 'ten'
-- ORDER BY CAST(index_value AS INTEGER);

-- ================================================================================
-- 完了メッセージ
-- ================================================================================
SELECT 'nar_hqs_index_stats テーブル作成完了！' AS message;
