FROM node:18-alpine

WORKDIR /app

# 安裝 curl (健康檢查用)
RUN apk add --no-cache curl

# 複製 package 文件
COPY package*.json ./

# 安裝依賴 - 強制方式
RUN npm install --legacy-peer-deps --no-package-lock

# 複製源代碼
COPY . .

# 設定環境變數
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# 建置應用
RUN npm run build

# 暴露端口
EXPOSE 3000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000 || exit 1

# 啟動命令
CMD ["npm", "start"]