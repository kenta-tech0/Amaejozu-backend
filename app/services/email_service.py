"""
メール送信サービス
Resend APIを使用してメールを送信する
"""
import os
import logging
from typing import Optional
import resend
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Resend API設定
resend.api_key = os.getenv("RESEND_API_KEY")

# 送信元メールアドレス
FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@example.com")


class EmailService:
    """メール送信サービスクラス"""
    
    def __init__(self):
        self.from_email = FROM_EMAIL
        
        if not resend.api_key:
            logger.warning("RESEND_API_KEY が設定されていません")
    
    def send_email(
        self,
        to: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> dict:
        """メールを送信する"""
        try:
            params = {
                "from": self.from_email,
                "to": [to],
                "subject": subject,
                "html": html_content,
            }
            
            if text_content:
                params["text"] = text_content
            
            response = resend.Emails.send(params)
            
            logger.info(f"メール送信成功: to={to}, subject={subject}")
            return {"success": True, "id": response.get("id")}
            
        except Exception as e:
            logger.error(f"メール送信エラー: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def send_price_drop_notification(
        self,
        to: str,
        product_name: str,
        old_price: int,
        new_price: int,
        drop_rate: float,
        product_url: str,
        image_url: Optional[str] = None
    ) -> dict:
        """価格下落通知メールを送信"""
        subject = f"【値下げ通知】{product_name[:30]}... が {abs(drop_rate):.1f}% 値下げ！"
        
        html_content = self._generate_price_drop_html(
            product_name=product_name,
            old_price=old_price,
            new_price=new_price,
            drop_rate=drop_rate,
            product_url=product_url,
            image_url=image_url
        )
        
        return self.send_email(to=to, subject=subject, html_content=html_content)
    
    def _generate_price_drop_html(
        self,
        product_name: str,
        old_price: int,
        new_price: int,
        drop_rate: float,
        product_url: str,
        image_url: Optional[str] = None
    ) -> str:
        """価格下落メールのHTMLを生成"""
        image_tag = f'<img src="{image_url}" alt="{product_name}" style="max-width: 200px;">' if image_url else ""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1 style="color: #e74c3c;">📉 値下げ通知</h1>
            
            {image_tag}
            
            <h2>{product_name}</h2>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <p style="font-size: 18px; margin: 0;">
                    <span style="text-decoration: line-through; color: #999;">¥{old_price:,}</span>
                    →
                    <span style="color: #e74c3c; font-weight: bold; font-size: 24px;">¥{new_price:,}</span>
                </p>
                <p style="color: #27ae60; font-weight: bold; margin: 10px 0 0 0;">
                    {abs(drop_rate):.1f}% OFF（¥{old_price - new_price:,} お得！）
                </p>
            </div>
            
            <a href="{product_url}" style="display: inline-block; background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px;">
                商品を見る
            </a>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                このメールは Amaejozu からの自動通知です。
            </p>
        </body>
        </html>
        """
    
    def send_test_email(self, to: str) -> dict:
        """テストメールを送信"""
        subject = "【テスト】Amaejozu メール通知テスト"
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <h1>✅ メール送信テスト成功！</h1>
            <p>このメールが届いていれば、Amaejozu のメール通知機能は正常に動作しています。</p>
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #999; font-size: 12px;">
                このメールは Amaejozu からのテスト通知です。
            </p>
        </body>
        </html>
        """
        
        return self.send_email(to=to, subject=subject, html_content=html_content)


# シングルトンインスタンス
email_service = EmailService()