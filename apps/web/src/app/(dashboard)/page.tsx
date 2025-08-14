import { auth } from "@/auth"
import { redirect } from "next/navigation"

export default async function DashboardPage() {
  const session = await auth()
  
  if (!session) {
    redirect("/auth/login")
  }

  // 根據角色決定預設頁面
  if (session.user.role === 'super_admin') {
    redirect("/admin")
  }

  return (
    <div className="space-y-6">
      <div className="border-b border-gray-200 pb-4">
        <h1 className="text-3xl font-bold text-gray-900">儀表板</h1>
        <p className="mt-2 text-gray-600">
          歡迎使用 LineRAG 多租戶管理平台
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            我的公司
          </h3>
          <p className="text-gray-600">
            管理您有權限的公司資料
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            對話記錄
          </h3>
          <p className="text-gray-600">
            查看和管理客戶對話記錄
          </p>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            知識庫
          </h3>
          <p className="text-gray-600">
            管理文檔和知識庫內容
          </p>
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          用戶資訊
        </h3>
        <div className="space-y-2">
          <p><span className="font-medium">姓名:</span> {session.user.name}</p>
          <p><span className="font-medium">Email:</span> {session.user.email}</p>
          <p><span className="font-medium">角色:</span> {session.user.role}</p>
          <p><span className="font-medium">狀態:</span> {session.user.isActive ? '啟用' : '停用'}</p>
        </div>
      </div>
    </div>
  )
}