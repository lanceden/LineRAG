import type { Metadata } from "next"

export const metadata: Metadata = {
  title: "登入 - LineRAG 多租戶管理平台",
  description: "LineRAG 多租戶 AI 客服系統管理平台",
}

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {children}
      </div>
    </div>
  )
}