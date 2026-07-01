from typing import Any, Dict, List

import structlog

try:
    from sentence_transformers import CrossEncoder
except ImportError:
    CrossEncoder = None

logger = structlog.get_logger()


class RerankerService:
    """
    Cross-Encoder Re-Ranking using sentence-transformers.
    Evaluates the relevance of each retrieved chunk against the query.
    """

    def __init__(
        self,
        model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        min_score: float = 0.3,
    ):
        self.model_name = model_name
        self.min_score = min_score
        self.model = None

        if CrossEncoder:
            try:
                logger.info("Loading Cross-Encoder model...", model_name=model_name)
                # Loads to GPU if available, else CPU
                self.model = CrossEncoder(self.model_name, max_length=512)
            except Exception as e:
                logger.error("Failed to load Cross-Encoder model", error=str(e))
        else:
            logger.warning(
                "sentence-transformers not installed. Reranking will be disabled."
            )

    def rerank(
        self, query: str, retrieved_chunks: List[Dict[str, Any]], top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Reranks the retrieved chunks and filters out those below min_score.
        """
        if not self.model or not retrieved_chunks:
            # If no model is loaded, just return the top_k from the RRF list
            return retrieved_chunks[:top_k]

        try:
            # Prepare pairs: (query, document_text)
            pairs = [
                [query, chunk["payload"].get("text", "")] for chunk in retrieved_chunks
            ]

            # Predict scores in batch
            scores = self.model.predict(pairs)

            # Combine scores with chunks
            scored_chunks = []
            for i, score in enumerate(scores):
                # Convert numpy float32 to python float
                float_score = float(score)
                if float_score >= self.min_score:
                    chunk = retrieved_chunks[i].copy()
                    chunk["rerank_score"] = float_score
                    scored_chunks.append(chunk)

            # Sort descending by cross-encoder score
            scored_chunks.sort(key=lambda x: x["rerank_score"], reverse=True)

            return scored_chunks[:top_k]

        except Exception as e:
            logger.error("Reranking failed", error=str(e))
            # Fallback to RRF ordering
            return retrieved_chunks[:top_k]


reranker = RerankerService()
