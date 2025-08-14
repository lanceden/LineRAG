'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect } from 'react'
import { hasPermission } from '@/lib/permissions'
import { Permission } from '@/types/auth'

interface PermissionGuardProps {
  requiredPermission?: keyof Omit<Permission, 'canAccessCompany'>
  fallback?: React.ReactNode
  redirectTo?: string
  children: React.ReactNode
}

export default function PermissionGuard({ 
  requiredPermission, 
  fallback, 
  redirectTo = '/dashboard',
  children 
}: PermissionGuardProps) {
  const { data: session, status } = useSession()
  const router = useRouter()
  
  useEffect(() => {
    if (status === 'loading') return
    
    if (!session) {
      router.push('/auth/login')
      return
    }
    
    if (!session.user?.isActive) {
      router.push('/auth/login')
      return
    }
    
    if (requiredPermission && !hasPermission(requiredPermission, session.user?.role)) {
      router.push(redirectTo)
      return
    }
  }, [session, status, requiredPermission, router, redirectTo])
  
  if (status === 'loading') {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <span className="ml-3 text-gray-600">載入中...</span>
      </div>
    )
  }
  
  if (!session || !session.user?.isActive) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">未授權存取</h1>
          <p className="text-gray-600 mb-6">您需要登入才能存取此頁面</p>
          <button 
            onClick={() => router.push('/auth/login')}
            className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            登入
          </button>
        </div>
      </div>
    )
  }
  
  if (requiredPermission && !hasPermission(requiredPermission, session.user?.role)) {
    return fallback || (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-800 mb-4">權限不足</h1>
          <p className="text-gray-600 mb-6">您沒有存取此功能的權限</p>
          <button 
            onClick={() => router.push(redirectTo)}
            className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700"
          >
            返回儀表板
          </button>
        </div>
      </div>
    )
  }
  
  return <>{children}</>
}