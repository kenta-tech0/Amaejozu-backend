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

    