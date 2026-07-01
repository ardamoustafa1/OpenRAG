from typing import Any

import structlog

from app.llm.token_counter import token_counter

logger = structlog.get_logger()


class ChunkingService:
    """
    Performs Structural and Semantic Chunking on extracted elements.
    """

    def __init__(self, max_tokens: int = 512, overlap: int = 64):
        self.max_tokens = max_tokens
        self.overlap = overlap

    def chunk_elements(
        self, elements: list[dict[str, Any]], document_id: str
    ) -> list[dict[str, Any]]:
        """
        Group elements structurally. If a block exceeds max_tokens, recursive split it.
        """
        chunks: list[dict[str, Any]] = []
        current_chunk_text: list[str] = []
        current_chunk_tokens = 0
        current_section_title = "Unknown"

        for el in elements:
            el_type = el["type"]
            text = el["text"]
            tokens = token_counter.count_tokens(text)

            # Structural logic
            if el_type == "Title":
                # Flush existing chunk before starting new section
                if current_chunk_text:
                    chunks.extend(
                        self._flush_chunk(
                            current_chunk_text, current_section_title, document_id
                        )
                    )
                    current_chunk_text = []
                    current_chunk_tokens = 0
                current_section_title = text
                # We can add Title to the next chunk's start
                current_chunk_text.append(text)
                current_chunk_tokens += tokens
                continue

            if el_type == "Table":
                # Flush existing
                if current_chunk_text:
                    chunks.extend(
                        self._flush_chunk(
                            current_chunk_text, current_section_title, document_id
                        )
                    )
                    current_chunk_text = []
                    current_chunk_tokens = 0

                # Tables are kept whole if possible, even if slightly larger
                if tokens > self.max_tokens * 2:
                    # Recursive split table (not ideal but necessary)
                    chunks.extend(
                        self._recursive_split(text, current_section_title, document_id)
                    )
                else:
                    chunks.append(
                        self._build_chunk_dict(
                            text, tokens, current_section_title, document_id
                        )
                    )
                continue

            # Accumulate NarrativeText / ListItem
            if current_chunk_tokens + tokens > self.max_tokens:
                # Flush existing
                if current_chunk_text:
                    chunks.extend(
                        self._flush_chunk(
                            current_chunk_text, current_section_title, document_id
                        )
                    )
                    current_chunk_text = []
                    current_chunk_tokens = 0

                # If the single element is larger than max_tokens, recursively split it
                if tokens > self.max_tokens:
                    chunks.extend(
                        self._recursive_split(text, current_section_title, document_id)
                    )
                else:
                    current_chunk_text.append(text)
                    current_chunk_tokens += tokens
            else:
                current_chunk_text.append(text)
                current_chunk_tokens += tokens

        # Flush final
        if current_chunk_text:
            chunks.extend(
                self._flush_chunk(
                    current_chunk_text, current_section_title, document_id
                )
            )

        logger.info(
            "Chunking completed", document_id=document_id, total_chunks=len(chunks)
        )
        return chunks

    def _flush_chunk(
        self, chunk_texts: list[str], section_title: str, document_id: str
    ) -> list[dict[str, Any]]:
        joined_text = "\n\n".join(chunk_texts)
        tokens = token_counter.count_tokens(joined_text)
        if tokens > self.max_tokens:
            return self._recursive_split(joined_text, section_title, document_id)
        return [self._build_chunk_dict(joined_text, tokens, section_title, document_id)]

    def _recursive_split(
        self, text: str, section_title: str, document_id: str
    ) -> list[dict[str, Any]]:
        """Fallback split by paragraphs/sentences."""
        # A simple implementation. In production, use Langchain's RecursiveCharacterTextSplitter logic.
        paragraphs = text.split("\n\n")
        chunks = []
        curr_text = ""

        for p in paragraphs:
            if token_counter.count_tokens(curr_text + "\n\n" + p) > self.max_tokens:
                if curr_text:
                    chunks.append(
                        self._build_chunk_dict(
                            curr_text,
                            token_counter.count_tokens(curr_text),
                            section_title,
                            document_id,
                        )
                    )
                curr_text = p
            else:
                curr_text = curr_text + "\n\n" + p if curr_text else p

        if curr_text:
            chunks.append(
                self._build_chunk_dict(
                    curr_text,
                    token_counter.count_tokens(curr_text),
                    section_title,
                    document_id,
                )
            )

        return chunks

    def _build_chunk_dict(
        self, text: str, tokens: int, section_title: str, document_id: str
    ) -> dict[str, Any]:
        return {
            "document_id": document_id,
            "text": text,
            "token_count": tokens,
            "section_title": section_title,
        }


chunking_service = ChunkingService()
