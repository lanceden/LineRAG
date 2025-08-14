"""
資料庫初始化腳本
用於建立初始的公司和管理員帳戶
"""

import asyncio
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, create_tables
from app.models.company import Company
from app.models.tenant_user import TenantUser
from app.models.system_user import SystemUser
from datetime import datetime
from app.core.auth import AuthService


async def init_database():
    """初始化資料庫"""

    # 建立資料表
    print("Creating database tables...")
    create_tables()
    print("Database tables created successfully")

    # 建立資料庫會話
    db = SessionLocal()

    try:
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
                role="super_admin",
                created_at=datetime.utcnow(),
            )
            db.add(admin_user)
            db.commit()

            # 給系統管理員所有公司的權限
            for company in companies:
                admin_user.accessible_companies.append(company)

            db.commit()
            print(f"   Created system admin: {admin_username}")
        else:
            print(f"   System admin already exists: {admin_username}")

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


if __name__ == "__main__":
    asyncio.run(init_database())
