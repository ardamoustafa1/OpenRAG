from app.rag.chunking import ChunkingService


def test_chunk_elements_structural():
    # Use a small max_tokens to test limits without huge texts
    service = ChunkingService(max_tokens=100)

    elements = [
        {"type": "Title", "text": "Introduction"},
        {"type": "NarrativeText", "text": "This is a short paragraph."},
        {"type": "Title", "text": "Details"},
        {"type": "NarrativeText", "text": "Here are the details."},
    ]

    chunks = service.chunk_elements(elements, document_id="doc1")

    assert len(chunks) == 2
    assert chunks[0]["section_title"] == "Introduction"
    assert "This is a short paragraph." in chunks[0]["text"]
    assert chunks[1]["section_title"] == "Details"
    assert "Here are the details." in chunks[1]["text"]


def test_recursive_split():
    service = ChunkingService(max_tokens=10)
    text = "Paragraph one is short.\n\nParagraph two is also short.\n\nParagraph three."

    chunks = service._recursive_split(text, "Test Section", "doc1")

    assert len(chunks) > 1
    assert chunks[0]["section_title"] == "Test Section"
    assert "Paragraph one" in chunks[0]["text"]
