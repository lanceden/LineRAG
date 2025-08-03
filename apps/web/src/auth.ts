import NextAuth from 'next-auth'
import Line from 'next-auth/providers/line'

export const { handlers, signIn, signOut, auth } = NextAuth({
    providers: [
        Line({
            clientId: process.env.LINE_CLIENT_ID!,
            clientSecret: process.env.LINE_CLIENT_SECRET!,
        }),
    ],
    callbacks: {
        async jwt({ token, account, profile }) {
            if (account && profile) {
                token.lineId = (profile as { userId?: string }).userId
            }
            return token
        },
        async session({ session, token }) {
            if (session.user) {
                session.user.lineId = token.lineId as string
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