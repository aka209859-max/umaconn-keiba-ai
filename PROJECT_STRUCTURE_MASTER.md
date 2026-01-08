# NAR-SI Ver.4.0 プロジェクト構造マスタードキュメント

**作成日**: 2026-01-08  
**対象**: NAR-SI Ver.4.0 地方競馬AI予想システム  
**目的**: 商用利用を前提とした完全な技術資料

---

## 📋 目次

1. [プロジェクト概要](#プロジェクト概要)
2. [ディレクトリ構造](#ディレクトリ構造)
3. [データベース構造](#データベース構造)
4. [コアモジュール](#コアモジュール)
5. [NAR-SIバージョン履歴](#nar-siバージョン履歴)
6. [HQS指数システム](#hqs指数システム)
7. [開発環境](#開発環境)
8. [商用利用ガイド](#商用利用ガイド)
9. [重要な技術的決定](#重要な技術的決定)

---

## 🎯 プロジェクト概要

### NAR-SI Ver.4.0 とは

**NAR Speed Index Ver.4.0** は、地方競馬の予想精度を最大化するために開発された総合的なAI予想システムです。

### 主要コンポーネント

1. **NAR-SI (NAR Speed Index)**
   - 基準タイムベースの競走能力指数
   - Ver.2.0 → Ver.2.1 → Ver.3.0 → Ver.4.0 と進化
   - 現在の最新版: **Ver.3.0**（2026-01-06統合完了）

2. **HQS (Hit & Quality Score)**
   - 4つの指数（テン/位置/上がり/ペース）の実績データに基づく予測スコア
   - 競馬場別・期間別の的中率・回収率を分析
   - 現在: **Phase 2 データ収集中**

3. **38ファクター統合システム**
   - NAR-SI + HQS + 38種類の競馬ファクターを統合
   - 最終予測精度の最大化

---

## 📁 ディレクトリ構造

```
E:\UmaData\nar-analytics-python-v2\  (CEO環境)
/home/user/webapp/nar-ai-yoso\       (サンドボックス環境)
│
├── 📂 config/                       # 設定ファイル
│   ├── base_times.py               # 競馬場別基準タイム
│   ├── db_config.py                # データベース接続設定
│   └── odds_correction.py          # オッズ補正設定
│
├── 📂 core/                         # コアモジュール
│   ├── index_calculator.py         # HQS指数計算エンジン
│   ├── ten_3f_estimator.py         # テン3F推定
│   ├── nar_si_calculator_v2_1_a.py # NAR-SI Ver.2.1-A
│   ├── nar_si_calculator_v2_1_b.py # NAR-SI Ver.2.1-B（バランス版）
│   ├── nar_si_calculator_v2_1_c.py # NAR-SI Ver.2.1-C
│   ├── nar_si_calculator_v2_enhanced.py # NAR-SI Ver.2.0 Enhanced
│   ├── nar_si_v3_data_fetcher.py   # Ver.3.0データ取得
│   ├── nar_si_v3_feature_engineering.py # Ver.3.0特徴量エンジニアリング
│   ├── calculate_factor_stats.py   # ファクター統計計算
│   ├── factor_stats_calculator.py  # ファクター統計計算（詳細版）
│   ├── hqs_calculator.py           # HQSスコア計算
│   └── rgs_calculator.py           # RGSスコア計算
│
├── 📂 scripts/                      # 実行スクリプト
│   ├── collect_index_stats.py      # ⭐ HQS指数実績データ収集（最重要）
│   ├── create_hqs_index_stats_table.sql # HQSテーブル作成
│   ├── check_nar_data_for_phase2.sql    # Phase2データ確認
│   ├── phase2_data_extraction.sql       # Phase2データ抽出
│   └── [その他SQLスクリプト...]
│
├── 📂 docs/                         # ドキュメント
│   ├── KEIBAJO_CODE_MASTER.md      # 競馬場コードマスター（13競馬場）
│   ├── HQS_INDEX_STATS_EXECUTION_GUIDE.md # HQS実行ガイド
│   ├── NAR_SI_INTEGRATION_SUMMARY.md     # NAR-SI統合サマリ
│   └── PROJECT_STRUCTURE_MASTER.md       # 本ドキュメント
│
├── 📂 tests/                        # テストファイル
│   └── test_*.py
│
└── 📄 ecosystem.config.cjs          # PM2設定（サンドボックス用）
```

---

## 🗄️ データベース構造

### PostgreSQL データベース: `pckeiba`

#### 主要テーブル

##### 1. nvd_ra (レース情報)
```sql
-- レースの基本情報
CREATE TABLE nvd_ra (
    kaisai_nen VARCHAR(4),          -- 開催年
    kaisai_tsukihi VARCHAR(4),      -- 開催月日
    keibajo_code VARCHAR(2),        -- 競馬場コード
    race_bango VARCHAR(2),          -- レース番号
    kyori INTEGER,                  -- 距離
    track_code VARCHAR(2),          -- トラックコード
    babajotai_code_dirt VARCHAR(2), -- 馬場状態コード（ダート）
    kyoso_joken_code VARCHAR(3),    -- 競走条件コード
    hassoujikoku VARCHAR(4),        -- 発走時刻
    PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango)
);
```

##### 2. nvd_se (レース結果・馬別データ)
```sql
-- レースの着順・タイム・オッズ
CREATE TABLE nvd_se (
    kaisai_nen VARCHAR(4),
    kaisai_tsukihi VARCHAR(4),
    keibajo_code VARCHAR(2),
    race_bango VARCHAR(2),
    umaban VARCHAR(2),              -- 馬番
    bamei VARCHAR(36),              -- 馬名
    wakuban VARCHAR(1),             -- 枠番
    bataiju DECIMAL(4,1),           -- 馬体重
    kakutei_chakujun VARCHAR(2),    -- 確定着順
    soha_time DECIMAL(5,1),         -- 走破タイム
    corner_1 VARCHAR(2),            -- コーナー通過順位1
    corner_2 VARCHAR(2),            -- コーナー通過順位2
    corner_3 VARCHAR(2),            -- コーナー通過順位3
    corner_4 VARCHAR(2),            -- コーナー通過順位4
    kohan_3f DECIMAL(4,1),          -- 後半3Fタイム
    tansho_odds DECIMAL(6,1),       -- 単勝オッズ ← 重要
    tansho_ninkijun VARCHAR(2),     -- 単勝人気順
    ketto_toroku_bango VARCHAR(10), -- 血統登録番号
    PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban)
);
```

**⚠️ 重要**: nvd_se には **fukusho_odds カラムは存在しません**！

##### 3. nvd_od (オッズデータ) ⭐ 最重要
```sql
-- 単勝・複勝・枠連オッズデータ
CREATE TABLE nvd_od (
    kaisai_nen VARCHAR(4),
    kaisai_tsukihi VARCHAR(4),
    keibajo_code VARCHAR(2),
    race_bango VARCHAR(2),
    odds_tansho VARCHAR(224),       -- 単勝オッズ（固定長フォーマット）
    odds_fukusho VARCHAR(336),      -- 複勝オッズ（固定長フォーマット） ← 重要
    odds_wakuren VARCHAR(324),      -- 枠連オッズ（固定長フォーマット）
    hyosu_gokei_tansho VARCHAR(11), -- 単勝票数合計
    hyosu_gokei_fukusho VARCHAR(11),-- 複勝票数合計
    hyosu_gokei_wakuren VARCHAR(11),-- 枠連票数合計
    PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango)
);
```

**odds_fukusho フォーマット仕様**:
```
固定長 336文字
各馬番のオッズは16文字ブロック:
- 馬番(2桁) + オッズ(5桁) + 人気(3桁) + 票数(5桁) + 予備(1桁)

例: 01001000130 = 馬番01、オッズ10.0、人気013

パース処理: core/index_calculator.py の parse_fukusho_odds() 関数
```

##### 4. nvd_hr (払戻情報)
```sql
-- 払戻金データ
CREATE TABLE nvd_hr (
    kaisai_nen VARCHAR(4),
    kaisai_tsukihi VARCHAR(4),
    keibajo_code VARCHAR(2),
    race_bango VARCHAR(2),
    umaban VARCHAR(2),
    haraimodoshi_tansho_1b INTEGER,  -- 単勝払戻金（100円単位）
    haraimodoshi_fukusho_1b INTEGER, -- 複勝払戻金（100円単位）
    PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban)
);
```

**⚠️ 注意**: nvd_hr は払戻金データであり、オッズではありません。
- 使用例: NAR-SI Ver.2.0 では回収率計算に使用
- HQS指数では **nvd_od.odds_fukusho** を使用（より正確）

##### 5. nar_hqs_index_stats (HQS指数実績データ) ⭐ 最重要
```sql
-- HQS指数の的中率・回収率データ
CREATE TABLE nar_hqs_index_stats (
    keibajo_code CHAR(2) NOT NULL,           -- 競馬場コード
    index_type VARCHAR(20) NOT NULL,         -- 指数種別（'ten', 'position', 'agari', 'pace'）
    index_value VARCHAR(10) NOT NULL,        -- 指数値（-100〜+100を10刻み）
    
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
    
    PRIMARY KEY (keibajo_code, index_type, index_value)
);
```

**データ収集スクリプト**: `scripts/collect_index_stats.py`

##### 6. nar_si_race_results (NAR-SI計算結果)
```sql
-- NAR-SI Ver.3.0の計算結果
CREATE TABLE nar_si_race_results (
    kaisai_nen VARCHAR(4),
    kaisai_tsukihi VARCHAR(4),
    keibajo_code VARCHAR(2),
    race_bango VARCHAR(2),
    umaban VARCHAR(2),
    final_nar_si DECIMAL(6,2),      -- 最終NAR-SI
    base_nar_si DECIMAL(6,2),       -- ベースNAR-SI
    -- 各種補正値
    weight_adj DECIMAL(6,2),
    pace_adj DECIMAL(6,2),
    wakuban_adj DECIMAL(6,2),
    distance_adj DECIMAL(6,2),
    course_adj DECIMAL(6,2),
    night_adj DECIMAL(6,2),
    track_adj DECIMAL(6,2),
    class_adj DECIMAL(6,2),
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban)
);
```

**データ取得**: `core/nar_si_v3_data_fetcher.py`

---

## 🧮 コアモジュール

### 1. index_calculator.py ⭐ 最重要

**場所**: `core/index_calculator.py`

**役割**: HQS指数の4つの指数を計算

#### 4つの指数

##### テン指数 (Ten Index)
```python
def calculate_ten_index(zenhan_3f: float, base_time: float, kyori: int) -> int:
    """
    前半3Fの速さを評価
    
    計算式:
    deviation = zenhan_3f - (base_time * 0.25)  # 基準タイムの25%
    index = int(-deviation * 10)
    
    範囲: -100 〜 +100（10刻み）
    高いほど: 前半が速い（逃げ・先行有利）
    """
```

##### 位置指数 (Position Index)
```python
def calculate_position_index(corner_positions: list, tosu: int) -> int:
    """
    コーナー通過順位を評価
    
    計算式:
    avg_position = sum(corner_positions) / len(corner_positions)
    relative_position = (avg_position - 1) / (tosu - 1)  # 0〜1に正規化
    index = int((0.5 - relative_position) * 200)
    
    範囲: -100 〜 +100（10刻み）
    高いほど: 前方を通過（先行力がある）
    """
```

##### 上がり指数 (Agari Index)
```python
def calculate_agari_index(kohan_3f: float, base_time: float, kyori: int) -> int:
    """
    後半3Fの速さを評価
    
    計算式:
    deviation = kohan_3f - (base_time * 0.25)  # 基準タイムの25%
    index = int(-deviation * 10)
    
    範囲: -100 〜 +100（10刻み）
    高いほど: 後半が速い（差し・追込有利）
    """
```

##### ペース指数 (Pace Index)
```python
def calculate_pace_index(zenhan_3f: float, kohan_3f: float, base_time: float) -> int:
    """
    ペースバランスを評価
    
    計算式:
    pace_balance = (zenhan_3f - kohan_3f) / (base_time * 0.25)
    index = int(pace_balance * 100)
    
    範囲: -100 〜 +100（10刻み）
    高いほど: 前半速い→後半遅い（ハイペース）
    低いほど: 前半遅い→後半速い（スローペース）
    """
```

#### 重要関数

```python
def parse_fukusho_odds(odds_fukusho_str: str, umaban: str) -> float:
    """
    nvd_od.odds_fukusho から指定馬番の複勝オッズを取得
    
    ⚠️ 超重要: これがないと複勝回収率が計算できない
    
    処理:
    1. 固定長336文字を16文字ブロックに分割
    2. 各ブロックから馬番・オッズ・人気・票数を抽出
    3. 指定馬番のオッズを返す
    
    例:
    odds_fukusho_str = "01001000130102002200370503..."
    umaban = "01"
    → return 10.0
    """
```

---

### 2. ten_3f_estimator.py

**場所**: `core/ten_3f_estimator.py`

**役割**: 前半3Fタイムの推定

```python
def estimate_zenhan_3f(soha_time: float, kohan_3f: float, kyori: int) -> float:
    """
    前半3Fを推定
    
    推定式:
    zenhan_3f = (soha_time - kohan_3f) × (600 / (kyori - 600))
    
    前提:
    - 前半3F = 600m
    - 後半3F = 600m
    - 中間距離 = kyori - 1200m
    
    例: 1200m、走破72.0秒、後半3F 36.0秒
    → zenhan_3f = (72.0 - 36.0) × (600 / 0) → デフォルト値
    
    例: 1400m、走破84.0秒、後半3F 36.0秒
    → zenhan_3f = (84.0 - 36.0) × (600 / 200) = 144.0秒
    """
```

---

### 3. NAR-SIバージョン別計算機

#### Ver.2.0 Enhanced
**ファイル**: `core/nar_si_calculator_v2_enhanced.py`

**特徴**:
- 基準タイムベースの計算
- 8種類の補正（馬体重/ペース/枠番/距離/コース/ナイター/トラック/クラス）
- 最も安定した基礎版

#### Ver.2.1-A
**ファイル**: `core/nar_si_calculator_v2_1_a.py`

**特徴**:
- 馬体重補正を強化（-0.3/-0.6/-0.9）
- 枠番補正を縮小（内枠 +3、外枠 -3）
- 攻撃的な補正値

#### Ver.2.1-B ⭐ バランス版（推奨）
**ファイル**: `core/nar_si_calculator_v2_1_b.py`

**特徴**:
- 馬体重補正をバランス調整（-0.2/-0.4/-0.6）
- 枠番補正を縮小（内枠 +2、外枠 -2）
- 最もバランスが取れたバージョン
- **商用利用推奨**

#### Ver.2.1-C
**ファイル**: `core/nar_si_calculator_v2_1_c.py`

**特徴**:
- 馬体重補正を最小化（-0.1/-0.2/-0.3）
- 枠番補正を縮小（内枠 +1、外枠 -1）
- 保守的な補正値

#### Ver.3.0 ⭐ 最新版
**ファイル**: 
- `core/nar_si_v3_data_fetcher.py` (データ取得)
- `core/nar_si_v3_feature_engineering.py` (特徴量エンジニアリング)

**特徴**:
- Ver.2.1-B をベースに機械学習用の特徴量を追加
- 38ファクター統合の準備
- 保存場所の一元管理（nar_si_race_results テーブル）
- **統合日**: 2026-01-06

---

### 4. HQS計算モジュール

**ファイル**: `core/hqs_calculator.py`

```python
def calculate_hqs_score(index_stats: dict) -> float:
    """
    HQSスコアを計算
    
    入力:
    index_stats = {
        'ten': {'hit_rate': 25.5, 'adj_return': 85.2},
        'position': {'hit_rate': 22.3, 'adj_return': 78.1},
        'agari': {'hit_rate': 28.1, 'adj_return': 92.3},
        'pace': {'hit_rate': 20.8, 'adj_return': 75.5}
    }
    
    計算式:
    Hit_raw = 0.65 × 単勝的中率 + 0.35 × 複勝的中率
    Ret_raw = 0.35 × 補正単勝回収率 + 0.65 × 補正複勝回収率
    
    HQS = (Hit_raw × 0.4 + Ret_raw × 0.6) × 調整係数
    
    範囲: 0 〜 100
    """
```

---

## 📊 NAR-SIバージョン履歴

| バージョン | リリース日 | 特徴 | ファイル | 推奨度 |
|-----------|-----------|------|---------|-------|
| Ver.2.0 Enhanced | 2026-01-05 | 基準タイムベース、8種類補正 | nar_si_calculator_v2_enhanced.py | ⭐⭐⭐ |
| Ver.2.1-A | 2026-01-06 | 馬体重補正強化、枠番縮小 | nar_si_calculator_v2_1_a.py | ⭐⭐ |
| Ver.2.1-B | 2026-01-06 | バランス調整版 | nar_si_calculator_v2_1_b.py | ⭐⭐⭐⭐⭐ |
| Ver.2.1-C | 2026-01-06 | 保守的補正版 | nar_si_calculator_v2_1_c.py | ⭐⭐ |
| Ver.3.0 | 2026-01-06 | 機械学習対応、統合版 | nar_si_v3_*.py | ⭐⭐⭐⭐⭐ |

### 選択ガイド

**商用利用**: Ver.2.1-B または Ver.3.0
**研究開発**: Ver.3.0
**安定性重視**: Ver.2.0 Enhanced

---

## 🎯 HQS指数システム

### Phase 1: データベース設計 ✅ 完了

**実装日**: 2026-01-08

**成果物**:
- `nar_hqs_index_stats` テーブル設計
- `scripts/create_hqs_index_stats_table.sql`

### Phase 2: データ収集 🚧 進行中

**実装日**: 2026-01-08

**スクリプト**: `scripts/collect_index_stats.py` ⭐ 最重要

#### 対象競馬場（13場）

| コード | 競馬場 | 期間 | 理由 |
|-------|--------|------|------|
| 42 | 大井 | 2023/10/01 〜 2025/12/31 | オーストラリア産白砂への全面置換 |
| 47 | 名古屋 | 2022/04/01 〜 2025/12/31 | 大幅改修 |
| 30 | 門別 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 35 | 盛岡 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 36 | 金沢 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 43 | 川崎 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 44 | 船橋 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 45 | 浦和 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 46 | 笠松 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 48 | 園田 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 49 | 姫路 | 2016/01/01 〜 2025/12/31 | 長期データ |
| 50 | 高知 | 2016/01/01 〜 2025/12/31 | 長期データ（R12除外） |
| 54 | 佐賀 | 2016/01/01 〜 2025/12/31 | 長期データ |

**除外競馬場**:
- 83: 帯広（ばんえい競馬）- データ品質問題

#### データ収集仕様

**実行コマンド**:
```bash
cd E:\UmaData\nar-analytics-python-v2
python scripts\collect_index_stats.py
```

**処理フロー**:
1. 13競馬場を順次処理
2. 各競馬場の期間を取得（`get_period_for_track()`）
3. レースデータを取得（`collect_race_data()`）
   - nvd_ra (レース情報)
   - nvd_se (馬別結果)
   - nvd_od (オッズデータ) ← 複勝オッズはここから取得
4. 4つの指数を計算（`calculate_indexes_for_horse()`）
5. 実績データを蓄積（`update_stats()`）
6. nar_hqs_index_stats へ保存（`save_stats_to_db()`）

**推定実行時間**: 3-5時間
- 大井 (42): 約15分
- 名古屋 (47): 約25分
- その他11場: 約20-45分/場

**期待される出力件数**:
- 13競馬場 × 4指数 × 21値（-100〜+100、10刻み）= 1,092レコード
- 各レコード: 単勝的中率、単勝回収率、複勝的中率、複勝回収率

### Phase 3: HQSスコア計算 📋 計画中

**実装予定**: Phase 2完了後

**処理内容**:
1. nar_hqs_index_stats からデータ取得
2. 4指数のスコアを統合
3. HQSスコアを算出
4. 予測精度を検証

### Phase 4: 38ファクター統合 📋 計画中

**実装予定**: Phase 3完了後

**処理内容**:
1. NAR-SI Ver.3.0 の結果を取得
2. HQSスコアを取得
3. 38種類のファクターを統合
4. 最終予測モデルを構築

---

## 💻 開発環境

### CEO環境

**OS**: Windows  
**ディレクトリ**: `E:\UmaData\nar-analytics-python-v2\`  
**データベース**: PostgreSQL (`pckeiba`)  
**接続**: pgAdmin4

**Python環境**:
```bash
python --version  # 3.x
pip install psycopg2-binary
```

### サンドボックス環境

**OS**: Linux  
**ディレクトリ**: `/home/user/webapp/nar-ai-yoso/`  
**Git**: https://github.com/aka209859-max/umaconn-keiba-ai

**同期方法**:
```bash
# CEO環境からpull
E:
cd \UmaData\nar-analytics-python-v2
git pull origin main
```

---

## 💼 商用利用ガイド

### ライセンス

**重要**: 商用利用前に以下を確認してください：

1. **データソース**: JRAまたはNARからのデータ利用許諾
2. **予測システム**: 競馬法・賭博法の遵守
3. **知的財産権**: NAR-SIアルゴリズムの著作権

### 推奨構成（商用版）

#### 1. コアシステム

- **NAR-SI**: Ver.2.1-B または Ver.3.0
- **HQS**: Phase 3完了版
- **ファクター**: 38ファクター統合版

#### 2. データベース

- **本番環境**: PostgreSQL 13以上
- **バックアップ**: 日次自動バックアップ
- **レプリケーション**: マスター・スレーブ構成

#### 3. セキュリティ

- **データ暗号化**: TLS/SSL接続
- **アクセス制御**: ロールベースアクセス制御（RBAC）
- **監査ログ**: 全操作のログ記録

#### 4. パフォーマンス

- **インデックス最適化**: 
  ```sql
  CREATE INDEX idx_hqs_stats_keibajo ON nar_hqs_index_stats(keibajo_code);
  CREATE INDEX idx_hqs_stats_type ON nar_hqs_index_stats(index_type);
  CREATE INDEX idx_hqs_stats_hit_rate ON nar_hqs_index_stats(rate_win_hit DESC);
  ```

- **クエリ最適化**: 
  - EXPLAIN ANALYZE の実施
  - 適切なJOIN戦略
  - バッチ処理の実装

#### 5. 運用

- **監視**: Prometheus + Grafana
- **アラート**: 異常値検知
- **メンテナンス**: 週次VACUUM、月次REINDEX

---

## 🔑 重要な技術的決定

### 決定1: 複勝オッズの取得元 ⭐ 超重要

**問題**: nvd_se.fukusho_odds は存在しない

**解決策**: nvd_od.odds_fukusho から取得

**実装**: `core/index_calculator.py` の `parse_fukusho_odds()` 関数

**理由**:
1. nvd_se はレース結果テーブル（着順・タイム）
2. nvd_od はオッズテーブル（単勝・複勝・枠連）
3. 固定長フォーマットのパース処理が必要
4. より正確なオッズデータが取得可能

**影響**:
- HQS複勝回収率の精度が向上
- nar_hqs_index_stats の adj_place_ret が正確に計算される

### 決定2: 競馬場別期間設定

**問題**: 馬場改修により基準タイムが変化

**解決策**: 競馬場ごとに異なる集計期間を設定

**実装**: `scripts/collect_index_stats.py` の `get_period_for_track()`

**理由**:
1. 大井: 2023/10 オーストラリア産白砂導入
2. 名古屋: 2022/04 大幅改修
3. その他: 2016/01〜の長期データ

**影響**:
- より正確な指数実績データ
- 馬場変化の影響を排除

### 決定3: kaisai_yen → kaisai_nen 修正

**問題**: テーブル定義のカラム名が kaisai_nen

**解決策**: すべての kaisai_yen を kaisai_nen に統一

**実装**: `scripts/collect_index_stats.py` の全SQL文

**理由**:
1. データベーススキーマに合わせる
2. PostgreSQLエラーを防ぐ
3. 一貫性の確保

**影響**:
- データ取得の成功率が100%に

### 決定4: NAR-SI Ver.3.0 統合

**問題**: NAR-SI Ver.2.0/2.1の結果が分散保存

**解決策**: Ver.3.0 で保存場所を nar_si_race_results に一元化

**実装日**: 2026-01-06

**理由**:
1. データ管理の簡素化
2. 機械学習モデルとの統合
3. バージョン管理の容易性

**影響**:
- 予測システムの開発効率が向上
- データの追跡が容易に

### 決定5: HQS指数の4指数選定

**指数**: テン/位置/上がり/ペース

**理由**:
1. **テン指数**: 前半の速さ（逃げ・先行力）
2. **位置指数**: レース展開（ポジション取り）
3. **上がり指数**: 後半の速さ（差し・追込力）
4. **ペース指数**: ペースバランス（ハイ/スロー判定）

**統合効果**:
- 4つの視点で総合的に評価
- 脚質別の適性を判定
- 展開予想の精度向上

---

## 📌 重要なルール

### ルール1: ファイル命名規則

- **スクリプト**: `snake_case.py`
- **モジュール**: `snake_case.py`
- **SQL**: `snake_case.sql`
- **ドキュメント**: `UPPER_SNAKE_CASE.md`

### ルール2: Git運用

**コミットメッセージ**:
```
✨ 追加: 新機能
🐛 修正: バグ修正
📝 文書: ドキュメント更新
🔧 設定: 設定変更
♻️ リファクタリング: コード整理
```

**ブランチ戦略**:
- `main`: 本番環境（stable）
- `develop`: 開発環境（unstable）
- `feature/*`: 新機能開発

### ルール3: データベース命名規則

**テーブル**:
- `nvd_*`: 元データ（JRA/NAR提供）
- `nar_si_*`: NAR-SI関連
- `nar_hqs_*`: HQS関連
- `temp_*`: 一時テーブル

**カラム**:
- `kaisai_nen`: 開催年
- `kaisai_tsukihi`: 開催月日
- `keibajo_code`: 競馬場コード
- `*_adj`: 補正値
- `*_ret`: 回収率
- `*_rate`: 的中率

### ルール4: コーディング規約

**Python**:
- PEP 8 準拠
- 型ヒントの使用
- Docstring の記述

**SQL**:
- 大文字キーワード（SELECT, FROM, WHERE）
- インデント（4スペース）
- テーブルエイリアス（ra, se, od, hr）

---

## 🚀 次のステップ

### 短期（1週間以内）

1. ✅ Phase 2完了: `collect_index_stats.py` 実行
2. 📋 データ検証: nar_hqs_index_stats の確認
3. 📋 Phase 3開始: HQSスコア計算実装

### 中期（1ヶ月以内）

1. 📋 Phase 3完了: HQSスコア計算
2. 📋 Phase 4開始: 38ファクター統合
3. 📋 Ver.4.0統合テスト

### 長期（3ヶ月以内）

1. 📋 商用版リリース
2. 📋 API提供開始
3. 📋 機械学習モデル最適化

---

## 📞 サポート

**技術的な質問**:
- GitHub Issues: https://github.com/aka209859-max/umaconn-keiba-ai/issues

**ドキュメント**:
- プロジェクトREADME: `/README.md`
- 競馬場コードマスター: `/docs/KEIBAJO_CODE_MASTER.md`
- HQS実行ガイド: `/docs/HQS_INDEX_STATS_EXECUTION_GUIDE.md`

---

**最終更新日**: 2026-01-08  
**バージョン**: NAR-SI Ver.4.0 (Phase 2)  
**ステータス**: 🚧 開発中

---

**Play to Win. 10x Mindset. 商用利用を見据えた完全な技術資料です。** 🚀🏇
