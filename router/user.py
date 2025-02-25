import os

from aiogram import F, types, Router, Bot
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile

from open_ai_api.transcription import \
    def_openai_api_voice_in_text, \
    def_openai_api_question, \
    def_openai_api_text_in_voice, \
    def_create_assistant

user_router = Router()


# class Assistant:
#     def __init__(self, assistant_id, thread_id):
#         self.id = assistant_id
#         self.thread_id = thread_id
#
#     def __call__(self):
#         return self.id, self.thread_id


@user_router.message(CommandStart())
async def start_cmd(message: types.Message, state: FSMContext):
    await message.answer(f'Привет {message.from_user.first_name}!\n'
                         f'Вас приветствует голосовой помощник!\n'
                         f'Запишите вопрос в голосовом сообщении!')

    # создаю ассистента и процесс для данного пользователя
    assistant_id, thread_id = await def_create_assistant()
    # assistant_current = Assistant(assistant_id, thread_id)  класс убрал поскольку redis не может сохранять списки

    # помещаю в state  для доступа в других обработчиках
    await state.set_data({'assistant_id': assistant_id})
    await state.update_data({'thread_id': thread_id})


@user_router.message(F.voice)
async def def_get_audio(message: types.Message, bot: Bot, state: FSMContext):
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
    question = await def_openai_api_voice_in_text(file_on_disk)
    # удаляю сообщение об ожидании
    await message_wait.delete()
    # текст вопроса
    await message.reply(question)

    # удаляю голосовой файл
    os.remove(file_on_disk)

# вопрос для ИИ
    # сообщение об ожидании
    message_wait = await message.answer('Ожидайте ответ...')

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

    # отправляю вопрос
    answer = await def_openai_api_question(assistant_id, thread_id, question)
    # удаляю сообщение об ожидании
    await message_wait.delete()
    # ответ ИИ
    await message.answer(answer)

# отправляю на преобразование ИИ из текста в файл голосом
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


@user_router.message(Command('new_dialog'))
async def new_dialog_cmd(message: types.Message, state: FSMContext):
    assistant_id, thread_id = await def_create_assistant()
    # помещаю в state  для доступа в других обработчиках
    await state.set_data({'assistant_id': assistant_id})
    await state.update_data({'thread_id': thread_id})

    await message.answer('Открыта новая тема!\n'
                         'Запишите вопрос в голосовом сообщении!')


@user_router.message(Command('about'))
async def about_cmd(message: types.Message):
    await message.answer('Чат-бот на Aiogram, способен принимать голосовые сообщения, '
                         'преобразовывать их в текст, получать ответы на заданные вопросы и '
                         'озвучивать ответы обратно пользователю с использованием асинхронного '
                         'клиента OpenAI API.')


@user_router.message()
async def def_any_message(message: types.Message):
    # обработка ошибок
    await message.answer('Запишите вопрос в голосовом сообщении!')
