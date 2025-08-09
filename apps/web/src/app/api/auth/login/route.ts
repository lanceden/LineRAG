import { NextRequest, NextResponse } from 'next/server'
import { signIn } from '@/auth'

export async function POST(request: NextRequest) {
    try {
        const body = await request.json()
        const { provider = 'line', callbackUrl = '/dashboard' } = body
        
        // 觸發 NextAuth 登入流程
        const result = await signIn(provider, {
            redirectTo: callbackUrl,
            redirect: false
        })
        
        return NextResponse.json({
            success: true,
            message: '登入成功',
            redirectUrl: result?.url || callbackUrl
        })
    } catch (error) {
        console.error('Login error:', error)
        return NextResponse.json(
            { 
                success: false, 
                error: '登入失敗',
                message: error instanceof Error ? error.message : '未知錯誤'
            },
            { status: 500 }
        )
    }
}

// GET 方法用於檢查登入狀態
export async function GET() {
    return NextResponse.json({
        message: '請使用 POST 方法進行登入',
        loginUrl: '/api/auth/signin/line'
    })
}