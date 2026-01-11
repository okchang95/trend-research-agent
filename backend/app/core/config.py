from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # extra="ignore"
    )
    OPENAI_API_KEY: str
    TAVILY_API_KEY: str

    LANGCHAIN_TRACING_V2: str
    LANGSMITH_ENDPOINT: str
    LANGSMITH_API_KEY: str
    LANGSMITH_PROJECT: str

    MONGODB_URI: str
    MONGODB_DB: str


@lru_cache
def get_config() -> Config:
    return Config()
