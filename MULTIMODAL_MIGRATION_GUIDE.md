# LineRAG 多模態功能遷移指南

## 🚨 重要變更：vLLM 限制與解決方案

### 問題背景

原本規劃使用 vLLM 作為統一的推理引擎，但發現 **vLLM 不支援多模態模型**，這影響了以下功能：

- 後台文檔 OCR 處理
- 前台圖片問答功能

### 解決方案：混合架構

我們採用了 **混合推理架構** 來解決這個問題：

```bash
文本對話 → vLLM (保持原有高效能)
多模態處理 → Transformers + Qwen2-VL (新增)
```

## 📋 主要變更內容

### 1. 新增文件

- `multimodal_service.py` - 多模態推理服務
- `document_processor.py` - 文檔 OCR 處理服務
- `README_MULTIMODAL.md` - 多模態功能說明

### 2. 修改文件

- `main.py` - 新增多模態 API 端點
- `requirements.txt` - 新增多模態依賴包

### 3. 新增 API 端點

- `POST /ask-image` - 圖片問答
- `POST /upload-image` - 圖片上傳
- `POST /ocr-extract` - OCR 文字提取
- `POST /ingest` - 支援 OCR 模式的文檔處理

## 🔧 部署步驟

### 1. 安裝新依賴

```bash
pip install -r requirements.txt
```

### 2. 下載多模態模型

```python
from transformers import AutoProcessor, AutoModelForVision2Seq

# 模型會自動下載到 ~/.cache/huggingface/
model_name = "Qwen/Qwen2-VL-2B-Instruct"
processor = AutoProcessor.from_pretrained(model_name)
model = AutoModelForVision2Seq.from_pretrained(model_name)
```

### 3. 創建上傳目錄

```bash
mkdir -p uploads/images
mkdir -p uploads/documents
```

### 4. 啟動服務

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## 📊 效能影響評估

### 記憶體使用

- **vLLM (文本)**：約 8-12GB VRAM
- **Qwen2-VL (多模態)**：約 4-6GB VRAM
- **總計**：約 12-18GB VRAM (RTX 5090 24GB 足夠)

### 處理速度

- **文本對話**：維持原有速度 (1-2秒)
- **圖片問答**：3-5秒 (首次載入模型需額外時間)
- **OCR 處理**：依文檔大小，每頁約 2-3秒

## 🎯 使用場景實現

### 場景 1：後台 OCR 文檔處理

```json
POST /ingest
{
  "file_path": "/path/to/scan.pdf",
  "original_name": "掃描文檔.pdf",
  "use_ocr": true
}
```

### 場景 2：前台器材圖片問答

```json
POST /ask-image
{
  "image_path": "/path/to/equipment.jpg",
  "question": "這個器材怎麼使用？"
}
```

## ⚠️ 注意事項

### 1. 模型載入

- 首次使用多模態功能時需要載入模型
- 建議在系統啟動時預載入模型

### 2. 資源管理

- 兩個推理引擎會同時佔用 GPU 記憶體
- 建議監控 GPU 使用率

### 3. 錯誤處理

- 多模態功能失敗時會降級到純文本模式
- 系統會記錄詳細的錯誤日誌

## 🔄 遷移檢查清單

- [ ] 安裝新的依賴包
- [ ] 測試多模態模型載入
- [ ] 驗證 OCR 文檔處理功能
- [ ] 測試圖片問答功能
- [ ] 檢查 GPU 記憶體使用情況
- [ ] 更新前端界面（如需要）
- [ ] 更新文檔和使用說明

## 🚀 未來優化方向

1. **模型量化**：使用 INT4 量化減少記憶體使用
2. **模型切換**：根據負載動態載入/卸載模型
3. **批次處理**：優化 OCR 批次處理效能
4. **快取機制**：常用圖片結果快取

這個混合架構既保持了原有文本對話的高效能，又新增了強大的多模態功能，完美解決了 vLLM 的限制問題。
