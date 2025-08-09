import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      lineId?: string
      role?: string
      isActive?: boolean
    } & DefaultSession["user"]
  }

  interface User {
    lineId?: string
    role?: string
    isActive?: boolean
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    lineId?: string
    role?: string
    isActive?: boolean
  }
}