"""
JWT 認證中間件
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
import jwt

from app.core.database import SessionLocal
from app.core.auth import AuthService
from app.models.system_user import SystemUser

# 不需要認證的路徑
EXEMPT_PATHS = {
    "/api/",
    "/api/docs",
    "/api/docs/",
    "/api/openapi.json", 
    "/api/redoc",
    "/api/health",
    "/api/system-users/login",
    "/api/system-users/refresh",
    "/api/webhook",  # LINE webhook 有自己的驗證機制
    "/docs",  # 直接訪問 docs 的情況
    "/docs/",
    "/openapi.json",
    "/redoc",
}

# 不需要認證的路徑前綴
EXEMPT_PATH_PREFIXES = [
    "/api/docs",
    "/api/redoc",
    "/docs",
    "/redoc",
]


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """JWT 認證中間件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳過 OPTIONS 預檢請求（CORS）
        if request.method == "OPTIONS":
            return await call_next(request)
            
        # 檢查是否為免認證路徑
        if self._is_exempt_path(request.url.path):
            return await call_next(request)

        # 檢查 Authorization header
        auth_header = request.headers.get("authorization")
        if not auth_header:
            return self._unauthorized_response("Missing authorization header")

        # 解析 Bearer token
        try:
            scheme, token = auth_header.split()
            if scheme.lower() != "bearer":
                return self._unauthorized_response("Invalid authentication scheme")
        except ValueError:
            return self._unauthorized_response("Invalid authorization header format")

        # 驗證 JWT token
        try:
            payload = AuthService.verify_token(token)
            user_id = payload.get("user_id")
            
            if not user_id:
                return self._unauthorized_response("Invalid token payload")

            # 從資料庫驗證用戶
            db = SessionLocal()
            try:
                user = db.query(SystemUser).filter(
                    SystemUser.id == user_id,
                    SystemUser.is_active == True
                ).first()
                
                if not user:
                    return self._unauthorized_response("User not found or inactive")
                
                # 將用戶資訊加到 request state 中
                request.state.current_user = user
                
            finally:
                db.close()

        except jwt.ExpiredSignatureError:
            return self._unauthorized_response("Token has expired")
        except jwt.JWTError:
            return self._unauthorized_response("Invalid token")
        except Exception as e:
            return self._unauthorized_response(f"Authentication error: {str(e)}")

        # 繼續處理請求
        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """檢查路徑是否免認證"""
        # 完全匹配
        if path in EXEMPT_PATHS:
            return True
        
        # 前綴匹配
        for prefix in EXEMPT_PATH_PREFIXES:
            if path.startswith(prefix):
                return True
                
        return False

    def _unauthorized_response(self, detail: str) -> JSONResponse:
        """返回 401 錯誤響應"""
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": detail}
        )


def get_current_user_from_state(request: Request) -> SystemUser:
    """從 request state 獲取當前用戶"""
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not authenticated"
        )
    return user


def require_admin_permission(request: Request) -> SystemUser:
    """要求管理員權限"""
    user = get_current_user_from_state(request)
    if user.role not in ["admin", "super_admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permission required"
        )
    return user


def require_super_admin_permission(request: Request) -> SystemUser:
    """要求超級管理員權限"""
    user = get_current_user_from_state(request)
    if user.role != "super_admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin permission required"
        )
    return user


def check_company_access_permission(company_id: int, request: Request) -> SystemUser:
    """檢查用戶是否有權限訪問指定公司"""
    user = get_current_user_from_state(request)
    
    # 超級管理員可以訪問所有公司
    if user.role == "super_admin":
        return user
    
    # 檢查用戶是否有該公司的訪問權限
    accessible_company_ids = [company.id for company in user.accessible_companies]
    
    if company_id not in accessible_company_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"No permission to access company {company_id}"
        )
    
    return user