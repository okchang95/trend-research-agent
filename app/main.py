import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.api.router import router
from app.core.logging import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터
app.include_router(router)

# 정적 파일 서빙 (프론트엔드)
ui_path = Path(__file__).parent.parent / "ui"
if ui_path.exists():
    app.mount("/static", StaticFiles(directory=str(ui_path)), name="static")
    
    @app.get("/")
    async def read_root():
        """루트 경로에서 index.html 서빙"""
        return FileResponse(str(ui_path / "index.html"))


@app.get("/health")
def health_check():
    return {"status": "ok"}
