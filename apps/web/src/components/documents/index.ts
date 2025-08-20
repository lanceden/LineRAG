/**
 * 文檔管理組件導出
 */

// 主要組件
export { DocumentUploader } from './DocumentUploader'
export { DocumentList, DocumentGrid } from './DocumentList'
export { ProcessingStatus, ProcessingStatusBadge } from './ProcessingStatus'

// 權限保護組件
export {
  DocumentPermissionGuard,
  DocumentUploadGuard,
  DocumentDeleteGuard,
  DocumentCategoryGuard,
  DocumentAnalyticsGuard,
  DocumentExportGuard,
  DocumentBatchGuard,
  useDocumentPermissions,
  checkDocumentPermission,
  DOCUMENT_PERMISSIONS,
  ROLE_DOCUMENT_PERMISSIONS,
} from './DocumentPermissionGuard'

// 類型導出
export type {
  DocumentMetadata,
  DocumentStatus,
  DocumentUploadRequest,
  DocumentUploadResponse,
  DocumentListParams,
  DocumentListResponse,
  DocumentStats,
  UploadProgress,
  BatchOperationRequest,
  BatchOperationResponse,
  SupportedFileType,
} from '@/types/document'
