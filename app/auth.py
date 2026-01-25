from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from typing import Optional
from collections import defaultdict
from time import time
import jwt
import bcrypt
import uuid
import secrets
import os
import logging

from app.database import get_db
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.services.email import send_password_reset_email

logger = logging.getLogger(__name__)

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1時間

# パスワードリセット設定
PASSWORD_RESET_EXPIRE_MINUTES = 60  # 1時間
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# レート制限設定
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT_WINDOW = 300  # 5分
RATE_LIMIT_MAX_REQUESTS = 5


# Pydanticモデル
class LoginRequest(BaseModel):
    email: str
    password: str


class SignupRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: str
    email: str
    nickname: str


class AuthResponse(BaseModel):
    success: bool
    message: str
    token: Optional[str] = None
    user: Optional[UserResponse] = None


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    success: bool
    message: str


router = APIRouter(prefix="/auth", tags=["auth"])


# パスワードハッシュ化
def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


# JWTトークン生成
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """アクセストークン生成"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(
    authorization: Optional[str] = Header(None), db: Session = Depends(get_db)
):
    """トークンからユーザー取得"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="認証トークンが必要です",
            headers={"WWW-Authenticate": "Bearer"},
        )
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="認証情報が無効です",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Bearer トークンの場合は "Bearer " プレフィックスを削除
        token = authorization
        if token.startswith("Bearer "):
            token = token[7:]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except jwt.InvalidTokenError:
        raise credentials_exception

    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user


def check_rate_limit(client_ip: str) -> bool:
    """
    レート制限チェック

    Args:
        client_ip: クライアントのIPアドレス

    Returns:
        制限内ならTrue、制限超過ならFalse
    """
    now = time()
    # 古いエントリを削除
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if now - t < RATE_LIMIT_WINDOW
    ]
    if len(_rate_limit_store[client_ip]) >= RATE_LIMIT_MAX_REQUESTS:
        return False
    _rate_limit_store[client_ip].append(now)
    return True


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """ユーザーログイン"""
    # ユーザー取得
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    # パスワード検証
    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません",
        )

    # トークン生成
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return AuthResponse(
        success=True,
        message="ログインに成功しました",
        token=access_token,
        user=UserResponse(id=user.id, email=user.email, nickname=user.nickname),
    )


@router.post("/signup", response_model=AuthResponse)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """ユーザー登録"""
    # メール重複チェック
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています",
        )

    # パスワードハッシュ化
    password_hash = hash_password(request.password)

    # 新規ユーザー作成
    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=password_hash,
        nickname=request.email.split("@")[0],  # メール名をニックネームに
        push_enabled=False,
        email_enabled=True,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # トークン生成
    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return AuthResponse(
        success=True,
        message="登録に成功しました",
        token=access_token,
        user=UserResponse(
            id=new_user.id, email=new_user.email, nickname=new_user.nickname
        ),
    )


@router.post("/forgot-password", response_model=MessageResponse)
def forgot_password(
    request: ForgotPasswordRequest,
    req: Request,
    db: Session = Depends(get_db),
):
    """
    パスワードリセットリクエスト

    メールアドレスに対してパスワードリセット用のメールを送信します。
    セキュリティ上、メールアドレスが存在しない場合も同じレスポンスを返します。
    """
    # レート制限チェック
    client_ip = req.client.host if req.client else "unknown"
    if not check_rate_limit(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="リクエストが多すぎます。しばらく待ってから再度お試しください。",
        )

    # 常に同じレスポンスを返す（アカウント列挙防止）
    success_response = MessageResponse(
        success=True,
        message="パスワードリセット用のメールを送信しました。メールをご確認ください。",
    )

    # ユーザー検索
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        logger.info(f"パスワードリセット: 存在しないメールアドレス {request.email}")
        return success_response

    # 既存のトークンを削除（1ユーザー1トークン制約）
    db.query(PasswordResetToken).filter(
        PasswordResetToken.user_id == user.id
    ).delete()

    # 新しいトークン生成
    plain_token = secrets.token_urlsafe(32)
    token_hash = hash_password(plain_token)

    # トークン保存
    reset_token = PasswordResetToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=token_hash,
        expires_at=datetime.utcnow() + timedelta(minutes=PASSWORD_RESET_EXPIRE_MINUTES),
    )
    db.add(reset_token)
    db.commit()

    # リセットURL生成
    reset_url = f"{FRONTEND_URL}/reset-password?token={plain_token}"

    # メール送信
    email_sent = send_password_reset_email(user.email, reset_url)
    if not email_sent:
        logger.error(f"パスワードリセットメール送信失敗: {user.email}")
        # メール送信失敗してもセキュリティ上同じレスポンスを返す

    logger.info(f"パスワードリセットトークン発行: user_id={user.id}")
    return success_response


@router.post("/reset-password", response_model=MessageResponse)
def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    パスワードリセット実行

    トークンを検証し、新しいパスワードを設定します。
    """
    # 有効期限内のトークンを取得
    now = datetime.utcnow()
    valid_tokens = (
        db.query(PasswordResetToken)
        .filter(PasswordResetToken.expires_at > now)
        .all()
    )

    # トークン照合
    matched_token: Optional[PasswordResetToken] = None
    for token_record in valid_tokens:
        try:
            if verify_password(request.token, token_record.token_hash):
                matched_token = token_record
                break
        except Exception:
            continue

    if not matched_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リセットリンクが無効または期限切れです",
        )

    # ユーザー取得
    user = db.query(User).filter(User.id == matched_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="リセットリンクが無効または期限切れです",
        )

    # パスワード更新
    user.password_hash = hash_password(request.new_password)

    # 使用済みトークン削除
    db.delete(matched_token)
    db.commit()

    logger.info(f"パスワードリセット完了: user_id={user.id}")

    return MessageResponse(
        success=True,
        message="パスワードを変更しました。新しいパスワードでログインしてください。",
    )


@router.get("/ping")
def auth_ping():
    return {"message": "auth router is alive"}


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """現在のログインユーザー情報を取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname,
    )
