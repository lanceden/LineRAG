/**
 * 公司管理組件導出
 */

// 新的統一管理後台組件
export { CompanyCard } from './CompanyCard'
export { CompanyFormDialog } from './CompanyFormDialog'
export { LineSettingsDialog } from './LineSettingsDialog'
export { SystemConfigDialog } from './SystemConfigDialog'
export { UserManagementDialog } from './UserManagementDialog'
export { DocumentManagementDialog } from './DocumentManagementDialog'

// 類型導出
export type {
  Company,
  CreateCompanyRequest,
  UpdateCompanyRequest,
  CompanyListParams,
  CompanyListResponse,
  CompanyStats,
  CompanySettings,
  CompanyUser,
  CompanyUserListResponse,
  InviteUserRequest,
  CompanyInvitation,
  CompanyActivity,
  BusinessHours,
} from '@/types/company'
