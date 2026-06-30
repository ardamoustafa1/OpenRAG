import json
from rank_bm25 import BM25Okapi

class BM25Serializer:
    """
    Safely serializes and deserializes rank_bm25.BM25Okapi objects to/from JSON.
    This avoids using `pickle` which is a known RCE vector when loading from external caches.
    """
    
    @staticmethod
    def to_json(bm25: BM25Okapi, mapping: list[dict]) -> str:
        """Serializes BM25 model and chunk mapping to a JSON string."""
        payload = {
            "model": {
                "corpus_size": bm25.corpus_size,
                "avgdl": bm25.avgdl,
                "doc_freqs": [dict(df) for df in bm25.doc_freqs],
                "idf": bm25.idf,
                "doc_len": bm25.doc_len,
                "k1": bm25.k1,
                "b": bm25.b,
                "epsilon": bm25.epsilon
            },
            "mapping": mapping
        }
        return json.dumps(payload)

    @staticmethod
    def from_json(json_str: str) -> dict:
        """
        Deserializes a JSON string back into a dict containing the BM25Okapi model and mapping.
        """
        payload = json.loads(json_str)
        model_data = payload["model"]
        
        # Initialize with dummy corpus to create the object
        bm25 = BM25Okapi([["dummy"]])
        
        # Override attributes with our cached data
        bm25.corpus_size = model_data["corpus_size"]
        bm25.avgdl = model_data["avgdl"]
        bm25.doc_freqs = model_data["doc_freqs"]
        bm25.idf = model_data["idf"]
        bm25.doc_len = model_data["doc_len"]
        bm25.k1 = model_data.get("k1", 1.5)
        bm25.b = model_data.get("b", 0.75)
        bm25.epsilon = model_data.get("epsilon", 0.25)
        
        return {
            "model": bm25,
            "mapping": payload["mapping"]
        }
