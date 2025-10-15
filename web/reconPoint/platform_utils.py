"""
Platform Detection and Optimization Utilities for reconPoint
Provides platform-specific optimizations for ARM and x86 architectures
"""

import os
import platform
import psutil
import logging
from typing import Dict, Tuple, Optional

logger = logging.getLogger(__name__)


class PlatformDetector:
    """
    Detects the current platform and provides optimization recommendations
    """
    
    def __init__(self):
        self.machine = platform.machine().lower()
        self.system = platform.system().lower()
        self.processor = platform.processor().lower()
        self._platform_info = None
    
    @property
    def is_arm(self) -> bool:
        """Check if running on ARM architecture"""
        return any(arch in self.machine for arch in ['arm', 'aarch'])
    
    @property
    def is_arm64(self) -> bool:
        """Check if running on ARM64 (aarch64)"""
        return 'aarch64' in self.machine or 'arm64' in self.machine
    
    @property
    def is_arm32(self) -> bool:
        """Check if running on ARM32 (armv7)"""
        return self.is_arm and not self.is_arm64
    
    @property
    def is_x86_64(self) -> bool:
        """Check if running on x86_64 (AMD64)"""
        return self.machine in ['x86_64', 'amd64', 'x64']
    
    @property
    def is_raspberry_pi(self) -> bool:
        """Check if running on Raspberry Pi"""
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read().lower()
                return 'raspberry pi' in cpuinfo or 'bcm' in cpuinfo
        except FileNotFoundError:
            return False
    
    def get_platform_info(self) -> Dict[str, any]:
        """Get comprehensive platform information"""
        if self._platform_info is None:
            self._platform_info = {
                'architecture': self.machine,
                'system': self.system,
                'processor': self.processor,
                'is_arm': self.is_arm,
                'is_arm64': self.is_arm64,
                'is_arm32': self.is_arm32,
                'is_x86_64': self.is_x86_64,
                'is_raspberry_pi': self.is_raspberry_pi,
                'cpu_count': psutil.cpu_count(logical=True),
                'cpu_count_physical': psutil.cpu_count(logical=False),
                'total_memory': psutil.virtual_memory().total,
                'total_memory_gb': round(psutil.virtual_memory().total / (1024**3), 2),
                'platform_type': self._get_platform_type(),
            }
        return self._platform_info
    
    def _get_platform_type(self) -> str:
        """Get a human-readable platform type"""
        if self.is_raspberry_pi:
            return 'Raspberry Pi'
        elif self.is_arm64:
            return 'ARM64 Server'
        elif self.is_arm32:
            return 'ARM32 Device'
        elif self.is_x86_64:
            return 'x86_64 Server'
        else:
            return 'Unknown'
    
    def get_recommended_workers(self) -> int:
        """Get recommended number of workers based on platform"""
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if self.is_arm32:
            # ARM32 devices are typically resource-constrained
            return min(2, cpu_count)
        elif self.is_arm64:
            # ARM64 can handle more, but still conservative
            if memory_gb < 2:
                return 1
            elif memory_gb < 4:
                return 2
            else:
                return min(4, cpu_count)
        else:
            # x86_64 - standard calculation
            return min(cpu_count * 2 + 1, 8)
    
    def get_recommended_celery_concurrency(self) -> Tuple[int, int]:
        """Get recommended Celery min/max concurrency"""
        cpu_count = psutil.cpu_count(logical=True)
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        if self.is_arm32:
            return (1, 2)
        elif self.is_arm64:
            if memory_gb < 2:
                return (1, 2)
            elif memory_gb < 4:
                return (1, 3)
            else:
                return (2, 5)
        else:
            # x86_64
            return (2, min(cpu_count * 2, 10))
    
    def get_memory_limits(self) -> Dict[str, int]:
        """Get recommended memory limits for different services"""
        total_memory = psutil.virtual_memory().total
        memory_gb = total_memory / (1024**3)
        
        if self.is_arm32 or memory_gb < 2:
            return {
                'web': 512 * 1024 * 1024,  # 512MB
                'celery': 512 * 1024 * 1024,  # 512MB
                'db': 256 * 1024 * 1024,  # 256MB
                'redis': 128 * 1024 * 1024,  # 128MB
            }
        elif self.is_arm64 and memory_gb < 4:
            return {
                'web': 1 * 1024 * 1024 * 1024,  # 1GB
                'celery': 1 * 1024 * 1024 * 1024,  # 1GB
                'db': 512 * 1024 * 1024,  # 512MB
                'redis': 256 * 1024 * 1024,  # 256MB
            }
        else:
            return {
                'web': 2 * 1024 * 1024 * 1024,  # 2GB
                'celery': 2 * 1024 * 1024 * 1024,  # 2GB
                'db': 1 * 1024 * 1024 * 1024,  # 1GB
                'redis': 512 * 1024 * 1024,  # 512MB
            }
    
    def get_optimization_settings(self) -> Dict[str, any]:
        """Get platform-specific optimization settings"""
        settings = {
            'GUNICORN_WORKERS': self.get_recommended_workers(),
            'GUNICORN_THREADS': 2 if self.is_arm else 4,
            'CELERY_MIN_CONCURRENCY': self.get_recommended_celery_concurrency()[0],
            'CELERY_MAX_CONCURRENCY': self.get_recommended_celery_concurrency()[1],
            'PYTHONOPTIMIZE': '1' if self.is_arm else '0',
            'MALLOC_ARENA_MAX': '2' if self.is_arm else '4',
        }
        
        # ARM-specific optimizations
        if self.is_arm:
            settings.update({
                'ENABLE_BROWSER_SCANNING': not self.is_arm32,  # Disable on ARM32
                'SCAN_TIMEOUT_MULTIPLIER': 1.5 if self.is_arm32 else 1.2,
                'MAX_PARALLEL_SCANS': 2 if self.is_arm32 else 4,
            })
        
        return settings
    
    def log_platform_info(self):
        """Log platform information for debugging"""
        info = self.get_platform_info()
        logger.info("=" * 60)
        logger.info("Platform Information:")
        logger.info("=" * 60)
        logger.info(f"Platform Type: {info['platform_type']}")
        logger.info(f"Architecture: {info['architecture']}")
        logger.info(f"System: {info['system']}")
        logger.info(f"CPU Cores: {info['cpu_count']} ({info['cpu_count_physical']} physical)")
        logger.info(f"Total Memory: {info['total_memory_gb']} GB")
        logger.info(f"Is ARM: {info['is_arm']}")
        logger.info(f"Is ARM64: {info['is_arm64']}")
        logger.info(f"Is ARM32: {info['is_arm32']}")
        logger.info(f"Is Raspberry Pi: {info['is_raspberry_pi']}")
        logger.info("=" * 60)
        
        # Log optimization recommendations
        optimizations = self.get_optimization_settings()
        logger.info("Recommended Optimizations:")
        logger.info("=" * 60)
        for key, value in optimizations.items():
            logger.info(f"{key}: {value}")
        logger.info("=" * 60)


class PerformanceMonitor:
    """
    Monitor system performance and provide warnings for resource constraints
    """
    
    def __init__(self, detector: Optional[PlatformDetector] = None):
        self.detector = detector or PlatformDetector()
    
    def check_system_resources(self) -> Dict[str, any]:
        """Check current system resource usage"""
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_available_gb': memory.available / (1024**3),
            'disk_percent': disk.percent,
            'disk_free_gb': disk.free / (1024**3),
            'swap_percent': psutil.swap_memory().percent if hasattr(psutil, 'swap_memory') else 0,
        }
    
    def get_resource_warnings(self) -> list:
        """Get warnings for resource constraints"""
        warnings = []
        resources = self.check_system_resources()
        
        # CPU warnings
        if resources['cpu_percent'] > 90:
            warnings.append({
                'type': 'cpu',
                'level': 'critical',
                'message': f"CPU usage is very high: {resources['cpu_percent']:.1f}%"
            })
        elif resources['cpu_percent'] > 75:
            warnings.append({
                'type': 'cpu',
                'level': 'warning',
                'message': f"CPU usage is high: {resources['cpu_percent']:.1f}%"
            })
        
        # Memory warnings
        if resources['memory_percent'] > 90:
            warnings.append({
                'type': 'memory',
                'level': 'critical',
                'message': f"Memory usage is very high: {resources['memory_percent']:.1f}%"
            })
        elif resources['memory_percent'] > 75:
            warnings.append({
                'type': 'memory',
                'level': 'warning',
                'message': f"Memory usage is high: {resources['memory_percent']:.1f}%"
            })
        
        # Disk warnings
        if resources['disk_percent'] > 90:
            warnings.append({
                'type': 'disk',
                'level': 'critical',
                'message': f"Disk usage is very high: {resources['disk_percent']:.1f}%"
            })
        elif resources['disk_percent'] > 80:
            warnings.append({
                'type': 'disk',
                'level': 'warning',
                'message': f"Disk usage is high: {resources['disk_percent']:.1f}%"
            })
        
        # Swap warnings (especially important for ARM devices)
        if resources['swap_percent'] > 50 and self.detector.is_arm:
            warnings.append({
                'type': 'swap',
                'level': 'warning',
                'message': f"Swap usage is high: {resources['swap_percent']:.1f}% (may impact performance on ARM)"
            })
        
        return warnings
    
    def get_temperature(self) -> Optional[float]:
        """Get CPU temperature (if available, mainly for Raspberry Pi)"""
        try:
            # Try Raspberry Pi method
            with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
                temp = float(f.read().strip()) / 1000.0
                return temp
        except (FileNotFoundError, ValueError):
            pass
        
        try:
            # Try psutil sensors (if available)
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except (AttributeError, KeyError):
            pass
        
        return None
    
    def check_thermal_throttling(self) -> Optional[Dict[str, any]]:
        """Check for thermal throttling (Raspberry Pi specific)"""
        if not self.detector.is_raspberry_pi:
            return None
        
        temp = self.get_temperature()
        if temp is None:
            return None
        
        status = {
            'temperature': temp,
            'throttled': temp > 80,
            'warning': temp > 70,
            'level': 'normal'
        }
        
        if temp > 80:
            status['level'] = 'critical'
            status['message'] = f"CPU temperature is critical: {temp:.1f}°C (throttling likely)"
        elif temp > 70:
            status['level'] = 'warning'
            status['message'] = f"CPU temperature is high: {temp:.1f}°C"
        else:
            status['message'] = f"CPU temperature is normal: {temp:.1f}°C"
        
        return status


# Global instance
_detector = None
_monitor = None


def get_platform_detector() -> PlatformDetector:
    """Get global platform detector instance"""
    global _detector
    if _detector is None:
        _detector = PlatformDetector()
    return _detector


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance"""
    global _monitor
    if _monitor is None:
        _monitor = PerformanceMonitor()
    return _monitor


def apply_platform_optimizations():
    """Apply platform-specific optimizations to environment"""
    detector = get_platform_detector()
    optimizations = detector.get_optimization_settings()
    
    # Apply to environment
    for key, value in optimizations.items():
        if isinstance(value, bool):
            os.environ[key] = '1' if value else '0'
        else:
            os.environ[key] = str(value)
    
    # Log platform info
    detector.log_platform_info()
    
    return optimizations


# Auto-detect and log on import
if __name__ != '__main__':
    try:
        detector = get_platform_detector()
        logger.info(f"Detected platform: {detector.get_platform_info()['platform_type']}")
    except Exception as e:
        logger.warning(f"Failed to detect platform: {e}")
