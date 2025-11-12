from google import genai
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi import APIRouter, HTTPException
from qdrant_client import QdrantClient
from langchain_core.documents import Document

from src.modules.rag.schema import AIRequest, AIResponse, SourceItem
from src.modules.rag.embeddings.generate_embedding import GeminiEmbeddingGenerator
from src.modules.rag.chains.reranker import Reranker
from src.modules.rag.embeddings.qdrant_store import QdrantStore
from src.core.config.env import env

segments = [
    {"id": 1, "recording_id": 1, "idx": 0, "start_ms": 0, "end_ms": 3000, "text": "What is the meaning of life?"},
    {"id": 2, "recording_id": 1, "idx": 1, "start_ms": 3000, "end_ms": 6000, "text": "What is the purpose of existence?"},
    {"id": 3, "recording_id": 1, "idx": 2, "start_ms": 6000, "end_ms": 9000, "text": "How do I bake a cake?"},
    {"id": 4, "recording_id": 1, "idx": 3, "start_ms": 9000, "end_ms": 12000, "text": "I like apple"}
]

documents = [
    Document(
        page_content=seg["text"],
        metadata={
            "segment_id": seg["id"],
            "recording_id": seg["recording_id"],
            "idx": seg["idx"],
            "start_ms": seg["start_ms"],
            "end_ms": seg["end_ms"]
        }
    )
    for seg in segments
]

client = genai.Client(api_key=env.GEMINI_API_KEY)
generator = GeminiEmbeddingGenerator() 
reranker = Reranker(generator)

qdrant_client = QdrantClient(url="http://qdrant:6333")
collection_name = "recording_segment"
vector_size = 3072
qdrant_store = QdrantStore(
    client=qdrant_client,
    collection_name=collection_name,
    embedding_model=generator,
    vector_size=vector_size
)
qdrant_store.ensure_collection_exists(recreate=False)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup code ---
    collection_info = qdrant_client.get_collection(collection_name)
    if collection_info.points_count == 0:
        texts = [doc.page_content for doc in documents]
        embeddings = generator.embed_documents(texts)
        await qdrant_store.add_documents_with_embeddings(documents=documents, embeddings=embeddings)
        print(f"Pushed {len(documents)} documents to Qdrant.")
    
    yield  # đây là thời điểm app chạy
    
    # --- Shutdown code nếu cần ---
    print("Application shutdown")

router = APIRouter(
    prefix="/ai",
    tags=["ai"],
)

def generate_embedding_langchain(texts: list[str]):
    return generator.embed_documents(texts=texts);
   
async def call_gemini_ai_rag_qdrant(query: str, top_k_qdrant: int = 10, top_k_rerank: int = 3):
    results = await qdrant_store.search_similar(query, k=top_k_qdrant)
    
    documents_with_meta = [(res, score) for res, score in results]

    # Rerank with cosine similarity
    ranked = await reranker.arerank(query=query, documents=[doc.page_content for doc, _ in documents_with_meta])
    top_text = [doc_text for doc_text, _ in ranked[:top_k_rerank]]
    top_context = [(doc, score) for doc, score in documents_with_meta if doc.page_content in top_text]

    # context_block = "\n".join(top_text)
    context_block = "\n".join([
        f"{doc.page_content} segment_id: {doc.metadata['segment_id']}, recording_id: {doc.metadata['recording_id']}, idx: {doc.metadata['idx']}, start_ms: {doc.metadata['start_ms']}, end_ms: {doc.metadata['end_ms']}"
        for doc, _ in top_context
    ])
    prompt = f"Context:\n{context_block}\n\nQuestion: {query}"

    response = client.models.generate_content(
        model=env.GEMINI_MODEL,
        contents=f"{prompt}. Ngắn gọn"
    )

    sources = [SourceItem(text=doc.page_content, score=score, metadata=doc.metadata) for doc, score in top_context]

    return response.text, sources

@router.post("/ask", response_model=AIResponse)
async def ask_ai(request: AIRequest):
    """
    Ask a question to AI.
    """
    try:
        answer, sources = await call_gemini_ai_rag_qdrant(request.query)
        return AIResponse(answer=answer, sources=sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))