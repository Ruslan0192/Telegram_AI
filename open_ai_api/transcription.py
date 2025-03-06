import json

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
        instructions="Вы бот погоды. Используйте функции для ответа на вопросы.",
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_current_temperature",
                    "description": "Получите температуру для определенного местоположения",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "Город, например, Казань"
                            },
                            "unit": {
                                "type": "string",
                                "enum": ["Цельсий", "Фаренгейт"],
                                "description": "Единица измерения температуры, которую нужно использовать. "
                                               "Определите это по местоположению пользователя."
                            }
                        },
                        "required": ["location", "unit"]
                    }
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
async def def_openai_api_question(thread_id: str, question: str):
    # добавляю вопрос в процесс
    await client_async.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )
    # запуск
    run = await client_async.beta.threads.runs.create_and_poll(thread_id=thread_id,
                                                               assistant_id=config.settings.ASSISTANT_ID
                                                               )

    # Пришел ответ
    if run.status == 'completed':
        try:
            messages = await client_async.beta.threads.messages.list(thread_id)
            message_content = messages.data[0].content[0].text.value
            return message_content, None
        except Exception as e:
            print(f'Failed to get messages: {e}')
            return 'Ошибка обработки', None

    elif run.status == 'requires_action':
        try:
            tool_outputs = []
            for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                tool_outputs.append({"tool_call_id": tool_call.id, "output": "success"})

            tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
            name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            try:
                run = await client_async.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            except Exception as e:
                print(f'Failed to submit tool outputs: {e}')
                return 'Ошибка обработки', None

            if name == 'get_current_temperature':
                return 'get_current_temperature', arguments
            else:
                print(f'Unknown tool name: {name}')
                return 'Ошибка обработки', None

        except Exception as e:
            print(f'Failed to submit tool outputs: {e}')
            return 'Ошибка обработки', None
    else:
        print(f'Unexpected run status: {run.status}')
        return 'Ошибка обработки', None


class ContentValidation(BaseModel):
    location: str
    unit: str
    validation: bool


async def def_completions_validation(question, arguments):
    completion = await client_async.beta.chat.completions.parse(
        model="gpt-4o-2024-08-06",
        messages=[
            {"role": "system", "content":
                f"Определи город, единицу измерения температуры  и согласно локации."
                f"Проверь  на соответствие  город с {arguments['location']} и единицу измерения с {arguments['unit']}"},
            {"role": "user", "content": question}
        ],
        response_format=ContentValidation,
    )
    compliance = completion.choices[0].message.parsed
    return compliance.validation


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
