from sqlalchemy import DateTime, String, Text, func, BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())


class Theme(Base):
    __tablename__ = 'Themes'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    assistant_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    thread_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    name_theme: Mapped[str] = mapped_column(String(50), nullable=False)
