# 🎯 NAR-SI Ver.4.0 Phase 2 - 現状完全整理（2026-01-08）

## 🚨 **絶対に忘れてはいけない事実**

### 1. **nvd_se テーブルに zenhan_3f は存在しない**
```
✅ 存在するデータ:
- nvd_se.soha_time (走破タイム)
- nvd_se.kohan_3f (後半3F/上がり3F)
- nvd_se.corner_1, corner_2, corner_3, corner_4 (コーナー順位)
- nvd_se.kakutei_chakujun (着順)

❌ 存在しないデータ:
- nvd_se.zenhan_3f (前半3F) → 推定する必要がある
```

### 2. **前半3Fの推定方法**
```python
# core/ten_3f_estimator.py が既に実装済み

# 1200m戦の場合（確定値）
zenhan_3f = soha_time - kohan_3f

# 1400m以上の場合（統計的推定）
zenhan_3f = soha_time × 距離別比率
# 例: 1400m → 26%, 1600m → 22%, 2000m → 17%
```

### 3. **base_times.py の問題**
```
❌ 現在の base_times.py は完全に推定値
   - 2026-01-07に私（AI）が作成
   - 実データから計算していない
   - 公式データでもない

✅ 正しいアプローチ:
   1. 実際のレースデータから前半3Fを推定
   2. 競馬場別・距離別の中央値を計算
   3. それを基準タイムとして使用
```

---

## 📊 **現在の状況**

### **Phase 2の目的**
```
HQS指数の実績データを収集し、nar_hqs_index_stats テーブルに保存する

対象:
- 13競馬場（帯広83と高知54を除外）
- 4つの指数（テン、位置、上がり、ペース）
- 各指数の単勝・複勝の的中率と補正回収率
```

### **現在の問題**
```
1. ❌ 基準タイムが推定値（実データから計算していない）
2. ✅ データ収集スクリプト（collect_index_stats.py）は完成
3. ✅ テーブル（nar_hqs_index_stats）は作成済み
4. ⏸️ 基準タイムを実データから計算するまで実行保留
```

---

## 🔧 **今後の正しい手順**

### **Step 1: 実データから基準タイムを計算**

```python
# 計算方法（疑似コード）
for 各競馬場 in 13競馬場:
    for 各距離 in 実際に開催されている距離:
        # 1. レースデータを取得
        races = DB.query(競馬場, 距離)
        
        # 2. 前半3Fを推定
        for race in races:
            zenhan_3f = estimate_ten_3f(
                soha_time=race.soha_time,
                kohan_3f=race.kohan_3f,
                kyori=race.kyori
            )
        
        # 3. 中央値を計算
        base_zenhan_3f = median(all_zenhan_3f)
        base_kohan_3f = median(all_kohan_3f)
        
        # 4. 基準タイムとして保存
        BASE_TIMES[競馬場][距離] = {
            'zenhan_3f': base_zenhan_3f,
            'kohan_3f': base_kohan_3f
        }
```

### **Step 2: base_times.py を実データで置換**

```bash
# 実データから計算された基準タイムで base_times.py を完全に書き換え
```

### **Step 3: collect_index_stats.py を実行**

```bash
cd E:\UmaData\nar-analytics-python-v2
python scripts\collect_index_stats.py
```

---

## 📂 **重要なファイルの場所**

```
E:\UmaData\nar-analytics-python-v2\
├── config\
│   └── base_times.py              # ❌ 推定値（要置換）
├── core\
│   └── ten_3f_estimator.py        # ✅ 前半3F推定エンジン
├── scripts\
│   ├── collect_index_stats.py     # ✅ データ収集スクリプト
│   └── check_distances.py         # ✅ 距離確認スクリプト
└── models\
    └── ten_3f_lgbm_model.pkl      # ✅ 機械学習モデル
```

---

## 🚫 **やってはいけないこと**

1. **推定・憶測で基準タイムを追加する**
   - ❌ 「川崎1700mは36.8秒くらいだろう」
   - ✅ 実データから計算する

2. **存在しないカラムを参照する**
   - ❌ `SELECT zenhan_3f FROM nvd_se`
   - ✅ `zenhan_3f` は推定して作成する

3. **クレジットを無駄に消費する**
   - ❌ 何度も同じ間違いを繰り返す
   - ✅ このファイルを毎回読んで確認する

---

## 📝 **CEO向けメモ**

### **今日やること**
```
1. 実データから基準タイムを計算するスクリプトを実行
2. 結果を確認
3. base_times.py を実データで置換
4. collect_index_stats.py を実行
```

### **確認事項**
```
- nvd_se に zenhan_3f は存在しない → 推定する
- base_times.py は推定値 → 実データから計算する
- 佐賀の競馬場コードは 51（54ではない）
```

---

## 🎯 **Phase 2完了の定義**

```
✅ nar_hqs_index_stats テーブルに以下のデータが格納されている:
   - 13競馬場 × 4指数 × 各指数値（10刻み）
   - 単勝の的中率・補正回収率
   - 複勝の的中率・補正回収率

✅ 基準タイムは実データから計算されたもの
✅ 推定値・憶測は一切使用していない
```

---

**最終更新**: 2026-01-08
**次回会話時**: このファイルを最初に読むこと
