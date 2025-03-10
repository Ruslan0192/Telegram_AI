from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import *


async def orm_add_theme(session: AsyncSession,
                        telegram_id: int,
                        thread_id: str,
                        values_human: str
                        ):
    if await orm_get_user(session, telegram_id):
        # поток у этого пользователя уже есть
        await orm_change_characteristic(session, telegram_id, thread_id, values_human)
    # записываю новую тему
    obj = User(
        telegram_id=telegram_id,
        thread_id=thread_id,
        values_human=values_human
    )
    session.add(obj)
    await session.commit()


async def orm_get_user(session: AsyncSession, telegram_id: int):
    # читаю данные для пользователя
    query = select(User).where(User.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_change_characteristic(session: AsyncSession, telegram_id: int, thread_id: str, values_human: str):
    query = update(User).where(User.telegram_id == telegram_id).\
        values(thread_id=thread_id, values_human=values_human)
    await session.execute(query)
    await session.commit()
