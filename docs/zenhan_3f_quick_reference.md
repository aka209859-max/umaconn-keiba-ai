# 前半3Fタイム計算 クイックリファレンス

**作成日**: 2026-01-10  
**対象**: 地方競馬AI予想システム（HQS指数計算エンジン）

---

## 📊 3つの計算方法 早見表

| # | 状況 | 条件 | 計算方法 | 実装箇所 | 精度 |
|---|------|------|---------|----------|------|
| 1️⃣ | **実測値** | `zenhan_3f > 0` | データベースの値をそのまま使用 | `index_calculator.py:678` | 完全 |
| 2️⃣ | **推定値（長距離）** | `zenhan_3f == 0` かつ `kyori ≥ 1201m` | Ten3FEstimator推定<br>基準タイム + スピード指数補正 | `ten_3f_estimator.py:119-151` | ±0.3-1.0秒 |
| 3️⃣ | **前半タイム（短距離）** | `zenhan_3f == 0` かつ `kyori ≤ 1200m` | `T_start = T_total - T_last` | `ten_3f_estimator.py:110-117` | 完全（確定値） |

---

## 🎯 距離別の処理フロー

```
入力: horse_data

↓

zenhan_3f 存在チェック
├─ YES → 実測値使用（method='actual'）
└─ NO  → 距離判定
         ├─ kyori ≤ 1200m  → T_total - T_last（method='baseline'）
         └─ kyori ≥ 1201m  → Ten3FEstimator推定（method='adjusted' or 'ml'）

↓

テン指数計算
```

---

## 📐 計算式詳細

### 1️⃣ 実測値使用

```python
zenhan_3f = horse_data['zenhan_3f'] / 10.0  # 秒単位に変換
```

**例**: `zenhan_3f = 358` → `35.8秒`

---

### 2️⃣ 推定値（1201m以上）

```python
# Step 1: 基準タイム取得（クラス別）
base_zenhan = get_base_time(keibajo_code, kyori, 'zenhan_3f', grade_code)

# Step 2: スピード指数補正
std_total = get_standard_total_time(keibajo_code, kyori, grade_code)
speed_index = std_total - time_seconds
adjusted_zenhan = base_zenhan - (speed_index * 0.3)

# Step 3: クリッピング
zenhan_3f = np.clip(adjusted_zenhan, 30.0, 45.0)
```

**補正係数**: `0.3`（理論文書準拠）

**例**: 門別1600m E級
- `base_zenhan = 35.8秒`
- `std_total = 104.0秒`, `time_seconds = 105.0秒`
- `speed_index = 104.0 - 105.0 = -1.0`
- `adjusted_zenhan = 35.8 - (-1.0 × 0.3) = 35.8 + 0.3 = 36.1秒`

---

### 3️⃣ 前半タイム（1200m以下）

```python
# 後半3Fがある場合
zenhan_3f = time_seconds - kohan_3f_seconds

# 後半3Fがない場合（フォールバック）
zenhan_3f = time_seconds * 0.50
```

**重要**: 1200m以下では「前半3F」は実際の3F（600m）を意味しない
- 1000m: 前半タイム ≈ 400m（約2F）
- 1100m: 前半タイム ≈ 500m（約2.5F）
- 1200m: 前半タイム = 600m（ちょうど3F）

**例**: 1000mレース
- `time_seconds = 60.5秒`
- `kohan_3f_seconds = 36.5秒`
- `zenhan_3f = 60.5 - 36.5 = 24.0秒`（約2Fに相当）

---

## 🔍 距離別の実例

| 距離 | 実測値 | 推定方法 | 前半タイムの意味 |
|------|--------|---------|----------------|
| 1000m | 優先 | `T_total - T_last` | 前半 400m（約2F） |
| 1100m | 優先 | `T_total - T_last` | 前半 500m（約2.5F） |
| 1200m | 優先 | `T_total - T_last` | 前半 600m（ちょうど3F） |
| 1400m | 優先 | Ten3FEstimator | 前半 600m（3F） |
| 1600m | 優先 | Ten3FEstimator | 前半 600m（3F） |
| 1800m | 優先 | Ten3FEstimator | 前半 600m（3F） |
| 2000m | 優先 | Ten3FEstimator | 前半 600m（3F） |

---

## ⚙️ 実装コード抜粋

### index_calculator.py (699-714行)

```python
if zenhan_3f_raw is None or zenhan_3f_raw == 0.0:
    logger.info(f"⚠️ zenhan_3f が欠損しています。Ten3FEstimator で推定します（kyori={kyori}m）")
    estimator = get_ten_3f_estimator()
    result = estimator.estimate(
        time_seconds=time_seconds,
        kohan_3f_seconds=kohan_3f,
        kyori=kyori,
        corner_1=corner_1 if corner_1 > 0 else None,
        corner_2=corner_2 if corner_2 > 0 else None,
        field_size=tosu,
        use_ml=True,
        keibajo_code=keibajo_code,      # ✅ 競馬場コード
        grade_code=grade_code           # ✅ クラス別補正
    )
    zenhan_3f = result['ten_3f_final']
    ten_3f_method = result['method']
```

### ten_3f_estimator.py (110-151行)

```python
def estimate_baseline(self, time_seconds, kohan_3f_seconds, kyori, 
                     keibajo_code=None, grade_code=None):
    # 1200m以下: 確定値
    if kyori <= 1200:
        if kohan_3f_seconds is not None:
            return time_seconds - kohan_3f_seconds  # ✅ T_total - T_last
        else:
            return time_seconds * 0.50
    
    # 1201m以上: 基準タイム + スピード指数補正
    base_zenhan = get_base_time(keibajo_code, kyori, 'zenhan_3f', grade_code)
    std_total = self._get_standard_total_time(keibajo_code, kyori, grade_code)
    
    if std_total and base_zenhan:
        speed_index = std_total - time_seconds
        adjusted_zenhan = base_zenhan - (speed_index * 0.3)
        return np.clip(adjusted_zenhan, 30.0, 45.0)
    
    # フォールバック
    if base_zenhan:
        return base_zenhan
    
    ratio = self._get_distance_ratio(kyori)
    return np.clip(time_seconds * ratio, self.MIN_TEN_3F, self.MAX_TEN_3F)
```

---

## 🎓 重要ポイント

### ✅ DO（推奨事項）

1. **実測値を優先**: `zenhan_3f > 0` の場合は必ず実測値を使用
2. **クラス別基準タイム**: 1201m以上では必ず `grade_code` を渡す
3. **距離判定**: 1200m以下と1201m以上で処理を分ける
4. **フォールバック**: 推定失敗時の代替処理を実装
5. **ログ記録**: 推定方法（method）を必ずログに記録

### ❌ DON'T（禁止事項）

1. **距離閾値を変更しない**: `1200m` と `1201m` の境界は厳守
2. **補正係数を変更しない**: `0.3` は理論文書に基づく最適値
3. **クリッピング範囲を変更しない**: `30.0-45.0秒` は実データ分析に基づく
4. **実測値を推定値で上書きしない**: 実測値がある場合は推定不要
5. **grade_code を省略しない**: クラス別基準タイムに必須

---

## 📝 チェックリスト

推定前半3Fタイムの実装時に確認すべき項目：

- [ ] `zenhan_3f_raw` の存在チェック（NULL/0.0）
- [ ] 距離判定（`kyori <= 1200` vs `kyori >= 1201`）
- [ ] `keibajo_code` の渡し忘れチェック
- [ ] `grade_code` の渡し忘れチェック（1201m以上）
- [ ] `kohan_3f_seconds` の存在チェック（1200m以下）
- [ ] 推定方法（method）のログ記録
- [ ] 異常値チェック（30.0-45.0秒の範囲外）
- [ ] テン指数計算への正しい値の受け渡し

---

## 🔗 関連ドキュメント

- **詳細版**: `docs/zenhan_3f_calculation_methods.md`
- **理論文書**: 会話履歴参照（`nar_ten3f_estimation_theory_v1.md`）
- **実装**: `core/ten_3f_estimator.py`, `core/index_calculator.py`
- **基準タイム**: `config/base_times.py`

---

**作成者**: Enable CEO & AI戦略家  
**最終更新**: 2026-01-10  
**Play to Win!** 🚀
