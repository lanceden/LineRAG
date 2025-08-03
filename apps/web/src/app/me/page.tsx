"use client"

import { useSession } from "next-auth/react"
import Image from "next/image"

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
          {session.user.image && (
            <Image
              src={session.user.image}
              alt="user image"
              width={100}
              height={100}
            />
          )}
        </>
      ) : (
        <h1 className="text-xl font-bold">尚未登入</h1>
      )}
    </div>
  )
}
