import langdetect
import numpy as np
import structlog

from app.llm.client import llm_client

logger = structlog.get_logger()


class QueryUnderstandingService:
    """
    Handles preprocessing of user queries before retrieval.
    Includes language detection, intent classification, and HyDE (Hypothetical Document Embeddings).
    """

    def detect_language(self, query: str) -> str:
        """Detect the language of the query."""
        try:
            return langdetect.detect(query)
        except Exception:
            return "unknown"

    async def generate_hyde_embedding(
        self, query: str, tenant_id: str, use_hyde: bool = True
    ) -> list[float]:
        """
        Generates an embedding for the query. If HyDE is enabled, it generates a hypothetical answer,
        embeds it, and averages it with the query embedding.
        """
        # Step 1: Embed the original query
        query_embedding = await llm_client.aembed(
            model="bge-m3",  # Standard embedding model
            input_text=query,
            tenant_id=tenant_id,
        )

        if not use_hyde:
            return self._normalize(query_embedding)

        # Step 2: Generate hypothetical document
        try:
            prompt = f"Please write a passage that answers the following question. Do not include introductory filler.\nQuestion: {query}\nAnswer:"
            messages = [{"role": "user", "content": prompt}]

            # Use a fast, lightweight model for HyDE (e.g., phi-4-mini)
            response = await llm_client.achat(
                model="phi-4-mini",
                messages=messages,
                tenant_id=tenant_id,
                temperature=0.7,
                max_tokens=256,
            )

            hypothetical_doc = response.choices[0].message.content

            # Step 3: Embed the hypothetical document
            doc_embedding = await llm_client.aembed(
                model="bge-m3", input_text=hypothetical_doc, tenant_id=tenant_id
            )

            # Step 4: Combine (Weighted Average)
            q_vec = np.array(query_embedding, dtype=np.float32)
            d_vec = np.array(doc_embedding, dtype=np.float32)

            # We weight the actual query slightly higher than the hallucinated document
            combined = (0.6 * q_vec) + (0.4 * d_vec)

            return self._normalize(combined.tolist())

        except Exception as e:
            logger.warning(
                "HyDE generation failed, falling back to standard query embedding",
                error=str(e),
            )
            return self._normalize(query_embedding)

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2 normalize a vector."""
        vec = np.array(vector, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    async def classify_intent(self, query: str, tenant_id: str) -> str:
        """
        Classifies the intent of the query (question, summarize, compare, infer).
        Could use a lightweight LLM call or regex rules.
        """
        # Simplified placeholder for intent classification
        return "question"


query_understanding = QueryUnderstandingService()
