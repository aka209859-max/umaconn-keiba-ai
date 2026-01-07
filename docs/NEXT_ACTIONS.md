# 🎯 次のアクション（2026-01-07）

## 📊 現在の状況

### ✅ Phase 1 完了事項
- 前走不利検知システム実装完了
- 直近1ヶ月分のデータ処理完了（256件検知）
- 誤検知問題の解決（逃げ失速パターン除外）
- ドキュメント作成完了

---

## 🚀 次のアクション（3つのオプション）

### **Option A: 過去3年分のデータ構築（推奨）**

**目的**: 本番運用に向けた大規模データ構築

**実行方法**:
```sql
-- pgAdminで実行
-- batch_trouble_detection_final.sql の日付範囲を変更

-- Line 42: 日付範囲を変更
WHERE se.kaisai_nen || se.kaisai_tsukihi BETWEEN '20230101' AND '20260107'
  -- 変更前: '20251207' AND '20260107'
```

**推定所要時間**: 5-10分

**推定処理件数**:
- レース数: 10,000-15,000レース
- 不利検知件数: 8,000-12,000件

**期待効果**:
- 過去3年分の不利データを構築
- Phase 2（HQS統合）の準備完了
- ファクター分析のデータ基盤確立

---

### **Option B: Phase 2へ進む（HQS指数への統合）**

**目的**: 前走不利補正をHQS指数に統合

**実装内容**:

#### Step 2-1: 前走不利補正関数の実装（1時間）

**ファイル**: `core/index_calculator.py`

```python
def get_prev_trouble_correction(conn, ketto_toroku_bango, prev_race_date, 
                                prev_keibajo_code, prev_race_bango):
    """
    前走の不利補正を取得
    
    Returns:
        tuple: (補正値（秒）, 不利タイプ)
    """
    if not all([ketto_toroku_bango, prev_race_date, prev_keibajo_code, prev_race_bango]):
        return 0.0, 'なし'
    
    query = """
        SELECT trouble_score, trouble_type, confidence
        FROM nar_trouble_estimated
        WHERE ketto_toroku_bango = %s
          AND race_date = %s
          AND keibajo_code = %s
          AND race_bango = %s
    """
    
    cursor = conn.cursor()
    cursor.execute(query, [ketto_toroku_bango, prev_race_date, prev_keibajo_code, prev_race_bango])
    result = cursor.fetchone()
    
    if not result:
        return 0.0, 'なし'
    
    trouble_score = result['trouble_score']  # 0-100
    trouble_type = result['trouble_type']
    confidence = result['confidence']
    
    # スコアを補正値（秒）に変換
    # trouble_score 100 = 最大2.0秒のプラス補正
    correction = (trouble_score / 100) * 2.0 * confidence
    
    return correction, trouble_type
```

#### Step 2-2: 上がり指数への統合（1時間）

**変更箇所**: `core/index_calculator.py` の `calculate_agari_index_from_prev`

```python
# 前走不利補正（NEW!）
trouble_correction, trouble_type = get_prev_trouble_correction(
    conn,
    ketto_toroku_bango, 
    prev_race_date, 
    prev_keibajo_code, 
    prev_race_bango
)

# 指数計算
# 前走で不利があった → 実力はもっと上 → プラス補正
agari_index = ((base_time - prev_kohan_3f) + baba_correction + trouble_correction) * 10
```

#### Step 2-3: ファクター追加（30分）

**ファイル**: `config/factor_definitions.py`

```python
# F31: 前走不利度スコア
{
    'id': 'F31',
    'name': '前走不利度スコア',
    'category': '前走不利',
    'table': 'nar_trouble_estimated',
    'column': 'trouble_score',
    'description': '前走レースでの不利度（0-100）',
    'data_type': 'decimal',
    'factor_type': 'single'
},

# F32: 前走不利タイプ
{
    'id': 'F32',
    'name': '前走不利タイプ',
    'category': '前走不利',
    'table': 'nar_trouble_estimated',
    'column': 'trouble_type',
    'description': '出遅れ/挟まれ/外回し等の分類',
    'data_type': 'varchar',
    'factor_type': 'single',
    'values': ['slow_start', 'rank_reversal', 'mixed', 'なし']
}
```

**期待効果**:
- 前走不利があった馬の次走能力評価が向上
- 上がり指数に最大2.0秒のプラス補正
- HQS充実度の向上（83% → 91-95%）

---

### **Option C: GitHubへプッシュ**

**目的**: 完成コードをGitHubに保存

**実行方法**:
```bash
# 1. GitHub環境セットアップ
setup_github_environment

# 2. リモート追加（まだの場合）
cd /home/user/webapp/nar-ai-yoso
git remote add origin https://github.com/USERNAME/nar-ai-yoso.git

# 3. プッシュ
git push -u origin main
```

**プッシュ内容**:
- ✅ 前走不利検知システム（Python + SQL）
- ✅ 改善レポート（docs/trouble_detection_improvement_report.md）
- ✅ バッチ処理SQL（batch_trouble_detection_final.sql）
- ✅ ロードマップ（TROUBLE_DETECTION_ROADMAP.md）

---

## 📊 推奨アクション

### **推奨順序**:

```
1️⃣ Option A: 過去3年分のデータ構築（5-10分）
   ↓
2️⃣ Option B: Phase 2へ進む（HQS統合、2-3時間）
   ↓
3️⃣ Option C: GitHubへプッシュ（完成コード保存）
```

### **理由**:
- **Option A（過去3年分）を先に実行**: Phase 2の実装・テストに必要なデータが揃う
- **Option B（HQS統合）を次に実行**: 前走不利補正の実装・検証
- **Option C（GitHub）を最後に実行**: 完成したコード全体を保存

---

## 🎯 CEO、どのオプションから始めますか？

**A**: 過去3年分のデータ構築（推奨）  
**B**: Phase 2（HQS統合）へ進む  
**C**: GitHubへプッシュ  
**D**: その他（詳細を教えてください）

---

**Play to Win. 10x Mindset. 🚀**
