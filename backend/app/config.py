from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./reviews.db"
    secret_key: str = "dev-secret-change-me-to-a-real-32-byte-key"
    token_expire_days: int = 30


settings = Settings()
