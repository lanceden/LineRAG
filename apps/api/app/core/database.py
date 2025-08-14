"""
資料庫配置和連接管理
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

# 確保載入 .env 檔案
load_dotenv()

# 建立基底類別
Base = declarative_base()

# 資料庫設定
DATABASE_URL = os.getenv("DATABASE_URL")


def create_database_if_not_exists():
    """自動建立資料庫（如果不存在）"""
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable not set")

    # 解析資料庫URL
    from urllib.parse import urlparse

    parsed = urlparse(DATABASE_URL)

    db_name = parsed.path[1:]  # 移除開頭的 '/'

    # 建立連接到postgres預設資料庫的URL
    postgres_url = DATABASE_URL.replace(f"/{db_name}", "/postgres")

    try:
        # 嘗試連接到目標資料庫
        test_engine = create_engine(DATABASE_URL)
        with test_engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"資料庫 '{db_name}' 已存在")
        return
    except OperationalError:
        print(f"資料庫 '{db_name}' 不存在，正在建立...")

    try:
        # 連接到postgres預設資料庫來建立新資料庫
        conn = psycopg2.connect(postgres_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        with conn.cursor() as cursor:
            cursor.execute(f'CREATE DATABASE "{db_name}";')

        conn.close()
        print(f"成功建立資料庫 '{db_name}'")

    except psycopg2.errors.DuplicateDatabase:
        print(f"資料庫 '{db_name}' 已存在")
    except Exception as e:
        print(f"建立資料庫失敗: {e}")
        raise


# 自動建立資料庫
create_database_if_not_exists()

# 建立引擎
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,  # 設為 True 可看到 SQL 查詢
)

# 建立會話工廠
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """取得資料庫會話"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """建立所有資料表"""
    from app.models import Company, DocumentMetadata, AuditLog
    from app.models.tenant_user import TenantUser
    from app.models.system_user import SystemUser

    Base.metadata.create_all(bind=engine)


def drop_tables():
    """刪除所有資料表"""
    Base.metadata.drop_all(bind=engine)
