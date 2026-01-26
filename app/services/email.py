"""
Email Service - Resendを使用したメール送信
"""

import logging
import os
import resend

logger = logging.getLogger(__name__)

# Resend API設定
resend.api_key = os.getenv("RESEND_API_KEY")

# 送信元アドレス
FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "Amaejozu <onboarding@resend.dev>")


def send_password_reset_email(to_email: str, reset_url: str) -> bool:
    """
    パスワードリセットメールを送信

    Args:
        to_email: 送信先メールアドレス
        reset_url: パスワードリセットURL

    Returns:
        送信成功時はTrue、失敗時はFalse
    """
    try:
        params: resend.Emails.SendParams = {
            "from": FROM_EMAIL,
            "to": [to_email],
            "subject": "【Amaejozu】パスワードリセットのご案内",
            "html": f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: sans-serif; line-height: 1.6; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #f97316;">パスワードリセット</h2>
        <p>パスワードリセットのリクエストを受け付けました。</p>
        <p>以下のボタンをクリックして、新しいパスワードを設定してください。</p>
        <p style="margin: 30px 0;">
            <a href="{reset_url}"
               style="background-color: #f97316; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 8px; display: inline-block;">
                パスワードを再設定する
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            このリンクは1時間で有効期限が切れます。
        </p>
        <p style="color: #666; font-size: 14px;">
            心当たりがない場合は、このメールを無視してください。
            アカウントのセキュリティは保たれています。
        </p>
        <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
        <p style="color: #999; font-size: 12px;">
            このメールは Amaejozu から自動送信されています。
        </p>
    </div>
</body>
</html>
            """,
        }

        result = resend.Emails.send(params)
        logger.info(f"パスワードリセットメール送信成功: {to_email}, id={result.get('id')}")
        return True

    except Exception as e:
        logger.error(f"パスワードリセットメール送信エラー: {to_email}, error={e}")
        return False
