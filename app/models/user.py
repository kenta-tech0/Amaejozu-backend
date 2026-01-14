from sqlalchemy import Column, String, Boolen, Datetime
from sqlalchemy.dialects.mysql import BIGINT
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "useres"

    id = Column(
        BIGINT(unsigned=True),
        primary_key=True,
        autoincrement=True,
        comment="ユーザーID"
    )

    email = Column(
        String(225),
        unique=True,
        nullable=False,
        index=True,
        comment="メールアドレス"
    )

    user_name = Column(
        String(225),
        nullable=False,
        comment="ユーザー名"
    )

    device_token = Column(
        String(225),
        nullable=True,
        comment="プッシュ通知用デバイストークン"
    )
    push_enabled = Column(
        Boolen,
        default=True,
        nullable=False,
        comment="プッシュ通知ON/OFF"
    )

    email_enabled = Column(
        Boolen,
        default=True,
        nullable=False,
        comment="メール通知ON/OFF"
    )

    created_at = Column(
        Datetime,
        nullable=False,
        server_default=func.now(),
        comment="作成日時"
    )

    updated_at = Column(
        Datetime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新日時"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', user_name='{self.user_name},')"