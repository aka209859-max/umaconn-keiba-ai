# 🚨 緊急確認：前半3Fが90秒・60秒になる原因調査

## 問題の概要

基準タイム再計算の結果、前半3Fの値が異常に大きい箇所と小さい箇所が混在しています：

```
- 門別 1000m: 前半3F=23.9秒 後半3F=36.9秒 (N=2749)  ← 短すぎる
- 大井 1000m: 前半3F=23.4秒 後半3F=36.3秒 (N=21)    ← 短すぎる
- （CEOが指摘）90秒や60秒の箇所もある          ← 長すぎる
```

**理論値（1000m）**:
- 走破タイム: 約60秒
- 前半3F（600m）: 約36秒
- 後半3F（400m）: 約24秒

---

## 🔍 検証が必要なポイント

### 1. `kohan_3f` の定義確認

**可能性A**: `kohan_3f` = 上がり3F（ゴール前600m） ← データスキーマの記載
**可能性B**: `kohan_3f` = 後半3F（ラップタイム）

### 2. `soha_time` のフォーマット確認

**現在の変換式（mSSd形式）**:
```python
soha_padded = str(soha_time).zfill(4)  # 4桁にゼロ埋め
minutes = int(soha_padded[0:1])        # 1桁目: 分
seconds = int(soha_padded[1:3])        # 2-3桁目: 秒
deciseconds = int(soha_padded[3:4])    # 4桁目: 1/10秒
soha_seconds = minutes * 60 + seconds + deciseconds / 10.0
```

**例**:
- `1058` → `1分05.8秒` = 65.8秒 ✅
- `598` → `0分59.8秒` = 59.8秒 ✅

---

## 📋 CEO への依頼事項

### 実行1: nvd_se テーブルのカラム名確認

```cmd
E:
cd \UmaData\nar-analytics-python-v2

python -c "import psycopg2; conn = psycopg2.connect(dbname='pckeiba', user='postgres', password='postgres', host='localhost', port=5432); cur = conn.cursor(); cur.execute(\"SELECT column_name FROM information_schema.columns WHERE table_name = 'nvd_se' AND (column_name LIKE '%%agari%%' OR column_name LIKE '%%kohan%%' OR column_name LIKE '%%soha%%') ORDER BY column_name\"); rows = cur.fetchall(); print('\n【カラム名一覧】'); [print(row[0]) for row in rows]; cur.close(); conn.close()"
```

### 実行2: 実データのサンプル確認（1200m・勝ち馬）

```cmd
python -c "import psycopg2; conn = psycopg2.connect(dbname='pckeiba', user='postgres', password='postgres', host='localhost', port=5432); cur = conn.cursor(); cur.execute(\"SELECT ra.kyori, se.soha_time, se.kohan_3f, se.bamei FROM nvd_ra ra JOIN nvd_se se ON ra.kaisai_nen = se.kaisai_nen AND ra.kaisai_tsukihi = se.kaisai_tsukihi AND ra.keibajo_code = se.keibajo_code AND ra.race_bango = se.race_bango WHERE ra.keibajo_code = '44' AND CAST(ra.kyori AS INTEGER) = 1200 AND se.kakutei_chakujun = '1' AND se.soha_time IS NOT NULL AND se.kohan_3f IS NOT NULL LIMIT 5\"); rows = cur.fetchall(); print('\n【大井1200m勝ち馬サンプル】'); print(f\"{'距離':<8} {'soha_time':<12} {'kohan_3f':<12} {'馬名'}\"); print('-'*50); [print(f\"{row[0]:<8} {row[1]:<12} {row[2]:<12} {row[3]}\") for row in rows]; cur.close(); conn.close()"
```

### 実行3: 変換テスト

```cmd
python -c "soha = '1149'; kohan = '387'; soha_padded = soha.zfill(4); minutes = int(soha_padded[0:1]); seconds = int(soha_padded[1:3]); deciseconds = int(soha_padded[3:4]); soha_sec = minutes * 60 + seconds + deciseconds / 10.0; kohan_sec = float(kohan) / 10.0; zenhan = soha_sec - kohan_sec; print(f'\nsoha_time={soha} → {soha_sec:.1f}秒'); print(f'kohan_3f={kohan} → {kohan_sec:.1f}秒'); print(f'zenhan_3f = {soha_sec:.1f} - {kohan_sec:.1f} = {zenhan:.1f}秒')"
```

---

## 🎯 期待される出力

### カラム名一覧:
```
kohan_3f
soha_time
```

### 実データサンプル:
```
【大井1200m勝ち馬サンプル】
距離     soha_time    kohan_3f     馬名
--------------------------------------------------
1200     1149         387          アイユーベスト
1200     1148         380          サクラノユメ
```

### 変換テスト:
```
soha_time=1149 → 74.9秒
kohan_3f=387 → 38.7秒
zenhan_3f = 74.9 - 38.7 = 36.2秒
```

---

## 🔥 Play to Win

この3つの実行結果を教えてください！
データの真実を確認して、正しい基準タイムを計算します！
