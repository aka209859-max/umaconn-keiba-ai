# 指数正規化実装プラン：RankGauss方式の導入

**作成日**: 2026-01-10  
**作成者**: AI戦略家（CSO兼クリエイティブディレクター）  
**目的**: 指数の極端な偏りを解消し、情報損失を防ぐ統計的正規化手法の実装

---

## 📊 ディープサーチ結果の要約

### 🚨 現状の問題

1. **70%の張り付き = 情報の壊滅的な損失**
   - テン指数: 69.42%が -100～-95 に集中
   - 位置指数: 58.43%が 0～5 に集中
   - 単純クリップ処理により、異なる能力の馬が同一評価になる

2. **AIへの悪影響**
   - 勾配消失（Vanishing Gradient）
   - 全出走馬の過半数の能力差を学習できない
   - 穴馬の発見が困難

3. **地方競馬データの特異性**
   - 右側（優秀側）: 薄いテール（物理的限界あり）
   - 左側（劣悪側）: ヘヴィーテール（無制限に遅くなる）
   - 統計的には: べき乗則（Power Law）に近い

---

## ✅ 推奨される解決策：RankGauss（Quantile Transformation）

### 🏆 これが最適解（Best Practice）

**理論的根拠**:
- 指数の絶対値ではなく、**集団内での位置（ランク）**に基づいて正規分布に再配置
- 下位70%のデータを詳細に分解し、情報の損失を完全に回避
- 正規分布化により、ニューラルネットワークの学習安定性が向上
- scikit-learn の `QuantileTransformer` で実装可能

**利点**:
1. ✅ 情報損失ゼロ（単調増加関数による変換）
2. ✅ 外れ値に頑健
3. ✅ 順序を完全に保持
4. ✅ 実装が容易（scikit-learn）
5. ✅ 学術的に広く認められた手法

---

## 🔧 実装方針

### Phase 1: データ収集と分析（完了）

**現状**:
- ✅ 4指数の分布確認完了
- ✅ 極端な偏りの定量的把握
- ✅ ディープサーチで解決策特定

---

### Phase 2: RankGauss正規化の実装

#### 2.1 新規モジュール作成

**ファイル**: `core/index_normalizer.py`

**機能**:
1. **学習フェーズ**: 過去データから分位点を学習
2. **変換フェーズ**: 新データを正規分布に変換
3. **スケーリング**: 4σ基準で [-100, 100] にマッピング

#### 2.2 実装コード（概要）

```python
from sklearn.preprocessing import QuantileTransformer
import numpy as np
import joblib

class RacingIndexNormalizer:
    """
    競馬指数の統計的正規化クラス
    
    RankGauss (Quantile Transformation) による正規化:
    - 70%の張り付きを解消
    - 情報損失を完全に回避
    - 正規分布化でAI学習を安定化
    """
    
    def __init__(self, target_range=(-100, 100), sigma_cap=4.0):
        self.target_range = target_range
        self.sigma_cap = sigma_cap
        self.qt = QuantileTransformer(
            n_quantiles=2000,           # 詳細な分解能
            output_distribution='normal',
            random_state=42,
            subsample=1000000           # 大規模データ対応
        )
        self.scale_factor = target_range[1] / sigma_cap
    
    def fit(self, X: np.ndarray) -> 'RacingIndexNormalizer':
        """
        過去データを用いて分布を学習
        
        Args:
            X: shape (n_samples, 1) の指数データ
        
        Returns:
            self
        """
        self.qt.fit(X.reshape(-1, 1))
        return self
    
    def transform(self, X: np.ndarray) -> np.ndarray:
        """
        指数を正規化
        
        Args:
            X: shape (n_samples,) or (n_samples, 1) の指数データ
        
        Returns:
            正規化済み指数 [-100, 100]
        """
        # Step 1: 正規分布へ変換 Z ~ N(0, 1)
        z_scores = self.qt.transform(X.reshape(-1, 1))
        
        # Step 2: 4σ = 100 点でスケーリング
        scaled_scores = z_scores * self.scale_factor
        
        # Step 3: 最終範囲制限
        final_scores = np.clip(scaled_scores, *self.target_range)
        
        return final_scores.flatten()
    
    def fit_transform(self, X: np.ndarray) -> np.ndarray:
        """fit と transform を一度に実行"""
        return self.fit(X).transform(X)
    
    def save(self, filepath: str):
        """学習済みモデルを保存"""
        joblib.dump(self, filepath)
    
    @classmethod
    def load(cls, filepath: str) -> 'RacingIndexNormalizer':
        """学習済みモデルを読み込み"""
        return joblib.load(filepath)
```

---

#### 2.3 学習データの準備

**スクリプト**: `scripts/train_index_normalizers.py`

**処理内容**:
1. データベースから過去2年分の指数データを取得
2. 各指数ごとに RankGauss 正規化器を学習
3. 学習済みモデルを保存（`models/normalizers/` ディレクトリ）

**期待される学習データサイズ**:
- 総レース数: 約50,000レース
- 総出走頭数: 約500,000頭
- 4指数 × 500,000頭 = 2,000,000データポイント

---

### Phase 3: 既存コードへの統合

#### 3.1 index_calculator.py への組み込み

**修正箇所**: `core/index_calculator.py`

**変更内容**:
```python
# 現在の実装
ten_index = (base_time - zenhan_3f) + corrections
ten_index = max(-100, min(100, ten_index))  # ❌ 単純クリップ

# 新しい実装
ten_index_raw = (base_time - zenhan_3f) + corrections
ten_index = ten_normalizer.transform([ten_index_raw])[0]  # ✅ RankGauss
```

**注意点**:
- 学習済み正規化器を事前にロード
- 各指数ごとに異なる正規化器を使用
- 変換後も [-100, 100] の範囲を保証

---

#### 3.2 正規化器の管理

**ファイル構成**:
```
models/
└── normalizers/
    ├── ten_index_normalizer.pkl          # テン指数用
    ├── agari_index_normalizer.pkl        # 上がり指数用
    ├── position_index_normalizer.pkl     # 位置指数用
    └── pace_index_normalizer.pkl         # ペース指数用
```

---

### Phase 4: 検証とテスト

#### 4.1 分布の確認

**スクリプト**: `scripts/validate_normalized_distribution.py`

**検証項目**:
1. ✅ 変換後の分布が正規分布に近いか（Shapiro-Wilk検定）
2. ✅ -100 や +100 への偏りが解消されたか
3. ✅ 順序が保持されているか（単調増加性）
4. ✅ 予測精度への影響（的中率・回収率）

---

#### 4.2 予測精度の比較

| 指標 | 現在（単純クリップ） | RankGauss正規化後 | 改善 |
|------|-------------------|------------------|------|
| 単勝的中率 | 22.77% | **??.??%** | +??.??% |
| 複勝的中率 | 63.44% | **??.??%** | +??.??% |
| 単勝回収率 | 68.30% | **??.??%** | +??.??% |
| 複勝回収率 | 95.16% | **??.??%** | +??.??% |

**期待される効果**:
- 穴馬の発見精度向上（下位馬の能力差を学習可能に）
- レース展開の予測精度向上
- AIモデルの学習安定性向上

---

## 🎯 実装スケジュール

### Week 1: 準備とプロトタイプ実装
- [ ] `core/index_normalizer.py` 作成
- [ ] `scripts/train_index_normalizers.py` 作成
- [ ] 小規模データでのテスト（1,000レース）

### Week 2: 大規模学習と統合
- [ ] 全データでの正規化器学習（500,000頭）
- [ ] `core/index_calculator.py` への統合
- [ ] 単体テスト作成

### Week 3: 検証と評価
- [ ] 分布の確認（正規分布化の検証）
- [ ] 予測精度の比較（的中率・回収率）
- [ ] パフォーマンステスト

### Week 4: 本番適用
- [ ] 本番環境への適用
- [ ] モニタリング体制構築
- [ ] ドキュメント整備

---

## 📝 技術的な注意点

### 1. 学習データの選定

**期間**: 2023-10-13 ～ 2025-12-31（大井砂入れ替え後）

**理由**:
- 競馬場改修前後でタイム傾向が変わる
- 最新データで学習することで、現在のレース環境を反映

### 2. 正規化器の更新頻度

**推奨**: 3ヶ月ごと

**理由**:
- 競馬場の馬場状態が季節で変動
- 新しいデータを取り込むことで精度維持

### 3. 未知の値への対応

**問題**: 学習データの範囲外の値が来た場合

**解決策**:
- QuantileTransformer は自動的に最小値/最大値に張り付く
- 競馬では「過去最低」を下回ることは稀なので実用上問題なし

### 4. 計算コストの考慮

**変換コスト**: O(log N)（二分探索による分位点検索）

**実用性**: 1頭あたり 0.1ms 以下（十分高速）

---

## 🔬 代替案との比較

| 手法 | 情報保持 | 外れ値対応 | 実装難易度 | 推奨度 |
|------|---------|-----------|-----------|--------|
| **RankGauss** | ✅ 完全 | ✅ 頑健 | ✅ 容易 | 🏆 **最推奨** |
| Robust Scaler | ⚠️ 良好 | ✅ 頑健 | ✅ 容易 | ⭐ 次点 |
| Sigmoid/Tanh | ⚠️ 良好 | ⚠️ パラメータ調整必要 | ⚠️ やや複雑 | ⭐ 次点 |
| 単純クリップ | ❌ 損失大 | ❌ 対応不可 | ✅ 容易 | ❌ 非推奨 |

---

## 📚 参考文献

1. **ディープサーチレポート**: `docs/deep_search_prompt_index_distribution.md`
2. **ディープサーチ結果**: `地方競馬AIにおける指数分布の統計的正規化と極値処理に関する包括的研究.md`
3. **scikit-learn QuantileTransformer**: https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.QuantileTransformer.html
4. **RankGauss in Kaggle**: Widely used in top solutions for tabular data competitions

---

## 🎯 期待される効果

### 1. 情報損失の完全回避
- 現在: 70%のデータが -100 に集中 → 能力差が識別不可
- 変換後: 全データが正規分布に展開 → 微細な能力差も識別可能

### 2. AI学習の安定化
- 勾配消失の解消
- 学習速度の向上
- モデルの収束性改善

### 3. 予測精度の向上
- 穴馬の発見精度向上（期待: +3～5%）
- レース展開の予測精度向上
- 回収率の改善（期待: +5～10%）

---

## 🚀 実装開始の承認依頼

**CEO、この実装プランで進めてよろしいですか？**

以下の点をご確認ください：

1. ✅ RankGauss（Quantile Transformation）方式で実装
2. ✅ scikit-learn の `QuantileTransformer` を使用
3. ✅ 4指数それぞれに専用の正規化器を学習
4. ✅ Phase 1～4 の4週間スケジュールで実施

**承認いただければ、すぐに実装を開始します！**

**Play to Win! 🏆**
