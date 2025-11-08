"""
Reranker service using embedding generators from generate_embedding.py.
"""

from typing import Any

import numpy as np

from src.modules.rag.embeddings import BaseEmbeddingGenerator


def cosine_similarity(vec1: list[float], vec2: list[float]) -> float:
    """
    Calculate cosine similarity between two vectors.

    Args:
        vec1: First vector
        vec2: Second vector

    Returns:
        Cosine similarity score
    """
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


class Reranker:
    """
    Reranker class that uses an embedding generator to rerank documents based on query similarity.
    """

    def __init__(self, embedding_generator: BaseEmbeddingGenerator):
        """
        Initialize the reranker with an embedding generator.

        Args:
            embedding_generator: Instance of a class inheriting from BaseEmbeddingGenerator
        """
        self.embedding_generator = embedding_generator

    def rerank(self, query: str, documents: list[str]) -> list[tuple[str, float]]:
        """
        Rerank documents based on their similarity to the query.

        Args:
            query: The query string
            documents: List of document strings to rerank

        Returns:
            List of tuples (document, similarity_score) sorted by similarity descending
        """
        # Generate embedding for the query
        query_emb = self.embedding_generator.embed_query(query)

        # Generate embeddings for the documents
        doc_embs = self.embedding_generator.embed_documents(documents)

        # Calculate similarities
        similarities = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

        # Rank documents by similarity (highest first)
        ranked = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        return ranked

    async def arerank(self, query: str, documents: list[str]) -> list[tuple[str, float]]:
        """
        Asynchronously rerank documents based on their similarity to the query.

        Args:
            query: The query string
            documents: List of document strings to rerank

        Returns:
            List of tuples (document, similarity_score) sorted by similarity descending
        """
        # Generate embedding for the query asynchronously
        query_emb = await self.embedding_generator.aembed_query(query)

        # Generate embeddings for the documents asynchronously
        doc_embs = await self.embedding_generator.aembed_documents(documents)

        # Calculate similarities (cosine similarity is synchronous)
        similarities = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

        # Rank documents by similarity (highest first)
        ranked = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        return ranked

    def rerank_objects(self, query: str, documents: list[Any], text_attr: str = 'content') -> list[tuple[Any, float]]:
        """
        Rerank document objects based on their similarity to the query, using a specified text attribute.

        Args:
            query: The query string
            documents: List of document objects to rerank
            text_attr: Attribute name of the document object to extract text for embedding (default: 'content')

        Returns:
            List of tuples (document, similarity_score) sorted by similarity descending
        """
        # Extract texts from documents using the specified attribute
        texts = [getattr(doc, text_attr) for doc in documents]

        # Generate embedding for the query
        query_emb = self.embedding_generator.embed_query(query)

        # Generate embeddings for the documents
        doc_embs = self.embedding_generator.embed_documents(texts)

        # Calculate similarities
        similarities = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

        # Rank documents by similarity (highest first)
        ranked = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        return ranked  # type: ignore

    async def arerank_objects(self, query: str, documents: list[Any], text_attr: str = 'content') -> list[tuple[Any, float]]:
        """
        Asynchronously rerank document objects based on their similarity to the query, using a specified text attribute.

        Args:
            query: The query string
            documents: List of document objects to rerank
            text_attr: Attribute name of the document object to extract text for embedding (default: 'content')

        Returns:
            List of tuples (document, similarity_score) sorted by similarity descending
        """
        # Extract texts from documents using the specified attribute
        texts = [getattr(doc, text_attr) for doc in documents]

        # Generate embedding for the query asynchronously
        query_emb = await self.embedding_generator.aembed_query(query)

        # Generate embeddings for the documents asynchronously
        doc_embs = await self.embedding_generator.aembed_documents(texts)

        # Calculate similarities (cosine similarity is synchronous)
        similarities = [cosine_similarity(query_emb, doc_emb) for doc_emb in doc_embs]

        # Rank documents by similarity (highest first)
        ranked = sorted(zip(documents, similarities), key=lambda x: x[1], reverse=True)

        return ranked  # type: ignore
