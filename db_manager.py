#!/usr/bin/env python3
"""
Alembic 資料庫遷移輔助腳本
簡化常用的資料庫管理操作
"""

import os
import sys
import subprocess
from pathlib import Path


def run_command(cmd, description):
    """執行命令並顯示結果"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, cwd="apps/api"
        )
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout.strip():
                print(result.stdout)
        else:
            print(f"❌ {description} 失敗")
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ 執行錯誤: {e}")
        return False
    return True


def init_alembic():
    """初始化 Alembic"""
    api_dir = Path("apps/api")
    if (api_dir / "alembic").exists():
        print("⚠️  Alembic 已經初始化")
        return

    if not run_command("alembic init alembic", "初始化 Alembic"):
        return

    # 自動配置 alembic.ini - 使用環境變數
    alembic_ini = api_dir / "alembic.ini"
    if alembic_ini.exists():
        from dotenv import load_dotenv
        load_dotenv()
        
        content = alembic_ini.read_text(encoding="utf-8")
        database_url = os.getenv("DATABASE_URL", "postgresql://postgres:!QAZ2wsx@localhost:5432/linerag")
        content = content.replace(
            "sqlalchemy.url = driver://user:pass@localhost/dbname",
            f"sqlalchemy.url = {database_url}",
        )
        alembic_ini.write_text(content, encoding="utf-8")
        print("✅ 已配置 alembic.ini (使用環境變數)")

    # 自動配置 env.py
    env_py = api_dir / "alembic" / "env.py"
    if env_py.exists():
        env_content = """# Alembic 環境配置
import os
import sys
from pathlib import Path

# 添加應用路徑
sys.path.append(str(Path(__file__).parent.parent))

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 導入模型
from app.core.database import Base
from app.models.company import Company
from app.models.tenant_user import TenantUser
from app.models.system_user import SystemUser
from app.models.document import DocumentMetadata

# Alembic Config 對象
config = context.config

# 設置日誌
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 設置元數據
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
"""
        env_py.write_text(env_content, encoding="utf-8")
        print("✅ 已配置 env.py")


def create_migration(message):
    """創建新遷移"""
    cmd = f'alembic revision --autogenerate -m "{message}"'
    return run_command(cmd, f"創建遷移: {message}")


def upgrade_database():
    """升級資料庫到最新版本"""
    return run_command("alembic upgrade head", "升級資料庫到最新版本")


def downgrade_database(revision="-1"):
    """降級資料庫"""
    cmd = f"alembic downgrade {revision}"
    return run_command(cmd, f"降級資料庫到 {revision}")


def show_history():
    """顯示遷移歷史"""
    return run_command("alembic history", "顯示遷移歷史")


def show_current():
    """顯示當前版本"""
    return run_command("alembic current", "顯示當前版本")


def stamp_head():
    """標記當前狀態為最新版本"""
    return run_command("alembic stamp head", "標記當前狀態為最新版本")


def main():
    """主菜單"""
    print("🗃️  Python 資料庫管理工具")
    print("=" * 40)

    while True:
        print("\n請選擇操作：")
        print("1. 初始化 Alembic")
        print("2. 創建新遷移")
        print("3. 升級資料庫")
        print("4. 降級資料庫")
        print("5. 顯示遷移歷史")
        print("6. 顯示當前版本")
        print("7. 標記為最新版本")
        print("8. 初始化資料庫數據")
        print("0. 退出")

        choice = input("\n輸入選項 (0-8): ").strip()

        if choice == "0":
            print("👋 再見！")
            break
        elif choice == "1":
            init_alembic()
        elif choice == "2":
            message = input("請輸入遷移描述: ").strip()
            if message:
                create_migration(message)
            else:
                print("❌ 遷移描述不能為空")
        elif choice == "3":
            upgrade_database()
        elif choice == "4":
            revision = input("輸入目標版本 (預設 -1): ").strip() or "-1"
            downgrade_database(revision)
        elif choice == "5":
            show_history()
        elif choice == "6":
            show_current()
        elif choice == "7":
            stamp_head()
        elif choice == "8":
            run_command("python init_db.py", "初始化資料庫數據")
        else:
            print("❌ 無效選項，請重新選擇")


if __name__ == "__main__":
    # 檢查是否在正確的目錄
    if not Path("apps/api").exists():
        print("❌ 請在專案根目錄執行此腳本")
        sys.exit(1)

    main()
