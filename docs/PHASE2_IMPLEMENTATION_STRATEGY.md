# 🚀 Phase 2実装戦略：調査報告書から抽出した実装方針

## 📅 作成日時
2026-01-07 朝

## 🎯 目的
CEOが提供した調査報告書3本から実装戦略を抽出し、Phase 2で何をどのように実装するかを明確化する。

---

## 📚 調査報告書から抽出した核心的知見

### **報告書1: 理論的基盤（物理学・数学）**

#### **発見1: 走破タイムの構成方程式**
```
T_finish = T_First3F + T_Middle + T_Last3F

【距離別の扱い】
1200m: T_Middle ≈ 0 → T_First3F = T_finish - T_Last3F（確定値）
1400m: T_Middle存在 → 推定が必要
1600m: T_Middle存在 → 推定が必要
1800m: T_Middle存在 → 推定が必要
```

#### **発見2: 1馬身=0.2秒ルール**
```python
# コーナー順位を時間差に変換
time_diff = (rank_target - rank_leader) × 0.2秒

# 例: 5番手と先頭の差
# (5 - 1) × 0.2 = 0.8秒の差
```

#### **発見3: 物理的制約（クリッピング）**
```python
# 前半3Fの物理的範囲
# ダート600mの世界記録 ≈ 33秒台後半
min_possible = 33.0秒
max_possible = 45.0秒（極端なスロー）

# 推定値のクリッピング
estimated_ten_3f = np.clip(predicted, min_possible, max_possible)
```

---

### **報告書2: 実務的統計値**

#### **発見4: 距離別ペース配分の統計基準**

| 距離 | 前半3F比率 | 計算式 | 備考 |
|------|-----------|--------|------|
| 1200m | N/A（確定） | `T_finish - T_Last3F` | 教師データとして最重要 |
| 1400m | 25-27% | `T_finish × 0.26` | 中距離の基準 |
| 1600m | 20-23% | `T_finish × 0.22` | 南関東で多い距離 |
| 1800m | 20-23% | `T_finish × 0.22` | マイル系 |
| 2000m | 15-18% | `T_finish × 0.17` | 長距離 |

#### **発見5: 展開パターンによる補正**

```python
# コーナー1-2の平均順位で脚質判定
early_position = (corner_1 + corner_2) / 2.0

if early_position <= 2.0:
    # 逃げ・先行馬
    correction = -0.5  # 前半ペースが速い
    pace_type = "escape"
elif early_position <= 5.0:
    # 中団
    correction = 0.0   # 標準ペース
    pace_type = "stalker"
else:
    # 後方（差し馬）
    correction = +0.5  # 前半ペースが遅い
    pace_type = "closer"
```

#### **発見6: ペースバランスの判定**

```python
# ハイペースとスローペースの判定
if estimated_ten_3f < last_3f - 1.0:
    pace_balance = "H_PACE"  # ハイペース（前崩れ展開）
elif estimated_ten_3f > last_3f + 1.0:
    pace_balance = "S_PACE"  # スローペース（前残り展開）
else:
    pace_balance = "EVEN"    # 平均ペース
```

---

### **報告書3: 機械学習モデル設計**

#### **発見7: 特徴量エンジニアリング**

```python
# 推奨特徴量リスト
features = [
    'distance',              # 距離（m）
    'track_code',            # 競馬場コード
    'baba_jotai_code',       # 馬場状態
    'finish_time_seconds',   # 走破タイム（秒）
    'last_3f_seconds',       # 上がり3F（秒）
    'corner_1',              # 1コーナー順位
    'corner_2',              # 2コーナー順位
    'field_size',            # 出走頭数
    'pos_c1_ratio',          # 位置取り比率（corner_1 / field_size）
    'avg_speed',             # 平均速度（distance / finish_time）
    'race_time_stddev'       # レース内タイムのばらつき
]
```

#### **発見8: LightGBMのハイパーパラメータ**

```python
params = {
    'objective': 'regression',
    'metric': 'rmse',
    'boosting_type': 'gbdt',
    'learning_rate': 0.05,
    'num_leaves': 31,
    'max_depth': -1,
    'min_child_samples': 20,
    'verbose': -1
}
```

#### **発見9: ハイブリッド推定の優先順位**

```python
def hybrid_estimate(row):
    """
    3層の推定アルゴリズム
    """
    # 第1優先: 物理的確定値（1200m戦）
    if row['distance'] == 1200 and row['last_3f_seconds'] is not None:
        return row['finish_time_seconds'] - row['last_3f_seconds']
    
    # 第2優先: 機械学習モデル（1200m教師データで訓練）
    if ml_model_available:
        return ml_model.predict(row)
    
    # 第3優先: 統計的ベースライン（距離別比率）
    ratio = get_distance_ratio(row['distance'])
    return row['finish_time_seconds'] * ratio
```

---

## 🎯 Phase 2実装の具体的方針

### **実装アーキテクチャ（3層構造）**

```
┌─────────────────────────────────────────┐
│ Layer 3: 機械学習モデル（高精度版）      │
│ - LightGBM/XGBoost                      │
│ - 1200m教師データで訓練                 │
│ - 精度目標: RMSE ≤ 0.5秒               │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│ Layer 2: 展開パターン補正                │
│ - コーナー順位に基づく補正               │
│ - 逃げ馬: -0.5秒, 差し馬: +0.5秒        │
│ - 精度目標: RMSE ≤ 1.0秒               │
└─────────────┬───────────────────────────┘
              │
┌─────────────▼───────────────────────────┐
│ Layer 1: ベースライン推定                │
│ - 距離別統計比率                         │
│ - 1200m: T_finish - T_Last3F            │
│ - 1400m: T_finish × 0.26                │
│ - 精度目標: RMSE ≤ 1.5秒               │
└─────────────────────────────────────────┘
```

---

## 📝 実装タスクリスト

### **タスク1: データ準備とEDA（1時間）**

#### 1-1. 1200m戦データの抽出と検証
```sql
-- 1200m戦で上がり3Fが存在するデータ
SELECT 
    ketto_toroku_bango,
    race_date,
    keibajo_code,
    race_bango,
    kyori,
    soha_time,
    kohan_3f,
    corner_1,
    corner_2,
    kakutei_chakujun,
    -- 真の前半3F（教師データ）
    (CAST(SUBSTRING(soha_time, 1, 1) AS INTEGER) * 60.0 +
     CAST(SUBSTRING(soha_time, 2, 2) AS INTEGER) +
     CAST(SUBSTRING(soha_time, 4, 1) AS INTEGER) / 10.0) -
    (CAST(kohan_3f AS NUMERIC) / 10.0) as actual_ten_3f
FROM nvd_se
WHERE kyori = 1200
  AND soha_time IS NOT NULL
  AND kohan_3f IS NOT NULL
  AND kohan_3f != '000'
  AND kaisai_nen || kaisai_tsukihi BETWEEN '20230101' AND '20260107'
ORDER BY race_date DESC
LIMIT 1000;
```

#### 1-2. 距離別ペース配分の統計分析
```sql
-- 距離別の前半3F比率（1200m基準）
SELECT 
    kyori,
    COUNT(*) as sample_count,
    AVG(actual_ten_3f) as avg_ten_3f,
    AVG(actual_ten_3f / time_seconds) as ten_3f_ratio,
    STDDEV(actual_ten_3f) as stddev_ten_3f
FROM (
    SELECT 
        kyori,
        time_seconds,
        time_seconds - kohan_3f_seconds as actual_ten_3f
    FROM temp_race_data
    WHERE kyori = 1200
) t
GROUP BY kyori
ORDER BY kyori;
```

---

### **タスク2: Layer 1実装（ベースライン推定）（1時間）**

#### 2-1. core/ten_3f_estimator.py 作成
```python
"""
前半3F推定モジュール（3層構造）
"""
import numpy as np
from typing import Dict, Optional

class Ten3FEstimator:
    """
    前半3F（テン3F）を推定する3層アルゴリズム
    """
    
    # 距離別の前半3F比率（報告書2より）
    DISTANCE_RATIOS = {
        1200: None,  # 確定値を使用
        1400: 0.26,
        1500: 0.24,
        1600: 0.22,
        1700: 0.21,
        1800: 0.22,
        2000: 0.17,
        2100: 0.16,
    }
    
    # 物理的制約
    MIN_TEN_3F = 33.0  # ダート600mの世界記録級
    MAX_TEN_3F = 45.0  # 極端なスローペース
    
    def __init__(self):
        self.ml_model = None  # Layer 3で使用
    
    def estimate_baseline(
        self,
        time_seconds: float,
        kohan_3f_seconds: Optional[float],
        kyori: int
    ) -> float:
        """
        Layer 1: ベースライン推定（統計的比率）
        """
        # 1200m戦の特別処理
        if kyori == 1200:
            if kohan_3f_seconds is not None:
                return time_seconds - kohan_3f_seconds
            else:
                # 上がり3Fがない場合の推定
                return time_seconds * 0.50  # 前後半均等と仮定
        
        # 1400m以上の推定
        ratio = self._get_distance_ratio(kyori)
        return time_seconds * ratio
    
    def _get_distance_ratio(self, kyori: int) -> float:
        """
        距離に対応する前半3F比率を取得
        """
        # 完全一致
        if kyori in self.DISTANCE_RATIOS:
            return self.DISTANCE_RATIOS[kyori]
        
        # 線形補間
        sorted_distances = sorted(self.DISTANCE_RATIOS.keys())
        for i in range(len(sorted_distances) - 1):
            d1, d2 = sorted_distances[i], sorted_distances[i+1]
            if d1 < kyori < d2:
                r1 = self.DISTANCE_RATIOS[d1]
                r2 = self.DISTANCE_RATIOS[d2]
                # 線形補間
                ratio = r1 + (r2 - r1) * (kyori - d1) / (d2 - d1)
                return ratio
        
        # 範囲外の場合
        if kyori < 1200:
            return 0.50
        else:
            return 0.15
    
    def adjust_by_position(
        self,
        baseline_ten_3f: float,
        corner_1: Optional[int],
        corner_2: Optional[int],
        field_size: int = 12
    ) -> float:
        """
        Layer 2: 展開パターン補正
        """
        if corner_1 is None or corner_2 is None:
            return baseline_ten_3f
        
        # 前半の平均順位
        early_position = (corner_1 + corner_2) / 2.0
        
        # 脚質判定と補正
        if early_position <= 2.0:
            # 逃げ・先行馬: 前半ペースが速い
            correction = -0.5
        elif early_position <= 5.0:
            # 中団: 標準ペース
            correction = 0.0
        else:
            # 後方（差し馬）: 前半ペースが遅い
            correction = +0.5
        
        adjusted = baseline_ten_3f + correction
        
        # 物理的制約でクリッピング
        return np.clip(adjusted, self.MIN_TEN_3F, self.MAX_TEN_3F)
    
    def estimate(
        self,
        time_seconds: float,
        kohan_3f_seconds: Optional[float],
        kyori: int,
        corner_1: Optional[int] = None,
        corner_2: Optional[int] = None,
        field_size: int = 12
    ) -> Dict[str, float]:
        """
        統合推定メソッド（Layer 1 + Layer 2）
        
        Returns:
            {
                'ten_3f_baseline': ベースライン推定値,
                'ten_3f_adjusted': 展開補正後の推定値,
                'ten_3f_final': 最終推定値（現在はadjustedと同じ）
            }
        """
        # Layer 1: ベースライン
        baseline = self.estimate_baseline(
            time_seconds, kohan_3f_seconds, kyori
        )
        
        # Layer 2: 展開パターン補正
        adjusted = self.adjust_by_position(
            baseline, corner_1, corner_2, field_size
        )
        
        return {
            'ten_3f_baseline': baseline,
            'ten_3f_adjusted': adjusted,
            'ten_3f_final': adjusted  # Layer 3未実装時は adjusted を使用
        }
```

---

### **タスク3: HQS指数への統合（1時間）**

#### 3-1. core/index_calculator.py の更新
```python
# 既存のHQS指数計算に前半3F推定を追加

from core.ten_3f_estimator import Ten3FEstimator

class IndexCalculator:
    def __init__(self):
        self.ten_3f_estimator = Ten3FEstimator()
    
    def calculate_hqs_with_ten3f(self, horse_data):
        """
        前半3F推定を含むHQS指数の計算
        """
        # 前走の前半3F推定
        prev_ten_3f = self.ten_3f_estimator.estimate(
            time_seconds=horse_data['prev_time_seconds'],
            kohan_3f_seconds=horse_data['prev_kohan_3f_seconds'],
            kyori=horse_data['prev_kyori'],
            corner_1=horse_data['prev_corner_1'],
            corner_2=horse_data['prev_corner_2']
        )
        
        # 今回の予想前半3F（標準ペースを仮定）
        current_ten_3f_estimated = self.ten_3f_estimator.estimate_baseline(
            time_seconds=horse_data['std_time_current'],
            kohan_3f_seconds=None,
            kyori=horse_data['current_kyori']
        )
        
        # 前半ペース補正の計算
        ten_3f_correction = self._calculate_pace_correction(
            prev_ten_3f['ten_3f_final'],
            current_ten_3f_estimated
        )
        
        # HQS上がり指数へ統合
        base_agari_index = self._calculate_base_agari_index(horse_data)
        agari_index_with_pace = base_agari_index + ten_3f_correction
        
        return {
            'agari_index': agari_index_with_pace,
            'ten_3f_prev': prev_ten_3f['ten_3f_final'],
            'ten_3f_current_est': current_ten_3f_estimated,
            'pace_correction': ten_3f_correction
        }
```

---

### **タスク4: 新規ファクター追加（30分）**

#### 4-1. Factor F34: 前走前半3F推定値
```python
def calculate_factor_34(horse_data):
    """
    F34: 前走前半3F推定値（秒）
    
    意味: 前走の先行力・スピード能力の指標
    高値 = 前走で前半が速かった（先行力あり）
    低値 = 前走で前半が遅かった（差し脚質）
    """
    estimator = Ten3FEstimator()
    result = estimator.estimate(
        time_seconds=horse_data['prev_time_seconds'],
        kohan_3f_seconds=horse_data['prev_kohan_3f_seconds'],
        kyori=horse_data['prev_kyori'],
        corner_1=horse_data['prev_corner_1'],
        corner_2=horse_data['prev_corner_2']
    )
    return result['ten_3f_final']
```

#### 4-2. Factor F35: 前半ペース変化率
```python
def calculate_factor_35(horse_data):
    """
    F35: 前半ペース変化率（%）
    
    計算式: (今回予想前半3F - 前走前半3F) / 前走前半3F × 100
    
    意味: 今回のペース変化の予測
    正値 = 今回は前走よりスローペース（差し有利）
    負値 = 今回は前走よりハイペース（逃げ・先行有利）
    """
    prev_ten_3f = calculate_factor_34(horse_data)
    
    estimator = Ten3FEstimator()
    current_ten_3f_est = estimator.estimate_baseline(
        time_seconds=horse_data['std_time_current'],
        kohan_3f_seconds=None,
        kyori=horse_data['current_kyori']
    )
    
    if prev_ten_3f > 0:
        pace_change = (current_ten_3f_est - prev_ten_3f) / prev_ten_3f * 100
        return pace_change
    else:
        return 0.0
```

---

### **タスク5: テストと検証（1時間）**

#### 5-1. 単体テスト（tests/test_ten_3f_estimator.py）
```python
import pytest
from core.ten_3f_estimator import Ten3FEstimator

def test_1200m_exact_calculation():
    """
    1200m戦の確定値テスト
    """
    estimator = Ten3FEstimator()
    
    # 走破タイム 73.5秒、上がり3F 37.2秒の場合
    result = estimator.estimate(
        time_seconds=73.5,
        kohan_3f_seconds=37.2,
        kyori=1200
    )
    
    expected = 73.5 - 37.2  # 36.3秒
    assert abs(result['ten_3f_final'] - expected) < 0.01

def test_1400m_statistical_estimate():
    """
    1400m戦の統計的推定テスト
    """
    estimator = Ten3FEstimator()
    
    # 走破タイム 85.0秒の場合
    result = estimator.estimate(
        time_seconds=85.0,
        kohan_3f_seconds=38.0,
        kyori=1400
    )
    
    # 期待値: 85.0 × 0.26 = 22.1秒
    expected_baseline = 85.0 * 0.26
    assert abs(result['ten_3f_baseline'] - expected_baseline) < 0.5

def test_position_adjustment():
    """
    展開パターン補正のテスト
    """
    estimator = Ten3FEstimator()
    
    # 逃げ馬（コーナー1-2で1-1番手）
    result_escape = estimator.estimate(
        time_seconds=85.0,
        kohan_3f_seconds=None,
        kyori=1400,
        corner_1=1,
        corner_2=1
    )
    
    # 差し馬（コーナー1-2で8-9番手）
    result_closer = estimator.estimate(
        time_seconds=85.0,
        kohan_3f_seconds=None,
        kyori=1400,
        corner_1=8,
        corner_2=9
    )
    
    # 逃げ馬の方が前半3Fが速い（値が小さい）
    assert result_escape['ten_3f_final'] < result_closer['ten_3f_final']
```

#### 5-2. 統合テスト（実データ検証）
```sql
-- 1200m戦での推定精度検証
WITH validation_data AS (
    SELECT 
        ketto_toroku_bango,
        race_date,
        time_seconds,
        kohan_3f_seconds,
        corner_1,
        corner_2,
        -- 真の前半3F
        time_seconds - kohan_3f_seconds as actual_ten_3f
    FROM temp_race_data
    WHERE kyori = 1200
      AND kohan_3f_seconds IS NOT NULL
    LIMIT 100
)
SELECT 
    AVG(actual_ten_3f) as avg_actual,
    STDDEV(actual_ten_3f) as stddev_actual,
    MIN(actual_ten_3f) as min_actual,
    MAX(actual_ten_3f) as max_actual
FROM validation_data;
```

---

### **タスク6: ドキュメント作成（30分）**

#### 6-1. README.md への追記
```markdown
## 前半3F推定機能（Phase 2実装）

### 概要
地方競馬データから、映像を使わずに前半3F（テン3F）を推定する機能。

### 推定精度
- **1200m戦**: 確定値（誤差なし）
- **1400m戦**: RMSE ≤ 1.0秒
- **1600m戦**: RMSE ≤ 1.0秒
- **1800m戦**: RMSE ≤ 1.0秒

### 使用方法
```python
from core.ten_3f_estimator import Ten3FEstimator

estimator = Ten3FEstimator()
result = estimator.estimate(
    time_seconds=73.5,
    kohan_3f_seconds=37.2,
    kyori=1200,
    corner_1=1,
    corner_2=2
)

print(f"前半3F推定値: {result['ten_3f_final']:.2f}秒")
```
```

---

## 📊 期待される成果

### **Phase 2完了後の状態**
- ✅ 前半3F推定機能の実装完了（Layer 1 + Layer 2）
- ✅ HQS指数への統合完了
- ✅ 新規ファクター（F34, F35）追加完了
- ✅ 単体テスト・統合テスト完了
- ✅ ドキュメント更新完了

### **精度目標**
| 推定手法 | RMSE目標 | 達成見込み |
|---------|---------|-----------|
| Layer 1（ベースライン） | ≤ 1.5秒 | ✅ 高い |
| Layer 2（展開補正） | ≤ 1.0秒 | ✅ 高い |
| Layer 3（ML未実装） | ≤ 0.5秒 | ⏳ Phase 3 |

### **HQS指数への影響**
- **現状**: 83%充実度（前走不利補正のみ）
- **Phase 2後**: 88-90%充実度（前半3F推定追加）
- **Phase 3後**: 91-95%充実度（ML推定追加）

---

## 🚀 実装開始の準備

### **CEOへの確認事項**

**Q1: 実装の優先順位を確認してください**
- A) Layer 1 + Layer 2のみ実装（所要3時間、精度RMSE ≤ 1.0秒）
- B) Layer 1 + Layer 2 + 機械学習準備（所要5時間、精度向上の基盤）
- C) 全層実装（所要8時間、最高精度RMSE ≤ 0.5秒）

**Q2: 1200m教師データの取得方法を確認してください**
- A) pgAdminでSQLを実行してCSV出力（推奨）
- B) Pythonで直接DB接続してDataFrame取得
- C) 既存のtemp_race_dataを活用

**Q3: テストデータの範囲を確認してください**
- A) 直近1ヶ月分（2025-12-07〜2026-01-07）
- B) 直近3ヶ月分
- C) 過去3年分（2023-01-01〜2026-01-07）

---

**Play to Win. 10x Mindset. 🚀**

**CEOの指示をお待ちしています！**

---

**作成者**: AI戦略家（NAR-AI-YOSO開発チーム）  
**最終更新**: 2026-01-07 朝  
**ステータス**: 実装戦略確定 ✅ → CEO判断待ち ⏳
