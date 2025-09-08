OPENAI_API_KEY = "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"
# app/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Pizza API"
    APP_VERSION: str = "1.0.0"

    class Config:
        case_sensitive = True


settings = Settings()