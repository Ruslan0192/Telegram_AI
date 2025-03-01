from sqlalchemy import String, BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class Theme(Base):
    __tablename__ = 'Themes'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    assistant_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    thread_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    name_theme: Mapped[str] = mapped_column(String(50), nullable=False)
    test: Mapped[bool] = mapped_column(default=False)
