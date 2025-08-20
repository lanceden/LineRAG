"use client"

import { useSession, signOut } from "next-auth/react"
import { usePathname } from "next/navigation"
import Link from "next/link"
import { useState, useMemo } from "react"

export function Sidebar() {
  const { data: session } = useSession()
  const pathname = usePathname()
  const [isCollapsed, setIsCollapsed] = useState(false)

  // 固定選單 - 所有用戶都能看到所有選單項目
  const navigation = useMemo(() => {
    if (!session) return []

    // 固定的選單項目
    const nav = [
      { name: "公司管理", href: "/multitenantrag/admin/companies", icon: "🏢" },
      { name: "用戶管理", href: "/multitenantrag/admin/users", icon: "👥" },
      {
        name: "權限管理",
        href: "/multitenantrag/admin/permissions",
        icon: "🔐",
      },
      {
        name: "系統監控",
        href: "/multitenantrag/admin/monitoring",
        icon: "📊",
      },
    ]

    return nav
  }, [session])

  if (!session) return null

  return (
    <div
      className={`fixed left-0 top-0 h-full bg-white shadow-lg border-r border-gray-200 z-40 transition-all duration-300 ${
        isCollapsed ? "w-16" : "w-64"
      }`}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        {!isCollapsed && (
          <h1 className="text-xl font-bold text-gray-900">LineRAG</h1>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-2 rounded-md hover:bg-gray-100">
          {isCollapsed ? "→" : "←"}
        </button>
      </div>

      {/* Navigation */}
      <nav className="mt-4 px-2">
        <ul className="space-y-1">
          {navigation.map((item) => {
            const isActive = pathname === item.href

            return (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? "bg-blue-50 text-blue-700 border-r-2 border-blue-500"
                      : "text-gray-700 hover:bg-gray-50"
                  }`}>
                  <span className="text-lg">{item.icon}</span>
                  {!isCollapsed && <span className="ml-3">{item.name}</span>}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      {/* User Info & Logout */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
        {!isCollapsed && (
          <div className="mb-3">
            <p className="text-sm font-medium text-gray-900">
              {session.user.name}
            </p>
          </div>
        )}
        <button
          onClick={() => signOut()}
          className={`w-full flex items-center px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 rounded-md transition-colors ${
            isCollapsed ? "justify-center" : ""
          }`}>
          <span className="text-lg">🚪</span>
          {!isCollapsed && <span className="ml-3">登出</span>}
        </button>
      </div>
    </div>
  )
}
