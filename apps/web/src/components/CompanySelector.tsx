'use client'

import React, { useState } from 'react'
import { useSession } from 'next-auth/react'
import { useRouter, useParams } from 'next/navigation'
import { ChevronDown, Building2, Check } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Company {
  id: string
  name: string
  is_active: boolean
}

export function CompanySelector() {
  const { data: session } = useSession()
  const router = useRouter()
  const params = useParams()
  const [isOpen, setIsOpen] = useState(false)

  if (!session?.user?.companies || session.user.companies.length === 0) {
    return null
  }

  const companies = session.user.companies as Company[]
  const currentCompanyId = params.companyId as string
  const currentCompany = companies.find(c => c.id === currentCompanyId) || companies[0]

  const handleCompanyChange = (companyId: string) => {
    setIsOpen(false)
    
    // 如果當前在公司相關頁面，切換到新公司的相同頁面
    const currentPath = window.location.pathname
    if (currentPath.includes('/company/')) {
      const newPath = currentPath.replace(
        `/company/${currentCompanyId}`,
        `/company/${companyId}`
      )
      router.push(newPath)
    } else {
      // 否則導航到新公司的儀表板
      router.push(`/multitenantrag/company/${companyId}`)
    }
  }

  // 如果只有一家公司，顯示簡單的公司名稱
  if (companies.length === 1) {
    return (
      <div className="flex items-center px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg">
        <Building2 className="h-4 w-4 mr-2 text-gray-400" />
        <span className="font-medium">{currentCompany.name}</span>
      </div>
    )
  }

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between w-full px-3 py-2 text-sm text-gray-700 bg-gray-50 rounded-lg hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
      >
        <div className="flex items-center">
          <Building2 className="h-4 w-4 mr-2 text-gray-400" />
          <span className="font-medium truncate">{currentCompany.name}</span>
        </div>
        <ChevronDown 
          className={cn(
            "h-4 w-4 text-gray-400 transition-transform",
            isOpen && "transform rotate-180"
          )} 
        />
      </button>

      {isOpen && (
        <>
          {/* 背景遮罩 */}
          <div 
            className="fixed inset-0 z-10" 
            onClick={() => setIsOpen(false)}
          />
          
          {/* 下拉選單 */}
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-20 max-h-60 overflow-y-auto">
            {companies.map((company) => (
              <button
                key={company.id}
                onClick={() => handleCompanyChange(company.id)}
                className={cn(
                  "flex items-center justify-between w-full px-3 py-2 text-sm text-left hover:bg-gray-50 focus:outline-none focus:bg-gray-50",
                  company.id === currentCompany.id && "bg-blue-50 text-blue-700",
                  !company.is_active && "opacity-50"
                )}
                disabled={!company.is_active}
              >
                <div className="flex items-center">
                  <Building2 className="h-4 w-4 mr-2 text-gray-400" />
                  <span className="font-medium truncate">{company.name}</span>
                  {!company.is_active && (
                    <span className="ml-2 text-xs text-gray-400">(停用)</span>
                  )}
                </div>
                {company.id === currentCompany.id && (
                  <Check className="h-4 w-4 text-blue-600" />
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  )
}

// 簡化版本的公司選擇器，用於較小的空間
export function CompactCompanySelector() {
  const { data: session } = useSession()
  const params = useParams()

  if (!session?.user?.companies || session.user.companies.length === 0) {
    return null
  }

  const companies = session.user.companies as Company[]
  const currentCompanyId = params.companyId as string
  const currentCompany = companies.find(c => c.id === currentCompanyId) || companies[0]

  return (
    <div className="flex items-center text-xs text-gray-500">
      <Building2 className="h-3 w-3 mr-1" />
      <span className="truncate max-w-24">{currentCompany.name}</span>
    </div>
  )
}

// 公司資訊顯示組件
export function CompanyInfo() {
  const { data: session } = useSession()
  const params = useParams()

  if (!session?.user?.companies || session.user.companies.length === 0) {
    return null
  }

  const companies = session.user.companies as Company[]
  const currentCompanyId = params.companyId as string
  const currentCompany = companies.find(c => c.id === currentCompanyId) || companies[0]

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4">
      <div className="flex items-center">
        <div className="flex-shrink-0">
          <Building2 className="h-8 w-8 text-gray-400" />
        </div>
        <div className="ml-3">
          <h3 className="text-sm font-medium text-gray-900">
            {currentCompany.name}
          </h3>
          <p className="text-xs text-gray-500">
            公司 ID: {currentCompany.id}
          </p>
          <div className="mt-1">
            <span className={cn(
              "inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium",
              currentCompany.is_active 
                ? "bg-green-100 text-green-800" 
                : "bg-red-100 text-red-800"
            )}>
              {currentCompany.is_active ? "啟用中" : "已停用"}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}

// 用於頁面標題的公司名稱顯示
export function CompanyPageTitle({ title }: { title: string }) {
  const { data: session } = useSession()
  const params = useParams()

  if (!session?.user?.companies || session.user.companies.length === 0) {
    return <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
  }

  const companies = session.user.companies as Company[]
  const currentCompanyId = params.companyId as string
  const currentCompany = companies.find(c => c.id === currentCompanyId) || companies[0]

  return (
    <div>
      <div className="flex items-center text-sm text-gray-500 mb-1">
        <Building2 className="h-4 w-4 mr-1" />
        <span>{currentCompany.name}</span>
      </div>
      <h1 className="text-2xl font-bold text-gray-900">{title}</h1>
    </div>
  )
}
