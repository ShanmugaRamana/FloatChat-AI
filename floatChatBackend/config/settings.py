# config/settings.py

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str
    OPENROUTER_MODEL: str
    OPENROUTER_API_BASE: str = "https://openrouter.ai/api/v1"
    APP_SITE_URL: str = "http://localhost:3000"
    
    # Application Settings
    APP_HOST: str = "127.0.0.1"
    APP_PORT: int = 8000

settings = Settings()