# ファイル配置クイックリファレンス

**作成日**: 2026-01-08  
**目的**: どこに何があるか一目でわかる索引

---

## 🗂️ クイック索引

### 📊 データ収集・実行

| 用途 | ファイル | 場所 |
|------|---------|------|
| **HQS指数データ収集** ⭐ | `collect_index_stats.py` | `scripts/` |
| HQSテーブル作成 | `create_hqs_index_stats_table.sql` | `scripts/` |
| Phase2データ確認 | `check_nar_data_for_phase2.sql` | `scripts/` |
| Phase2データ抽出 | `phase2_data_extraction.sql` | `scripts/` |

### 🧮 コア計算モジュール

| 用途 | ファイル | 場所 |
|------|---------|------|
| **HQS指数計算エンジン** ⭐ | `index_calculator.py` | `core/` |
| テン3F推定 | `ten_3f_estimator.py` | `core/` |
| HQSスコア計算 | `hqs_calculator.py` | `core/` |
| RGSスコア計算 | `rgs_calculator.py` | `core/` |

### 🔢 NAR-SI計算モジュール

| バージョン | ファイル | 場所 |
|-----------|---------|------|
| Ver.2.0 Enhanced | `nar_si_calculator_v2_enhanced.py` | `core/` |
| Ver.2.1-A | `nar_si_calculator_v2_1_a.py` | `core/` |
| **Ver.2.1-B** ⭐ | `nar_si_calculator_v2_1_b.py` | `core/` |
| Ver.2.1-C | `nar_si_calculator_v2_1_c.py` | `core/` |
| Ver.3.0 データ取得 | `nar_si_v3_data_fetcher.py` | `core/` |
| Ver.3.0 特徴量 | `nar_si_v3_feature_engineering.py` | `core/` |

### ⚙️ 設定ファイル

| 用途 | ファイル | 場所 |
|------|---------|------|
| **競馬場別基準タイム** | `base_times.py` | `config/` |
| データベース接続 | `db_config.py` | `config/` |
| オッズ補正 | `odds_correction.py` | `config/` |

### 📖 ドキュメント

| 用途 | ファイル | 場所 |
|------|---------|------|
| **プロジェクト構造マスター** ⭐ | `PROJECT_STRUCTURE_MASTER.md` | `/` |
| ファイル配置リファレンス | `FILE_LOCATION_REFERENCE.md` | `/` |
| 競馬場コードマスター | `KEIBAJO_CODE_MASTER.md` | `docs/` |
| HQS実行ガイド | `HQS_INDEX_STATS_EXECUTION_GUIDE.md` | `docs/` |
| NAR-SI統合サマリ | `NAR_SI_INTEGRATION_SUMMARY.md` | `docs/` |

---

## 📁 ディレクトリ別索引

### `/` (ルート)

```
PROJECT_STRUCTURE_MASTER.md     # ⭐ プロジェクト全体の技術資料
FILE_LOCATION_REFERENCE.md      # 本ファイル
README.md                       # プロジェクト概要
ecosystem.config.cjs            # PM2設定（サンドボックス用）
.gitignore                      # Git除外設定
```

### `config/`

```
base_times.py        # 競馬場別基準タイム（1200m-2400m）
db_config.py         # PostgreSQL接続設定
odds_correction.py   # オッズ補正係数
```

### `core/`

```
# HQS関連
index_calculator.py         # ⭐ HQS指数計算エンジン（4指数）
ten_3f_estimator.py         # テン3F推定
hqs_calculator.py           # HQSスコア計算
rgs_calculator.py           # RGSスコア計算

# NAR-SI Ver.2.x
nar_si_calculator_v2_enhanced.py  # Ver.2.0 Enhanced
nar_si_calculator_v2_1_a.py       # Ver.2.1-A
nar_si_calculator_v2_1_b.py       # Ver.2.1-B ⭐ バランス版
nar_si_calculator_v2_1_c.py       # Ver.2.1-C

# NAR-SI Ver.3.0
nar_si_v3_data_fetcher.py         # データ取得
nar_si_v3_feature_engineering.py  # 特徴量エンジニアリング

# ファクター統計
calculate_factor_stats.py         # ファクター統計計算
factor_stats_calculator.py        # ファクター統計計算（詳細版）
```

### `scripts/`

```
# HQS Phase 2
collect_index_stats.py                # ⭐ HQS指数実績データ収集
create_hqs_index_stats_table.sql      # HQSテーブル作成

# データ確認
check_nar_data_for_phase2.sql         # Phase2データ確認
check_nar_si_v2_data.sql              # NAR-SI Ver.2データ確認
check_nar_trouble_estimated.sql       # トラブル推定確認
check_nvd_se_structure.sql            # nvd_se構造確認
check_race_table.sql                  # レーステーブル確認
check_temp_race_data.sql              # 一時レースデータ確認

# データ抽出
phase2_data_extraction.sql            # Phase2データ抽出
export_training_data.sql              # 学習データエクスポート

# デバッグ
debug_1200m_data.sql                  # 1200mデータデバッグ
verify_corner_data.sql                # コーナーデータ検証

# NAR-SI Ver.2.x
create_nar_si_v2_tables.sql           # NAR-SI Ver.2テーブル作成
create_nar_si_v2_tables_utf8.sql      # NAR-SI Ver.2テーブル作成（UTF-8）
insert_nar_si_v2_data.sql             # NAR-SI Ver.2データ挿入
insert_nar_si_v2_data_utf8.sql        # NAR-SI Ver.2データ挿入（UTF-8）

# ナイターレース設定
create_night_race_settings_v2.sql     # ナイターレース設定
```

### `docs/`

```
KEIBAJO_CODE_MASTER.md              # 競馬場コードマスター（13競馬場）
HQS_INDEX_STATS_EXECUTION_GUIDE.md  # HQS実行ガイド
NAR_SI_INTEGRATION_SUMMARY.md       # NAR-SI統合サマリ
```

### `tests/`

```
test_*.py           # 各種テストファイル
```

---

## 🎯 よく使うファイル

### 最重要（毎日使う）

1. **`scripts/collect_index_stats.py`**
   - HQS指数データ収集
   - 実行: `python scripts/collect_index_stats.py`

2. **`core/index_calculator.py`**
   - HQS指数計算
   - 4指数の実装

3. **`PROJECT_STRUCTURE_MASTER.md`**
   - プロジェクト全体の理解
   - 商用利用ガイド

### 重要（週1回以上）

4. **`core/nar_si_calculator_v2_1_b.py`**
   - NAR-SI Ver.2.1-B（バランス版）
   - 最も推奨されるバージョン

5. **`config/base_times.py`**
   - 競馬場別基準タイム
   - 距離別の標準タイム

6. **`docs/KEIBAJO_CODE_MASTER.md`**
   - 競馬場コード一覧
   - 期間設定の理由

### 参考（必要時）

7. **`core/ten_3f_estimator.py`**
   - 前半3F推定
   - アルゴリズムの理解

8. **`scripts/create_hqs_index_stats_table.sql`**
   - HQSテーブル構造
   - データベース設計

9. **`docs/HQS_INDEX_STATS_EXECUTION_GUIDE.md`**
   - HQS実行手順
   - トラブルシューティング

---

## 🔍 目的別ファイル検索

### 「HQS指数を計算したい」
1. `core/index_calculator.py` - 計算エンジン
2. `scripts/collect_index_stats.py` - データ収集
3. `core/ten_3f_estimator.py` - テン3F推定

### 「NAR-SIを計算したい」
1. `core/nar_si_calculator_v2_1_b.py` - 推奨版
2. `config/base_times.py` - 基準タイム
3. `core/nar_si_v3_data_fetcher.py` - Ver.3.0データ取得

### 「データベースを理解したい」
1. `PROJECT_STRUCTURE_MASTER.md` - データベース構造
2. `scripts/create_hqs_index_stats_table.sql` - HQSテーブル
3. `scripts/check_nvd_se_structure.sql` - nvd_se構造

### 「競馬場コードを確認したい」
1. `docs/KEIBAJO_CODE_MASTER.md` - 13競馬場の詳細
2. `scripts/collect_index_stats.py` - 期間設定の実装

### 「オッズを取得したい」
1. `core/index_calculator.py` - `parse_fukusho_odds()` 関数
2. `PROJECT_STRUCTURE_MASTER.md` - nvd_od テーブル仕様

### 「商用利用を検討したい」
1. `PROJECT_STRUCTURE_MASTER.md` - 商用利用ガイド
2. `FILE_LOCATION_REFERENCE.md` - 本ファイル

---

## 📊 データベーステーブル別ファイル

### nvd_ra (レース情報)
- 使用例: `scripts/collect_index_stats.py`
- 参照: `PROJECT_STRUCTURE_MASTER.md`

### nvd_se (レース結果)
- 使用例: `scripts/collect_index_stats.py`
- 確認: `scripts/check_nvd_se_structure.sql`

### nvd_od (オッズデータ) ⭐
- 使用例: `core/index_calculator.py` の `parse_fukusho_odds()`
- 重要: 複勝オッズはここから取得

### nvd_hr (払戻情報)
- 使用例: NAR-SI Ver.2.0（回収率計算）
- 注意: HQSではnvd_odを使用

### nar_hqs_index_stats (HQS指数実績) ⭐
- 作成: `scripts/create_hqs_index_stats_table.sql`
- 更新: `scripts/collect_index_stats.py`
- 参照: `core/hqs_calculator.py`

### nar_si_race_results (NAR-SI結果)
- 作成: `scripts/create_nar_si_v2_tables.sql`
- 更新: `core/nar_si_v3_data_fetcher.py`

---

## 🔧 トラブルシューティング用ファイル

### エラー: 「kaisai_yen は存在しません」
- 修正ファイル: `scripts/collect_index_stats.py`
- 対処: kaisai_yen → kaisai_nen に置換

### エラー: 「fukusho_odds は存在しません」
- 原因: nvd_se に fukusho_odds は存在しない
- 解決: nvd_od.odds_fukusho を使用
- 実装: `core/index_calculator.py` の `parse_fukusho_odds()`

### エラー: 「ModuleNotFoundError: config.db_config」
- 必要ファイル: `config/db_config.py`
- ダウンロード: GitHubから取得

### エラー: 「ModuleNotFoundError: psycopg2」
- インストール: `pip install psycopg2-binary`

### データが取得できない
- 確認SQL: `scripts/check_nar_data_for_phase2.sql`
- 期間確認: `docs/KEIBAJO_CODE_MASTER.md`

---

## 📦 配布用ファイルセット

### 最小構成（HQS指数のみ）
```
core/
  index_calculator.py
  ten_3f_estimator.py
config/
  base_times.py
  db_config.py
scripts/
  collect_index_stats.py
  create_hqs_index_stats_table.sql
docs/
  KEIBAJO_CODE_MASTER.md
PROJECT_STRUCTURE_MASTER.md
```

### 標準構成（NAR-SI + HQS）
```
最小構成 +
core/
  nar_si_calculator_v2_1_b.py
  nar_si_v3_data_fetcher.py
  hqs_calculator.py
scripts/
  create_nar_si_v2_tables.sql
docs/
  NAR_SI_INTEGRATION_SUMMARY.md
  HQS_INDEX_STATS_EXECUTION_GUIDE.md
```

### 完全版（商用利用）
```
すべてのファイル
```

---

## 🚀 初めてのユーザー向けガイド

### ステップ1: プロジェクト理解
1. `PROJECT_STRUCTURE_MASTER.md` を読む
2. `FILE_LOCATION_REFERENCE.md`（本ファイル）を読む
3. `docs/KEIBAJO_CODE_MASTER.md` を確認

### ステップ2: 環境構築
1. PostgreSQLをインストール
2. `config/db_config.py` を設定
3. `pip install psycopg2-binary`

### ステップ3: データベース作成
1. `scripts/create_hqs_index_stats_table.sql` を実行
2. `scripts/create_nar_si_v2_tables.sql` を実行

### ステップ4: データ収集
1. `python scripts/collect_index_stats.py` を実行（3-5時間）
2. 進捗を確認

### ステップ5: 予測実行
1. `core/hqs_calculator.py` を使用
2. `core/nar_si_calculator_v2_1_b.py` を使用
3. 結果を確認

---

## 📞 さらに詳しく知りたい場合

- **プロジェクト全体**: `PROJECT_STRUCTURE_MASTER.md`
- **HQS実行**: `docs/HQS_INDEX_STATS_EXECUTION_GUIDE.md`
- **競馬場コード**: `docs/KEIBAJO_CODE_MASTER.md`
- **NAR-SI統合**: `docs/NAR_SI_INTEGRATION_SUMMARY.md`

---

**最終更新日**: 2026-01-08  
**バージョン**: NAR-SI Ver.4.0 (Phase 2)  

**どこに何があるか、すぐに見つかります！** 🚀🔍
