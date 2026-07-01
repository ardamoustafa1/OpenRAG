import asyncio
from collections import defaultdict
from typing import Any, Dict, List

import structlog
from redis.asyncio import Redis

from app.core.config import settings
from app.rag.bm25_serializer import BM25Serializer
from app.rag.query_understanding import query_understanding
from app.rag.vector_store import vector_store

logger = structlog.get_logger()


class HybridRetriever:
    """
    Combines Dense Retrieval (Qdrant) and Sparse Retrieval (BM25 via Redis cache)
    using Reciprocal Rank Fusion (RRF).

    On each query:
      1. A dense Qdrant vector search is run using the HyDE-augmented embedding.
      2. A sparse BM25 lookup is run against the pre-built index stored in Redis.
      3. Results are merged with RRF and optionally boosted by freshness signal.
    """

    def __init__(self, top_k: int = 50, rrf_k: int = 60):
        self.top_k = top_k
        self.rrf_k = rrf_k
        self.redis_client = Redis.from_url(settings.REDIS_URL)

    async def retrieve(
        self,
        query: str,
        tenant_id: str,
        collection_id: str,
        use_hyde: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Executes hybrid retrieval and fuses results.

        Args:
            query: Natural language user query.
            tenant_id: UUID string for the active tenant.
            collection_id: UUID string for the document collection.
            use_hyde: Whether to use HyDE for query augmentation.

        Returns:
            List of result dicts sorted by fused RRF score (descending).
        """
        col_name = vector_store._collection_name(tenant_id, collection_id)

        try:
            # 1. Generate query embedding (with optional HyDE augmentation)
            query_vector = await query_understanding.generate_hyde_embedding(
                query, tenant_id, use_hyde
            )

            # 2. Run Dense and Sparse retrieval in parallel; handle partial failures gracefully
            dense_task = self._dense_search(col_name, query_vector)
            sparse_task = self._sparse_search(col_name, query, tenant_id, collection_id)

            gather_res: list[Any] = await asyncio.gather(
                dense_task, sparse_task, return_exceptions=True
            )
            dense_res_raw: Any = gather_res[0]
            sparse_res_raw: Any = gather_res[1]

            dense_results: list[dict[str, Any]] = []
            if isinstance(dense_res_raw, Exception):
                logger.warning(
                    "Dense search failed — proceeding with sparse only",
                    error=str(dense_res_raw),
                )
            else:
                dense_results = dense_res_raw

            sparse_results: list[dict[str, Any]] = []
            if isinstance(sparse_res_raw, Exception):
                logger.warning(
                    "Sparse search failed — proceeding with dense only",
                    error=str(sparse_res_raw),
                )
            else:
                sparse_results = sparse_res_raw

            # 3. RRF Fusion
            fused_results = self._reciprocal_rank_fusion(dense_results, sparse_results)

            # 4. Freshness-based metadata boosting
            fused_results = self._apply_metadata_boosting(fused_results)

            logger.info(
                "Hybrid retrieval complete",
                dense_hits=len(dense_results),
                sparse_hits=len(sparse_results),
                fused_hits=len(fused_results),
                collection=col_name,
            )

            # Return top 100 max after fusion
            return fused_results[:100]

        except Exception as e:
            logger.error("Hybrid retrieval failed", error=str(e), collection=col_name)
            raise

    # ─── Private Retrieval Methods ─────────────────────────────────────────────

    async def _dense_search(
        self, collection_name: str, query_vector: list[float]
    ) -> List[Dict[str, Any]]:
        """Qdrant dense vector search."""
        hits = await vector_store.client.search(  # type: ignore[attr-defined]
            collection_name=collection_name,
            query_vector=query_vector,
            limit=self.top_k,
            with_payload=True,
        )
        return [
            {"id": hit.id, "score": hit.score, "payload": hit.payload} for hit in hits
        ]

    async def _sparse_search(
        self,
        collection_name: str,
        query: str,
        tenant_id: str,
        collection_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Sparse BM25 search using the pre-built index stored in Redis.
        The index is built by the Celery `build_bm25_index` task after each
        document ingestion and refreshed on-demand.
        Falls back to empty list if the index is not yet available.
        """
        cache_key = f"bm25:{collection_name}"
        cached = await self.redis_client.get(cache_key)
        if not cached:
            logger.info(
                "BM25 index not yet available for collection — skipping sparse",
                collection=collection_name,
            )
            return []

        # Deserialize using safe JSON deserialization
        cache_payload = BM25Serializer.from_json(cached)
        bm25 = cache_payload["model"]
        mapping: list[dict[str, Any]] = cache_payload["mapping"]

        tokenized_query = query.lower().split()
        scores = bm25.get_scores(tokenized_query)

        # Sort by BM25 score descending and take top_k
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[
            : self.top_k
        ]

        results = []
        for idx, score in ranked:
            if idx < len(mapping) and score > 0:
                entry = mapping[idx]
                results.append(
                    {
                        "id": entry["id"],
                        "score": float(score),
                        "payload": entry.get("payload", {}),
                    }
                )
        return results

    # ─── Fusion & Ranking ──────────────────────────────────────────────────────

    def _reciprocal_rank_fusion(
        self, dense_results: List[Dict[str, Any]], sparse_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        RRF Formula: score(d) = Σ_i  1 / (k + rank_i(d))
        where k=60 (default) dampens the impact of very high ranks.
        Documents appearing in both lists receive additive boosts.
        """
        rrf_scores: dict[str, float] = defaultdict(float)
        items_map: dict[str, dict[str, Any]] = {}

        for rank, item in enumerate(dense_results):
            doc_id = str(item["id"])
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
            items_map[doc_id] = item["payload"]

        for rank, item in enumerate(sparse_results):
            doc_id = str(item["id"])
            rrf_scores[doc_id] += 1.0 / (self.rrf_k + rank + 1)
            items_map[doc_id] = item["payload"]

        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"id": doc_id, "rrf_score": score, "payload": items_map[doc_id]}
            for doc_id, score in fused
        ]

    def _apply_metadata_boosting(
        self, results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Freshness boost: documents created within the last 30 days receive
        a 20% multiplicative boost to their RRF score, surfacing recent
        knowledge above older but semantically similar content.
        """
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(days=30)

        for res in results:
            created_at_str = res["payload"].get("created_at")
            if created_at_str:
                try:
                    created_at = datetime.fromisoformat(str(created_at_str))
                    if created_at.tzinfo is None:
                        created_at = created_at.replace(tzinfo=timezone.utc)
                    if created_at > cutoff:
                        res["rrf_score"] = res.get("rrf_score", 0.0) * 1.2
                except (ValueError, TypeError):
                    pass

        return sorted(results, key=lambda x: x.get("rrf_score", 0.0), reverse=True)


retriever = HybridRetriever()
