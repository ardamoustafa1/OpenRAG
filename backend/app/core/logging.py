import logging
import sys
from typing import Any, Dict

import structlog


def mask_sensitive_data(
    logger: logging.Logger, name: str, event_dict: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Masks sensitive information in log events.
    """
    sensitive_keys = {
        "password",
        "token",
        "access_token",
        "api_key",
        "secret",
        "credit_card",
    }

    for key, value in event_dict.items():
        if key.lower() in sensitive_keys and isinstance(value, str):
            event_dict[key] = "***MASKED***"

    return event_dict


def setup_logging(is_production: bool = False) -> None:
    """
    Configures structlog. JSON for production, console for development.
    """
    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        mask_sensitive_data,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if is_production:
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]
    else:
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Standard library logging configuration
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO if is_production else logging.DEBUG,
    )

    # Silence third-party noisy loggers
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


setup_logging(is_production=False)
