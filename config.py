from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN_TG: str
    OPENAI_APIKEY: str
    ASSISTANT_ID: str
    REDIS_URL: str
    DB_URL: str
    AMPLITUDE_APIKEY: str

    model_config = SettingsConfigDict(env_file=".env")


# Получаем параметры для загрузки переменных среды
settings = Settings()


