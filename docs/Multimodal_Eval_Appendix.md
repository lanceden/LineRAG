# 多模態評測附錄（最小可重現）

本附錄提供一套「最小、可重現」的評測方法與樣例，用於驗證主報告中的內部估算結論。內容聚焦於：
- 指標定義（圖表信息保持率、表格結構保持率、圖文關聯保持率、最終問答正確率、引用準確率）
- 樣例資料格式（vendor-neutral JSONL）
- 最小評測腳本（不依賴外部服務，僅對輸出與標準答案做比較）

---

## 1. 指標定義（簡化版）
- 圖表信息保持率 (Chart Info Retention)
  - 定義：對圖表型題目，系統答案中是否包含關鍵數值/趨勢或圖說要點
  - 衡量：以關鍵詞/關鍵數字命中率（EM or F1）衡量
- 表格結構保持率 (Table Structure Retention)
  - 定義：表格題中，是否保留表頭、列/行對齊與單元格對應關係
  - 衡量：使用結構關鍵詞（欄名）與值對（header:value）命中率估計
- 圖文關聯保持率 (Caption-Context Linking)
  - 定義：回答是否同時引用圖（或表）與其相鄰段落的關聯資訊（例如：圖號 + 圖說要點）
  - 衡量：答案中同時命中「圖/表 ID」與「圖說關鍵詞」即記 1
- 問答正確率 (QA Accuracy)
  - 定義：答案是否命中標準答案的關鍵詞集合（或正則）
  - 衡量：EM/F1（此處以關鍵詞命中率近似）
- 引用準確率 (Citation Precision)
  - 定義：答案所附來源切片是否對應到標準答案標註來源（頁碼/圖表 ID）
  - 衡量：引用 IDs 與標註 IDs 交集 / 引用 IDs 數

> 備註：上述皆為簡化指標，目的是建立最小可重現的評測流程。正式評測可替換為更嚴謹的 NER/表格對齊/版面對齊方法。

---

## 2. 樣例資料格式（docs/eval_samples/ground_truth.jsonl）
每行為一題，JSON 結構如下：
```json
{
  "id": "q1",
  "type": "chart|table|caption|text",
  "question": "問題文本",
  "answer_keywords": ["關鍵字1", "關鍵字2"],
  "source_ids": ["p3_fig2", "p3"],
  "notes": "可選：評註或說明"
}
```
- type：簡化題型，對應不同指標
- answer_keywords：最小關鍵詞集合，用於計算命中率
- source_ids：標準來源（頁碼/圖表 ID），用於引用準確率

同時準備一份系統輸出樣例（scripts/eval_outputs/sample_predictions.jsonl）：
```json
{
  "id": "q1",
  "answer": "系統答案...",
  "citations": ["p3_fig2"]
}
```

---

## 3. 最小評測腳本
位置：scripts/eval_minimal.py
職責：讀取 ground_truth.jsonl 與 sample_predictions.jsonl，計算簡化指標（EM/F1 近似：關鍵詞命中率）。

執行方式：
```bash
python scripts/eval_minimal.py \
  --gold docs/eval_samples/ground_truth.jsonl \
  --pred scripts/eval_outputs/sample_predictions.jsonl
```
輸出：各指標的 micro 平均分與逐題結果摘要（stdout）。

---

## 4. 最小資料集建議
- 每種類型至少 2 題（chart/table/caption/text），總計 8 題起步
- 若有實際文件，建議來源 ID 命名：p{頁碼}_fig{序號} 或 p{頁碼}_tbl{序號}

---

## 5. 延伸（可選）
- 導入 reranker/階層索引後再評測，觀察 Lost in the Middle 緩解幅度
- 對多模態管線與文本管線分別跑同一題集，比較保持率差異

