"""
Django management command for running performance benchmarks
Usage: python manage.py benchmark_performance [--save] [--compare previous.json]
"""

from reconPoint.performance_monitor import Command
