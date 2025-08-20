"""
公司管理 API 路由
權限檢查由 PermissionMiddleware 自動處理
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.middleware import get_current_user
from app.core.exceptions import ValidationError
from app.models.system_user import SystemUser
from app.schemas.company import (
    Company as CompanySchema,
    CompanyCreate,
    CompanyUpdate,
    CompanyListResponse,
    CompanyStats,
    CompanyUserListResponse,
    CompanyUserCreate,
    BatchOperationRequest,
    BatchOperationResponse,
    ApiResponse,
)
from app.services.company_service import CompanyService

router = APIRouter(prefix="/companies", tags=["公司管理"])


@router.get("/", response_model=CompanyListResponse)
async def get_companies(
    page: int = Query(1, ge=1, description="頁碼"),
    limit: int = Query(20, ge=1, le=100, description="每頁數量"),
    search: Optional[str] = Query(None, description="搜尋關鍵字"),
    is_active: Optional[bool] = Query(None, description="是否啟用"),
    sort_by: str = Query("created_at", description="排序欄位"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="排序方向"),
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取公司列表 - 需要 company.view 權限"""
    companies = CompanyService.get_companies(
        db=db,
        page=page,
        limit=limit,
        search=search,
        is_active=is_active,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return companies


@router.get("/{company_id}", response_model=CompanySchema)
async def get_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取單一公司資訊 - 需要 company.view 權限"""
    company = CompanyService.get_company(db, company_id)
    return company


@router.post("/", response_model=CompanySchema)
async def create_company(
    company_data: CompanyCreate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """創建新公司 - 需要 company.create 權限"""
    try:
        company = CompanyService.create_company(db, company_data)
        return company
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{company_id}", response_model=CompanySchema)
async def update_company(
    company_id: int,
    company_data: CompanyUpdate,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """更新公司資訊 - 需要 company.edit 權限"""
    try:
        company = CompanyService.update_company(db, company_id, company_data)
        if not company:
            raise HTTPException(status_code=404, detail="公司不存在")
        return company
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{company_id}")
async def delete_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """刪除公司 - 需要 company.delete 權限"""
    success = CompanyService.delete_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="公司不存在")
    return {"message": "公司已刪除"}


@router.get("/{company_id}/stats", response_model=CompanyStats)
async def get_company_stats(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """獲取公司統計資訊 - 需要 company.view 權限"""
    stats = CompanyService.get_company_stats(db, company_id)
    if not stats:
        raise HTTPException(status_code=404, detail="公司不存在")
    return stats


@router.post("/{company_id}/activate")
async def activate_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """啟用公司 - 需要 company.edit 權限"""
    success = CompanyService.activate_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="公司不存在")
    return {"message": "公司已啟用"}


@router.post("/{company_id}/deactivate")
async def deactivate_company(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """停用公司 - 需要 company.edit 權限"""
    success = CompanyService.deactivate_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="公司不存在")
    return {"message": "公司已停用"}


@router.post("/batch", response_model=BatchOperationResponse)
async def batch_operations(
    request: BatchOperationRequest,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """批次操作公司 - 需要 company.edit 權限"""
    try:
        result = CompanyService.batch_operation(db, request)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{company_id}/line-settings", response_model=CompanySchema)
async def update_line_settings(
    company_id: int,
    settings: dict,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """更新公司 LINE 設定 - 需要 company.edit 權限"""
    try:
        company = CompanyService.update_line_settings(
            db=db,
            company_id=company_id,
            channel_token=settings.get("line_channel_token", ""),
            channel_secret=settings.get("line_channel_secret", ""),
            bot_enabled=settings.get("line_bot_enabled", True),
        )
        return company
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{company_id}/line-settings/test")
async def test_line_connection(
    company_id: int,
    db: Session = Depends(get_db),
    current_user: SystemUser = Depends(get_current_user),
):
    """測試 LINE 連接 - 需要 company.view 權限"""
    import httpx
    
    try:
        company = CompanyService.get_company(db, company_id)
        if not company.line_channel_token or not company.line_channel_secret:
            raise HTTPException(status_code=400, detail="LINE 設定不完整")

        # 測試 LINE Messaging API 連接
        async with httpx.AsyncClient() as client:
            # 使用 LINE Bot Info API 來測試連接
            response = await client.get(
                "https://api.line.me/v2/bot/info",
                headers={
                    "Authorization": f"Bearer {company.line_channel_token}",
                    "Content-Type": "application/json"
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                bot_info = response.json()
                return {
                    "success": True, 
                    "message": "LINE Bot 連接測試成功",
                    "bot_info": {
                        "display_name": bot_info.get("displayName", ""),
                        "user_id": bot_info.get("userId", ""),
                        "basic_id": bot_info.get("basicId", "")
                    }
                }
            elif response.status_code == 401:
                return {"success": False, "message": "Channel Access Token 無效"}
            else:
                return {"success": False, "message": f"LINE API 回應錯誤: {response.status_code}"}
                
    except httpx.TimeoutException:
        return {"success": False, "message": "連接超時，請檢查網路連接"}
    except Exception as e:
        return {"success": False, "message": f"連接測試失敗: {str(e)}"}
