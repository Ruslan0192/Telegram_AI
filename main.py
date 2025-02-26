import asyncio

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.redis import RedisStorage

from commands.com_menu import private

from router.user import user_router
import config


bot = Bot(config.settings.TOKEN_TG)

storage = RedisStorage.from_url(config.settings.REDIS_URL)
dp = Dispatcher(storage=storage)

dp = Dispatcher()
dp.include_router(user_router)


async def on_startup():
    print("Бот успешно запущен!")


async def on_shutdown():
    print('бот остановился')


async def main():
    
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await bot.delete_webhook(drop_pending_updates=True)
    await bot.set_my_commands(commands=private, scope=types.BotCommandScopeAllPrivateChats())
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
