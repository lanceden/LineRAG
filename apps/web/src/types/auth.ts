import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      role?: string
      isActive?: boolean
      accessToken?: string
      companies?: Array<{
        id: string
        name: string
        is_active: boolean
      }>
    } & DefaultSession["user"]
  }

  interface User {
    role?: string
    isActive?: boolean
    accessToken?: string
    companies?: Array<{
      id: string
      name: string
      is_active: boolean
    }>
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    role?: string
    isActive?: boolean
    accessToken?: string
    companies?: Array<{
      id: string
      name: string
      is_active: boolean
    }>
  }
}

export type SystemUserRole = 'super_admin' | 'company_admin' | 'cs_manager' | 'cs_agent'

export interface Permission {
  canManageCompanies: boolean
  canManageUsers: boolean
  canViewAllChats: boolean
  canUploadDocuments: boolean
  canDeleteDocuments: boolean
  canManageDocumentCategories: boolean
  canViewDocumentAnalytics: boolean
  canExportDocuments: boolean
  canBatchOperateDocuments: boolean
  canAccessCompany: (companyId: string) => boolean
}