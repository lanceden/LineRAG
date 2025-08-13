# AI 客服系統 Function Calling 實作指南

## 概述

本文檔說明如何在 AI 客服系統中實現 Function Calling 功能，以支援課程預約、查詢等外部 API 整合。核心概念是讓 LLM 自動判斷何時需要調用外部函數，並管理整個對話流程。

---

## 1. 架構設計

### 1.1 系統流程圖

```
用戶訊息 → 意圖識別 → 路由判斷 → 執行對應處理
                    ↓
            ┌─────────────────┐
            │  一般問答 (RAG)  │
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │  Function Call  │
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │   API 調用      │
            └─────────────────┘
                    ↓
            ┌─────────────────┐
            │   結果回傳      │
            └─────────────────┘
```

### 1.2 核心組件

1. **意圖識別器** - 判斷用戶意圖
2. **對話狀態管理** - 追蹤多輪對話
3. **函數註冊器** - 管理可用函數
4. **API 調用器** - 執行外部 API 調用
5. **回應生成器** - 生成自然語言回應

---

## 2. 實作方法

### 2.1 方法一：意圖識別 + 條件觸發

```python
from typing import Dict, List, Optional
import json
import re

class IntentDetector:
    """意圖識別器"""
    
    BOOKING_KEYWORDS = ['預約', '報名', '訂課', '安排', '課程時間', '預定']
    INQUIRY_KEYWORDS = ['查詢', '課程表', '時間表', '有什麼課']
    CANCEL_KEYWORDS = ['取消', '退課', '改時間']
    
    @classmethod
    def detect_intent(cls, message: str) -> Dict[str, str]:
        """檢測用戶意圖"""
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in cls.BOOKING_KEYWORDS):
            return {'intent': 'booking', 'confidence': 0.9}
        elif any(keyword in message_lower for keyword in cls.INQUIRY_KEYWORDS):
            return {'intent': 'inquiry', 'confidence': 0.8}
        elif any(keyword in message_lower for keyword in cls.CANCEL_KEYWORDS):
            return {'intent': 'cancel', 'confidence': 0.8}
        else:
            return {'intent': 'general_qa', 'confidence': 0.6}

def enhanced_qa_chain(question: str, user_id: str) -> str:
    """增強版問答鏈，支援 Function Calling"""
    
    # 1. 意圖識別
    intent_result = IntentDetector.detect_intent(question)
    intent = intent_result['intent']
    
    # 2. 根據意圖路由到不同處理器
    if intent == 'booking':
        return handle_booking_flow(question, user_id)
    elif intent == 'inquiry':
        return handle_inquiry_flow(question, user_id)
    elif intent == 'cancel':
        return handle_cancel_flow(question, user_id)
    else:
        # 一般 RAG 問答
        return handle_general_qa(question)
```

### 2.2 方法二：LLM 自動判斷（推薦）

```python
class LLMIntentDetector:
    """使用 LLM 進行意圖識別"""
    
    INTENT_PROMPT = """
你是一個智能助手，需要判斷用戶的意圖。請分析用戶訊息並回傳 JSON 格式結果。

可能的意圖類型：
- general_qa: 一般問答（關於健身知識、設施等）
- booking: 想要預約課程
- inquiry: 查詢課程時間表或可用課程
- cancel: 取消或修改預約
- other: 其他

請回傳格式：
{
    "intent": "意圖類型",
    "confidence": 0.0-1.0,
    "extracted_info": {
        "course_type": "提取的課程類型（如果有）",
        "date": "提取的日期（如果有）",
        "time": "提取的時間（如果有）"
    }
}

用戶訊息："{message}"
"""

    @classmethod
    def detect_intent_with_llm(cls, message: str) -> Dict:
        """使用 LLM 識別意圖"""
        prompt = cls.INTENT_PROMPT.format(message=message)
        
        try:
            response = call_vllm(prompt)
            # 清理回應，提取 JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {"intent": "general_qa", "confidence": 0.5}
        except Exception as e:
            print(f"意圖識別錯誤: {e}")
            return {"intent": "general_qa", "confidence": 0.5}
```

### 2.3 對話狀態管理

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class ConversationState(Enum):
    """對話狀態枚舉"""
    GENERAL = "general"
    BOOKING_START = "booking_start"
    BOOKING_COURSE_TYPE = "booking_course_type"
    BOOKING_DATE = "booking_date"
    BOOKING_TIME = "booking_time"
    BOOKING_CONFIRM = "booking_confirm"
    BOOKING_COMPLETE = "booking_complete"

@dataclass
class UserSession:
    """用戶會話數據"""
    user_id: str
    state: ConversationState = ConversationState.GENERAL
    booking_info: Dict = None
    last_message: str = ""
    context: Dict = None

class SessionManager:
    """會話管理器"""
    
    def __init__(self):
        self.sessions: Dict[str, UserSession] = {}
    
    def get_session(self, user_id: str) -> UserSession:
        """獲取或創建用戶會話"""
        if user_id not in self.sessions:
            self.sessions[user_id] = UserSession(user_id=user_id)
        return self.sessions[user_id]
    
    def update_session(self, user_id: str, **kwargs):
        """更新會話狀態"""
        session = self.get_session(user_id)
        for key, value in kwargs.items():
            setattr(session, key, value)
    
    def reset_session(self, user_id: str):
        """重置會話狀態"""
        if user_id in self.sessions:
            self.sessions[user_id].state = ConversationState.GENERAL
            self.sessions[user_id].booking_info = None

# 全局會話管理器
session_manager = SessionManager()
```

---

## 3. Function Calling 實作

### 3.1 函數註冊與管理

```python
from typing import Callable, Dict, Any
import inspect

class FunctionRegistry:
    """函數註冊器"""
    
    def __init__(self):
        self.functions: Dict[str, Callable] = {}
        self.descriptions: Dict[str, str] = {}
    
    def register(self, name: str, description: str):
        """註冊函數裝飾器"""
        def decorator(func: Callable):
            self.functions[name] = func
            self.descriptions[name] = description
            return func
        return decorator
    
    def get_function(self, name: str) -> Optional[Callable]:
        """獲取註冊的函數"""
        return self.functions.get(name)
    
    def list_functions(self) -> Dict[str, str]:
        """列出所有可用函數"""
        return self.descriptions.copy()

# 全局函數註冊器
function_registry = FunctionRegistry()

# 註冊預約相關函數
@function_registry.register("check_availability", "檢查課程可用時段")
def check_availability(course_type: str, date: str, time_slot: str = None) -> Dict[str, Any]:
    """
    檢查課程可用性
    
    Args:
        course_type: 課程類型（瑜伽、健身、游泳等）
        date: 日期 (YYYY-MM-DD 格式)
        time_slot: 時段（可選，如 "morning", "afternoon", "evening"）
    
    Returns:
        Dict: 包含可用時段的字典
    """
    # 模擬 API 調用
    available_slots = {
        "date": date,
        "course_type": course_type,
        "available_times": [
            {"time": "09:00", "instructor": "王教練", "spots_left": 5},
            {"time": "14:00", "instructor": "李教練", "spots_left": 3},
            {"time": "19:00", "instructor": "張教練", "spots_left": 8}
        ]
    }
    return available_slots

@function_registry.register("book_class", "預約課程")
def book_class(user_info: Dict, course_info: Dict) -> Dict[str, Any]:
    """
    預約課程
    
    Args:
        user_info: 用戶資訊 {"name": "姓名", "phone": "電話"}
        course_info: 課程資訊 {"type": "類型", "date": "日期", "time": "時間"}
    
    Returns:
        Dict: 預約結果
    """
    # 模擬預約 API 調用
    booking_id = f"BK{hash(str(user_info) + str(course_info)) % 10000:04d}"
    
    return {
        "success": True,
        "booking_id": booking_id,
        "message": f"預約成功！預約編號：{booking_id}",
        "details": {
            "user": user_info["name"],
            "course": course_info["type"],
            "date": course_info["date"],
            "time": course_info["time"],
            "instructor": "王教練"  # 這裡應該從實際 API 獲取
        }
    }

@function_registry.register("cancel_booking", "取消預約")
def cancel_booking(booking_id: str, user_phone: str) -> Dict[str, Any]:
    """
    取消預約
    
    Args:
        booking_id: 預約編號
        user_phone: 用戶電話（用於驗證）
    
    Returns:
        Dict: 取消結果
    """
    # 模擬取消預約 API
    return {
        "success": True,
        "message": f"預約 {booking_id} 已成功取消",
        "refund_info": "款項將在 3-5 個工作天內退回"
    }
```

### 3.2 智能函數調用

```python
class SmartFunctionCaller:
    """智能函數調用器"""
    
    FUNCTION_CALL_PROMPT = """
你是一個健身房的智能客服助理。根據用戶需求，判斷是否需要調用函數來完成任務。

可用函數：
{function_list}

用戶當前狀態：{user_state}
用戶訊息：{user_message}

如果需要調用函數，請回覆：
FUNCTION_CALL: function_name(param1="value1", param2="value2")

如果需要收集更多資訊，請友善地詢問用戶。
如果可以直接回答，請提供幫助。

請保持友善、專業的語氣。
"""

    def __init__(self, function_registry: FunctionRegistry):
        self.registry = function_registry
    
    def should_call_function(self, message: str, session: UserSession) -> tuple[bool, str]:
        """判斷是否需要調用函數"""
        
        function_list = "\n".join([
            f"- {name}: {desc}" 
            for name, desc in self.registry.list_functions().items()
        ])
        
        prompt = self.FUNCTION_CALL_PROMPT.format(
            function_list=function_list,
            user_state=session.state.value,
            user_message=message
        )
        
        response = call_vllm(prompt)
        
        if "FUNCTION_CALL:" in response:
            function_call = response.split("FUNCTION_CALL:")[1].strip()
            return True, function_call
        else:
            return False, response
    
    def parse_function_call(self, function_call_str: str) -> tuple[str, Dict]:
        """解析函數調用字串"""
        # 簡單的函數調用解析
        # 格式：function_name(param1="value1", param2="value2")
        
        import re
        match = re.match(r'(\w+)\((.*)\)', function_call_str)
        if not match:
            return None, {}
        
        function_name = match.group(1)
        params_str = match.group(2)
        
        # 解析參數
        params = {}
        if params_str.strip():
            # 這裡應該使用更安全的解析方法
            try:
                params_str = "{" + params_str + "}"
                params = eval(params_str)  # 注意：實際使用時應該用更安全的解析
            except:
                pass
        
        return function_name, params
    
    def execute_function(self, function_name: str, params: Dict) -> Any:
        """執行函數"""
        func = self.registry.get_function(function_name)
        if func:
            try:
                return func(**params)
            except Exception as e:
                return {"error": f"函數執行錯誤: {str(e)}"}
        else:
            return {"error": f"未找到函數: {function_name}"}

# 創建智能函數調用器
smart_caller = SmartFunctionCaller(function_registry)
```

---

## 4. 完整對話流程實作

### 4.1 主要對話處理器

```python
def handle_conversation(user_id: str, message: str) -> str:
    """
    主要對話處理函數
    
    Args:
        user_id: 用戶 ID
        message: 用戶訊息
    
    Returns:
        str: 系統回應
    """
    
    # 1. 獲取用戶會話
    session = session_manager.get_session(user_id)
    session.last_message = message
    
    # 2. 意圖識別
    intent_result = LLMIntentDetector.detect_intent_with_llm(message)
    intent = intent_result.get('intent', 'general_qa')
    
    # 3. 根據當前狀態和意圖處理
    if session.state == ConversationState.GENERAL:
        if intent == 'booking':
            return start_booking_flow(user_id, message, intent_result)
        elif intent == 'inquiry':
            return handle_course_inquiry(user_id, message, intent_result)
        elif intent == 'cancel':
            return handle_cancel_request(user_id, message)
        else:
            return handle_general_qa(message)
    
    elif session.state.value.startswith('booking'):
        return continue_booking_flow(user_id, message)
    
    else:
        # 其他狀態處理
        return handle_general_qa(message)

def start_booking_flow(user_id: str, message: str, intent_result: Dict) -> str:
    """開始預約流程"""
    
    session = session_manager.get_session(user_id)
    session.state = ConversationState.BOOKING_START
    session.booking_info = intent_result.get('extracted_info', {})
    
    # 檢查是否已有課程類型資訊
    if session.booking_info.get('course_type'):
        session.state = ConversationState.BOOKING_DATE
        return f"好的！您想預約{session.booking_info['course_type']}課程。請問您希望哪一天上課呢？（請提供具體日期，如：明天、2024-01-15）"
    else:
        session.state = ConversationState.BOOKING_COURSE_TYPE
        return "我來協助您預約課程！請問您想預約什麼類型的課程呢？我們有瑜伽、健身、游泳、舞蹈等課程。"

def continue_booking_flow(user_id: str, message: str) -> str:
    """繼續預約流程"""
    
    session = session_manager.get_session(user_id)
    
    if session.state == ConversationState.BOOKING_COURSE_TYPE:
        # 收集課程類型
        session.booking_info = session.booking_info or {}
        session.booking_info['course_type'] = extract_course_type(message)
        session.state = ConversationState.BOOKING_DATE
        return f"好的！您想預約{session.booking_info['course_type']}課程。請問您希望哪一天上課呢？"
    
    elif session.state == ConversationState.BOOKING_DATE:
        # 收集日期
        date = extract_date(message)
        if date:
            session.booking_info['date'] = date
            
            # 調用函數檢查可用時段
            should_call, result = smart_caller.should_call_function(
                f"檢查 {session.booking_info['course_type']} 課程在 {date} 的可用時段",
                session
            )
            
            if should_call:
                # 解析並執行函數調用
                func_name, params = smart_caller.parse_function_call(result)
                if func_name == "check_availability":
                    availability = smart_caller.execute_function(func_name, {
                        "course_type": session.booking_info['course_type'],
                        "date": date
                    })
                    
                    if availability and not availability.get('error'):
                        session.state = ConversationState.BOOKING_TIME
                        return format_availability_response(availability)
                    else:
                        return f"抱歉，查詢 {date} 的課程時段時發生錯誤。請稍後再試或選擇其他日期。"
            
            return "讓我為您查詢可用時段..."
        else:
            return "請提供一個有效的日期，例如：明天、後天、或具體日期如 2024-01-15"
    
    elif session.state == ConversationState.BOOKING_TIME:
        # 收集時間並確認預約
        time = extract_time(message)
        if time:
            session.booking_info['time'] = time
            session.state = ConversationState.BOOKING_CONFIRM
            
            return f"""
請確認您的預約資訊：
📅 課程：{session.booking_info['course_type']}
📅 日期：{session.booking_info['date']}
⏰ 時間：{session.booking_info['time']}

請提供您的姓名和電話以完成預約，或回覆「確認」來繼續。
"""
        else:
            return "請選擇一個可用的時段，例如：09:00、14:00 或 19:00"
    
    elif session.state == ConversationState.BOOKING_CONFIRM:
        # 收集用戶資訊並完成預約
        user_info = extract_user_info(message)
        if user_info or "確認" in message:
            
            if not user_info:
                user_info = {"name": "用戶", "phone": "未提供"}  # 實際應用中需要收集完整資訊
            
            # 調用預約函數
            booking_result = smart_caller.execute_function("book_class", {
                "user_info": user_info,
                "course_info": session.booking_info
            })
            
            session.state = ConversationState.BOOKING_COMPLETE
            
            if booking_result.get('success'):
                session_manager.reset_session(user_id)
                return f"""
🎉 {booking_result['message']}

預約詳情：
👤 姓名：{booking_result['details']['user']}
📚 課程：{booking_result['details']['course']}
📅 日期：{booking_result['details']['date']}
⏰ 時間：{booking_result['details']['time']}
👨‍🏫 教練：{booking_result['details']['instructor']}

請記住您的預約編號：{booking_result['booking_id']}
如需取消或修改，請提供此編號。

還有其他需要協助的嗎？
"""
            else:
                return f"預約失敗：{booking_result.get('message', '未知錯誤')}。請稍後再試或聯繫客服。"
        else:
            return "請提供您的姓名和電話，格式如：張三 0912345678"
    
    return "抱歉，我不太理解。讓我們重新開始預約流程。"

def format_availability_response(availability: Dict) -> str:
    """格式化可用時段回應"""
    if not availability.get('available_times'):
        return f"抱歉，{availability['date']} 沒有可用的 {availability['course_type']} 課程時段。請選擇其他日期。"
    
    response = f"✅ {availability['date']} 的 {availability['course_type']} 課程可用時段：\n\n"
    
    for i, slot in enumerate(availability['available_times'], 1):
        response += f"{i}. {slot['time']} - {slot['instructor']} （剩餘 {slot['spots_left']} 個名額）\n"
    
    response += "\n請選擇您想要的時段（直接回覆時間，如：09:00）"
    return response
```

### 4.2 輔助函數

```python
import re
from datetime import datetime, timedelta

def extract_course_type(message: str) -> str:
    """從訊息中提取課程類型"""
    course_mapping = {
        '瑜伽': ['瑜伽', 'yoga', '瑜珈'],
        '健身': ['健身', '重訓', '肌力', 'gym'],
        '游泳': ['游泳', 'swimming', '泳'],
        '舞蹈': ['舞蹈', 'dance', '跳舞'],
        '有氧': ['有氧', 'cardio', '心肺']
    }
    
    message_lower = message.lower()
    for course_type, keywords in course_mapping.items():
        if any(keyword in message_lower for keyword in keywords):
            return course_type
    
    return "健身"  # 預設值

def extract_date(message: str) -> Optional[str]:
    """從訊息中提取日期"""
    today = datetime.now()
    
    # 處理相對日期
    if '今天' in message or '今日' in message:
        return today.strftime('%Y-%m-%d')
    elif '明天' in message or '明日' in message:
        return (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif '後天' in message:
        return (today + timedelta(days=2)).strftime('%Y-%m-%d')
    
    # 處理絕對日期格式
    date_patterns = [
        r'(\d{4})-(\d{1,2})-(\d{1,2})',
        r'(\d{1,2})/(\d{1,2})',
        r'(\d{1,2})月(\d{1,2})日'
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, message)
        if match:
            try:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    return f"{year}-{int(month):02d}-{int(day):02d}"
                elif len(match.groups()) == 2:
                    month, day = match.groups()
                    return f"{today.year}-{int(month):02d}-{int(day):02d}"
            except ValueError:
                continue
    
    return None

def extract_time(message: str) -> Optional[str]:
    """從訊息中提取時間"""
    time_patterns = [
        r'(\d{1,2}):(\d{2})',
        r'(\d{1,2})點',
        r'(\d{1,2})時'
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, message)
        if match:
            if ':' in pattern:
                hour, minute = match.groups()
                return f"{int(hour):02d}:{int(minute):02d}"
            else:
                hour = match.group(1)
                return f"{int(hour):02d}:00"
    
    # 處理文字時間
    if '早上' in message or '上午' in message:
        return "09:00"
    elif '下午' in message:
        return "14:00"
    elif '晚上' in message:
        return "19:00"
    
    return None

def extract_user_info(message: str) -> Optional[Dict[str, str]]:
    """從訊息中提取用戶資訊"""
    # 簡單的姓名和電話提取
    phone_match = re.search(r'09\d{8}|\d{2,4}-\d{6,8}', message)
    
    # 假設剩下的就是姓名（實際應用中需要更複雜的 NLP）
    if phone_match:
        phone = phone_match.group()
        name = re.sub(r'09\d{8}|\d{2,4}-\d{6,8}', '', message).strip()
        name = re.sub(r'[^\w\u4e00-\u9fff]', '', name)  # 只保留中文和字母數字
        
        if name:
            return {"name": name, "phone": phone}
    
    return None
```

---

## 5. LINE Bot 整合

### 5.1 更新 LINE Webhook

```python
@app.post("/webhook")
async def line_webhook(request: Request):
    """LINE Webhook 處理器，支援 Function Calling"""
    body = await request.json()
    events = body.get("events", [])
    
    for event in events:
        if event["type"] == "message" and event["message"]["type"] == "text":
            user_text = event["message"]["text"]
            reply_token = event["replyToken"]
            user_id = event["source"]["userId"]  # 獲取 LINE 用戶 ID
            
            # 使用新的對話處理器
            try:
                response = handle_conversation(user_id, user_text)
            except Exception as e:
                print(f"對話處理錯誤: {e}")
                response = "抱歉，系統發生錯誤，請稍後再試。"
            
            # 發送回應
            headers = {
                "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            }
            payload = {
                "replyToken": reply_token,
                "messages": [{"type": "text", "text": response}],
            }
            
            async with httpx.AsyncClient() as client:
                await client.post(LINE_REPLY_ENDPOINT, headers=headers, json=payload)
    
    return "ok"
```

### 5.2 Web API 更新

```python
@app.post("/ask")
def ask(input: AskRequest):
    """Web API 端點，支援 Function Calling"""
    
    # 從訊息中提取用戶 ID（實際應用中從認證中獲取）
    user_id = input.messages[-1].id if input.messages else "web_user"
    user_message = input.messages[-1].parts[0]["text"] if input.messages else ""
    
    try:
        response = handle_conversation(user_id, user_message)
        return {"text": response}
    except Exception as e:
        print(f"對話處理錯誤: {e}")
        return {"text": "抱歉，系統發生錯誤，請稍後再試。"}
```

---

## 6. 測試與驗證

### 6.1 單元測試

```python
import unittest
from unittest.mock import patch, MagicMock

class TestFunctionCalling(unittest.TestCase):
    
    def setUp(self):
        self.session_manager = SessionManager()
        self.function_registry = FunctionRegistry()
        self.smart_caller = SmartFunctionCaller(self.function_registry)
    
    def test_intent_detection(self):
        """測試意圖識別"""
        test_cases = [
            ("我想預約瑜伽課", "booking"),
            ("課程時間表", "inquiry"),
            ("取消預約", "cancel"),
            ("瑜伽有什麼好處", "general_qa")
        ]
        
        for message, expected_intent in test_cases:
            result = IntentDetector.detect_intent(message)
            self.assertEqual(result['intent'], expected_intent)
    
    def test_booking_flow(self):
        """測試預約流程"""
        user_id = "test_user"
        
        # 開始預約
        response1 = handle_conversation(user_id, "我想預約瑜伽課")
        self.assertIn("預約", response1)
        
        # 選擇日期
        response2 = handle_conversation(user_id, "明天")
        self.assertIn("時段", response2)
        
        # 選擇時間
        response3 = handle_conversation(user_id, "09:00")
        self.assertIn("確認", response3)
    
    @patch('your_module.call_vllm')
    def test_function_calling(self, mock_call_vllm):
        """測試函數調用"""
        # 模擬 LLM 回應
        mock_call_vllm.return_value = 'FUNCTION_CALL: check_availability(course_type="瑜伽", date="2024-01-15")'
        
        session = UserSession("test_user")
        should_call, result = self.smart_caller.should_call_function("檢查瑜伽課程時間", session)
        
        self.assertTrue(should_call)
        self.assertIn("check_availability", result)

if __name__ == '__main__':
    unittest.main()
```

### 6.2 對話測試腳本

```python
def test_conversation_scenarios():
    """測試完整對話場景"""
    
    scenarios = [
        {
            "name": "完整預約流程",
            "messages": [
                "我想預約瑜伽課",
                "明天",
                "09:00",
                "王小明 0912345678"
            ],
            "expected_keywords": ["預約成功", "預約編號"]
        },
        {
            "name": "查詢課程",
            "messages": [
                "有什麼課程",
                "瑜伽課程時間"
            ],
            "expected_keywords": ["課程", "時間"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n測試場景：{scenario['name']}")
        user_id = f"test_{scenario['name']}"
        
        for i, message in enumerate(scenario['messages']):
            response = handle_conversation(user_id, message)
            print(f"用戶: {message}")
            print(f"系統: {response}")
            
            if i == len(scenario['messages']) - 1:
                # 檢查最後一個回應是否包含期望的關鍵字
                for keyword in scenario['expected_keywords']:
                    assert keyword in response, f"最終回應中缺少關鍵字: {keyword}"
        
        print("✅ 測試通過")

if __name__ == '__main__':
    test_conversation_scenarios()
```

---

## 7. 部署注意事項

### 7.1 效能優化

1. **會話管理優化**
   - 使用 Redis 存儲會話狀態
   - 設置會話過期時間
   - 定期清理無效會話

2. **函數調用快取**
   - 快取 API 調用結果
   - 實現智能快取失效策略

3. **並發處理**
   - 使用異步處理
   - 實現請求佇列機制

### 7.2 錯誤處理

```python
class ConversationError(Exception):
    """對話處理錯誤基類"""
    pass

class FunctionCallError(ConversationError):
    """函數調用錯誤"""
    pass

def safe_handle_conversation(user_id: str, message: str) -> str:
    """安全的對話處理函數"""
    try:
        return handle_conversation(user_id, message)
    except FunctionCallError as e:
        logger.error(f"函數調用錯誤 - 用戶: {user_id}, 錯誤: {e}")
        return "抱歉，處理您的請求時發生錯誤，請稍後再試。"
    except Exception as e:
        logger.error(f"未預期錯誤 - 用戶: {user_id}, 錯誤: {e}")
        return "系統繁忙，請稍後再試。"
```

### 7.3 監控與日誌

```python
import logging
from datetime import datetime

# 設置日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def log_conversation(user_id: str, message: str, response: str, function_calls: List[str] = None):
    """記錄對話日誌"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user_id,
        "message": message,
        "response": response,
        "function_calls": function_calls or []
    }
    logger.info(f"對話記錄: {log_data}")

# 在 handle_conversation 中添加日誌記錄
def handle_conversation_with_logging(user_id: str, message: str) -> str:
    """帶日誌記錄的對話處理"""
    start_time = datetime.now()
    function_calls = []
    
    try:
        response = handle_conversation(user_id, message)
        
        # 記錄成功的對話
        log_conversation(user_id, message, response, function_calls)
        
        return response
    except Exception as e:
        # 記錄錯誤
        logger.error(f"對話處理失敗 - 用戶: {user_id}, 訊息: {message}, 錯誤: {e}")
        raise
    finally:
        # 記錄處理時間
        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"對話處理時間: {duration:.2f}秒")
```

---

## 8. 總結

本指南展示了如何在 AI 客服系統中實現 Function Calling 功能，主要特點：

1. **智能意圖識別** - 自動判斷用戶需求
2. **狀態管理** - 支援多輪對話
3. **靈活函數調用** - 動態執行外部 API
4. **自然對話體驗** - 保持對話的連貫性
5. **易於擴展** - 可輕鬆添加新的函數和功能

這個架構可以輕鬆擴展到其他業務場景，如餐廳訂位、醫療預約、客戶服務等。關鍵是設計好 prompt 和狀態管理，讓 LLM 能夠智能地調用合適的函數來完成用戶任務。
