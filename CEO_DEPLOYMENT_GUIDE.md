# NAR-SI Ver.4.0 - CEO向け配置・実行ガイド

## 🚀 緊急対応: collect_index_stats.py 完全修正版の配置

### ✅ 修正内容（Ver.4.0.1）

#### 1. nvd_odテーブル名修正
```diff
- LEFT JOIN nvd_od od ON
+ LEFT JOIN nvd_o1 od ON
```

#### 2. 補正回収率の範囲制限追加
```python
# DECIMAL(6,2) の範囲内に制限（-9999.99 〜 9999.99）
adjusted_return = max(-9999.99, min(9999.99, adjusted_return))
```

---

## 📋 CEO実行手順（PowerShell）

### Step 1: 古いファイルを削除
```powershell
# E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py を削除
Remove-Item "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Force -ErrorAction SilentlyContinue
Write-Host "古いファイル削除完了" -ForegroundColor Yellow
```

### Step 2: 最新版をダウンロード（コミットハッシュ指定）
```powershell
# GitHub から最新版を強制ダウンロード
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/aka209859-max/umaconn-keiba-ai/34c54cd/scripts/collect_index_stats.py?nocache=$timestamp" -OutFile "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py"
Write-Host "完全修正版ダウンロード完了！" -ForegroundColor Green
```

### Step 3: 確認（nvd_odが存在しないことを確認）
```powershell
# nvd_od が存在しない → nvd_o1 に修正済み
$result = Select-String -Path "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Pattern "nvd_od"
if ($result -eq $null) {
    Write-Host "✅ nvd_od は存在しません（修正成功）" -ForegroundColor Green
} else {
    Write-Host "❌ nvd_od がまだ存在します（修正失敗）" -ForegroundColor Red
}

# nvd_o1 が存在することを確認
$result2 = Select-String -Path "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Pattern "nvd_o1"
if ($result2 -ne $null) {
    Write-Host "✅ nvd_o1 が存在します（修正成功）" -ForegroundColor Green
} else {
    Write-Host "❌ nvd_o1 が存在しません（修正失敗）" -ForegroundColor Red
}
```

### Step 4: 実行
```powershell
# E:\UmaData\nar-analytics-python-v2 に移動して実行
cd E:\UmaData\nar-analytics-python-v2
python scripts\collect_index_stats.py
```

---

## 🔍 エラーが出た場合の対応

### エラー1: `nvd_od` は存在しません
**原因**: テーブル名が間違っている（nvd_od → nvd_o1）

**確認**:
```powershell
Select-String -Path "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Pattern "nvd_o1"
```

### エラー2: `kaisai_yen` は存在しません
**原因**: 古いバージョンのファイルが残っている

**確認**:
```powershell
Select-String -Path "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Pattern "kaisai_yen"
```
→ 何も表示されなければOK

### エラー3: `NumericValueOutOfRange`
**原因**: 補正回収率が DECIMAL(6,2) の範囲を超えている

**確認**:
```powershell
Select-String -Path "E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py" -Pattern "max.*min.*9999.99"
```
→ 範囲制限のコードが存在すればOK

---

## 📊 実行結果の確認

### 1. 進行状況の確認
```powershell
# 処理中のログを表示
Get-Content "E:\UmaData\nar-analytics-python-v2\logs\collect_index_stats.log" -Tail 50
```

### 2. データベース確認（pgAdmin4）
```sql
-- 競馬場別のデータ件数確認
SELECT 
    keibajo_code,
    index_type,
    COUNT(*) as cnt
FROM nar_hqs_index_stats
GROUP BY keibajo_code, index_type
ORDER BY keibajo_code, index_type;

-- 大井（42）のデータ確認
SELECT 
    index_type,
    index_value,
    cnt_win,
    hit_win,
    rate_win_hit,
    adj_win_ret
FROM nar_hqs_index_stats
WHERE keibajo_code = '42'
ORDER BY index_type, index_value;
```

---

## 📂 ファイル配置パス

### 完全版ファイル
- **GitHub最新版**: https://github.com/aka209859-max/umaconn-keiba-ai/blob/main/scripts/collect_index_stats.py
- **コミットハッシュ**: `34c54cd`
- **配置先**: `E:\UmaData\nar-analytics-python-v2\scripts\collect_index_stats.py`

### 関連ファイル
```
E:\UmaData\nar-analytics-python-v2\
├── scripts\
│   └── collect_index_stats.py  ← ここに配置
├── config\
│   └── db_config.py
├── core\
│   └── index_calculator.py
└── logs\
    └── collect_index_stats.log
```

---

## ⏱️ 実行時間の目安

| 競馬場 | 期間 | 推定データ件数 | 推定処理時間 |
|--------|------|---------------|-------------|
| 大井（42） | 2023-10-01 〜 2025-12-31 | 約50,000件 | 約30分 |
| 名古屋（47） | 2022-04-01 〜 2025-12-31 | 約70,000件 | 約45分 |
| その他11場 | 2016-01-01 〜 2025-12-31 | 約800,000件 | 約4〜5時間 |

**合計**: 約5〜6時間（13競馬場）

---

## ✅ チェックリスト

- [ ] Step 1: 古いファイル削除完了
- [ ] Step 2: 最新版ダウンロード完了
- [ ] Step 3: nvd_od が存在しない（修正確認）
- [ ] Step 3: nvd_o1 が存在する（修正確認）
- [ ] Step 4: スクリプト実行開始
- [ ] データベースに nar_hqs_index_stats テーブルが存在
- [ ] 処理完了後、13競馬場分のデータが格納されている

---

## 🎯 次のステップ（Phase 3）

collect_index_stats.py の実行が完了したら:

1. **nar_hqs_index_stats テーブルのデータ確認**
2. **HQSスコア算出ロジックの実装開始**
3. **商用化に向けたAPIエンドポイント設計**

---

## 📞 サポート

問題が発生した場合は、以下の情報を添えて報告してください:

1. エラーメッセージの全文
2. 実行したコマンド
3. `Select-String` の確認結果
4. PostgreSQL のバージョン

---

**作成日**: 2026-01-08  
**バージョン**: Ver.4.0.1  
**最終更新**: 34c54cd (GitHub commit hash)
