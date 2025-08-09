"use client"

import { useSession } from "next-auth/react"
import FileUpload from "../components/FileUpload"
import { useState } from "react"

export default function UploadPage() {
  const { data: session, status } = useSession()
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  if (status === "loading") {
    return (
      <div className="p-6 text-center">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <p className="mt-2 text-gray-600">載入中...</p>
      </div>
    )
  }

  const handleUploadSuccess = (fileName: string) => {
    setMessage({ type: 'success', text: `檔案 ${fileName} 上傳成功！` })
    setTimeout(() => setMessage(null), 5000)
  }

  const handleUploadError = (error: string) => {
    setMessage({ type: 'error', text: error })
    setTimeout(() => setMessage(null), 5000)
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">文檔上傳</h1>
          <p className="text-gray-600">
            上傳 PDF 或 Word 文檔到知識庫，讓 AI 助手能夠回答相關問題
          </p>
        </div>

        {/* 訊息提示 */}
        {message && (
          <div className={`
            mb-6 p-4 rounded-lg border
            ${message.type === 'success' 
              ? 'bg-green-50 border-green-200 text-green-800' 
              : 'bg-red-50 border-red-200 text-red-800'
            }
          `}>
            <div className="flex items-center">
              <div className="flex-shrink-0">
                {message.type === 'success' ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                )}
              </div>
              <div className="ml-3">
                <p className="font-medium">{message.text}</p>
              </div>
              <div className="ml-auto">
                <button
                  onClick={() => setMessage(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        )}

        {session && session.user ? (
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-6">
              <FileUpload 
                onUploadSuccess={handleUploadSuccess}
                onUploadError={handleUploadError}
              />
            </div>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-sm border p-8 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">需要登入</h3>
            <p className="text-gray-600">請先登入以使用文檔上傳功能</p>
          </div>
        )}
      </div>
    </div>
  )
}