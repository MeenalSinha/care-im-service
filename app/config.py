import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    CARE_API_BASE_URL: str = "https://care.api"
    CARE_API_KEY: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "your_verify_token"
    WHATSAPP_ACCESS_TOKEN: str = "your_access_token"
    WHATSAPP_PHONE_NUMBER_ID: str = "your_phone_id"
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"
    SESSION_EXPIRY: int = 3600 * 24 * 7 # 7 Days
    SECRET_KEY: str = "supersecret"

    class Config:
        env_file = ".env"

settings = Settings()
