'use client'

import React, { useState, useEffect } from 'react'
import { useSession } from 'next-auth/react'
import { Sidebar } from '@/components/Sidebar'
import { DocumentUpload } from '@/components/documents/DocumentUpload'
import { DocumentList } from '@/components/documents/DocumentList'
import { ProcessingStatus } from '@/components/documents/ProcessingStatus'
import { companiesApi, documentsApi } from '@/lib/api'
import { FileText, Upload, List, Activity } from 'lucide-react'

export default function DocumentsPage() {
  const { data: session } = useSession()
  const [activeTab, setActiveTab] = useState<'upload' | 'list' | 'processing'>('upload')
  const [documents, setDocuments] = useState<any[]>([])
  const [processingTasks, setProcessingTasks] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [userCompanyId, setUserCompanyId] = useState<number | null>(null)

  // 獲取用戶所屬公司 ID
  useEffect(() => {
    const fetchUserCompany = async () => {
      if (!session?.user) return
      
      try {
        // 如果是 super_admin，可以選擇公司；否則使用用戶所屬公司
        if (session.user.role === 'super_admin') {
          // 暫時使用第一個公司，後續可以添加公司選擇器
          const companies = await companiesApi.getList()
          if (companies.companies && companies.companies.length > 0) {
            setUserCompanyId(companies.companies[0].id)
          }
        } else {
          // 一般用戶，獲取所屬公司
          // TODO: 實作獲取用戶所屬公司的 API
          setUserCompanyId(1) // 暫時硬編碼
        }
      } catch (error) {
        console.error('獲取用戶公司失敗:', error)
      }
    }

    fetchUserCompany()
  }, [session])

  // 載入文檔列表
  const loadDocuments = async () => {
    if (!userCompanyId) return
    
    setLoading(true)
    try {
      const result = await documentsApi.getCompanyDocuments(userCompanyId)
      setDocuments(result.documents || [])
    } catch (error) {
      console.error('載入文檔列表失敗:', error)
    } finally {
      setLoading(false)
    }
  }

  // 載入處理中的任務
  const loadProcessingTasks = async () => {
    // TODO: 實作獲取處理中任務的 API
    setProcessingTasks([])
  }

  useEffect(() => {
    if (activeTab === 'list') {
      loadDocuments()
    } else if (activeTab === 'processing') {
      loadProcessingTasks()
    }
  }, [activeTab, userCompanyId])

  // 處理文檔上傳完成
  const handleUploadComplete = (result: any) => {
    console.log('文檔上傳完成:', result)
    // 如果在列表標籤，重新載入列表
    if (activeTab === 'list') {
      loadDocuments()
    }
    // 切換到處理狀態標籤
    setActiveTab('processing')
  }

  // 處理文檔刪除
  const handleDocumentDelete = async (documentId: string) => {
    if (!userCompanyId) return
    
    try {
      await documentsApi.delete(documentId)
      // 重新載入文檔列表
      loadDocuments()
    } catch (error) {
      console.error('刪除文檔失敗:', error)
    }
  }

  const tabs = [
    { id: 'upload', name: '上傳文檔', icon: Upload },
    { id: 'list', name: '文檔列表', icon: List },
    { id: 'processing', name: '處理狀態', icon: Activity },
  ]

  if (!session) {
    return (
      <>
        <Sidebar />
        <div className="ml-64 p-6">
          <div className="text-center py-12">
            <p className="text-gray-500">請先登入</p>
          </div>
        </div>
      </>
    )
  }

  if (!userCompanyId) {
    return (
      <>
        <Sidebar />
        <div className="ml-64 p-6">
          <div className="text-center py-12">
            <p className="text-gray-500">載入中...</p>
          </div>
        </div>
      </>
    )
  }

  return (
    <>
      <Sidebar />
      <div className="ml-64 p-6 space-y-6">
        {/* 頁面標題 */}
        <div className="flex items-center space-x-3">
          <FileText className="h-8 w-8 text-blue-600" />
          <div>
            <h1 className="text-2xl font-bold text-gray-900">文檔管理</h1>
            <p className="text-sm text-gray-500">上傳和管理知識庫文檔</p>
          </div>
        </div>

        {/* 標籤導航 */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as any)}
                  className={`flex items-center space-x-2 py-2 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{tab.name}</span>
                </button>
              )
            })}
          </nav>
        </div>

        {/* 標籤內容 */}
        <div className="space-y-6">
          {activeTab === 'upload' && (
            <div className="bg-white rounded-lg shadow p-6">
              <DocumentUpload
                companyId={userCompanyId}
                onUploadComplete={handleUploadComplete}
                onUploadError={(error) => console.error('上傳錯誤:', error)}
              />
            </div>
          )}

          {activeTab === 'list' && (
            <div className="bg-white rounded-lg shadow p-6">
              <DocumentList
                companyId={userCompanyId}
                documents={documents}
                loading={loading}
                onDocumentDelete={handleDocumentDelete}
              />
            </div>
          )}

          {activeTab === 'processing' && (
            <div className="bg-white rounded-lg shadow p-6">
              <ProcessingStatus
                tasks={processingTasks}
                onRefresh={loadProcessingTasks}
              />
            </div>
          )}
        </div>
      </div>
    </>
  )
}
