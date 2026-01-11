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
    mongo_client = AsyncMongoClient(
        config.MONGODB_URI,
        # maxPoolSize=config.MAX_CONNECTIONS_COUNT,
        # minPoolSize=config.MIN_CONNECTIONS_COUNT,
        # serverSelectionTimeoutMS=config.SERVER_SELECTION_TIMEOUT_MS
    )

    # db 연결 확인
    try:
        ping_response = await mongo_client.admin.command("ping")
        if int(ping_response["ok"]) != 1:
            raise Exception("Problem connecting to database cluster.")
        logger.info(f"MongoDB connected successfully")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise RuntimeError(f"Error connecting to MongoDB: {e}")

    # fastapi app state에 저장
    app.state.mongo_client = mongo_client
    app.state.mongo_db = mongo_client[config.MONGODB_DB]

    logger.info("MongoDB client initialized")

    try:
        yield
    finally:
        # 종료 시 자원 정리
        await mongo_client.close()
        logger.info("MongoDB client closed")
