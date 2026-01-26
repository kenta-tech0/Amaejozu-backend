"""Application configuration"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Amaejozu"
    VERSION: str = "0.1.0"
    DEBUG: bool = True

    # database
    DATABASE_URL: str

    # API keys
    RAKUTEN_APP_ID: str
    RAKUTEN_AFFILIATE_ID: str
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str
    RESEND_API_KEY: str

    # Frontend
    FRONTEND_URL: str = "http://localhost:3000"

    # Email
    RESEND_FROM_EMAIL: str = "Amaejozu <onboarding@resend.dev>"

    model_config = SettingsConfigDict(
        env_file=".env", case_sensitive=True, extra="ignore"
    )


settings = Settings()
