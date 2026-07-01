import logging
import logging.config
from pathlib import Path

LOG_DIR = Path("logs")
LOG_FILE = LOG_DIR / "app.log"
ERROR_LOG_FILE = LOG_DIR / "error.log"

_configured = False


def setup_logging() -> None:
    global _configured
    if _configured:
        return

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
                "detailed": {
                    "format": (
                        "%(asctime)s | %(levelname)s | %(name)s | "
                        "%(pathname)s:%(lineno)d | %(message)s"
                    ),
                    "datefmt": "%Y-%m-%d %H:%M:%S",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
                "app_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "INFO",
                    "formatter": "detailed",
                    "filename": str(LOG_FILE),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
                "error_file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "level": "ERROR",
                    "formatter": "detailed",
                    "filename": str(ERROR_LOG_FILE),
                    "maxBytes": 10 * 1024 * 1024,
                    "backupCount": 10,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["console", "app_file", "error_file"],
            },
            "loggers": {
                "app": {
                    "level": "INFO",
                    "propagate": True,
                },
                "uvicorn": {
                    "level": "INFO",
                    "propagate": True,
                },
                "uvicorn.error": {
                    "level": "INFO",
                    "propagate": True,
                },
                "uvicorn.access": {
                    "level": "INFO",
                    "propagate": True,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                    "propagate": True,
                },
            },
        }
    )

    _configured = True
