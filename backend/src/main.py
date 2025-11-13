import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from qdrant_client import QdrantClient
from scalar_fastapi import Theme, get_scalar_api_reference
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

import src.core.logger
from src.api.v1.main import api_router
from src.core.config.env import env, global_logger_name
from src.modules.rag.chains.completion import LLMConfig, ModelName
from src.modules.rag.chains.rag import AudioTranscriptRAGChain
from src.modules.rag.embeddings.audio_search import AudioSearch
from src.modules.rag.embeddings.generate_embedding import GoogleEmbeddingGenerator
from src.modules.rag.embeddings.qdrant_store import QdrantStore
from src.shared.schemas.response import ErrorResponse

logger = logging.getLogger(global_logger_name)

@asynccontextmanager
async def lifespan(fastapi_app: FastAPI):
    logger.info("Initializing resources...")
    # 1. Khởi tạo client
    qdrant_client = QdrantClient(url=env.QDRANT_URL)

    # 2. Khởi tạo embedding generator
    embedding_gen = GoogleEmbeddingGenerator(model_name="gemini-embedding-001", api_key=env.GOOGLE_API_KEY)

    # 3. Khởi tạo QdrantStore
    qdrant_store = QdrantStore(
        client=qdrant_client,
        collection_name=env.QDRANT_AUDIO_TRANSCRIPT_COLLECTION,
        embedding_model=embedding_gen,
        vector_size=3072
    )

    # 4. Chạy I/O kiểm tra collection
    qdrant_store.ensure_collection_exists(recreate=False)

    # 5. Khởi tạo RAG chain
    rag_chain = AudioTranscriptRAGChain(
        search_engine=AudioSearch(qdrant_store),
        embedding_generator=embedding_gen,
        llm_config=LLMConfig(
            api_key=env.GOOGLE_API_KEY,
            model_name=ModelName.GEMINI_2_5_FLASH,
            temperature=0.7,
            max_output_tokens=2048,
            top_p=0.95,
            top_k=40
        )
    )

    # 6. Lưu tất cả vào app state để các dependency có thể dùng
    fastapi_app.state.rag_chain = rag_chain
    fastapi_app.state.qdrant_store = qdrant_store
    fastapi_app.state.embedding_gen = embedding_gen

    logger.info("Resources initialized successfully.")

    yield  # Server bắt đầu nhận request ở đây

    # --- Code chạy KHI SERVER TẮT ---
    logger.info("Resources initialized successfully.")
    qdrant_client.close()

app = FastAPI(
    title="Backend API",
    version="1.0.0",
    openapi_url=f"{env.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

if env.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=env.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "btl-python-backend",
        "version": "1.0.0"
    }

# Register a global exception handler
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """
    catch HTTP exceptions and return JSON response.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            message=str(exc.detail)
        ).model_dump()
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """
    Catch-all handler for unexpected exceptions.
    """
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error_code="INTERNAL_SERVER_ERROR",
            message="An unexpected internal error occurred."
        ).model_dump()
    )

# Scalar UI endpoint
@app.get("/scalar", include_in_schema=False)
async def scalar_html():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title + " - Scalar UI",
        theme=Theme.BLUE_PLANET,
    )

# Include API routers here
app.include_router(api_router, prefix=env.API_PREFIX)
