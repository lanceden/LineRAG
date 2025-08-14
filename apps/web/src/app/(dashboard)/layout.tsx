import { auth } from "@/auth"
import { redirect } from "next/navigation"
import { SessionProvider } from "@/components/SessionProvider"
import { Sidebar } from "@/components/Sidebar"

export default async function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const session = await auth()
  
  if (!session) {
    redirect("/auth/login")
  }

  return (
    <SessionProvider>
      <div className="flex min-h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 lg:ml-64 transition-all duration-300">
          <div className="p-6">
            {children}
          </div>
        </main>
      </div>
    </SessionProvider>
  )
}