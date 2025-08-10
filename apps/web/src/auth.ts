import NextAuth from 'next-auth'
import Line from 'next-auth/providers/line'
import './types/auth' // 匯入類型擴展

export const { handlers, signIn, signOut, auth } = NextAuth({
    secret: process.env.NEXTAUTH_SECRET,
    providers: [
        Line({
            clientId: process.env.LINE_CLIENT_ID!,
            clientSecret: process.env.LINE_CLIENT_SECRET!,
        }),
    ],
    callbacks: {
        async jwt({ token, account, profile }) {
            if (account && profile) {
                // 調試：輸出 profile 內容
                console.log('LINE Profile:', profile)
                
                // LINE profile 中的 user ID 屬性名稱是 'sub'
                token.lineId = (profile as { sub?: string }).sub

                // 從FastAPI取得用戶角色
                if (token.lineId) {
                    try {
                        const apiUrl = process.env.PYTHON_API_URL || 'http://localhost:8000'
                        const response = await fetch(`${apiUrl}/users/role/${token.lineId}`)
                        if (response.ok) {
                            const userData = await response.json()
                            token.role = userData.role || 'cs'
                            token.isActive = userData.is_active ?? true
                        } else {
                            // API呼叫失敗，設定預設值
                            token.role = 'cs'
                            token.isActive = true
                        }
                    } catch (error) {
                        console.error('Failed to fetch user role:', error)
                        token.role = 'cs'
                        token.isActive = true
                    }
                }
            }
            return token
        },
        async session({ session, token }) {
            if (session.user) {
                session.user.lineId = token.lineId as string
                session.user.role = token.role as string
                session.user.isActive = token.isActive as boolean
            }
            return session
        },
        async redirect({ url, baseUrl }) {
            // 如果是從登入頁面來的，預設導向到 /me
            if (url.startsWith(baseUrl)) {
                return url
            }
            // 如果沒有指定 URL，預設導向到 /me
            return `${baseUrl}/me`
        },
    },
    pages: {
        signIn: '/',
    },
})