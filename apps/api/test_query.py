#!/usr/bin/env python3
"""
本機 RAG 查詢測試腳本
不需要 LINE Bot，直接呼叫 API 端點進行測試
"""

import requests
import json
import sys
import time

# API 配置
API_BASE_URL = "http://localhost:8000/api"
COMPANY_ID = 12  # 替換成你的測試公司 ID


def test_text_query(question: str, company_id: int = COMPANY_ID):
    """測試純文本查詢"""
    print(f"🔍 測試文本查詢...")
    print(f"   問題: {question}")
    print(f"   公司ID: {company_id}")
    
    url = f"{API_BASE_URL}/ask"
    
    payload = {
        "messages": [
            {
                "id": "test-msg-1",
                "role": "user", 
                "content": question
            }
        ],
        "company_id": company_id
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    try:
        print(f"📡 發送請求到: {url}")
        response = requests.post(url, json=payload, headers=headers, stream=True)
        
        if response.status_code == 200:
            print(f"✅ 請求成功，開始接收回應...")
            print("=" * 60)
            
            # 處理串流回應
            full_response = ""
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        data_str = line_str[6:]  # 移除 'data: '
                        if data_str == '[DONE]':
                            break
                        try:
                            data = json.loads(data_str)
                            if data.get('type') == 'text':
                                text = data.get('text', '')
                                print(text, end='', flush=True)
                                full_response += text
                        except json.JSONDecodeError:
                            continue
            
            print("\n" + "=" * 60)
            print(f"✅ 查詢完成")
            return full_response
            
        else:
            print(f"❌ 請求失敗: {response.status_code}")
            print(f"   錯誤訊息: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ 連接失敗: {e}")
        return None


def test_health_check():
    """測試 API 健康狀態"""
    print(f"🏥 檢查 API 健康狀態...")
    
    url = f"{API_BASE_URL}/health"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print(f"✅ API 服務正常運行")
            return True
        else:
            print(f"❌ API 服務異常: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 無法連接 API: {e}")
        print(f"   請確保 FastAPI 服務正在運行 (python main.py)")
        return False


def list_company_documents(company_id: int = COMPANY_ID):
    """列出公司的文檔"""
    print(f"📄 查看公司 {company_id} 的文檔...")
    
    url = f"{API_BASE_URL}/ingest/documents/{company_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            documents = response.json()
            print(f"✅ 找到 {len(documents)} 個文檔:")
            for i, doc in enumerate(documents, 1):
                print(f"   {i}. {doc.get('original_filename', 'Unknown')} "
                      f"({doc.get('processing_status', 'Unknown')})")
            return documents
        else:
            print(f"❌ 獲取文檔清單失敗: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 請求失敗: {e}")
        return []


def interactive_mode():
    """互動模式 - 連續提問"""
    print(f"🎯 進入互動模式 (輸入 'quit' 或 'exit' 退出)")
    print(f"   使用公司ID: {COMPANY_ID}")
    
    while True:
        try:
            question = input(f"\n❓ 請輸入問題: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print(f"👋 再見！")
                break
                
            if not question:
                continue
                
            test_text_query(question)
            
        except KeyboardInterrupt:
            print(f"\n👋 再見！")
            break


def main():
    """主函數"""
    print(f"🚀 LineRAG 本機測試工具")
    print(f"=" * 60)
    
    # 檢查 API 健康狀態
    if not test_health_check():
        sys.exit(1)
    
    # 查看文檔清單
    list_company_documents()
    
    print(f"\n選擇測試模式:")
    print(f"1. 單次查詢測試")
    print(f"2. 互動模式")
    
    try:
        choice = input(f"請選擇 (1/2): ").strip()
        
        if choice == "1":
            question = input(f"請輸入問題: ").strip()
            if question:
                test_text_query(question)
        elif choice == "2":
            interactive_mode()
        else:
            print(f"❌ 無效選擇")
            
    except KeyboardInterrupt:
        print(f"\n👋 再見！")


if __name__ == "__main__":
    main()