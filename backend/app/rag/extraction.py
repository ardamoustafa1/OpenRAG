import io
from unstructured.partition.auto import partition
from unstructured.cleaners.core import clean, clean_non_ascii_chars, replace_unicode_quotes
import langdetect
import structlog

logger = structlog.get_logger()

class ExtractionService:
    """
    Handles extracting text and structural metadata from various file formats
    using Unstructured.io.
    """

    def process_file(self, file_bytes: bytes, filename: str, content_type: str) -> dict:
        """
        Partition the document into structured elements (Title, NarrativeText, Table, etc.).
        """
        logger.info("Starting extraction", filename=filename, content_type=content_type)
        
        try:
            # We use `partition` which auto-detects the format.
            # Unstructured uses Tesseract if OCR is needed (e.g. scanned PDF).
            # We pass a file-like object
            elements = partition(
                file=io.BytesIO(file_bytes),
                metadata_filename=filename,
                content_type=content_type,
                strategy="hi_res" # Use high-resolution strategy for OCR/Tables
            )

            cleaned_elements = []
            full_text_for_lang = []
            
            for element in elements:
                text = str(element)
                if not text.strip():
                    continue
                
                # Apply cleaners
                text = replace_unicode_quotes(text)
                text = clean(text, extra_whitespace=True, dashes=True, bullets=True, trailing_punctuation=False)
                
                # Only keep element if text remains after cleaning
                if text.strip():
                    # Keep Unstructured metadata like page numbers, element type
                    el_type = type(element).__name__
                    metadata = element.metadata.to_dict() if hasattr(element, "metadata") else {}
                    
                    cleaned_elements.append({
                        "type": el_type,
                        "text": text,
                        "metadata": metadata
                    })
                    
                    if len(full_text_for_lang) < 5000:
                        full_text_for_lang.append(text)

            # Detect language from first few chunks
            lang = "unknown"
            if full_text_for_lang:
                try:
                    lang = langdetect.detect(" ".join(full_text_for_lang[:10]))
                except Exception:
                    pass

            logger.info("Extraction completed", filename=filename, elements_count=len(cleaned_elements), lang=lang)
            
            return {
                "elements": cleaned_elements,
                "language": lang
            }
            
        except Exception as e:
            logger.error("Extraction failed", filename=filename, error=str(e))
            raise

extraction_service = ExtractionService()
