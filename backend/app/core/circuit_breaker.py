from typing import Any

import pybreaker
import structlog

logger = structlog.get_logger()


class CircuitBreakerListener(pybreaker.CircuitBreakerListener):
    def state_change(self, cb: Any, old_state: Any, new_state: Any) -> None:
        logger.warning(
            "Circuit Breaker state changed",
            breaker_name=cb.name,
            old_state=old_state.name,
            new_state=new_state.name,
        )


# Global Circuit Breakers for critical external services
llm_breaker = pybreaker.CircuitBreaker(
    fail_max=5, reset_timeout=60, listeners=[CircuitBreakerListener()]
)

stripe_breaker = pybreaker.CircuitBreaker(
    fail_max=3, reset_timeout=30, listeners=[CircuitBreakerListener()]
)
