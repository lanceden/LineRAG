"""
資料庫初始化腳本
用於建立初始的公司和管理員帳戶
"""

import asyncio
import os
from typing import List
from dotenv import load_dotenv

# 載入環境變數
load_dotenv("../../.env")
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.company import Company
from app.models.tenant_user import TenantUser
from app.models.system_user import SystemUser
from app.models.permission import Permission, UserPermission
from datetime import datetime
from app.core.auth import AuthService
from app.services.permission_service import PermissionService


async def init_database():
    """初始化資料庫"""

    # 建立資料表
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully")

    # 建立資料庫會話
    db = SessionLocal()

    try:
        # 清除所有現有資料（重新初始化）
        print("Clearing existing data...")
        db.query(UserPermission).delete()
        db.query(Permission).delete()
        db.query(SystemUser).delete()
        db.query(Company).delete()
        # 如果有其他相關表也在這裡清除
        db.commit()
        print("Existing data cleared successfully")

        # 建立範例公司
        companies_data = [
            {
                "name": "示範公司 A",
                "code": "DEMO_A",
                "line_channel_token": "your_line_channel_token_a",
                "line_channel_secret": "your_line_channel_secret_a",
                "subscription_plan": "standard",
                "max_documents": 1000,
                "max_queries_per_month": 10000,
                "rag_working_dir": "./rag_storage/company_1",
            },
            {
                "name": "示範公司 B",
                "code": "DEMO_B",
                "line_channel_token": "your_line_channel_token_b",
                "line_channel_secret": "your_line_channel_secret_b",
                "subscription_plan": "premium",
                "max_documents": 5000,
                "max_queries_per_month": 50000,
                "rag_working_dir": "./rag_storage/company_2",
            },
        ]

        print("Creating demo companies...")
        companies = []
        for company_data in companies_data:
            # 檢查公司是否已存在
            existing = (
                db.query(Company).filter(Company.code == company_data["code"]).first()
            )
            if not existing:
                company = Company(**company_data)
                db.add(company)
                companies.append(company)
                print(f"   Created company: {company_data['name']}")
            else:
                companies.append(existing)
                print(f"   Company already exists: {company_data['name']}")

        db.commit()

        # 建立系統管理員（Web登入用）
        admin_username = os.getenv("ADMIN_USERNAME", "admin")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        admin_email = os.getenv("ADMIN_EMAIL", "admin@linerag.com")

        print("Creating system administrator...")
        existing_admin = (
            db.query(SystemUser).filter(SystemUser.username == admin_username).first()
        )

        if not existing_admin:
            # 使用 bcrypt 密碼雜湊
            password_hash = AuthService.get_password_hash(admin_password)

            admin_user = SystemUser(
                username=admin_username,
                email=admin_email,
                password_hash=password_hash,
                full_name="系統管理員",
                created_at=datetime.utcnow(),
            )
            db.add(admin_user)
            db.commit()
            db.refresh(admin_user)

            print(f"   Created system admin: {admin_username}")

            # 初始化權限系統
            print("Initializing permission system...")
            init_permission_system(db, admin_user.id, companies)

        else:
            print(f"   System admin already exists: {admin_username}")

            # 初始化權限系統（所有資料已清除，直接設置）
            print("Initializing permission system...")
            init_permission_system(db, existing_admin.id, companies)

        # 建立租戶用戶（LINE Bot用戶）
        admin_line_ids = os.getenv("ADMIN_LINE_IDS", "").split(",")
        admin_line_ids = [lid.strip() for lid in admin_line_ids if lid.strip()]

        if admin_line_ids:
            print("Creating tenant users...")
            for i, line_id in enumerate(admin_line_ids):
                # 為每個公司建立租戶用戶
                for company in companies:
                    existing_user = (
                        db.query(TenantUser)
                        .filter(
                            TenantUser.line_id == line_id,
                            TenantUser.company_id == company.id,
                        )
                        .first()
                    )

                    if not existing_user:
                        tenant_user = TenantUser(
                            company_id=company.id,
                            line_id=line_id,
                            name=f"租戶管理員 {i+1}",
                            role="admin",
                            created_at=datetime.utcnow(),
                        )
                        db.add(tenant_user)
                        print(f"   Created tenant user for {company.name}: {line_id}")
                    else:
                        print(
                            f"   Tenant user already exists for {company.name}: {line_id}"
                        )

            db.commit()
        else:
            print("No ADMIN_LINE_IDS set in environment variables")

        print("\nDatabase initialization completed successfully!")
        print("\nNext steps:")
        print("1. 更新各公司的 LINE Channel Token 和 Secret")
        print("2. 設定環境變數 ADMIN_LINE_IDS")
        print("3. 啟動 API 服務")

    except Exception as e:
        print(f"Error during database initialization: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def initialize_default_permissions(db: Session) -> List[Permission]:
    """初始化預設權限"""
    default_permissions = [
        # 公司管理
        ("company.view", "查看公司", "公司管理"),
        ("company.create", "建立公司", "公司管理"),
        ("company.edit", "編輯公司", "公司管理"),
        ("company.delete", "刪除公司", "公司管理"),
        ("company.stats", "公司統計", "公司管理"),
        # 用戶管理
        ("user.view", "查看用戶", "用戶管理"),
        ("user.create", "建立用戶", "用戶管理"),
        ("user.edit", "編輯用戶", "用戶管理"),
        ("user.delete", "刪除用戶", "用戶管理"),
        # 權限管理
        ("permission.view", "查看權限", "權限管理"),
        ("permission.edit", "編輯權限", "權限管理"),
        # 文檔管理
        ("document.view", "查看文檔", "文檔管理"),
        ("document.upload", "上傳文檔", "文檔管理"),
        ("document.edit", "編輯文檔", "文檔管理"),
        ("document.delete", "刪除文檔", "文檔管理"),
        ("document.stats", "文檔統計", "文檔管理"),
        # 對話管理
        ("chat.view", "查看對話", "對話管理"),
        ("chat.reply", "回覆對話", "對話管理"),
        ("chat.delete", "刪除對話", "對話管理"),
        ("chat.stats", "對話統計", "對話管理"),
        # 報表分析
        ("report.view", "查看報表", "報表分析"),
        ("report.export", "匯出報表", "報表分析"),
        ("report.custom", "自訂報表", "報表分析"),
        # 系統設定
        ("system.setting", "基本設定", "系統設定"),
        ("system.ai", "AI 設定", "系統設定"),
        ("system.monitor", "系統監控", "系統設定"),
    ]

    created_permissions = []
    for code, name, category in default_permissions:
        existing = db.query(Permission).filter(Permission.code == code).first()
        if not existing:
            permission = Permission(
                code=code, name=name, category=category, is_active=True
            )
            db.add(permission)
            created_permissions.append(permission)

    db.commit()
    return created_permissions


def init_permission_system(db: Session, admin_user_id: int, companies: list):
    """初始化權限系統"""
    print(" Initializing permission system...")

    # 1. 初始化預設權限
    created_permissions = initialize_default_permissions(db)
    print(f" Successfully initialized {len(created_permissions)} default permissions")

    # 2. 為超級管理員設置所有權限
    all_permissions = (
        db.query(Permission.code).filter(Permission.is_active == True).all()
    )
    permission_codes = [p.code for p in all_permissions]

    # 所有公司 ID + 全域存取權限 (-1)
    company_ids = [company.id for company in companies] + [-1]

    PermissionService.set_user_permissions(
        db=db,
        user_id=admin_user_id,
        permission_codes=permission_codes,
        company_ids=company_ids,
    )
    print(f" Set full permissions for admin user (ID: {admin_user_id})")
    print(f"   - Permissions: {len(permission_codes)} permissions")
    print(f"   - Company access: {len(company_ids)} companies + global access")


def show_permissions():
    """顯示所有權限"""
    db = SessionLocal()
    try:
        permissions = (
            db.query(Permission).order_by(Permission.category, Permission.code).all()
        )

        print("\n[INFO] All Permissions:")
        print("-" * 80)

        current_category = None
        for permission in permissions:
            if permission.category != current_category:
                current_category = permission.category
                print(f"\n[CATEGORY] {current_category}:")
                print("-" * 40)

            status = "[ACTIVE]" if permission.is_active else "[INACTIVE]"
            print(f"   {status} {permission.code:<30} {permission.name}")

        print(f"\n[TOTAL] {len(permissions)} permissions")

    finally:
        db.close()


def show_user_permissions(username: str = None):
    """顯示用戶權限"""
    db = SessionLocal()
    try:
        if username:
            users = db.query(SystemUser).filter(SystemUser.username == username).all()
        else:
            users = db.query(SystemUser).filter(SystemUser.is_active == True).all()

        if not users:
            print(f"[ERROR] User not found: {username}")
            return

        print(f"\n👥 User Permissions:")
        print("-" * 80)

        for user in users:
            user_permission = (
                db.query(UserPermission)
                .filter(UserPermission.user_id == user.id)
                .first()
            )

            print(f"\n👤 {user.username} ({user.full_name})")
            print("-" * 40)

            if user_permission:
                if user_permission.granted_permissions:
                    print("🔐 Functional Permissions:")
                    for perm in user_permission.granted_permissions:
                        print(f"    {perm}")

                if user_permission.accessible_companies:
                    print("🏢 Company Access:")
                    for company_id in user_permission.accessible_companies:
                        if company_id == -1:
                            print("    All companies")
                        else:
                            print(f"    Company ID: {company_id}")
            else:
                print("   ❌ No permissions")

    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Database initialization and management"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="init",
        choices=["init", "show-permissions", "show-users"],
        help="Command to execute",
    )
    parser.add_argument("--username", help="Show permissions for specific user")

    args = parser.parse_args()

    if args.command == "init":
        asyncio.run(init_database())
    elif args.command == "show-permissions":
        show_permissions()
    elif args.command == "show-users":
        show_user_permissions(args.username)
