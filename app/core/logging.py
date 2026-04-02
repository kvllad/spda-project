from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path


class JsonFormatter(logging.Formatter):
    _reserved = {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
    }

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in self._reserved and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, ensure_ascii=True)


def configure_logging(level: str, log_file_path: str) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())
    root_logger.handlers.clear()

    formatter = JsonFormatter()
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    log_path = Path(log_file_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_path)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.getLogger("uvicorn.access").disabled = True


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
