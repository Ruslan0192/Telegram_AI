import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from database.orm_query import *
from events.amplitude import def_event_api_client

from open_ai_api.transcription import *
from open_ai_api.vision import def_openai_vision

user_router = Router()


# проверка запущенного потока
async def def_control_active_thread(state: FSMContext, session: AsyncSession, telegram_id: int):
    # забираю id по ассистенту ИИ и процессу
    state_data = await state.get_data()
    if state_data:
        thread_id = state_data['thread_id']
    else:
        # читаю данные из БД
        result = await orm_get_user(session, telegram_id)

        if result:
            thread_id = result.thread_id
        else:
            # у этого пользователя не было потока
            # процесс для данного пользователя
            thread_id = await def_create_thread()

        # помещаю в state  для доступа в других обработчиках
        await state.set_data({'thread_id': thread_id})
    return thread_id

# прием голосового сообщения и преобразование его в текст и отправка
async def def_get_audio_to_text(message: types.Message, bot: Bot):
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    # сохраняю голос. сообщение в файл
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
async def start_cmd(message: types.Message, state: FSMContext):
    # оправка уведомления о действиях рользователя
    def_event_api_client(message.from_user.id,
                         'зарегистрировался',
                         {'first_name': message.from_user.first_name})

    await message.answer(f'Привет {message.from_user.first_name}!\n'
                         f'Вас приветствует бот подбора профессии и анализа настроения по фото!\n'
                         f'В голосовом виде назовите профессию или отправьте фото человека'
                         )

    # # создаю ассистента
    # assistant_id = await def_create_assistant()
    # print(assistant_id)

    # создаю процесс для данного пользователя
    thread_id = await def_create_thread()

    # помещаю в state  для доступа в других обработчиках
    await state.set_data({'thread_id': thread_id})


@user_router.message(Command('about'))
async def about_cmd(message: types.Message):
    # оправка уведомления о действиях рользователя
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
    # оправка уведомления о действиях рользователя
    def_event_api_client(message.from_user.id,
                         'отправил голосовое сообщение',
                         {'task': 'определять ценности для профессии'})

    # прием голосового сообщения и преобразование его в текст и отправка подтверждения
    question = await def_get_audio_to_text(message, bot)

    # вопрос для ИИ
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    # проверка запущенного ассистента
    thread_id = await def_control_active_thread(state, session, message.from_user.id)

    # отправляю вопрос в ИИ
    answer, arguments = await def_openai_api_question(thread_id, question)

    if arguments:
        # ценности определены, проверяю на соответствие
        if await def_completions_validation(question, arguments):
            # запись в БД
            await orm_add_theme(session=session,
                                thread_id=thread_id,
                                telegram_id=message.from_user.id,
                                values_human=arguments['values_human']
                                )
        else:
            answer = 'Ценности не прошли валидацию'

    # удаляю сообщение об ожидании
    await message_wait.delete()

    await message.answer(answer)

    # отправляю на преобразование ИИ из текста в файл голосом и отправка
    # await def_get_text_to_audio(message, answer)


# прием фото
@user_router.message(F.photo)
async def def_get_photo(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    # оправка уведомления о действиях рользователя
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


@user_router.message()
async def def_any_message(message: types.Message):
    # оправка уведомления о действиях рользователя
    def_event_api_client(message.from_user.id,
                         'вводит текст',
                         {'task': 'ошибка действий'})

    # обработка ошибок
    await message.answer('Запишите сообщение в голосовом виде или отправьте фото!')

