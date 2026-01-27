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
    
    def send_target_price_achieved_notification(
        self,
        to: str,
        product_name: str,
        registered_price: int,
        target_price: int,
        current_price: int,
        product_url: str,
        image_url: Optional[str] = None,
        ai_recommendation: Optional[str] = None
    ) -> dict:
        """目標価格達成通知メールを送信"""
        savings = registered_price - current_price
        subject = f"🎉【目標達成】{product_name[:30]}... が目標価格を下回りました！"
        
        html_content = self._generate_target_achieved_html(
            product_name=product_name,
            registered_price=registered_price,
            target_price=target_price,
            current_price=current_price,
            savings=savings,
            product_url=product_url,
            image_url=image_url,
            ai_recommendation=ai_recommendation
        )
        
        return self.send_email(to=to, subject=subject, html_content=html_content)
    
    def _generate_target_achieved_html(
        self,
        product_name: str,
        registered_price: int,
        target_price: int,
        current_price: int,
        savings: int,
        product_url: str,
        image_url: Optional[str] = None,
        ai_recommendation: Optional[str] = None
    ) -> str:
        """目標価格達成メールのHTMLを生成"""
        image_tag = f'<img src="{image_url}" alt="{product_name}" style="max-width: 200px; border-radius: 8px;">' if image_url else ""
        
        ai_section = ""
        if ai_recommendation:
            ai_section = f"""
            <div style="background: #e8f4fd; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #3498db;">
                <h3 style="margin: 0 0 10px 0; color: #2980b9;">💡 AIからのおすすめ</h3>
                <p style="margin: 0; line-height: 1.6;">{ai_recommendation}</p>
            </div>
            """
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; background: #f5f5f5;">
            <div style="background: white; padding: 30px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                <h1 style="color: #27ae60; text-align: center; margin-bottom: 30px;">🎉 目標価格達成！</h1>
                
                <div style="text-align: center; margin-bottom: 20px;">
                    {image_tag}
                </div>
                
                <h2 style="color: #333; text-align: center;">{product_name}</h2>
                
                <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <tr>
                            <td style="padding: 8px 0; color: #666;">登録時価格:</td>
                            <td style="padding: 8px 0; text-align: right; font-size: 16px;">¥{registered_price:,}</td>
                        </tr>
                        <tr>
                            <td style="padding: 8px 0; color: #666;">目標価格:</td>
                            <td style="padding: 8px 0; text-align: right; font-size: 16px;">¥{target_price:,}</td>
                        </tr>
                        <tr style="border-top: 2px solid #27ae60;">
                            <td style="padding: 12px 0; color: #27ae60; font-weight: bold;">現在価格:</td>
                            <td style="padding: 12px 0; text-align: right; font-size: 24px; color: #27ae60; font-weight: bold;">¥{current_price:,}</td>
                        </tr>
                    </table>
                </div>
                
                <div style="background: #27ae60; color: white; padding: 15px; border-radius: 8px; text-align: center; margin: 20px 0;">
                    <span style="font-size: 24px; font-weight: bold;">💰 {savings:,}円お得！</span>
                </div>
                
                {ai_section}
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="{product_url}" style="display: inline-block; background: #e74c3c; color: white; padding: 15px 40px; text-decoration: none; border-radius: 8px; font-size: 18px; font-weight: bold;">
                        今すぐ購入する
                    </a>
                </div>
                
                <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
                <p style="color: #999; font-size: 12px; text-align: center;">
                    このメールは Amaejozu からの自動通知です。<br>
                    目標価格を達成した商品についてお知らせしています。
                </p>
            </div>
        </body>
        </html>
        """
    
# シングルトンインスタンス
email_service = EmailService()