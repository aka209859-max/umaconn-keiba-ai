# NAR-SI Ver.4.0 商用利用ガイド

**作成日**: 2026-01-08  
**対象**: NAR-SI Ver.4.0 の商用利用を検討する事業者向け  
**目的**: 法的・技術的・ビジネス的観点からの完全なガイドライン

---

## ⚖️ 法的要件

### 1. データ利用許諾

#### JRA/NARデータの利用
```
重要: 競馬データの商用利用には正式な許諾が必要です
```

**必要な手続き**:
1. **日本中央競馬会（JRA）**
   - データ利用契約の締結
   - 使用目的の申告
   - 利用料の支払い

2. **地方競馬全国協会（NAR）**
   - データ提供契約の締結
   - 競馬場別の許諾取得
   - 月次報告の提出

**問い合わせ先**:
- JRA: https://www.jra.go.jp/
- NAR: https://www.nankankeiba.com/

### 2. 競馬法・賭博法の遵守

**禁止事項**:
- ❌ 予想の結果に基づく金銭授受
- ❌ 違法賭博への関与・誘導
- ❌ 的中保証の表示

**許可される範囲**:
- ✅ 予想情報の提供（有料・無料）
- ✅ データ分析サービス
- ✅ 教育・研究目的の利用

### 3. 知的財産権

**NAR-SIアルゴリズム**:
- 著作権: Enable株式会社
- ライセンス: 要確認
- 商標: 要確認

**推奨対応**:
1. 独自の改良版を開発
2. ライセンス契約の締結
3. 法的助言の取得

---

## 💼 ビジネスモデル

### モデル1: SaaS型予想サービス

**概要**:
- 月額課金制の予想配信サービス
- Webアプリケーション/モバイルアプリ
- リアルタイム予想更新

**技術要件**:
- NAR-SI Ver.3.0
- HQS Phase 3完了版
- 38ファクター統合

**推定開発期間**: 3-6ヶ月

**推定初期投資**: 500-1,000万円

**想定価格**:
- ベーシックプラン: 月額 3,000円
- プレミアムプラン: 月額 10,000円
- エンタープライズ: 応相談

### モデル2: API提供サービス

**概要**:
- REST API経由でNAR-SI/HQSを提供
- 従量課金制
- 他サービスへの組み込み

**技術要件**:
- NAR-SI Ver.3.0
- HQS Phase 3完了版
- API Gateway
- 認証・課金システム

**推定開発期間**: 2-4ヶ月

**推定初期投資**: 300-700万円

**想定価格**:
- 1,000リクエスト: 100円
- 100,000リクエスト: 5,000円
- 1,000,000リクエスト: 30,000円

### モデル3: B2B データ分析サービス

**概要**:
- 競馬関連企業向けデータ分析
- カスタムレポート作成
- コンサルティング

**技術要件**:
- NAR-SI Ver.4.0 完全版
- 38ファクター統合
- BI ツール連携

**推定開発期間**: 1-2ヶ月

**推定初期投資**: 200-500万円

**想定価格**:
- 月次レポート: 50,000円/月
- 年次分析: 500,000円/年
- カスタム開発: 応相談

---

## 🏗️ システム構成

### 推奨アーキテクチャ

```
┌─────────────────────────────────────────┐
│          ユーザー/クライアント           │
└───────────────┬─────────────────────────┘
                │ HTTPS
┌───────────────▼─────────────────────────┐
│        Webサーバー/API Gateway          │
│         (Nginx/AWS API Gateway)         │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│      アプリケーションサーバー            │
│      (Python/FastAPI/Flask)             │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  NAR-SI Ver.3.0 Engine         │     │
│  │  - Ver.2.1-B Calculator        │     │
│  │  - Feature Engineering         │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  HQS Score Engine              │     │
│  │  - 4 Index Calculator          │     │
│  │  - Score Integration           │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  38 Factor Integration         │     │
│  │  - Factor Stats Calculator     │     │
│  │  - ML Model Integration        │     │
│  └────────────────────────────────┘     │
└───────────────┬─────────────────────────┘
                │
┌───────────────▼─────────────────────────┐
│       データベース（PostgreSQL）         │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  nvd_ra, nvd_se, nvd_od       │     │
│  │  (レース/結果/オッズ)          │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  nar_hqs_index_stats           │     │
│  │  (HQS指数実績データ)           │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  nar_si_race_results           │     │
│  │  (NAR-SI計算結果)              │     │
│  └────────────────────────────────┘     │
└─────────────────────────────────────────┘
```

### スケーラビリティ

**小規模（〜1,000ユーザー）**:
- サーバー: 1台（CPU 4core, RAM 16GB）
- データベース: 1台（PostgreSQL）
- 推定コスト: 月額 3-5万円（クラウド）

**中規模（1,000〜10,000ユーザー）**:
- Webサーバー: 2台（ロードバランサー）
- アプリサーバー: 3台
- データベース: マスター1台 + スレーブ2台
- キャッシュ: Redis
- 推定コスト: 月額 15-30万円（クラウド）

**大規模（10,000ユーザー〜）**:
- Kubernetes クラスター
- オートスケーリング
- マネージドデータベース（RDS/CloudSQL）
- CDN（CloudFront/Cloud CDN）
- 推定コスト: 月額 50-200万円（クラウド）

---

## 🔒 セキュリティ

### 必須対策

#### 1. データ暗号化
```python
# TLS/SSL接続（PostgreSQL）
import psycopg2

conn = psycopg2.connect(
    host="your-db-host.com",
    port=5432,
    database="pckeiba",
    user="your_user",
    password="your_password",
    sslmode="require"  # ⭐ 必須
)
```

#### 2. API認証
```python
# JWT認証（FastAPI）
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@app.get("/api/nar-si")
async def get_nar_si(token: str = Depends(oauth2_scheme)):
    # トークン検証
    if not verify_token(token):
        raise HTTPException(status_code=401, detail="Invalid token")
    # 処理
    return {"nar_si": 75.5}
```

#### 3. アクセス制御
```sql
-- PostgreSQL ロールベースアクセス制御
CREATE ROLE readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO readonly;

CREATE ROLE readwrite;
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO readwrite;

CREATE USER api_user WITH PASSWORD 'strong_password';
GRANT readonly TO api_user;
```

#### 4. 監査ログ
```python
# すべてのAPI呼び出しをログ記録
import logging

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"API Call: {request.method} {request.url} from {request.client.host}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response
```

---

## 📊 パフォーマンス最適化

### データベース最適化

#### 1. インデックス作成
```sql
-- HQS指数用インデックス
CREATE INDEX idx_hqs_keibajo_type 
ON nar_hqs_index_stats(keibajo_code, index_type);

CREATE INDEX idx_hqs_hit_rate 
ON nar_hqs_index_stats(rate_win_hit DESC, rate_place_hit DESC);

-- NAR-SI用インデックス
CREATE INDEX idx_narsi_kaisai 
ON nar_si_race_results(kaisai_nen, kaisai_tsukihi, keibajo_code);

CREATE INDEX idx_narsi_score 
ON nar_si_race_results(final_nar_si DESC);

-- レース情報用インデックス
CREATE INDEX idx_ra_kaisai 
ON nvd_ra(kaisai_nen, kaisai_tsukihi, keibajo_code);

CREATE INDEX idx_se_umaban 
ON nvd_se(kaisai_nen, kaisai_tsukihi, keibajo_code, race_bango, umaban);
```

#### 2. クエリ最適化
```sql
-- 悪い例: 全テーブルスキャン
SELECT * FROM nar_hqs_index_stats 
WHERE rate_win_hit > 30;

-- 良い例: インデックス利用
SELECT keibajo_code, index_type, index_value, rate_win_hit
FROM nar_hqs_index_stats 
WHERE keibajo_code = '42' 
  AND index_type = 'ten'
  AND rate_win_hit > 30
ORDER BY rate_win_hit DESC;
```

#### 3. 接続プーリング
```python
from psycopg2 import pool

# 接続プール作成
connection_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=20,
    host="your-db-host.com",
    database="pckeiba",
    user="your_user",
    password="your_password"
)

# 接続取得
conn = connection_pool.getconn()
# 処理
# 接続返却
connection_pool.putconn(conn)
```

### アプリケーション最適化

#### 1. キャッシュ活用
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_base_time(keibajo_code: str, kyori: int) -> float:
    """基準タイムをキャッシュ"""
    # config/base_times.py から取得
    return base_times[keibajo_code][kyori]

# Redis キャッシュ
import redis

r = redis.Redis(host='localhost', port=6379, db=0)

def get_hqs_score_cached(keibajo_code: str, index_type: str):
    cache_key = f"hqs:{keibajo_code}:{index_type}"
    cached = r.get(cache_key)
    
    if cached:
        return json.loads(cached)
    
    # データベースから取得
    score = calculate_hqs_score(keibajo_code, index_type)
    
    # 1時間キャッシュ
    r.setex(cache_key, 3600, json.dumps(score))
    
    return score
```

#### 2. バッチ処理
```python
# 悪い例: 1件ずつ処理
for race in races:
    calculate_nar_si(race)
    save_to_db(race)

# 良い例: バッチ処理
results = []
for race in races:
    result = calculate_nar_si(race)
    results.append(result)

# 一括保存
save_batch_to_db(results)
```

---

## 🧪 テスト・品質保証

### 単体テスト

```python
# tests/test_index_calculator.py
import pytest
from core.index_calculator import calculate_ten_index

def test_ten_index_positive():
    """前半が速い場合、テン指数はプラス"""
    zenhan_3f = 34.0  # 速い
    base_time = 72.0
    kyori = 1200
    
    index = calculate_ten_index(zenhan_3f, base_time, kyori)
    assert index > 0
    assert -100 <= index <= 100

def test_ten_index_negative():
    """前半が遅い場合、テン指数はマイナス"""
    zenhan_3f = 40.0  # 遅い
    base_time = 72.0
    kyori = 1200
    
    index = calculate_ten_index(zenhan_3f, base_time, kyori)
    assert index < 0
    assert -100 <= index <= 100
```

### 統合テスト

```python
# tests/test_integration.py
import pytest
from core.nar_si_calculator_v2_1_b import calculate_nar_si_v2_1_b

def test_nar_si_calculation_integration(test_db_conn):
    """NAR-SI計算の統合テスト"""
    race_info = {
        'kaisai_nen': '2025',
        'kaisai_tsukihi': '0101',
        'keibajo_code': '42',
        'race_bango': '01'
    }
    
    horse_data = {
        'umaban': '01',
        'bataiju': 480,
        # ... その他のデータ
    }
    
    result = calculate_nar_si_v2_1_b(test_db_conn, horse_data, race_info)
    
    assert 'final_nar_si' in result
    assert 40 <= result['final_nar_si'] <= 100
    assert result['base_nar_si'] > 0
```

### パフォーマンステスト

```python
# tests/test_performance.py
import time
import pytest

def test_hqs_calculation_performance():
    """HQS計算のパフォーマンステスト"""
    start_time = time.time()
    
    # 1000レース分の計算
    for i in range(1000):
        calculate_hqs_score(test_data[i])
    
    elapsed_time = time.time() - start_time
    
    # 1000レース/秒以上
    assert elapsed_time < 1.0
```

---

## 📈 モニタリング・運用

### Prometheus メトリクス

```python
from prometheus_client import Counter, Histogram, Gauge

# APIリクエスト数
api_requests = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])

# レスポンスタイム
api_response_time = Histogram('api_response_seconds', 'API response time')

# データベース接続数
db_connections = Gauge('db_connections_active', 'Active database connections')

# 使用例
@api_response_time.time()
@app.get("/api/nar-si")
async def get_nar_si():
    api_requests.labels(method='GET', endpoint='/api/nar-si').inc()
    # 処理
    return result
```

### Grafana ダッシュボード

**推奨メトリクス**:
1. APIレスポンスタイム（P50, P95, P99）
2. エラー率（4xx, 5xx）
3. データベースクエリ実行時間
4. キャッシュヒット率
5. システムリソース（CPU, メモリ, ディスク）

### アラート設定

```yaml
# prometheus/alerts.yml
groups:
  - name: nar-si-alerts
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        annotations:
          summary: "High error rate detected"
          
      - alert: SlowResponse
        expr: histogram_quantile(0.95, api_response_seconds) > 2
        for: 5m
        annotations:
          summary: "95th percentile response time > 2s"
          
      - alert: DatabaseDown
        expr: up{job="postgresql"} == 0
        for: 1m
        annotations:
          summary: "PostgreSQL is down"
```

---

## 💰 コスト試算

### AWS構成例（中規模）

| サービス | スペック | 月額コスト |
|---------|---------|-----------|
| EC2 (Web) | t3.medium × 2 | $120 |
| EC2 (App) | t3.large × 3 | $360 |
| RDS (PostgreSQL) | db.t3.large | $200 |
| ElastiCache (Redis) | cache.t3.medium | $80 |
| ALB | - | $30 |
| CloudWatch | - | $30 |
| S3 | 100GB | $3 |
| 転送量 | 1TB | $90 |
| **合計** | - | **$913/月** |

### GCP構成例（中規模）

| サービス | スペック | 月額コスト |
|---------|---------|-----------|
| Compute Engine | n1-standard-2 × 5 | $400 |
| Cloud SQL | db-n1-standard-4 | $280 |
| Memorystore (Redis) | Basic 5GB | $60 |
| Cloud Load Balancing | - | $25 |
| Cloud Storage | 100GB | $3 |
| 転送量 | 1TB | $120 |
| **合計** | - | **$888/月** |

---

## 📝 契約・ライセンス

### 推奨ライセンス構造

**オープンソース版**:
- MIT License または Apache License 2.0
- 非商用利用無料
- 商用利用は別途契約

**商用ライセンス**:
- 年間ライセンス料
- サポート付き
- アップデート無償提供

**エンタープライズライセンス**:
- 無制限利用
- 専任サポート
- カスタマイズ対応

---

## 🎯 成功事例（想定）

### ケース1: 競馬予想サイト

**規模**: 5,000ユーザー  
**料金**: 月額 5,000円  
**月商**: 2,500万円  
**システムコスト**: 月額 20万円  
**粗利率**: 99%

### ケース2: データ分析API

**規模**: 50社  
**料金**: 月額 10万円/社  
**月商**: 500万円  
**システムコスト**: 月額 15万円  
**粗利率**: 97%

### ケース3: コンサルティング

**規模**: 10社  
**料金**: 年額 300万円/社  
**年商**: 3,000万円  
**システムコスト**: 年額 200万円  
**粗利率**: 93%

---

## 🚀 ロードマップ

### Phase 1: MVP開発（3ヶ月）
- [ ] NAR-SI Ver.3.0 統合
- [ ] HQS Phase 3完了
- [ ] 基本API実装
- [ ] 管理画面開発

### Phase 2: β版リリース（3ヶ月）
- [ ] 100ユーザー限定β
- [ ] フィードバック収集
- [ ] バグ修正
- [ ] パフォーマンス改善

### Phase 3: 正式リリース（2ヶ月）
- [ ] セキュリティ監査
- [ ] 負荷テスト
- [ ] ドキュメント整備
- [ ] マーケティング開始

### Phase 4: スケールアップ（6ヶ月〜）
- [ ] 38ファクター統合
- [ ] 機械学習モデル最適化
- [ ] 多言語対応
- [ ] グローバル展開

---

## 📞 サポート・問い合わせ

**技術サポート**:
- Email: support@enable-keiba.com（仮）
- GitHub Issues: https://github.com/aka209859-max/umaconn-keiba-ai/issues

**ビジネス問い合わせ**:
- Email: business@enable-keiba.com（仮）

**法的相談**:
- 顧問弁護士との相談を推奨

---

**最終更新日**: 2026-01-08  
**バージョン**: NAR-SI Ver.4.0  

**Play to Win. 10x Mindset. 商用利用で競馬業界に革命を！** 🚀🏇💼
