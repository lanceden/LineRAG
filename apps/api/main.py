from contextlib import asynccontextmanager
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

# Core utilities
from app.core.logging import setup_logging
from app.core.database import create_tables
from app.core.middleware import PermissionMiddleware

# Services (initialize on startup)
from app.services.multitenant_rag import get_multitenant_rag_service
from app.services.rag_anything import get_rag_service
from app.services.resource_monitor import (
    start_resource_monitoring,
    stop_resource_monitoring,
)

# Routers
from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.ask import router as ask_router
from app.routers.ingest import router as ingest_router
from app.routers.webhook import router as webhook_router
from app.routers.system_users import router as system_users_router
from app.routers.tenant_users import router as tenant_users_router
from app.routers.admin import router as admin_router
from app.routers.companies import router as companies_router
from app.routers.knowledge_graph import router as knowledge_graph_router
from app.routers.metrics import router as metrics_router
from app.routers.permissions import router as permissions_router


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

    # 清空所有緩存，防止舊狀態引起重複對話
    multitenant_rag_service.clear_all_caches()

    logger.info("✅ Multi-Tenant RAG service initialized successfully")

    # 啟動資源監控
    try:
        await start_resource_monitoring()
        logger.info("✅ Resource monitoring started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start resource monitoring: {e}")

    # Initialize RAG-Anything service
    try:
        rag_service = get_rag_service()
        logger.info(
            "📦 RAG-Anything service instance created, attempting initialization..."
        )
        await rag_service.initialize()
        logger.info("✅ RAG-Anything service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize RAG-Anything service: {e}")
        logger.error(f"❌ Error type: {type(e).__name__}")
        import traceback

        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        # Continue anyway, service will be initialized on first use

    yield

    # Shutdown
    logger.info("🛑 Shutting down LineRAG API...")
    await multitenant_rag_service.cleanup_all_services()

    # 停止資源監控
    try:
        await stop_resource_monitoring()
        logger.info("✅ Resource monitoring stopped successfully")
    except Exception as e:
        logger.error(f"❌ Failed to stop resource monitoring: {e}")


app = FastAPI(
    title="LineRAG Multi-Tenant API",
    description="Multi-Tenant RAG API with RAG-Anything multimodal support",
    version="2.0.0",
    lifespan=lifespan,
    root_path="/api",  # 添加 API 前綴支援 nginx 反向代理
)

# Configure CORS FIRST (必須在其他中間件之前)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Add Metrics Middleware (before JWT for monitoring all requests)
class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Import here to avoid circular imports
        from app.routers.metrics import record_request_metrics

        record_request_metrics(request, response, process_time)

        return response


app.add_middleware(MetricsMiddleware)

# Add JWT authentication middleware AFTER CORS and Metrics
app.add_middleware(PermissionMiddleware)

# Include modular routers
app.include_router(health_router)
app.include_router(auth_router)  # 認證路由不需要認證
app.include_router(ask_router)
app.include_router(ingest_router)
app.include_router(webhook_router)
app.include_router(system_users_router)
app.include_router(tenant_users_router)
app.include_router(admin_router)
app.include_router(companies_router)
app.include_router(knowledge_graph_router)
app.include_router(metrics_router)
app.include_router(permissions_router)


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
