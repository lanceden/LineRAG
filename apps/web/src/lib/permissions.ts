import { SystemUserRole, Permission } from '@/types/auth'

type Company = {
  id: string
  name: string
  is_active: boolean
}

export const getPermissions = (userRole?: string, userCompanies?: Company[]): Permission => {
  const role = userRole as SystemUserRole

  return {
    canManageCompanies: role === 'super_admin',
    canManageUsers: ['super_admin', 'company_admin'].includes(role),
    canViewAllChats: ['super_admin', 'company_admin', 'cs_manager'].includes(role),
    canUploadDocuments: role !== 'cs_agent',
    canDeleteDocuments: ['super_admin', 'company_admin'].includes(role),
    canManageDocumentCategories: ['super_admin', 'company_admin'].includes(role),
    canViewDocumentAnalytics: ['super_admin', 'company_admin', 'cs_manager'].includes(role),
    canExportDocuments: role !== 'cs_agent',
    canBatchOperateDocuments: ['super_admin', 'company_admin'].includes(role),
    canAccessCompany: (companyId: string) => {
      if (role === 'super_admin') return true

      // 檢查用戶是否有該公司的權限
      if (userCompanies) {
        return userCompanies.some(company => company.id === companyId && company.is_active)
      }

      return false
    }
  }
}

export const hasPermission = (
  permission: keyof Omit<Permission, 'canAccessCompany'>,
  userRole?: string
): boolean => {
  const permissions = getPermissions(userRole)
  return permissions[permission]
}

export const canAccessCompany = (
  companyId: string,
  userRole?: string,
  userCompanies?: Company[]
): boolean => {
  const permissions = getPermissions(userRole, userCompanies)
  return permissions.canAccessCompany(companyId)
}