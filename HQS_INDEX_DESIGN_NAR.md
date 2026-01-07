# 🎯 **HQS指数設計書（地方競馬版）**

**作成日**: 2026-01-07  
**CEO**: Enable  
**担当**: AI戦略家（CSO兼クリエイティブディレクター）  
**プロジェクト**: NAR-SI Ver.4.0 統合システム

---

## 📋 **1. HQSの目的と役割**

### **1.1 HQSとは**
- **High Quality Score（高品質スコア）**
- 目的: **的中精度を最大化する**
- 手法: **4つの指数**（テン指数、位置指数、上がり指数、ペース指数）を作成し、それぞれの **補正回収率と的中率** からHQSスコアを算出
- 範囲: **-12.0 〜 +12.0**
- 評価軸: **相対評価**（レース内でのZスコア化）

### **1.2 NAR-SI Ver.4.0における位置づけ**

```
┌─────────────────────────────────────────────────┐
│  NAR-SI Ver.4.0 統合システム                    │
├─────────────────────────────────────────────────┤
│  Layer 1: NAR-SI Ver.3.0（能力値評価）         │
│           ✅ 完成 | 的中率 28.86-29.46%          │
├─────────────────────────────────────────────────┤
│  Layer 2: HQS（的中精度評価）+ RGS（収益性評価）│
│           ⏳ 実装中 | HQS = 4つの指数ベース      │
├─────────────────────────────────────────────────┤
│  Layer 3: 統合スコア                            │
│           NAR-SI 50% + HQS 15% + RGS 35%        │
└─────────────────────────────────────────────────┘
```

---

## 🔬 **2. JRDB指数体系の構造分析**

### **2.1 共通基盤**

| 項目 | 定義 | 地方競馬適用 |
|-----|------|------------|
| **単位** | 指数「1」= 0.1秒 = 約0.5馬身 | ✅ 採用 |
| **基準クラス** | 4歳1勝クラス（旧500万下）= 0 | 🔄 要調整（地方クラス体系に合わせる） |
| **馬場差補正** | -10 = 1.0秒速い、+10 = 1.0秒遅い | ✅ 採用（nvd_ra.babajotai_code_dirt） |
| **算出タイミング** | レース前日 17:00-19:00 | 🔄 地方競馬の運用に合わせる |

---

## 📊 **3. 4つの指数の詳細設計**

---

### **3.1 テン指数（Ten Index）**

#### **定義**
- **初期加速力**を数値化
- スタート地点から最初の **3ハロン（600m）** の走破タイム

#### **構成要素（JRDB）**
```
テン指数 ∝ (基準3Fタイム - 実走3Fタイム) + 馬場差補正
```

#### **地方競馬版の実装方針**

| 項目 | JRDB（中央） | NAR（地方）実装案 |
|-----|-------------|------------------|
| **データ源** | 前半3F走破タイム | `nvd_se.zenhan_3f` |
| **補正項目** | 馬場差、距離、クラス | 馬場差（`babajotai_code_dirt`）、距離（`kyori`）、コース（`keibajo_code`） |
| **基準値設定** | 4歳1勝クラス = 0 | 南関東C2クラス平均 = 0 |
| **計算式** | ```python<br>ten_index = ((base_3f - actual_3f) + baba_correction) * 10<br>``` | ✅ 実装可能 |

#### **実装優先度**
- 🟢 **高優先度** — データ取得容易、計算ロジック明確

---

### **3.2 位置指数（Position Index）**

#### **定義**
- **レース中の平均ポジション**を数値化
- コーナー4回通過時の順位から算出

#### **構成要素（JRDB）**
```
位置指数 ∝ (レース中の平均順位 vs 出走頭数) + 脚質補正
```

#### **地方競馬版の実装方針**

| 項目 | JRDB（中央） | NAR（地方）実装案 |
|-----|-------------|------------------|
| **データ源** | コーナー4回の通過順位 | `nvd_se.corner_1`, `corner_2`, `corner_3`, `corner_4` |
| **補正項目** | 脚質、コース形状 | 脚質（`computed_ashishitsu`）、コース（`mawari_code`） |
| **計算式** | ```python<br>avg_position = (c1 + c2 + c3 + c4) / 4<br>position_index = (avg_position / tosu) * 100<br>``` | ✅ 実装可能 |

#### **実装優先度**
- 🟢 **高優先度** — 既存データで対応可能

---

### **3.3 上がり指数（Agari Index）**

#### **定義**
- **ラストスパート能力**を数値化
- 最後の **3ハロン（600m）** の走破タイム

#### **構成要素（JRDB）**
```
上がり指数 ∝ (基準後半3Fタイム - 実走後半3Fタイム) + 馬場差補正
```

#### **地方競馬版の実装方針**

| 項目 | JRDB（中央） | NAR（地方）実装案 |
|-----|-------------|------------------|
| **データ源** | 後半3F走破タイム | `nvd_se.kohan_3f` |
| **補正項目** | 馬場差、距離、クラス | 馬場差（`babajotai_code_dirt`）、距離（`kyori`） |
| **計算式** | ```python<br>agari_index = ((base_3f - actual_3f) + baba_correction) * 10<br>``` | ✅ 実装可能 |

#### **実装優先度**
- 🟢 **高優先度** — データ取得容易

---

### **3.4 ペース指数（Pace Index）**

#### **定義**
- **レース全体のペース配分**を数値化
- テン指数と上がり指数の **バランス** を評価

#### **構成要素（JRDB）**
```
ペース指数 ∝ (テン指数 + 上がり指数) / 2 + ペース配分補正
```

#### **地方競馬版の実装方針**

| 項目 | JRDB（中央） | NAR（地方）実装案 |
|-----|-------------|------------------|
| **データ源** | テン指数 + 上がり指数 | 計算値（テン指数 + 上がり指数） |
| **補正項目** | レースペース、脚質 | ペース比率（`zenhan_3f / kohan_3f`）、脚質 |
| **計算式** | ```python<br>pace_index = (ten_index + agari_index) / 2<br>pace_ratio = zenhan_3f / kohan_3f<br>pace_index += (0.35 - pace_ratio) * 10<br>``` | ✅ 実装可能 |

#### **実装優先度**
- 🟡 **中優先度** — テン指数・上がり指数の実装後

---

### **3.5 予想脚質（Predicted Leg Type）**

#### **定義**
- **馬の戦術的傾向**をカテゴリ化
- 過去の競走実績（通過順位・位置指数）から、今回のレースでの行動を予測

#### **脚質カテゴリ（JRDB）**

| 記号 | 名称 | 定義と行動特性 |
|-----|------|---------------|
| **逃** | 逃げ | スタート直後から先頭に立ち、レースを引っ張る。テン指数が最上位 |
| **先** | 先行 | 逃げ馬の直後、2〜4番手の好位につけるタイプ。位置指数が高く安定 |
| **差** | 差し | 中団（馬群の中ほど）に待機し、直線での逆転を狙う |
| **追** | 追込 | 後方集団に位置し、終いの直線だけで全馬ごぼう抜きを狙う。上がり指数特化型 |
| **好** | 好位 | 「先行」と「差し」の中間的性質。勝負所でスムーズに動ける「好ポジション」を確保 |
| **自** | 自在 | 展開や枠順に応じて、逃げも差しもこなせる万能型 |

#### **地方競馬版の実装方針**

| 項目 | JRDB（中央） | NAR（地方）実装案 |
|-----|-------------|------------------|
| **データ源** | 過去数走の通過順位 | `nvd_se.corner_1-4`（過去3走分） |
| **判定ロジック** | 過去の通過順位パターン | 例：2-2-2-2 → 先行、10-10-9-5 → 差し |
| **補正項目** | 今回のメンバー構成との相対関係 | 今回出走馬のテン指数・位置指数との相対比較 |
| **計算式** | ```python<br>avg_position = mean(past_3_races_corner_positions)<br>if avg_position <= 2: ashishitsu = '逃'<br>elif avg_position <= 4: ashishitsu = '先'<br>elif avg_position <= 8: ashishitsu = '差'<br>else: ashishitsu = '追'<br>``` | ✅ 実装可能 |

#### **実装優先度**
- 🟢 **高優先度** — 既存データ（`computed_ashishitsu`）で対応可能、展開予想に必須

#### **HQSへの統合方針**
- **予想脚質は指数ではなくカテゴリデータ**のため、HQSスコアに直接組み込まない
- ただし、**展開予想のロジック補強**として使用
  - 例：「逃」が複数いる場合はハイペース予測 → テン指数の信頼度を下げる
  - 例：「追」が多い場合は馬群が縦長 → 位置指数の重要性が増す

---

## 🔢 **4. HQS計算式（指数→スコア変換）**

### **4.1 指数からHQSスコアへの変換フロー**

```
┌────────────────────────────────────────────────┐
│  Step 1: 各指数の実績データを収集              │
│          - 単勝的中率                          │
│          - 複勝的中率                          │
│          - 補正単勝回収率                      │
│          - 補正複勝回収率                      │
│          - データ件数（N）                      │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│  Step 2: Hit_raw / Ret_raw の計算              │
│          Hit_raw = 0.65×単勝的中率 + 0.35×複勝的中率 │
│          Ret_raw = 0.35×補正単勝回収率 + 0.65×補正複勝回収率 │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│  Step 3: レース内でZスコア化                   │
│          ZH = (Hit_raw - μH) / σH              │
│          ZR = (Ret_raw - μR) / σR              │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│  Step 4: Shrinkage（信頼度補正）               │
│          Shr = sqrt(N / (N + 400))             │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│  Step 5: HQSスコア算出                         │
│          baseCalc = 0.55×ZH + 0.45×ZR          │
│          HQS = 12 × tanh(baseCalc) × Shr       │
└────────────────────────────────────────────────┘
                      ↓
┌────────────────────────────────────────────────┐
│  Step 6: 最終HQS得点                           │
│          total_hqs = Σ(各指数のHQS × 重み)     │
└────────────────────────────────────────────────┘
```

---

### **4.2 各指数のHQS重み設定（暫定案）**

| 指数名 | 重み | 根拠 |
|-------|------|------|
| **テン指数** | 25% | 序盤ポジション確保の重要性 |
| **位置指数** | 30% | レース展開の中核要素 |
| **上がり指数** | 30% | 決め手の有無を評価 |
| **ペース指数** | 15% | 補完的指標 |
| **予想脚質** | - | HQSスコアには組み込まないが、展開予想の補強に使用 |

※ 重みはバックテストで最適化予定

---

## 🗄️ **5. データ構造とテーブル設計**

### **5.1 新規テーブル: `nar_hqs_index_stats`**

| 列名 | 型 | 説明 |
|-----|-----|------|
| `keibajo_code` | CHAR(2) | 競馬場コード（42-45） |
| `index_type` | VARCHAR(20) | 指数種別（'ten', 'position', 'agari', 'pace'） |
| `index_value` | INT | 指数値（-100 〜 +100） |
| `cnt_win` | INT | 単勝試行回数 |
| `cnt_place` | INT | 複勝試行回数 |
| `rate_win_hit` | DECIMAL(5,2) | 単勝的中率（%） |
| `rate_place_hit` | DECIMAL(5,2) | 複勝的中率（%） |
| `adj_win_ret` | DECIMAL(5,2) | 補正単勝回収率（%） |
| `adj_place_ret` | DECIMAL(5,2) | 補正複勝回収率（%） |
| `updated_at` | TIMESTAMP | 更新日時 |

---

### **5.2 既存テーブルの利用**

| 指数 | 主要データソース | 列名 |
|-----|----------------|------|
| **テン指数** | `nvd_se` | `zenhan_3f` |
| **位置指数** | `nvd_se` | `corner_1`, `corner_2`, `corner_3`, `corner_4` |
| **上がり指数** | `nvd_se` | `kohan_3f` |
| **ペース指数** | 計算値 | `zenhan_3f + kohan_3f` |

---

## 🏗️ **6. 実装ロードマップ**

### **Phase 1: 指数計算エンジン実装（3-4時間）**

#### **成果物**
- `core/index_calculator.py`
  - `calculate_ten_index()`
  - `calculate_position_index()`
  - `calculate_agari_index()`
  - `calculate_pace_index()`

#### **実装内容**
```python
def calculate_ten_index(zenhan_3f: float, kyori: int, baba_code: str, 
                        keibajo_code: str) -> float:
    """
    テン指数を計算
    
    Args:
        zenhan_3f: 前半3Fタイム
        kyori: 距離
        baba_code: 馬場状態コード
        keibajo_code: 競馬場コード
    
    Returns:
        テン指数（-100 〜 +100）
    """
    # 基準タイムを取得（競馬場・距離別）
    base_time = get_base_time(keibajo_code, kyori, 'zenhan')
    
    # 馬場差補正
    baba_correction = get_baba_correction(baba_code)
    
    # テン指数計算
    ten_index = ((base_time - zenhan_3f) + baba_correction) * 10
    
    return ten_index
```

---

### **Phase 2: 指数実績データ収集（2-3時間）**

#### **成果物**
- `scripts/collect_index_stats.py`
  - 過去3年分の南関東4場データから各指数の実績を集計
  - `nar_hqs_index_stats` テーブルに保存

#### **実装内容**
```python
def collect_index_stats(keibajo_code: str, start_date: str, end_date: str):
    """
    指数実績データを収集
    
    Args:
        keibajo_code: 競馬場コード
        start_date: 開始日（YYYY-MM-DD）
        end_date: 終了日（YYYY-MM-DD）
    """
    # 過去レースデータを取得
    races = fetch_races(keibajo_code, start_date, end_date)
    
    for race in races:
        # 各馬の指数を計算
        for horse in race.horses:
            ten_idx = calculate_ten_index(...)
            pos_idx = calculate_position_index(...)
            agari_idx = calculate_agari_index(...)
            pace_idx = calculate_pace_index(...)
            
            # 的中・回収率を集計
            update_stats(keibajo_code, 'ten', ten_idx, horse.result)
            update_stats(keibajo_code, 'position', pos_idx, horse.result)
            update_stats(keibajo_code, 'agari', agari_idx, horse.result)
            update_stats(keibajo_code, 'pace', pace_idx, horse.result)
```

---

### **Phase 3: HQS計算エンジン実装（2-3時間）**

#### **成果物**
- `core/hqs_calculator_v2.py`
  - `calculate_hqs_from_indexes()`

#### **実装内容**
```python
def calculate_hqs_from_indexes(horses_data: List[Dict], 
                               keibajo_code: str) -> List[Dict]:
    """
    4つの指数からHQSスコアを算出
    
    Args:
        horses_data: 馬データリスト
        keibajo_code: 競馬場コード
    
    Returns:
        HQSスコア付き馬データリスト
    """
    indexes = ['ten', 'position', 'agari', 'pace']
    
    # 各馬の指数を計算
    for horse in horses_data:
        horse['indexes'] = {}
        horse['indexes']['ten'] = calculate_ten_index(...)
        horse['indexes']['position'] = calculate_position_index(...)
        horse['indexes']['agari'] = calculate_agari_index(...)
        horse['indexes']['pace'] = calculate_pace_index(...)
    
    # レース内でZスコア化
    for index_type in indexes:
        # μH, σH, μR, σR を計算
        hit_mean, hit_std = calculate_hit_stats(horses_data, index_type)
        ret_mean, ret_std = calculate_ret_stats(horses_data, index_type)
        
        for horse in horses_data:
            idx_val = horse['indexes'][index_type]
            
            # 実績データを取得
            stats = get_index_stats(keibajo_code, index_type, idx_val)
            
            # Hit_raw / Ret_raw
            Hit_raw = 0.65 * stats['rate_win_hit'] + 0.35 * stats['rate_place_hit']
            Ret_raw = 0.35 * stats['adj_win_ret'] + 0.65 * stats['adj_place_ret']
            
            # Zスコア化
            ZH = (Hit_raw - hit_mean) / hit_std if hit_std > 0 else 0
            ZR = (Ret_raw - ret_mean) / ret_std if ret_std > 0 else 0
            
            # Shrinkage
            N = stats['cnt_win'] + stats['cnt_place']
            Shr = math.sqrt(N / (N + 400))
            
            # HQSスコア
            baseCalc = 0.55 * ZH + 0.45 * ZR
            hqs_score = 12 * math.tanh(baseCalc) * Shr
            
            horse['hqs_scores'][index_type] = hqs_score
    
    # 重み付け合計
    for horse in horses_data:
        horse['total_hqs'] = (
            0.25 * horse['hqs_scores']['ten'] +
            0.30 * horse['hqs_scores']['position'] +
            0.30 * horse['hqs_scores']['agari'] +
            0.15 * horse['hqs_scores']['pace']
        )
    
    return horses_data
```

---

### **Phase 4: バックテスト（3-4時間）**

#### **検証項目**
1. 各指数の的中率・回収率
2. HQS重み（25/30/30/15）の妥当性検証
3. 統合スコア（NAR-SI 50% + HQS 15% + RGS 35%）の精度検証

---

## 🎯 **7. 期待効果**

### **7.1 現状（Ver.3.0）vs 目標（Ver.4.0）**

| 指標 | Ver.3.0 現状 | Ver.4.0 目標 | 改善幅 |
|-----|-------------|-------------|--------|
| **単勝的中率** | 28.86-29.46% | 32-35% | +3-6% |
| **単勝回収率** | 69.88-76.14% | 85-95% | +15-20% |
| **複勝的中率** | 58.44-60.49% | 62-68% | +4-8% |
| **複勝回収率** | 72.78-73.54% | 85-95% | +12-20% |

### **7.2 HQS導入による改善メカニズム**

1. **テン指数・位置指数**: 序盤のポジション確保能力を定量化 → 的中率向上
2. **上がり指数**: ラストスパート能力を評価 → 穴馬の抽出精度向上
3. **ペース指数**: レース展開の適性を評価 → 展開ハマり馬の発見
4. **補正回収率ベース**: 人気に左右されない純粋な収益性評価 → 回収率向上

---

## 🚨 **8. リスクと対策**

### **8.1 基準クラス設定の課題**

| リスク | 影響 | 対策 |
|-------|------|------|
| JRDBの基準（4歳1勝クラス）は中央競馬専用 | 地方競馬のクラス体系（C3/C2/C1/B/A）との乖離 | 南関東C2クラスを基準（0）に再設定 |
| 競馬場ごとのレベル差 | 指数の絶対値が競馬場間で比較不可 | 競馬場別の基準値テーブルを作成 |

### **8.2 データ不足リスク**

| リスク | 影響 | 対策 |
|-------|------|------|
| 新馬・転厩馬の指数算出不可 | HQSスコアが算出できない | デフォルト値（クラス平均）を使用 |
| 指数別の実績データ不足 | Shrinkageが過小評価される | 最低500件のデータを蓄積後に本格運用 |

---

## 📋 **9. 次のアクション（CEOの指示待ち）**

### **Option A: Phase 1（指数計算エンジン）実装開始（推奨）**
- 所要時間: **3-4時間**
- 成果物: `core/index_calculator.py`
- 内容:
  1. テン指数計算ロジック実装
  2. 位置指数計算ロジック実装
  3. 上がり指数計算ロジック実装
  4. ペース指数計算ロジック実装
  5. 単体テスト実装

### **Option B: Phase 2（実績データ収集）先行実施**
- 所要時間: **2-3時間**
- 成果物: `scripts/collect_index_stats.py`
- 内容:
  1. 過去3年分の南関東4場データを収集
  2. 各指数の的中率・補正回収率を集計
  3. `nar_hqs_index_stats` テーブルに保存

### **Option C: 完全設計レビュー後に実装**
- 所要時間: **1時間**
- 内容:
  1. 本設計書の内容をCEOと共に精査
  2. 基準クラス設定の最終決定
  3. 重み設定（25/30/30/15）の承認

---

## 🚀 **CEO、どのオプションで進めますか？**

**Play to Win. 10x Mindset. 🚀**

---

**ファイルパス**: `/home/user/webapp/nar-ai-yoso/HQS_INDEX_DESIGN_NAR.md`  
**作成者**: AI戦略家（CSO兼クリエイティブディレクター）  
**作成日時**: 2026-01-07
