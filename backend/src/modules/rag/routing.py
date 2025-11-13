"""RAG module routing - simplified with dependency injection."""

from fastapi import APIRouter, HTTPException, Depends, Request

from src.modules.rag.schema import AskRequest, AskResponse, SourceItem
from src.modules.rag.chains.rag import AudioTranscriptRAGChain, RAGInput

def get_rag_chain(request: Request) -> AudioTranscriptRAGChain:
    """Dependency: get RAG chain instance from app state."""
    return request.app.state.rag_chain

router = APIRouter(prefix="/ai", tags=["ai"])

@router.post("/ask", response_model=AskResponse)
async def ask_about_transcript(
    request: AskRequest,
    rag_chain: AudioTranscriptRAGChain = Depends(get_rag_chain),
):
    """Ask questions about audio transcripts using RAG."""
    try:
        result = await rag_chain.ainvoke({
            "query": request.query,
            "top_k": request.top_k,
            "score_threshold": request.score_threshold,
            "rerank_top_k": request.rerank_top_k
        })

        sources = [
            SourceItem(text=doc.page_content, score=0.0, metadata=doc.metadata)
            for doc in result.reranked_docs
        ]

        return AskResponse(message=result.completion, sources=sources, total=len(sources))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))