"""
Azure MySQL 接続テストスクリプト

使い方:
    python test_db_connection.py

このスクリプトは.envファイルからDATABASE_URLを読み込んで接続テストを行います。
"""

import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def test_connection():
    """データベース接続テスト"""

    # .env ファイル読み込み
    load_dotenv()

    DATABASE_URL = os.getenv("DATABASE_URL")

    if not DATABASE_URL:
        print("エラー: DATABASE_URL が設定されていません")
        print(" .env ファイルに DATABASE_URL を設定してください")
        return False

    print("接続テスト開始...")
    print(f"接続先: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else 'unknown'}")
    print()

    try:
        # エンジン作成
        engine = create_engine(DATABASE_URL, echo=False)

        # 接続テスト
        with engine.connect() as conn:
            # テスト1: バージョン確認
            result = conn.execute(text("SELECT VERSION() as version"))
            version = result.fetchone()[0]
            print(f"MySQL バージョン: {version}")

            # テスト2: データベース名確認
            result = conn.execute(text("SELECT DATABASE() as db_name"))
            db_name = result.fetchone()[0]
            print(f"✅ データベース名: {db_name}")

            # テスト3: 現在時刻取得
            result = conn.execute(text("SELECT NOW() as server_time"))
            server_time = result.fetchone()[0]
            print(f"✅ サーバー時刻: {server_time}")

            # テスト4: テーブル一覧
            result = conn.execute(text("SHOW TABLES"))
            tables = [row[0] for row in result.fetchall()]
            print(f"✅ テーブル数: {len(tables)}")
            if tables:
                print(f"   テーブル: {', '.join(tables)}")
            else:
                print(f"(テーブルはまだ作成されていません)")

        print()
        print("🎉 接続テスト成功！")
        print()
        print("次のステップ:")
        print("  2. ブラウザで確認: http://localhost:8000/api/db/health")

        return True

    except Exception as e:
        print(f"❌ 接続エラー: {e}")
        print()
        print("トラブルシューティング:")
        print("  1. DATABASE_URL の形式を確認")
        print("     正: mysql+mysqlconnector://user:pass@host:3306/db")
        print("  2. パスワードに特殊文字がある場合はURLエンコード")
        print("  3. Azure のファイアウォール設定を確認")
        print("  4. ネットワーク接続を確認")

        return False

if __name__ == "__main__":
    # python-dotenv が必要
    try:
        import dotenv
    except ImportError:
        print("⚠️  python-dotenv がインストールされていません")
        print("   インストール: pip install python-dotenv")
        print()

    test_connection()