"use client"

import { useSession, signOut } from "next-auth/react"
import { usePathname, useParams } from "next/navigation"
import Link from "next/link"
import { useState, useMemo } from "react"
import {
  getAdminFeatures,
  getCompanyFeatures,
  type FeatureCard,
} from "@/config/features"
import { CompanySelector } from "./CompanySelector"

// 將功能卡片轉換為導航項目
function featureToNavItem(feature: FeatureCard) {
  return {
    name: feature.title.replace(/^[^\s]+\s/, ""), // 移除 emoji
    href: feature.href || "",
    icon: feature.title.match(/^[^\s]+/)?.[0] || "📄", // 提取 emoji
  }
}

export function Sidebar() {
  const { data: session } = useSession()
  const pathname = usePathname()
  const params = useParams()
  const [isCollapsed, setIsCollapsed] = useState(false)

  // 根據用戶角色和當前路徑決定顯示的導航
  const navigation = useMemo(() => {
    if (!session) return []

    const userRole = session.user.role || ""
    const userCompanies = session.user.companies || []
    const currentCompanyId = params.companyId as string
    const nav = []

    // Super Admin 可以看到系統管理導航
    if (userRole === "super_admin") {
      const adminFeatures = getAdminFeatures(userRole)
      nav.push(...adminFeatures.map(featureToNavItem))
    }

    // 如果有當前公司 ID 或用戶有公司權限，顯示公司導航
    if (currentCompanyId || userCompanies.length > 0) {
      const companyId = currentCompanyId || userCompanies[0]?.id
      if (companyId) {
        const companyFeatures = getCompanyFeatures(userRole, companyId)
        nav.push(...companyFeatures.map(featureToNavItem))
      }
    }

    return nav
  }, [session, params.companyId])

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

      {/* 公司選擇器 */}
      {!isCollapsed &&
        session?.user?.companies &&
        session.user.companies.length > 0 && (
          <div className="px-4 py-2 border-b border-gray-200">
            <CompanySelector />
          </div>
        )}

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
            <p className="text-xs text-gray-500">{session.user.role}</p>
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
