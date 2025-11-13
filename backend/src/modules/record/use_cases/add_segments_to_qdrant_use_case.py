"""Use case for adding transcribed segments to Qdrant for RAG."""

from uuid import UUID

from langchain_core.documents import Document

from src.modules.rag.embeddings.generate_embedding import GoogleEmbeddingGenerator
from src.modules.rag.embeddings.qdrant_store import QdrantStore
from src.shared.uow import UnitOfWork


class AddSegmentsToQdrantUseCase:
    """Add transcribed segments to Qdrant vector store for RAG."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, recording_id: UUID, segments: list[dict]) -> int:
        """
        Add segments to Qdrant for RAG search.

        Args:
            recording_id: UUID of the recording
            segments: List of segment dictionaries with format:
                {
                    "id": int,
                    "recording_id": int,
                    "idx": int,
                    "start_ms": int,
                    "end_ms": int,
                    "text": str
                }

        Returns:
            Number of documents added to Qdrant

        Raises:
            ValueError: If recording not found or segments invalid
        """
        # Verify recording exists
        recording = await self.uow.recording_repo.get(recording_id)
        if not recording:
            raise ValueError(f"Recording {recording_id} not found")

        if not segments:
            return 0

        # Convert segments to LangChain documents
        documents = []
        for seg in segments:
            # Validate required fields
            required_fields = ["id", "recording_id", "idx", "start_ms", "end_ms", "text"]
            if not all(field in seg for field in required_fields):
                raise ValueError(f"Segment missing required fields: {seg}")

            document = Document(
                page_content=seg["text"],
                metadata={
                    "segment_id": seg["id"],
                    "recording_id": seg["recording_id"],
                    "idx": seg["idx"],
                    "start_ms": seg["start_ms"],
                    "end_ms": seg["end_ms"]
                }
            )
            documents.append(document)

        # Initialize Qdrant store (this should be injected or configured)
        # For now, we'll create it here - in production this should be dependency injected
        from src.core.config.env import env
        from qdrant_client import QdrantClient

        qdrant_client = QdrantClient(url=env.QDRANT_URL)
        embedding_gen = GoogleEmbeddingGenerator(
            model_name="gemini-embedding-001",
            api_key=env.GOOGLE_API_KEY
        )

        qdrant_store = QdrantStore(
            client=qdrant_client,
            collection_name=env.QDRANT_AUDIO_TRANSCRIPT_COLLECTION,
            embedding_model=embedding_gen,
            vector_size=3072
        )

        # Ensure collection exists
        qdrant_store.ensure_collection_exists(recreate=False)

        # Add documents with embeddings
        await qdrant_store.add_documents_with_embeddings(
            documents=documents,
            embeddings=await embedding_gen.aembed_documents([doc.page_content for doc in documents])
        )

        return len(documents)

