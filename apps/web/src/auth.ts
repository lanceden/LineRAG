import NextAuth from 'next-auth'
import CredentialsProvider from 'next-auth/providers/credentials'
import './types/auth'

export const { handlers, signIn, signOut, auth } = NextAuth({
  secret: process.env.NEXTAUTH_SECRET,
  providers: [
    CredentialsProvider({
      name: "credentials",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" }
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials?.password) {
          return null
        }

        try {
          const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
          const response = await fetch(`${apiUrl}/api/auth/login`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })

          if (response.ok) {
            const loginData = await response.json()
            const userData = loginData.user
            return {
              id: userData.id,
              email: userData.email,
              name: userData.full_name,
              isActive: userData.is_active,
              companies: loginData.accessible_companies || [],
              accessToken: loginData.access_token, // 保存後端的 access_token
            }
          }
        } catch (error) {
          console.error('Authentication error:', error)
        }
        
        return null
      }
    })
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        token.isActive = user.isActive
        token.companies = user.companies
        token.accessToken = user.accessToken // 保存 access_token 到 JWT
      }
      return token
    },
    async session({ session, token }) {
      if (session.user) {
        session.user.isActive = token.isActive as boolean
        session.user.companies = token.companies as Array<{
          id: string
          name: string
          is_active: boolean
        }>
        session.user.accessToken = token.accessToken as string // 添加到 session
      }
      return session
    },
    async redirect({ url, baseUrl }) {
      if (url.startsWith(baseUrl)) {
        return url
      }
      return `${baseUrl}/multitenantrag/admin`
    },
  },
  pages: {
    signIn: '/multitenantrag/auth/login',
  },
})