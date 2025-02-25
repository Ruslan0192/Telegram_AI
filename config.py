from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    TOKEN_TG: str
    OPENAI_APIKEY: str
    REDIS_URL: str
    model_config = SettingsConfigDict(env_file=f".env")


# Получаем параметры для загрузки переменных среды
settings = Settings()
