from contextlib import asynccontextmanager
from fastapi import FastAPI

# Core utilities
from app.core.logging import setup_logging

# Services (initialize on startup)
from app.services.vectorstore import get_vectorstore_service
from app.services.user_service import get_user_service

# Ensure LLM client initializes OpenAI base/key
from app.services import llm as _llm  # noqa: F401

# Routers
from app.routers.health import router as health_router
from app.routers.ask import router as ask_router
from app.routers.ingest import router as ingest_router
from app.routers.image import router as image_router
from app.routers.webhook import router as webhook_router
from app.routers.users import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger = setup_logging()

    # Startup
    logger.info("🚀 Starting LineRAG API...")

    # Initialize vector store (embeddings + Qdrant)
    vs = get_vectorstore_service()
    try:
        vs.init()
        logger.info("✅ Vector store initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize vector store: {e}")
        # Do not crash the app; health endpoint will reflect the error state.

    # Initialize user service (Redis)
    user_service = await get_user_service()
    logger.info("✅ User service initialized successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down LineRAG API...")


app = FastAPI(
    title="LineRAG API",
    description="RAG API with multimodal support",
    version="1.0.0",
    lifespan=lifespan,
)


# Include modular routers
app.include_router(health_router)
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(image_router)
app.include_router(webhook_router)
app.include_router(users_router)


# 支援直接運行調試
if __name__ == "__main__":
    import uvicorn
    import os

    print(os.getenv("DEBUG"))
    print(os.getenv("DEBUG") == "1")
    print(os.getenv("DEBUG") == "True")
    # 如果設定了DEBUG環境變數，啟用debugpy
    if os.getenv("DEBUG") == "1":  # 只在設定DEBUG=1時啟用
        import debugpy

        debugpy.listen(("0.0.0.0", 5678))
        print("🔍 Debug server listening on port 5678")
        print("💡 在VSCode中選擇 '🔗 Attach to FastAPI' 進行debug")
        debugpy.wait_for_client()  # 等待 debugger 連接

    print("🚀 直接運行 FastAPI (Debug 模式)")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
