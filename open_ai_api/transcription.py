from pathlib import Path
from pydantic import BaseModel

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
        )
    return transcript.text


# Модуль получения ответа от ИИ на вопрос
# **************************************************************************************
# создаю ассистента
async def def_create_assistant():
    assistant = await client_async.beta.assistants.create(
        model="gpt-4-1106-preview",
        tools=[{"type": "code_interpreter"}],
    )
    thread = await def_create_thread()
    return assistant.id, thread.id


# создаю процесс
async def def_create_thread():
    return await client_async.beta.threads.create()


# ИИ отвечает на вопрос
async def def_openai_api_question(assistant_id: any, thread_id: any, question: str, characteristic: str):
    # добавляю вопрос в процесс
    await client_async.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )
    # запуск
    run = await client_async.beta.threads.runs.create_and_poll(thread_id=thread_id,
                                                               assistant_id=assistant_id,
                                                               instructions=characteristic)

    # Пришел ответ
    if run.completed_at:
        messages = await client_async.beta.threads.messages.list(thread_id)
        message_content = messages.data[0].content[0].text.value
        return message_content
    return


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


# class OutText(BaseModel):
#     output: str


async def save_value(content_system: str, content_user: str):
    completion = await client_async.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system",
             "content": content_system},
            {"role": "user",
             "content": content_user}
        ],
        # response_format=OutText,
    )
    text_out = completion.choices[0].message

    # проверка соответствия классу
    if text_out.refusal:
        return  # для выполнения задания, здесь False
    else:
        return text_out.content   # для выполнения задания, здесь True
