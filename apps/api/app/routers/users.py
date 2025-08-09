"""
用戶管理 API 路由
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends

from app.services.user_service import get_user_service, UserService
from app.schemas.user import (
    UserCreateRequest,
    UserRoleUpdateRequest,
    UserResponse,
    UserRoleResponse,
    PermissionCheckResponse,
    ApiResponse
)

router = APIRouter(prefix="/users", tags=["用戶管理"])

@router.post("/create", response_model=ApiResponse)
async def create_user(
    request: UserCreateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """建立新用戶"""
    success = await user_service.create_user(
        line_id=request.line_id,
        name=request.name,
        email=request.email,
        role=request.role,
        created_by="api"
    )
    
    if success:
        user_data = await user_service.get_user(request.line_id)
        user = UserResponse(**user_data) if user_data else None
        return ApiResponse(success=True, message="用戶建立成功", user=user)
    else:
        raise HTTPException(status_code=500, detail="建立用戶失敗")

@router.get("/role/{line_id}", response_model=UserRoleResponse)
async def get_user_role(
    line_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """取得用戶角色（供NextAuth使用）"""
    user = await user_service.get_user(line_id)
    
    if not user:
        # 自動註冊為客服角色
        await user_service.create_user(
            line_id=line_id,
            name="新用戶",
            role="cs",
            created_by="auto_register"
        )
        user = await user_service.get_user(line_id)
    
    return UserRoleResponse(
        line_id=line_id,
        role=user.get("role", "cs"),
        is_active=user.get("is_active", True),
        name=user.get("name", "")
    )

@router.get("/{line_id}", response_model=UserResponse)
async def get_user_info(
    line_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """取得用戶詳細資訊"""
    user = await user_service.get_user(line_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="用戶不存在")
    
    return UserResponse(**user)

@router.put("/{line_id}/role", response_model=ApiResponse)
async def update_user_role(
    line_id: str,
    request: UserRoleUpdateRequest,
    user_service: UserService = Depends(get_user_service)
):
    """更新用戶角色"""
    if request.role not in ["admin", "cs"]:
        raise HTTPException(status_code=400, detail="無效的角色")
    
    success = await user_service.update_user_role(
        line_id=line_id,
        new_role=request.role,
        updated_by="api"
    )
    
    if success:
        user_data = await user_service.get_user(line_id)
        user = UserResponse(**user_data) if user_data else None
        return ApiResponse(success=True, message="角色更新成功", user=user)
    else:
        raise HTTPException(status_code=404, detail="用戶不存在或更新失敗")

@router.delete("/{line_id}", response_model=ApiResponse)
async def deactivate_user(
    line_id: str,
    user_service: UserService = Depends(get_user_service)
):
    """停用用戶"""
    success = await user_service.deactivate_user(line_id)
    
    if success:
        return ApiResponse(success=True, message="用戶已停用")
    else:
        raise HTTPException(status_code=404, detail="用戶不存在或停用失敗")

@router.get("/", response_model=List[UserResponse])
async def list_all_users(
    role: Optional[str] = None,
    user_service: UserService = Depends(get_user_service)
):
    """列出所有用戶"""
    if role:
        users = await user_service.get_users_by_role(role)
    else:
        users = await user_service.get_all_users()
    
    return [UserResponse(**user) for user in users]

@router.get("/check/{line_id}/permission", response_model=PermissionCheckResponse)
async def check_permission(
    line_id: str,
    required_role: str = "cs",
    user_service: UserService = Depends(get_user_service)
):
    """檢查用戶權限"""
    has_permission = await user_service.has_permission(line_id, required_role)
    
    return PermissionCheckResponse(
        line_id=line_id,
        required_role=required_role,
        has_permission=has_permission
    )