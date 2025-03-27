import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from database.orm_query import *
from events.amplitude import def_event_api_client

from open_ai_api.transcription import def_create_thread, def_openai_api_voice_in_text, def_openai_api_text_in_voice, \
    def_create_assistant, def_create_vector_assistant, def_openai_api_file_search

from open_ai_api.vision import def_openai_vision

user_router = Router()


# прием голосового сообщения и преобразование его в текст и отправка
async def def_get_audio_to_text(message: types.Message, bot: Bot):
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    # Сохраняю голос. Сообщение в файл
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    if not os.path.exists('voice_tmp'):
        os.mkdir('voice_tmp')
    file_on_disk = f'voice_tmp\{file_id}.wav'
    await bot.download_file(file_path, destination=file_on_disk)

    # отправляю на преобразование ИИ голоса из файла в текст
    text = await def_openai_api_voice_in_text(file_on_disk)
    # удаляю сообщение об ожидании
    await message_wait.delete()
    # текст вопроса
    await message.reply(text)

    # удаляю голосовой файл
    os.remove(file_on_disk)
    return text


async def def_get_answer_assistant(message: types.Message, session: AsyncSession, state: FSMContext,
                                   question: str):
    # вопрос для ИИ
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    state_data = await state.get_data()
    assistant_id = state_data['assistant_id']
    thread_id = state_data['thread_id']

    # отправляю вопрос в ИИ
    answer, arguments = await def_openai_api_file_search(assistant_id, thread_id, question)

    if arguments:
        # запись в БД
        for get_value, values_human in arguments.items():
            # определены ценности, записываю
            await orm_add_value(session=session,
                                telegram_id=message.from_user.id,
                                thread_id=thread_id,
                                get_value=get_value,
                                values_human=values_human
                                )

    # удаляю сообщение об ожидании
    await message_wait.delete()
    return answer


# отправляю на преобразование ИИ из текста в файл голосом и отправка
async def def_get_text_to_audio(message: types.Message, answer: str):
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    file_on_disk = await def_openai_api_text_in_voice(answer, message.from_user.id)
    # записываю файл на диск
    audio_file = FSInputFile(file_on_disk, "Ответ ИИ.wav")
    # удаляю сообщение об ожидании
    await message_wait.delete()
    # отправка голосового файла
    await message.answer_voice(audio_file)
    # удаляю голосовой файл
    os.remove(file_on_disk)


# ******************************************************************************
# все хендлеры
@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    # оправка уведомления о действиях пользователя
    telegram_id = message.from_user.id
    user_name = message.from_user.first_name

    await message.answer(f'Привет {user_name}!\n'
                         f'Вас приветствует бот подбора профессии и анализа настроения по фото!\n'
                         f'Вы можете задавать вопросы в голосовом или текстовом видах.\n'
                         f'Также бот принимает фото человека для расшифровки его состояния'
                         )

    user = await orm_get_user(session, telegram_id)
    if user:
        assistant_id = user.assistant_id
    else:
        # в базе этого пользователя не было, создаю запись с ассистентом
        assistant_id = await def_create_assistant()
        await orm_add_user(session, telegram_id, assistant_id)
        def_event_api_client(telegram_id,
                             'зарегистрировался',
                             {'first_name': user_name})

    message_wait = await message.answer('Подключаю помощника...')

    # обновляю ассистента для работы с файлами
    await def_create_vector_assistant(assistant_id)

    # процесс для данного пользователя
    thread_id = await def_create_thread('store_files/anxiety.docx')
    def_event_api_client(telegram_id,
                         'новая тема',
                         {'first_name': user_name})

    # помещаю в state для доступа в других обработчиках
    await state.set_data({'assistant_id': assistant_id})
    await state.update_data({'thread_id': thread_id})

    # удаляю сообщение об ожидании
    await message_wait.delete()


@user_router.message(Command('about'))
async def about_cmd(message: types.Message):
    # оправка уведомления о действиях пользователя
    def_event_api_client(message.from_user.id,
                         'посмотрел сведения о программе',
                         {'command': 'about'})

    await message.answer('Чат-бот на Aiogram, способен принимать голосовые сообщения, '
                         'преобразовывать их в текст, получать ответы на заданные вопросы и '
                         'озвучивать ответы обратно пользователю и анализировать настроение человека'
                         ' по фото с использованием асинхронного клиента OpenAI API.')


# прием сообщения в диалоге
@user_router.message(F.voice)
async def def_get_audio(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    # оправка уведомления о действиях пользователя
    def_event_api_client(message.from_user.id,
                         'отправил голосовое сообщение',
                         {'task': 'определять ценности для профессии'})

    # прием голосового сообщения и преобразование его в текст и отправка подтверждения
    question = await def_get_audio_to_text(message, bot)

    # вопрос для ИИ
    answer = await def_get_answer_assistant(message, session, state, question)

    # await message.answer(answer, parse_mode='Markdown')

    # отправляю на преобразование ИИ из текста в файл голосом и отправка
    await def_get_text_to_audio(message, answer)


# прием фото
# **************************************************************************************
@user_router.message(F.photo)
async def def_get_photo(message: types.Message, bot: Bot):
    # оправка уведомления о действиях пользователя
    def_event_api_client(message.from_user.id,
                         'отправил фото',
                         {'task': 'определять настроение пользователя'})

    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    # сохраняю фото в файл
    file_id = message.photo[-1].file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path
    if not os.path.exists('photo_tmp'):
        os.mkdir('photo_tmp')
    file_on_disk = f'photo_tmp\{file_id}.jpg'
    await bot.download_file(file_path, destination=file_on_disk)

    # отправляю фото на анализ openai
    text = await def_openai_vision(file_on_disk)
    # удаляю сообщение об ожидании
    await message_wait.delete()

    # текст анализа
    await message.reply(text)

    # удаляю  файл
    os.remove(file_on_disk)


# прием текста
# **************************************************************************************
@user_router.message()
async def def_any_message(message: types.Message, session: AsyncSession, state: FSMContext):
    # оправка уведомления о действиях пользователя
    def_event_api_client(message.from_user.id,
                         'вводит текст',
                         {'task': 'определять ценности для профессии'})

    # вопрос для ИИ
    answer = await def_get_answer_assistant(message, session, state, message.text)

    await message.answer(answer, parse_mode='Markdown')

    # обработка ошибок
    # await message.answer('Запишите сообщение в голосовом виде или отправьте фото!')
