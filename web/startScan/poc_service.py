"""
PoC Generation and Execution Service.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from reconPoint.llm.utils import get_llm_config
from reconPoint.utilities.logger import get_module_logger


PREFIX_POC = "[POC]"
logger = get_module_logger(__name__)


@dataclass
class PoCGenerationResult:
    """Result of PoC generation."""

    success: bool
    code: Optional[str] = None
    language: Optional[str] = None
    error: Optional[str] = None
    model_used: Optional[str] = None
    generation_time_ms: Optional[int] = None


@dataclass
class PoCExecutionResult:
    """Result of PoC execution."""

    success: bool
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time_ms: int = 0
    is_blocked: bool = False


class PoCGenerator:
    """
    LLM-powered PoC generator for vulnerabilities.
    """

    SYSTEM_PROMPT = """You are a security expert specializing in writing Proof-of-Concept (PoC) exploit code.

Your task is to generate working PoC code for security vulnerabilities.
Guidelines:
- Write clean, well-commented code
- Include proper error handling
- Use safe testing practices
- Never include actual exploit payloads that could cause damage
- Prioritize safe validation methods
- Include descriptive comments explaining what the code does

Respond with the generated code in a code block.
"""

    VULN_CONTEXT_PROMPT = """
Vulnerability Details:
- Name: {name}
- Severity: {severity}
- CVSS Score: {cvss}
- Description: {description}
- Affected Endpoint: {endpoint}
- Template: {template}

Generate a safe PoC that demonstrates how this vulnerability could be tested.
The PoC should:
1. Validate the vulnerability exists
2. NOT cause any harm to the target
3. Include proper error handling
4. Be well-commented with explanation of what is being tested
"""

    def __init__(self):
        self.llm_config = get_llm_config()

    def generate(
        self,
        vulnerability,
        context: Dict[str, Any] = None,
    ) -> PoCGenerationResult:
        """Generate PoC for a vulnerability."""
        import time

        start_time = time.time()

        try:
            prompt = self._build_prompt(vulnerability, context or {})

            llm = self.llm_config.get("llm_instance")
            if not llm:
                raise ValueError("LLM not configured")

            from llm import LLMResponse

            response: LLMResponse = llm.chat(
                messages=[
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
            )

            code = self._extract_code(response.content)
            language = self._detect_language(code, vulnerability.template)

            generation_time_ms = int((time.time() - start_time) * 1000)

            return PoCGenerationResult(
                success=True,
                code=code,
                language=language,
                model_used=self.llm_config.get("model_name", "unknown"),
                generation_time_ms=generation_time_ms,
            )

        except Exception as e:
            logger.log_line(PREFIX_POC, "GENERATE", f"Failed: {e}", level="error")
            generation_time_ms = int((time.time() - start_time) * 1000)

            return PoCGenerationResult(
                success=False,
                error=str(e),
                generation_time_ms=generation_time_ms,
            )

    def _build_prompt(self, vulnerability, context: Dict) -> str:
        prompt_parts = [
            self.VULN_CONTEXT_PROMPT.format(
                name=vulnerability.name,
                severity=vulnerability.severity,
                cvss=vulnerability.cvss_score or "N/A",
                description=vulnerability.description or "No description",
                endpoint=vulnerability.endpoint or "N/A",
                template=vulnerability.template or "N/A",
            ),
        ]

        if context.get("language"):
            prompt_parts.append(f"\nPreferred language: {context['language']}")

        if context.get("framework"):
            prompt_parts.append(f"\nTarget framework: {context['framework']}")

        return "\n\n".join(prompt_parts)

    def _extract_code(self, response: str) -> str:
        import re

        code_block_pattern = r"```(?:\w+)?\n?(.*?)```"
        matches = re.findall(code_block_pattern, response, re.DOTALL)
        if matches:
            return matches[0].strip()
        return response.strip()

    def _detect_language(self, code: str, template: str = None) -> str:
        if "import requests" in code or "import urllib" in code:
            return "python"
        if "<script>" in code or "javascript" in code.lower():
            return "javascript"
        if "<?php" in code:
            return "php"
        if "package main" in code:
            return "go"
        if "public class" in code or "System." in code:
            return "java"
        if template and "nuclei" in template.lower():
            return "yaml"
        return "text"


class PoCExecutor:
    """
    Sandboxed execution environment for PoC code.
    """

    EXECUTION_TIMEOUT = 30
    MAX_OUTPUT_SIZE = 1024 * 1024

    def __init__(self):
        self.execution_mode = "sandbox"

    def execute(
        self,
        code: str,
        language: str,
        target_url: str = None,
        params: Dict = None,
    ) -> PoCExecutionResult:
        """Execute PoC code in a sandboxed environment."""
        import time

        start_time = time.time()

        try:
            if language == "python":
                return self._execute_python(code, target_url, params, start_time)
            elif language == "javascript":
                return self._execute_javascript(code, start_time)
            else:
                return PoCExecutionResult(
                    success=False,
                    error=f"Unsupported language: {language}",
                )
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return PoCExecutionResult(
                success=False,
                error=str(e),
                execution_time_ms=execution_time_ms,
            )

    def _execute_python(
        self,
        code: str,
        target_url: str,
        params: Dict,
        start_time: float,
    ) -> PoCExecutionResult:
        """Execute Python PoC in sandbox."""
        import sys
        import time

        output_capture = []
        error_capture = []

        class OutputCapture:
            def write(self, x):
                if len(output_capture) < self.MAX_OUTPUT_SIZE:
                    output_capture.append(str(x))

        class ErrorCapture:
            def write(self, x):
                if len(error_capture) < self.MAX_OUTPUT_SIZE:
                    error_capture.append(str(x))

        old_stdout = sys.stdout
        old_stderr = sys.stderr

        sys.stdout = OutputCapture()
        sys.stderr = ErrorCapture()

        try:
            exec_globals = {
                "__builtins__": {
                    "print": lambda x: output_capture.append(str(x)),
                    "len": len,
                    "str": str,
                    "int": int,
                    "float": float,
                    "list": list,
                    "dict": dict,
                    "range": range,
                },
                "target_url": target_url,
                "params": params or {},
            }

            exec(code, exec_globals)

            output = "".join(output_capture)
            error = "".join(error_capture)
            execution_time_ms = int((time.time() - start_time) * 1000)

            return PoCExecutionResult(
                success=not error,
                output=output[: self.MAX_OUTPUT_SIZE],
                error=error or None,
                execution_time_ms=execution_time_ms,
            )

        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

    def _execute_javascript(
        self,
        code: str,
        start_time: float,
    ) -> PoCExecutionResult:
        """Execute JavaScript PoC (simulated)."""
        import time

        return PoCExecutionResult(
            success=True,
            output="[Simulated] JavaScript execution not supported in sandbox",
            execution_time_ms=int((time.time() - start_time) * 1000),
        )


def create_poc_and_execute(vulnerability, user, execution_mode="sandbox"):
    """Create a PoC request and execute it."""
    from .models_poc import PoCExecution, PoCRequest

    generator = PoCGenerator()
    poc_result = generator.generate(vulnerability)

    poc_request = PoCRequest.objects.create(
        vulnerability=vulnerability,
        requested_by=user,
        status=PoCRequest.Status.READY if poc_result.success else PoCRequest.Status.FAILED,
        generated_code=poc_result.code,
        language=poc_result.language or "python",
        error_message=poc_result.error,
        llm_model=poc_result.model_used,
        generation_time_ms=poc_result.generation_time_ms,
    )

    if not poc_result.success:
        return poc_request, None

    executor = PoCExecutor()
    exec_result = executor.execute(
        poc_result.code,
        poc_result.language or "python",
    )

    execution = PoCExecution.objects.create(
        poc_request=poc_request,
        executed_by=user,
        execution_mode=execution_mode,
        status=PoCExecution.ExecutionStatus.SUCCESS if exec_result.success else PoCExecution.ExecutionStatus.FAILED,
        output=exec_result.output,
        error_output=exec_result.error,
        execution_time_ms=exec_result.execution_time_ms,
    )

    return poc_request, execution


def get_poc_templates(category: str = None) -> List[Dict]:
    """Get available PoC templates."""
    from .models_poc import PoCTemplate

    templates = PoCTemplate.objects.all()
    if category:
        templates = templates.filter(category=category)

    return [
        {
            "id": str(t.id),
            "name": t.name,
            "description": t.description,
            "category": t.category,
            "language": t.language,
            "risk_level": t.risk_level,
            "is_sandbox_only": t.is_sandbox_only,
        }
        for t in templates
    ]
