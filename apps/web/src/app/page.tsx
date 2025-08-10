"use client"

import { signIn, signOut, useSession } from "next-auth/react"
import Image from "next/image"

export default function Home() {
  const { data: session, status } = useSession()

  if (status === "loading") {
    return (
      <div className="min-h-screen flex items-center justify-center">
        載入中...
      </div>
    )
  }

  return (
    <div className="font-sans min-h-screen p-8 pb-20 gap-16">
      <main className="max-w-2xl mx-auto pt-20">
        <div className="text-center mb-12">
          <Image
            className="dark:invert mx-auto mb-8"
            src="/next.svg"
            alt="Next.js logo"
            width={180}
            height={38}
            priority
          />
          <h1 className="text-3xl font-bold mb-4">LINE RAG Lite</h1>
          <p className="text-gray-600 dark:text-gray-400">
            使用 LINE 登入測試應用程式
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-8 border border-gray-200 dark:border-gray-700">
          {session && session.user?.lineId ? (
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-6 text-green-600">
                登入成功！
              </h2>
              <div className="mb-6">
                {session.user?.image && (
                  <div className="mb-4">
                    <Image
                      src={session.user.image}
                      alt="Profile"
                      width={80}
                      height={80}
                      className="rounded-full mx-auto"
                    />
                  </div>
                )}
                <div className="space-y-2 text-left bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                  <p>
                    <strong>姓名:</strong> {session.user?.name || "未設定"}
                  </p>
                  <p>
                    <strong>Email:</strong> {session.user?.email || "未設定"}
                  </p>
                  <p>
                    <strong>LINE ID:</strong> {session.user?.lineId || "未設定"}
                  </p>
                </div>
              </div>
              <button
                onClick={() => signOut()}
                className="bg-red-500 hover:bg-red-600 text-white font-medium py-2 px-6 rounded-lg transition-colors">
                登出
              </button>
            </div>
          ) : (
            <div className="text-center">
              <h2 className="text-2xl font-semibold mb-6">請登入以繼續</h2>
              <button
                onClick={() => signIn("line", { callbackUrl: "/me" })}
                className="bg-green-500 hover:bg-green-600 text-white font-medium py-3 px-8 rounded-lg transition-colors flex items-center gap-3 mx-auto">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="currentColor">
                  <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12.017.572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314" />
                </svg>
                使用 LINE 登入
              </button>
              <div className="mt-6 text-sm text-gray-500 dark:text-gray-400">
                <p>點擊登入按鈕將導向至 LINE 授權頁面</p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
