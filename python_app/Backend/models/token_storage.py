from .Base import Base
from sqlalchemy.orm import mapped_column,Mapped
from enum import Enum
from sqlalchemy import ForeignKey,Enum as SQLEnum
from typing import Annotated
import datetime


primary = Annotated[int,mapped_column(primary_key=True)]


class Token_type(str, Enum):
    Refresh_token = "Refresh_token"


class Token_Storage(Base):
    __tablename__ = "token_storage"
    id : Mapped[primary]
    user_id : Mapped[int] = mapped_column(ForeignKey("usersauth.id"))
    token_type : Mapped[Token_type] = mapped_column(SQLEnum(Token_type))
    token : Mapped[bytes]
    created_at : Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow())
    expires_at : Mapped[datetime.datetime]

 
