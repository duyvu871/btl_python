"""RAG Chain for audio transcript QA with simplified flow."""

from dataclasses import dataclass
from typing import TypedDict

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate

from src.modules.rag.chains.completion import PromptBasedCompletionChain, LLMConfig
from src.modules.rag.chains.reranker import Reranker
from src.modules.rag.embeddings.generate_embedding import BaseEmbeddingGenerator
from src.modules.rag.embeddings.audio_search import AudioSearch


class RAGInput(TypedDict):
    """Input for RAG chain."""
    query: str
    top_k: int
    score_threshold: float
    rerank_top_k: int


@dataclass
class RAGResult:
    """Result from RAG chain."""
    reranked_docs: list[Document]
    completion: str


class AudioTranscriptRAGChain:
    """RAG Chain for audio transcript QA."""

    PROMPT_TEMPLATE = """You are a helpful AI assistant specializing in answering questions about audio transcripts. You have access to relevant transcript segments as reference materials.

**Your Role:**
- Answer questions conversationally and helpfully
- Use transcript segments as reference when they contain relevant information
- If transcript segments don't contain relevant information, answer based on your general knowledge
- Reference specific transcript segments when using information from them
- Provide accurate, detailed answers when possible
- Use markdown formatting for better readability (lists, bold, italics, etc.)

**Examples:**
- If context has relevant info: "According to the transcript segment [Segment 1], the speaker mentioned..."
- If context lacks info: "While I don't have specific information from the transcript about this, generally speaking..."
- Use **bold** for emphasis, *italics* for stress, and lists for structured information

**Reference Materials (Transcript Segments):**
{context}

**User Question:** {question}

**Your Response:**"""

    def __init__(
        self,
        search_engine: AudioSearch,
        embedding_generator: BaseEmbeddingGenerator,
        llm_config: LLMConfig,
    ):
        self.search_engine = search_engine
        self.reranker = Reranker(embedding_generator)
        self.completion_chain = PromptBasedCompletionChain(
            config=llm_config,
            prompt_template=ChatPromptTemplate.from_template(self.PROMPT_TEMPLATE)
        ).build()

    def _extract_documents(self, search_results: list) -> list[Document]:
        """Extract documents from search results."""
        return [doc for doc, _ in search_results] if search_results else []

    def _format_context(self, documents: list[Document]) -> str:
        """Format documents into context string."""
        if not documents:
            return "(No relevant transcript segments found. You may answer based on general knowledge.)"

        parts = []
        for i, doc in enumerate(documents, 1):
            meta = doc.metadata
            segment_info = f"[Segment {meta.get('segment_id', i)}] {meta.get('start_ms', 0)}-{meta.get('end_ms', 0)}ms"
            parts.append(f"{segment_info}: {doc.page_content}")
        return "\n\n".join(parts)

    async def _rerank_docs(
        self,
        query: str,
        documents: list[Document],
        rerank_top_k: int
    ) -> list[Document]:
        """Rerank documents by relevance to query."""
        if not documents:
            return []
        reranked = await self.reranker.arerank_objects(query, documents, "page_content")
        return [doc for doc, _ in reranked[:rerank_top_k]]

    async def ainvoke(self, input_data: RAGInput) -> RAGResult:
        """Async invoke: search → rerank → generate answer."""
        results = await self.search_engine.search_similar(
            input_data["query"],
            input_data.get("top_k", 10),
            input_data.get("score_threshold", 0.1)
        )

        docs = self._extract_documents(results)
        reranked = await self._rerank_docs(
            input_data["query"],
            docs,
            input_data.get("rerank_top_k", 3)
        )

        # if not reranked:
        #     return RAGResult([], "No relevant information found.")

        context = self._format_context(reranked)
        completion = await self.completion_chain.ainvoke({
            "context": context,
            "question": input_data["query"]
        })

        return RAGResult(reranked, completion)

    def invoke(self, input_data: RAGInput) -> RAGResult:
        """Sync invoke: search → rerank → generate answer."""
        results = self.search_engine.search_similar_sync(
            input_data["query"],
            input_data.get("top_k", 10),
            input_data.get("score_threshold", 0.1)
        )

        docs = self._extract_documents(results)
        reranked = [doc for doc, _ in self.reranker.rerank_objects(
            input_data["query"],
            docs,
            "page_content"
        )[:input_data.get("rerank_top_k", 3)]]

        if not reranked:
            return RAGResult([], "No relevant information found.")

        context = self._format_context(reranked)
        completion = self.completion_chain.invoke({
            "context": context,
            "question": input_data["query"]
        })

        return RAGResult(reranked, completion)
