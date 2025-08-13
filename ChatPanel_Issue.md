# ChatPanel 會話管理與身份認證整合方案

## 📋 問題描述

官網聊天框（ChatPanel）需要實現會話持久化功能，讓用戶關閉視窗後重新開啟時能恢復之前的對話。同時需要處理匿名用戶登入後的會話合併問題。

## 🎯 核心需求

1. **會話持久化**：用戶關閉/重新開啟網頁時對話能夠恢復
2. **身份認證整合**：匿名對話在用戶登入後能自動合併到個人帳號
3. **輪數限制**：方案B支援3輪、方案A支援6-8輪對話記憶
4. **資料同步**：前端localStorage與後端資料庫的雙向同步

## 🛠️ 技術實作方案

### 1. 會話管理架構

#### 前端實作（ChatPanel.tsx）

```javascript
import { useState, useEffect } from 'react'

interface ChatSession {
  sessionId: string
  userId?: string
  messages: Message[]
  createdAt: number
  updatedAt: number
}

export default function ChatPanel() {
  const [sessionId, setSessionId] = useState<string>('')
  const [currentUserId, setCurrentUserId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])

  // 頁面載入時恢復會話
  useEffect(() => {
    initializeSession()
    checkLoginStatus()
    setupLoginListener()
  }, [])

  // 初始化會話
  const initializeSession = async () => {
    const savedSessionId = localStorage.getItem('chat_session_id')
    const savedMessages = localStorage.getItem('chat_messages')
    const sessionTimestamp = localStorage.getItem('chat_session_timestamp')

    // 檢查會話是否過期（24小時）
    const isExpired = sessionTimestamp && 
      (Date.now() - parseInt(sessionTimestamp)) > 24 * 60 * 60 * 1000

    if (savedSessionId && savedMessages && !isExpired) {
      // 恢復舊會話
      setSessionId(savedSessionId)
      setMessages(JSON.parse(savedMessages))
      
      // 從伺服器同步最新對話（可選）
      await syncMessagesFromServer(savedSessionId)
    } else {
      // 建立新會話
      const newSessionId = generateSessionId()
      setSessionId(newSessionId)
      localStorage.setItem('chat_session_id', newSessionId)
      localStorage.setItem('chat_session_timestamp', Date.now().toString())
    }
  }

  // 檢查登入狀態
  const checkLoginStatus = async () => {
    try {
      const response = await fetch('/api/auth/status', {
        credentials: 'include'
      })
      const { isLoggedIn, userId } = await response.json()
      
      if (isLoggedIn) {
        setCurrentUserId(userId)
        
        // 如果有匿名會話需要合併
        if (sessionId && !currentUserId) {
          await mergeAnonymousSession(sessionId, userId)
        }
      }
    } catch (error) {
      console.error('檢查登入狀態失敗:', error)
    }
  }

  // 監聽登入事件
  const setupLoginListener = () => {
    window.addEventListener('user-login', async (event: CustomEvent) => {
      const { userId } = event.detail
      setCurrentUserId(userId)
      await mergeAnonymousSession(sessionId, userId)
    })

    window.addEventListener('user-logout', () => {
      setCurrentUserId(null)
      // 可選：清除會話或轉為匿名模式
    })
  }

  // 合併匿名會話到用戶帳號
  const mergeAnonymousSession = async (sessionId: string, userId: string) => {
    try {
      await fetch('/api/sessions/merge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sessionId, userId }),
        credentials: 'include'
      })
      
      // 更新localStorage中的用戶關聯
      localStorage.setItem('chat_user_id', userId)
    } catch (error) {
      console.error('合併會話失敗:', error)
    }
  }

  // 發送訊息（更新版本）
  const sendMessage = async (text: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      parts: [{ type: "text", text }],
    }

    setMessages(prev => [...prev, userMessage])

    try {
      const response = await fetch("/api/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          sessionId,
          userId: currentUserId,
          maxRounds: getMaxRounds() // 根據方案限制輪數
        }),
        credentials: 'include'
      })

      // ... AI 回覆處理邏輯
      
      // 更新localStorage
      updateLocalStorage()
      
    } catch (error) {
      console.error("發送訊息失敗:", error)
    }
  }

  // 根據方案決定最大輪數
  const getMaxRounds = () => {
    // 這裡可以從用戶訂閱方案或配置中取得
    return currentUserId ? 8 : 3 // 假設登入用戶為方案A，匿名為方案B
  }

  // 更新本地儲存
  const updateLocalStorage = () => {
    localStorage.setItem('chat_messages', JSON.stringify(messages))
    localStorage.setItem('chat_session_timestamp', Date.now().toString())
  }

  // 從伺服器同步訊息
  const syncMessagesFromServer = async (sessionId: string) => {
    try {
      const response = await fetch(`/api/sessions/${sessionId}/messages`, {
        credentials: 'include'
      })
      const serverMessages = await response.json()
      
      // 合併本地和伺服器訊息（取較新的）
      if (serverMessages.length > messages.length) {
        setMessages(serverMessages)
        updateLocalStorage()
      }
    } catch (error) {
      console.error('同步訊息失敗:', error)
    }
  }

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9)
  }

  // ... 其餘組件邏輯
}
```

### 2. 後端API實作（FastAPI）

```python
from fastapi import FastAPI, HTTPException, Request, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid

app = FastAPI()

class ChatMessage(BaseModel):
    session_id: str
    user_id: Optional[str] = None
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    max_rounds: int = 3

class SessionManager:
    @staticmethod
    async def save_message(session_id: str, role: str, content: str, user_id: str = None):
        """保存單條訊息到資料庫"""
        message = ChatMessage(
            id=str(uuid.uuid4()),
            session_id=session_id,
            user_id=user_id,
            role=role,
            content=content,
            timestamp=datetime.utcnow()
        )
        
        db.add(message)
        await db.commit()
        
        # 限制對話輪數
        await SessionManager.trim_conversation(session_id, user_id)
    
    @staticmethod
    async def trim_conversation(session_id: str, user_id: str = None):
        """限制對話輪數，保留最近的N輪對話"""
        # 根據用戶方案決定最大輪數
        max_rounds = await get_user_max_rounds(user_id) if user_id else 3
        
        messages = await db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.timestamp.desc()).all()
        
        if len(messages) > max_rounds * 2:  # 每輪包含 user + assistant
            # 刪除最舊的訊息
            excess_messages = messages[max_rounds * 2:]
            for msg in excess_messages:
                await db.delete(msg)
            await db.commit()
    
    @staticmethod
    async def get_conversation_history(session_id: str, user_id: str = None):
        """取得會話歷史"""
        query = db.query(ChatMessage).filter(ChatMessage.session_id == session_id)
        
        if user_id:
            query = query.filter(ChatMessage.user_id == user_id)
            
        messages = query.order_by(ChatMessage.timestamp.asc()).all()
        return messages
    
    @staticmethod
    async def merge_anonymous_session(session_id: str, user_id: str):
        """合併匿名會話到用戶帳號"""
        # 更新所有該session的訊息，關聯到user_id
        await db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id,
            ChatMessage.user_id.is_(None)
        ).update({"user_id": user_id})
        
        await db.commit()
        
        # 應用用戶的輪數限制
        await SessionManager.trim_conversation(session_id, user_id)

# API 端點
@app.post("/api/ask")
async def chat_completion(request: ChatRequest):
    """AI對話端點"""
    
    # 1. 保存用戶訊息
    await SessionManager.save_message(
        session_id=request.session_id,
        role="user",
        content=request.message,
        user_id=request.user_id
    )
    
    # 2. 取得對話歷史
    history = await SessionManager.get_conversation_history(
        request.session_id, 
        request.user_id
    )
    
    # 3. AI 推理
    ai_response = await llm_inference(history, request.message)
    
    # 4. 保存AI回覆
    await SessionManager.save_message(
        session_id=request.session_id,
        role="assistant", 
        content=ai_response,
        user_id=request.user_id
    )
    
    return {"response": ai_response}

@app.get("/api/sessions/{session_id}/messages")
async def get_session_messages(session_id: str, current_user = Depends(get_current_user_optional)):
    """取得會話訊息列表"""
    user_id = current_user.id if current_user else None
    messages = await SessionManager.get_conversation_history(session_id, user_id)
    return messages

@app.post("/api/sessions/merge")
async def merge_session(request: MergeSessionRequest, current_user = Depends(get_current_user)):
    """合併匿名會話到用戶帳號"""
    await SessionManager.merge_anonymous_session(
        session_id=request.session_id,
        user_id=current_user.id
    )
    return {"success": True}

@app.get("/api/auth/status")
async def auth_status(current_user = Depends(get_current_user_optional)):
    """檢查登入狀態"""
    if current_user:
        return {
            "isLoggedIn": True,
            "userId": current_user.id,
            "maxRounds": await get_user_max_rounds(current_user.id)
        }
    return {"isLoggedIn": False}

async def get_user_max_rounds(user_id: str) -> int:
    """根據用戶訂閱方案返回最大對話輪數"""
    # 這裡實作訂閱方案邏輯
    user_plan = await get_user_subscription_plan(user_id)
    return 8 if user_plan == "enterprise" else 3
```

### 3. 資料庫設計

```sql
-- 對話訊息表
CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100) NOT NULL,
    user_id UUID REFERENCES users(id),
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_timestamp (timestamp)
);

-- 會話表（可選）
CREATE TABLE chat_sessions (
    session_id VARCHAR(100) PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_user_id (user_id),
    INDEX idx_expires_at (expires_at)
);
```

## 🔄 完整流程圖

### 匿名用戶對話流程
1. 用戶開啟聊天框
2. 系統生成 session_id
3. 對話儲存到 localStorage + 資料庫
4. 關閉/重新開啟 → 從 localStorage 恢復

### 登入用戶對話流程
1. 用戶登入成功
2. 觸發 'user-login' 事件
3. ChatPanel 檢測到登入
4. 調用 `/api/sessions/merge` 合併匿名會話
5. 後續對話關聯到 user_id

### 會話過期處理
1. 檢查 localStorage 時間戳
2. 超過24小時自動清除
3. 資料庫定期清理過期會話

## 🚀 部署注意事項

1. **隱私保護**：匿名會話資料定期清理
2. **效能優化**：對話歷史分頁載入
3. **錯誤處理**：網路中斷時的本地備份
4. **安全考量**：防止會話劫持和跨站攻擊

## 📊 監控指標

- 會話恢復成功率
- 匿名轉登入用戶轉換率  
- 平均會話時長
- 資料庫儲存空間使用情況

## 🎯 測試案例

1. **基本會話恢復**：關閉重開網頁，對話是否保持
2. **登入合併**：匿名對話後登入，會話是否合併
3. **輪數限制**：超過限制時舊對話是否正確清除
4. **跨裝置同步**：登入用戶在不同裝置的會話同步
5. **過期處理**：過期會話是否正確清理

---

這個方案提供了完整的會話管理和身份認證整合功能，確保用戶在不同狀態下都能獲得良好的對話體驗。