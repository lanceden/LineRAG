/**
 * API 統一出口
 * 所有 API 調用都通過這裡匯出
 */

export { api, apiClient, ApiError } from './client'
export { usersApi } from './users'
export type {
  User,
  CreateUserRequest,
  UpdateUserRequest,
  UserListResponse,
  UserStatsResponse,
} from './users'

// 未來可以添加更多 API 模組
// export { companiesApi } from './companies'
// export { documentsApi } from './documents'
// export { chatsApi } from './chats'