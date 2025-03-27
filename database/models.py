from sqlalchemy import String, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class Users(Base):
    __tablename__ = 'user'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    assistant_id: Mapped[str] = mapped_column(String(50))


class Values(Base):
    __tablename__ = 'value'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    thread_id: Mapped[str] = mapped_column(String(50))
    get_value: Mapped[str] = mapped_column(Text)
    values_human: Mapped[str] = mapped_column(Text)

