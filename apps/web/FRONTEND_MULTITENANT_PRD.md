# LineRAG 前端多租戶架構 PRD 文檔

**版本**：v2.0
**日期**：2025-01-13
**狀態**：設計階段

---

## 📋 產品需求概述

### 🎯 核心目標

將現有的單一公司前端介面升級為**多租戶管理平台**，支援統一管理多家公司的 AI 客服系統。

### 🏢 業務場景

- **系統管理員**：管理多家公司、分配資源、監控使用狀況
- **公司管理員**：管理自己公司的用戶、文檔、對話記錄
- **客服人員**：查看自己公司的客戶對話、管理知識庫
- **一般用戶**：通過 LINE 與 AI 客服互動（不需要前端介面）

---

## 🏗️ 多租戶前端架構設計

### 系統架構概覽

```bash
┌─────────────────────────────────────────────────────────────────┐
│                LineRAG Multi-Tenant Frontend                   │
├─────────────────────────────────────────────────────────────────┤
│                      Next.js 14 App Router                     │
├─────────────────────────────────────────────────────────────────┤
│  Routes: /auth | /admin | /company/[id] | /dashboard | /api    │
├─────────────────────────────────────────────────────────────────┤
│                         Features                               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐  │
│  │ System Admin   │ │ Company Mgmt   │ │ Knowledge Base     │  │
│  │ Dashboard      │ │ Dashboard      │ │ Management         │  │
│  └────────────────┘ └────────────────┘ └────────────────────┘  │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐  │
│  │ User Role      │ │ Chat Analytics │ │ Document Upload    │  │
│  │ Management     │ │ & Reports      │ │ & Processing       │  │
│  └────────────────┘ └────────────────┘ └────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                        State Management                        │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐  │
│  │ Zustand Store  │ │ TanStack Query │ │ NextAuth Session   │  │
│  │ (Global State) │ │ (Server State) │ │ (Auth Context)     │  │
│  └────────────────┘ └────────────────┘ └────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                         UI Components                          │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────────┐  │
│  │ Shadcn/ui      │ │ Custom Charts  │ │ Multi-tenant       │  │
│  │ Components     │ │ & Analytics    │ │ Layout System      │  │
│  └────────────────┘ └────────────────┘ └────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔐 權限與角色設計

### 角色定義

| 角色              | 權限範圍 | 主要功能                      |
| ----------------- | -------- | ----------------------------- |
| **Super Admin**   | 全系統   | 管理所有公司、系統設定、監控  |
| **Company Admin** | 單一公司 | 管理公司用戶、文檔、LINE 設定 |
| **CS Manager**    | 單一公司 | 查看對話記錄、管理知識庫      |
| **CS Agent**      | 單一公司 | 查看指定的對話記錄            |

### 權限控制策略

```typescript
// 權限控制 Hook
const usePermissions = () => {
  const { user, company } = useAuth();
  
  return {
    canManageCompanies: user.role === 'super_admin',
    canManageUsers: ['super_admin', 'company_admin'].includes(user.role),
    canViewAllChats: ['super_admin', 'company_admin', 'cs_manager'].includes(user.role),
    canUploadDocuments: user.role !== 'cs_agent',
    canAccessCompany: (companyId: string) => {
      if (user.role === 'super_admin') return true;
      return user.company_id === companyId;
    }
  };
};
```

---

## 📱 頁面架構設計

### 路由結構

```bash
src/app/
├── (auth)/
│   ├── login/page.tsx              # 登入頁面
│   └── layout.tsx                  # 認證布局
├── (dashboard)/
│   ├── layout.tsx                  # 主要布局（側邊欄、導航）
│   ├── page.tsx                    # 儀表板首頁
│   ├── admin/                      # 系統管理員專區
│   │   ├── companies/              # 公司管理
│   │   ├── users/                  # 用戶管理
│   │   ├── system/                 # 系統設定
│   │   └── analytics/              # 系統分析
│   ├── company/[companyId]/        # 公司專區
│   │   ├── page.tsx                # 公司儀表板
│   │   ├── users/                  # 公司用戶管理
│   │   ├── documents/              # 知識庫管理
│   │   ├── chats/                  # 對話記錄
│   │   ├── analytics/              # 公司分析
│   │   └── settings/               # 公司設定
│   └── profile/                    # 個人設定
└── api/                           # API Routes
    ├── auth/                      # 認證相關
    ├── companies/                 # 公司管理 API
    ├── users/                     # 用戶管理 API
    └── upload/                    # 檔案上傳 API
```

### 核心頁面功能

#### 1. 系統管理員儀表板 (`/admin`)

**功能特色：**

- 🏢 **公司總覽**：所有公司狀態、使用統計
- 👥 **用戶管理**：跨公司用戶搜尋、角色管理
- 📊 **系統監控**：API 使用量、錯誤率、效能指標
- ⚙️ **系統設定**：全域配置、維護模式

**關鍵組件：**

```typescript
// 系統統計卡片
<StatCard 
  title="總公司數" 
  value={companies.length} 
  trend="+2 本月" 
/>

// 公司列表表格
<CompaniesTable 
  companies={companies}
  onEdit={handleEditCompany}
  onToggleStatus={handleToggleStatus}
/>

// 系統監控圖表
<SystemMetricsChart 
  data={systemMetrics}
  timeRange="7d"
/>
```

#### 2. 公司管理頁面 (`/company/[companyId]`)

**功能特色：**

- 📈 **公司儀表板**：對話統計、文檔數量、用戶活躍度
- 🔧 **LINE 設定**：Channel Token、Webhook 配置
- 📄 **知識庫管理**：文檔上傳、分類、搜尋
- 💬 **對話記錄**：實時對話監控、品質評估

**關鍵組件：**

```typescript
// 公司切換器
<CompanySelector 
  currentCompany={currentCompany}
  companies={userCompanies}
  onSwitch={handleCompanySwitch}
/>

// 對話監控面板
<ChatMonitor 
  companyId={companyId}
  realtime={true}
  showMetrics={true}
/>

// 文檔上傳組件
<DocumentUploader 
  companyId={companyId}
  onUploadSuccess={handleUploadSuccess}
  maxFileSize="100MB"
/>
```

#### 3. 知識庫管理 (`/company/[companyId]/documents`)

**功能特色：**

- 📂 **文檔分類**：按類型、標籤、部門分類
- 🔍 **智能搜尋**：全文搜尋、語義搜尋
- 📊 **處理狀態**：上傳進度、解析結果、錯誤處理
- 🔄 **批次操作**：批次上傳、刪除、重新處理

**關鍵組件：**

```typescript
// 文檔列表視圖
<DocumentGrid 
  documents={documents}
  view={viewMode} // grid | list
  onSelect={handleDocumentSelect}
/>

// 文檔處理狀態
<ProcessingStatus 
  documentId={documentId}
  status={processing.status}
  progress={processing.progress}
/>

// 批次操作工具欄
<BatchActions 
  selectedDocuments={selectedDocs}
  actions={['delete', 'reprocess', 'export']}
/>
```

#### 4. 對話分析 (`/company/[companyId]/analytics`)

**功能特色：**

- 📊 **對話統計**：數量趨勢、回應時間、滿意度
- 🎯 **熱門問題**：常見問題排行、答案準確率
- 👤 **用戶分析**：活躍用戶、使用習慣、留存率
- 🔍 **搜尋分析**：查詢關鍵字、檢索準確率

**關鍵組件：**

```typescript
// 統計圖表
<ChatAnalyticsChart 
  data={chatMetrics}
  period={selectedPeriod}
  companyId={companyId}
/>

// 熱門問題表格
<PopularQuestionsTable 
  questions={popularQuestions}
  showAnswerRate={true}
/>

// 用戶行為分析
<UserBehaviorInsights 
  companyId={companyId}
  dateRange={dateRange}
/>
```

---

## 🎨 UI/UX 設計原則

### 設計系統

#### 色彩系統

```css
/* 多租戶主題色彩 */
:root {
  /* 系統管理員 */
  --admin-primary: #1e40af;      /* 深藍 */
  --admin-secondary: #dbeafe;    /* 淺藍 */
  
  /* 公司管理 */
  --company-primary: #059669;    /* 綠色 */
  --company-secondary: #d1fae5;  /* 淺綠 */
  
  /* 客服人員 */
  --cs-primary: #7c3aed;         /* 紫色 */
  --cs-secondary: #ede9fe;       /* 淺紫 */
}
```

#### 組件庫

- **基礎組件**：基於 shadcn/ui 的統一組件系統
- **業務組件**：多租戶專用的複合組件
- **圖表組件**：基於 Recharts 的數據可視化

### 響應式設計

| 螢幕尺寸            | 布局策略        | 主要調整         |
| ------------------- | --------------- | ---------------- |
| Desktop (>1200px)   | 側邊欄 + 主內容 | 完整功能展示     |
| Tablet (768-1200px) | 可收縮側邊欄    | 適當隱藏次要功能 |
| Mobile (<768px)     | 底部導航        | 簡化操作流程     |

---

## 🔧 技術架構詳細設計

### 狀態管理策略

#### 1. 全域狀態 (Zustand)

```typescript
// store/authStore.ts
interface AuthState {
  user: User | null;
  company: Company | null;
  companies: Company[];
  permissions: Permission[];
  setUser: (user: User) => void;
  setCompany: (company: Company) => void;
  clearAuth: () => void;
}

// store/uiStore.ts
interface UIState {
  sidebarCollapsed: boolean;
  theme: 'light' | 'dark' | 'system';
  currentCompanyId: string | null;
  notifications: Notification[];
}
```

#### 2. 服務端狀態 (TanStack Query)

```typescript
// hooks/useCompanies.ts
export const useCompanies = () => {
  return useQuery({
    queryKey: ['companies'],
    queryFn: () => companiesApi.getAll(),
    staleTime: 5 * 60 * 1000, // 5分鐘
  });
};

// hooks/useCompanyDocuments.ts
export const useCompanyDocuments = (companyId: string) => {
  return useQuery({
    queryKey: ['documents', companyId],
    queryFn: () => documentsApi.getByCompany(companyId),
    enabled: !!companyId,
  });
};
```

### API 整合

#### 1. API 客戶端設計

```typescript
// lib/api/client.ts
class ApiClient {
  private baseURL: string;
  private token: string | null = null;

  async request<T>(
    endpoint: string, 
    options: RequestOptions = {}
  ): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    };

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new ApiError(response.status, await response.text());
    }

    return response.json();
  }

  // 公司相關 API
  companies = {
    getAll: () => this.request<Company[]>('/companies'),
    getById: (id: string) => this.request<Company>(`/companies/${id}`),
    create: (data: CreateCompanyData) => 
      this.request<Company>('/companies', { method: 'POST', body: JSON.stringify(data) }),
    update: (id: string, data: UpdateCompanyData) => 
      this.request<Company>(`/companies/${id}`, { method: 'PUT', body: JSON.stringify(data) }),
  };
}
```

#### 2. 錯誤處理

```typescript
// components/ErrorBoundary.tsx
export const ErrorBoundary = ({ children }: { children: ReactNode }) => {
  return (
    <ReactErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        console.error('Error caught by boundary:', error, errorInfo);
        // 發送錯誤到監控系統
        errorReporting.captureException(error);
      }}
    >
      {children}
    </ReactErrorBoundary>
  );
};
```

### 認證與授權

#### 1. NextAuth.js 配置

```typescript
// lib/auth.ts
export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        const user = await authenticateUser(credentials);
        if (user) {
          return {
            id: user.id,
            email: user.email,
            name: user.name,
            role: user.role,
            companyId: user.company_id,
          };
        }
        return null;
      }
    })
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.role = user.role;
        token.companyId = user.companyId;
      }
      return token;
    },
    async session({ session, token }) {
      session.user.role = token.role;
      session.user.companyId = token.companyId;
      return session;
    }
  }
};
```

#### 2. 路由保護

```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.nextauth.token;
  const { pathname } = request.nextUrl;

  // 檢查認證
  if (!token && pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/auth/login', request.url));
  }

  // 檢查權限
  if (pathname.startsWith('/admin') && token?.role !== 'super_admin') {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // 檢查公司存取權限
  const companyMatch = pathname.match(/\/company\/([^\/]+)/);
  if (companyMatch) {
    const companyId = companyMatch[1];
    if (!canAccessCompany(token, companyId)) {
      return NextResponse.redirect(new URL('/dashboard', request.url));
    }
  }

  return NextResponse.next();
}
```

---

## 📊 數據流設計

### 實時數據更新

#### 1. WebSocket 連接

```typescript
// hooks/useWebSocket.ts
export const useWebSocket = (companyId: string) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/company/${companyId}`);
    
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // 更新相關的查詢快取
      queryClient.invalidateQueries(['chats', companyId]);
    };

    setSocket(ws);
    return () => ws.close();
  }, [companyId]);

  return { socket, isConnected };
};
```

#### 2. 服務端事件 (SSE)

```typescript
// hooks/useSSE.ts
export const useSSE = (endpoint: string) => {
  const [data, setData] = useState(null);

  useEffect(() => {
    const eventSource = new EventSource(endpoint);
    
    eventSource.onmessage = (event) => {
      setData(JSON.parse(event.data));
    };

    return () => eventSource.close();
  }, [endpoint]);

  return data;
};
```

---

## 🧪 測試策略

### 測試層級

#### 1. 單元測試 (Jest + Testing Library)

```typescript
// __tests__/components/CompanySelector.test.tsx
describe('CompanySelector', () => {
  it('should render companies list', () => {
    render(<CompanySelector companies={mockCompanies} />);
    expect(screen.getByText('Company A')).toBeInTheDocument();
  });

  it('should call onSwitch when company is selected', () => {
    const onSwitch = jest.fn();
    render(<CompanySelector companies={mockCompanies} onSwitch={onSwitch} />);
    
    fireEvent.click(screen.getByText('Company B'));
    expect(onSwitch).toHaveBeenCalledWith(mockCompanies[1]);
  });
});
```

#### 2. 整合測試 (Playwright)

```typescript
// e2e/admin-workflow.spec.ts
test('admin can manage companies', async ({ page }) => {
  await page.goto('/auth/login');
  await page.fill('[data-testid=email]', 'admin@example.com');
  await page.fill('[data-testid=password]', 'password');
  await page.click('[data-testid=login-button]');

  await page.goto('/admin/companies');
  await page.click('[data-testid=add-company-button]');
  
  await page.fill('[data-testid=company-name]', 'Test Company');
  await page.click('[data-testid=save-button]');
  
  await expect(page.locator('text=Test Company')).toBeVisible();
});
```

### 效能測試

#### 1. Bundle 分析

```typescript
// next.config.ts
const nextConfig = {
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.resolve.fallback = {
        fs: false,
        net: false,
        tls: false,
      };
    }
    return config;
  },
  experimental: {
    bundlePagesRouterDependencies: true,
  },
};
```

#### 2. 效能監控

```typescript
// lib/analytics.ts
export const trackPageView = (url: string) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', GA_TRACKING_ID, {
      page_path: url,
    });
  }
};

export const trackUserAction = (action: string, data?: any) => {
  if (typeof window !== 'undefined' && window.gtag) {
    window.gtag('event', action, data);
  }
};
```

---

## 📦 部署策略

### 環境配置

#### 1. 環境變數

```bash
# .env.local (開發)
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-secret-key
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# .env.production (生產)
NEXTAUTH_URL=https://your-domain.com
NEXTAUTH_SECRET=production-secret
NEXT_PUBLIC_API_URL=https://api.your-domain.com
NEXT_PUBLIC_WS_URL=wss://api.your-domain.com
```

#### 2. Docker 配置

```dockerfile
# Dockerfile
FROM node:18-alpine AS base

FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --only=production

FROM base AS builder
WORKDIR /app
COPY . .
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

FROM base AS runner
WORKDIR /app
ENV NODE_ENV production
COPY --from=builder /app/next.config.js ./
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

EXPOSE 3000
CMD ["npm", "start"]
```

### CI/CD 流程

```yaml
# .github/workflows/deploy.yml
name: Deploy Frontend
on:
  push:
    branches: [main]
    paths: ['apps/web/**']

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
        working-directory: apps/web
      
      - name: Run tests
        run: npm test
        working-directory: apps/web
      
      - name: Build application
        run: npm run build
        working-directory: apps/web
      
      - name: Deploy to Vercel
        uses: vercel/action@v20
        with:
          vercel-token: ${{ secrets.VERCEL_TOKEN }}
          vercel-org-id: ${{ secrets.ORG_ID }}
          vercel-project-id: ${{ secrets.PROJECT_ID }}
```

---

## 📈 效能優化

### 程式碼分割

```typescript
// 路由層級的程式碼分割
const AdminDashboard = dynamic(() => import('./AdminDashboard'), {
  loading: () => <DashboardSkeleton />,
  ssr: false,
});

const CompanyManagement = dynamic(() => import('./CompanyManagement'), {
  loading: () => <LoadingSpinner />,
});

// 組件層級的延遲載入
const HeavyChart = dynamic(() => import('./HeavyChart'), {
  loading: () => <ChartSkeleton />,
  ssr: false,
});
```

### 圖片優化

```typescript
// 使用 Next.js Image 組件
import Image from 'next/image';

<Image
  src="/company-logos/company-1.png"
  alt="Company Logo"
  width={120}
  height={40}
  priority={isAboveFold}
  placeholder="blur"
  blurDataURL="data:image/jpeg;base64,..."
/>
```

### 快取策略

```typescript
// lib/cache.ts
export const getCachedData = async <T>(
  key: string,
  fetcher: () => Promise<T>,
  ttl: number = 300 // 5分鐘
): Promise<T> => {
  const cached = sessionStorage.getItem(key);
  if (cached) {
    const { data, timestamp } = JSON.parse(cached);
    if (Date.now() - timestamp < ttl * 1000) {
      return data;
    }
  }

  const data = await fetcher();
  sessionStorage.setItem(key, JSON.stringify({
    data,
    timestamp: Date.now()
  }));
  
  return data;
};
```

---

## 🔮 未來功能規劃

### Phase 1 (3個月) - 核心多租戶功能

- ✅ 基礎多租戶架構 - 完成路由結構和認證系統
- ✅ 用戶角色權限系統 - 完成基礎 RBAC 和 middleware
- 🚧 公司管理介面 - 儀表板完成，詳細管理功能進行中
- ❌ 文檔上傳管理 - 待開發

### Phase 2 (6個月) - 增強功能

- 📊 高級分析報表
- 🔔 實時通知系統
- 📱 行動端優化
- 🎨 白標客製化

### Phase 3 (9個月) - 進階功能

- 🤖 AI 驅動的洞察
- 📈 預測分析
- 🔗 第三方整合
- 🌍 多語言支援

### Phase 4 (12個月) - 企業級功能

- 🔐 SSO 整合
- 📋 合規性工具
- 🚀 效能最佳化
- 🎯 個人化推薦

---

## 📋 開發里程碑

### Sprint 1-2 (2週) - 基礎架構

- [x] 設定 Next.js 14 多租戶路由 (`/multitenantrag/auth/login`, `/multitenantrag/admin`)
- [x] 實作認證系統 (NextAuth.js) - credentials provider with email login
- [x] 建立基礎 UI 組件庫 (shadcn/ui components)
- [ ] 設定狀態管理 (Zustand + TanStack Query)

### Sprint 3-4 (2週) - 管理介面

- [x] 系統管理員儀表板 - 基礎版本已完成，包含 Sidebar 導航
- [ ] 公司管理頁面
- [x] 用戶角色管理 - 基礎權限檢查已實作 (super_admin role)
- [x] 權限控制系統 - middleware 和 auth callback 已實作

### Sprint 5-6 (2週) - 業務功能

- [ ] 文檔上傳管理
- [ ] 對話記錄查看
- [ ] 基礎分析報表
- [ ] LINE 設定介面

### Sprint 7-8 (2週) - 優化與測試

- [ ] 效能優化
- [ ] 錯誤處理完善
- [ ] 單元測試撰寫
- [ ] E2E 測試建立

---

## 🎯 成功指標

### 技術指標

- **載入時間**：首頁 < 2秒，其他頁面 < 3秒
- **錯誤率**：< 1%
- **測試覆蓋率**：> 80%
- **Bundle 大小**：< 500KB (gzipped)

### 用戶體驗指標

- **操作效率**：常用操作 < 3次點擊
- **學習成本**：新用戶 < 30分鐘上手
- **滿意度**：用戶滿意度 > 4.5/5
- **支援請求**：相較舊系統減少 50%

### 業務指標

- **多租戶支援**：支援 100+ 公司
- **併發處理**：支援 1000+ 同時在線用戶
- **資料隔離**：100% 公司資料隔離
- **擴展性**：新增公司 < 5分鐘設定完成

---

**文檔維護者**：LineRAG 前端團隊  
**最後更新**：2025-01-13  
**版本控制**：遵循 Semantic Versioning
