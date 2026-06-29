import asyncio
from typing import List, Dict, Any
from collections import defaultdict
from qdrant_client.http import models
import pickle
from redis.asyncio import Redis

from app.rag.vector_store import vector_store
from app.rag.query_understanding import query_understanding
from app.core.config import settings
import structlog

logger = structlog.get_logger()

class HybridRetriever:
    """
    Combines Dense Retrieval (Qdrant) and Sparse Retrieval (BM25) using Reciprocal Rank Fusion (RRF).
    """

    def __init__(self, top_k: int = 50, rrf_k: int = 60):
        self.top_k = top_k
        self.rrf_k = rrf_k

    async def retrieve(self, query: str, tenant_id: str, collection_id: str, use_hyde: bool = True) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval and fuses results.
        """
        col_name = vector_store._collection_name(tenant_id, collection_id)
        
        try:
            # 1. Generate query embedding (with optional HyDE)
            query_vector = await query_understanding.generate_hyde_embedding(query, tenant_id, use_hyde)

            # 2. Parallel Fetch: Dense and Sparse (Sparse is coming soon, disabled for now)
            dense_results = await self._dense_search(col_name, query_vector)
            sparse_results = []
            
            # 3. RRF Fusion
            fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results)
            
            # 4. Optional: Metadata Boosting (e.g. freshness)
            fused_results = self._apply_metadata_boosting(fused_results)

            # Return top 100 max after fusion
            return fused_results[:100]

        except Exception as e:
            logger.error("Hybrid retrieval failed", error=str(e), collection=col_name)
            raise

    async def _dense_search(self, collection_name: str, query_vector: list[float]) -> List[Dict[str, Any]]:
        """Qdrant vector search."""
        try:
            hits = await vector_store.client.search(
                collection_name=collection_name,
                query_vector=query_vector,
                limit=self.top_k,
                with_payload=True
            )
            return [{"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in hits]
        except Exception as e:
            logger.warning("Dense search failed", error=str(e), collection=collection_name)
            return []

    async def _sparse_search(self, collection_name: str, query: str) -> List[Dict[str, Any]]:
        """
        Sparse search using BM25.
        Currently disabled as we migrate from local Redis BM25 index to a robust inverted index.
        """
        raise NotImplementedError("BM25 retrieval coming soon")

    def _reciprocal_rank_fusion(self, dense_results: List[Dict], sparse_results: List[Dict]) -> List[Dict]:
        """
        RRF Formula: score = Σ (1 / (k + rank_i))
        """
        rrf_scores = defaultdict(float)
        items_map = {}

        # Rank Dense
        for rank, item in enumerate(dense_results):
            doc_id = item["id"]
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
            items_map[doc_id] = item["payload"]

        # Rank Sparse
        for rank, item in enumerate(sparse_results):
            doc_id = item["id"]
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
            items_map[doc_id] = item["payload"]

        # Sort by fused score descending
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        
        return [{"id": doc_id, "rrf_score": score, "payload": items_map[doc_id]} for doc_id, score in fused]

    def _apply_metadata_boosting(self, results: List[Dict]) -> List[Dict]:
        """
        Applies artificial score boosts based on payload metadata.
        e.g., boosting documents created in the last 30 days.
        """
        # Example logic:
        # for res in results:
        #     if is_recent(res["payload"].get("created_at")):
        #         res["rrf_score"] *= 1.2
        return results

retriever = HybridRetriever()
