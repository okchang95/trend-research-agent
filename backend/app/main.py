import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat.router import router as chat_router
from app.api.users.router import router as users_router
from app.api.threads.router import router as threads_router

from app.core.logging import setup_logging
from app.core.lifespan import lifespan

# 로깅 설정
setup_logging()
logger = logging.getLogger(__name__)


# FastAPI 애플리케이션 생성 factory
def create_app() -> FastAPI:
    # FastAPI 애플리케이션 생성
    app = FastAPI(lifespan=lifespan)

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API 라우터 등록
    PREFIX = "/api"
    app.include_router(chat_router, prefix=PREFIX, tags=["chat"])
    app.include_router(users_router, prefix=PREFIX, tags=["users"])
    app.include_router(threads_router, prefix=PREFIX, tags=["threads"])

    # 상태 체크 엔드포인트
    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
