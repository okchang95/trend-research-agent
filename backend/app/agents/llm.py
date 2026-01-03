from langchain_openai import ChatOpenAI

from app.core.config import Config

config = Config()


SCOPING_LLM = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.5,
    api_key=config.OPENAI_API_KEY,
)
RESEARCHER_LLM = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0,
    api_key=config.OPENAI_API_KEY,
)
WRITER_LLM = ChatOpenAI(
    model="gpt-4.1-mini",
    temperature=0.2,
    api_key=config.OPENAI_API_KEY,
)
