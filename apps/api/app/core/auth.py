"""
JWT 認證服務
只處理基本的認證功能：密碼驗證、JWT 生成/驗證、密碼雜湊
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from jwt import PyJWTError, ExpiredSignatureError
from passlib.context import CryptContext
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.system_user import SystemUser

# JWT 設定
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

# 密碼加密
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def authenticate_user(
    db: Session, email_or_username: str, password: str
) -> Optional[SystemUser]:
    """驗證用戶登入 - 支援 email 或 username 登入"""
    # 先嘗試用 email 查詢，再用 username 查詢
    user = db.query(SystemUser).filter(SystemUser.email == email_or_username).first()
    if not user:
        user = db.query(SystemUser).filter(SystemUser.username == email_or_username).first()
    if not user:
        return None

    if not AuthService.verify_password(password, user.password_hash):
        return None

    if not user.is_active:
        return None

    return user


class AuthService:
    """認證服務 - 專注於 JWT 和密碼處理"""

    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """創建訪問令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """創建刷新令牌"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """驗證 JWT token - 中間件使用"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token has expired"
            )
        except PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate token",
            )

    @staticmethod
    def get_password_hash(password: str) -> str:
        """生成密碼雜湊 - 創建用戶時使用"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證密碼 - 登入時使用"""
        return pwd_context.verify(plain_password, hashed_password)
