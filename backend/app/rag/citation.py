from typing import Any, Dict, List


class CitationService:
    """
    Handles structuring source citations for the frontend UI.
    """

    def format_sources(self, used_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transforms the internal used_chunks structure into a clean, frontend-ready
        source array.
        """
        sources = []
        for chunk in used_chunks:
            sources.append(
                {
                    "chunk_id": chunk.get("id"),
                    "document_name": chunk.get("document_name"),
                    "section": chunk.get("section_title"),
                    "text_preview": chunk.get("original_text", "")[:200]
                    + "...",  # Snippet
                }
            )

        # Optional: Deduplicate sources by document if the UI prefers document-level grouping
        return sources

    def match_sentences_to_sources(
        self, response_text: str, used_chunks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Advanced feature: Uses local similarity to match specific generated sentences
        to their source chunk. Returns annotated text with citation markers [1], [2].
        """
        # Placeholder for NLI / Sentence-transformer based sentence matching.
        # Currently, the prompt instructs the LLM to write [Kaynak: X] directly.
        # We will parse those markers if needed, or rely on the LLM's inline citations.
        pass


citation_service = CitationService()
