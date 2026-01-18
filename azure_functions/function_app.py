"""
Azure Functions - 価格更新タイマートリガー

6時間ごとに自動実行され、ウォッチリスト商品の価格を更新する
"""
import azure.functions as func
import logging
import json
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

app = func.FunctionApp()

@app.timer_trigger(
    schedule="0 0 */6 * * *",  # 6時間ごとに実行（0分0秒）
    arg_name="myTimer",
    run_on_startup=False
)
def price_update_timer(myTimer: func.TimerRequest) -> None:
    """
    価格更新バッチのタイマートリガー
    
    スケジュール: 6時間ごと（0:00, 6:00, 12:00, 18:00）
    """
    logging.info('価格更新バッチ処理を開始します')
    
    try:
        from app.services.price_batch import run_price_update_batch
        
        # バッチ処理を実行
        result = run_price_update_batch()
        
        # 結果をログ出力
        logging.info(f"バッチ処理完了: {json.dumps(result, ensure_ascii=False, default=str)}")
        logging.info(f"処理件数: {result['total']}, 更新: {result['updated']}, エラー: {result['errors']}")
        
        if result.get('price_drops', 0) > 0:
            logging.info(f"値下げ検出: {result['price_drops']}件")
        
    except Exception as e:
        logging.error(f"バッチ処理でエラーが発生: {str(e)}")
        raise


@app.route(route="health", methods=["GET"])
def health_check(req: func.HttpRequest) -> func.HttpResponse:
    """ヘルスチェックエンドポイント"""
    return func.HttpResponse(
        json.dumps({"status": "healthy", "service": "price-update-function"}),
        mimetype="application/json"
    )


@app.route(route="trigger-price-update", methods=["POST"])
def manual_trigger(req: func.HttpRequest) -> func.HttpResponse:
    """
    手動トリガーエンドポイント
    
    テストや緊急時に手動で価格更新を実行する
    """
    logging.info('手動トリガーによる価格更新を開始')
    
    try:
        from app.services.price_batch import run_price_update_batch
        
        result = run_price_update_batch()
        
        return func.HttpResponse(
            json.dumps(result, ensure_ascii=False, default=str),
            mimetype="application/json"
        )
    except Exception as e:
        logging.error(f"手動トリガーでエラー: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )