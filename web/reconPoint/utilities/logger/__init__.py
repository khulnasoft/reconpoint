"""
Logger utilities - Generic base logger and specialized loggers.

This module provides:
- BaseLogger: Generic base class for all custom loggers (reusable across the application)
- SecatorAPILogger: Logger for Secator API endpoints (incoming data)
- RunnerLogger: Logger for Secator runner operations (outgoing data)
"""

from reconPoint.utilities.logger.api_logger import SecatorAPILogger, get_secator_api_logger
from reconPoint.utilities.logger.base import BaseLogger
from reconPoint.utilities.logger.module_logger import (
    ModuleLogger,
    format_exception_for_log,
    get_module_logger,
)
from reconPoint.utilities.logger.runner_logger import RunnerLogger, get_runner_logger


__all__ = [
    "BaseLogger",
    "ModuleLogger",
    "format_exception_for_log",
    "get_module_logger",
    "SecatorAPILogger",
    "get_secator_api_logger",
    "RunnerLogger",
    "get_runner_logger",
]
