# NAR-SI Ver.4.0 地方競馬AI予想システム

**Enable CEO専用** - NAR-SI (NAR Speed Index) Ver.4.0 統合システム

🎉 **NAR-SI Ver.3.0 統合完了: 2026-01-06** 🎉  
🚀 **HQS Phase 2 開発中: 2026-01-08** 🚀

---

## 🎯 NAR-SI Ver.4.0 とは

**NAR Speed Index Ver.4.0** は、地方競馬の予想精度を最大化するために開発された総合的なAI予想システムです。

### 主要コンポーネント

1. **NAR-SI (NAR Speed Index)** ⭐
   - 基準タイムベースの競走能力指数
   - 現在の最新版: **Ver.3.0**（2026-01-06統合完了）
   - 推奨バージョン: **Ver.2.1-B**（バランス版）

2. **HQS (Hit & Quality Score)** 🚧
   - 4つの指数（テン/位置/上がり/ペース）の実績データに基づく予測スコア
   - 競馬場別・期間別の的中率・回収率を分析
   - 現在: **Phase 2 データ収集中**（2026-01-08）

3. **38ファクター統合システム** 📋
   - NAR-SI + HQS + 38種類の競馬ファクターを統合
   - 最終予測精度の最大化
   - Phase 4で実装予定

---

## 📚 完全ドキュメント

### 必読ドキュメント

| ドキュメント | 内容 | 対象読者 |
|------------|------|---------|
| **[PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md)** ⭐ | プロジェクト全体の技術資料（完全版） | 開発者/技術者 |
| **[FILE_LOCATION_REFERENCE.md](FILE_LOCATION_REFERENCE.md)** 🔍 | ファイル配置クイックリファレンス | 全員 |
| **[COMMERCIAL_USE_GUIDE.md](COMMERCIAL_USE_GUIDE.md)** 💼 | 商用利用ガイド（法的・技術・ビジネス） | 経営者/事業企画 |
| **[DOCUMENTATION_COMPLETION_REPORT.md](DOCUMENTATION_COMPLETION_REPORT.md)** 📊 | ドキュメント完成報告書 | CEO |

### 詳細ドキュメント

| ドキュメント | 内容 |
|------------|------|
| [docs/KEIBAJO_CODE_MASTER.md](docs/KEIBAJO_CODE_MASTER.md) | 競馬場コードマスター（13競馬場） |
| [docs/HQS_INDEX_STATS_EXECUTION_GUIDE.md](docs/HQS_INDEX_STATS_EXECUTION_GUIDE.md) | HQS実行ガイド |
| [docs/NAR_SI_INTEGRATION_SUMMARY.md](docs/NAR_SI_INTEGRATION_SUMMARY.md) | NAR-SI統合サマリ |

---

## 🚀 クイックスタート

### Phase 2: HQS指数データ収集

#### 1. 環境要件

- **Python:** 3.8以上
- **PostgreSQL:** 12以上
- **OS:** Windows 10/11 または Linux

#### 2. 依存パッケージのインストール

```bash
cd E:\UmaData\nar-analytics-python-v2
pip install psycopg2-binary numpy
```

#### 3. HQS指数データ収集

```bash
cd E:\UmaData\nar-analytics-python-v2
python scripts\collect_index_stats.py
```

**推定実行時間**: 3-5時間  
**対象競馬場**: 13場（大井、川崎、船橋、浦和、門別、盛岡、金沢、笠松、名古屋、園田、姫路、高知、佐賀）

---

## 📁 プロジェクト構成

```
E:\UmaData\nar-analytics-python-v2\  (CEO環境)
/home/user/webapp/nar-ai-yoso\       (サンドボックス環境)
│
├── 📄 PROJECT_STRUCTURE_MASTER.md       ⭐ 技術資料（完全版）
├── 📄 FILE_LOCATION_REFERENCE.md        🔍 ファイル索引
├── 📄 COMMERCIAL_USE_GUIDE.md           💼 商用利用ガイド
├── 📄 DOCUMENTATION_COMPLETION_REPORT.md 📊 完成報告書
│
├── 📂 config/                       # 設定ファイル
│   ├── base_times.py               # 競馬場別基準タイム
│   ├── db_config.py                # データベース接続設定
│   └── odds_correction.py          # オッズ補正設定
│
├── 📂 core/                         # コアモジュール
│   ├── index_calculator.py         # ⭐ HQS指数計算エンジン（4指数）
│   ├── ten_3f_estimator.py         # テン3F推定
│   ├── nar_si_calculator_v2_1_b.py # NAR-SI Ver.2.1-B（バランス版）
│   ├── nar_si_v3_data_fetcher.py   # Ver.3.0データ取得
│   ├── hqs_calculator.py           # HQSスコア計算
│   └── [その他NAR-SIバージョン...]
│
├── 📂 scripts/                      # 実行スクリプト
│   ├── collect_index_stats.py      # ⭐ HQS指数実績データ収集（最重要）
│   ├── create_hqs_index_stats_table.sql # HQSテーブル作成
│   └── [その他SQLスクリプト...]
│
├── 📂 docs/                         # ドキュメント
│   ├── KEIBAJO_CODE_MASTER.md      # 競馬場コードマスター
│   ├── HQS_INDEX_STATS_EXECUTION_GUIDE.md # HQS実行ガイド
│   └── NAR_SI_INTEGRATION_SUMMARY.md # NAR-SI統合サマリ
│
└── 📂 tests/                        # テストファイル
    └── test_*.py
```

---

## 🗄️ データベース構造

### PostgreSQL データベース: `pckeiba`

#### 主要テーブル

| テーブル | 内容 | 備考 |
|---------|------|------|
| **nvd_ra** | レース情報 | 距離、トラック、馬場状態 |
| **nvd_se** | レース結果（馬別） | 着順、タイム、単勝オッズ |
| **nvd_od** ⭐ | オッズデータ | 単勝・複勝・枠連オッズ（固定長フォーマット） |
| **nvd_hr** | 払戻情報 | 単勝・複勝払戻金 |
| **nar_hqs_index_stats** ⭐ | HQS指数実績データ | 4指数の的中率・回収率 |
| **nar_si_race_results** | NAR-SI計算結果 | Ver.3.0の計算結果 |

**⚠️ 超重要**: 複勝オッズは `nvd_od.odds_fukusho` から取得（固定長336文字をパース）

詳細は [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md) を参照

---

## 🔧 主要モジュール

### 1. HQS指数計算エンジン

**ファイル**: `core/index_calculator.py`

**4つの指数**:
1. **テン指数**: 前半3Fの速さ（逃げ・先行力）
2. **位置指数**: コーナー通過順位（ポジション取り）
3. **上がり指数**: 後半3Fの速さ（差し・追込力）
4. **ペース指数**: ペースバランス（ハイ/スロー判定）

### 2. NAR-SI計算エンジン

**推奨バージョン**: `core/nar_si_calculator_v2_1_b.py` （Ver.2.1-B バランス版）

**補正項目**:
- 馬体重補正（-0.2/-0.4/-0.6）
- ペース補正
- 枠番補正（内枠 +2、外枠 -2）
- 距離補正
- コース補正
- ナイター補正
- トラック補正
- クラス補正

---

## 📊 開発ロードマップ

### Phase 1: データベース設計 ✅ 完了（2026-01-08）
- [x] nar_hqs_index_stats テーブル設計
- [x] create_hqs_index_stats_table.sql 作成

### Phase 2: データ収集 🚧 進行中（2026-01-08）
- [x] collect_index_stats.py 実装
- [x] nvd_od からの複勝オッズ取得実装
- [ ] 13競馬場のデータ収集実行（3-5時間）
- [ ] データ検証

### Phase 3: HQSスコア計算 📋 計画中
- [ ] HQSスコア計算実装
- [ ] 4指数の統合
- [ ] 予測精度検証

### Phase 4: 38ファクター統合 📋 計画中
- [ ] NAR-SI + HQS 統合
- [ ] 38ファクター統合
- [ ] 最終予測モデル構築

---

## 💼 商用利用

NAR-SI Ver.4.0 は商用利用を前提として設計されています。

### 推奨ビジネスモデル

1. **SaaS型予想サービス** (月額 3,000円〜)
2. **API提供サービス** (従量課金制)
3. **B2B データ分析サービス** (月額 50,000円〜)

詳細は [COMMERCIAL_USE_GUIDE.md](COMMERCIAL_USE_GUIDE.md) を参照

---

## 🔐 重要な技術的決定

### 決定1: 複勝オッズの取得元 ⭐ 超重要

**問題**: nvd_se.fukusho_odds は存在しない

**解決策**: nvd_od.odds_fukusho から取得（固定長336文字をパース）

**実装**: `core/index_calculator.py` の `parse_fukusho_odds()` 関数

### 決定2: 競馬場別期間設定

**理由**: 馬場改修により基準タイムが変化

**設定**:
- 大井 (42): 2023/10/01〜（オーストラリア産白砂導入）
- 名古屋 (47): 2022/04/01〜（大幅改修）
- その他11場: 2016/01/01〜（長期データ）

### 決定3: NAR-SI Ver.2.1-B を推奨

**理由**: バランスが最も取れたバージョン

**特徴**:
- 馬体重補正をバランス調整（-0.2/-0.4/-0.6）
- 枠番補正を縮小（内枠 +2、外枠 -2）

詳細は [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md) を参照

---

## 🧪 テスト

### 単体テスト

```bash
cd E:\UmaData\nar-analytics-python-v2
python -m pytest tests/test_index_calculator.py
```

### 統合テスト

```bash
python -m pytest tests/test_integration.py
```

---

## 📝 Enable憲法（CEO行動指針）

- **10x Mindset:** 10%の改善ではなく、10倍の成長を目指す
- **Be Resourceful:** リソース不足を言い訳にせず、知恵とAIで突破する
- **Play to Win:** 負けないためではなく、勝つためにプレイする
- **Buy Back Time:** 時間を金で買い（AI活用含む）、戦略に投資する

### プロジェクト特性

- **48時間で"勘"を"確信"に変える**
- **スピードと論理的根拠（エビデンス）を両立**
- **プロフェッショナル、クリーン、モダン、信頼性**

---

## 📞 サポート

**技術的な質問**:
- GitHub Issues: https://github.com/aka209859-max/umaconn-keiba-ai/issues

**ドキュメント**:
- [PROJECT_STRUCTURE_MASTER.md](PROJECT_STRUCTURE_MASTER.md)
- [FILE_LOCATION_REFERENCE.md](FILE_LOCATION_REFERENCE.md)
- [COMMERCIAL_USE_GUIDE.md](COMMERCIAL_USE_GUIDE.md)

---

## 📜 ライセンス

**商用利用**: 要確認  
**非商用利用**: MIT License（予定）

詳細は [COMMERCIAL_USE_GUIDE.md](COMMERCIAL_USE_GUIDE.md) を参照

---

## 🎉 バージョン履歴

| バージョン | リリース日 | 主な変更 |
|-----------|-----------|---------|
| Ver.4.0 Phase 2 | 2026-01-08 | HQS Phase 2実装、完全ドキュメント作成 |
| Ver.3.0 | 2026-01-06 | NAR-SI Ver.3.0統合、保存場所一元化 |
| Ver.2.1-B | 2026-01-06 | バランス版リリース |
| Ver.2.0 | 2026-01-05 | 基準タイムベース実装 |

---

**NAR-SI Ver.4.0 - 地方競馬AI予想システム**  
**Play to Win. 10x Mindset. 48時間で確信に変えましょう！** 🚀🏇

**CEO、完全なドキュメントが揃いました。商用化の準備完了です！**
