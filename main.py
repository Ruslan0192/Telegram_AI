import asyncio
import json
import os

from aiogram import Bot, Dispatcher

from router.user import user_router

import config


bot = Bot(config.settings.TOKEN_TG)

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
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())

asyncio.run(main())
