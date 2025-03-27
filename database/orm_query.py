from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import *


# __tablename__ = 'user'
# ************************************************************************************
async def orm_get_user(session: AsyncSession, telegram_id: int):
    # читаю данные для пользователя
    query = select(Users).where(Users.telegram_id == telegram_id)
    result = await session.execute(query)
    return result.scalar()


async def orm_add_user(session: AsyncSession, telegram_id: int, assistant_id: str):
    # записываю нового ассистента
    obj = Users(telegram_id=telegram_id, assistant_id=assistant_id)
    session.add(obj)
    await session.commit()


# __tablename__ = 'value'
# ************************************************************************************
async def orm_add_value(session: AsyncSession,
                        telegram_id: int,
                        thread_id: str,
                        get_value: str,
                        values_human: str
                        ):

    # записываю новые ценности
    obj = Values(
        telegram_id=telegram_id,
        thread_id=thread_id,
        get_value=get_value,
        values_human=values_human
    )
    session.add(obj)
    await session.commit()
