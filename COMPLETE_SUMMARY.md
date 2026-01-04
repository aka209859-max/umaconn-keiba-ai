# NAR AI予想システム 完全サマリ

**最終更新:** 2025年01月04日  
**CEO:** Enable  
**プロジェクト:** NAR（地方競馬）AI予想システム Phase 1

---

## 🎯 最終ゴール（Enable憲法: Play to Win）

CEOのPCで以下のコマンドを実行して、**明日のレース予想TXTファイルが自動生成される**：

```bash
cd E:\UmaData\nar-analytics-python
python main.py --date 2025-01-05
```

**出力イメージ（競馬場ごと1ファイル）:**
```
E:\UmaData\nar-analytics-python\output\20250105\
├── 20250105_大井_予想.txt   (全12レース分を1ファイルに)
├── 20250105_川崎_予想.txt   (全11レース分を1ファイルに)
└── 20250105_浦和_予想.txt   (全10レース分を1ファイルに)
```

**重要:** レースごとではなく、**競馬場ごとに1ファイル**を出力

---

## 📊 現在の状況（2025/01/04）

### ✅ 完了項目

#### 1. データベース接続確認 ✅ 100%
- **Host:** localhost
- **Port:** 5432
- **User:** postgres
- **Password:** keiba2025
- **Database:** pckeiba
- **データ件数:** 1,514,202件（2016年以降）
- **テーブル:** nvd_se(70列), nvd_ra(62列)

#### 2. 重要な列名確定 ✅ 100%

**以下の3つの列名は絶対に忘れないこと:**

| 項目 | 列名 | 備考 |
|------|------|------|
| 馬場状態 | `babajotai_code_dirt` | ダート馬場状態（地方競馬） |
| トラック | `track_code` | 回り（左/右） |
| 人気順 | `tansho_ninkijun` | 単勝人気順（前走データ取得用） |

#### 3. AAS計算式の確定（CEO承認済み）✅ 100%

**🔴 絶対に忘れてはいけない重要ルール:**

1. ✅ **15% = 15** として扱う（0.15ではない）
2. ✅ **母集団標準偏差** を使用（STDEV.P, ddof=0）
3. ✅ **baseCalc = 0.55 × ZH + 0.45 × ZR**
4. ✅ **最終AAS得点 = 31ファクター全ての合計**

**計算フロー:**

```python
# Step 1: 基礎値計算（15% = 15として計算）
Hit_raw = 0.65 × rateWinHit + 0.35 × ratePlaceHit
Ret_raw = 0.35 × adjWinRet + 0.65 × adjPlaceRet
N_min = min(cntWin, cntPlace)

# Step 2: グループ統計（母集団標準偏差 STDEV.P）
μH = mean(Hit_raw_values)
σH = std(Hit_raw_values, ddof=0)  # STDEV.P
μR = mean(Ret_raw_values)
σR = std(Ret_raw_values, ddof=0)  # STDEV.P

# Step 3: Zスコア化
ZH = (Hit_raw - μH) / σH
ZR = (Ret_raw - μR) / σR

# Step 4: 信頼度収縮
Shr = sqrt(N_min / (N_min + 400))

# Step 5: AAS得点計算
baseCalc = 0.55 × ZH + 0.45 × ZR
AAS = 12 × tanh(baseCalc) × Shr

# Step 6: 最終AAS得点（31ファクターの合計）
最終AAS得点 = Σ(各ファクターのAAS得点 × 競馬場別重み)
```

**実装ファイル:** `core/aas_calculator.py`  
**テスト結果:** 全問正解 ✅（誤差 ±0.1）

#### 4. 補正回収率計算式の確定（CEO承認済み）✅ 100%

**基本式:**
```
補正回収率 = (Σ 補正後払戻金 / Σ 補正後ベット額) × 100
```

**重要パラメータ:**
- **目標払戻額:** 10,000円（固定）
- **オッズ補正係数:** 単勝123段階、複勝108段階
- **期間別重み:** 2016=1, 2017=2, ..., 2025=10

**完全版の式:**
```
補正回収率 = (ΣΣ 実配当 × 補正係数 × 的中フラグ × 重み) / 
             (ΣΣ ベット額 × 重み) × 100
```

**実装ファイル:** 
- `config/odds_correction.py` - オッズ補正係数マスタ
- `core/factor_stats_calculator.py` - 補正回収率計算ロジック

#### 5. 31ファクターの定義と抽出ロジック ✅ 100%

**単独ファクター（16個）:**

| ID | ファクター名 | 列名 | 取得方法 |
|----|------------|------|---------|
| F01 | 騎手 | kishu_code | 直接取得 |
| F02 | 調教師 | chokyoshi_code | 直接取得 |
| F03 | 距離適性 | kyori | 直接取得 |
| F04 | 馬場状態 | babajotai_code_dirt | 直接取得 |
| F05 | 回り | track_code | 直接取得 |
| F06 | 条件 | kyoso_joken_code | 直接取得 |
| F07 | 脚質 | corner_1,2,3 | 計算 |
| F08 | 枠番 | wakuban | 直接取得 |
| F09 | 前走着順 | kakutei_chakujun | 前走データ検索 |
| F10 | 前走人気 | tansho_ninkijun | 前走データ検索 |
| F11 | 前走距離 | kyori | 前走データ検索 |
| F12 | 前走馬場 | babajotai_code_dirt | 前走データ検索 |
| F13 | 休養週数 | - | 計算 |
| F14 | 馬体重 | bataiju | 直接取得 |
| F15 | 馬体重増減 | zogen_sa | 直接取得 |
| F16 | 性別 | seibetsu_code | 直接取得 |

**組み合わせファクター（15個）:**

| ID | ファクター名 | 組み合わせ |
|----|------------|-----------|
| C01 | 騎手×距離 | F01 + F03 |
| C02 | 騎手×馬場状態 | F01 + F04 |
| C03 | 騎手×回り | F01 + F05 |
| C04 | 騎手×条件 | F01 + F06 |
| C05 | 調教師×距離 | F02 + F03 |
| C06 | 調教師×馬場状態 | F02 + F04 |
| C07 | 距離×馬場状態 | F03 + F04 |
| C08 | 距離×回り | F03 + F05 |
| C09 | 脚質×距離 | F07 + F03 |
| C10 | 脚質×馬場状態 | F07 + F04 |
| C11 | 枠番×距離 | F08 + F03 |
| C12 | 前走着順×休養週数 | F09 + F13 |
| C13 | 前走人気×前走着順 | F10 + F09 |
| C14 | 馬体重増減×休養週数 | F15 + F13 |
| C15 | 性別×距離 | F16 + F03 |

**脚質の計算方法:**
```python
def calculate_kyakushitsu(corner_positions):
    avg_position = sum(corner_positions) / len(corner_positions)
    
    if avg_position <= 2.0:
        return '逃げ'
    elif avg_position <= 4.0:
        return '先行'
    elif avg_position <= 8.0:
        return '差し'
    else:
        return '追込'
```

**前走データの取得方法:**
```sql
SELECT 
    se.kakutei_chakujun,
    se.tansho_ninkijun,  -- ★ 重要: ninkijunではなくtansho_ninkijun
    ra.kyori,
    ra.babajotai_code_dirt,
    se.kaisai_nen || se.kaisai_tsukihi as race_date
FROM nvd_se se
JOIN nvd_ra ra ON (...)
WHERE se.ketto_toroku_bango = %s
AND se.kaisai_nen || se.kaisai_tsukihi < %s
ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
LIMIT 1
```

**休養週数の計算:**
```python
def calculate_kyuyo_weeks(prev_race_date, current_race_date):
    prev_date = datetime.strptime(prev_race_date, '%Y%m%d')
    curr_date = datetime.strptime(current_race_date, '%Y%m%d')
    days_diff = (curr_date - prev_date).days
    weeks = days_diff // 7
    return max(0, weeks)
```

**実装ファイル:** 
- `config/factor_definitions.py` - ファクター定義
- `core/factor_extractor.py` - ファクター抽出ロジック

**テスト結果:** ✅ 31ファクター抽出成功（test_factor_extraction_final.py）

#### 6. 競馬場別重み係数 ✅ 100%

**14競馬場（帯広は除外）:**
- 大井（RA）、川崎（KC）、船橋（HF）、浦和（UW）
- 盛岡（MI）、水沢（MZ）、門別（MM）
- 旭川（AS）、札幌地方（SA）、函館地方（HA）
- 金沢（KZ）、笠松（KS）、名古屋（NA）
- ~~帯広（OB）~~ ← **ばんえいは除外**

**重み係数:**
- 各競馬場 × 各ファクター = 14 × 31 = 434個の重み係数
- 実装ファイル: `config/factor_weights.py`

#### 7. TXT出力フォーマット（CEO承認済み）✅ 100%

**ファイル名規則:**
```
20250105_大井_予想.txt
20250105_川崎_予想.txt
20250105_浦和_予想.txt
```

**重要:** 競馬場ごとに1ファイル（レースごとではない）

**出力フォーマット（シンプル版）:**
```
================================================================
2025年01月05日 大井競馬場 全レース予想
================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 01R ダート1200m 3歳未勝利
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

順位  馬番  馬名              最終AAS得点  ランク
--------------------------------------------------------
 1     14   ○○○○○○           +28.5      SS
 2     11   △△△△△△           +25.3      S
 3      4   □□□□□□           +22.8      A
 4      2   ××××××××           +18.6      B
 5      9   ◎◎◎◎◎◎           +15.2      B
 6      5   ●●●●●●           +12.8      C
 7      6   ▲▲▲▲▲▲           +10.5      C
 8      3   ■■■■■■           +8.3       C
 9     10   ★★★★★★           +6.1       D
10      7   ☆☆☆☆☆☆           +3.8       D
11     12   ◆◆◆◆◆◆           +1.5       D
12      8   ▼▼▼▼▼▼           -0.8       E

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 02R ダート1600m サラ系3歳
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

**特徴:**
- ✅ シンプル版（主要ファクターは表示しない）
- ✅ ランク: SS/S/A/B/C/D/E/F
- ✅ 最終AAS得点のみ表示

---

## 🔧 実装済みファイル一覧

### サンドボックス環境: /home/user/webapp/nar-ai-yoso/

```
nar-ai-yoso/
├── config/
│   ├── db_config.py              ✅ DB接続設定
│   ├── odds_correction.py        ✅ オッズ補正係数（単勝123段階、複勝108段階）
│   ├── factor_weights.py         ✅ 競馬場別×ファクター別重み係数
│   ├── course_master.py          ✅ 競馬場マスタ（コース特性）
│   └── factor_definitions.py     ✅ 31ファクター定義
├── core/
│   ├── factor_extractor.py       ✅ ファクター抽出ロジック（31ファクター）
│   ├── factor_stats_calculator.py ✅ 補正回収率計算
│   ├── aas_calculator.py          ✅ AAS得点計算（修正済み）
│   ├── data_fetcher.py            ✅ データベースからのデータ取得
│   └── prediction_generator.py    ✅ 予想生成・TXT出力（実装済み）
├── test_connection.py            ✅ DB接続テスト
├── test_check_columns.py         ✅ テーブル列名確認
├── test_baba_columns.py          ✅ 馬場状態列名確認
├── test_aas_calculation.py       ✅ AAS計算テスト（16頭）
├── test_factor_extraction.py     ✅ ファクター抽出テスト
├── test_corrected_return_rate.py ✅ 補正回収率計算テスト（Step 2用）
├── main.py                       ✅ メインスクリプト（実装済み）
├── requirements.txt              ✅ 依存パッケージ
├── .gitignore                    ✅ Git管理
├── PROJECT_REPORT.md             ✅ プロジェクトレポート
├── README.md                     ✅ README
└── COMPLETE_SUMMARY.md           ✅ この完全サマリ（NEW!）
```

### ローカル環境: E:\UmaData\nar-analytics-python\

**CEOのPC環境（Windows）:**
- 全ての実装はサンドボックスで完了
- CEOのPCには、完成したコードをダウンロードして配置する必要がある
- main.pyの出力先パスは `E:/UmaData/nar-analytics-python/predictions` にハードコード済み

---

## 🚀 完全ロードマップ（残り作業）

### ✅ Step 1: ファクター抽出テスト（完了 100%）

**目的:** データベースから31ファクターを正しく取得  
**所要時間:** 完了

**完了内容:**
- ✅ データベース列名確認完了
- ✅ 31ファクター定義作成完了
- ✅ ファクター抽出ロジック実装完了
- ✅ 馬場状態列名確認完了（`babajotai_code_dirt`）
- ✅ 人気順列名確認完了（`tansho_ninkijun`）
- ✅ トラック列名確認完了（`track_code`）
- ✅ 31ファクター抽出テスト成功

**テスト結果（test_factor_extraction_final.py）:**
```
最新レースデータ:
  レース: 2026/0101 54 11R
  馬名: ノエル
  騎手: 山崎雅由 (20507)
  着順: 12着

単独ファクター（16個）:
  F01 騎手: 山崎雅由 (20507)
  F02 調教師: 田中譲二 (20366)
  F03 距離: 1300m
  F04 馬場状態: 1（良）
  F05 トラック: 24
  F06 条件: C3-17
  F07 脚質: 差し  ← ★ 計算成功
  F08 枠番: 5
  F09 前走着順: 4着  ← ★ 前走データ取得成功
  F10 前走人気: 4番人気
  F11 前走距離: 1400m
  F12 前走馬場: 3
  F13 休養週数: 1週  ← ★ 計算成功
  F14 馬体重: 430kg
  F15 馬体重増減: +2kg
  F16 性別: 1

組み合わせファクター（15個）: 全て正常生成 ✅

✅ 全31ファクター抽出成功！
```

---

### 🔄 Step 2: 補正回収率計算の実データテスト（進行中 50%）

**目的:** 実データでCEO式の補正回収率が正しく計算できるか確認  
**所要時間:** 2-3時間

**作業内容:**
1. ✅ テストスクリプト作成（test_corrected_return_rate.py）
2. ⚠️ 実行と結果検証（CEOのPCで実行待ち）
3. ⚠️ サンプルファクターで計算結果を検証

**実装ファイル:**
- `test_corrected_return_rate.py` - テストスクリプト（作成済み）
- `core/factor_stats_calculator.py` - 補正回収率計算ロジック（実装済み）

**次のアクション:**
```bash
# CEOのPCで実行:
cd E:\UmaData\nar-analytics-python
python test_corrected_return_rate.py
```

**期待される出力:**
```
================================================================================
📊 Step 2: 補正回収率計算テスト
================================================================================

【Step 1】サンプル騎手を選択
--------------------------------------------------------------------------------
  サンプル騎手: 的場文男 (01234)
  レース数: 5,432件

【Step 2】過去データ集計（2016-2025年）
--------------------------------------------------------------------------------
  取得データ数: 5,432件

【Step 3】補正回収率を計算
--------------------------------------------------------------------------------

【単勝】
  件数:            5,432件
  的中数:          543件
  的中率:          10.00%
  補正回収率:      95.23%

【複勝】
  件数:            5,432件
  的中数:          1,629件
  的中率:          30.00%
  補正回収率:      98.45%

================================================================================
✅ Step 2完了: 補正回収率計算成功！
================================================================================
```

---

### ⚠️ Step 3: AAS得点計算の実データテスト（未着手 0%）

**目的:** 実際のレースで31ファクター全てのAAS得点を計算  
**所要時間:** 1-2時間

**作業内容:**
1. 1レース分の全馬データで検証
2. 31ファクター × 全馬のAAS得点算出
3. 最終AAS得点（合計）のランキング確認
4. 競馬場別重みの適用確認

**実装ファイル:**
- `test_aas_full_race.py` の作成

**テストシナリオ:**
```python
# 1レース（例: 大井01R）の全馬でテスト
# 期待される出力:
1位: 14番 ○○○○○○ 最終AAS: +28.5点
  - 騎手AAS: +4.2点
  - 調教師AAS: +3.1点
  - 距離適性AAS: +3.8点
  - ... (全31ファクター)
  
2位: 11番 △△△△△△ 最終AAS: +25.3点
  ...
```

---

### ⚠️ Step 4: 予想生成パイプラインの統合テスト（未着手 0%）

**目的:** 個別機能を統合して、1レース分の予想を生成  
**所要時間:** 2-3時間

**作業内容:**
1. パイプライン統合
   ```python
   race_data = fetch_race_data(date, keibajo, race_bango)
   for horse in race_data:
       factors = extract_31_factors(horse)
       total_aas = 0
       for factor in factors:
           stats = calculate_corrected_return_rate(factor)
           aas = calculate_aas(stats)
           weight = get_factor_weight(keibajo, factor_name)
           total_aas += aas * weight
       horse['final_aas'] = total_aas
   output_txt(race_data)
   ```
2. エラーハンドリング実装
3. 1レースでの動作確認

**実装ファイル:**
- `core/prediction_generator.py` - 既に実装済み ✅
- 統合テストスクリプトの作成

---

### ⚠️ Step 5: 競馬場ごとの一括出力対応（未着手 0%）

**目的:** 1つの競馬場の全レースを1つのTXTファイルにまとめる  
**所要時間:** 1-2時間

**作業内容:**
1. 競馬場別グループ化
2. 競馬場ごとのTXT生成
3. ファイル名規則: `20250105_大井_予想.txt`
4. 全競馬場での動作確認

**実装ファイル:**
- `core/prediction_generator.py` の修正（競馬場別出力対応）

---

### ⚠️ Step 6: TXT出力フォーマットの最終調整（未着手 0%）

**目的:** CEO要求の出力フォーマットを完全実装  
**所要時間:** 1時間

**作業内容:**
1. TXT出力フォーマットの確認
2. 文字揃え、区切り線
3. 日本語文字コード対応（UTF-8 BOM）
4. CEO承認

---

### ⚠️ Step 7: 本番運用準備と最終テスト（未着手 0%）

**目的:** 明日から実運用できる状態にする  
**所要時間:** 1-2時間

**作業内容:**
1. コマンドライン引数の実装（main.pyは実装済み ✅）
2. バッチファイル作成（Windows用）
   ```batch
   @echo off
   cd E:\UmaData\nar-analytics-python
   python main.py
   pause
   ```
3. README.md作成
4. 最終テスト
5. CEOのPCへのコード配置

**実装ファイル:**
- `main.py` - 既に実装済み ✅
- `run_prediction.bat` - 作成予定
- `README.md` - 更新予定

---

## ⏱️ 合計残り作業時間: 8-13時間

**内訳:**
- Step 2: 1-2時間（50%完了、残り1時間）
- Step 3: 1-2時間
- Step 4: 2-3時間
- Step 5: 1-2時間
- Step 6: 1時間
- Step 7: 1-2時間

---

## 🎯 実行スケジュール案（Enable憲法: Buy Back Time）

### 今夜 (2025/01/04)
- ✅ Step 1完了（31ファクター抽出）
- ⚠️ Step 2: 補正回収率計算テスト - 1-2時間

### 明日朝 (2025/01/05)
- Step 3: AAS得点計算テスト - 1-2時間
- Step 4: パイプライン統合 - 2-3時間

### 明日午後 (2025/01/05)
- Step 5: 競馬場ごと出力対応 - 1-2時間
- Step 6: TXT出力調整 - 1時間
- Step 7: 本番運用準備 - 1-2時間

---

## 🔐 重要な確定事項（絶対に忘れてはいけない）

### 1. AAS計算の重要ルール

✅ **15% = 15** (0.15ではない)
- 的中率15%は、15として計算
- Hit_raw = 0.65 × 15 + 0.35 × 45 = 25.5

✅ **母集団標準偏差** (ddof=0, STDEV.P)
- `np.std(values, ddof=0)`
- 標本標準偏差ではない

✅ **baseCalc = 0.55 × ZH + 0.45 × ZR**
- 0.55と0.45の比率を厳守
- (ZH + ZR) / 2 ではない

✅ **最終AAS = 31ファクター全ての合計**
- 各ファクターのAAS得点を計算
- 競馬場別重みを適用
- 全て合計して最終AAS得点

### 2. 補正回収率計算の重要ルール

✅ 目標払戻額 = 10,000円（固定）

✅ オッズ補正係数:
- 単勝: 123段階
- 複勝: 108段階
- ファイル: `config/odds_correction.py`

✅ 期間別重み: 2016=1 → 2025=10
- 2016年以前のデータは除外
- 2016-2025の10年分のみ使用

### 3. ファクター抽出の重要ルール

✅ 前走データ: ketto_toroku_bango で検索

✅ 脚質: コーナー通過順位から計算
- 平均≤2.0 → 逃げ
- 平均≤4.0 → 先行
- 平均≤8.0 → 差し
- 平均>8.0 → 追込

✅ 休養週数: 前走日付から計算

✅ 馬場状態: `babajotai_code_dirt` を使用  
✅ トラック: `track_code` を使用  
✅ 人気順: `tansho_ninkijun` を使用

### 4. 出力フォーマットの重要ルール

✅ 競馬場ごとに1ファイル（レースごとではない）

✅ 主要ファクターは表示しない（シンプル版）

✅ 表示項目:
- 順位
- 馬番
- 馬名
- 最終AAS得点
- ランク（SS/S/A/B/C/D/E/F）

---

## 💾 Gitコミット履歴

```
[main 255f4be] Step 1準備: ファクター抽出テスト用スクリプト作成
[main 172d0a5] Step 1: ファクター抽出ロジック実装完了
[main c011bf0] AAS計算式修正: STDEV.P + baseCalc係数修正
[main b8180f1] 修正: 的中率・補正回収率の単位を%値のまま使用
[main ed0aa6a] 補正回収率計算ロジック実装完了
```

---

## 📊 テスト結果サマリ

### ✅ AAS計算テスト（16頭）
- 馬番1: 期待値 +5.5 → 実際 +5.5 (誤差0.02) ✅
- 馬番2: 期待値 +5.8 → 実際 +5.8 (誤差0.04) ✅
- 馬番3: 期待値 +2.4 → 実際 +2.4 (誤差0.01) ✅
- **結論:** 全問正解 ✅

### ✅ ファクター抽出テスト（31ファクター）
- 単独ファクター（16個）: 全て正常取得 ✅
- 組み合わせファクター（15個）: 全て正常生成 ✅
- 脚質計算: 成功 ✅
- 前走データ取得: 成功 ✅
- 休養週数計算: 成功 ✅

---

## 🔍 次のアクション（優先順位順）

### 最優先（今すぐ）

1. **test_corrected_return_rate.py の実行**
   ```bash
   cd E:\UmaData\nar-analytics-python
   python test_corrected_return_rate.py
   ```
   - 補正回収率の実データテスト
   - 結果をレポート

### その後

2. **Step 3: AAS得点計算の実データテスト**
   - 1レース分の全馬でAAS得点を計算
   - 最終AAS得点のランキング確認

3. **Step 4: パイプライン統合テスト**
   - 1レース分の予想を生成
   - エラーハンドリング確認

---

## 📝 Enable憲法（CEO行動指針）

- **10x Mindset:** 10%の改善ではなく、10倍の成長を目指す
- **Be Resourceful:** リソース不足を言い訳にせず、知恵とAIで突破する
- **Play to Win:** 負けないためではなく、勝つためにプレイする
- **Buy Back Time:** 時間を金で買い（AI活用含む）、戦略に投資する

### プロジェクト特性

- **48時間で"勘"を"確信"に変える**
- **スピードと論理的根拠（エビデンス）を両立**
- **プロフェッショナル、クリーン、モダン、信頼性**

---

## 🌐 環境情報

### サンドボックス環境
- **パス:** /home/user/webapp/nar-ai-yoso/
- **用途:** 開発・テスト
- **Python:** Python 3.x
- **データベース:** 接続不可（CEOのローカル環境に接続する必要がある）

### ローカル環境（CEOのPC）
- **パス:** E:\UmaData\nar-analytics-python\
- **OS:** Windows
- **データベース:** PostgreSQL (localhost:5432)
- **用途:** 本番実行

---

**このレポートは、AIアシスタントが忘れないように保存された完全な記録です。**

**CEO、明日のゴールまで一緒に走り抜けましょう！Play to Win！🚀**
