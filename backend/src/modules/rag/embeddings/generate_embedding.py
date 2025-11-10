from google import genai
from google.genai import types
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from src.core.config.env import env

BaseEmbeddingGenerator = Embeddings

class GeminiEmbeddingGenerator(BaseEmbeddingGenerator):
    """
    Generate embeddings from document using Gemini embedding model.
    """

    def __init__(self, model_name: str = "gemini-embedding-001", output_dimensionality: int = None):
        self.embedding_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=env.GEMINI_API_KEY,
            task_type="SEMANTIC_SIMILARITY"
        )
        self.output_dimensionality = output_dimensionality

    def embed_query(self, text: str) -> list[float]:
        return self.embedding_model.embed_query(text=text, output_dimensionality=self.output_dimensionality)
    
    def embed_documents(self, texts) -> list[list[float]]:
        return self.embedding_model.embed_documents(texts, output_dimensionality=self.output_dimensionality)
    
    async def aembed_query(self, text) -> list[float]:
        return await self.embedding_model.aembed_query(text=text, output_dimensionality=self.output_dimensionality)


    async def aembed_documents(self, texts) -> list[list[float]]:
        return await self.embedding_model.aembed_documents(texts, output_dimensionality=self.output_dimensionality)