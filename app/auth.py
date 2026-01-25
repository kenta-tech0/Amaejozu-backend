"""
認証API - ユーザー登録・ログイン・認証
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime, timedelta
from typing import Optional
import jwt
import bcrypt
import uuid
import os

from app.database import get_db
from app.models.user import User

# JWT設定
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7日間


# ============================================
# Pydanticモデル（リクエスト/レスポンス）
# ============================================

class LoginRequest(BaseModel):
    """ログインリクエスト"""
    email: str = Field(..., description="メールアドレス")
    password: str = Field(..., description="パスワード")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "password123"
            }
        }
    )


class SignupRequest(BaseModel):
    """サインアップリクエスト"""
    email: str = Field(..., description="メールアドレス")
    password: str = Field(..., min_length=8, description="パスワード（8文字以上）")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "securepass123"
            }
        }
    )


class UserResponse(BaseModel):
    """ユーザー情報レスポンス"""
    id: str = Field(..., description="ユーザーID")
    email: str = Field(..., description="メールアドレス")
    nickname: str = Field(..., description="ニックネーム")


class AuthResponse(BaseModel):
    """認証レスポンス"""
    success: bool = Field(..., description="処理成功フラグ")
    message: str = Field(..., description="メッセージ")
    token: Optional[str] = Field(None, description="JWTアクセストークン")
    user: Optional[UserResponse] = Field(None, description="ユーザー情報")


# ============================================
# ルーター設定
# ============================================

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)


# ============================================
# ユーティリティ関数
# ============================================

def hash_password(password: str) -> str:
    """パスワードをハッシュ化"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """パスワード検証"""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


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


def get_current_user(authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    """
    トークンからユーザー取得
    
    Authorizationヘッダーからトークンを取得し、ユーザーを返す
    """
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


# ============================================
# エンドポイント
# ============================================

@router.post(
    "/login",
    response_model=AuthResponse,
    summary="ログイン",
    description="""
ユーザーログインを行い、JWTトークンを取得します。

## 認証フロー
1. メールアドレスとパスワードを送信
2. 認証成功時、JWTトークンとユーザー情報を返却
3. 以降のリクエストでは `Authorization: Bearer {token}` ヘッダーを付与

## トークン有効期限
- 7日間
""",
    responses={
        200: {
            "description": "ログイン成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "ログインに成功しました",
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "email": "user@example.com",
                            "nickname": "user"
                        }
                    }
                }
            }
        },
        401: {
            "description": "認証失敗",
            "content": {
                "application/json": {
                    "example": {"detail": "メールアドレスまたはパスワードが正しくありません"}
                }
            }
        }
    }
)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """ユーザーログイン"""
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません"
        )

    if not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="メールアドレスまたはパスワードが正しくありません"
        )
    
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return AuthResponse(
        success=True,
        message="ログインに成功しました",
        token=access_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            nickname=user.nickname
        )
    )


@router.post(
    "/signup",
    response_model=AuthResponse,
    summary="ユーザー登録",
    description="""
新規ユーザーを登録します。

## 登録フロー
1. メールアドレスとパスワードを送信
2. メールアドレスの重複チェック
3. 登録成功時、JWTトークンとユーザー情報を返却

## パスワード要件
- 8文字以上
""",
    responses={
        200: {
            "description": "登録成功",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "message": "登録に成功しました",
                        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "user": {
                            "id": "550e8400-e29b-41d4-a716-446655440000",
                            "email": "newuser@example.com",
                            "nickname": "newuser"
                        }
                    }
                }
            }
        },
        400: {
            "description": "登録失敗（メールアドレス重複）",
            "content": {
                "application/json": {
                    "example": {"detail": "このメールアドレスは既に登録されています"}
                }
            }
        }
    }
)
def signup(request: SignupRequest, db: Session = Depends(get_db)):
    """ユーザー登録"""
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="このメールアドレスは既に登録されています"
        )
    
    password_hash = hash_password(request.password)
    
    new_user = User(
        id=str(uuid.uuid4()),
        email=request.email,
        password_hash=password_hash,
        nickname=request.email.split("@")[0],
        push_enabled=False,
        email_enabled=True
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    access_token = create_access_token(
        data={"sub": new_user.email},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return AuthResponse(
        success=True,
        message="登録に成功しました",
        token=access_token,
        user=UserResponse(
            id=new_user.id,
            email=new_user.email,
            nickname=new_user.nickname
        )
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="ログインユーザー情報取得",
    description="""
現在ログイン中のユーザー情報を取得します。

## 認証
`Authorization: Bearer {token}` ヘッダーが必要です。
""",
    responses={
        200: {
            "description": "取得成功",
            "content": {
                "application/json": {
                    "example": {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "email": "user@example.com",
                        "nickname": "user"
                    }
                }
            }
        },
        401: {
            "description": "認証エラー",
            "content": {
                "application/json": {
                    "example": {"detail": "認証トークンが必要です"}
                }
            }
        }
    }
)
def get_me(current_user: User = Depends(get_current_user)):
    """現在のログインユーザー情報を取得"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        nickname=current_user.nickname
    )


@router.get(
    "/ping",
    summary="認証ルーター疎通確認",
    description="認証ルーターが動作しているか確認します。",
    responses={
        200: {
            "description": "疎通成功",
            "content": {
                "application/json": {
                    "example": {"message": "auth router is alive"}
                }
            }
        }
    }
)
def auth_ping():
    """認証ルーター疎通確認"""
    return {"message": "auth router is alive"}
