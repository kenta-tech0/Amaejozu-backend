# 🚀 Amaejozu 開発環境セットアップガイド

## 📋 事前準備(全員必須)

### 1. 必要なツール

- [ ] Docker Desktop インストール済み
- [ ] Git インストール済み
- [ ] VS Code インストール済み
- [ ] VS Code拡張機能: Dev Containers

### 2. リポジトリアクセス権限

- [ ] Amaejozu-frontend リポジトリへのアクセス権
- [ ] Amaejozu-backend リポジトリへのアクセス権

---

## 🎯 初回セットアップ(30分)

### ステップ1: リポジトリクローン

```bash
# 作業用ディレクトリ作成
mkdir ~/Projects/amaejozu-project
cd ~/Projects/amaejozu-project

# リポジトリクローン
git clone [frontend-repo-url] Amaejozu-frontend
git clone [backend-repo-url] Amaejozu-backend
```

---

### ステップ2: Dockerネットワーク作成

```bash
# 共有ネットワーク作成(1回だけ)
docker network create amaejozu-network

# 確認
docker network ls | grep amaejozu
```

✅ `amaejozu-network` が表示されればOK

---

### ステップ3: 環境変数設定

#### フロントエンド

```bash
cd Amaejozu-frontend

# テンプレートをコピー
cp .env.example .env.local

# 内容確認(変更不要)
cat .env.local
# → NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### バックエンド

```bash
cd Amaejozu-backend

# テンプレートをコピー
cp .env.example .env

# 認証情報を設定(Week 1ではAzure MySQL接続情報のみ)
code .env
```

### ステップ4: Dev Container起動

#### バックエンドを先に起動

1. 右下に表示される **"Reopen in Container"** をクリック
2. 初回は数分かかります(イメージビルド)
3. `http://localhost:8000/docs` にアクセスして確認

✅ FastAPIのドキュメントページが表示されればOK

---

#### フロントエンドを起動(別ウィンドウ)

1. **"Reopen in Container"** をクリック
2. `http://localhost:3000` にアクセス

✅ "✅ Connected via Docker network!" が表示されればOK

---

## 🆘 トラブルシューティング

### Q1: "Reopen in Container"が表示されない

**対処:**
1. VS Codeの拡張機能で"Dev Containers"がインストールされているか確認
2. Docker Desktopが起動しているか確認
3. VS Codeを再起動

---

### Q2: コンテナ名が `sad_euclid` などランダム名になる

**対処:**
```bash
# 既存コンテナを削除
docker rm -f $(docker ps -aq)

# VS Code: Cmd/Ctrl + Shift + P
# → "Dev Containers: Rebuild Container"
```

---

### Q3: Frontend → Backend 接続エラー

**確認項目:**
- [ ] `.env.local` に `NEXT_PUBLIC_API_URL=http://localhost:8000`
- [ ] Backendが起動している(`http://localhost:8000/docs`確認)
- [ ] Next.jsを再起動した(環境変数変更後は必須)

---

### Q4: ポート競合エラー

```
Error: port 3000 is already allocated
```

**対処:**
```bash
# 使用中のプロセスを確認
lsof -i :3000
lsof -i :8000

# 不要なコンテナを削除
docker rm -f frontend backend
```

---

### 困ったら

1. **このドキュメントのトラブルシューティング確認**
2. **Slack #techチャンネルで質問**

-

## ✅ セットアップ完了チェックリスト

初回セットアップ後、以下を確認:

- [ ] `http://localhost:3000` でフロントエンド表示
- [ ] `http://localhost:8000/docs` でバックエンドAPI表示
- [ ] フロントエンドで "✅ Connected!" 表示
- [ ] `docker ps` で `frontend` と `backend` が表示
- [ ] `docker network inspect amaejozu-network` で両コンテナが参加

**すべてOKなら開発開始できます！🎉**

---

最終更新: 2025年1月11日  
作成者: けんた