"""
Secator integration module for reconPoint.

This module provides all Secator-related functionality:
- Runner: Interface with Secator library
- Orchestrator: High-level scan orchestration
- Config: Configuration conversion
- Parser: Result parsing
- Control: Scan lifecycle control
- Progress: Progress synchronization
- Tasks: Celery task functions
"""

from reconPoint.secator.config import SecatorConfigConverter
from reconPoint.secator.control import SecatorScanController
from reconPoint.secator.orchestrator import ScanOrchestrator
from reconPoint.secator.parser import SecatorParser
from reconPoint.secator.progress import SecatorProgressSync
from reconPoint.secator.runner import SecatorRunner
from reconPoint.secator.service import (
    handle_scan_error,
    run_per_task_secator_scans,
    start_secator_scan,
)
from reconPoint.secator.tasks import build_enriched_targets, initiate_secator_scan


__all__ = [
    "SecatorRunner",
    "SecatorConfigConverter",
    "SecatorParser",
    "SecatorScanController",
    "ScanOrchestrator",
    "SecatorProgressSync",
    "initiate_secator_scan",
    "build_enriched_targets",
    "start_secator_scan",
    "handle_scan_error",
    "run_per_task_secator_scans",
]
