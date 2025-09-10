from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped,mapped_column,relationship
from typing import Annotated
from .Base import Base
import datetime

primary = Annotated[int,mapped_column(primary_key=True)]

class Banned_users(Base):
    __tablename__ = "banned_users"
    id : Mapped[primary]
    banned_user_id : Mapped[int] 
    banned_by_id : Mapped[int] = mapped_column(ForeignKey("admins.id",ondelete="CASCADE"))
    reason : Mapped[str]
    ban_time : Mapped[datetime.datetime] = mapped_column(default= datetime.datetime.utcnow())
    expires_at : Mapped[datetime.datetime]
    is_active : Mapped[bool]


    admins = relationship("Admins",back_populates="banned_users")