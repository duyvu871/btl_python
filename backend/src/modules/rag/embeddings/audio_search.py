"""Audio transcript search with threshold filtering."""

from langchain_core.documents import Document
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

    async def search_similar(
        self,
        query: str,
        k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[tuple[Document, float]]:
        """Async search for similar segments."""
        results = await self.qdrant_store.search_similar(query, k)
        return self._filter_by_threshold(results, score_threshold)

    def search_similar_sync(
        self,
        query: str,
        k: int = 10,
        score_threshold: float = 0.0,
    ) -> list[tuple[Document, float]]:
        """Sync search for similar segments."""
        results = self.qdrant_store.get_vector_store().similarity_search_with_score(query, k)
        return self._filter_by_threshold(results=results, score_threshold=score_threshold)
