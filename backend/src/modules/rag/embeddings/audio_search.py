"""Audio transcript search with threshold filtering."""

from typing import Optional
from langchain_core.documents import Document
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from src.modules.rag.embeddings.qdrant_store import QdrantStore


class AudioSearch:
    """Search engine for audio transcripts."""

    def __init__(self, qdrant_store: QdrantStore):
        self.qdrant_store = qdrant_store

    @staticmethod
    def _filter_by_threshold(
        results: list[tuple[Document, float]],
        score_threshold: float
    ) -> list[tuple[Document, float]]:
        """Filter results by score threshold."""
        return [(doc, score) for doc, score in results if score >= score_threshold]

    def _create_recording_filter(self, recording_id: Optional[str] = None) -> Optional[Filter]:
        """Create Qdrant filter for recording_id if provided."""
        if recording_id is None:
            return None

        return Filter(
            must=[
                FieldCondition(
                    key="metadata.recording_id",
                    match=MatchValue(value=recording_id)
                )
            ]
        )

    async def search_similar(
        self,
        query: str,
        k: int = 10,
        score_threshold: float = 0.0,
        recording_id: Optional[str] = None,
    ) -> list[tuple[Document, float]]:
        """Async search for similar segments."""
        filter_condition = self._create_recording_filter(recording_id)
        results = await self.qdrant_store.search_similar(query, k, filter=filter_condition)
        return self._filter_by_threshold(results, score_threshold)

    def search_similar_sync(
        self,
        query: str,
        k: int = 10,
        score_threshold: float = 0.0,
        recording_id: Optional[str] = None,
    ) -> list[tuple[Document, float]]:
        """Sync search for similar segments."""
        filter_condition = self._create_recording_filter(recording_id)

        # For sync search, we need to use the Qdrant client directly with filter
        if filter_condition is not None:
            # Get embedding for the query
            query_embedding = self.qdrant_store.embedding_model.embed_query(query)

            # Search with filter using Qdrant client
            search_result = self.qdrant_store.client.search(
                collection_name=self.qdrant_store.collection_name,
                query_vector=query_embedding,
                limit=k,
                query_filter=filter_condition,
                with_payload=True,
                with_vectors=False
            )

            # Convert to LangChain format
            results = []
            for hit in search_result:
                doc = Document(
                    page_content=hit.payload["page_content"],
                    metadata=hit.payload["metadata"]
                )
                results.append((doc, hit.score))

            return self._filter_by_threshold(results=results, score_threshold=score_threshold)
        else:
            # Use LangChain's sync method if no filter needed
            results = self.qdrant_store.get_vector_store().similarity_search_with_score(query, k)
            return self._filter_by_threshold(results=results, score_threshold=score_threshold)
