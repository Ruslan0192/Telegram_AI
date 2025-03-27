from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN_TG: str

    OPENAI_APIKEY: str

    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_PORT: str

    REDIS_DB: str
    REDIS_HOST: str
    REDIS_PORT: str

    AMPLITUDE_APIKEY: str

    model_config = SettingsConfigDict(env_file=".env")


# Получаем параметры для загрузки переменных среды
settings = Settings()


