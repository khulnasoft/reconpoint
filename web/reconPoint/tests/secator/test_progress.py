"""
Tests for SecatorProgressSync and map_secator_status_to_reconpoint.
"""

import unittest
from unittest.mock import patch

from reconPoint.definitions import (
    ABORTED_TASK,
    FAILED_TASK,
    INITIATED_TASK,
    RUNNING_BACKGROUND,
    RUNNING_TASK,
    SKIPPED_TASK,
    SUCCESS_TASK,
)
from reconPoint.secator.progress import (
    UNKNOWN_SECATOR_STATUS_FALLBACK,
    SecatorProgressSync,
)


class TestMapSecatorStatusToReconpoint(unittest.TestCase):
    """Test cases for map_secator_status_to_reconpoint."""

    def test_known_statuses_mapped_correctly(self):
        """Known Secator statuses return the expected reconPoint code."""
        cases = [
            ("RUNNING", RUNNING_TASK),
            ("running", RUNNING_TASK),
            ("SUCCESS", SUCCESS_TASK),
            ("FAILURE", FAILED_TASK),
            ("FAILED", FAILED_TASK),
            ("PENDING", INITIATED_TASK),
            ("REVOKED", ABORTED_TASK),
            ("SKIPPED", SKIPPED_TASK),
        ]
        for secator_status, expected in cases:
            with self.subTest(secator_status=secator_status):
                self.assertEqual(
                    SecatorProgressSync.map_secator_status_to_reconpoint(secator_status),
                    expected,
                )

    def test_none_and_empty_status_return_fallback(self):
        """None and empty-string status map to UNKNOWN_SECATOR_STATUS_FALLBACK."""
        self.assertEqual(
            SecatorProgressSync.map_secator_status_to_reconpoint(None),
            UNKNOWN_SECATOR_STATUS_FALLBACK,
        )
        self.assertEqual(
            SecatorProgressSync.map_secator_status_to_reconpoint(""),
            UNKNOWN_SECATOR_STATUS_FALLBACK,
        )
        self.assertEqual(
            SecatorProgressSync.map_secator_status_to_reconpoint("   "),
            UNKNOWN_SECATOR_STATUS_FALLBACK,
        )

    def test_reconpoint_numeric_status_codes_mapped_directly(self):
        """Numeric strings for reconPoint codes are accepted and returned as-is."""
        cases = [
            ("-1", INITIATED_TASK),
            ("0", FAILED_TASK),
            ("1", RUNNING_TASK),
            ("2", SUCCESS_TASK),
            ("3", ABORTED_TASK),
            ("4", RUNNING_BACKGROUND),
            ("5", SKIPPED_TASK),
        ]
        for status_str, expected in cases:
            with self.subTest(status_str=status_str):
                self.assertEqual(
                    SecatorProgressSync.map_secator_status_to_reconpoint(status_str),
                    expected,
                )

    def test_unknown_status_returns_fallback(self):
        """Unknown Secator status returns UNKNOWN_SECATOR_STATUS_FALLBACK."""
        self.assertEqual(
            SecatorProgressSync.map_secator_status_to_reconpoint("UNKNOWN_STATUS"),
            UNKNOWN_SECATOR_STATUS_FALLBACK,
        )
        self.assertEqual(
            SecatorProgressSync.map_secator_status_to_reconpoint("CUSTOM"),
            UNKNOWN_SECATOR_STATUS_FALLBACK,
        )

    def test_unknown_status_fallback_equals_initiated_task(self):
        """Fallback for unknown status is INITIATED_TASK."""
        self.assertEqual(UNKNOWN_SECATOR_STATUS_FALLBACK, INITIATED_TASK)

    @patch("reconPoint.secator.progress.logger")
    def test_unknown_status_logs_warning(self, mock_logger):
        """Unknown Secator status logs a warning via log_line."""
        SecatorProgressSync.map_secator_status_to_reconpoint("UNKNOWN_STATUS")
        mock_logger.log_line.assert_called_once()
        call_args = mock_logger.log_line.call_args
        self.assertEqual(call_args[1].get("level"), "warning")
        self.assertIn("UNKNOWN_STATUS", str(call_args[0]))
        self.assertIn(str(UNKNOWN_SECATOR_STATUS_FALLBACK), str(call_args[0]))
