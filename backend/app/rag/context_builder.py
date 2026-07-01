from typing import Any, Dict, List

from app.llm.token_counter import token_counter


class ContextBuilder:
    """
    Builds the final prompt context from reranked chunks.
    Handles deduplication and context window limits.
    """

    def __init__(self, sim_threshold: float = 0.95):
        self.sim_threshold = sim_threshold

    def build_context(
        self, reranked_chunks: List[Dict[str, Any]], max_context_tokens: int
    ) -> tuple[List[Dict[str, Any]], str]:
        """
        Deduplicates chunks, fits them into max_context_tokens, and formats them.
        Returns the finalized list of used chunks and the formatted context string.
        """
        deduped = self._deduplicate(reranked_chunks)

        final_chunks = []
        current_tokens = 0

        for chunk in deduped:
            payload = chunk.get("payload", {})
            text = payload.get("text", "")

            # Approximation of token cost for the formatting block + text
            # Format: [Kaynak: doc_name, Bölüm: section_title] \n text
            doc_name = payload.get("document_name", "Unknown")
            section_title = payload.get("section_title", "General")

            chunk_str = f"[Kaynak: {doc_name}, Bölüm: {section_title}]\n{text}"
            c_tokens = token_counter.count_tokens(chunk_str)

            if current_tokens + c_tokens <= max_context_tokens:
                final_chunks.append(
                    {
                        "id": chunk.get("id"),
                        "text": chunk_str,
                        "document_name": doc_name,
                        "section_title": section_title,
                        "original_text": text,
                    }
                )
                current_tokens += c_tokens
            else:
                # Stop adding once limit is reached
                break

        # Format the final string
        context_string = "\n\n".join([c["text"] for c in final_chunks])

        return final_chunks, context_string

    def _deduplicate(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Removes exact duplicate texts.
        In production, you'd use min-hash or Jaccard similarity for near-duplicate removal.
        """
        seen_texts = set()
        deduped = []

        for chunk in chunks:
            text = chunk.get("payload", {}).get("text", "").strip()
            if text and text not in seen_texts:
                seen_texts.add(text)
                deduped.append(chunk)

        return deduped


context_builder = ContextBuilder()
