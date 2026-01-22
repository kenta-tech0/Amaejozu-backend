# デプロイガイド - Amaejozu Backend

## 概要

GitHub Actions を使用して Azure Web App にデプロイします。
`main` ブランチへのプッシュで自動デプロイが実行されます。

---

## アーキテクチャ

```
GitHub (main branch)
    ↓ push
GitHub Actions
    ↓ build & push
Azure Container Registry (ACR)
    ↓ pull
Azure Web App (aps-step3-2-FK-2)
    ↓ connect
Azure MySQL
```

---

## 事前準備

### 1. Azure リソース

以下のリソースが作成済みであること:

- Azure Container Registry (ACR)
- Azure Web App for Containers (`aps-step3-2-FK-2`)
- Azure Database for MySQL

### 2. GitHub Secrets の設定

リポジトリの **Settings** → **Secrets and variables** → **Actions** で以下を設定:

| Secret 名 | 値 | 説明 |
|-----------|-----|------|
| `ACR_LOGIN_SERVER` | `<registry>.azurecr.io` | ACR のログインサーバー |
| `ACR_USERNAME` | ACR のユーザー名 | Azure Portal → ACR → アクセスキー |
| `ACR_PASSWORD` | ACR のパスワード | Azure Portal → ACR → アクセスキー |
| `AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND` | XMLファイルの内容 | 下記参照 |

#### 発行プロファイルの取得方法

1. Azure Portal → `aps-step3-2-FK-2`
2. 概要ページ上部の **発行プロファイルのダウンロード** をクリック
3. ダウンロードしたファイルの内容をコピー
4. GitHub Secrets に `AZURE_WEBAPP_PUBLISH_PROFILE_BACKEND` として貼り付け

---

### 3. Azure Web App の環境変数設定

Azure Portal → `aps-step3-2-FK-2` → **構成** → **アプリケーション設定** で以下を設定:

#### データベース接続

| 名前 | 値 |
|------|-----|
| `DB_HOST` | `<server>.mysql.database.azure.com` |
| `DB_USER` | データベースユーザー名 |
| `DB_PASSWORD` | データベースパスワード |
| `DB_NAME` | `cosmetics_price_db` |
| `DB_PORT` | `3306` |
| `SSL_CA_PATH` | `DigiCertGlobalRootG2.crt.pem` |

#### 認証・セキュリティ

| 名前 | 値 |
|------|-----|
| `SECRET_KEY` | JWT用シークレット（長いランダム文字列） |

#### Azure OpenAI

| 名前 | 値 |
|------|-----|
| `AZURE_OPENAI_API_KEY` | Azure OpenAI の API キー |
| `AZURE_OPENAI_ENDPOINT` | `https://<resource>.openai.azure.com/` |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | デプロイメント名 |

#### 楽天 API

| 名前 | 値 |
|------|-----|
| `RAKUTEN_APP_ID` | 楽天 API の App ID |
| `RAKUTEN_AFFILIATE_ID` | 楽天アフィリエイト ID |

#### アプリケーション設定

| 名前 | 値 |
|------|-----|
| `ENVIRONMENT` | `production` |
| `LOG_LEVEL` | `INFO` |

---

## ワークフローの動作

### トリガー

- `main` ブランチへのプッシュ
- GitHub Actions の手動実行 (workflow_dispatch)

### 実行ステップ

1. **Checkout**: ソースコードを取得
2. **Docker Buildx セットアップ**: マルチプラットフォームビルド準備
3. **ACR ログイン**: Azure Container Registry に認証
4. **ビルド & プッシュ**: `Dockerfile.prod` を使用してイメージをビルド
5. **デプロイ**: Azure Web App にイメージをデプロイ

### コンテナ起動時の処理

1. Alembic マイグレーション実行 (`alembic upgrade head`)
2. Uvicorn で FastAPI アプリ起動

---

## デプロイの確認

### ヘルスチェック

```bash
curl https://aps-step3-2-FK-2.azurewebsites.net/app/api/health
```

### データベース接続確認

```bash
curl https://aps-step3-2-FK-2.azurewebsites.net/app/api/db/health
```

### ログの確認

Azure Portal → `aps-step3-2-FK-2` → **ログストリーム**

---

## トラブルシューティング

### デプロイが失敗する

1. GitHub Actions のログを確認
2. Secrets が正しく設定されているか確認
3. ACR の認証情報が有効か確認

### コンテナが起動しない

1. Azure Portal → ログストリームでエラーを確認
2. 環境変数が正しく設定されているか確認
3. マイグレーションが失敗していないか確認

### データベース接続エラー

1. `DB_HOST`, `DB_USER`, `DB_PASSWORD` が正しいか確認
2. Azure MySQL のファイアウォール設定を確認
3. SSL 証明書 (`DigiCertGlobalRootG2.crt.pem`) が含まれているか確認

---

## 関連ファイル

| ファイル | 説明 |
|---------|------|
| `.github/workflows/deploy-backend.yml` | デプロイワークフロー |
| `Dockerfile.prod` | 本番用 Dockerfile |
| `alembic.ini` | Alembic 設定 |
| `DigiCertGlobalRootG2.crt.pem` | Azure MySQL SSL 証明書 |

---

最終更新: 2025年1月
