from sqlalchemy import String, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class User(Base):
    __tablename__ = 'Users'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    thread_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    location: Mapped[str] = mapped_column(String(50), default='')
    unit: Mapped[str] = mapped_column(String(20), default='')
