# 基礎權限管理實現方案

## 方案B - 基礎權限管理（2層級）

### 🎯 權限架構設計

```typescript
enum UserRole {
  ADMIN = 'admin',        // 管理員：管理知識庫、查看所有對話、系統設定
  CUSTOMER_SERVICE = 'cs' // 客服人員：查看對話記錄、基礎統計
}
```

### 📋 權限功能對照表

| 功能模組      | 管理員 (ADMIN) | 客服 (CS) | 說明                   |
| ------------- | -------------- | --------- | ---------------------- |
| 知識庫管理    | ✅              | ❌         | 上傳/刪除文檔、管理FAQ |
| 對話記錄查詢  | ✅              | ✅         | 查看用戶對話歷史       |
| 系統統計報表  | ✅              | ✅         | 使用量、問答效果統計   |
| 用戶管理      | ✅              | ❌         | 設定其他用戶角色       |
| 系統設定      | ✅              | ❌         | 調整AI參數、系統配置   |
| ChatPanel使用 | ✅              | ✅         | 測試對話功能           |

### 🏗️ 實現架構

#### 1. 資料庫設計

```sql
-- 用戶角色表
CREATE TABLE user_roles (
    id SERIAL PRIMARY KEY,
    line_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'cs', -- 'admin' | 'cs'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(255), -- 建立者的line_id
    is_active BOOLEAN DEFAULT true
);

-- 初始管理員資料
INSERT INTO user_roles (line_id, name, role, created_by) 
VALUES ('YOUR_LINE_ID_HERE', '系統管理員', 'admin', 'system');
```

#### 2. NextAuth 配置擴展

```typescript
// apps/web/src/auth.ts
import NextAuth from 'next-auth'
import Line from 'next-auth/providers/line'
import { getUserRole } from '@/lib/db/users'

export const { handlers, signIn, signOut, auth } = NextAuth({
    secret: process.env.NEXTAUTH_SECRET,
    providers: [
        Line({
            clientId: process.env.LINE_CLIENT_ID!,
            clientSecret: process.env.LINE_CLIENT_SECRET!,
        }),
    ],
    callbacks: {
        async jwt({ token, account, profile }) {
            if (account && profile) {
                token.lineId = (profile as { userId?: string }).userId
                token.name = (profile as { displayName?: string }).displayName
                
                // 獲取用戶角色
                if (token.lineId) {
                    const userRole = await getUserRole(token.lineId as string)
                    token.role = userRole?.role || 'cs' // 預設為客服
                    token.isActive = userRole?.is_active || false
                }
            }
            return token
        },
        async session({ session, token }) {
            if (session.user) {
                session.user.lineId = token.lineId as string
                session.user.role = token.role as string
                session.user.isActive = token.isActive as boolean
            }
            return session
        },
        async redirect({ url, baseUrl }) {
            if (url.startsWith(baseUrl)) {
                return url
            }
            return `${baseUrl}/dashboard`
        },
    },
    pages: {
        signIn: '/',
    },
})

// 擴展 NextAuth 類型
declare module 'next-auth' {
    interface User {
        lineId?: string
        role?: string
        isActive?: boolean
    }
    interface Session {
        user: User & {
            lineId: string
            role: string
            isActive: boolean
        }
    }
}
```

#### 3. 權限檢查工具

```typescript
// apps/web/src/lib/auth.ts
import { auth } from '@/auth'
import { redirect } from 'next/navigation'

export async function requireAuth() {
    const session = await auth()
    if (!session?.user) {
        redirect('/')
    }
    return session
}

export async function requireAdmin() {
    const session = await requireAuth()
    if (session.user.role !== 'admin') {
        redirect('/dashboard')
    }
    return session
}

export function hasPermission(userRole: string, requiredRole: 'admin' | 'cs') {
    if (requiredRole === 'cs') {
        return ['admin', 'cs'].includes(userRole)
    }
    return userRole === 'admin'
}

// React Hook 版本
export function usePermissions() {
    const { data: session } = useSession()
    
    return {
        isAdmin: session?.user.role === 'admin',
        isCS: ['admin', 'cs'].includes(session?.user.role || ''),
        hasRole: (role: 'admin' | 'cs') => hasPermission(session?.user.role || '', role)
    }
}
```

#### 4. 路由保護 Middleware

```typescript
// apps/web/src/middleware.ts
import { auth } from '@/auth'
import { NextResponse } from 'next/server'

export async function middleware(request: NextRequest) {
    const session = await auth()
    const { pathname } = request.nextUrl
    
    // 需要登入的路由
    const protectedRoutes = ['/dashboard', '/admin', '/api/upload', '/api/documents']
    
    // 需要管理員權限的路由
    const adminRoutes = ['/admin']
    
    if (protectedRoutes.some(route => pathname.startsWith(route))) {
        if (!session?.user) {
            return NextResponse.redirect(new URL('/', request.url))
        }
        
        if (!session.user.isActive) {
            return NextResponse.redirect(new URL('/unauthorized', request.url))
        }
        
        // 檢查管理員權限
        if (adminRoutes.some(route => pathname.startsWith(route))) {
            if (session.user.role !== 'admin') {
                return NextResponse.redirect(new URL('/dashboard', request.url))
            }
        }
    }
    
    return NextResponse.next()
}

export const config = {
    matcher: ['/dashboard/:path*', '/admin/:path*', '/api/upload/:path*', '/api/documents/:path*']
}
```

#### 5. API 路由保護

```typescript
// apps/web/src/lib/api-auth.ts
import { auth } from '@/auth'
import { NextRequest, NextResponse } from 'next/server'

export async function withAuth(handler: Function, requiredRole?: 'admin' | 'cs') {
    return async (request: NextRequest) => {
        const session = await auth()
        
        if (!session?.user) {
            return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
        }
        
        if (!session.user.isActive) {
            return NextResponse.json({ error: 'Account inactive' }, { status: 403 })
        }
        
        if (requiredRole && !hasPermission(session.user.role, requiredRole)) {
            return NextResponse.json({ error: 'Insufficient permissions' }, { status: 403 })
        }
        
        return handler(request, { session })
    }
}

// 使用範例
// apps/web/src/app/api/upload/route.ts
export const POST = withAuth(async (request: NextRequest, { session }) => {
    // 只有管理員可以上傳文檔
    // 處理上傳邏輯...
}, 'admin')
```

#### 6. 資料庫操作函數

```typescript
// apps/web/src/lib/db/users.ts
import { db } from '@/lib/db' // 假設有資料庫連線

export interface UserRole {
    id: number
    line_id: string
    email?: string
    name?: string
    role: 'admin' | 'cs'
    is_active: boolean
    created_at: Date
    updated_at: Date
}

export async function getUserRole(lineId: string): Promise<UserRole | null> {
    const result = await db.query(
        'SELECT * FROM user_roles WHERE line_id = $1 AND is_active = true',
        [lineId]
    )
    return result.rows[0] || null
}

export async function createUser(userData: {
    line_id: string
    name: string
    email?: string
    role?: 'admin' | 'cs'
    created_by: string
}): Promise<UserRole> {
    const result = await db.query(`
        INSERT INTO user_roles (line_id, name, email, role, created_by)
        VALUES ($1, $2, $3, $4, $5)
        RETURNING *
    `, [userData.line_id, userData.name, userData.email, userData.role || 'cs', userData.created_by])
    
    return result.rows[0]
}

export async function updateUserRole(lineId: string, role: 'admin' | 'cs', updatedBy: string): Promise<boolean> {
    const result = await db.query(`
        UPDATE user_roles 
        SET role = $1, updated_at = CURRENT_TIMESTAMP
        WHERE line_id = $2
    `, [role, lineId])
    
    return result.rowCount > 0
}

export async function getAllUsers(): Promise<UserRole[]> {
    const result = await db.query('SELECT * FROM user_roles ORDER BY created_at DESC')
    return result.rows
}
```

#### 7. 前端權限組件

```tsx
// apps/web/src/components/PermissionGuard.tsx
import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'

interface PermissionGuardProps {
    requiredRole?: 'admin' | 'cs'
    fallback?: React.ReactNode
    redirectTo?: string
    children: React.ReactNode
}

export function PermissionGuard({ 
    requiredRole, 
    fallback, 
    redirectTo = '/dashboard',
    children 
}: PermissionGuardProps) {
    const { data: session, status } = useSession()
    const router = useRouter()
    
    useEffect(() => {
        if (status === 'loading') return
        
        if (!session) {
            router.push('/')
            return
        }
        
        if (!session.user.isActive) {
            router.push('/unauthorized')
            return
        }
        
        if (requiredRole && !hasPermission(session.user.role, requiredRole)) {
            router.push(redirectTo)
            return
        }
    }, [session, status, requiredRole, router])
    
    if (status === 'loading') {
        return <div>載入中...</div>
    }
    
    if (!session || !session.user.isActive) {
        return fallback || <div>未授權存取</div>
    }
    
    if (requiredRole && !hasPermission(session.user.role, requiredRole)) {
        return fallback || <div>權限不足</div>
    }
    
    return <>{children}</>
}
```

### 📁 檔案結構

```bash
apps/web/src/
├── auth.ts                     # NextAuth 配置
├── middleware.ts               # 路由保護
├── lib/
│   ├── auth.ts                # 權限檢查工具
│   ├── api-auth.ts            # API 權限保護
│   └── db/
│       └── users.ts           # 用戶資料庫操作
├── components/
│   └── PermissionGuard.tsx    # 權限保護組件
├── app/
│   ├── dashboard/             # 通用儀表板（CS+Admin）
│   ├── admin/                 # 管理員專區
│   └── unauthorized/          # 未授權頁面
└── types/
    └── auth.ts                # 類型定義
```

### 🚀 部署步驟

1. **建立資料庫表**

   ```bash
   # 執行 SQL 建立 user_roles 表
   psql -d your_database -f scripts/create_user_roles.sql
   ```

2. **設定環境變數**

   ```bash
   # 在 .env 中加入
   DATABASE_URL=your_database_connection_string
   ```

3. **初始化管理員帳號**
   - 先用LINE登入一次，取得你的LINE ID
   - 手動將LINE ID加入資料庫，設定為admin角色

4. **測試權限功能**
   - 管理員：可存取 `/admin` 路由
   - 客服：只能存取 `/dashboard` 路由

### 🎯 後續擴展

- 新增部門管理功能
- 操作日誌記錄
- 批量用戶匯入
- 權限細粒度控制
- SSO 整合準備
