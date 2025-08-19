import { auth } from "@/auth"
import { redirect } from "next/navigation"
import Link from "next/link"

export default async function AdminPage() {
  const session = await auth()

  // 檢查是否已登入
  if (!session?.user) {
    redirect("/multitenantrag/auth/login")
  }

  return (
    <>
        <div className="border-b border-gray-200 pb-4">
          <h1 className="text-3xl font-bold text-gray-900">
            LineRAG 管理儀表板
          </h1>
          <p className="mt-2 text-gray-600">
            歡迎，{session.user.name || session.user.email}
          </p>
        </div>

        {/* 統計卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">總公司數</p>
                <p className="text-2xl font-bold text-gray-900">-</p>
              </div>
              <div className="text-blue-500">🏢</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">總用戶數</p>
                <p className="text-2xl font-bold text-gray-900">-</p>
              </div>
              <div className="text-green-500">👥</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-yellow-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">本月對話數</p>
                <p className="text-2xl font-bold text-gray-900">-</p>
              </div>
              <div className="text-yellow-500">💬</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-purple-500">
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">系統狀態</p>
                <p className="text-2xl font-bold text-green-600">正常</p>
              </div>
              <div className="text-purple-500">⚙️</div>
            </div>
          </div>
        </div>

        {/* 快速操作 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              🏢 公司管理
            </h3>
            <p className="text-gray-600 mb-4">新增、編輯和管理所有公司資料</p>
            <Link
              href="/multitenantrag/admin/companies"
              className="block w-full bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md transition-colors text-center">
              管理公司
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              👥 用戶管理
            </h3>
            <p className="text-gray-600 mb-4">管理系統用戶和權限設定</p>
            <Link
              href="/multitenantrag/admin/users"
              className="block w-full bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md transition-colors text-center">
              管理用戶
            </Link>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              🔐 權限管理
            </h3>
            <p className="text-gray-600 mb-4">管理用戶權限矩陣設定</p>
            <Link
              href="/multitenantrag/admin/permissions"
              className="block w-full bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md transition-colors text-center">
              權限設定
            </Link>
          </div>
        </div>

        {/* 最新活動 */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            📋 最新活動
          </h3>
          <div className="space-y-3">
            <div className="flex items-center space-x-3 text-sm">
              <span className="w-2 h-2 bg-green-500 rounded-full"></span>
              <span className="text-gray-600">系統啟動完成</span>
              <span className="text-gray-400">剛剛</span>
            </div>
            <div className="flex items-center space-x-3 text-sm">
              <span className="w-2 h-2 bg-blue-500 rounded-full"></span>
              <span className="text-gray-600">管理員登入系統</span>
              <span className="text-gray-400">1 分鐘前</span>
            </div>
          </div>
        </div>
    </>
  )
}
