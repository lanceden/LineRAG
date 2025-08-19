/**
 * 功能配置 - 已棄用角色系統，改用權限矩陣
 * 保留此文件為參考，實際權限控制由後端中間件處理
 */

import { PERMISSIONS, type Permission } from './permissions'

export interface FeatureCard {
  id: string
  title: string
  description: string
  buttonText: string
  buttonColor: string
  href?: string
  permissions: Permission[]  // 使用權限常量類型
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
    permissions: [PERMISSIONS.COMPANY_VIEW, PERMISSIONS.COMPANY_CREATE],
    category: 'admin'
  },
  {
    id: 'users',
    title: '👥 用戶管理',
    description: '管理系統用戶和權限設定',
    buttonText: '管理用戶',
    buttonColor: 'bg-green-500 hover:bg-green-600',
    href: '/multitenantrag/admin/users',
    permissions: [PERMISSIONS.USER_VIEW, PERMISSIONS.USER_CREATE],
    category: 'admin'
  },
  {
    id: 'admin-documents',
    title: '📄 文檔管理',
    description: '管理文檔和知識庫內容',
    buttonText: '文檔管理',
    buttonColor: 'bg-emerald-500 hover:bg-emerald-600',
    href: '/multitenantrag/admin/documents',
    permissions: [PERMISSIONS.DOCUMENT_VIEW, PERMISSIONS.DOCUMENT_UPLOAD],
    category: 'admin'
  },
  {
    id: 'company-dashboard',
    title: '📊 公司儀表板',
    description: '查看公司總覽和關鍵指標',
    buttonText: '查看儀表板',
    buttonColor: 'bg-blue-500 hover:bg-blue-600',
    href: '/multitenantrag/company/[companyId]',
    permissions: [PERMISSIONS.COMPANY_VIEW],
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
    permissions: [PERMISSIONS.CHAT_VIEW],
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
    permissions: [PERMISSIONS.COMPANY_MANAGE],
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
    permissions: [PERMISSIONS.ANALYTICS_VIEW],
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
    permissions: [PERMISSIONS.COMPANY_MANAGE],
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
    permissions: [PERMISSIONS.SYSTEM_MONITOR],
    category: 'admin'
  }
]

