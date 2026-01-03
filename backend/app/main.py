import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import router
from app.core.config import Config
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 환경변수 로딩 및 LangSmith tracking 설정
    config = Config()

    # LangChain이 자동으로 tracking을 시작하도록 환경변수 설정
    # LangChain은 os.environ에서 직접 읽으므로 여기서 설정해야 함
    if config.LANGCHAIN_TRACING_V2:
        os.environ["LANGCHAIN_TRACING_V2"] = config.LANGCHAIN_TRACING_V2
    if config.LANGSMITH_API_KEY:
        os.environ["LANGSMITH_API_KEY"] = config.LANGSMITH_API_KEY
    if config.LANGSMITH_ENDPOINT:
        os.environ["LANGSMITH_ENDPOINT"] = config.LANGSMITH_ENDPOINT
    if config.LANGSMITH_PROJECT:
        os.environ["LANGSMITH_PROJECT"] = config.LANGSMITH_PROJECT

    logger.info(f"LangSmith tracking enabled: {config.LANGCHAIN_TRACING_V2}")
    logger.info(f"LangSmith project: {config.LANGSMITH_PROJECT}")

    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터 (/api prefix)
app.include_router(router, prefix="/api")


@app.get("/health")
def health_check():
    return {"status": "ok"}
