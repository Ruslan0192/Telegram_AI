import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder

from commands.com_menu import private

from database.middleware import DataBaseSession
from database.engine import session_maker

from router.user import user_router
from config import settings


bot = Bot(settings.TOKEN_TG)

storage = RedisStorage.from_url(settings.REDIS_URL,
                                key_builder=DefaultKeyBuilder(with_bot_id=True, with_destiny=True),
                                )

dp = Dispatcher(storage=storage)
dp.include_router(user_router)


async def on_startup():
    print("Бот успешно запущен!")


async def on_shutdown():
    print('бот остановился')


async def main():
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    dp.update.middleware(DataBaseSession(session_pool=session_maker))

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
