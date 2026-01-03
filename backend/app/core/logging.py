import json
import logging
from logging.config import dictConfig
from pathlib import Path


class JsonFormatter(logging.Formatter):
    def format(self, record):
        record.asctime = self.formatTime(record, self.datefmt)
        log_record = {
            "timestamp": record.asctime,
            "logger": record.name,
            "level": record.levelname,
            "funcName": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
        }

        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info).replace(
                "\n", " | "
            )

        return json.dumps(log_record, ensure_ascii=False, separators=(",", ":"))


def load_logging_config():
    """로깅 설정 파일 로드"""
    config_path = Path(__file__).parent / "logging.json"
    with open(config_path, "r", encoding="utf-8") as f:
        logging_config = json.load(f)
    return logging_config


def setup_logging():
    Path("logs").mkdir(parents=True, exist_ok=True)
    dictConfig(load_logging_config())
