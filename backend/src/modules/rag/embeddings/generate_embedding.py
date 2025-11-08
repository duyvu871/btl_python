"""
Embedding generation service using Google AI, OpenAI, and Cohere models.
"""

from httpx import AsyncClient
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings

BaseEmbeddingGenerator = Embeddings


class GoogleEmbeddingGenerator(BaseEmbeddingGenerator):
    """
    Service for generating embeddings from text using Google AI models.
    """

    def __init__(self, model_name: str = "text-embedding-004", api_key: str = None, output_dimensionality: int = None):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the Google AI embedding model to use
            api_key: Google AI API key (if not set in environment)
        """
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=api_key,
        )
        self.output_dimensionality = output_dimensionality

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return self.embedding_model.embed_query(text, output_dimensionality=self.output_dimensionality)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embedding_model.embed_documents(texts,output_dimensionality=self.output_dimensionality)

    async def aembed_query(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return await self.embedding_model.aembed_query(text, output_dimensionality=self.output_dimensionality)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.embedding_model.aembed_documents(texts, output_dimensionality=self.output_dimensionality)


class OpenAIEmbeddingGenerator(BaseEmbeddingGenerator):
    """
    Service for generating embeddings from text using OpenAI models.
    """

    def __init__(self, model_name: str = "text-embedding-3-small", api_key: str = None, base_url: str = None):
        """
        Initialize the embedding generator.

        Args:
            model_name: Name of the OpenAI embedding model to use
            api_key: OpenAI API key (if not set in environment)
        """
        self.embedding_model = OpenAIEmbeddings(
            base_url=base_url,
            model=model_name,
            api_key=api_key
        )

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return self.embedding_model.embed_query(text)

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return self.embedding_model.embed_documents(texts)

    async def aembed_query(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a query text.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        return await self.embedding_model.aembed_query(text)

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple documents.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        return await self.embedding_model.aembed_documents(texts)


class APIEmbeddingGenerator(BaseEmbeddingGenerator):
    """
    Service for generating embeddings by calling a local API endpoint.
    """

    def __init__(self, base_url: str = "http://localhost:8000", model_name: str = "text-embedding-3-small", api_key: str = None):
        """
        Initialize the API embedding generator.

        Args:
            base_url: Base URL of the API server
            model_name: Model name to use for embeddings
            api_key: API key for authentication (if required)
        """
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name

    def _get_headers(self) -> dict:
        """
        Get headers for API requests.

        Returns:
            Dictionary of headers
        """
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _call_api(self, payload: dict) -> dict:
        """
        Make a synchronous API call to the embeddings endpoint.

        Args:
            payload: Request payload

        Returns:
            Response data
        """
        import requests
        headers = self._get_headers()
        response = requests.post(f"{self.base_url}/v1/embeddings", json=payload, headers=headers)
        response.raise_for_status()
        return response.json()

    async def _acall_api(self, payload: dict) -> dict:
        """
        Make an asynchronous API call to the embeddings endpoint.

        Args:
            payload: Request payload

        Returns:
            Response data
        """
        async with AsyncClient(timeout=120.0) as client:  # Increased timeout to 120 seconds
            headers = self._get_headers()
            response = await client.post(f"{self.base_url}/v1/embeddings", json=payload, headers=headers)
            response.raise_for_status()
            return response.json()

    def embed_query(self, text: str) -> list[float]:
        """
        Generate embedding for a query text by calling the API.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        payload = {"input": text, "model": self.model_name}
        # print(f"APIEmbeddingGenerator.embed_query payload: {payload}")
        data = self._call_api(payload)
        return data['data'][0]['embedding']

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple documents by calling the API.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        payload = {"input": texts, "model": self.model_name}
        # print(f"APIEmbeddingGenerator.embed_documents payload: {payload}")
        data = self._call_api(payload)
        return [item['embedding'] for item in data['data']]

    async def aembed_query(self, text: str) -> list[float]:
        """
        Asynchronously generate embedding for a query text by calling the API.

        Args:
            text: Query text to embed

        Returns:
            Embedding vector
        """
        payload = {"input": text, "model": self.model_name}
        # print(f"APIEmbeddingGenerator.aembed_query payload: {payload}")
        data = await self._acall_api(payload)
        return data['data'][0]['embedding']

    async def aembed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Asynchronously generate embeddings for multiple documents by calling the API.

        Args:
            texts: List of document texts to embed

        Returns:
            List of embedding vectors
        """
        payload = {"input": texts, "model": self.model_name}
        # print(f"APIEmbeddingGenerator.aembed_documents input length: {payload.get('input') and len(payload['input'])}")
        data = await self._acall_api(payload)
        return [item['embedding'] for item in data['data']]


# Backward compatibility alias
EmbeddingGenerator = APIEmbeddingGenerator
