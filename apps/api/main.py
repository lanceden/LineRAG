from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Core utilities
from app.core.logging import setup_logging
from app.core.database import create_tables
from app.core.middleware import JWTAuthMiddleware

# Services (initialize on startup)
from app.services.multitenant_rag import get_multitenant_rag_service

# Routers
from app.routers.health import router as health_router
from app.routers.ask import router as ask_router
from app.routers.ingest import router as ingest_router
from app.routers.webhook import router as webhook_router
from app.routers.system_users import router as system_users_router
from app.routers.tenant_users import router as tenant_users_router
from app.routers.admin import router as admin_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    logger = setup_logging()

    # Startup
    logger.info("🚀 Starting LineRAG API with Multi-Tenant RAG-Anything...")

    # Initialize database tables
    try:
        create_tables()
        logger.info("✅ Database tables initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database tables: {e}")
        # Do not crash the app; health endpoint will reflect the error state.

    # Initialize Multi-Tenant RAG service
    multitenant_rag_service = get_multitenant_rag_service()
    logger.info("✅ Multi-Tenant RAG service initialized successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down LineRAG API...")
    await multitenant_rag_service.cleanup_all_services()


app = FastAPI(
    title="LineRAG Multi-Tenant API",
    description="Multi-Tenant RAG API with RAG-Anything multimodal support",
    version="2.0.0",
    lifespan=lifespan,
    root_path="/api",  # 添加 API 前綴支援 nginx 反向代理
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add JWT authentication middleware
app.add_middleware(JWTAuthMiddleware)

# Include modular routers
app.include_router(health_router)
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(webhook_router)
app.include_router(system_users_router)
app.include_router(tenant_users_router)
app.include_router(admin_router)


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
        print("Debug server listening on port 5678")
        print("In VSCode choose 'Attach to FastAPI' to debug")
        debugpy.wait_for_client()  # 等待 debugger 連接

    print("Starting FastAPI (Debug Mode)")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True, log_level="debug")
