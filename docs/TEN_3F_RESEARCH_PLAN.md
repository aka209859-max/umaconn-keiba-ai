# 🔍 前半3F（テン3F）逆算のための調査計画

## 📅 作成日時
2026-01-07 深夜

## 🎯 調査目的
現在持っている**地方競馬データ（NAR）から、映像を使わずに「前半3F（テン3F）のタイム」を逆算・推定する方法**を確立する。

---

## 📊 利用可能データ

### nvd_se（成績データ）テーブル
```
- soha_time (走破タイム): '1234' 形式（1分23秒4）
- kohan_3f (後半3F/上がり3F): '123' 形式（12.3秒）
- corner_1~4 (各コーナー通過順位): INTEGER
- kyori (距離): メートル単位
- baba_jotai_code (馬場状態)
- track_code (トラック種別)
```

### データ制約
- ❌ 映像データなし
- ❌ 200m刻みラップタイムなし
- ✅ 統計的推定が必要

---

## 🔍 調査プロンプト（3本並行実行）

### プロンプト A: 理論的逆算手法の調査
**目的**: 学術的・理論的根拠の確立

**調査項目**:
1. 走破タイムと上がり3Fから前半3Fを推定する理論的根拠
2. 距離別・馬場状態別の前半3F比率の統計モデル
3. コーナー通過順位を利用した前半ペース推定手法
4. 海外競馬（香港・韓国等）での類似事例
5. 機械学習を用いた前半3F予測モデルの先行研究

**情報源**:
- 学術論文・統計分析レポート
- 競馬予測システムの技術解説
- データサイエンス事例（Kaggle等）

**期待成果物**:
- 計算式: 前半3F = f(走破タイム, 上がり3F, 距離, ...)
- 統計的根拠（論文・実務事例）
- 実装可能なアルゴリズム

---

### プロンプト B: 実務的推定手法の調査
**目的**: 実務レベルで使える推定手法の発見

**調査項目**:
1. **距離別の前半3F比率の統計値**
   - 1200m: 前半3F = 走破タイムの何%？
   - 1400m: 前半3F = 走破タイムの何%？
   - 1800m: 前半3F = 走破タイムの何%？

2. **展開パターン別の前半ペース推定**
   - 逃げ馬（コーナー1-2で1-2番手）
   - 差し馬（コーナー1-2で中団以降）

3. **上がり3Fとの相関分析**
   - 前半3Fと上がり3Fの相関係数
   - 「前半速い → 上がり遅い」のトレードオフ関係

4. **機械学習モデルでの推定精度**
   - ランダムフォレスト・XGBoost等での予測精度
   - 特徴量の重要度（距離、馬場、コーナー順位等）

**情報源**:
- JRA-VAN Data Labの分析事例
- 地方競馬データ分析ブログ
- 競馬AI予測システムの技術解説

**期待成果物**:
- 距離別・馬場別の前半3F比率テーブル
- 展開パターン別の補正係数
- 実装可能な推定式

---

### プロンプト C: データ分析による実証的推定
**目的**: 実データから統計モデルを構築

**分析ステップ**:

#### 1. 探索的データ分析（EDA）
```sql
-- 距離別の平均走破タイム・上がり3F分析
SELECT 
    kyori,
    AVG(time_seconds) as avg_time,
    AVG(kohan_3f_seconds) as avg_kohan_3f,
    AVG(time_seconds - kohan_3f_seconds) as avg_early_pace,
    COUNT(*) as sample_count
FROM temp_race_data
GROUP BY kyori
ORDER BY kyori;
```

#### 2. 前半3F比率の算出
```sql
-- 仮定: 前半3F ≈ (走破タイム - 上がり3F) × 補正係数
SELECT 
    kyori,
    AVG((time_seconds - kohan_3f_seconds) / time_seconds) as early_pace_ratio,
    STDDEV((time_seconds - kohan_3f_seconds) / time_seconds) as ratio_std
FROM temp_race_data
WHERE time_seconds > 0 AND kohan_3f_seconds > 0
GROUP BY kyori;
```

#### 3. 展開パターン別分析
```sql
-- 逃げ馬の前半ペース分析
SELECT 
    kyori,
    AVG(time_seconds - kohan_3f_seconds) as avg_early_pace,
    COUNT(*) as sample_count
FROM temp_race_data
WHERE corner_1 <= 2 AND corner_2 <= 2  -- 逃げ・先行馬
GROUP BY kyori;
```

#### 4. 回帰モデル構築
```python
# Pythonでの実装例
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor

# 特徴量: 走破タイム, 上がり3F, 距離, 馬場状態, コーナー順位
X = df[['time_seconds', 'kohan_3f_seconds', 'kyori', 'baba_code', 'corner_1', 'corner_2']]

# 目的変数: 前半3F（仮想値 = time - kohan_3f - 中間区間推定値）
y = df['estimated_ten_3f']

# モデル訓練
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X, y)

# 特徴量の重要度
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)
```

**期待成果物**:
- 前半3F推定の計算式
- 距離別・馬場別の補正係数テーブル
- 推定精度の評価指標（RMSE, MAE）

---

## 🎯 活用方針（Phase 2への統合）

### Phase 2: HQS指数への統合計画

#### 新規実装項目

1. **前半3F推定関数の追加**
```python
def estimate_ten_3f(
    time_seconds: float,
    kohan_3f_seconds: float,
    kyori: int,
    baba_code: str,
    corner_1: int,
    corner_2: int
) -> float:
    """
    前半3F（テン3F）を推定する
    
    Returns:
        推定前半3Fタイム（秒）
    """
    # 調査結果に基づく実装
    # 例: 距離別補正係数を使用
    pass
```

2. **HQS指数への統合**
```python
# 前走の前半3Fを取得
prev_ten_3f = estimate_ten_3f(
    prev_time, prev_kohan_3f, prev_kyori, 
    prev_baba, prev_corner_1, prev_corner_2
)

# 今回の前半3F推定値
current_ten_3f_estimated = estimate_ten_3f(...)

# 前半ペース補正
ten_3f_correction = calculate_pace_correction(
    prev_ten_3f, current_ten_3f_estimated
)

# HQS上がり指数へ統合
agari_index = base_agari_index + ten_3f_correction
```

3. **新規ファクターの追加**
```python
# F34: 前半3F推定値
factor_34_ten_3f_estimated = estimate_ten_3f(...)

# F35: 前半ペース変化率
factor_35_pace_change = (current_ten_3f - prev_ten_3f) / prev_ten_3f
```

---

## 📊 期待効果

### Phase 2統合後のHQS指数の充実度
- **現状**: 83%（前走不利補正のみ）
- **統合後**: 91-95%（前半3F推定値 + 前走不利補正）

### 予測精度の向上（見込み）
- **出遅れ検知精度**: 85% → 90%（前半3F実測値での検証）
- **HQS指数の予測精度**: +2-3%の向上
- **ファクター分析の深度**: 33ファクター → 35ファクター

---

## 🚀 次のアクション（CEOが起床後）

### ステップ1: 調査結果の共有
- [ ] プロンプトA（理論調査）の結果を報告
- [ ] プロンプトB（実務調査）の結果を報告
- [ ] プロンプトC（データ分析）の結果を報告

### ステップ2: Phase 2実装開始
- [ ] 前半3F推定関数の実装（2時間）
- [ ] HQS指数への統合（2時間）
- [ ] 新規ファクター追加（1時間）
- [ ] テスト・検証（1時間）

### ステップ3: GitHub更新
- [ ] 実装コードのコミット
- [ ] ドキュメント更新
- [ ] プッシュ（ローカルPCから）

---

## 💡 重要な前提条件の整理

### 現在の「前半ペース指標」の問題点
```
❌ 誤解を招く命名: 「テン3F相当タイム」
✅ 正確な定義: 前半ペース指標 = 走破タイム - 上がり3F
```

### 計算式の真の意味
```
ten_equivalent = 走破タイム - 上がり3F
               = 前半3F + 中間区間 + (残り - 上がり3F)
               ≠ 純粋な前半3F
```

### 今回の調査で解決すべき課題
```
【課題】
現在の ten_equivalent は「前半〜中盤の合計時間」であり、
純粋な「前半3F」ではない。

【解決策】
1. 理論的根拠の確立（プロンプトA）
2. 実務的推定手法の発見（プロンプトB）
3. 統計モデルの構築（プロンプトC）

【ゴール】
純粋な「前半3F」を推定し、HQS指数の精度向上に貢献する。
```

---

## 🎯 成功基準

### Phase 2完了の定義
- [ ] 前半3F推定関数の実装完了
- [ ] HQS指数への統合完了
- [ ] 推定精度の評価（RMSE ≤ 1.0秒）
- [ ] 新規ファクター（F34-F35）の追加完了
- [ ] ドキュメント更新完了
- [ ] GitHub更新完了

### 推定精度の目標
- **Tier 1（最高）**: RMSE ≤ 0.5秒（±0.5秒以内）
- **Tier 2（良好）**: RMSE ≤ 1.0秒（±1.0秒以内）
- **Tier 3（実用）**: RMSE ≤ 1.5秒（±1.5秒以内）

---

## 📝 備考

### CEOへのメッセージ
```
おやすみなさい、CEO！

調査結果が出たら共有してください。
忘れないようにこのドキュメントを作成し、
Gitにコミットしておきました。

Phase 2の実装準備は整っています。
起床後、調査結果を基に即座に実装開始できます。

Play to Win. 10x Mindset. 🚀
```

---

**作成者**: AI戦略家（NAR-AI-YOSO開発チーム）  
**最終更新**: 2026-01-07 深夜  
**ステータス**: CEO調査待ち → Phase 2実装予定
