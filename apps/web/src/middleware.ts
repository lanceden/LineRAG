import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'
import { auth } from '@/auth'

export async function middleware(request: NextRequest) {
  const session = await auth()
  const { pathname } = request.nextUrl

  // 公開路由，不需要認證
  const publicRoutes = ['/multitenantrag/auth/login']
  if (publicRoutes.includes(pathname)) {
    return NextResponse.next()
  }

  // 檢查是否已認證
  if (!session) {
    return NextResponse.redirect(new URL('/multitenantrag/auth/login', request.url))
  }

  // 檢查用戶是否啟用
  if (!session.user.isActive) {
    return NextResponse.redirect(new URL('/multitenantrag/auth/login', request.url))
  }

  // 檢查系統管理員權限 - 只限制特定管理功能，允許儀表板訪問
  const restrictedAdminPaths = [
    '/multitenantrag/admin/users',
    '/multitenantrag/admin/companies',
    '/multitenantrag/admin/system'
  ]
  
  const isRestrictedPath = restrictedAdminPaths.some(path => pathname.startsWith(path))
  if (isRestrictedPath && session.user.role !== 'super_admin') {
    return NextResponse.redirect(new URL('/multitenantrag/admin', request.url))
  }

  // 檢查公司存取權限
  const companyMatch = pathname.match(/\/company\/([^\/]+)/)
  if (companyMatch) {
    const companyId = companyMatch[1]
    const userRole = session.user.role
    const userCompanies = session.user.companies || []

    // super_admin 可以存取所有公司
    if (userRole !== 'super_admin') {
      // 檢查用戶是否有該公司的權限
      const hasAccess = userCompanies.some(company => 
        company.id === companyId && company.is_active
      )
      
      if (!hasAccess) {
        return NextResponse.redirect(new URL('/dashboard', request.url))
      }
    }
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * 符合所有請求路徑，除了：
     * - api (API routes)
     * - _next/static (靜態文件)
     * - _next/image (圖片優化文件)
     * - favicon.ico (網站圖標)
     * - 其他靜態資源
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}