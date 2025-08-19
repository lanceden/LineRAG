/**
 * 權限矩陣管理 API
 */

import { httpClient } from './httpClient'

interface User {
  id: number
  username: string
  full_name: string
}

interface Permission {
  code: string
  name: string
  category: string
}

interface Company {
  id: string
  name: string
}

interface PermissionMatrix {
  users: User[]
  permissions: Permission[]
  companies: Company[]
  permission_matrix: Record<number, string[]>
  company_matrix: Record<number, string[]>
}

export const permissionsApi = {
  // 獲取權限矩陣資料
  async getMatrix(): Promise<PermissionMatrix> {
    return await httpClient.get('/api/permissions/matrix')
  },

  // 切換用戶功能權限
  async togglePermission(userId: number, permissionCode: string, granted: boolean) {
    return await httpClient.post('/api/permissions/matrix/toggle', {
      user_id: userId,
      permission_code: permissionCode,
      granted: granted
    })
  },

  // 切換用戶公司存取權限
  async toggleCompanyAccess(userId: number, companyId: string, granted: boolean) {
    return await httpClient.post('/api/permissions/matrix/company-access', {
      user_id: userId,
      company_id: companyId,
      granted: granted
    })
  }
}