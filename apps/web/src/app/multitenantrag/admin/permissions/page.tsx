"use client"

import React, { useState, useEffect } from "react"
import { permissionsApi } from "@/lib/api/permissionsApi"

interface User {
  id: number
  username: string
  full_name: string
}

interface Permission {
  code: string
  name: string
  category: string
}

interface Company {
  id: string
  name: string
}

interface PermissionMatrix {
  users: User[]
  permissions: Permission[]
  companies: Company[]
  permission_matrix: Record<number, string[]>
  company_matrix: Record<number, string[]>
}

export default function PermissionsPage() {
  const [matrix, setMatrix] = useState<PermissionMatrix | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadMatrix()
  }, [])

  const loadMatrix = async () => {
    try {
      const data = await permissionsApi.getMatrix()
      setMatrix(data)
    } catch (error) {
      console.error("載入權限矩陣失敗:", error)
    } finally {
      setLoading(false)
    }
  }

  const hasPermission = (userId: number, permissionCode: string) => {
    if (!matrix) return false
    return matrix.permission_matrix[userId]?.includes(permissionCode) || false
  }

  const hasCompanyAccess = (userId: number, companyId: string) => {
    if (!matrix) return false
    const userCompanies = matrix.company_matrix[userId] || []
    return userCompanies.includes(companyId) || userCompanies.includes("*")
  }

  const togglePermission = async (userId: number, permissionCode: string) => {
    if (!matrix) return

    const currentlyHas = hasPermission(userId, permissionCode)
    try {
      await permissionsApi.togglePermission(
        userId,
        permissionCode,
        !currentlyHas
      )
      await loadMatrix()
    } catch (error) {
      console.error("切換權限失敗:", error)
    }
  }

  const toggleCompanyAccess = async (userId: number, companyId: string) => {
    if (!matrix) return

    const currentlyHas = hasCompanyAccess(userId, companyId)
    try {
      await permissionsApi.toggleCompanyAccess(userId, companyId, !currentlyHas)
      await loadMatrix()
    } catch (error) {
      console.error("切換公司存取權限失敗:", error)
    }
  }

  // 按分類組織權限
  const groupedPermissions =
    matrix?.permissions.reduce((groups, permission) => {
      const category = permission.category
      if (!groups[category]) {
        groups[category] = []
      }
      groups[category].push(permission)
      return groups
    }, {} as Record<string, Permission[]>) || {}

  if (loading) {
    return <div className="p-6">載入中...</div>
  }

  if (!matrix) {
    return <div className="p-6">載入權限矩陣失敗</div>
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">權限管理矩陣</h1>

      {/* 功能權限矩陣 */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold mb-4">功能權限</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  功能
                </th>
                {matrix.users.map((user) => (
                  <th
                    key={user.id}
                    className="border border-gray-300 px-2 py-2 text-center min-w-[100px]">
                    <div className="text-sm font-medium">{user.username}</div>
                    <div className="text-xs text-gray-500">
                      {user.full_name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {Object.entries(groupedPermissions).map(
                ([category, permissions]) => (
                  <React.Fragment key={`category-${category}`}>
                    <tr className="bg-gray-100">
                      <td
                        colSpan={matrix.users.length + 1}
                        className="border border-gray-300 px-4 py-2 font-semibold">
                        🏷️ {category}
                      </td>
                    </tr>
                    {permissions.map((permission) => (
                      <tr
                        key={`permission-${permission.code}`}
                        className="hover:bg-gray-50">
                        <td className="border border-gray-300 px-4 py-2">
                          ├ {permission.name}
                          <div className="text-xs text-gray-500">
                            {permission.code}
                          </div>
                        </td>
                        {matrix.users.map((user) => (
                          <td
                            key={`${permission.code}-${user.id}`}
                            className="border border-gray-300 px-2 py-2 text-center">
                            <input
                              type="checkbox"
                              checked={hasPermission(user.id, permission.code)}
                              onChange={() =>
                                togglePermission(user.id, permission.code)
                              }
                              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                            />
                          </td>
                        ))}
                      </tr>
                    ))}
                  </React.Fragment>
                )
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* 公司存取權限矩陣 */}
      <div>
        <h2 className="text-lg font-semibold mb-4">公司存取權限</h2>
        <div className="overflow-x-auto">
          <table className="min-w-full border border-gray-300">
            <thead className="bg-gray-50">
              <tr>
                <th className="border border-gray-300 px-4 py-2 text-left">
                  公司
                </th>
                {matrix.users.map((user) => (
                  <th
                    key={user.id}
                    className="border border-gray-300 px-2 py-2 text-center min-w-[100px]">
                    <div className="text-sm font-medium">{user.username}</div>
                    <div className="text-xs text-gray-500">
                      {user.full_name}
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              <tr className="hover:bg-gray-50">
                <td className="border border-gray-300 px-4 py-2">
                  🌍 所有公司
                </td>
                {matrix.users.map((user) => (
                  <td
                    key={user.id}
                    className="border border-gray-300 px-2 py-2 text-center">
                    <input
                      type="checkbox"
                      checked={hasCompanyAccess(user.id, "*")}
                      onChange={() => toggleCompanyAccess(user.id, "*")}
                      className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                    />
                  </td>
                ))}
              </tr>
              {matrix.companies.map((company) => (
                <tr key={company.id} className="hover:bg-gray-50">
                  <td className="border border-gray-300 px-4 py-2">
                    🏢 {company.name}
                  </td>
                  {matrix.users.map((user) => (
                    <td
                      key={user.id}
                      className="border border-gray-300 px-2 py-2 text-center">
                      <input
                        type="checkbox"
                        checked={hasCompanyAccess(user.id, company.id)}
                        onChange={() =>
                          toggleCompanyAccess(user.id, company.id)
                        }
                        className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
                      />
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
