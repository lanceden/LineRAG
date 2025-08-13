"""
Redis-based 用戶角色管理服務
"""
import os
import json
import time
from typing import Optional, Dict, List
import redis.asyncio as redis

# Load environment variables
from app.core import env

class UserService:
    def __init__(self):
        self.redis_client = None
    
    async def init(self):
        """初始化Redis連線"""
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True
        )
        
        # 初始化預設管理員
        await self._init_default_admin()
    
    async def _init_default_admin(self):
        """初始化預設管理員"""
        admin_line_ids = os.getenv("ADMIN_LINE_IDS", "").split(',')
        admin_line_ids = [lid.strip() for lid in admin_line_ids if lid.strip()]
        
        for line_id in admin_line_ids:
            if not await self.get_user(line_id):
                await self.create_user(
                    line_id=line_id,
                    name="系統管理員",
                    role="admin",
                    created_by="system"
                )
    
    async def create_user(self, line_id: str, name: str, role: str = "cs", 
                         email: Optional[str] = None, created_by: str = "system") -> bool:
        """建立用戶"""
        try:
            user_data = {
                "line_id": line_id,
                "name": name,
                "email": email or "",
                "role": role,  # admin | cs
                "is_active": "True",
                "created_at": str(int(time.time())),
                "updated_at": str(int(time.time())),
                "created_by": created_by
            }
            
            # 存到 Redis Hash
            await self.redis_client.hset(f"user:{line_id}", mapping=user_data)
            
            # 加入角色索引
            await self.redis_client.sadd(f"role:{role}", line_id)
            
            return True
        except Exception as e:
            print(f"Failed to create user: {e}")
            return False
    
    async def get_user(self, line_id: str) -> Optional[Dict]:
        """取得用戶資訊"""
        try:
            user_data = await self.redis_client.hgetall(f"user:{line_id}")
            if not user_data:
                return None
            
            # 轉換資料類型
            user_data["is_active"] = user_data.get("is_active", "True") == "True"
            user_data["created_at"] = int(user_data.get("created_at", 0))
            user_data["updated_at"] = int(user_data.get("updated_at", 0))
            
            return user_data
        except Exception as e:
            print(f"Failed to get user: {e}")
            return None
    
    async def update_user_role(self, line_id: str, new_role: str, updated_by: str) -> bool:
        """更新用戶角色"""
        try:
            user = await self.get_user(line_id)
            if not user:
                return False
            
            old_role = user.get("role")
            
            # 更新角色
            await self.redis_client.hset(f"user:{line_id}", mapping={
                "role": new_role,
                "updated_at": str(int(time.time()))
            })
            
            # 更新角色索引
            if old_role and old_role != new_role:
                await self.redis_client.srem(f"role:{old_role}", line_id)
            await self.redis_client.sadd(f"role:{new_role}", line_id)
            
            return True
        except Exception as e:
            print(f"Failed to update user role: {e}")
            return False
    
    async def deactivate_user(self, line_id: str) -> bool:
        """停用用戶"""
        try:
            await self.redis_client.hset(f"user:{line_id}", "is_active", "False")
            return True
        except Exception as e:
            print(f"Failed to deactivate user: {e}")
            return False
    
    async def get_users_by_role(self, role: str) -> List[Dict]:
        """取得特定角色的所有用戶"""
        try:
            line_ids = await self.redis_client.smembers(f"role:{role}")
            users = []
            
            for line_id in line_ids:
                user = await self.get_user(line_id)
                if user and user.get("is_active"):
                    users.append(user)
            
            return users
        except Exception as e:
            print(f"Failed to get users by role: {e}")
            return []
    
    async def get_all_users(self) -> List[Dict]:
        """取得所有用戶"""
        try:
            # 掃描所有用戶key
            keys = []
            async for key in self.redis_client.scan_iter(match="user:*"):
                keys.append(key)
            
            users = []
            for key in keys:
                line_id = key.replace("user:", "")
                user = await self.get_user(line_id)
                if user:
                    users.append(user)
            
            return users
        except Exception as e:
            print(f"Failed to get all users: {e}")
            return []
    
    async def has_permission(self, line_id: str, required_role: str = "cs") -> bool:
        """檢查用戶權限"""
        user = await self.get_user(line_id)
        if not user or not user.get("is_active"):
            return False
        
        user_role = user.get("role", "")
        
        if required_role == "cs":
            return user_role in ["admin", "cs"]
        elif required_role == "admin":
            return user_role == "admin"
        
        return False
    
    async def auto_register_user(self, line_id: str, name: str, email: str = "") -> Dict:
        """自動註冊新用戶（預設為cs角色）"""
        existing_user = await self.get_user(line_id)
        if existing_user:
            return existing_user
        
        # 建立新用戶，預設為客服角色
        success = await self.create_user(
            line_id=line_id,
            name=name,
            email=email,
            role="cs",
            created_by="auto_register"
        )
        
        if success:
            return await self.get_user(line_id)
        
        return {}


# 全域用戶服務實例
user_service = UserService()

async def get_user_service() -> UserService:
    """取得用戶服務實例"""
    if user_service.redis_client is None:
        await user_service.init()
    return user_service