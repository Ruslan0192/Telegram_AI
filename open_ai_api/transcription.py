import time
from pathlib import Path

import config

from openai import AsyncOpenAI

client_async = AsyncOpenAI(api_key=config.settings.OPENAI_APIKEY)


# Модуль преобразования ИИ голоса из файла в текст
# **************************************************************************************
async def def_openai_api_voice_in_text(audio_filename: str):
    # открываю аудио файл
    with open(audio_filename, "rb") as audio_file:
        # расшифровка
        transcript = await client_async.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            # temperature=0.5,
            # response_format="verbose_json"
            # language='ru'
        )
    return transcript.text


# Модуль получения ответа от ИИ на вопрос
# **************************************************************************************
# создаю ассистента и процесс
async def def_create_assistant():
    assistant = await client_async.beta.assistants.create(
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}],
    )
    thread = await client_async.beta.threads.create()
    return assistant, thread


# ожидание ответа
async def def_get_answer(assistant_id, thread_id):
    # запуск ассистента
    run = await client_async.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    # # ожидание ответа
    while True:
        runInfo = await client_async.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)
        if runInfo.completed_at:
            break
        # запрос ответа через каждые 0,5 сек
        time.sleep(0.5)

    # Пришел ответ
    messages = await client_async.beta.threads.messages.list(thread_id)
    message_content = messages.data[0].content[0].text.value
    return message_content


# ИИ отвечает на вопрос
async def def_openai_api_question(assistant, thread, question: str):
    # добавляю вопрос в процесс
    await client_async.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=question
    )
    # ожидание ответа
    message_content = await def_get_answer(assistant.id, thread.id)
    return message_content


# Модуль преобразования ИИ из текста в файл голосом
# **************************************************************************************
async def def_openai_api_text_in_voice(text: str, user_id):
    response = await client_async.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    # user_id для создания уникального имени файла
    file_on_disk = Path("voice_tmp", f"output_for_{user_id}.wav")
    # запись на диск
    response.write_to_file(file_on_disk)
    return file_on_disk
