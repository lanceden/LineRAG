# LineRAG 監控系統

## 🚀 快速啟動

### 啟動監控服務

```bash
# 啟動所有服務（包含監控）
docker-compose up -d

# 或者分別啟動
docker-compose up -d qdrant neo4j prometheus grafana
```

### 訪問監控介面

- **Grafana Dashboard**: http://localhost:3001
  - 用戶名: `admin`
  - 密碼: `linerag123`

- **Prometheus**: http://localhost:9090
- **API Metrics**: http://localhost:8000/api/metrics
- **API Health**: http://localhost:8000/api/metrics/health

## 📊 監控指標

### 系統指標

- **CPU 使用率**: 系統 CPU 負載百分比
- **記憶體使用率**: 記憶體使用百分比
- **磁碟使用率**: 磁碟空間使用百分比

### 業務指標

- **HTTP 請求率**: 每秒 HTTP 請求數
- **RAG 回應時間**: RAG 查詢處理時間
- **活躍公司數**: 目前活躍的租戶公司數量
- **總用戶數**: 系統總用戶數
- **RAG 查詢數**: 每小時 RAG 查詢統計

## 🎨 Dashboard 功能

### 即時監控

- 自動 30 秒刷新
- 即時系統資源狀態
- 業務指標趨勢圖

### 告警閾值

- **CPU**: >90% 紅色警告
- **記憶體**: >85% 紅色警告
- **磁碟**: >90% 紅色警告

## 🔧 自定義配置

### 修改刷新頻率

編輯 `monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s  # 改為所需頻率
```

### 新增監控目標

在 `monitoring/prometheus.yml` 加入:

```yaml
scrape_configs:
  - job_name: 'your-service'
    static_configs:
      - targets: ['your-service:port']
```

### 自定義 Dashboard

1. 登入 Grafana (http://localhost:3001)
2. 點選 "+" → "Dashboard"
3. 新增 Panel 並配置查詢

## 📈 Demo 展示重點

### 1. 系統健康狀態

- 綠色指示燈 = 系統正常
- CPU/記憶體使用合理
- 服務回應正常

### 2. 性能指標

- RAG 回應時間 < 3 秒
- HTTP 請求處理正常
- 無錯誤率飆升

### 3. 業務數據

- 活躍公司數量
- 用戶成長趨勢
- 查詢量統計

## 🚨 故障排除

### Grafana 無法連接 Prometheus

```bash
# 檢查服務狀態
docker-compose ps
docker logs linerag-prometheus-1
docker logs linerag-grafana-1
```

### Metrics 端點無數據

```bash
# 檢查 API metrics
curl http://localhost:8000/api/metrics
curl http://localhost:8000/api/metrics/health
```

### Dashboard 顯示 "No data"

1. 檢查 Prometheus 是否能抓取到數據
2. 訪問 http://localhost:9090/targets
3. 確認所有 targets 為 "UP" 狀態

---
