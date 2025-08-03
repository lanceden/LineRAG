"use client"

import { useSession } from "next-auth/react"

export default function MePage() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="p-4 text-center">
        <p>載入中...</p>
      </div>
    )
  }

  return (
    <div className="p-4 text-center">
      {session && session.user ? (
        <>
          <h1 className="text-xl font-bold">歡迎回來 {session.user.name}</h1>
          <p className="mt-2">userId: {session.user.lineId}</p>
        </>
      ) : (
        <h1 className="text-xl font-bold">尚未登入</h1>
      )}
    </div>
  )
}
