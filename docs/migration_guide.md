# Alembic マイグレーションガイド

## 概要

このプロジェクトでは、データベーススキーマの管理にAlembicを使用しています。
AlembicはSQLAlchemyと連携してデータベースマイグレーションを管理するツールです。

## 構成ファイル

```
Amaejozu-backend/
├── alembic.ini              # Alembic設定ファイル
├── alembic/
│   ├── env.py               # マイグレーション環境設定
│   ├── script.py.mako       # マイグレーションファイルテンプレート
│   ├── README               # Alembic説明
│   └── versions/            # マイグレーションファイル格納
│       └── de571193d02e_initial_migration_create_all_tables.py
└── app/
    └── models/              # SQLAlchemyモデル
```

## 環境設定

マイグレーションは`.env`ファイルの`DATABASE_URL`環境変数を使用してデータベースに接続します。

```env
DATABASE_URL=mysql+mysqlconnector://user:password@host:port/database
```

---

## 基本コマンド

### マイグレーション状態の確認

```bash
# 現在のマイグレーション状態を確認
alembic current

# マイグレーション履歴を表示
alembic history
```

### マイグレーションの適用

```bash
# 最新のマイグレーションまで適用
alembic upgrade head

# 特定のリビジョンまで適用
alembic upgrade <revision_id>

# 1つ進める
alembic upgrade +1
```

### マイグレーションのロールバック

```bash
# 1つ前のマイグレーションに戻す
alembic downgrade -1

# 特定のリビジョンまで戻す
alembic downgrade <revision_id>

# 全てのマイグレーションを取り消す
alembic downgrade base
```

---

## 新しいマイグレーションの作成

### 自動生成（推奨）

モデルの変更を自動検出してマイグレーションを作成します。

```bash
alembic revision --autogenerate -m "変更内容の説明"
```

**例:**
```bash
# カラム追加の場合
alembic revision --autogenerate -m "Add phone column to users table"

# テーブル追加の場合
alembic revision --autogenerate -m "Create reviews table"
```

### 手動作成

空のマイグレーションファイルを作成します。

```bash
alembic revision -m "変更内容の説明"
```

---

## 開発ワークフロー

### 1. モデルを変更

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    # 新しいカラムを追加
    phone = Column(String(20), nullable=True)
```

### 2. マイグレーションを自動生成

```bash
alembic revision --autogenerate -m "Add phone column to users"
```

### 3. 生成されたマイグレーションを確認

`alembic/versions/`に生成されたファイルを確認し、必要に応じて調整します。

### 4. マイグレーションを適用

```bash
alembic upgrade head
```

### 5. 動作確認

```bash
# 現在の状態を確認
alembic current
```

---

## 初期テーブル構成

初回マイグレーション(`de571193d02e`)で作成されるテーブル:

| テーブル名 | 説明 |
|-----------|------|
| users | ユーザー情報 |
| brands | ブランド情報 |
| categories | カテゴリ情報 |
| products | 商品情報 |
| price_histories | 価格履歴 |
| watchlists | ウォッチリスト |
| alerts | アラート |
| notifications | 通知履歴 |
| brand_follows | ブランドフォロー |
| user_interests | ユーザー興味カテゴリ |

---

## トラブルシューティング

### Q1: `ModuleNotFoundError: No module named 'mysql'`

**対処:**
```bash
pip install mysql-connector-python
```

### Q2: マイグレーションが検出されない

**確認事項:**
- モデルが`app/models/__init__.py`でエクスポートされているか
- `alembic/env.py`でモデルがインポートされているか

### Q3: データベース接続エラー

**確認事項:**
- `.env`ファイルに`DATABASE_URL`が設定されているか
- データベースサーバーが起動しているか
- ネットワーク接続が正常か

### Q4: マイグレーションの競合

複数人で開発している場合、マイグレーションが競合することがあります。

**対処:**
1. 最新のマイグレーションをプル
2. 自分のマイグレーションを再生成
3. `down_revision`を修正して依存関係を解決

---

## 注意事項

- 本番環境でマイグレーションを実行する前に、必ずバックアップを取得してください
- `downgrade`は本番環境では慎重に使用してください
- 自動生成されたマイグレーションは必ず内容を確認してから適用してください

---

最終更新: 2026年1月15日
