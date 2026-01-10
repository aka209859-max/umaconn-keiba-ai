# 上がり指数ペース補正値の最適化に関するディープリサーチ用プロンプト

## 📋 リサーチ目的
地方競馬（ダート）における上がり指数のペース補正値について、現行実装値と研究推奨値の妥当性を検証し、データ駆動型の最適値を導出する。

---

## 🎯 検証対象の補正値

### 現行実装値（core/index_calculator.py:304-309）
```python
def get_pace_correction_for_agari(pace_type: str) -> Tuple[float, str]:
    """ペース判定に基づく上がり指数の補正値"""
    if pace_type == 'H':  # ハイペース
        return -0.5, 'ハイペース → 後半余力減'
    elif pace_type == 'S':  # スローペース
        return +0.5, 'スローペース → 後半余力増'
    else:  # ミドルペース
        return 0.0, 'ミドルペース'
```

### 研究推奨値（地方競馬HQS指数システムの総合最適化）
```python
# 推奨値
H: -0.8秒  # ハイペース（前半速い）
S: +0.3秒  # スローペース（前半遅い）
M:  0.0秒  # ミドルペース
```

### 差分分析
| ペース | 現行 | 推奨 | 差分 | 影響方向 |
|--------|------|------|------|----------|
| H      | -0.5 | -0.8 | -0.3 | ハイペースを過小評価 |
| S      | +0.5 | +0.3 | -0.2 | スローペースを過大評価 |
| M      | 0.0  | 0.0  | 0.0  | 一致 |

---

## 🔬 検証すべき仮説

### 仮説1: ペースタイプと上がり3Fの相関
**問い**:
- ハイペース（H）のレースでは、後半3Fタイムが平均で何秒悪化するか？
- スローペース（S）のレースでは、後半3Fタイムが平均で何秒向上するか？

**データ要件**:
- 全14競馬場 × 主要距離（1200m, 1400m, 1600m, 1800m, 2000m）
- ペースタイプ別の後半3F平均タイム
- サンプル数: 各セグメント最低100レース以上

---

### 仮説2: 競馬場・距離別の補正値の最適化
**問い**:
- ペース補正値は全競馬場で一律でよいのか？
- 距離による補正値の調整は必要か？

**検証例**:
```
門別 1600m:
  - H: -0.7秒
  - S: +0.4秒

大井 1200m:
  - H: -0.9秒
  - S: +0.2秒
```

**データ要件**:
- 競馬場コード（30~55の14場）
- 距離別（1000m, 1200m, 1400m, 1600m, 1800m, 2000m）
- ペース判定（H/M/S）と後半3F実績タイム

---

### 仮説3: クラス別の影響
**問い**:
- E級（下位クラス）とA級（上位クラス）でペース補正値は異なるべきか？

**予想される傾向**:
- E級: ハイペースの影響が大きい（体力差が大きいため）
- A級: スローペースでも安定した上がり（体力レベルが高いため）

---

## 📊 必要なデータ抽出クエリ

### クエリ1: ペース別の後半3F平均タイム（競馬場×距離別）
```sql
SELECT 
    keibajo_code,
    kyori,
    pace_type,
    AVG(kohan_3f / 10.0) AS avg_kohan_3f_seconds,
    STDDEV(kohan_3f / 10.0) AS std_kohan_3f_seconds,
    COUNT(*) AS sample_count
FROM races
WHERE zenhan_3f > 0 AND kohan_3f > 0
GROUP BY keibajo_code, kyori, pace_type
HAVING sample_count >= 100
ORDER BY keibajo_code, kyori, pace_type;
```

### クエリ2: ペース補正の効果検証（勝率・回収率への影響）
```sql
SELECT 
    pace_type,
    AVG(CASE WHEN kakutei_chakujun = 1 THEN 1 ELSE 0 END) * 100 AS win_rate,
    AVG(CASE WHEN kakutei_chakujun <= 3 THEN tansho_odds ELSE 0 END) AS avg_roi,
    COUNT(*) AS total_races
FROM races
WHERE kohan_3f > 0
GROUP BY pace_type
ORDER BY pace_type;
```

### クエリ3: クラス別のペース影響度
```sql
SELECT 
    grade_code,
    pace_type,
    AVG(kohan_3f / 10.0) AS avg_kohan_3f_seconds,
    STDDEV(kohan_3f / 10.0) AS std_kohan_3f_seconds,
    COUNT(*) AS sample_count
FROM races
WHERE zenhan_3f > 0 AND kohan_3f > 0
GROUP BY grade_code, pace_type
HAVING sample_count >= 50
ORDER BY grade_code, pace_type;
```

---

## 🎯 最適値の導出アプローチ

### ステップ1: 基準値の算出
```python
# 全競馬場・全距離の平均的な補正値を算出
base_H_correction = avg_kohan_3f(H) - avg_kohan_3f(M)
base_S_correction = avg_kohan_3f(S) - avg_kohan_3f(M)
```

### ステップ2: 競馬場・距離別の調整係数
```python
# 競馬場ごとの特性を反映
for keibajo in [30, 35, 36, 40, 41, 42, 43, 44, 45, 46, 47, 50, 54, 55]:
    for kyori in [1000, 1200, 1400, 1600, 1800, 2000]:
        venue_H_correction = calculate_adjustment(keibajo, kyori, 'H')
        venue_S_correction = calculate_adjustment(keibajo, kyori, 'S')
```

### ステップ3: 回収率ベースの最終調整
```python
# 単勝回収率が最大化される補正値を逆算
optimal_H = optimize_for_roi(pace_type='H', target='tansho_roi')
optimal_S = optimize_for_roi(pace_type='S', target='tansho_roi')
```

---

## 📈 期待される成果物

### 1. ペース補正値の最適化レポート
**ファイル名**: `docs/agari_pace_correction_optimized.md`

**内容**:
- 現行値 vs 推奨値 vs データ導出値の比較
- 競馬場・距離別の補正値マトリックス
- 的中率・回収率への影響シミュレーション

### 2. 実装用コード
```python
# core/pace_correction_table.py
PACE_CORRECTION_TABLE = {
    'universal': {  # 全競馬場共通（デフォルト）
        'H': -0.8,
        'S': +0.3,
        'M': 0.0
    },
    'venue_specific': {  # 競馬場別（必要に応じて）
        '42': {  # 大井
            'H': -0.9,
            'S': +0.2,
            'M': 0.0
        },
        # ...
    }
}
```

---

## 🔍 ディープサーチの具体的な質問リスト

### WebSearch用プロンプト例

#### 検索1: 学術的根拠の調査
```
Query: "競馬 ペース補正 上がり3F ハイペース 疲労度 統計分析"
Focus: 学術論文やJRA公式データでのペース影響度
```

#### 検索2: 地方競馬特有の傾向
```
Query: "地方競馬 ダート ペース 上がり タイム 差 ハイペース スローペース"
Focus: 中央競馬との差異、ダート特有の傾向
```

#### 検索3: 海外事例の調査
```
Query: "horse racing pace adjustment late speed dirt"
Focus: 海外の競馬データ分析におけるペース補正手法
```

---

## ⚠️ 重要な注意点

### データ品質の確保
- 欠損値（zenhan_3f = 0, kohan_3f = 0）を除外
- 異常値（極端に速い/遅いタイム）のフィルタリング
- サンプル数が少ない組み合わせの扱い（最低100レース推奨）

### 過学習の防止
- 訓練データとテストデータの分割（80:20）
- クロスバリデーションの実施
- 補正値の適用範囲の制限（±1.5秒以内など）

### 実装の優先順位
1. **Phase 1**: 全競馬場共通の補正値を最適化（universal）
2. **Phase 2**: 主要競馬場（大井、川崎、船橋）の個別最適化
3. **Phase 3**: 距離別・クラス別の細分化

---

## 📝 CEO承認事項

**この調査を実施する前に確認が必要な事項**:

1. **データアクセス権限**: `umatabi.db`の使用可否
2. **計算リソース**: 全データを処理する時間（推定2-3時間）
3. **実装タイミング**: いつまでに最適化を完了させるか
4. **許容誤差**: 現行値からどの程度変更を許容するか（例: ±0.3秒以内）

---

## 🚀 次のアクション

**CEO、以下をご指示ください**:

- [ ] このプロンプトを使用してディープサーチを実施
- [ ] データベースからペース別タイムデータを抽出
- [ ] 統計分析を実行して最適値を算出
- [ ] 実装とA/Bテストの実施

**推定所要時間**:
- ディープサーチ: 30分
- データ抽出・分析: 2-3時間
- 実装・テスト: 1時間

**Play to Win!** 🏇💨
