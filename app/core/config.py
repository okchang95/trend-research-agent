from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    OPENAI_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None


settings = Config()
