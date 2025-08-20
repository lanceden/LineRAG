"""
權限檢查中間件
基於 PERMISSION_SYSTEM_DESIGN.md 設計
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sqlalchemy.orm import Session
from jwt import PyJWTError, ExpiredSignatureError
from typing import List
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.auth import AuthService
from app.models.system_user import SystemUser
from app.models.permission import UserPermission

# 不需要認證的路徑
EXEMPT_PATHS = {
    "/",  # 根路徑
    "/api/",
    "/api/docs",
    "/api/openapi.json",
    "/api/redoc",
    "/api/health",
    "/api/auth/login",
    "/api/auth/refresh",
    "/api/webhook",  # LINE webhook (標準路徑)
    "/webhook",  # LINE webhook (簡化路徑)
    "/docs",
    "/redoc",
}


class PermissionMiddleware(BaseHTTPMiddleware):
    """權限檢查中間件"""

    async def dispatch(self, request: Request, call_next) -> Response:
        # 跳過 OPTIONS 預檢請求
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

        # 驗證 JWT token 並載入用戶權限
        try:
            payload = AuthService.verify_token(token)
            user_id = payload.get("user_id")

            if not user_id:
                return self._unauthorized_response("Invalid token payload")

            # 檢查是否需要重新載入權限（每5分鐘重新查詢一次）
            current_time = datetime.now(timezone.utc).timestamp()
            last_permission_check = payload.get("last_permission_check", 0)
            permission_refresh_interval = 300  # 5分鐘

            if current_time - last_permission_check > permission_refresh_interval:
                # 需要重新查詢權限
                db = SessionLocal()
                try:
                    user = (
                        db.query(SystemUser)
                        .filter(SystemUser.id == user_id, SystemUser.is_active == True)
                        .first()
                    )

                    if not user:
                        return self._unauthorized_response("User not found or inactive")

                    # 載入用戶權限
                    user_permissions = self._load_user_permissions(db, user.id)
                    user_company_access = self._load_user_company_access(db, user.id)

                finally:
                    db.close()
            else:
                # 使用 JWT 中的權限資訊
                user_permissions = payload.get("permissions", [])
                user_company_access = payload.get("company_access", [])

                # 創建用戶物件（只包含基本資訊）
                user = type(
                    "SystemUser",
                    (),
                    {
                        "id": user_id,
                        "username": payload.get("username"),
                        "email": payload.get("email"),
                        "full_name": payload.get("full_name"),
                        "is_active": True,
                    },
                )()

            # 將用戶資訊和權限存到 request state
            request.state.current_user = user
            request.state.user_permissions = user_permissions
            request.state.user_company_access = user_company_access

            # 自動權限檢查 - 從用戶權限列表中查找匹配當前請求的權限
            if not self._check_route_permission(
                request.method, request.url.path, user_permissions
            ):
                return self._forbidden_response("權限不足，無法訪問此資源")

        except ExpiredSignatureError:
            return self._unauthorized_response("Token has expired")
        except PyJWTError:
            return self._unauthorized_response("Invalid token")
        except Exception as e:
            return self._unauthorized_response(f"Authentication error: {str(e)}")

        # 繼續處理請求
        return await call_next(request)

    def _is_exempt_path(self, path: str) -> bool:
        """檢查路徑是否免認證"""
        return (
            path in EXEMPT_PATHS
            or path.startswith("/docs")
            or path.startswith("/api/docs")
            or path.endswith("/webhook")  # 支援各種 webhook 路徑變體
            or "webhook" in path.lower()  # 更寬鬆的 webhook 路徑匹配
        )

    def _unauthorized_response(self, detail: str) -> JSONResponse:
        """返回 401 錯誤響應"""
        response = JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED, content={"detail": detail}
        )
        # 添加 CORS 頭
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    def _forbidden_response(self, detail: str) -> JSONResponse:
        """返回 403 錯誤響應"""
        response = JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN, content={"detail": detail}
        )
        # 添加 CORS 頭
        response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    def _check_route_permission(
        self, method: str, path: str, user_permissions: list
    ) -> bool:
        """檢查用戶權限列表中是否有匹配當前請求的權限"""
        # 移除 API 前綴
        if path.startswith("/api"):
            path = path[4:]

        # 檢查是否為公開路由
        if self._is_public_route(path):
            return True

        # 直接檢查用戶權限列表是否包含當前請求路徑的權限
        # 依照用戶要求：db.users.where(s => s.permissions.contains(req,path))
        return self._user_permissions_contains_path(user_permissions, method, path)

    def _user_permissions_contains_path(
        self, user_permissions: list, method: str, path: str
    ) -> bool:
        """檢查用戶權限是否包含當前請求路徑"""
        # 直接檢查用戶權限列表中是否有匹配當前路徑和方法的權限
        # 用戶權限格式如: company.view, company.create 等

        # 根據路徑和方法，檢查用戶權限列表
        for permission in user_permissions:
            if self._permission_matches_request(permission, method, path):
                return True

        return False

    def _permission_matches_request(
        self, permission: str, method: str, path: str
    ) -> bool:
        """檢查權限是否匹配當前請求"""
        # 解析權限格式: resource.action (如: company.view, user.create)
        parts = permission.split(".")
        if len(parts) != 2:
            return False

        resource, action = parts

        # 檢查路徑是否匹配資源
        if not self._path_matches_resource(path, resource):
            return False

        # 檢查方法是否匹配動作
        return self._method_matches_action(method, action)

    def _path_matches_resource(self, path: str, resource: str) -> bool:
        """檢查路徑是否匹配資源"""
        resource_path_map = {
            # company.*
            "company": "/companies",
            # user.*
            "user": "/system-users",
            # user.permission 特殊處理
            "permission": "/permissions",
            # report.*
            "report": "/analytics",
            # document.*
            "document": ["/ingest", "/documents"],
            # chat.*
            "chat": ["/ask", "/chat"],
            # system.*
            "system": ["/settings", "/monitor"],
        }

        expected_paths = resource_path_map.get(resource)
        if not expected_paths:
            return False

        if isinstance(expected_paths, list):
            return any(path.startswith(p) for p in expected_paths)
        else:
            return path.startswith(expected_paths)

    def _method_matches_action(self, method: str, action: str) -> bool:
        """檢查方法是否匹配動作"""
        action_method_map = {
            "view": ["GET"],
            "create": ["POST"],
            "edit": ["PUT", "PATCH"],
            "delete": ["DELETE"],
            "upload": ["POST"],
            "use": ["GET", "POST"],
            "import": ["POST"],
            "export": ["GET", "POST"],
            "process": ["POST"],
            "manage": ["GET", "POST", "PUT", "PATCH", "DELETE"],
            "analytics": ["GET"],
            "permission": ["GET", "POST", "PUT", "PATCH", "DELETE"],  # 權限管理
        }

        allowed_methods = action_method_map.get(action, [])
        return method in allowed_methods

    def _is_public_route(self, path: str) -> bool:
        """檢查是否為公開路由（不需要特定權限）"""
        public_routes = [
            "/profile",  # 用戶檔案
            "/health",  # 健康檢查
        ]

        for public_route in public_routes:
            if path.startswith(public_route):
                return True

        return False

    def _load_user_permissions(self, db: Session, user_id: int) -> List[str]:
        """載入用戶權限代碼列表"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if user_permission and user_permission.granted_permissions:
            return user_permission.granted_permissions
        return []

    def _load_user_company_access(self, db: Session, user_id: int) -> List[str]:
        """載入用戶公司存取權限列表"""
        user_permission = (
            db.query(UserPermission).filter(UserPermission.user_id == user_id).first()
        )

        if user_permission and user_permission.accessible_companies:
            return user_permission.accessible_companies
        return []


def get_current_user(request: Request) -> SystemUser:
    """從 request state 獲取當前用戶"""
    user = getattr(request.state, "current_user", None)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    return user


def has_permission(request: Request, permission_code: str) -> bool:
    """檢查用戶是否有指定權限"""
    user_permissions = getattr(request.state, "user_permissions", [])
    return permission_code in user_permissions


def can_access_company(request: Request, company_id: int) -> bool:
    """檢查用戶是否可存取指定公司"""
    user_company_access = getattr(request.state, "user_company_access", [])
    return "*" in user_company_access or str(company_id) in user_company_access
