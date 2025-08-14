/**
 * 功能權限配置
 * 定義各個功能模塊的權限和展示信息
 */

export interface FeatureCard {
  id: string
  title: string
  description: string
  buttonText: string
  buttonColor: string
  href?: string
  roles: string[]
  requiresCompanyId?: boolean
  category?: 'admin' | 'company' | 'analytics'
}

export const featureCards: FeatureCard[] = [
  {
    id: 'companies',
    title: '🏢 公司管理',
    description: '新增、編輯和管理所有公司資料',
    buttonText: '管理公司',
    buttonColor: 'bg-blue-500 hover:bg-blue-600',
    href: '/multitenantrag/admin/companies',
    roles: ['super_admin'],
    category: 'admin'
  },
  {
    id: 'users',
    title: '👥 用戶管理',
    description: '管理系統用戶和權限設定',
    buttonText: '管理用戶',
    buttonColor: 'bg-green-500 hover:bg-green-600',
    href: '/multitenantrag/admin/users',
    roles: ['super_admin'],
    category: 'admin'
  },
  {
    id: 'admin-documents',
    title: '📄 全域知識庫',
    description: '管理所有公司的文檔和知識庫',
    buttonText: '管理知識庫',
    buttonColor: 'bg-emerald-500 hover:bg-emerald-600',
    href: '/multitenantrag/admin/documents',
    roles: ['super_admin'],
    category: 'admin'
  },
  {
    id: 'company-dashboard',
    title: '📊 公司儀表板',
    description: '查看公司總覽和關鍵指標',
    buttonText: '查看儀表板',
    buttonColor: 'bg-blue-500 hover:bg-blue-600',
    href: '/multitenantrag/company/[companyId]',
    roles: ['company_admin', 'cs_manager', 'cs_agent'],
    requiresCompanyId: true,
    category: 'company'
  },
  {
    id: 'documents',
    title: '📄 知識庫管理',
    description: '上傳、管理文檔和知識庫內容',
    buttonText: '管理知識庫',
    buttonColor: 'bg-emerald-500 hover:bg-emerald-600',
    href: '/multitenantrag/company/[companyId]/documents',
    roles: ['super_admin', 'admin', 'company_admin', 'cs_manager'],
    requiresCompanyId: true,
    category: 'company'
  },
  {
    id: 'chats',
    title: '💬 對話記錄',
    description: '查看和管理客戶對話記錄',
    buttonText: '查看對話',
    buttonColor: 'bg-green-500 hover:bg-green-600',
    href: '/multitenantrag/company/[companyId]/chats',
    roles: ['super_admin', 'company_admin', 'cs_manager', 'cs_agent'],
    requiresCompanyId: true,
    category: 'company'
  },
  {
    id: 'company-users',
    title: '👥 公司用戶',
    description: '管理公司內部用戶和權限',
    buttonText: '管理用戶',
    buttonColor: 'bg-violet-500 hover:bg-violet-600',
    href: '/multitenantrag/company/[companyId]/users',
    roles: ['company_admin'],
    requiresCompanyId: true,
    category: 'company'
  },
  {
    id: 'analytics',
    title: '📈 分析報表',
    description: '查看使用統計和分析報表',
    buttonText: '查看報表',
    buttonColor: 'bg-indigo-500 hover:bg-indigo-600',
    href: '/multitenantrag/company/[companyId]/analytics',
    roles: ['super_admin', 'company_admin', 'cs_manager'],
    requiresCompanyId: true,
    category: 'analytics'
  },
  {
    id: 'company-settings',
    title: '⚙️ 公司設定',
    description: '管理公司設定和 LINE 整合',
    buttonText: '管理設定',
    buttonColor: 'bg-gray-500 hover:bg-gray-600',
    href: '/multitenantrag/company/[companyId]/settings',
    roles: ['company_admin'],
    requiresCompanyId: true,
    category: 'company'
  },
  {
    id: 'monitoring',
    title: '📊 系統監控',
    description: '監控系統效能和使用狀況',
    buttonText: '查看監控',
    buttonColor: 'bg-purple-500 hover:bg-purple-600',
    href: '/multitenantrag/admin/monitoring',
    roles: ['super_admin'],
    category: 'admin'
  }
]

/**
 * 根據用戶角色過濾可用功能
 */
export function getAvailableFeatures(userRole: string, companyId?: string): FeatureCard[] {
  return featureCards
    .filter(card => card.roles.includes(userRole))
    .map(card => {
      // 如果功能需要 companyId 且有提供，則替換 URL 中的佔位符
      if (card.requiresCompanyId && companyId && card.href) {
        return {
          ...card,
          href: card.href.replace('[companyId]', companyId)
        }
      }
      return card
    })
}

/**
 * 根據分類獲取功能
 */
export function getFeaturesByCategory(category: 'admin' | 'company' | 'analytics', userRole: string, companyId?: string): FeatureCard[] {
  return getAvailableFeatures(userRole, companyId).filter(card => card.category === category)
}

/**
 * 獲取系統管理功能
 */
export function getAdminFeatures(userRole: string): FeatureCard[] {
  return getFeaturesByCategory('admin', userRole)
}

/**
 * 獲取公司級功能
 */
export function getCompanyFeatures(userRole: string, companyId: string): FeatureCard[] {
  return getFeaturesByCategory('company', userRole, companyId)
}

/**
 * 獲取分析相關功能
 */
export function getAnalyticsFeatures(userRole: string, companyId?: string): FeatureCard[] {
  return getFeaturesByCategory('analytics', userRole, companyId)
}

/**
 * 檢查用戶是否有權限訪問特定功能
 */
export function hasFeaturePermission(featureId: string, userRole: string): boolean {
  const feature = featureCards.find(card => card.id === featureId)
  return feature ? feature.roles.includes(userRole) : false
}

/**
 * 檢查功能是否需要公司 ID
 */
export function requiresCompanyId(featureId: string): boolean {
  const feature = featureCards.find(card => card.id === featureId)
  return feature ? feature.requiresCompanyId === true : false
}

/**
 * 獲取用戶的主要儀表板 URL
 */
export function getUserDashboardUrl(userRole: string, companyId?: string): string {
  if (userRole === 'super_admin') {
    return '/multitenantrag/admin'
  }

  if (companyId) {
    return `/multitenantrag/company/${companyId}`
  }

  // 如果沒有公司 ID，返回預設頁面
  return '/multitenantrag/admin'
}

/**
 * 文檔管理功能配置
 */
export const DOCUMENT_FEATURES = {
  UPLOAD: 'document-upload',
  MANAGE: 'document-manage',
  ANALYTICS: 'document-analytics',
  CATEGORIES: 'document-categories',
  EXPORT: 'document-export',
} as const

/**
 * 檢查用戶是否有文檔相關權限
 */
export function hasDocumentPermission(permission: keyof typeof DOCUMENT_FEATURES, userRole: string): boolean {
  const permissions = {
    'document-upload': ['super_admin', 'company_admin', 'cs_manager'],
    'document-manage': ['super_admin', 'company_admin', 'cs_manager'],
    'document-analytics': ['super_admin', 'company_admin', 'cs_manager'],
    'document-categories': ['super_admin', 'company_admin'],
    'document-export': ['super_admin', 'company_admin', 'cs_manager'],
  }

  const feature = DOCUMENT_FEATURES[permission]
  return permissions[feature]?.includes(userRole) || false
}