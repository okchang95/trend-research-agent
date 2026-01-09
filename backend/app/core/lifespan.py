import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pymongo import AsyncMongoClient

from app.core.config import get_config

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 환경변수 로딩
    config = get_config()

    # LangSmith tracking 설정
    os.environ["LANGCHAIN_TRACING_V2"] = config.LANGCHAIN_TRACING_V2
    os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
    os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT
    os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT
    logger.info(f"LangSmith tracking enabled: {config.LANGCHAIN_TRACING_V2}")
    logger.info(f"LangSmith project: {config.LANGSMITH_PROJECT}")

    # MongoDB 연결, fastapi app state에 저장
    mongo_client = AsyncMongoClient(config.MONGODB_URI)
    app.state.mongo_client = mongo_client
    app.state.mongo_db = mongo_client[config.MONGODB_DB]

    logger.info("MongoDB client initialized")

    try:
        yield
    finally:
        # 종료 시 자원 정리
        mongo_client.close()
        logger.info("MongoDB client closed")
