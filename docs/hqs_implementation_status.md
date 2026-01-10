# HQS指数システム実装状況の確認レポート

**作成日**: 2026-01-10  
**対象**: 4つの指数（テン/位置/上がり/ペース）の実装確認  
**参照**: 研究報告書 vs 現在の実装

---

## 📋 目次

1. [CEOテスト結果確認](#ceoテスト結果確認)
2. [4つの指数の実装状況](#4つの指数の実装状況)
3. [研究報告書との整合性](#研究報告書との整合性)
4. [HQSワークフローの確認](#hqsワークフローの確認)
5. [次のステップ](#次のステップ)

---

## ✅ CEOテスト結果確認

### **git pull 結果**
```
Updating 83a6fbb..3e2a736
Fast-forward
 core/index_calculator.py     |  53 ++++++---
 docs/fix_1200m_processing.md | 273 ++++++++++++++++++++++
 2 files changed, 308 insertions(+), 18 deletions(-)
```

### **統合テスト結果**
```
✅ テスト1: 実測値使用 - 成功
✅ テスト2: 推定値使用（E級） - 成功
✅ テスト3: 推定値使用（上位クラス） - 成功
✅ テスト4: 1200m以下計算 - 成功
✅ テスト5: 1000m計算 - 成功

✅ 全テスト合格！
```

**1200m以下の処理確認**:
```
INFO:core.index_calculator:✅ 1200m以下の前半タイム計算: 36.00秒 (T_total=72.00秒 - T_last=36.00秒)
INFO:core.index_calculator:✅ 1200m以下の前半タイム計算: 24.00秒 (T_total=60.50秒 - T_last=36.50秒)
```

✅ **Ten3FEstimator を呼ばず、直接計算に修正済み**

---

## 🎯 4つの指数の実装状況

### **1️⃣ テン指数（Ten Index）**

#### **実装場所**: `core/index_calculator.py:320-381`

#### **計算式**:
```python
ten_index = (base_time - zenhan_3f) + baba_correction + furi_correction + waku_correction + kinryo_correction
```

#### **構成要素**:
| 要素 | 説明 | 実装状況 |
|------|------|---------|
| **base_time** | 基準前半3Fタイム（クラス別） | ✅ 実装済み |
| **zenhan_3f** | 実測/推定前半3Fタイム | ✅ 実装済み |
| **baba_correction** | 馬場差補正 | ✅ 実装済み |
| **furi_correction** | 不利補正（スタート直後） | ✅ 実装済み |
| **waku_correction** | 枠順補正（短距離で内枠有利） | ✅ 実装済み |
| **kinryo_correction** | 斤量補正 | ✅ 実装済み |

#### **特記事項**:
- ✅ クラス別基準タイム対応（E級 vs 上位クラス）
- ✅ 1200m以下は直接計算（`direct_calculation`）
- ✅ 1201m以上は Ten3FEstimator で推定（`adjusted` or `ml`）
- ✅ 範囲制限: -100 〜 +100

---

### **2️⃣ 位置指数（Position Index）**

#### **実装場所**: `core/index_calculator.py:388-440`

#### **計算式**:
```python
avg_position = sum(valid_corners) / len(valid_corners)
position_index = 100 - ((avg_position / tosu) * 100)
position_index = position_index + (waku_correction * 15)
```

#### **構成要素**:
| 要素 | 説明 | 実装状況 |
|------|------|---------|
| **corner_1-4** | 1-4コーナー通過順位 | ✅ 実装済み |
| **avg_position** | 平均通過順位 | ✅ 実装済み |
| **tosu** | 出走頭数 | ✅ 実装済み |
| **waku_correction** | 枠順補正（×15倍） | ✅ 実装済み |

#### **特記事項**:
- ✅ 大きいほど先頭に近い（100 = 先頭、0 = 最後尾）
- ✅ 枠順補正あり（内枠有利、係数15）
- ✅ 範囲制限: 0 〜 100
- ⚠️ **研究報告書との比較が必要**

---

### **3️⃣ 上がり指数（Agari Index）**

#### **実装場所**: `core/index_calculator.py:447-511`

#### **計算式**:
```python
agari_index = (base_time - kohan_3f) + baba_correction + furi_correction + (kinryo_correction * 1.2) + pace_correction
```

#### **構成要素**:
| 要素 | 説明 | 実装状況 |
|------|------|---------|
| **base_time** | 基準後半3Fタイム | ✅ 実装済み |
| **kohan_3f** | 実測後半3Fタイム | ✅ 実装済み |
| **baba_correction** | 馬場差補正 | ✅ 実装済み |
| **furi_correction** | 不利補正（直線・4角） | ✅ 実装済み |
| **kinryo_correction** | 斤量補正（×1.2倍） | ✅ 実装済み |
| **pace_correction** | ペース補正（H/M/S） | ✅ 実装済み |

#### **ペース補正ロジック**:
```python
if zenhan_3f > 0:
    pace_type = judge_pace_type(zenhan_3f, kohan_3f, kyori, keibajo_code)
    pace_correction = get_pace_correction_for_agari(pace_type)
    # H（ハイペース）: マイナス補正
    # S（スローペース）: プラス補正
```

#### **特記事項**:
- ✅ 斤量補正は1.2倍（疲労による影響）
- ✅ ペース補正あり（H/M/S判定）
- ✅ 範囲制限: -100 〜 +100
- ⚠️ **研究報告書のペース補正値との比較が必要**

---

### **4️⃣ ペース指数（Pace Index）**

#### **実装場所**: `core/index_calculator.py:518-577`

#### **計算式**:
```python
base_pace = (ten_index + agari_index) / 2
pace_ratio = zenhan_3f / kohan_3f
pace_correction = (pace_ratio - 0.95) * 20.0
pace_index = base_pace + pace_correction + pace_type_correction
```

#### **構成要素**:
| 要素 | 説明 | 実装状況 |
|------|------|---------|
| **base_pace** | テン指数と上がり指数の平均 | ✅ 実装済み |
| **pace_ratio** | 前半3F / 後半3F | ✅ 実装済み |
| **OPTIMAL_BASE_RATIO** | 最適基準値: **0.95** | ✅ 実装済み |
| **CORRECTION_MULTIPLIER** | 最適係数: **20.0** | ✅ 実装済み |
| **pace_type_correction** | H/M/S判定による補正 | ✅ 実装済み |

#### **ペース比率補正の詳細**:
```python
# 実データ分析の結果（2026-01-09 最適化）
OPTIMAL_BASE_RATIO = 0.95  # 平均比率0.942 → 0.95に丸め
CORRECTION_MULTIPLIER = 20.0  # 実データから導出

# 論理:
# pace_ratio > 0.95（前半速い）→ プラス補正（評価上げる）
# pace_ratio < 0.95（前半遅い）→ マイナス補正（評価下げる）
```

#### **特記事項**:
- ✅ **2026-01-09に最適化済み**（研究報告書の結果を反映）
- ✅ 最適基準値: 0.95（実データ平均0.942）
- ✅ 最適係数: 20.0（実データから導出）
- ✅ 範囲制限: -100 〜 +100
- ✅ **研究報告書と一致**

---

## 📚 研究報告書との整合性

### **研究報告書の構成**

CEOが提供した研究報告書:
1. **ペース比率補正の最適化に関する包括的研究報告** (28KB)
2. **HQS指数システムの総合最適化** (25KB)
3. **ペース補正値の最適化に関する包括的研究報告書** (20KB)

---

### **1️⃣ ペース指数の最適化（研究報告書vs実装）**

#### **研究報告書の結論**:
```
現行式の問題点:
Correction = (0.35 - PaceRatio) × 10
→ 0.35が物理的にあり得ない（通常0.90-1.00）

最適化後の式:
Correction = (PaceRatio - OPTIMAL_BASE_RATIO) × CORRECTION_MULTIPLIER
→ OPTIMAL_BASE_RATIO = 0.95
→ CORRECTION_MULTIPLIER = 20.0
```

#### **現在の実装**:
```python
# core/index_calculator.py:545-552
OPTIMAL_BASE_RATIO = 0.95  # 最適基準値（実データから導出）
CORRECTION_MULTIPLIER = 20.0  # 最適係数（実データから導出）
pace_correction = (pace_ratio - OPTIMAL_BASE_RATIO) * CORRECTION_MULTIPLIER
```

#### **整合性評価**:
- ✅ **完全一致**: 研究報告書の結果が正しく実装されている
- ✅ 最適基準値0.95の使用
- ✅ 最適係数20.0の使用
- ✅ コメントで「2026-01-09 最適化」と明記

---

### **2️⃣ 上がり指数のペース補正（要確認）**

#### **研究報告書の内容**:
```
ペース補正の問題点:
現行: H（ハイペース）: -0.5秒、S（スローペース）: +0.5秒
→ 対称性の仮定（非現実的）

最適化:
- ハイペースの影響 > スローペースの影響
- 非対称な補正値の導入
```

#### **現在の実装**:
```python
# core/index_calculator.py:494-499
pace_correction = 0.0
if zenhan_3f > 0:
    pace_type = judge_pace_type(...)
    pace_correction = get_pace_correction_for_agari(pace_type)
```

#### **確認が必要**:
```python
def get_pace_correction_for_agari(pace_type: str) -> Tuple[float, str]:
    """ペースタイプに応じた上がり補正値を取得"""
    # ⚠️ この関数の実装値を確認する必要あり
    # 研究報告書の推奨値: H=-0.8秒、S=+0.3秒（非対称）
    # 現行値: H=-0.5秒、S=+0.5秒（対称）
```

#### **整合性評価**:
- ⚠️ **要確認**: `get_pace_correction_for_agari` の実装値を確認
- ⚠️ 研究報告書の推奨値が反映されているか不明
- 📋 **アクション**: 関数の実装を読んで確認

---

### **3️⃣ 位置指数（要確認）**

#### **研究報告書の内容**:
```
Position Index の計算:
- 平均通過順位を正規化
- 枠順補正の適用
```

#### **現在の実装**:
```python
# core/index_calculator.py:415-426
avg_position = sum(valid_corners) / len(valid_corners)
position_index = 100 - ((avg_position / tosu) * 100)
position_index = position_index + (waku_correction * 15)
```

#### **整合性評価**:
- ✅ **基本的なロジックは実装済み**
- ⚠️ **枠順補正係数15** の根拠を研究報告書で確認
- 📋 **アクション**: 研究報告書の Position Index 章を確認

---

## 🔍 実装確認が必要な関数

### **1. get_pace_correction_for_agari**

**場所**: `core/index_calculator.py` 内

**確認項目**:
- H（ハイペース）の補正値: 研究推奨 -0.8秒 vs 現行 -0.5秒
- S（スローペース）の補正値: 研究推奨 +0.3秒 vs 現行 +0.5秒
- 非対称性の実装

### **2. judge_pace_type**

**場所**: `core/index_calculator.py` 内

**確認項目**:
- ペースタイプ判定の閾値
- H/M/S の分類基準
- 競馬場別・距離別の調整

### **3. 枠順補正係数**

**場所**: テン指数、位置指数、上がり指数

**確認項目**:
- 位置指数での係数15の根拠
- テン指数での枠順補正の減衰（1800m以上で70%）
- 研究報告書との整合性

---

## 📊 HQSワークフローの確認

### **CEOが提示したワークフロー**

```
【HQSワークフロー】
①：4つの指数（テン指数、位置指数、上がり指数、ペース指数）をそれぞれ計算
②：4つの指数の出力値に当てはまる単勝/複勝回収率・単勝/複勝補正回収率を得点化（固定値の為毎回計算しなくていい）
③：当該馬に当てはまる得点化されたものをHQS得点とする
④：結果例（テン指数：8.1点/位置指数：2.6点/上がり指数：10点/ペース指数：9.7点）のように該当馬に付与される
```

### **現在の実装状況**

#### **①: 4つの指数計算** ✅
```python
# core/index_calculator.py:calculate_all_indexes
ten_index = calculate_ten_index(...)
position_index = calculate_position_index(...)
agari_index = calculate_agari_index(...)
pace_index = calculate_pace_index(...)
```
**状況**: ✅ 実装済み

---

#### **②: 回収率に基づく得点化** ❌
```
指数の出力値 → 単勝/複勝回収率マッピング → HQS得点
例: テン指数 = 5.0 → 単勝回収率 = 110% → HQS得点 = 8.1点
```
**状況**: ❌ **未実装**

**必要な実装**:
1. **回収率テーブルの作成**
   - 競馬場別 × クラス別 × 距離別
   - テン指数の値 → 単勝/複勝回収率のマッピング
   - 位置指数の値 → 単勝/複勝回収率のマッピング
   - 上がり指数の値 → 単勝/複勝回収率のマッピング
   - ペース指数の値 → 単勝/複勝回収率のマッピング

2. **得点化関数**
   ```python
   def convert_index_to_hqs_score(
       index_value: float,
       index_type: str,  # 'ten', 'position', 'agari', 'pace'
       keibajo_code: str,
       grade_code: str,
       kyori: int
   ) -> float:
       """指数値をHQS得点に変換"""
       # 回収率テーブルから該当値を取得
       # 得点化ロジックを適用
       return hqs_score
   ```

---

#### **③: HQS得点の統合** ❌
```python
hqs_score = {
    'ten_score': 8.1,
    'position_score': 2.6,
    'agari_score': 10.0,
    'pace_score': 9.7,
    'total_hqs': 30.4  # 合計
}
```
**状況**: ❌ **未実装**

---

#### **④: 最終ゴール（NAR-SI4.0）** ❌
```
NAR-SI4.0 = NAR-SI3.0 + HQS得点 + RGS得点
```
**状況**: ❌ **未実装**

---

## 📋 次のステップ（優先順位付き）

### **🔴 緊急タスク**

#### **タスク2.1: ペース補正値の確認** ⭐⭐⭐
```python
# 確認対象: get_pace_correction_for_agari
# 研究推奨値: H=-0.8秒、S=+0.3秒
# 現行値: H=-0.5秒、S=+0.5秒（推定）
```

**アクション**:
1. `get_pace_correction_for_agari` の実装を読む
2. 研究報告書の推奨値と比較
3. 必要に応じて修正

---

#### **タスク2.2: 枠順補正係数の確認** ⭐⭐
```python
# 位置指数での係数15の根拠
position_waku_correction = waku_correction * 15
```

**アクション**:
1. 研究報告書の Position Index 章を確認
2. 係数15の妥当性を検証

---

### **🟡 高優先タスク**

#### **タスク3: 回収率分析ツールの作成** ⭐⭐⭐
```
目的: 4つの指数 → 回収率マッピングテーブルの作成
```

**機能**:
1. **データ収集**: 過去レースデータから回収率を計算
2. **テーブル作成**: 
   - 指数値 × 競馬場 × クラス × 距離 → 回収率
3. **CSVエクスポート**: Excel で確認可能

---

#### **タスク4: HQS得点化システムの実装** ⭐⭐⭐
```
目的: 指数 → HQS得点への変換
```

**機能**:
1. **回収率テーブル読み込み**
2. **得点化関数**
3. **統合HQS得点の計算**

---

### **🟢 通常タスク**

#### **タスク5: NAR-SI4.0の統合** ⭐⭐
```
NAR-SI4.0 = NAR-SI3.0 + HQS得点 + RGS得点
```

---

## 🎯 CEOへの質問

### **Q1: ペース補正値の修正**
研究報告書の推奨値（H=-0.8秒、S=+0.3秒）を適用しますか？
- A) はい、今すぐ修正
- B) いいえ、現行値（-0.5秒/+0.5秒）を維持
- C) まず実装を確認してから判断

### **Q2: 回収率分析の優先順位**
どの順序で進めますか？
- A) ペース補正値の確認 → 回収率分析
- B) 回収率分析を先に進める
- C) 両方同時進行

### **Q3: データソース**
回収率分析のデータソースは？
- A) 既存のデータベース（SQLite/PostgreSQL）
- B) CSV ファイル
- C) API

---

**作成者**: Enable CEO & AI戦略家  
**Play to Win!** 🚀
