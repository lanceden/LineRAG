'use client'

import React from 'react'
import { useSession } from 'next-auth/react'
import { getPermissions } from '@/lib/permissions'
import type { Permission } from '@/types/auth'

interface DocumentPermissionGuardProps {
  children: React.ReactNode
  companyId?: string
  permission?: keyof Omit<Permission, 'canAccessCompany'>
  fallback?: React.ReactNode
  requireAll?: boolean // 是否需要所有權限都滿足
}

/**
 * 文檔權限保護組件
 * 根據用戶角色和公司權限控制文檔功能的顯示
 */
export function DocumentPermissionGuard({
  children,
  companyId,
  permission,
  fallback = null,
  requireAll = false,
}: DocumentPermissionGuardProps) {
  const { data: session } = useSession()
  
  if (!session?.user) {
    return <>{fallback}</>
  }

  const permissions = getPermissions(session.user.role, session.user.companies)

  // 檢查公司存取權限
  if (companyId && !permissions.canAccessCompany(companyId)) {
    return <>{fallback}</>
  }

  // 檢查特定權限
  if (permission && !permissions[permission]) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

/**
 * 文檔上傳權限保護
 */
export function DocumentUploadGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canUploadDocuments"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 文檔刪除權限保護
 */
export function DocumentDeleteGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canDeleteDocuments"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 文檔分類管理權限保護
 */
export function DocumentCategoryGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canManageDocumentCategories"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 文檔分析權限保護
 */
export function DocumentAnalyticsGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canViewDocumentAnalytics"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 文檔匯出權限保護
 */
export function DocumentExportGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canExportDocuments"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 文檔批次操作權限保護
 */
export function DocumentBatchGuard({
  children,
  companyId,
  fallback,
}: {
  children: React.ReactNode
  companyId?: string
  fallback?: React.ReactNode
}) {
  return (
    <DocumentPermissionGuard
      companyId={companyId}
      permission="canBatchOperateDocuments"
      fallback={fallback}
    >
      {children}
    </DocumentPermissionGuard>
  )
}

/**
 * 使用權限的 hook
 */
export function useDocumentPermissions(companyId?: string) {
  const { data: session } = useSession()
  
  if (!session?.user) {
    return {
      canUploadDocuments: false,
      canDeleteDocuments: false,
      canManageDocumentCategories: false,
      canViewDocumentAnalytics: false,
      canExportDocuments: false,
      canBatchOperateDocuments: false,
      canAccessCompany: false,
    }
  }

  const permissions = getPermissions(session.user.role, session.user.companies)
  
  return {
    canUploadDocuments: permissions.canUploadDocuments,
    canDeleteDocuments: permissions.canDeleteDocuments,
    canManageDocumentCategories: permissions.canManageDocumentCategories,
    canViewDocumentAnalytics: permissions.canViewDocumentAnalytics,
    canExportDocuments: permissions.canExportDocuments,
    canBatchOperateDocuments: permissions.canBatchOperateDocuments,
    canAccessCompany: companyId ? permissions.canAccessCompany(companyId) : true,
  }
}

/**
 * 檢查是否有文檔相關權限的工具函數
 */
export function checkDocumentPermission(
  permission: keyof Omit<Permission, 'canAccessCompany'>,
  userRole?: string,
  companyId?: string,
  userCompanies?: Array<{ id: string; name: string; is_active: boolean }>
): boolean {
  const permissions = getPermissions(userRole, userCompanies)
  
  // 檢查公司存取權限
  if (companyId && !permissions.canAccessCompany(companyId)) {
    return false
  }
  
  return permissions[permission]
}

/**
 * 文檔操作權限配置
 */
export const DOCUMENT_PERMISSIONS = {
  UPLOAD: 'canUploadDocuments' as const,
  DELETE: 'canDeleteDocuments' as const,
  MANAGE_CATEGORIES: 'canManageDocumentCategories' as const,
  VIEW_ANALYTICS: 'canViewDocumentAnalytics' as const,
  EXPORT: 'canExportDocuments' as const,
  BATCH_OPERATE: 'canBatchOperateDocuments' as const,
} as const

/**
 * 角色對應的文檔權限映射
 */
export const ROLE_DOCUMENT_PERMISSIONS = {
  super_admin: [
    DOCUMENT_PERMISSIONS.UPLOAD,
    DOCUMENT_PERMISSIONS.DELETE,
    DOCUMENT_PERMISSIONS.MANAGE_CATEGORIES,
    DOCUMENT_PERMISSIONS.VIEW_ANALYTICS,
    DOCUMENT_PERMISSIONS.EXPORT,
    DOCUMENT_PERMISSIONS.BATCH_OPERATE,
  ],
  company_admin: [
    DOCUMENT_PERMISSIONS.UPLOAD,
    DOCUMENT_PERMISSIONS.DELETE,
    DOCUMENT_PERMISSIONS.MANAGE_CATEGORIES,
    DOCUMENT_PERMISSIONS.VIEW_ANALYTICS,
    DOCUMENT_PERMISSIONS.EXPORT,
    DOCUMENT_PERMISSIONS.BATCH_OPERATE,
  ],
  cs_manager: [
    DOCUMENT_PERMISSIONS.UPLOAD,
    DOCUMENT_PERMISSIONS.VIEW_ANALYTICS,
    DOCUMENT_PERMISSIONS.EXPORT,
  ],
  cs_agent: [
    // cs_agent 只能檢視，不能進行任何文檔操作
  ],
} as const
