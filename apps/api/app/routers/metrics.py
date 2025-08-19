"""
Prometheus Metrics 路由
提供系統監控指標
"""

import time
import psutil
from typing import Dict, Any
from fastapi import APIRouter, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.database import get_db
from app.models.company import Company
from app.models.system_user import SystemUser
from app.models.tenant_user import TenantUser

# 創建 Prometheus 指標
REQUEST_COUNT = Counter(
    'linerag_http_requests_total', 
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'linerag_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

RAG_QUERY_COUNT = Counter(
    'linerag_rag_queries_total',
    'Total RAG queries processed',
    ['company_id', 'status']
)

RAG_RESPONSE_TIME = Histogram(
    'linerag_rag_response_time_seconds',
    'RAG query response time in seconds',
    ['company_id']
)

ACTIVE_COMPANIES = Gauge(
    'linerag_active_companies_total',
    'Number of active companies'
)

TOTAL_USERS = Gauge(
    'linerag_users_total',
    'Total number of users',
    ['user_type']
)

SYSTEM_CPU_PERCENT = Gauge(
    'linerag_system_cpu_percent',
    'CPU usage percentage'
)

SYSTEM_MEMORY_PERCENT = Gauge(
    'linerag_system_memory_percent', 
    'Memory usage percentage'
)

SYSTEM_DISK_PERCENT = Gauge(
    'linerag_system_disk_percent',
    'Disk usage percentage'
)

router = APIRouter(prefix="/metrics", tags=["monitoring"])

def update_system_metrics():
    """更新系統資源指標"""
    try:
        # CPU 使用率
        cpu_percent = psutil.cpu_percent(interval=1)
        SYSTEM_CPU_PERCENT.set(cpu_percent)
        
        # 記憶體使用率
        memory = psutil.virtual_memory()
        SYSTEM_MEMORY_PERCENT.set(memory.percent)
        
        # 磁碟使用率
        disk = psutil.disk_usage('/')
        disk_percent = (disk.used / disk.total) * 100
        SYSTEM_DISK_PERCENT.set(disk_percent)
        
    except Exception as e:
        print(f"Error updating system metrics: {e}")

def update_business_metrics():
    """更新業務指標"""
    try:
        db = next(get_db())
        
        # 活躍公司數
        active_companies = db.query(Company).filter(Company.is_active == True).count()
        ACTIVE_COMPANIES.set(active_companies)
        
        # 系統用戶數
        system_users = db.query(SystemUser).filter(SystemUser.is_active == True).count()
        TOTAL_USERS.labels(user_type='system').set(system_users)
        
        # 租戶用戶數
        tenant_users = db.query(TenantUser).filter(TenantUser.is_active == True).count()
        TOTAL_USERS.labels(user_type='tenant').set(tenant_users)
        
        db.close()
        
    except Exception as e:
        print(f"Error updating business metrics: {e}")

@router.get("")
async def get_metrics():
    """
    Prometheus metrics 端點
    返回 Prometheus 格式的監控數據
    """
    # 更新指標
    update_system_metrics()
    update_business_metrics()
    
    # 生成 Prometheus 格式數據
    metrics_data = generate_latest()
    
    return Response(
        content=metrics_data,
        media_type=CONTENT_TYPE_LATEST
    )

@router.get("/health")
async def health_check():
    """
    健康檢查端點
    提供詳細的系統狀態資訊
    """
    try:
        # 檢查資料庫連接
        db = next(get_db())
        db.execute(text("SELECT 1"))
        db_status = "healthy"
        db.close()
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # 獲取系統資源
    cpu_percent = psutil.cpu_percent(interval=0.1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "database": {
            "status": db_status
        },
        "system": {
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": round(memory.available / (1024**3), 2),
            "disk_percent": round((disk.used / disk.total) * 100, 2),
            "disk_free_gb": round(disk.free / (1024**3), 2)
        }
    }

@router.get("/stats")
async def get_stats():
    """
    系統統計資訊
    提供業務相關的統計數據
    """
    try:
        db = next(get_db())
        
        stats = {
            "companies": {
                "total": db.query(Company).count(),
                "active": db.query(Company).filter(Company.is_active == True).count(),
                "inactive": db.query(Company).filter(Company.is_active == False).count(),
            },
            "users": {
                "system_users": db.query(SystemUser).filter(SystemUser.is_active == True).count(),
                "tenant_users": db.query(TenantUser).filter(TenantUser.is_active == True).count(),
            }
        }
        
        db.close()
        return stats
        
    except Exception as e:
        return {"error": str(e)}

# 中間件：記錄請求指標
def record_request_metrics(request, response, process_time: float):
    """記錄 HTTP 請求指標"""
    method = request.method
    endpoint = request.url.path
    status_code = str(response.status_code)
    
    REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=status_code).inc()
    REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(process_time)

# 記錄 RAG 查詢指標
def record_rag_metrics(company_id: int, response_time: float, status: str = "success"):
    """記錄 RAG 查詢指標"""
    RAG_QUERY_COUNT.labels(company_id=str(company_id), status=status).inc()
    RAG_RESPONSE_TIME.labels(company_id=str(company_id)).observe(response_time)