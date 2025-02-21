from pathlib import Path

import config

from openai import OpenAI

client = OpenAI(api_key=config.settings.OPENAI_APIKEY)


# преобразование ИИ голоса из файла в текст
def def_openai_api_voice_in_text(audio_filename: str):
    # открываю аудио файл
    with open(audio_filename, "rb") as audio_file:
        # расшифровка
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            # language='ru'
        )
    return transcript.text


# преобразование ИИ из текста в файл голосом
def def_openai_api_text_in_voice(text: str, user_id):
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    # user_id для создания уникального имени файла
    file_on_disk = Path("voice_tmp", f"output_for_{user_id}.wav")
    # запись на диск
    response.write_to_file(file_on_disk)
    return file_on_disk
