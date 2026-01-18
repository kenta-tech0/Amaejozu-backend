"""
価格更新バッチ実行スクリプト

使い方:
    python -m app.scripts.run_price_update

cronで定期実行する場合:
    0 */6 * * * cd /path/to/project && python -m app.scripts.run_price_update >> /var/log/price_update.log 2>&1
"""
import sys
import os
import json
from datetime import datetime

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv()

from app.services.price_batch import run_price_update_batch


def main():
    """メイン処理"""
    print("=" * 60)
    print(f"🚀 価格更新バッチ処理")
    print(f"   実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # バッチ処理を実行
        result = run_price_update_batch()
        
        # 結果を表示
        print("\n📊 実行結果:")
        print(f"   ステータス: {result['status']}")
        print(f"   処理件数: {result['total']}")
        print(f"   更新成功: {result['updated']}")
        print(f"   エラー: {result['errors']}")
        
        if 'price_drops' in result:
            print(f"   値下げ検出: {result['price_drops']}件")
            print(f"   値上げ検出: {result['price_increases']}件")
        
        if 'duration_seconds' in result:
            print(f"   処理時間: {result['duration_seconds']:.2f}秒")
        
        # 価格変動があれば詳細を表示
        if result.get('price_changes'):
            print("\n💰 価格変動詳細:")
            for change in result['price_changes']:
                symbol = "📉" if change['is_price_drop'] else "📈"
                print(f"   {symbol} {change['product_name'][:30]}...")
                print(f"      ¥{change['old_price']:,} → ¥{change['new_price']:,} ({change['change_percent']:+.1f}%)")
        
        print("\n✅ バッチ処理が完了しました")
        return 0
        
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)