# Azure OpenAI 商品お勧め文生成機能

## 概要

商品詳細ページに「なぜおすすめ？」セクションを表示するため、Azure OpenAI (GPT-4o-mini) を使ってお勧め文を自動生成する機能。

## アーキテクチャ

```
Frontend → GET /app/api/products/{id} → Azure OpenAI (GPT-4o-mini)
                      ↓
                 MySQL DB (キャッシュ)
```

**キャッシュ戦略**: 商品ごとにお勧め文をDBに保存し、7日間有効。初回リクエスト時に生成、以降はキャッシュから返却。

---

## 環境変数

`.env` に以下を設定:

```bash
AZURE_OPENAI_API_KEY=your_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4o-mini
```

**注意**: `AZURE_OPENAI_ENDPOINT` はベースURLのみ（`/openai/deployments/...` は不要）

---

## API仕様

### エンドポイント

```
GET /app/api/products/{product_id}
```

### パラメータ

| パラメータ | 型 | 必須 | 説明 |
|-----------|-----|------|------|
| product_id | string | Yes | 商品ID (path) |
| include_recommendation | bool | No | お勧め文を含めるか (default: true) |

### レスポンス例

```json
{
  "status": "ok",
  "product": {
    "id": "abc123",
    "name": "バルクオム THE TONER 化粧水 200ml",
    "brand": {
      "id": "brand123",
      "name": "BULK HOMME"
    },
    "category": {
      "id": "cat123",
      "name": "化粧水"
    },
    "current_price": 2640,
    "original_price": 3300,
    "lowest_price": 2640,
    "discount_rate": 20.0,
    "is_on_sale": true,
    "image_url": "https://...",
    "product_url": "https://...",
    "affiliate_url": "https://...",
    "review_score": 4,
    "review_count": 1234,
    "recommendation": {
      "text": "忙しい男性にぴったりのバルクオム THE TONER。肌のうるおいをしっかり補給し、乾燥やテカリを防ぎます。価格は今なら¥2,640とお得で、コスパも抜群。",
      "generated_at": "2026-01-20T13:30:00",
      "is_cached": true
    }
  }
}
```

---

## 実装ファイル

| ファイル | 説明 |
|---------|------|
| `app/services/openai_service.py` | Azure OpenAI連携サービス |
| `app/models/product.py` | Productモデル（キャッシュカラム含む） |
| `app/schemas/product.py` | レスポンススキーマ |
| `app/main.py` | 商品詳細エンドポイント |

---

## DBカラム

`products` テーブルに追加されたカラム:

| カラム名 | 型 | 説明 |
|---------|-----|------|
| recommendation_text | VARCHAR(2000) | お勧め文キャッシュ |
| recommendation_generated_at | DATETIME | 生成日時 |

マイグレーション: `alembic/versions/488350b719ed_add_password_hash_and_recommendation_.py`

---

## プロンプト設計

商品情報から以下のプロンプトを構築:

```
あなたはメンズコスメの専門家です。以下の商品について、男性ユーザーに向けた魅力的なお勧め文を日本語で作成してください。

【商品情報】
商品名: {name}
ブランド: {brand}
カテゴリ: {category}
現在価格: ¥{current_price} (定価¥{original_price}から¥{discount}お得)
過去最安値: ¥{lowest_price}
レビュー: {review_score}点 ({review_count}件)

【条件】
- 100〜150文字程度で簡潔に
- 男性の肌悩みや美容意識に寄り添った内容
- 価格のお得感やコスパの良さを強調
- 誇大広告にならない自然な表現
- 絵文字は使用しない
```

---

## エラーハンドリング

| エラー種別 | 対応 |
|-----------|------|
| 環境変数未設定 | 警告ログ、`recommendation: null` を返却 |
| API認証エラー | 警告ログ、`recommendation: null` を返却 |
| タイムアウト | 警告ログ、`recommendation: null` を返却 |

**グレースフルデグラデーション**: お勧め文生成に失敗しても、商品詳細は正常に返却される。

---

## テスト方法

### 環境変数確認

```bash
python -c "
from app.services.openai_service import validate_env_variables
print('設定済み' if validate_env_variables() else '未設定')
"
```

### API呼び出しテスト

```bash
python -c "
from app.services.openai_service import _build_prompt, _create_openai_client
from unittest.mock import Mock
import os

mock_product = Mock()
mock_product.name = 'テスト商品'
mock_product.current_price = 1000
mock_product.original_price = 1500
mock_product.lowest_price = 1000
mock_product.review_score = 4
mock_product.review_count = 100
mock_product.brand = Mock(name='テストブランド')
mock_product.category = Mock(name='化粧水')

prompt = _build_prompt(mock_product)
client = _create_openai_client()

response = client.chat.completions.create(
    model=os.getenv('AZURE_OPENAI_DEPLOYMENT_NAME'),
    messages=[
        {'role': 'system', 'content': 'あなたはメンズコスメアドバイザーです。'},
        {'role': 'user', 'content': prompt}
    ],
    max_tokens=300,
)
print(response.choices[0].message.content)
"
```

### エンドポイントテスト

```bash
# 商品詳細取得（お勧め文あり）
curl http://localhost:8000/app/api/products/{product_id}

# 商品詳細取得（お勧め文なし）
curl "http://localhost:8000/app/api/products/{product_id}?include_recommendation=false"
```

---

## キャッシュ仕様

- **有効期間**: 7日間 (`RECOMMENDATION_CACHE_TTL_DAYS`)
- **保存先**: `products.recommendation_text`, `products.recommendation_generated_at`
- **再生成**: 有効期限切れ時に自動再生成
- **強制再生成**: `generate_recommendation(product, db, force_regenerate=True)`

---

最終更新: 2026年1月20日
