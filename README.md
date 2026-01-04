# NAR AI予想システム

**Enable CEO専用** - 地方競馬（NAR）AI予想システム Phase 1

---

## 🎯 最終ゴール

明日のレース予想TXTファイルを自動生成する

```bash
cd E:\UmaData\nar-analytics-python
python main.py --date 2025-01-05
```

**出力先:**
```
E:\UmaData\nar-analytics-python\output\20250105\
├── 20250105_大井_予想.txt   (全12レース分を1ファイルに)
├── 20250105_川崎_予想.txt   (全11レース分を1ファイルに)
└── 20250105_浦和_予想.txt   (全10レース分を1ファイルに)
```

---

## 📦 セットアップ

### 1. 環境要件

- **Python:** 3.8以上
- **PostgreSQL:** 12以上
- **OS:** Windows 10/11

### 2. 依存パッケージのインストール

```bash
cd E:\UmaData\nar-analytics-python
pip install -r requirements.txt
```

**requirements.txt:**
```
psycopg2-binary
numpy
```

### 3. データベース設定

`config/db_config.py` を確認：

```python
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'user': 'postgres',
    'password': 'keiba2025',
    'dbname': 'pckeiba'
}
```

---

## 🚀 実行方法

### 方法1: バッチファイルで実行（推奨）

**明日の予想を生成:**
```bash
run_prediction.bat
```

**特定の日付の予想を生成:**
```bash
run_prediction.bat 20250105
```

### 方法2: コマンドラインで実行

```bash
cd E:\UmaData\nar-analytics-python

# 明日の予想を生成
python main.py

# 特定の日付の予想を生成
python main.py --date 20250105
```

---

## 📊 出力フォーマット

**ファイル名規則:**
- `20250105_大井_予想.txt`
- `20250105_川崎_予想.txt`
- `20250105_浦和_予想.txt`

**出力内容:**

```
================================================================================
2025年01月05日 大井競馬場 全レース予想
================================================================================

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
■ 01R ダート1200m 3歳未勝利
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

順位  馬番  馬名              最終AAS得点  ランク
--------------------------------------------------------------------------------
 1     14   ○○○○○○           +28.5      SS
 2     11   △△△△△△           +25.3      S
 3      4   □□□□□□           +22.8      A
 4      2   ××××××××           +18.6      B
 5      9   ◎◎◎◎◎◎           +15.2      B
 ...
```

**ランク基準:**
- **SS:** AAS得点 ≥ 20点
- **S:** AAS得点 ≥ 15点
- **A:** AAS得点 ≥ 10点
- **B:** AAS得点 ≥ 5点
- **C:** AAS得点 ≥ 0点
- **D:** AAS得点 ≥ -5点
- **E:** AAS得点 ≥ -10点
- **F:** AAS得点 < -10点

---

## 🔧 プロジェクト構成

```
E:\UmaData\nar-analytics-python\
├── output\                          # 予想結果出力ディレクトリ
│   └── 20250105\
│       ├── 20250105_大井_予想.txt
│       ├── 20250105_川崎_予想.txt
│       └── 20250105_浦和_予想.txt
├── config\                          # 設定ファイル
│   ├── db_config.py              ✅ DB接続設定
│   ├── odds_correction.py        ✅ オッズ補正係数
│   ├── factor_weights.py         ✅ 競馬場別×ファクター別重み
│   ├── course_master.py          ✅ 競馬場マスタ
│   └── factor_definitions.py     ✅ 31ファクター定義
├── core\                            # コアロジック
│   ├── factor_extractor.py       ✅ ファクター抽出
│   ├── calculate_factor_stats.py ✅ 補正回収率計算
│   ├── aas_calculator.py          ✅ AAS得点計算
│   ├── data_fetcher.py            ✅ データ取得
│   └── prediction_generator_keibajo.py ✅ 競馬場別TXT出力
├── test_connection.py            ✅ DB接続テスト
├── test_step2_corrected_return_rate.py ✅ Step2テスト
├── test_step3_aas_calculation.py ✅ Step3テスト
├── main.py                       ✅ メインスクリプト
├── run_prediction.bat            ✅ 実行バッチファイル
├── requirements.txt              ✅ 依存パッケージ
└── README.md                     ✅ このファイル
```

---

## 🔐 重要な確定事項（絶対に忘れてはいけない）

### 1. AAS計算の重要ルール

✅ **15% = 15** (0.15ではない)
- 的中率15%は、15として計算

✅ **母集団標準偏差** (ddof=0, STDEV.P)
- `np.std(values, ddof=0)`

✅ **baseCalc = 0.55 × ZH + 0.45 × ZR**
- 0.55と0.45の比率を厳守

✅ **最終AAS = 31ファクター全ての合計**
- 各ファクターのAAS得点を計算
- 競馬場別重みを適用
- 全て合計して最終AAS得点

### 2. 補正回収率計算の重要ルール

✅ 目標払戻額 = 10,000円（固定）

✅ オッズ補正係数:
- 単勝: 123段階
- 複勝: 108段階

✅ 期間別重み: 2016=1 → 2025=10
- 2016年以前のデータは除外

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

## 🧪 テスト実行

### Step 2: 補正回収率計算テスト

```bash
cd E:\UmaData\nar-analytics-python
python test_step2_corrected_return_rate.py
```

### Step 3: AAS得点計算テスト

```bash
cd E:\UmaData\nar-analytics-python
python test_step3_aas_calculation.py
```

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

## 📞 サポート

問題が発生した場合は、以下を確認してください：

1. **データベース接続**: `test_connection.py` を実行
2. **ファイル出力先**: `E:\UmaData\nar-analytics-python\output\` が作成されているか確認
3. **Python環境**: `python --version` で Python 3.8以上か確認

---

**NAR AI予想システム Phase 1 完成！**  
**CEO、明日から実運用可能です。Play to Win！🚀**
