from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import *


async def orm_add_theme(session: AsyncSession,
                        telegram_id: int,
                        assistant_id: str,
                        thread_id: str,
                        name_theme: str,
                        characteristic: str
                        ):
    # записываю новую тему
    obj = Theme(
        telegram_id=telegram_id,
        assistant_id=assistant_id,
        thread_id=thread_id,
        name_theme=name_theme.lower(),
        characteristic=characteristic
    )
    session.add(obj)
    await session.commit()
    return True


async def orm_get_themes(session: AsyncSession, telegram_id: int):
    # читаю все темы для данного пользователя
    query = select(Theme).where(Theme.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalars().all()


async def orm_get_theme(session: AsyncSession, telegram_id: int, name_theme: str):
    # читаю все темы для данного пользователя
    query = select(Theme).where(Theme.telegram_id == telegram_id,
                                Theme.name_theme == name_theme.lower())
    result = await session.execute(query)
    return result.scalar()


async def orm_delete_theme(session: AsyncSession, thread_id: str):
    query = (delete(Theme).where(Theme.thread_id == thread_id))
    await session.execute(query)
    await session.commit()
