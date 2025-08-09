"use client"

import { useSession } from "next-auth/react"
import Image from "next/image"
import Chat from "../components/ChatPanel"
import FileUpload from "../components/FileUpload"

export default function MePage() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="p-4 text-center">
        <p>載入中...</p>
      </div>
    )
  }

  const handleUploadSuccess = (fileName: string) => {
    console.log(`檔案 ${fileName} 上傳成功`)
    // 可以在這裡添加成功提示或其他邏輯
  }

  const handleUploadError = (error: string) => {
    console.error('上傳錯誤:', error)
    // 可以在這裡添加錯誤提示
  }

  return (
    <div className="p-4">
      {session && session.user ? (
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="text-center">
            <h1 className="text-2xl font-bold mb-4">歡迎回來 {session.user.name}</h1>
            {session.user.image && (
              <Image
                src={session.user.image}
                alt="user image"
                width={100}
                height={100}
                className="mx-auto rounded-full"
              />
            )}
          </div>
          
          {/* 檔案上傳區域 */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <FileUpload 
              onUploadSuccess={handleUploadSuccess}
              onUploadError={handleUploadError}
            />
          </div>
          
          {/* 聊天區域 */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">AI 助手</h2>
            <Chat />
          </div>
        </div>
      ) : (
        <div className="text-center">
          <h1 className="text-xl font-bold">尚未登入</h1>
        </div>
      )}
    </div>
  )
}
