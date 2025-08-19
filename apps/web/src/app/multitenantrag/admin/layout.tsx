"use client"

import { Sidebar } from "@/components/Sidebar"

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      <Sidebar />
      <main className="ml-64 p-6 space-y-6">
        {children}
      </main>
    </div>
  )
}