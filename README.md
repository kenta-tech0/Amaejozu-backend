# amejozu-backend

## Development Setup

This project uses Dev Containers.

1. Clone this repository.
2. Open the folder in VS Code.
3. Click "Reopen in Container" when prompted.

# 化粧品価格比較アプリケーション（Amaejozu）

化粧品の価格を自動で監視し、価格変動を通知するWebアプリケーションです。楽天市場APIとAzure OpenAIを活用して、ユーザーが希望する化粧品の価格を追跡し、お得な情報をメールで通知します。

## プロジェクト概要

このプロジェクトは、以下の機能を提供します：

- 化粧品の価格監視と追跡
- 楽天市場APIを利用した価格情報の取得
- Azure OpenAI (ChatGPT)を活用した商品情報の分析
- 価格変動時のメール通知（Resend経由）
- ユーザー認証とセキュアなデータ管理
- 定期的な価格更新とバックグラウンド処理

## 技術スタック

### フロントエンド
- **Next.js** - Reactベースのフロントエンドフレームワーク
- **Node.js** - JavaScript実行環境

### バックエンド
- **FastAPI** (v0.128.0) - Python製の高速Webフレームワーク
- **Python 3.11** - プログラミング言語
- **SQLAlchemy** (v2.0.45) - ORMとデータベース管理
- **Pydantic** (v2.12.5) - データバリデーション

### データベース
- **MySQL 8.0** - リレーショナルデータベース
- **Alembic** (v1.17.2) - データベースマイグレーションツール

### 外部API・サービス
- **楽天市場API** - 商品情報と価格データの取得
- **Azure OpenAI** (GPT-4o-mini) - 商品情報の分析とAI機能
- **Resend** (v2.5.0) - メール通知サービス

## GitHub運用ルール
- IssueとPRを紐づける（説明のところに、**Closes #<紐付けたいIssueの番号>**と書くことで、PRとIssueを紐付けることができます。）
- PRの相互レビューを行う
- ローカル環境で動作確認後に承認/マージを行う

## ブランチ命名規則
### フォーマット
`<type>/#<issue番号>-<brief-description>`

### 例
- `feature/#17-add-watchlist-api`
- `fix/#25-notification-email-bug`

### ワークフロー
1. 作業 → add → commit → push
2. PRを作成して Closes #XX を記載
3. レビュー → マージ

## 開発環境のセットアップ

### 前提条件

以下のツールがインストールされている必要があります：

- Docker Desktop
- Git
- テキストエディタ（VS Code推奨）
- VS Code拡張機能: Visual Studio Codeを開き、拡張機能マーケットプレイスからDev Containers (ID: ms-vscode-remote.remote-containers) をインストールします。
