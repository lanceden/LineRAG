import { redirect } from "next/navigation"

export default function HomePage() {
  // 直接重導向到登入頁面
  redirect("/multitenantrag/auth/login")
}