"use client"

import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface SidebarProps {
  className?: string
}

interface MenuItem {
  id: string
  label: string
  href: string
  icon: React.ReactNode
}

export default function Sidebar({ className = "" }: SidebarProps) {
  const [isCollapsed, setIsCollapsed] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)
  const pathname = usePathname()

  const menuItems: MenuItem[] = [
    {
      id: "home",
      label: "首頁",
      href: "/me",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      )
    },
    {
      id: "chat",
      label: "對話測試",
      href: "/chat",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-3.582 8-8 8a8.959 8.959 0 01-4.906-1.436L3 21l2.436-5.094A8.959 8.959 0 013 12c0-4.418 3.582-8 8-8s8 3.582 8 8z" />
        </svg>
      )
    },
    {
      id: "upload",
      label: "文檔上傳",
      href: "/upload",
      icon: (
        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
        </svg>
      )
    }
  ]

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed)
  }

  const toggleMobileMenu = () => {
    setIsMobileMenuOpen(!isMobileMenuOpen)
  }

  const isActiveRoute = (href: string) => {
    return pathname === href
  }

  return (
    <>
      {/* 移動端選單按鈕 */}
      <button
        onClick={toggleMobileMenu}
        className="fixed top-4 left-4 z-50 lg:hidden p-2 bg-white rounded-lg shadow-md border border-gray-200"
      >
        <svg className="w-6 h-6 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      <div className={`${className} relative`}>
        {/* 側邊欄 */}
        <div 
          className={`
            fixed left-0 top-0 h-full bg-white border-r border-gray-200 shadow-sm z-40 transition-all duration-300 ease-in-out
            ${isCollapsed ? 'w-16' : 'w-64'}
            ${isMobileMenuOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
          `}
        >
        {/* 頂部區域 */}
        <div className="flex items-center justify-between p-4 border-b border-gray-200">
          {!isCollapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                <span className="text-white font-bold text-sm">LR</span>
              </div>
              <span className="font-semibold text-gray-900">LineRAG</span>
            </div>
          )}
          
          {/* 縮放按鈕 */}
          <button
            onClick={toggleSidebar}
            className={`
              p-2 rounded-lg hover:bg-gray-100 transition-colors
              ${isCollapsed ? 'mx-auto' : ''}
            `}
            title={isCollapsed ? "展開側邊欄" : "收起側邊欄"}
          >
            <svg 
              className={`w-5 h-5 text-gray-600 transition-transform duration-300 ${isCollapsed ? 'rotate-180' : ''}`} 
              fill="none" 
              stroke="currentColor" 
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        {/* 導航選單 */}
        <nav className="p-4">
          <ul className="space-y-2">
            {menuItems.map((item) => (
              <li key={item.id}>
                <Link
                  href={item.href}
                  className={`
                    flex items-center p-3 rounded-lg transition-colors group
                    ${isActiveRoute(item.href) 
                      ? 'bg-blue-50 text-blue-700 border border-blue-200' 
                      : 'text-gray-700 hover:bg-gray-100'
                    }
                  `}
                  title={isCollapsed ? item.label : undefined}
                >
                  <div className={`
                    flex-shrink-0 transition-colors
                    ${isActiveRoute(item.href) ? 'text-blue-600' : 'text-gray-500 group-hover:text-gray-700'}
                  `}>
                    {item.icon}
                  </div>
                  
                  {!isCollapsed && (
                    <span className="ml-3 font-medium">{item.label}</span>
                  )}
                  
                  {/* 活動指示器 */}
                  {isActiveRoute(item.href) && isCollapsed && (
                    <div className="absolute left-0 w-1 h-8 bg-blue-600 rounded-r-full"></div>
                  )}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        {/* 底部區域 */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          {!isCollapsed ? (
            <div className="text-xs text-gray-500 text-center">
              <p>LineRAG v1.0</p>
              <p>AI 文檔助手</p>
            </div>
          ) : (
            <div className="flex justify-center">
              <div className="w-2 h-2 bg-green-500 rounded-full" title="系統運行中"></div>
            </div>
          )}
        </div>
      </div>

        {/* 遮罩層 (移動端) */}
        {isMobileMenuOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-25 z-30 lg:hidden"
            onClick={toggleMobileMenu}
          />
        )}
      </div>
    </>
  )
}