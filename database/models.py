from sqlalchemy import String, BigInteger, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.engine import Base


class Theme(Base):
    __tablename__ = 'Themes'
    telegram_id: Mapped[int] = mapped_column(BigInteger)
    assistant_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    thread_id: Mapped[str] = mapped_column(String(50),  nullable=False)
    name_theme: Mapped[str] = mapped_column(String(50), nullable=False)
    characteristic: Mapped[str] = mapped_column(Text, nullable=False)


