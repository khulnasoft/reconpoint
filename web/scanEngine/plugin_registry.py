"""
Plugin registry for discovering and managing available plugins.
"""

from dataclasses import dataclass, field
import inspect
from typing import Any, Callable, Dict, List, Optional

from django.utils import timezone

from reconPoint.utilities.logger import get_module_logger


PREFIX_PLUGIN = "[PLUGIN]"
logger = get_module_logger(__name__)


@dataclass
class PluginInfo:
    """Metadata about a registered plugin."""

    name: str
    slug: str
    version: str
    description: str
    category: str
    author: str
    entry_point: str
    config_schema: Dict[str, Any] = field(default_factory=dict)
    required_permissions: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    execute: Optional[Callable] = None


@dataclass
class PluginResult:
    """Result from plugin execution."""

    success: bool
    output: Any = None
    error: Optional[str] = None
    duration_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class PluginRegistry:
    """
    Central registry for plugin discovery and management.
    Plugins can be registered at startup or dynamically loaded.
    """

    _plugins: Dict[str, PluginInfo] = {}
    _executors: Dict[str, Callable] = {}

    @classmethod
    def register(
        cls,
        name: str,
        slug: str,
        version: str,
        description: str,
        category: str,
        author: str,
        entry_point: str = "run",
        config_schema: Dict[str, Any] = None,
        required_permissions: List[str] = None,
        tags: List[str] = None,
        execute: Callable = None,
    ) -> None:
        """Register a plugin with the registry."""
        plugin_info = PluginInfo(
            name=name,
            slug=slug,
            version=version,
            description=description,
            category=category,
            author=author,
            entry_point=entry_point,
            config_schema=config_schema or {},
            required_permissions=required_permissions or [],
            tags=tags or [],
            execute=execute,
        )
        cls._plugins[slug] = plugin_info
        if execute:
            cls._executors[slug] = execute
        logger.log_line(PREFIX_PLUGIN, "REGISTER", f"Registered plugin: {name} ({slug})")

    @classmethod
    def unregister(cls, slug: str) -> bool:
        """Unregister a plugin from the registry."""
        if slug in cls._plugins:
            del cls._plugins[slug]
            cls._executors.pop(slug, None)
            logger.log_line(PREFIX_PLUGIN, "UNREGISTER", f"Unregistered plugin: {slug}")
            return True
        return False

    @classmethod
    def get(cls, slug: str) -> Optional[PluginInfo]:
        """Get a plugin by slug."""
        return cls._plugins.get(slug)

    @classmethod
    def list_all(cls) -> List[PluginInfo]:
        """List all registered plugins."""
        return list(cls._plugins.values())

    @classmethod
    def list_by_category(cls, category: str) -> List[PluginInfo]:
        """List plugins by category."""
        return [p for p in cls._plugins.values() if p.category == category]

    @classmethod
    def search(cls, query: str) -> List[PluginInfo]:
        """Search plugins by name, description, or tags."""
        query_lower = query.lower()
        return [
            p
            for p in cls._plugins.values()
            if query_lower in p.name.lower()
            or query_lower in p.description.lower()
            or any(query_lower in tag.lower() for tag in p.tags)
        ]

    @classmethod
    def execute(
        cls,
        slug: str,
        config: Dict[str, Any],
        context: Dict[str, Any] = None,
    ) -> PluginResult:
        """Execute a plugin with given configuration."""
        import time

        start_time = time.time()

        plugin = cls.get(slug)
        if not plugin:
            return PluginResult(
                success=False,
                error=f"Plugin '{slug}' not found",
            )

        executor = cls._executors.get(slug) or plugin.execute
        if not executor:
            return PluginResult(
                success=False,
                error=f"No executor found for plugin '{slug}'",
            )

        try:
            if inspect.iscoroutinefunction(executor):
                import asyncio

                output = asyncio.run(executor(config, context or {}))
            else:
                output = executor(config, context or {})

            duration_ms = int((time.time() - start_time) * 1000)

            return PluginResult(
                success=True,
                output=output,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.log_line(PREFIX_PLUGIN, "EXECUTE", f"Plugin {slug} failed: {e}", level="error")
            return PluginResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )


class PluginSandbox:
    """
    Sandboxed environment for plugin execution.
    Provides isolation and resource limits.
    """

    def __init__(
        self,
        timeout_seconds: int = 300,
        memory_limit_mb: int = 512,
        allowed_modules: List[str] = None,
    ):
        self.timeout_seconds = timeout_seconds
        self.memory_limit_mb = memory_limit_mb
        self.allowed_modules = allowed_modules or [
            "requests",
            "urllib",
            "json",
            "re",
            "hashlib",
            "base64",
            "csv",
        ]

    def execute_plugin(
        self,
        source_code: str,
        config: Dict[str, Any],
        context: Dict[str, Any],
    ) -> PluginResult:
        """Execute plugin source code in sandbox."""
        import signal
        import time

        start_time = time.time()

        def timeout_handler(signum, frame):
            raise TimeoutError(f"Plugin execution timed out after {self.timeout_seconds}s")

        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(self.timeout_seconds)

        try:
            exec_globals = {
                "__builtins__": {name: __import__(name) for name in self.allowed_modules if name in dir(__builtins__)},
                "config": config,
                "context": context,
                "results": None,
            }

            exec(source_code, exec_globals)
            signal.alarm(0)
            duration_ms = int((time.time() - start_time) * 1000)

            return PluginResult(
                success=True,
                output=exec_globals.get("results"),
                duration_ms=duration_ms,
            )
        except TimeoutError as e:
            signal.alarm(0)
            duration_ms = int((time.time() - start_time) * 1000)
            return PluginResult(
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )
        except Exception as e:
            signal.alarm(0)
            duration_ms = int((time.time() - start_time) * 1000)
            return PluginResult(
                success=False,
                error=f"Execution error: {str(e)}",
                duration_ms=duration_ms,
            )
        finally:
            signal.signal(signal.SIGALRM, old_handler)


class PluginSecurityScanner:
    """
    Security scanning for plugin source code before installation.
    """

    DANGEROUS_PATTERNS = [
        (r"import\s+os", "OS module import"),
        (r"import\s+subprocess", "Subprocess module import"),
        (r"import\s+sys", "Sys module import"),
        (r"eval\s*\(", "Use of eval()"),
        (r"exec\s*\(", "Use of exec()"),
        (r"open\s*\([^)]*['\"][wr]", "File write operations"),
        (r"__import__", "Dynamic module import"),
        (r"os\.system", "OS system calls"),
        (r"os\.popen", "OS popen calls"),
        (r"subprocess\.", "Subprocess calls"),
        (r"shutil\.", "Shutil operations"),
        (r"socket\.", "Socket operations"),
        (r"requests\.post", "HTTP POST requests"),
        (r"urllib", "URL fetching"),
        (r"ctypes", "Ctypes usage"),
        (r"pickle\.load", "Pickle deserialization"),
    ]

    @classmethod
    def scan_source(cls, source_code: str) -> Dict[str, Any]:
        """
        Scan plugin source code for security issues.
        Returns dict with issues_found and severity_counts.
        """
        import re

        issues = []
        severity_counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}

        for pattern, description in cls.DANGEROUS_PATTERNS:
            matches = re.finditer(pattern, source_code)
            for match in matches:
                line_num = source_code[: match.start()].count("\n") + 1
                issues.append(
                    {
                        "pattern": description,
                        "line": line_num,
                        "code": match.group(),
                        "severity": "error"
                        if pattern.startswith(r"import\s+os") or "eval" in description
                        else "warning",
                    }
                )

                severity = "error" if issues[-1]["severity"] == "error" else "warning"
                severity_counts[severity] += 1

        if "import" not in source_code and "import" not in source_code.lower():
            issues.append(
                {
                    "pattern": "No imports found",
                    "severity": "info",
                }
            )
            severity_counts["info"] += 1

        return {
            "issues_found": issues,
            "severity_counts": severity_counts,
            "is_passed": severity_counts["critical"] == 0 and severity_counts["error"] == 0,
            "scanned_at": timezone.now().isoformat(),
        }


def register_builtin_plugins():
    """Register built-in plugins."""

    def run_subdomain_enum(config, context):
        return {"subdomains": [], "count": 0}

    def run_port_scan(config, context):
        return {"ports": [], "count": 0}

    def run_vuln_scan(config, context):
        return {"vulnerabilities": [], "count": 0}

    PluginRegistry.register(
        name="Subdomain Enumerator",
        slug="builtin-subdomain-enum",
        version="1.0.0",
        description="Built-in subdomain enumeration template",
        category="subdomain",
        author="reconPoint",
        execute=run_subdomain_enum,
    )

    PluginRegistry.register(
        name="Port Scanner",
        slug="builtin-port-scan",
        version="1.0.0",
        description="Built-in port scanning template",
        category="port",
        author="reconPoint",
        execute=run_port_scan,
    )

    PluginRegistry.register(
        name="Vulnerability Scanner",
        slug="builtin-vuln-scan",
        version="1.0.0",
        description="Built-in vulnerability scanning template",
        category="vuln",
        author="reconPoint",
        execute=run_vuln_scan,
    )
