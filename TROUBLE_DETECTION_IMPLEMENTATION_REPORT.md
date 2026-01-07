# 前走不利検知システム 実装レポート

**作成日:** 2026-01-07  
**プロジェクト:** NAR-AI予想システム  
**Phase:** 1 Step 1-3 完了

---

## 📋 目次

1. [実装概要](#実装概要)
2. [技術仕様](#技術仕様)
3. [誤検知対策と改善履歴](#誤検知対策と改善履歴)
4. [検証結果](#検証結果)
5. [今後の課題](#今後の課題)
6. [データベース設計](#データベース設計)
7. [使用方法](#使用方法)

---

## 実装概要

### 目的
地方競馬（NAR）の前走レースにおいて、馬が受けた「不利」を統計的異常検知により自動検出し、次走予想の精度向上に活用する。

### 対象期間
- **開発・検証期間:** 2025年12月7日〜2026年1月7日（直近1ヶ月）
- **本番運用想定:** 2023年1月1日〜現在（過去3年分）

### 対象競馬場
地方競馬14場（ばんえい競馬61を除外）:
- 30: 門別
- 35: 盛岡
- 36: 水沢
- 42: 浦和
- 43: 船橋
- 44: 大井
- 45: 川崎
- 46: 金沢
- 47: 笠松
- 48: 名古屋
- 50: 園田
- 51: 姫路
- 54: 高知
- 55: 佐賀

---

## 技術仕様

### 1. 出遅れ検知（Modified Z-score / MAD法）

#### 理論
- **テン3F相当タイム** = 走破タイム - 上がり3F
- レース内での相対的な遅れをMAD（中央絶対偏差）を用いたロバスト統計で検知
- Modified Z-score > 3.5 で出遅れ判定

#### 計算式
```
median_ten = PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ten_equivalent)
mad = PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ABS(ten_equivalent - median_ten))
modified_z_score = 0.6745 * (ten_equivalent - median_ten) / mad
trouble_score = min(100.0, modified_z_score * 20)
```

#### パラメータ
- **閾値:** Modified Z-score > 3.5
- **最小レース頭数:** 5頭以上
- **信頼度:** 0.85

---

### 2. 順位逆転検知（挟まれ・外回し）

#### 理論
- corner_1 → corner_4 の順位変動を分析
- 順位標準偏差 > 2.5 → 挟まれ/外回し
- 前半→後半で3頭以上後退 → 不利判定

#### 計算式
```
early_avg = (corner_1 + corner_2) / 2.0
late_avg = (corner_3 + corner_4) / 2.0
rank_decline = late_avg - early_avg

rank_std = SQRT(
    (POWER(corner_1 - avg_all, 2) +
     POWER(corner_2 - avg_all, 2) +
     POWER(corner_3 - avg_all, 2) +
     POWER(corner_4 - avg_all, 2)) / 4.0
)

trouble_score = min(100.0, rank_decline * 15 + rank_std * 10)
```

#### パラメータ
- **順位後退閾値:** 3.0頭以上
- **順位標準偏差閾値:** 2.5以上
- **信頼度:** 0.80

---

### 3. 統合スコア算出

#### 重み配分
- **出遅れスコア:** 0.4（40%）
- **順位逆転スコア:** 0.6（60%）

#### 不利タイプ
- `slow_start`: 出遅れのみ
- `rank_reversal`: 順位逆転のみ
- `mixed`: 両方検知

---

## 誤検知対策と改善履歴

### 問題1: 「逃げ失速」を「不利」として誤検知

#### 発見契機
2025年12月29日 笠松2R モリスカイ（馬ID: 2023104582）の検証

#### 実際の状況
```
1コーナー: 1番手（先頭）
2コーナー: 2番手
3コーナー: 7番手 ↓↓↓ (5頭後退)
4コーナー: 7番手
最終着順: 7着

レース動画確認結果: 「逃げてバテただけ」
```

#### システムの誤検知
```
出遅れ検知:
  - テン3F相当タイム: 63.60秒（レース最遅）
  - Modified Z-score: 24.28（異常に高い）
  - trouble_score: 40.00
  
順位逆転検知:
  - 前半平均: 1.5番手
  - 後半平均: 7.0番手
  - 順位後退数: 5.5頭
  - trouble_score: 60.00（重み0.6で算出）

統合結果: trouble_score = 100.00, trouble_type = mixed
```

#### 根本原因
「前半飛ばし過ぎ → 失速」を「不利」として検知してしまう

---

### 改善策1: 順位逆転検知に「逃げ失速」除外ロジック追加

#### 実装内容（v5）
```python
# 前半2番手以内 → 4頭以上後退 = 逃げ失速（不利ではない）
is_front_runner_fade = (
    early_avg <= 2.0 and  # 前半2番手以内
    rank_decline > 4.0     # 4頭以上後退
)

if is_front_runner_fade:
    logger.info(f"逃げ失速パターン除外: {ketto} → 不利ではない")
    continue
```

#### SQL版
```sql
WHERE (late_avg - early_avg) > 3.0
  AND rank_std > 2.5
  -- 🚫 除外: 逃げ失速（前半2番手以内→4頭以上後退）
  AND NOT (early_avg <= 2.0 AND (late_avg - early_avg) > 4.0);
```

#### 結果
順位逆転検知からは除外されたが、**出遅れ検知では依然として検知**

---

### 改善策2: 出遅れ検知にも「逃げ馬」除外ロジック追加

#### 問題の再定義
「テン3F相当タイムが遅い」には2つの意味がある:
1. **出遅れ:** スタートで遅れた（不利）
2. **逃げ・先行:** 前半飛ばし過ぎて全体的にペースが遅い（不利ではない）

#### 実装内容（v7 最終版）
```python
# 出遅れ判定前にコーナー順位をチェック
if modified_z > self.MAD_THRESHOLD:
    corner_1 = horse.get('corner_1')
    corner_2 = horse.get('corner_2')
    
    if corner_1 is not None and corner_2 is not None:
        if corner_1 > 0 and corner_2 > 0:
            early_avg = (corner_1 + corner_2) / 2.0
            
            # 前半2番手以内 = 逃げ・先行馬（出遅れではない）
            if early_avg <= 2.0:
                logger.info(f"逃げ馬除外: {ketto} → 出遅れではない")
                continue
```

#### SQL版
```sql
WHERE modified_z_score > 3.5
  -- 🚫 除外: 逃げ馬（前半2番手以内）
  AND NOT (corner_1 > 0 AND corner_2 > 0 AND (corner_1 + corner_2) / 2.0 <= 2.0);
```

---

### 検証結果: モリスカイ完全除外成功

#### Before（改善前）
```sql
SELECT COUNT(*) FROM nar_trouble_estimated
WHERE ketto_toroku_bango = '2023104582'
  AND race_date = '20251229';
-- found_count = 1 (誤検知)
```

#### After（改善後 v7）
```sql
SELECT COUNT(*) FROM nar_trouble_estimated
WHERE ketto_toroku_bango = '2023104582'
  AND race_date = '20251229';
-- found_count = 0 ✅（完全除外成功）
```

---

## 検証結果

### 直近1ヶ月のデータ（2025-12-07 〜 2026-01-07）

#### 検証前データ件数
- 改善前（v0）: 326件
- 改善版v5（順位逆転のみ除外）: 224件（-102件）
- 改善版v7（出遅れも除外）: 257件削除後の最終件数は実行時に確認

#### 除外された主なパターン
1. **逃げ失速パターン:** 前半2番手以内 → 4頭以上後退
2. **逃げ馬の誤検知:** 前半2番手以内で高いModified Z-score

---

## 今後の課題

### 1. 誤検知リスクが残るケース

#### ケースA: 「差し馬の好走」を誤検知する可能性
```
状況:
  後方待機（前半10番手）→ 最後に追い込んで2着
  
システムの判定:
  順位後退数 = 負の値（前進）
  → 現在のロジックでは検知されない（正しい）
  
リスク: なし
```

#### ケースB: 「前半3-5番手の失速」を見逃す可能性
```
状況:
  前半4番手（2.0 < early_avg <= 5.0）
  → 後半大幅後退（挟まれた可能性）
  
システムの判定:
  early_avg = 4.0 > 2.0 → 除外条件に該当しない
  → 正しく検知される
  
リスク: なし
```

#### ケースC: 「逃げ馬の真の不利」を見逃す可能性
```
状況:
  逃げ馬（前半1番手）が挟まれて失速
  
システムの判定:
  early_avg <= 2.0 → 逃げ馬として除外される
  
リスク: あり（低頻度だが重要）
```

### 改善案: コーナー順位の急変をチェック
```python
# corner_1 → corner_2 で大幅後退（挟まれた可能性）
if corner_1 <= 2 and corner_2 - corner_1 >= 5:
    # これは「逃げ馬が挟まれた」不利として検知
    pass
```

---

### 2. 閾値の最適化

#### 現在の閾値
- 出遅れ: Modified Z-score > 3.5
- 順位後退: 3.0頭以上
- 順位標準偏差: 2.5以上
- 逃げ馬除外: 前半2番手以内

#### 最適化の必要性
- 実データでの精度検証が必要
- 競馬場ごとに閾値を調整する可能性

---

### 3. 他の不利パターンの追加

#### 未実装の不利パターン
1. **出遅れ + 挟まれ（複合不利）:** 既に `mixed` として実装済み
2. **不良馬場の影響:** データ不足のため未実装
3. **騎手ミス（落馬・失格）:** 着順データで判別可能だが未実装
4. **故障・怪我:** データなし

---

## データベース設計

### テーブル: nar_trouble_estimated

#### スキーマ
```sql
CREATE TABLE nar_trouble_estimated (
    ketto_toroku_bango VARCHAR(10) NOT NULL,
    race_date VARCHAR(8) NOT NULL,
    keibajo_code VARCHAR(2) NOT NULL,
    race_bango INTEGER NOT NULL,
    trouble_score DECIMAL(5,2) NOT NULL,        -- 0-100の不利度スコア
    trouble_type VARCHAR(20) NOT NULL,          -- slow_start / rank_reversal / mixed
    confidence DECIMAL(3,2) NOT NULL,           -- 0.00-1.00の検知信頼度
    detection_method VARCHAR(50),               -- MAD / rank_reversal / ensemble
    raw_z_score DECIMAL(5,2),                   -- Modified Z-score
    rank_std DECIMAL(5,2),                      -- 順位標準偏差
    ten_equivalent DECIMAL(5,2),                -- テン3F相当タイム（秒）
    rank_decline DECIMAL(5,2),                  -- 順位後退数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ketto_toroku_bango, race_date, keibajo_code, race_bango)
);
```

#### インデックス
```sql
CREATE INDEX idx_trouble_score ON nar_trouble_estimated(trouble_score DESC);
CREATE INDEX idx_race_lookup ON nar_trouble_estimated(race_date, keibajo_code, race_bango);
CREATE INDEX idx_ketto_lookup ON nar_trouble_estimated(ketto_toroku_bango, race_date);
CREATE INDEX idx_trouble_type ON nar_trouble_estimated(trouble_type);
CREATE INDEX idx_confidence ON nar_trouble_estimated(confidence DESC);
```

---

## 使用方法

### 1. Python版バッチ処理

```bash
# 直近1ヶ月
python batch_process_trouble_detection.py --start-date 20251207 --end-date 20260107

# 過去3年分
python batch_process_trouble_detection.py --start-date 20230101 --end-date 20260107
```

### 2. SQL版バッチ処理

```sql
-- pgAdminで batch_trouble_detection_final.sql を実行
-- 日付範囲を変更して実行可能
```

### 3. 次走予想での使用（Phase 2で実装予定）

```python
# 前走不利補正を取得
from core.nar_trouble_detection import TroubleDetector

detector = TroubleDetector(db_connection)

# 前走不利データを取得
prev_trouble = get_prev_trouble_correction(
    ketto_toroku_bango='2023104582',
    prev_race_date='20251229',
    keibajo_code='47',
    race_bango=2
)

# HQS指数に反映
if prev_trouble:
    trouble_correction = prev_trouble['trouble_score'] / 100 * 3.0  # 最大3秒補正
    agari_index += trouble_correction * 10  # 指数化
```

---

## まとめ

### 実装成果
✅ 出遅れ検知（MAD法）実装  
✅ 順位逆転検知実装  
✅ 統合スコア算出実装  
✅ 逃げ失速パターン除外実装  
✅ 逃げ馬の誤検知除外実装  
✅ データベース設計・保存実装  
✅ バッチ処理実装（Python版・SQL版）

### 検証結果
✅ モリスカイ（逃げ失速）完全除外成功  
✅ 直近1ヶ月データで動作確認完了

### 次のステップ
- [ ] 過去3年分データの処理
- [ ] Phase 2: HQS指数への統合
- [ ] ファクター定義追加（F31-F33）
- [ ] 実予想での精度検証

---

**作成者:** AI Assistant  
**レビュー:** CEO  
**承認日:** 2026-01-07  
**バージョン:** v7 (最終版)

---

Play to Win. 10x Mindset. 🚀
