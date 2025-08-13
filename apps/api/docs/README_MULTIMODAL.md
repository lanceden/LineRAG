# LineRAG 多模態功能說明

## 🎯 功能概述

本系統現在支援兩種主要的多模態使用場景：

### 場景 1：後台文檔 OCR 處理

- **功能**：上傳 PDF/WORD 文檔，先轉換為圖片，再使用多模態模型進行 OCR 文字識別
- **優勢**：可以處理掃描版 PDF、圖片化文檔等傳統文字提取無法處理的內容
- **API 端點**：`POST /ingest` (設定 `use_ocr: true`)

### 場景 2：前台圖片問答

- **功能**：用戶上傳器材圖片，詢問使用方法，系統提供專業的健身指導
- **優勢**：結合視覺理解和專業知識，提供個性化的器材使用建議
- **API 端點**：`POST /ask-image`

## 🏗️ 技術架構

### 混合推理架構

```bash
文本對話 → vLLM (高效能、高併發)
多模態處理 → Transformers + Qwen2-VL (支援圖片理解)
```

### 核心組件

1. **MultimodalService** (`multimodal_service.py`)
   - 負責多模態模型的載入和推理
   - 支援圖片理解、OCR 文字識別
   - 專門針對健身器材分析優化

2. **DocumentProcessor** (`document_processor.py`)
   - 負責文檔轉圖片處理
   - 支援 PDF/WORD → 圖片 → OCR → 文字的完整流程
   - 整合到向量資料庫的索引流程

## 📋 API 端點說明

### 1. 文檔上傳（支援 OCR）

```http
POST /ingest
Content-Type: application/json

{
  "file_path": "/path/to/document.pdf",
  "original_name": "健身指南.pdf",
  "use_ocr": true  // 新增：啟用 OCR 模式
}
```

### 2. 圖片上傳

```http
POST /upload-image
Content-Type: multipart/form-data

file: [圖片文件]
```

### 3. 圖片問答

```http
POST /ask-image
Content-Type: application/json

{
  "image_path": "/path/to/equipment.jpg",
  "question": "這個器材怎麼使用？"
}
```

### 4. OCR 文字提取

```http
POST /ocr-extract
Content-Type: application/json

{
  "image_path": "/path/to/document_page.jpg",
  "question": ""  // 可以為空，純 OCR 功能
}
```

## 🚀 部署建議

### 硬體需求

- **GPU**：RTX 5090 (24GB VRAM) 或更高
- **RAM**：32GB+ (多模態模型記憶體需求較高)
- **儲存**：額外 20GB+ 用於多模態模型

### 模型選擇

- **推薦模型**：`Qwen/Qwen2-VL-2B-Instruct`
- **優勢**：
  - 支援中文和英文
  - 模型大小適中 (2B 參數)
  - 優秀的 OCR 和圖片理解能力
  - 適合 RTX 5090 運行

### 效能優化

1. **模型量化**：使用 INT4 量化減少記憶體使用
2. **批次處理**：OCR 處理時可批次處理多頁
3. **快取機制**：常用圖片結果可以快取

## 🔄 使用流程

### 後台管理員使用流程

1. 上傳 PDF/WORD 文檔
2. 選擇是否啟用 OCR 模式
3. 系統自動處理並索引到向量資料庫
4. 可在文檔列表中查看處理方式

### 前台用戶使用流程

1. 上傳器材圖片
2. 詢問使用方法或相關問題
3. 系統分析圖片並提供專業建議
4. 可結合 RAG 檢索相關文檔內容

## ⚠️ 注意事項

1. **模型載入時間**：首次使用多模態功能時需要載入模型，可能需要 1-2 分鐘
2. **記憶體管理**：多模態模型會佔用額外的 GPU 記憶體
3. **處理時間**：OCR 處理大文檔可能需要較長時間
4. **文件格式**：目前支援 PDF、DOC、DOCX 和常見圖片格式

## 🔧 故障排除

### 常見問題

1. **模型載入失敗**：檢查 GPU 記憶體是否足夠
2. **OCR 效果不佳**：可以調整圖片解析度或使用更高品質的掃描
3. **處理速度慢**：考慮使用更小的模型或啟用量化

### 日誌監控

系統會記錄詳細的處理日誌，包括：

- 模型載入狀態
- 文檔處理進度
- 錯誤信息和堆疊追蹤
