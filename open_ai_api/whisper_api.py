import config

from openai import OpenAI

client = OpenAI(api_key=config.settings.OPENAI_APIKEY)


def get_openai_api_transcription(audio_filename):
    # открываю видео
    with open(audio_filename, "rb") as audio_file:
        # расшифровка голоса из файла в текст
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file
            # language='ru'
        )
    return transcript


