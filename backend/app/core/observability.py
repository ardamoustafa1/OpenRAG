from contextlib import contextmanager
from typing import Any, Generator

import structlog
from langfuse import Langfuse

from app.core.config import settings

logger = structlog.get_logger()


class AIObserver:
    """
    Integrates with Langfuse to trace entire RAG execution flows.
    """

    def __init__(self):
        try:
            self.langfuse = Langfuse(
                public_key=settings.LANGFUSE_PUBLIC_KEY,
                secret_key=settings.LANGFUSE_SECRET_KEY,
                host=settings.LANGFUSE_HOST,
            )
        except Exception as e:
            logger.warning(
                "Langfuse initialization failed. Tracing disabled.", error=str(e)
            )
            self.langfuse = None

    @contextmanager
    def trace_rag_pipeline(
        self, tenant_id: str, user_id: str, conversation_id: str, query: str
    ) -> Generator[Any, None, None]:
        """
        Creates a top-level Langfuse trace for a RAG interaction.
        Yields the trace object so child spans can be attached to it.
        """
        if not self.langfuse:
            # Yield a dummy object if Langfuse is offline
            class DummyTrace:
                @contextmanager
                def span(self, *args, **kwargs):
                    yield DummySpan()

                def update(self, *args, **kwargs):
                    pass

            class DummySpan:
                def update(self, *args, **kwargs):
                    pass

                def end(self, *args, **kwargs):
                    pass

            yield DummyTrace()
            return

        trace = self.langfuse.trace(
            name="rag_pipeline",
            session_id=conversation_id,
            user_id=user_id,
            tags=[f"tenant:{tenant_id}"],
        )

        # Attach the initial query
        trace.update(input=query)

        try:
            yield trace
        except Exception as e:
            trace.update(level="ERROR", status_message=str(e))
            raise e
        finally:
            # Flush traces asynchronously
            self.langfuse.flush()

    def record_feedback(self, trace_id: str, score: float, comment: str = None):
        """
        Records user feedback (e.g. thumb up=1.0, thumb down=0.0) against a specific trace.
        """
        if not self.langfuse:
            return

        self.langfuse.score(
            trace_id=trace_id, name="user_feedback", value=score, comment=comment
        )


ai_observer = AIObserver()
