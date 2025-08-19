/**
 * 權限代碼配置
 * 定義所有系統權限的常量
 */

export const PERMISSIONS = {
  // 公司管理
  COMPANY_VIEW: 'company.view',
  COMPANY_CREATE: 'company.create',
  COMPANY_EDIT: 'company.edit',
  COMPANY_DELETE: 'company.delete',
  COMPANY_MANAGE: 'company.manage',

  // 用戶管理
  USER_VIEW: 'user.view',
  USER_CREATE: 'user.create',
  USER_EDIT: 'user.edit',
  USER_DELETE: 'user.delete',
  USER_MANAGE: 'user.manage',

  // 文檔管理
  DOCUMENT_VIEW: 'document.view',
  DOCUMENT_UPLOAD: 'document.upload',
  DOCUMENT_EDIT: 'document.edit',
  DOCUMENT_DELETE: 'document.delete',
  DOCUMENT_MANAGE: 'document.manage',
  DOCUMENT_ANALYTICS: 'document.analytics',
  DOCUMENT_CATEGORIES: 'document.categories',
  DOCUMENT_EXPORT: 'document.export',

  // 對話管理
  CHAT_VIEW: 'chat.view',
  CHAT_MANAGE: 'chat.manage',

  // 分析報表
  ANALYTICS_VIEW: 'analytics.view',
  ANALYTICS_EXPORT: 'analytics.export',

  // 系統管理
  SYSTEM_MONITOR: 'system.monitor',
  SYSTEM_CONFIG: 'system.config',

  // 權限管理
  PERMISSION_VIEW: 'permission.view',
  PERMISSION_MANAGE: 'permission.manage',
} as const

// 權限分類
export const PERMISSION_CATEGORIES = {
  COMPANY: '公司管理',
  USER: '用戶管理', 
  DOCUMENT: '文檔管理',
  CHAT: '對話管理',
  ANALYTICS: '分析報表',
  SYSTEM: '系統管理',
  PERMISSION: '權限管理',
} as const

// 權限描述映射
export const PERMISSION_DESCRIPTIONS = {
  [PERMISSIONS.COMPANY_VIEW]: '查看公司資訊',
  [PERMISSIONS.COMPANY_CREATE]: '創建新公司',
  [PERMISSIONS.COMPANY_EDIT]: '編輯公司資訊',
  [PERMISSIONS.COMPANY_DELETE]: '刪除公司',
  [PERMISSIONS.COMPANY_MANAGE]: '完整公司管理權限',

  [PERMISSIONS.USER_VIEW]: '查看用戶資訊',
  [PERMISSIONS.USER_CREATE]: '創建新用戶',
  [PERMISSIONS.USER_EDIT]: '編輯用戶資訊',
  [PERMISSIONS.USER_DELETE]: '刪除用戶',
  [PERMISSIONS.USER_MANAGE]: '完整用戶管理權限',

  [PERMISSIONS.DOCUMENT_VIEW]: '查看文檔',
  [PERMISSIONS.DOCUMENT_UPLOAD]: '上傳文檔',
  [PERMISSIONS.DOCUMENT_EDIT]: '編輯文檔',
  [PERMISSIONS.DOCUMENT_DELETE]: '刪除文檔',
  [PERMISSIONS.DOCUMENT_MANAGE]: '完整文檔管理權限',
  [PERMISSIONS.DOCUMENT_ANALYTICS]: '查看文檔分析',
  [PERMISSIONS.DOCUMENT_CATEGORIES]: '管理文檔分類',
  [PERMISSIONS.DOCUMENT_EXPORT]: '匯出文檔',

  [PERMISSIONS.CHAT_VIEW]: '查看對話記錄',
  [PERMISSIONS.CHAT_MANAGE]: '管理對話記錄',

  [PERMISSIONS.ANALYTICS_VIEW]: '查看分析報表',
  [PERMISSIONS.ANALYTICS_EXPORT]: '匯出分析報表',

  [PERMISSIONS.SYSTEM_MONITOR]: '系統監控',
  [PERMISSIONS.SYSTEM_CONFIG]: '系統配置',

  [PERMISSIONS.PERMISSION_VIEW]: '查看權限設定',
  [PERMISSIONS.PERMISSION_MANAGE]: '管理權限設定',
} as const

export type Permission = typeof PERMISSIONS[keyof typeof PERMISSIONS]