"""
Qdrant vector store service for managing collections and documents.
"""

import uuid

from langchain_core.embeddings import Embeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
from qdrant_client.models import PointStruct


class QdrantStore:
    """
    Service for managing Qdrant vector database operations.
    """

    def __init__(
            self,
            client: QdrantClient,
            collection_name: str,
            embedding_model: Embeddings,
            vector_size: int = 768
    ):
        """
        Initialize the Qdrant store.

        Args:
            client: QdrantClient instance
            collection_name: Name of the collection
            embedding_model: Embedding model (LangChain compatible)
            vector_size: Size of the embedding vectors
        """
        self.client = client
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.vector_size = vector_size
        self._vector_store: QdrantVectorStore | None = None

    def ensure_collection_exists(self, recreate: bool = False):
        """
        Ensure the collection exists, optionally recreating it.

        Args:
            recreate: Whether to delete and recreate the collection if it exists
        """
        collection_exists = self.client.collection_exists(self.collection_name)

        if collection_exists and recreate:
            self.client.delete_collection(collection_name=self.collection_name)
            collection_exists = False

        if not collection_exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE
                )
            )

    def get_vector_store(self) -> QdrantVectorStore:
        """
        Get the LangChain QdrantVectorStore instance.

        Returns:
            QdrantVectorStore instance
        """
        if self._vector_store is None:
            self._vector_store = QdrantVectorStore(
                client=self.client,
                collection_name=self.collection_name,
                embedding=self.embedding_model
            )
        return self._vector_store

    async def add_documents(self, documents, ids: list[str] | None = None):
        """
        Add documents to the vector store.

        Args:
            documents: List of Document objects
            ids: Optional list of IDs for the documents
        """
        vector_store = self.get_vector_store()
        await vector_store.aadd_documents(documents=documents, ids=ids)

    async def add_documents_with_embeddings(
        self,
        documents,
        embeddings: list[list[float]],
        ids: list[str] | None = None
    ):
        """
        Add documents with pre-computed embeddings to the vector store.
        This bypasses LangChain's embedding generation, allowing external rate limiting.

        Args:
            documents: List of Document objects
            embeddings: Pre-computed embeddings for the documents
            ids: Optional list of IDs for the documents
        """

        if len(documents) != len(embeddings):
            raise ValueError("Number of documents must match number of embeddings")

        # Generate IDs if not provided
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in documents]

        # Create points with embeddings
        points = []
        for i, (doc, embedding, point_id) in enumerate(zip(documents, embeddings, ids)):
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "page_content": doc.page_content,
                    "metadata": doc.metadata,
                }
            )
            points.append(point)

        # Upload to Qdrant
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    async def search_similar(self, query: str, k: int = 5, **kwargs):
        """
        Search for similar documents.

        Args:
            query: Search query
            k: Number of results to return
            **kwargs: Additional search parameters

        Returns:
            List of similar documents
        """
        vector_store = self.get_vector_store()
        return await vector_store.asimilarity_search_with_score(query=query, k=k, **kwargs)

    def delete_collection(self):
        """
        Delete the collection.
        """
        self.client.delete_collection(collection_name=self.collection_name)
        self._vector_store = None
