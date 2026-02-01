from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, ForeignKey
from typing import Optional

class Base(DeclarativeBase):
    pass

class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str | None] = mapped_column(String(50))
    last_name: Mapped[str | None] = mapped_column(String(50))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    def __repr__(self):
        return f"User(id={self.id}, first_name={self.first_name}, last_name={self.last_name})"

class OperationModel(Base):
    __tablename__ = "operations"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    type_op: Mapped[str] = mapped_column(String(7))
    sticker_id: Mapped[str] = mapped_column(String(255))




