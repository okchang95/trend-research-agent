from langchain_openai import ChatOpenAI

from app.core.config import settings

openai_api_key = settings.OPENAI_API_KEY


class LLMSetup:
    intent_analysis_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=openai_api_key,
    )
    data_collection_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=openai_api_key,
    )
    generate_response_llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        api_key=openai_api_key,
    )
