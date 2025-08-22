# LineRAG 修正實施計劃

## 修正優先級

### P0 (緊急) - 核心功能修正

1. 統一命名空間管理
2. 修正文檔內容索引問題（**關鍵：向量點數量為0的問題**）
3. 修正查詢命名空間問題
4. **修正 LightRAG 實例重新創建邏輯**
5. **修正文檔處理狀態更新邏輯**

### P1 (高優先級) - 數據完整性

1. 修正文檔刪除功能（**完全清理 Qdrant 和 Neo4j 數據**）
2. 添加數據驗證邏輯
3. **修正多租戶隔離驗證**
4. **添加處理失敗時的狀態回滾**

### P2 (中優先級) - 系統穩定性
1. 完善錯誤處理
2. 添加詳細日誌
3. **添加背景任務監控**
4. **添加資料庫連接池管理**

## 具體修正步驟

### 步驟 1: 創建統一命名空間管理

**文件：** `apps/api/app/utils/namespace.py`

```python
def get_company_workspace(company_id: int) -> str:
    """獲取公司的統一命名空間"""
    return f"company_{company_id}"

def set_company_environment(company_id: int):
    """設定公司環境變數"""
    workspace = get_company_workspace(company_id)
    os.environ["QDRANT_WORKSPACE"] = workspace
    os.environ["NEO4J_WORKSPACE"] = workspace
    return workspace

def restore_environment(original_qdrant: str, original_neo4j: str):
    """恢復原始環境變數"""
    if original_qdrant:
        os.environ["QDRANT_WORKSPACE"] = original_qdrant
    if original_neo4j:
        os.environ["NEO4J_WORKSPACE"] = original_neo4j
```

### 步驟 2: 修正文檔處理邏輯

**文件：** `apps/api/app/services/rag_anything.py`

**修正點：**
1. 在 `process_document` 方法中使用統一命名空間
2. 確保 LightRAG 實例使用正確的命名空間
3. 直接解析文檔內容並插入 LightRAG
4. 添加處理結果驗證

**關鍵修改：**
```python
async def process_document(self, file_path: str, company_id: str, output_dir: str = "./output"):
    # 1. 設定統一命名空間
    workspace = set_company_environment(int(company_id))
    
    # 2. 重新創建 LightRAG 實例
    new_lightrag = create_lightrag_instance(workspace)
    
    # 3. 解析文檔內容
    content = extract_document_content(file_path)
    
    # 4. 直接插入 LightRAG
    await new_lightrag.ainsert(content)
    
    # 5. 驗證數據是否正確存儲
    verify_data_storage(workspace)
```

### 步驟 3: 修正查詢邏輯

**文件：** `apps/api/app/services/rag_anything.py`

**修正點：**
1. 在查詢前設定正確的命名空間
2. 確保查詢在正確的命名空間中執行
3. 添加查詢前的數據驗證

**關鍵修改：**
```python
async def query_text(self, query: str, mode: str = "hybrid", company_id: str = None):
    if company_id:
        # 設定查詢命名空間
        original_env = set_company_environment(int(company_id))
        
        # 驗證數據存在
        verify_query_data_exists(company_id)
    
    # 執行查詢
    result = await self.rag_instance.aquery(query, mode=mode)
    
    # 恢復環境
    if company_id:
        restore_environment(original_env)
    
    return result
```

### 步驟 4: 修正刪除邏輯

**文件：** `apps/api/app/services/rag_anything.py`

**修正點：**
1. 完全清理 Qdrant 中的相關集合
2. 完全清理 Neo4j 中的相關節點
3. 刪除物理文件
4. 更新資料庫狀態

**關鍵修改：**
```python
async def delete_document(self, document_id: str, company_id: str):
    workspace = set_company_environment(int(company_id))
    
    # 1. 刪除 Qdrant 集合
    await delete_qdrant_collections(workspace)
    
    # 2. 刪除 Neo4j 節點
    await delete_neo4j_nodes(workspace)
    
    # 3. 刪除物理文件
    delete_physical_files(company_id)
    
    # 4. 驗證刪除完成
    verify_deletion_complete(workspace)
```

### 步驟 5: 添加數據驗證

**新文件：** `apps/api/app/utils/data_validator.py`

```python
async def verify_document_processing(company_id: int, document_name: str):
    """驗證文檔是否正確處理"""
    workspace = get_company_workspace(company_id)

    # 檢查 Qdrant
    qdrant_valid = check_qdrant_data(workspace)

    # 檢查 Neo4j
    neo4j_valid = check_neo4j_data(workspace)

    return qdrant_valid and neo4j_valid

async def verify_query_data_exists(company_id: int):
    """驗證查詢數據是否存在"""
    workspace = get_company_workspace(company_id)

    if not has_qdrant_data(workspace):
        raise ValueError(f"No vector data found for company {company_id}")

    if not has_neo4j_data(workspace):
        raise ValueError(f"No graph data found for company {company_id}")
```

### 步驟 6: 修正背景任務處理

**文件：** `apps/api/app/routers/ingest.py`

**遺漏的關鍵修正：**
1. 背景任務錯誤處理
2. 處理狀態正確更新
3. 失敗時的回滾邏輯

```python
async def process_document_task(doc_id: str, file_path: str, company_id: int, user_id: int):
    """背景文檔處理任務 - 添加完整的錯誤處理"""
    db = SessionLocal()
    try:
        # 更新狀態為處理中
        document = db.query(DocumentMetadata).filter(DocumentMetadata.document_id == doc_id).first()
        document.processing_status = "processing"
        db.commit()

        # 處理文檔
        rag_service = await get_company_rag_service(company_id, db)
        result = await rag_service.process_document(file_path, str(company_id))

        # 驗證處理結果
        if result["status"] == "success":
            # 驗證數據是否正確存儲
            data_valid = await verify_document_processing(company_id, document.original_filename)
            if data_valid:
                document.processing_status = "completed"
            else:
                document.processing_status = "failed"
                document.error_message = "Data validation failed"
        else:
            document.processing_status = "failed"
            document.error_message = result.get("message", "Unknown error")

    except Exception as e:
        document.processing_status = "failed"
        document.error_message = str(e)
        print(f"❌ 背景任務處理失敗: {e}")
    finally:
        db.commit()
        db.close()
```

### 步驟 7: 修正 webhook 查詢邏輯

**文件：** `apps/api/app/routers/webhook.py`

**遺漏的關鍵修正：**
1. 查詢前的數據存在驗證
2. 命名空間設定確認
3. 查詢失敗時的友好提示

```python
# 在查詢前添加數據驗證
try:
    # 驗證公司數據是否存在
    await verify_query_data_exists(company_id)

    # 使用正確的命名空間查詢
    answer = await company_rag_service.query_text(
        user_text, mode="hybrid", company_id=str(company_id)
    )

except ValueError as e:
    # 數據不存在的友好提示
    answer = "抱歉，系統中還沒有相關文檔資料。請先上傳文檔後再進行查詢。"
    logger.warning(f"查詢數據不存在: {e}")
except Exception as e:
    # 其他錯誤的處理
    answer = "抱歉，查詢時發生錯誤，請稍後再試。"
    logger.error(f"查詢錯誤: {e}")
```

## 實施順序

### 第一天：核心修正
1. ✅ 創建 `namespace.py` 統一命名空間管理
2. ✅ 修正 `process_document` 方法
3. ✅ 修正 `query_text` 方法
4. ✅ 測試基本上傳和查詢功能

### 第二天：完善功能
1. ✅ 修正 `delete_document` 方法
2. ✅ 創建 `data_validator.py` 數據驗證
3. ✅ 添加詳細日誌
4. ✅ 測試刪除功能

### 第三天：測試和優化
1. ✅ 完整的端到端測試
2. ✅ 性能優化
3. ✅ 錯誤處理完善
4. ✅ 文檔更新

## 測試計劃

### 單元測試
- [ ] 命名空間管理函數測試
- [ ] 文檔處理邏輯測試
- [ ] 查詢邏輯測試
- [ ] 刪除邏輯測試

### 集成測試
- [ ] 完整的上傳-處理-查詢流程
- [ ] 多租戶隔離測試
- [ ] 刪除功能測試
- [ ] 錯誤處理測試

### 驗收測試
- [ ] LINE Bot 端到端測試
- [ ] 前端管理界面測試
- [ ] 性能測試
- [ ] 壓力測試

## 回滾計劃

如果修正出現問題，按以下順序回滾：

1. **立即回滾：** 恢復原始的 `rag_anything.py`
2. **數據恢復：** 從備份恢復 Qdrant 和 Neo4j 數據
3. **服務重啟：** 重啟所有相關服務
4. **驗證功能：** 確保基本功能正常

## 監控指標

### 處理成功率
- 文檔上傳成功率 > 95%
- 文檔處理成功率 > 90%
- 查詢響應成功率 > 98%

### 性能指標
- 文檔處理時間 < 2分鐘（10MB以下文檔）
- 查詢響應時間 < 5秒
- 系統可用性 > 99%

### 數據完整性
- 多租戶隔離 100% 正確
- 數據刪除 100% 完整
- 無數據洩漏事件

---

**實施負責人：** 開發團隊  
**預計完成時間：** 3個工作日  
**風險等級：** 中等  
**回滾準備：** 已完成
