import NextAuth from 'next-auth';
import { LineProvider } from '@/app/auth/line';

const handler = NextAuth({
    providers: [LineProvider],
    pages: {
        signIn: '/',
    },
    callbacks: {
        async jwt({ token, account, profile }) {
            if (account && profile) {
                token.lineId = (profile as { userId?: string }).userId;
            }
            return token;
        },
        async session({ session, token }) {
            if (!session.user) {
                session.user = {};
            }
            session.user.lineId = token.lineId;
            return session;
        },
        async redirect({ url, baseUrl }) {
            // 如果 URL 已經是完整的 URL 且是同一個 domain，直接使用
            if (url.startsWith(baseUrl)) return url;
            // 如果 URL 是相對路徑，加上 baseUrl
            if (url.startsWith('/')) return `${baseUrl}${url}`;
            // 預設重定向到 /me
            return `${baseUrl}/me`;
        },
    },
});

export { handler as GET, handler as POST };