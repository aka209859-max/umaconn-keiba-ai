# ペース補正値の最適化に関するディープサーチプロンプト

## 🎯 **研究の目的**

地方競馬（ダート）における「ペース補正」の最適値を、2016年〜2025年の実データから統計的に導出する。

---

## 📋 **背景と問題点**

### **現行の補正値（経験則）:**
```python
# 現行値（根拠不明）
if pace_type == 'H':  # ハイペース
    correction = -0.5秒
elif pace_type == 'S':  # スローペース
    correction = +0.5秒
else:  # ミドルペース
    correction = 0.0秒
```

### **問題点:**
1. **対称性の仮定**: ハイペースの消耗（-0.5秒）とスローペースの余力（+0.5秒）が対称であると仮定している（誤り）
2. **経験則**: ±0.5秒の根拠が不明確
3. **非線形性の無視**: 物理学的には、限界を超えた消耗は非線形である可能性が高い

---

## 📊 **データセットの定義**

### **対象期間:**
- 2016年1月1日 〜 2025年12月31日（10年間）

### **対象競馬場:**
- 地方競馬全場（ばんえい除く）
- **除外**: 大井競馬場（'44'）、名古屋競馬場（'48'）
  - **理由**: 大井は砂の全面入れ替え、名古屋は移転により、10年間の一貫性がない

### **有効サンプル数:**
- 約118,500レース（除外・中止等を除く）

---

## 🔬 **分析手法**

### **Step 1: ペースタイプの定量的定義**

```python
# ペース比率の計算
pace_ratio = 実走前半3F / 実走後半3F
base_pace_ratio = 基準前半3F / 基準後半3F

# 差分
pace_diff = pace_ratio - base_pace_ratio

# ペースタイプ判定
if pace_diff >= 0.03:
    pace_type = 'H'  # ハイペース
elif pace_diff <= -0.03:
    pace_type = 'S'  # スローペース
else:
    pace_type = 'M'  # ミドルペース
```

---

### **Step 2: ペースタイプ別の後半3F差分を分析**

**分析クエリ:**
```sql
SELECT 
    pace_type,
    AVG(kohan_3f - base_kohan_3f) AS avg_kohan_diff,
    STDDEV(kohan_3f - base_kohan_3f) AS stddev_kohan_diff,
    COUNT(*) AS race_count,
    SUM(CASE WHEN chakujun = 1 THEN 1 ELSE 0 END) AS win_count,
    AVG(CASE WHEN chakujun = 1 THEN 1.0 ELSE 0.0 END) AS win_rate
FROM races
WHERE keibajo_code NOT IN ('44', '48')  -- 大井・名古屋除外
  AND kaisai_date BETWEEN '2016-01-01' AND '2025-12-31'
  AND zenhan_3f > 0
  AND kohan_3f > 0
GROUP BY pace_type
```

---

### **Step 3: 着順相関の検証**

**分析クエリ:**
```sql
-- ペース補正後の上がり指数と着順の相関を検証
SELECT 
    pace_type,
    correction_value,
    AVG(CASE WHEN chakujun = 1 THEN 1.0 ELSE 0.0 END) AS win_rate,
    AVG(chakujun) AS avg_chakujun
FROM (
    SELECT 
        pace_type,
        chakujun,
        kohan_3f,
        base_kohan_3f,
        (base_kohan_3f - kohan_3f) + correction_value AS corrected_agari_index
    FROM races
    WHERE ...
) sub
GROUP BY pace_type, correction_value
ORDER BY pace_type, win_rate DESC
```

---

### **Step 4: 最適補正値の導出**

**最適化目標:**
1. **単勝的中率の最大化**: 補正後の上がり指数が高い馬の単勝率が最大化される補正値を探す
2. **分布の正規化**: 補正後の上がり指数が正規分布に近づく補正値を探す
3. **平均着順の最小化**: 補正後の上がり指数が高い馬の平均着順が小さくなる補正値を探す

**探索範囲:**
```python
# ハイペース (H) の補正値探索
H_correction_range = [-2.0, -1.5, -1.0, -0.5, 0.0, +0.5, +1.0]

# スローペース (S) の補正値探索
S_correction_range = [-1.0, -0.5, 0.0, +0.5, +1.0, +1.5, +2.0]
```

---

## 📈 **期待される出力**

### **1. ペースタイプ別の統計**

```
【ハイペース (H)】
  レース数: 25,000レース
  単勝率: 9.5%
  後半3F平均差分: +1.2秒（実走 - 基準）
  標準偏差: 0.8秒
  推奨補正値: -1.2秒（基準より遅いため、ハンデとしてプラス補正）

【ミドルペース (M)】
  レース数: 70,000レース
  単勝率: 10.0%
  後半3F平均差分: +0.0秒（実走 - 基準）
  標準偏差: 0.6秒
  推奨補正値: 0.0秒

【スローペース (S)】
  レース数: 23,500レース
  単勝率: 10.3%
  後半3F平均差分: -0.8秒（実走 - 基準）
  標準偏差: 0.7秒
  推奨補正値: +0.8秒（基準より速いため、ペナルティとしてマイナス補正）
```

---

### **2. 最適補正値の提言**

```python
# 実データ分析に基づく最適補正値
PACE_CORRECTION = {
    'H': -1.2,  # ハイペース（後半バテる → ハンデ）
    'M': 0.0,   # ミドルペース（標準）
    'S': +0.8,  # スローペース（後半余力 → ペナルティ）
}
```

---

### **3. 距離別最適化（オプション）**

```python
# 距離区分別の最適補正値
PACE_CORRECTION_BY_DISTANCE = {
    '短距離': {  # 〜1300m
        'H': -0.8,
        'M': 0.0,
        'S': +0.5,
    },
    '中距離': {  # 1301〜1600m
        'H': -1.2,
        'M': 0.0,
        'S': +0.8,
    },
    '長距離': {  # 1601m〜
        'H': -1.5,
        'M': 0.0,
        'S': +1.0,
    },
}
```

---

## 🔍 **検証方法**

### **検証1: 補正前後の単勝率比較**
```sql
-- 補正前の単勝率
SELECT 
    CASE 
        WHEN agari_index > 10 THEN '上位'
        WHEN agari_index > 0 THEN '中位'
        ELSE '下位'
    END AS agari_rank,
    AVG(CASE WHEN chakujun = 1 THEN 1.0 ELSE 0.0 END) AS win_rate
FROM races
GROUP BY agari_rank

-- 補正後の単勝率
SELECT 
    CASE 
        WHEN corrected_agari_index > 10 THEN '上位'
        WHEN corrected_agari_index > 0 THEN '中位'
        ELSE '下位'
    END AS agari_rank,
    AVG(CASE WHEN chakujun = 1 THEN 1.0 ELSE 0.0 END) AS win_rate
FROM races
GROUP BY agari_rank
```

### **検証2: 分布の正規性検証**
```python
import matplotlib.pyplot as plt
import scipy.stats as stats

# 補正前の分布
plt.hist(agari_index_before, bins=50, alpha=0.5, label='Before')

# 補正後の分布
plt.hist(agari_index_after, bins=50, alpha=0.5, label='After')

# 正規性検定（Shapiro-Wilk検定）
stat, p_value = stats.shapiro(agari_index_after)
```

---

## 🎯 **最終目標**

実データ分析に基づき、以下を提言する：

1. **最適補正値**: ハイペース/ミドル/スローペースそれぞれの最適補正値
2. **統計的根拠**: なぜその値が最適なのか（単勝率、着順、分布の正規性）
3. **距離別最適化**: 距離区分ごとの補正値（オプション）
4. **実装コード**: すぐに実装できるPythonコード

---

## 💡 **注意事項**

1. **馬場状態の影響**: 馬場状態（良/稍重/重/不良）によるバイアスを考慮
2. **クラス別の影響**: クラス（A/B/C）による能力差を考慮
3. **季節変動**: 季節（春/夏/秋/冬）による影響を考慮

---

以上のプロンプトをディープサーチエンジンに入力し、最適なペース補正値を導出してください。
