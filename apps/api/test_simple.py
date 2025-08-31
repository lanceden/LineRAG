#!/usr/bin/env python3
"""
簡單的 RAG 查詢測試
"""

import requests
import json

# 配置
API_BASE_URL = "http://localhost:8000/api"
COMPANY_ID = 12

def simple_ask(question: str):
    """簡單查詢函數"""
    url = f"{API_BASE_URL}/ask"
    
    payload = {
        "messages": [{"id": "1", "role": "user", "content": question}],
        "company_id": COMPANY_ID
    }
    
    response = requests.post(url, json=payload, stream=True)
    
    if response.status_code == 200:
        full_text = ""
        for line in response.iter_lines():
            if line:
                line_str = line.decode('utf-8')
                if line_str.startswith('data: '):
                    data_str = line_str[6:]
                    if data_str == '[DONE]':
                        break
                    try:
                        data = json.loads(data_str)
                        if data.get('type') == 'text':
                            text = data.get('text', '')
                            print(text, end='', flush=True)
                            full_text += text
                    except:
                        continue
        print("\n")
        return full_text
    else:
        print(f"錯誤: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    # 測試查詢
    question = input("請輸入問題: ")
    print(f"\n回答:")
    simple_ask(question)