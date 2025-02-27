import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.fsm.state import State, StatesGroup

from database.orm_query import *

from open_ai_api.transcription import *

user_router = Router()


class Allstate(StatesGroup):
    # Состояния бота
    state_new_theme = State()           # новая тема разговора
    state_choice_theme = State()        # выбор темы


@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer(f'Привет {message.from_user.first_name}!\n'
                         f'Вас приветствует голосовой помощник!\n'
                         f'Назовите тему диалога в голосовом сообщении!')

    # создаю ассистента и процесс для данного пользователя
    assistant_id, thread_id = await def_create_assistant()

    # помещаю в state  для доступа в других обработчиках
    await state.set_data({'assistant_id': assistant_id})
    await state.update_data({'thread_id': thread_id})

    await state.set_state(Allstate.state_new_theme)


# проверка запущенного ассистента
async def def_control_active_assistant(state: FSMContext):
    # забираю id по ассистенту ИИ и процессу
    state_data = await state.get_data()
    if state_data:
        assistant_id = state_data['assistant_id']
        thread_id = state_data['thread_id']
    else:
        # если запуск бота был до обновления версии
        # создаю ассистента и процесс для данного пользователя
        assistant_id, thread_id = await def_create_assistant()
        # assistant_current = Assistant(assistant_id, thread_id)
        # помещаю в state  для доступа в других обработчиках
        await state.set_data({'assistant_id': assistant_id})
        await state.update_data({'thread_id': thread_id})
    return assistant_id, thread_id


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


# пришла новая тема для диалога
@user_router.message(Allstate.state_new_theme, F.voice)
async def def_get_audio_new_theme(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    # прием голосового сообщения и преобразование его в текст и отправка текста
    theme = await def_get_audio_to_text(message, bot)

    # проверка запущенного ассистента
    assistant_id, thread_id = await def_control_active_assistant(state)
    # создаю новый процесс
    thread = await def_create_thread()
    # помещаю в state  для доступа в других обработчиках
    await state.update_data({'thread_id': thread.id})

    # обнуляю состояние
    await state.set_state(state=None)

    # сохраняю в БД
    await orm_add_theme(session=session,
                        telegram_id=message.from_user.id,
                        assistant_id=assistant_id,
                        thread_id=thread.id,
                        name_theme=theme
                        )

    # отправляю на преобразование ИИ из текста в файл голосом и отправка
    await def_get_text_to_audio(message, f'Озвучьте ваш вопрос по теме: {theme}')


# тема для диалога выбрана
@user_router.message(Allstate.state_choice_theme, F.voice)
async def def_get_choice_theme(message: types.Message, bot: Bot, state: FSMContext, session: AsyncSession):
    # прием голосового сообщения и преобразование его в текст и отправка подтверждения
    theme = await def_get_audio_to_text(message, bot)
    result = await orm_get_theme(session, theme)
    if result:
        # помещаю в state  для доступа в других обработчиках
        await state.update_data({'thread_id': result.thread_id})
        # отправляю на преобразование ИИ из текста в файл голосом и отправка
        await def_get_text_to_audio(message, f'Озвучьте ваш вопрос по теме: {theme}')
    else:
        await def_get_text_to_audio(message, 'Тема не найдена, вы в текущем диалоге')

    # обнуляю состояние
    await state.set_state(state=None)


# прием сообщения в диалоге
@user_router.message(F.voice)
async def def_get_audio(message: types.Message, bot: Bot, state: FSMContext):
    # прием голосового сообщения и преобразование его в текст и отправка подтверждения
    question = await def_get_audio_to_text(message, bot)

    # вопрос для ИИ
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

    # проверка запущенного ассистента
    assistant_id, thread_id = await def_control_active_assistant(state)

    # отправляю вопрос в ИИ
    answer = await def_openai_api_question(assistant_id, thread_id, question)
    # удаляю сообщение об ожидании
    await message_wait.delete()
    # ответ ИИ
    # await message.answer(answer)

    # отправляю на преобразование ИИ из текста в файл голосом и отправка
    await def_get_text_to_audio(message, answer)


# создаю запрос на новую тему
@user_router.message(Command('new_dialog'))
async def new_dialog_cmd(message: types.Message, state: FSMContext):
    await def_get_text_to_audio(message, 'Назовите новую тему диалога!')
    await state.set_state(Allstate.state_new_theme)


# выбор тем из базы
@user_router.message(Command('theme_dialog'))
async def themes_dialog_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    themes = 'Назовите одну из озвученных тем'
    # данные из БД по этому пользователю
    result = await orm_get_themes(session, message.from_user.id)
    if result:
        for theme in result:
            # заполняю сообщение всеми темами
            themes += ' ' + theme.name_theme
        # преобразую в голос и отправляю
        await def_get_text_to_audio(message, themes)

        await state.set_state(Allstate.state_choice_theme)
    else:
        # темы отсутствуют создать новую
        await new_dialog_cmd(message, state)


# удаление текущей темы
@user_router.message(Command('delete_dialog'))
async def delete_dialog_cmd(message: types.Message, state: FSMContext, session: AsyncSession):
    state_data = await state.get_data()
    if state_data:
        await orm_delete_theme(session, state_data['thread_id'])
    await themes_dialog_cmd(message, state, session)


@user_router.message(Command('about'))
async def about_cmd(message: types.Message):
    await message.answer('Чат-бот на Aiogram, способен принимать голосовые сообщения, '
                         'преобразовывать их в текст, получать ответы на заданные вопросы и '
                         'озвучивать ответы обратно пользователю с использованием асинхронного '
                         'клиента OpenAI API.')


@user_router.message()
async def def_any_message(message: types.Message):
    # обработка ошибок
    await message.answer('Запишите сообщение в голосовом виде!')
