import json
import os

from pathlib import Path
from pydantic import BaseModel

from openai import AsyncOpenAI

from config import settings

client_async = AsyncOpenAI(api_key=settings.OPENAI_APIKEY)
PATH_STORE = 'store_files/'


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


# **************************************************************************************
# создаю ассистента
async def def_create_assistant():
    assistant = await client_async.beta.assistants.create(
        instructions="Вы бот подбора профессии. "
                     "Используйте все функции для определения ее аргументов при ответе на вопросы.",
        model="gpt-4o",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_positive_values",
                    "description": "Определите качества/ценности человека для выбранной профессии",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "positive_values_human": {
                                "type": "string",
                                "description": "Ценности подходят, например аналитический склад ума, усидчивость."
                            },
                        },
                        "required": ["positive_values_human"]
                    }
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_negative_values",
                    "description": "Определите не подходящие качества/ценности человека для выбранной профессии",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "negative_values_human": {
                                "type": "string",
                                "description": "Ценности не подходят, например тревожность, страх, невнимательность"
                            },
                        },
                        "required": ["negative_values_human"]
                    }
                }
            }
        ]
    )
    return assistant.id


# Создаю вектор хранилища
async def def_create_vector_assistant(assistant_id: str):
    vector_store = await client_async.beta.vector_stores.create(name="Качества человека")

    # Ready the files for upload to OpenAI
    file_list = os.listdir(PATH_STORE)
    file_streams = [open(PATH_STORE + name, "rb") for name in file_list]

    # Use the upload and poll SDK helper to upload the files, add them to the vector store,
    # and poll the status of the file batch for completion.
    file_batch = await client_async.beta.vector_stores.file_batches.upload_and_poll(
        vector_store_id=vector_store.id, files=file_streams
    )

    # You can print the status and the file counts of the batch to see the result of this operation.
    # print(file_batch.status)
    print(file_batch.file_counts)

    # обновляю ассистента для работы с файлами
    assistant = await client_async.beta.assistants.update(
        assistant_id=assistant_id,
        tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        instructions='Вы отвечаете на вопросы на основе предоставленного вам файла или файлов.'
    )
    return assistant.id


# создаю процесс
async def def_create_thread(file_name: str):
    # thread = await client_async.beta.threads.create()
    message_file = await client_async.files.create(
        file=open(file_name, "rb"), purpose="assistants"
    )
    # Create a thread and attach the file to the message
    thread = await client_async.beta.threads.create(
        messages=[
            {
                "role": "user",
                "content": "'Вы отвечаете на вопросы на основе предоставленного вам файла или файлов.'",
                # Attach the new file to the message.
                "attachments": [
                    {"file_id": message_file.id, "tools": [{"type": "file_search"}]}
                ],
            }
        ]
    )
    print(thread.tool_resources.file_search)
    return thread.id


# Модуль получения ответа от ИИ на вопрос
# **************************************************************************************
async def def_openai_api_file_search(assistant_id: str, thread_id: str, question: str):
    # добавляю вопрос в процесс
    await client_async.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=question
    )

    # Поиск информации в хранилище по векторам
    run = await client_async.beta.threads.runs.create_and_poll(thread_id=thread_id, assistant_id=assistant_id)

    # Пришел ответ
    if run.status == 'completed':
        messages = await client_async.beta.threads.messages.list(thread_id=thread_id, run_id=run.id)
        message_content = messages.data[0].content[0].text
        message_answer = message_content.value

        annotations = message_content.annotations

        if annotations:
            citations = []
            answer = []
            for index, annotation in enumerate(annotations):
                # messages_content.value = messages_content.value.replace(annotation.text, f"[{index}]")
                # if file_citation := getattr(annotation, "file_citation", None):
                #     cited_file = await client_async.files.retrieve(file_citation.file_id)
                #     citations.append(f"[{index}] {cited_file.filename}")
                if annotation.type == "file_path":
                    answer.insert(0, {"type": "file",
                                      "file": await download_file(annotation.file_path.file_id),
                                      "filename": os.path.basename(annotation.text.split(":")[-1])
                                      },
                                  )
            return answer, None
        return message_answer, None

    elif run.status == 'requires_action':
        # отрабатываю функции
        tool_outputs = []
        arguments = {}
        for tool_call in run.required_action.submit_tool_outputs.tool_calls:

            if tool_call.function.name == "get_positive_values":
                argument_dict = json.loads(tool_call.function.arguments)
                argument = argument_dict["positive_values_human"]

                tool_outputs.append({"tool_call_id": tool_call.id, "output": argument})
                arguments.update({'positive_values_human': argument})

            elif tool_call.function.name == "get_negative_values":
                argument_dict = json.loads(tool_call.function.arguments)
                argument = argument_dict["negative_values_human"]

                tool_outputs.append({"tool_call_id": tool_call.id, "output": argument})
                arguments.update({'negative_values_human': argument})

        if tool_outputs:
            # # ценности определены, проверяю на соответствие
            arguments = await def_completions_validation(question, arguments)

            if not arguments:
                return 'Качества человека не прошли валидацию, опишите профессию подробнее', None

            try:
                run = await client_async.beta.threads.runs.submit_tool_outputs_and_poll(
                    thread_id=thread_id,
                    run_id=run.id,
                    tool_outputs=tool_outputs
                )
            except Exception as e:
                print(f'Failed to submit tool outputs: {e}')
                return 'Ошибка запуска с параметрами', arguments

            if run.status == 'completed':
                messages = await client_async.beta.threads.messages.list(thread_id=thread_id)
                message_content = messages.data[0].content[0].text.value

                # await def_create_vector_assistant()
                return message_content, arguments

            return 'Ошибка ожидания ответа. Повторите вопрос.', arguments
        return 'Качества человека не определены', None
    return 'Ошибка обработки', None


async def download_file(file_id: str) -> str:
    file_content = await client_async.files.content(file_id)
    content = file_content.read()
    with open(f"/tmp/{file_id}", "wb") as f:
        f.write(content)
    return f"/tmp/{file_id}"


class ContentValidation(BaseModel):
    values: str
    validation: bool


async def def_completions_validation(question: str, arguments: dict):
    validation = {}

    for key, value in arguments.items():
        if key == 'positive_values_human':
            content = f"Определи ценности/качества человека по выбранной профессии. " \
                      f"Проверь  на соответствие  ценности с {value}"
        elif key == 'negative_values_human':
            content = f"Определи не подходящие ценности/качества человека по выбранной профессии." \
                      f"Проверь  на соответствие  ценности с {value}"
        else:
            return None

        completion = await client_async.beta.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": content},
                {"role": "user", "content": question}
            ],
            response_format=ContentValidation,
        )
        compliance = completion.choices[0].message.parsed
        if compliance.validation:
            validation.update({key: arguments[key]})

    return validation


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
