"""Chat module routing - API endpoints for chat operations."""
import logging
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends, status, Request

from src.core.database.models import MessageRole
from src.core.database.models.user import User
from src.core.security.user import get_current_user
from src.modules.chat.schema import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessageRead,
    ChatSessionRead,
    CreateMessageRequest,
    CreateSessionRequest,
    UpdateSessionRequest,
)
from src.modules.chat.use_cases.helpers import ChatUseCase, get_chat_usecase
from src.modules.rag.chains.rag import AudioTranscriptRAGChain
from src.modules.rag.schema import AskRequest
from src.shared.schemas.response import SuccessResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chats", tags=["chats"])

def get_rag_chain(request: Request) -> AudioTranscriptRAGChain:
    """Dependency: get RAG chain instance from app state."""
    return request.app.state.rag_chain

@router.post("", response_model=SuccessResponse[ChatSessionRead], status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Create a new chat session for a recording."""
    try:
        data = await chat_usecase.create_session(current_user.id, request)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating chat session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
@router.get("", response_model=SuccessResponse[dict])
async def list_sessions(
    page: int = 1,
    per_page: int = 20,
    recording_id: UUID | None = None,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """List all chat sessions for current user."""
    try:
        data = await chat_usecase.list_sessions(current_user.id, page, per_page, recording_id)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing chat sessions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
@router.get("/{session_id}", response_model=SuccessResponse[ChatSessionRead])
async def get_session_detail(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Get details of a specific chat session."""
    try:
        data = await chat_usecase.get_session(current_user.id, session_id)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting chat session detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
@router.patch("/{session_id}", response_model=SuccessResponse[ChatSessionRead])
async def update_session_title(
    session_id: UUID,
    request: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Update chat session title."""
    try:
        data = await chat_usecase.update_session(current_user.id, session_id, request)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating chat session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Delete a chat session."""
    try:
        await chat_usecase.delete_session(current_user.id, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting chat session: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
# ============================================================================
# Chat Message Endpoints
# ============================================================================
@router.post("/{session_id}/messages", response_model=SuccessResponse[ChatMessageRead], status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: UUID,
    request: CreateMessageRequest,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Add a message to a chat session."""
    try:
        data = await chat_usecase.add_user_message(current_user.id, session_id, request)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error adding message: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
@router.get("/{session_id}/messages", response_model=SuccessResponse[list[ChatMessageRead]])
async def get_session_messages(
    session_id: UUID,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
):
    """Get all messages in a chat session."""
    try:
        data = await chat_usecase.get_session_messages(current_user.id, session_id)
        return SuccessResponse(data=data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting session messages: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# ============================================================================
# Chat Completion Endpoints
# ============================================================================


@router.post("/{session_id}/ask", response_model=SuccessResponse[ChatCompletionResponse])
async def ask_question(
    session_id: UUID,
    request: ChatCompletionRequest,
    current_user: User = Depends(get_current_user),
    chat_usecase: ChatUseCase = Depends(get_chat_usecase),
    rag_chain: AudioTranscriptRAGChain = Depends(get_rag_chain),
):
    """Ask a question and get AI response in a chat session."""
    try:
        # 1. Add user message to session
        user_message = await chat_usecase.add_user_message(
            current_user.id,
            session_id,
            CreateMessageRequest(content=request.query, role=MessageRole.USER)
        )

        # 2. Get AI response using RAG
        rag_result = await rag_chain.ainvoke({
            "query": request.query,
            "top_k": request.top_k,
            "score_threshold": request.score_threshold,
            "rerank_top_k": request.rerank_top_k
        })

        # 3. Convert RAG sources to our format
        sources = []
        for doc in rag_result.reranked_docs:
            sources.append({
                "text": doc.page_content,
                "metadata": doc.metadata
            })

        # 4. Add assistant message to session
        assistant_message = await chat_usecase.add_assistant_message(
            current_user.id,
            session_id,
            rag_result.completion,
            sources=sources,
            prompt_tokens=getattr(rag_result, 'prompt_tokens', None),
            completion_tokens=getattr(rag_result, 'completion_tokens', None),
            total_tokens=getattr(rag_result, 'total_tokens', None),
        )

        # 5. Return both messages
        response_data = ChatCompletionResponse(
            user_message=user_message,
            assistant_message=assistant_message
        )

        return SuccessResponse(
            message="Question answered successfully",
            data=response_data
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in chat completion: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")
