"""Application configuration """
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Amaejozu"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # database
    DATABASE_URL: str

    # API keys
    RAKUTEN_API_KEY: str
    AZURE_OPENAI_KEY: str
    RESEND_API_KEY: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()