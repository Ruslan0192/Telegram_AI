import asyncio

from pathlib import Path
# from pydantic import BaseModel

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
        instructions="Вы лучший собеседник на любую тему разговора. "
                     "Предлагайте темы разговоров. "
                     "Используйте предоставленную функцию для определения ценностей пользователя наводящими вопросами.",
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "save_value",
                    "description": "Дать характеристику пользователя из разговора",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "temper": {
                                "type": "string",
                                "description": "Черты характера, например: вежливость, доброта, лживость, раздражительность"
                            },
                            "interests": {
                                "type": "string",
                                "description": "Чем интересуется?"
                            }
                        },
                        "required": ["temper", "interests"],
                        "additionalProperties": False
                    },
                    "strict": True
                }
            }
        ]
    )
    return assistant.id


# создаю процесс
async def def_create_thread():
    thread = await client_async.beta.threads.create()
    return thread.id


# ИИ отвечает на вопрос
async def def_openai_api_question(thread_id: str, question: str, characteristic: str):
    # добавляю вопрос в процесс
    await client_async.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )
    # запуск
    run = await client_async.beta.threads.runs.create_and_poll(thread_id=thread_id,
                                                               assistant_id=config.settings.ASSISTANT_ID)

    # Пришел ответ
    # if run.status == 'completed':
    #     messages = await client_async.beta.threads.messages.list(thread_id)
    #     message_content = messages.data[0].content[0].text.value
    #     return message_content
    # return

    if run.status == 'completed':
        messages = await client_async.beta.threads.messages.list(thread_id)
        print(messages)
    else:
        print(run.status)
        return

    # while not run.required_action:
    #     await asyncio.sleep(1)
    #     print("Checking again...\n")
    #     run = await client_async.beta.threads.runs.retrieve(
    #         thread_id=thread_id,
    #         run_id=run.id
    #     )

    tool_outputs = []
    # Loop through each tool in the required action section
    for tool in run.required_action.submit_tool_outputs.tool_calls:
        if tool.function.name == "save_value":
            tool_outputs.append({
                "tool_call_id": tool.id,
                "output": "57"
            })

    # Submit all tool outputs at once after collecting them in a list
    if tool_outputs:
        try:
            run = await client_async.beta.threads.runs.submit_tool_outputs_and_poll(
                thread_id=thread_id,
                run_id=run.id,
                tool_outputs=tool_outputs
            )
            print("Tool outputs submitted successfully.")
        except Exception as e:
            print("Failed to submit tool outputs:", e)
    else:
        print("No tool outputs to submit.")

    if run.status == 'completed':
        messages = await client_async.beta.threads.messages.list(thread_id=thread_id)
        print(messages)
    else:
        print(run.status)
    return messages.data[0].content[0].text.value


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
