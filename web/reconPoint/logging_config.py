import os
import logging.config
from pathlib import Path
from django.utils.log import DEFAULT_LOGGING

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FORMAT_JSON = '{"time": "%(asctime)s", "name": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'

# Ensure logs directory exists
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# Log file paths
DEBUG_LOG = str(LOG_DIR / "debug.log")
INFO_LOG = str(LOG_DIR / "info.log")
WARNING_LOG = str(LOG_DIR / "warning.log")
ERROR_LOG = str(LOG_DIR / "error.log")
CRITICAL_LOG = str(LOG_DIR / "critical.log")
CELERY_LOG = str(LOG_DIR / "celery.log")

# Logging configuration
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "json": {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": LOG_FORMAT_JSON,
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "django.server": DEFAULT_LOGGING["formatters"]["django.server"],
    },
    "handlers": {
        "console": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "console_json": {
            "level": LOG_LEVEL,
            "class": "logging.StreamHandler",
            "formatter": "json",
        },
        "file_debug": {
            "level": "DEBUG",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": DEBUG_LOG,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_info": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": INFO_LOG,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_warning": {
            "level": "WARNING",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": WARNING_LOG,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_error": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": ERROR_LOG,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "file_critical": {
            "level": "CRITICAL",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": CRITICAL_LOG,
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
            "formatter": "verbose",
        },
        "celery": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": CELERY_LOG,
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 5,
        },
        "django.server": DEFAULT_LOGGING["handlers"]["django.server"],
    },
    "loggers": {
        "": {
            "handlers": ["console", "file_info", "file_warning", "file_error", "file_critical"],
            "level": "DEBUG",
            "propagate": True,
        },
        "django": {
            "handlers": ["console", "file_warning", "file_error", "file_critical"],
            "level": "INFO",
            "propagate": False,
        },
        "django.request": {
            "handlers": ["file_error", "file_critical"],
            "level": "ERROR",
            "propagate": False,
        },
        "django.server": {
            "handlers": ["django.server"],
            "level": "INFO",
            "propagate": False,
        },
        "celery": {
            "handlers": ["celery", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "reconpoint": {
            "handlers": ["console", "file_info", "file_warning", "file_error", "file_critical"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "api": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "scan": {
            "handlers": ["console", "file_info", "file_warning", "file_error"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}

# Configure logging
logging.config.dictConfig(LOGGING)

# Disable noisy loggers
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("botocore").setLevel(logging.WARNING)
logging.getLogger("boto3").setLevel(logging.WARNING)
logging.getLogger("s3transfer").setLevel(logging.WARNING)
logging.getLogger("celery.worker.strategy").setLevel(logging.WARNING)
logging.getLogger("faker").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
