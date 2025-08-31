from contextlib import asynccontextmanager
import asyncio
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
    """Application lifespan events with robust error handling."""
    logger = setup_logging()

    # Startup
    logger.info("🚀 Starting LineRAG API with Multi-Tenant RAG-Anything...")

    startup_tasks = []
    cleanup_tasks = []

    try:
        # Initialize database tables
        try:
            create_tables()
            logger.info("✅ Database tables initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database tables: {e}")
            # Do not crash the app; health endpoint will reflect the error state.

        # Initialize Multi-Tenant RAG service with error handling
        try:
            multitenant_rag_service = get_multitenant_rag_service()
            startup_tasks.append(multitenant_rag_service)

            # 清空所有緩存，防止舊狀態引起重複對話
            if hasattr(multitenant_rag_service, "clear_all_caches"):
                multitenant_rag_service.clear_all_caches()
            logger.info("✅ Multi-Tenant RAG service initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize Multi-Tenant RAG service: {e}")
            # Don't raise here, continue with degraded functionality
            multitenant_rag_service = None

        # 啟動資源監控
        try:
            resource_monitor = await start_resource_monitoring()
            startup_tasks.append(resource_monitor)
            logger.info("✅ Resource monitoring started successfully")
        except Exception as e:
            logger.error(f"❌ Failed to start resource monitoring: {e}")
            # Continue without resource monitoring

        # RAG-Anything 服務將在第一次使用時按需初始化（多租戶模式）
        logger.info("✅ 服務初始化完成（使用多租戶模式）")

        yield

    except asyncio.CancelledError:
        logger.warning("⚠️  Application startup was cancelled")
        raise
    except Exception as e:
        logger.error(f"❌ Critical error during application startup: {e}")
        raise
    finally:
        # Shutdown - Always execute cleanup, even if startup failed
        logger.info("🛑 Shutting down LineRAG API...")

        # Execute cleanup tasks with timeout protection
        cleanup_timeout = 30  # seconds
        try:
            await asyncio.wait_for(
                _perform_cleanup(cleanup_tasks, logger), timeout=cleanup_timeout
            )
        except asyncio.TimeoutError:
            logger.error(f"❌ Cleanup timed out after {cleanup_timeout} seconds")
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")
        finally:
            logger.info("✅ Application shutdown complete")


async def _perform_cleanup(cleanup_tasks, logger):
    """Perform cleanup tasks with proper error handling."""
    # Cleanup Multi-Tenant RAG service
    for task in cleanup_tasks:
        try:
            if hasattr(task, "cleanup_all_services"):
                await task.cleanup_all_services()
                logger.info("✅ Multi-Tenant RAG service cleaned up")
            elif hasattr(task, "stop_monitoring"):
                await task.stop_monitoring()
                logger.info("✅ Resource monitoring stopped")
        except asyncio.CancelledError:
            logger.warning("⚠️  Cleanup task was cancelled, continuing with other tasks")
            continue
        except Exception as e:
            logger.error(f"❌ Error cleaning up task: {e}")
            continue

    # Additional cleanup for any remaining resources
    try:
        # Force cleanup of any remaining async tasks
        current_task = asyncio.current_task()
        if current_task:
            # Cancel any child tasks that might still be running
            for task in asyncio.all_tasks():
                if task != current_task and not task.done():
                    task.cancel()

        logger.info("✅ All cleanup tasks completed")
    except Exception as e:
        logger.error(f"❌ Error in final cleanup: {e}")


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
