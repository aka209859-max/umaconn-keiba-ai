# NAR AI予想システム Phase 1 完全レポート

**作成日:** 2025年01月04日  
**プロジェクト:** NAR（地方競馬）AI予想システム  
**CEO:** Enable  
**開発者:** Claude (AI Assistant)

---

## 🎯 最終ゴール

CEOのPCで以下のコマンドを実行して、明日のレース予想TXTファイルが自動生成される：

```bash
cd E:\UmaData\nar-analytics-python
python main.py --date 2025-01-05
```

**出力ファイル:**
```
E:\UmaData\nar-analytics-python\output\20250105\
├── 20250105_大井_予想.txt   (全12レース分を1ファイルに)
├── 20250105_川崎_予想.txt
└── 20250105_浦和_予想.txt
```

---

## ✅ 完了済み項目（2025/01/04 23:00時点）

### 1. データベース接続確認 ✅

**接続情報:**
- Host: `localhost`
- Port: `5432`
- User: `postgres`
- Password: `keiba2025`
- Database: `pckeiba`

**確認結果:**
- nvd_se テーブル: 1,514,202件（2016年以降）
- nvd_se: 70列
- nvd_ra: 62列

**重要な列名:**
- **nvd_se:**
  - `ketto_toroku_bango` - 血統登録番号（前走データ検索用）
  - `kishu_code`, `kishumei_ryakusho` - 騎手
  - `chokyoshi_code`, `chokyoshimei_ryakusho` - 調教師
  - `wakuban` - 枠番
  - `corner_1`, `corner_2`, `corner_3` - コーナー通過順位（脚質計算用）
  - `bataiju` - 馬体重
  - `zogen_sa` - 馬体重増減
  - `seibetsu_code` - 性別
  - `ninkijun` - 人気順

- **nvd_ra:**
  - `kyori` - 距離
  - `babajotai_code_shiba` - 芝馬場状態
  - `babajotai_code_dirt` - ダート馬場状態 ✅
  - `mawari_code` - 回り（左/右）
  - `kyoso_joken_code`, `kyoso_joken_meisho` - 条件（クラス）

---

### 2. AAS計算式の確定（CEO承認済み） ✅

#### 🔴 重要ルール

**絶対に忘れてはいけないこと:**
1. **15% = 15** として扱う（0.15ではない）
2. **母集団標準偏差** を使用（STDEV.P, ddof=0）
3. **baseCalc = 0.55 × ZH + 0.45 × ZR**
4. **最終AAS得点 = 31ファクター全ての合計**

#### Step 1: 基礎値計算
```python
Hit_raw = 0.65 × rateWinHit + 0.35 × ratePlaceHit
Ret_raw = 0.35 × adjWinRet + 0.65 × adjPlaceRet
N_min = min(cntWin, cntPlace)
```

**重要:** rateWinHit=15% の場合、15として計算（0.15ではない）

#### Step 2: グループ統計（母集団標準偏差 STDEV.P）
```python
μH = mean(Hit_raw_values)
σH = std(Hit_raw_values, ddof=0)  # STDEV.P（母集団標準偏差）
μR = mean(Ret_raw_values)
σR = std(Ret_raw_values, ddof=0)  # STDEV.P（母集団標準偏差）
```

**重要:** `ddof=0` を使用（標本標準偏差ではない）

#### Step 3: Zスコア化
```python
ZH = (Hit_raw - μH) / σH  # σH=0 のとき 0
ZR = (Ret_raw - μR) / σR  # σR=0 のとき 0
```

#### Step 4: 信頼度収縮
```python
Shr = sqrt(N_min / (N_min + 400))
```

#### Step 5: AAS得点計算
```python
baseCalc = 0.55 × ZH + 0.45 × ZR  # ← 重要: 0.55と0.45の比率
AAS = 12 × tanh(baseCalc) × Shr
```

#### Step 6: 最終AAS得点（31ファクターの合計）
```python
最終AAS得点 = Σ(各ファクターのAAS得点 × 競馬場別重み)
           = 騎手AAS + 調教師AAS + 距離AAS + ... (全31ファクター)
```

**実装ファイル:** `core/aas_calculator.py`

**テスト結果:** 全問正解（誤差 ±0.1）✅

---

### 3. 補正回収率計算式の確定（CEO承認済み） ✅

#### 基本式
```
補正回収率 = (Σ 補正後払戻金 / Σ 補正後ベット額) × 100
```

#### Step 1: 均等払戻時のベット額
```
ベット額 = 目標払戻額 / オッズ
目標払戻額 = 10,000円（固定）
```

#### Step 2: オッズ別補正係数

**単勝補正係数:** 123段階（0.0-999999.9）
- 例: 1.0-1.6 → 0.94
- 例: 100.0-110.0 → 1.19
- 例: 400.0-999999.9 → 2.38

**複勝補正係数:** 108段階（0.0-999999.9）
- 例: 1.0-1.1 → 0.85
- 例: 20.0-21.0 → 1.35
- 例: 70.0-999999.9 → 5.06

**実装ファイル:** `config/odds_correction.py`

#### Step 3: 期間別重み付け（2016-2025）
```python
YEAR_WEIGHTS = {
    '2016': 1, '2017': 2, '2018': 3, '2019': 4, '2020': 5,
    '2021': 6, '2022': 7, '2023': 8, '2024': 9, '2025': 10
}
```

**重要:** 2016年以前のデータがあっても、2016-2025の10年分のみを使用

#### 完全版の式
```
補正回収率 = (ΣΣ 実配当 × 補正係数 × 的中フラグ × 重み) / 
             (ΣΣ ベット額 × 重み) × 100
```

**実装ファイル:** `core/factor_stats_calculator.py`

---

### 4. 31ファクターの定義（CEO承認済み） ✅

#### 単独ファクター（16個）

| ID | ファクター名 | テーブル | 列名 | 取得方法 |
|----|------------|---------|------|---------|
| F01 | 騎手 | nvd_se | kishu_code | 直接取得 |
| F02 | 調教師 | nvd_se | chokyoshi_code | 直接取得 |
| F03 | 距離適性 | nvd_ra | kyori | 直接取得 |
| F04 | 馬場状態 | nvd_ra | babajotai_code_dirt | 直接取得 |
| F05 | 回り | nvd_ra | mawari_code | 直接取得 |
| F06 | 条件 | nvd_ra | kyoso_joken_code | 直接取得 |
| F07 | 脚質 | nvd_se | corner_1,2,3 | 計算（コーナー通過順位から） |
| F08 | 枠番 | nvd_se | wakuban | 直接取得 |
| F09 | 前走着順 | nvd_se | kakutei_chakujun | 前走データ検索 |
| F10 | 前走人気 | nvd_se | ninkijun | 前走データ検索 |
| F11 | 前走距離 | nvd_ra | kyori | 前走データ検索 |
| F12 | 前走馬場 | nvd_ra | babajotai_code_dirt | 前走データ検索 |
| F13 | 休養週数 | - | - | 計算（前走日付から） |
| F14 | 馬体重 | nvd_se | bataiju | 直接取得 |
| F15 | 馬体重増減 | nvd_se | zogen_sa | 直接取得 |
| F16 | 性別 | nvd_se | seibetsu_code | 直接取得 |

#### 組み合わせファクター（15個）

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

**実装ファイル:** 
- `config/factor_definitions.py` - ファクター定義
- `core/factor_extractor.py` - ファクター抽出ロジック

#### 脚質の計算方法（CEO承認済み）

コーナー通過順位から判定：

```python
def calculate_kyakushitsu(corner_positions):
    """
    corner_positions: [corner_1, corner_2, corner_3]
    """
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

#### 前走データの取得方法（CEO承認済み）

同じ馬（ketto_toroku_bango）の過去レースを検索：

```sql
SELECT 
    se.kakutei_chakujun as chakujun,
    se.ninkijun as ninki,
    ra.kyori,
    ra.babajotai_code_dirt as baba,
    se.kaisai_nen || se.kaisai_tsukihi as race_date
FROM nvd_se se
JOIN nvd_ra ra ON (
    se.kaisai_nen = ra.kaisai_nen 
    AND se.kaisai_tsukihi = ra.kaisai_tsukihi
    AND se.keibajo_code = ra.keibajo_code
    AND se.race_bango = ra.race_bango
)
WHERE se.ketto_toroku_bango = %s
AND se.kaisai_nen || se.kaisai_tsukihi < %s
ORDER BY se.kaisai_nen DESC, se.kaisai_tsukihi DESC
LIMIT 1
```

#### 休養週数の計算方法（CEO承認済み）

前走日付から今回レース日までの週数：

```python
def calculate_kyuyo_weeks(prev_race_date, current_race_date):
    prev_date = datetime.strptime(prev_race_date, '%Y%m%d')
    curr_date = datetime.strptime(current_race_date, '%Y%m%d')
    days_diff = (curr_date - prev_date).days
    weeks = days_diff // 7
    return max(0, weeks)
```

---

### 5. 競馬場別重み係数（CEO承認済み） ✅

**14競馬場:**
- 大井（RA）
- 川崎（KC）
- 船橋（HF）
- 浦和（UW）
- 盛岡（MI）
- 水沢（MZ）
- 門別（MM）
- 帯広（OB）← **除外**
- 旭川（AS）
- 札幌地方（SA）
- 函館地方（HA）
- 金沢（KZ）
- 笠松（KS）
- 名古屋（NA）

**重み係数:**
- 各競馬場 × 各ファクター = 14 × 31 = 434個の重み係数
- 実装ファイル: `config/factor_weights.py`

---

### 6. TXT出力フォーマット（CEO承認済み） ✅

#### ファイル名規則
```
20250105_大井_予想.txt
20250105_川崎_予想.txt
20250105_浦和_予想.txt
```

**重要:** 競馬場ごとに1ファイル（レースごとではない）

#### 出力フォーマット

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
13      1   △△△△△△           -2.3       E
14     13   □□□□□□           -4.7       E
15     15   ○○○○○○           -6.5       F
16     16   ××××××××           -8.9       F

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 02R ダート1600m サラ系3歳
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
...
```

**特徴:**
- シンプル版（主要ファクターは表示しない）
- ランク: SS/S/A/B/C/D/E/F
- 最終AAS得点のみ表示

---

## 🔧 実装済みファイル一覧

### config/ (設定ファイル)

```
config/
├── db_config.py              ✅ DB接続設定
├── odds_correction.py        ✅ オッズ補正係数（単勝123段階、複勝108段階）
├── factor_weights.py         ✅ 競馬場別×ファクター別重み係数
├── course_master.py          ✅ 競馬場マスタ（コース特性）
└── factor_definitions.py     ✅ 31ファクター定義
```

### core/ (コアロジック)

```
core/
├── factor_stats_calculator.py  ✅ 補正回収率計算
├── aas_calculator.py            ✅ AAS得点計算（修正済み）
├── factor_extractor.py          ✅ ファクター抽出（NEW!）
└── prediction_generator.py      ⚠️ 未実装
```

### テストスクリプト

```
test_connection.py              ✅ DB接続テスト
test_check_columns.py           ✅ テーブル列名確認
test_baba_columns.py            ✅ 馬場状態列名確認
test_aas_calculation.py         ✅ AAS計算テスト（16頭）
test_factor_extraction.py       ⚠️ 次のテスト
```

### その他

```
main.py                         ⚠️ 未実装
run_prediction.bat              ⚠️ 未実装
requirements.txt                ✅ 依存パッケージ
README.md                       ⚠️ 未作成
.gitignore                      ✅ Git管理
```

---

## 🚀 完全ロードマップ（残り作業）

### ✅ Step 1: ファクター抽出テスト（進行中 80%完了）

**目的:** データベースから31ファクターを正しく取得

**完了項目:**
- ✅ データベース列名確認完了
- ✅ 31ファクター定義作成完了
- ✅ ファクター抽出ロジック実装完了
- ✅ 馬場状態列名確認完了（`babajotai_code_dirt`）

**残り作業:**
- ⚠️ test_factor_extraction.py の実行
- ⚠️ 31ファクター抽出の動作確認
- ⚠️ 欠損データ処理の確認

**所要時間:** 残り30分

---

### ⚠️ Step 2: 補正回収率計算の実データテスト（未着手）

**目的:** 実データでCEO式の補正回収率が正しく計算できるか確認

**作業内容:**
1. 過去データ集計関数の実装（2016-2025年）
2. ファクター別の的中率・回収率を計算
3. サンプルファクターで計算結果を検証

**実装ファイル:**
- `core/factor_stats_calculator.py` の拡張
- `test_corrected_return_rate.py` の作成

**所要時間:** 2-3時間

---

### ⚠️ Step 3: AAS得点計算の実データテスト（未着手）

**目的:** 実際のレースで31ファクター全てのAAS得点を計算

**作業内容:**
1. 1レース分の全馬データで検証
2. 31ファクター × 全馬のAAS得点算出
3. 最終AAS得点（合計）のランキング確認
4. 競馬場別重みの適用確認

**実装ファイル:**
- `test_aas_full_race.py` の作成

**所要時間:** 1-2時間

---

### ⚠️ Step 4: 予想生成パイプラインの統合（未着手）

**目的:** 個別機能を統合して、1レース分の予想を生成

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
- `core/prediction_generator.py` の実装

**所要時間:** 2-3時間

---

### ⚠️ Step 5: 競馬場ごとの一括出力対応（未着手）

**目的:** 1つの競馬場の全レースを1つのTXTファイルにまとめる

**作業内容:**
1. 競馬場別グループ化
2. 競馬場ごとのTXT生成
3. ファイル名規則: `20250105_大井_予想.txt`
4. 全競馬場での動作確認

**実装ファイル:**
- `core/txt_output_generator.py` の実装

**所要時間:** 1-2時間

---

### ⚠️ Step 6: TXT出力フォーマットの最終調整（未着手）

**目的:** CEO要求の出力フォーマットを完全実装

**作業内容:**
1. TXT出力フォーマットの確認
2. 文字揃え、区切り線
3. 日本語文字コード対応（UTF-8 BOM）
4. CEO承認

**所要時間:** 1時間

---

### ⚠️ Step 7: 本番運用準備と最終テスト（未着手）

**目的:** 明日から実運用できる状態にする

**作業内容:**
1. コマンドライン引数の実装
2. バッチファイル作成（Windows用）
3. README.md作成
4. 最終テスト

**実装ファイル:**
- `main.py` の完全実装
- `run_prediction.bat` の作成
- `README.md` の作成

**所要時間:** 1-2時間

---

## ⏱️ 合計残り作業時間: 9-15時間

---

## 🎯 実行スケジュール案

### 今夜 (2025/01/04)
- ✅ Step 1の最終確認（test_factor_extraction.py実行） - 30分
- Step 2: 補正回収率計算テスト - 2-3時間

### 明日朝 (2025/01/05)
- Step 3: AAS得点計算テスト - 1-2時間
- Step 4: パイプライン統合 - 2-3時間

### 明日午後 (2025/01/05)
- Step 5: 競馬場ごと出力対応 - 1-2時間
- Step 6: TXT出力調整 - 1時間
- Step 7: 本番運用準備 - 1-2時間

---

## 📂 プロジェクト構成（最終形態）

```
E:\UmaData\nar-analytics-python\
├── output\                          # 予想結果出力ディレクトリ
│   └── 20250105\
│       ├── 20250105_大井_予想.txt
│       ├── 20250105_川崎_予想.txt
│       └── 20250105_浦和_予想.txt
├── config\                          # 設定ファイル
│   ├── db_config.py              ✅
│   ├── odds_correction.py        ✅
│   ├── factor_weights.py         ✅
│   ├── course_master.py          ✅
│   └── factor_definitions.py     ✅
├── core\                            # コアロジック
│   ├── factor_extractor.py       ✅
│   ├── factor_stats_calculator.py ✅
│   ├── aas_calculator.py          ✅
│   └── prediction_generator.py    ⚠️
├── test_connection.py            ✅
├── test_check_columns.py         ✅
├── test_baba_columns.py          ✅
├── test_aas_calculation.py       ✅
├── test_factor_extraction.py     ⚠️ 次のテスト
├── main.py                       ⚠️
├── run_prediction.bat            ⚠️
├── requirements.txt              ✅
├── README.md                     ⚠️
└── .gitignore                    ✅
```

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
[main 172d0a5] Step 1: ファクター抽出ロジック実装完了
- 31ファクター定義 (config/factor_definitions.py)
- ファクター抽出ロジック (core/factor_extractor.py)
- テストスクリプト作成

[main c011bf0] AAS計算式修正: STDEV.P + baseCalc係数修正
- 母集団標準偏差（ddof=0）使用
- baseCalc = 0.55×ZH + 0.45×ZR
- 全テスト合格

[main b8180f1] 修正: 的中率・補正回収率の単位を%値のまま使用
- 15% = 15 として計算
- /100を削除

[main ed0aa6a] 補正回収率計算ロジック実装完了
- オッズ補正係数マスタ
- 期間別重み付け
- CEO式実装
```

---

## 📊 テスト結果

### AAS計算テスト（16頭）

**テストケース:**
- 馬番1: 期待値 +5.5 → 実際 +5.5 (誤差0.02) ✅
- 馬番2: 期待値 +5.8 → 実際 +5.8 (誤差0.04) ✅
- 馬番3: 期待値 +2.4 → 実際 +2.4 (誤差0.01) ✅

**結論:** 全問正解 ✅

---

## 🔍 次のアクション

### 最優先（今すぐ）

1. **test_factor_extraction.py の実行**
   - 31ファクター抽出の動作確認
   - エラーがないか確認

### その後

2. **Step 2: 補正回収率計算の実データテスト**
   - 実データで補正回収率を計算
   - サンプルファクターで検証

---

## 📝 備考

### Enable憲法（CEO行動指針）

- **10x Mindset:** 10%の改善ではなく、10倍の成長を目指す
- **Be Resourceful:** リソース不足を言い訳にせず、知恵とAIで突破する
- **Play to Win:** 負けないためではなく、勝つためにプレイする
- **Buy Back Time:** 時間を金で買い（AI活用含む）、戦略に投資する

### プロジェクト特性

- **48時間で"勘"を"確信"に変える**
- **スピードと論理的根拠（エビデンス）を両立**
- **プロフェッショナル、クリーン、モダン、信頼性**

---

**このレポートは、AIアシスタントが忘れないように保存された完全な記録です。**
