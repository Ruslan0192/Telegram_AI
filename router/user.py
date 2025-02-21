import os
from pathlib import Path

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart

from open_ai_api.whisper_api import get_openai_api_transcription

user_router = Router()


@user_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(f'Привет {message.from_user.first_name}!\n'
                         f'Вас приветствует голосовой помощник!\n'
                         f'Запишите вопрос в голосовом сообщении!')


@user_router.message(F.voice)
async def def_get_audio(message: types.Message, bot: Bot):
    # сохраняю голос. сообщение в файл
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    file_on_disk = Path("voice_tmp", f"{file_id}.wav")
    await bot.download_file(file_path, destination=file_on_disk)

    # отправляю на расшифровку
    text = get_openai_api_transcription(file_on_disk)
    await message.reply(text)

    # удаляю файл
    os.remove(file_on_disk)


@user_router.message()
async def def_get_audio(message: types.Message):
    # отработка ошибок
    await message.answer('Запишите вопрос в голосовом сообщении!')
