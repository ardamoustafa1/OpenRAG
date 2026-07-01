import re
from dataclasses import dataclass

import structlog

logger = structlog.get_logger()


@dataclass
class ScanResult:
    is_safe: bool
    reason: str | None = None


class PromptGuard:
    """
    Synchronous Security shield blocking Prompt Injection, Jailbreaks, and malicious inputs.
    Designed for zero-latency execution via RegEx and heuristics.
    """

    JAILBREAK_PATTERNS = [
        re.compile(r"ignore\s+(all\s+)?(previous\s+)?instructions", re.IGNORECASE),
        re.compile(r"system\s+prompt", re.IGNORECASE),
        re.compile(
            r"you\s+are\s+(now\s+)?a\s+(developer|unrestricted|DAN)", re.IGNORECASE
        ),
        re.compile(r"bypassing", re.IGNORECASE),
        re.compile(r"forget\s+what\s+you\s+were\s+told", re.IGNORECASE),
        re.compile(r"print\s+your\s+initial\s+instructions", re.IGNORECASE),
    ]

    @classmethod
    def scan_user_input(cls, text: str) -> ScanResult:
        """
        Scans user input for malicious intent.
        Returns a ScanResult.
        """
        if not text or len(text) > 4000:
            return ScanResult(is_safe=False, reason="Payload too large or empty.")

        for pattern in cls.JAILBREAK_PATTERNS:
            if pattern.search(text):
                logger.warning(
                    "Prompt injection detected",
                    pattern=pattern.pattern,
                    text=text[:100],
                )
                return ScanResult(
                    is_safe=False, reason="Malicious prompt injection pattern detected."
                )

        # Future Expansion: Call async LLM classification here if heuristics pass but risk is high.
        return ScanResult(is_safe=True)

    @classmethod
    def sanitize_output(cls, text: str) -> str:
        """
        Cleans the final LLM output to prevent leakage of internal system metadata.
        """
        if not text:
            return ""

        # Example: Scrubbing internal API keys or exact prompt reflections
        sanitized = re.sub(r"(sk-[A-Za-z0-9]{48})", "***MASKED***", text)
        sanitized = re.sub(
            r"(AI_PLATFORM_INTERNAL_ID_[A-Z0-9]+)", "***REDACTED***", sanitized
        )

        return sanitized
