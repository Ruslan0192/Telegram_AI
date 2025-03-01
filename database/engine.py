from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession, AsyncAttrs, async_sessionmaker, create_async_engine

import config

db_url = config.settings.DB_URL
engine = create_async_engine(db_url, echo=True)

session_maker = async_sessionmaker(bind=engine,
                                   class_=AsyncSession,
                                   expire_on_commit=False)


class Base(AsyncAttrs, DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())
