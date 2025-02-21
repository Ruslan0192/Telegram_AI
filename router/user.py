import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart
from aiogram.types import FSInputFile

from open_ai_api.transcription import def_openai_api_voice_in_text, def_openai_api_text_in_voice
from open_ai_api.answer_ai import def_openai_api_question

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
    file_on_disk = f'voice_tmp\{file_id}.wav'
    await bot.download_file(file_path, destination=file_on_disk)

    # отправляю на преобразование ИИ голоса из файла в текст
    question = def_openai_api_voice_in_text(file_on_disk)
    await message.reply(question)

    # удаляю голосовой файл
    os.remove(file_on_disk)

    # вопрос для ИИ
    answer = await def_openai_api_question(question)
    await message.answer(answer)

    # отправляю на преобразование ИИ из текста в файл голосом
    file_on_disk = def_openai_api_text_in_voice(answer, message.from_user.id)

    # записываю файл на диск
    audio_file = FSInputFile(file_on_disk, "Ответ ИИ.wav")
    await message.answer_voice(audio_file)
    # удаляю голосовой файл
    os.remove(file_on_disk)


@user_router.message()
async def def_get_audio(message: types.Message):
    # обработка ошибок
    await message.answer('Запишите вопрос в голосовом сообщении!')
